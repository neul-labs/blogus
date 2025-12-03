"""
JavaScript/TypeScript Parser for detecting LLM API calls.

Uses regex-based parsing to detect common patterns:
- openai.chat.completions.create()
- new Anthropic().messages.create()
- Various SDK patterns for OpenAI, Anthropic, etc.

Note: For more accurate parsing, consider using tree-sitter-javascript
via py-tree-sitter in the future.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Set
import hashlib


@dataclass
class JSDetectedPrompt:
    """A prompt detected in JavaScript/TypeScript source code."""
    file_path: Path
    line_number: int
    end_line: int
    prompt_text: str
    detection_type: str          # 'llm_call', 'marker', 'string_variable'
    api_type: Optional[str]      # 'openai', 'anthropic', 'vercel-ai'
    function_name: Optional[str]
    variable_name: Optional[str]
    linked_prompt: Optional[str]
    version_info: Optional[str]
    messages: List[Dict[str, str]] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        """SHA256 hash of the prompt content."""
        return hashlib.sha256(self.prompt_text.encode()).hexdigest()[:16]


# Regex patterns for detecting LLM API calls in JS/TS
LLM_CALL_PATTERNS = [
    # OpenAI SDK
    (r'openai\.chat\.completions\.create\s*\(', 'openai'),
    (r'\.chat\.completions\.create\s*\(', 'openai'),
    (r'new\s+OpenAI\s*\(', 'openai'),

    # Anthropic SDK
    (r'anthropic\.messages\.create\s*\(', 'anthropic'),
    (r'\.messages\.create\s*\(', 'anthropic'),
    (r'new\s+Anthropic\s*\(', 'anthropic'),

    # Vercel AI SDK
    (r'generateText\s*\(', 'vercel-ai'),
    (r'streamText\s*\(', 'vercel-ai'),
    (r'generateObject\s*\(', 'vercel-ai'),

    # LangChain JS
    (r'ChatOpenAI\s*\(', 'langchain'),
    (r'ChatAnthropic\s*\(', 'langchain'),
    (r'\.invoke\s*\(\s*\[', 'langchain'),

    # Generic patterns
    (r'messages\s*:\s*\[', 'generic'),
    (r'system\s*:\s*[`"\']', 'generic'),
]

# Pattern for @blogus markers in JS comments
MARKER_PATTERN = re.compile(
    r'[@//*]+\s*@blogus:(?P<name>[\w-]+)(?:@v(?P<version>\d+))?\s*(?:sha256:(?P<hash>[a-f0-9]+))?',
    re.IGNORECASE
)

# Pattern to extract string content (handles template literals, single/double quotes)
STRING_PATTERNS = [
    r'`([^`]*)`',           # Template literals
    r'"([^"\\]*(?:\\.[^"\\]*)*)"',  # Double quotes
    r"'([^'\\]*(?:\\.[^'\\]*)*)'",  # Single quotes
]

# Variable name patterns that suggest prompts
PROMPT_VAR_PATTERNS = [
    r'(?:const|let|var)\s+(\w*(?:prompt|system|instruction|message|template)\w*)\s*=',
    r'(?:const|let|var)\s+(\w*(?:PROMPT|SYSTEM|INSTRUCTION|MESSAGE|TEMPLATE)\w*)\s*=',
]


class JSPromptParser:
    """
    Parse JavaScript/TypeScript files to detect LLM API calls.

    Uses regex-based parsing for broad compatibility.
    """

    def __init__(self):
        self.detected_prompts: List[JSDetectedPrompt] = []
        self._current_file: Optional[Path] = None
        self._source_lines: List[str] = []
        self._source: str = ""

    def parse_file(self, file_path: Path) -> List[JSDetectedPrompt]:
        """
        Parse a JavaScript/TypeScript file and detect prompts.

        Args:
            file_path: Path to JS/TS file

        Returns:
            List of detected prompts
        """
        self.detected_prompts = []
        self._current_file = file_path

        try:
            self._source = file_path.read_text(encoding='utf-8')
            self._source_lines = self._source.splitlines()
        except (UnicodeDecodeError, IOError):
            return []

        # Detect LLM API calls
        self._scan_llm_calls()

        # Detect prompt variable assignments
        self._scan_prompt_variables()

        # Scan for @blogus markers
        self._scan_markers()

        return self.detected_prompts

    def parse_string(self, source: str, filename: str = "<string>") -> List[JSDetectedPrompt]:
        """Parse JavaScript/TypeScript source from a string."""
        self.detected_prompts = []
        self._current_file = Path(filename)
        self._source = source
        self._source_lines = source.splitlines()

        self._scan_llm_calls()
        self._scan_prompt_variables()
        self._scan_markers()

        return self.detected_prompts

    def _scan_llm_calls(self) -> None:
        """Scan source for LLM API call patterns."""
        for pattern, api_type in LLM_CALL_PATTERNS:
            for match in re.finditer(pattern, self._source, re.IGNORECASE):
                line_number = self._source[:match.start()].count('\n') + 1

                # Try to extract the full call and its arguments
                call_content, end_line = self._extract_call_block(match.start())

                # Extract messages from the call
                messages = self._extract_messages(call_content)
                prompt_text = self._messages_to_text(messages) if messages else call_content[:200]

                # Check for preceding marker
                marker_info = self._find_preceding_marker(line_number)

                detected = JSDetectedPrompt(
                    file_path=self._current_file,
                    line_number=line_number,
                    end_line=end_line,
                    prompt_text=prompt_text,
                    detection_type='llm_call',
                    api_type=api_type,
                    function_name=self._find_containing_function(line_number),
                    variable_name=None,
                    linked_prompt=marker_info.get('name') if marker_info else None,
                    version_info=marker_info.get('hash') if marker_info else None,
                    messages=messages
                )
                self.detected_prompts.append(detected)

    def _scan_prompt_variables(self) -> None:
        """Scan for variable assignments that look like prompts."""
        for pattern in PROMPT_VAR_PATTERNS:
            for match in re.finditer(pattern, self._source, re.IGNORECASE):
                var_name = match.group(1)
                line_number = self._source[:match.start()].count('\n') + 1

                # Extract the value after the =
                value_start = match.end()
                value_content, end_line = self._extract_string_value(value_start)

                if not value_content or len(value_content) < 20:
                    continue

                # Check for @blogus marker
                marker_info = self._find_preceding_marker(line_number)

                detected = JSDetectedPrompt(
                    file_path=self._current_file,
                    line_number=line_number,
                    end_line=end_line,
                    prompt_text=value_content,
                    detection_type='string_variable',
                    api_type=None,
                    function_name=self._find_containing_function(line_number),
                    variable_name=var_name,
                    linked_prompt=marker_info.get('name') if marker_info else None,
                    version_info=marker_info.get('hash') if marker_info else None
                )
                self.detected_prompts.append(detected)

    def _scan_markers(self) -> None:
        """Scan all comments for @blogus markers."""
        for i, line in enumerate(self._source_lines, 1):
            if '//' not in line and '/*' not in line:
                continue

            match = MARKER_PATTERN.search(line)
            if not match:
                continue

            # Check if already associated with a detection
            already_found = any(
                d.linked_prompt == match.group('name') and
                abs(d.line_number - i) <= 5
                for d in self.detected_prompts
            )

            if already_found:
                continue

            detected = JSDetectedPrompt(
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

    def _extract_call_block(self, start_pos: int) -> tuple:
        """Extract the full function call including its arguments."""
        # Find the opening parenthesis
        paren_start = self._source.find('(', start_pos)
        if paren_start == -1:
            return "", self._source[:start_pos].count('\n') + 1

        # Match balanced parentheses
        depth = 0
        pos = paren_start
        while pos < len(self._source):
            char = self._source[pos]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    break
            pos += 1

        content = self._source[paren_start:pos + 1]
        end_line = self._source[:pos].count('\n') + 1
        return content, end_line

    def _extract_string_value(self, start_pos: int) -> tuple:
        """Extract string value starting from a position."""
        # Look for template literal, double or single quoted string
        remaining = self._source[start_pos:start_pos + 2000]  # Limit search

        for pattern in STRING_PATTERNS:
            match = re.match(r'\s*' + pattern, remaining, re.DOTALL)
            if match:
                content = match.group(1)
                end_pos = start_pos + match.end()
                end_line = self._source[:end_pos].count('\n') + 1
                return content, end_line

        return "", self._source[:start_pos].count('\n') + 1

    def _extract_messages(self, call_content: str) -> List[Dict[str, str]]:
        """Extract messages array from a call's arguments."""
        messages = []

        # Look for messages: [ ... ] pattern
        messages_match = re.search(
            r'messages\s*:\s*\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]',
            call_content,
            re.DOTALL
        )

        if not messages_match:
            return messages

        messages_content = messages_match.group(1)

        # Parse individual message objects
        msg_pattern = re.compile(
            r'\{\s*role\s*:\s*["\'](\w+)["\']\s*,\s*content\s*:\s*([`"\'])(.+?)\2\s*\}',
            re.DOTALL
        )

        for match in msg_pattern.finditer(messages_content):
            role = match.group(1)
            content = match.group(3)
            messages.append({'role': role, 'content': content})

        return messages

    def _messages_to_text(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages list to readable text."""
        parts = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            parts.append(f"[{role}] {content}")
        return '\n'.join(parts)

    def _find_containing_function(self, line_number: int) -> Optional[str]:
        """Find the function containing the given line."""
        # Look for function declarations above the line
        patterns = [
            r'(?:async\s+)?function\s+(\w+)',
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>',
            r'(\w+)\s*:\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)',
        ]

        for i in range(line_number - 1, max(0, line_number - 50), -1):
            if i >= len(self._source_lines):
                continue
            line = self._source_lines[i]

            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)

        return None

    def _find_preceding_marker(self, line_number: int) -> Optional[Dict[str, str]]:
        """Find @blogus marker in comments above the given line."""
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


def scan_js_files(directory: Path, exclude_patterns: Optional[List[str]] = None) -> List[JSDetectedPrompt]:
    """
    Scan all JavaScript/TypeScript files in a directory for prompts.

    Args:
        directory: Directory to scan
        exclude_patterns: Glob patterns to exclude

    Returns:
        List of detected prompts
    """
    parser = JSPromptParser()
    all_prompts = []

    exclude_patterns = exclude_patterns or [
        '**/node_modules/**',
        '**/dist/**',
        '**/build/**',
        '**/.next/**',
        '**/coverage/**'
    ]
    exclude_set: Set[Path] = set()

    for pattern in exclude_patterns:
        exclude_set.update(directory.glob(pattern))

    # Scan .js, .ts, .jsx, .tsx files
    extensions = ['*.js', '*.ts', '*.jsx', '*.tsx', '*.mjs', '*.mts']

    for ext in extensions:
        for js_file in directory.rglob(ext):
            if js_file in exclude_set:
                continue
            if any(parent in exclude_set for parent in js_file.parents):
                continue

            prompts = parser.parse_file(js_file)
            all_prompts.extend(prompts)

    return all_prompts
