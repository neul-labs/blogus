"""
Python AST Parser for detecting LLM API calls.

Detects calls to:
- openai.chat.completions.create()
- anthropic.messages.create()
- litellm.completion()
- litellm.acompletion()
- instructor.create()
- And extracts prompt/message content
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import hashlib


@dataclass
class DetectedPrompt:
    """A prompt detected in source code."""
    file_path: Path
    line_number: int
    end_line: int
    prompt_text: str
    detection_type: str          # 'llm_call', 'marker', 'string_variable'
    api_type: Optional[str]      # 'openai', 'anthropic', 'litellm', 'instructor'
    function_name: Optional[str] # Name of containing function
    variable_name: Optional[str] # Variable the prompt is assigned to
    linked_prompt: Optional[str] # Reference from @blogus marker
    version_info: Optional[str]  # Embedded version hash from marker
    messages: List[Dict[str, str]] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        """SHA256 hash of the prompt content."""
        return hashlib.sha256(self.prompt_text.encode()).hexdigest()[:16]

    @property
    def short_hash(self) -> str:
        """Short hash for display."""
        return self.content_hash[:8]


# Patterns for detecting LLM API calls
LLM_CALL_PATTERNS = {
    'openai': [
        ('chat', 'completions', 'create'),
        ('ChatCompletion', 'create'),
    ],
    'anthropic': [
        ('messages', 'create'),
        ('completions', 'create'),
    ],
    'litellm': [
        ('completion',),
        ('acompletion',),
        ('text_completion',),
    ],
    'instructor': [
        ('create',),
        ('chat', 'completions', 'create'),
    ],
}

# Comment marker pattern: @blogus:prompt-name@v1 sha256:abc123
MARKER_PATTERN = re.compile(
    r'@blogus:(?P<name>[\w-]+)(?:@v(?P<version>\d+))?\s*(?:sha256:(?P<hash>[a-f0-9]+))?',
    re.IGNORECASE
)


class PythonPromptParser:
    """
    Parse Python files to detect LLM API calls and prompt strings.

    Uses Python's ast module for reliable parsing.
    """

    def __init__(self):
        self.detected_prompts: List[DetectedPrompt] = []
        self._imports: Dict[str, str] = {}  # alias -> module
        self._current_file: Optional[Path] = None
        self._current_function: Optional[str] = None
        self._source_lines: List[str] = []

    def parse_file(self, file_path: Path) -> List[DetectedPrompt]:
        """
        Parse a Python file and detect prompts.

        Args:
            file_path: Path to Python file

        Returns:
            List of detected prompts
        """
        self.detected_prompts = []
        self._current_file = file_path
        self._imports = {}
        self._current_function = None

        try:
            source = file_path.read_text(encoding='utf-8')
            self._source_lines = source.splitlines()
        except (UnicodeDecodeError, IOError):
            return []

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            # Fall back to regex-based detection for files with syntax errors
            return self._regex_fallback(source)

        # First pass: collect imports
        self._collect_imports(tree)

        # Second pass: find LLM calls
        self._visit_node(tree)

        # Third pass: find comment markers
        self._scan_markers()

        return self.detected_prompts

    def parse_string(self, source: str, filename: str = "<string>") -> List[DetectedPrompt]:
        """Parse Python source code from a string."""
        self.detected_prompts = []
        self._current_file = Path(filename)
        self._imports = {}
        self._current_function = None
        self._source_lines = source.splitlines()

        try:
            tree = ast.parse(source, filename=filename)
        except SyntaxError:
            return self._regex_fallback(source)

        self._collect_imports(tree)
        self._visit_node(tree)
        self._scan_markers()

        return self.detected_prompts

    def _collect_imports(self, tree: ast.AST) -> None:
        """Collect import statements to track module aliases."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    self._imports[name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.asname or alias.name
                    self._imports[name] = f"{module}.{alias.name}"

    def _visit_node(self, node: ast.AST, parent_function: Optional[str] = None) -> None:
        """Visit AST nodes recursively."""
        # Track current function context
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent_function = node.name

        # Check for LLM API calls
        if isinstance(node, ast.Call):
            self._check_llm_call(node, parent_function)

        # Check for prompt string assignments
        if isinstance(node, ast.Assign):
            self._check_prompt_assignment(node, parent_function)

        # Recurse into children
        for child in ast.iter_child_nodes(node):
            self._visit_node(child, parent_function)

    def _check_llm_call(self, node: ast.Call, function_name: Optional[str]) -> None:
        """Check if a Call node is an LLM API call."""
        call_chain = self._get_call_chain(node.func)
        if not call_chain:
            return

        # Check against known patterns
        api_type = self._match_api_pattern(call_chain)
        if not api_type:
            return

        # Extract messages/prompt from the call
        messages, prompt_text = self._extract_messages(node)
        if not prompt_text and not messages:
            return

        # Get source lines for context
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', node.lineno)

        # Check for preceding @blogus marker
        marker_info = self._find_preceding_marker(start_line)

        detected = DetectedPrompt(
            file_path=self._current_file,
            line_number=start_line,
            end_line=end_line,
            prompt_text=prompt_text or str(messages),
            detection_type='llm_call',
            api_type=api_type,
            function_name=function_name,
            variable_name=None,
            linked_prompt=marker_info.get('name') if marker_info else None,
            version_info=marker_info.get('hash') if marker_info else None,
            messages=messages
        )
        self.detected_prompts.append(detected)

    def _get_call_chain(self, node: ast.AST) -> List[str]:
        """Extract the call chain from an AST node (e.g., ['openai', 'chat', 'completions', 'create'])."""
        chain = []

        while True:
            if isinstance(node, ast.Attribute):
                chain.insert(0, node.attr)
                node = node.value
            elif isinstance(node, ast.Name):
                # Resolve import alias
                name = node.id
                if name in self._imports:
                    module_parts = self._imports[name].split('.')
                    chain = module_parts + chain
                else:
                    chain.insert(0, name)
                break
            elif isinstance(node, ast.Call):
                # Handle chained calls like client().chat.completions.create()
                node = node.func
            else:
                break

        return chain

    def _match_api_pattern(self, call_chain: List[str]) -> Optional[str]:
        """Check if call chain matches known LLM API patterns."""
        chain_str = '.'.join(call_chain).lower()

        for api_type, patterns in LLM_CALL_PATTERNS.items():
            for pattern in patterns:
                pattern_str = '.'.join(pattern).lower()
                if pattern_str in chain_str:
                    return api_type

        return None

    def _extract_messages(self, node: ast.Call) -> tuple:
        """Extract messages or prompt from an API call."""
        messages = []
        prompt_text = ""

        for keyword in node.keywords:
            if keyword.arg == 'messages':
                messages = self._extract_messages_list(keyword.value)
                if messages:
                    prompt_text = self._messages_to_text(messages)
            elif keyword.arg in ('prompt', 'content', 'input'):
                prompt_text = self._extract_string_value(keyword.value)
            elif keyword.arg == 'system':
                system_text = self._extract_string_value(keyword.value)
                if system_text:
                    messages.append({'role': 'system', 'content': system_text})

        # Also check positional arguments
        if not messages and not prompt_text and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.List):
                messages = self._extract_messages_list(first_arg)
                prompt_text = self._messages_to_text(messages)
            else:
                prompt_text = self._extract_string_value(first_arg)

        return messages, prompt_text

    def _extract_messages_list(self, node: ast.AST) -> List[Dict[str, str]]:
        """Extract a list of message dictionaries."""
        messages = []

        if not isinstance(node, ast.List):
            return messages

        for elem in node.elts:
            if isinstance(elem, ast.Dict):
                msg = {}
                for key, value in zip(elem.keys, elem.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        key_name = key.value
                        if key_name in ('role', 'content'):
                            msg[key_name] = self._extract_string_value(value)
                if 'role' in msg and 'content' in msg:
                    messages.append(msg)

        return messages

    def _extract_string_value(self, node: ast.AST) -> str:
        """Extract string value from an AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.JoinedStr):
            # f-string - extract parts
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif isinstance(value, ast.FormattedValue):
                    parts.append("{...}")  # Placeholder for formatted value
            return ''.join(parts)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            # String concatenation
            left = self._extract_string_value(node.left)
            right = self._extract_string_value(node.right)
            return left + right
        elif isinstance(node, ast.Name):
            # Variable reference
            return f"{{{node.id}}}"  # Mark as variable
        return ""

    def _messages_to_text(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages list to readable text."""
        parts = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            parts.append(f"[{role}] {content}")
        return '\n'.join(parts)

    def _check_prompt_assignment(self, node: ast.Assign, function_name: Optional[str]) -> None:
        """Check if an assignment is a prompt string variable."""
        # Look for assignments like:
        # system_prompt = "You are a helpful assistant..."
        # PROMPT = """..."""

        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue

            var_name = target.id.lower()
            prompt_indicators = ['prompt', 'system', 'instruction', 'template', 'message']

            if not any(ind in var_name for ind in prompt_indicators):
                continue

            value = self._extract_string_value(node.value)
            if not value or len(value) < 20:  # Skip short strings
                continue

            # Check for @blogus marker
            marker_info = self._find_preceding_marker(node.lineno)

            detected = DetectedPrompt(
                file_path=self._current_file,
                line_number=node.lineno,
                end_line=getattr(node, 'end_lineno', node.lineno),
                prompt_text=value,
                detection_type='string_variable',
                api_type=None,
                function_name=function_name,
                variable_name=target.id,
                linked_prompt=marker_info.get('name') if marker_info else None,
                version_info=marker_info.get('hash') if marker_info else None
            )
            self.detected_prompts.append(detected)

    def _find_preceding_marker(self, line_number: int) -> Optional[Dict[str, str]]:
        """Find @blogus marker in comments above the given line."""
        # Check up to 5 lines above
        for i in range(max(0, line_number - 5), line_number):
            if i >= len(self._source_lines):
                continue
            line = self._source_lines[i]
            match = MARKER_PATTERN.search(line)
            if match:
                return {
                    'name': match.group('name'),
                    'version': match.group('version'),
                    'hash': match.group('hash')
                }
        return None

    def _scan_markers(self) -> None:
        """Scan all comments for @blogus markers without associated code."""
        for i, line in enumerate(self._source_lines, 1):
            if '#' not in line:
                continue

            match = MARKER_PATTERN.search(line)
            if not match:
                continue

            # Check if this marker was already associated with a detection
            already_found = any(
                d.linked_prompt == match.group('name') and
                abs(d.line_number - i) <= 5
                for d in self.detected_prompts
            )

            if already_found:
                continue

            # This is an orphan marker
            detected = DetectedPrompt(
                file_path=self._current_file,
                line_number=i,
                end_line=i,
                prompt_text="",
                detection_type='marker',
                api_type=None,
                function_name=None,
                variable_name=None,
                linked_prompt=match.group('name'),
                version_info=match.group('hash')
            )
            self.detected_prompts.append(detected)

    def _regex_fallback(self, source: str) -> List[DetectedPrompt]:
        """Fallback to regex-based detection for files with syntax errors."""
        prompts = []

        # Pattern for simple LLM calls
        llm_patterns = [
            r'openai\.chat\.completions\.create',
            r'anthropic\.messages\.create',
            r'litellm\.completion',
            r'litellm\.acompletion',
        ]

        for i, line in enumerate(source.splitlines(), 1):
            for pattern in llm_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    prompts.append(DetectedPrompt(
                        file_path=self._current_file,
                        line_number=i,
                        end_line=i,
                        prompt_text=f"LLM call detected (parse error, line {i})",
                        detection_type='llm_call',
                        api_type='unknown',
                        function_name=None,
                        variable_name=None,
                        linked_prompt=None,
                        version_info=None
                    ))
                    break

        return prompts


def scan_python_files(directory: Path, exclude_patterns: Optional[List[str]] = None) -> List[DetectedPrompt]:
    """
    Scan all Python files in a directory for prompts.

    Args:
        directory: Directory to scan
        exclude_patterns: Glob patterns to exclude (e.g., ['**/test_*.py'])

    Returns:
        List of detected prompts
    """
    parser = PythonPromptParser()
    all_prompts = []

    exclude_patterns = exclude_patterns or ['**/__pycache__/**', '**/venv/**', '**/.venv/**']
    exclude_set: Set[Path] = set()

    for pattern in exclude_patterns:
        exclude_set.update(directory.glob(pattern))

    for py_file in directory.rglob('*.py'):
        if py_file in exclude_set:
            continue

        # Skip if any parent is in exclude set
        if any(parent in exclude_set for parent in py_file.parents):
            continue

        prompts = parser.parse_file(py_file)
        all_prompts.extend(prompts)

    return all_prompts
