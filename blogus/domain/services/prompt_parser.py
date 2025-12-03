"""
Parser for .prompt files.

.prompt files use YAML frontmatter for metadata and support multi-turn
conversation blocks using <system>, <user>, <assistant> tags.

Example:
---
name: customer-support
description: Customer support agent
model:
  id: gpt-4o
  temperature: 0.7
---

<system>
You are a helpful assistant.
</system>

<user>
{{user_input}}
</user>
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re
import yaml
import hashlib


@dataclass
class PromptVariable:
    """Definition of a template variable."""
    name: str
    description: str = ""
    required: bool = True
    default: Optional[str] = None
    enum: Optional[List[str]] = None


@dataclass
class ModelConfig:
    """Model configuration from .prompt file."""
    id: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0


@dataclass
class PromptMetadata:
    """Metadata parsed from .prompt file frontmatter."""
    name: str
    description: str = ""
    author: str = "unknown"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    model: ModelConfig = field(default_factory=ModelConfig)
    goal: Optional[str] = None
    variables: List[PromptVariable] = field(default_factory=list)


@dataclass
class ConversationBlock:
    """A block in a multi-turn conversation."""
    role: str  # system, user, assistant
    content: str


@dataclass
class ParsedPromptFile:
    """Result of parsing a .prompt file."""
    metadata: PromptMetadata
    content: str                          # Raw content section (after frontmatter)
    blocks: List[ConversationBlock]       # Parsed conversation blocks
    content_hash: str                     # SHA256 of content
    raw_text: str                         # Original file content
    file_path: Optional[Path] = None


class PromptParseError(Exception):
    """Error during .prompt file parsing."""
    pass


class PromptParser:
    """Parser for .prompt files."""

    # Pattern to match YAML frontmatter (--- at start and end)
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.DOTALL
    )

    # Pattern to match conversation blocks like <system>...</system>
    BLOCK_PATTERN = re.compile(
        r'<(system|user|assistant)>\s*(.*?)\s*</\1>',
        re.DOTALL | re.IGNORECASE
    )

    # Pattern to extract Handlebars variables
    VARIABLE_PATTERN = re.compile(r'\{\{\s*(\w+)\s*\}\}')

    # Pattern for Handlebars conditionals
    CONDITIONAL_PATTERN = re.compile(r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}', re.DOTALL)

    def parse_file(self, path: Path) -> ParsedPromptFile:
        """
        Parse a .prompt file.

        Args:
            path: Path to the .prompt file

        Returns:
            ParsedPromptFile with metadata and content

        Raises:
            PromptParseError: If parsing fails
        """
        if not path.exists():
            raise PromptParseError(f"File not found: {path}")

        if not path.suffix == '.prompt':
            raise PromptParseError(f"Expected .prompt file, got: {path.suffix}")

        try:
            raw_text = path.read_text(encoding='utf-8')
        except Exception as e:
            raise PromptParseError(f"Failed to read file: {e}")

        result = self.parse_string(raw_text)
        result.file_path = path
        return result

    def parse_string(self, text: str) -> ParsedPromptFile:
        """
        Parse .prompt content from string.

        Args:
            text: Raw .prompt file content

        Returns:
            ParsedPromptFile with metadata and content
        """
        # Parse frontmatter
        metadata, content = self._parse_frontmatter(text)

        # Parse conversation blocks
        blocks = self._parse_blocks(content)

        # Calculate content hash (of the content section only)
        content_hash = self._calculate_hash(content)

        return ParsedPromptFile(
            metadata=metadata,
            content=content,
            blocks=blocks,
            content_hash=content_hash,
            raw_text=text
        )

    def _parse_frontmatter(self, text: str) -> Tuple[PromptMetadata, str]:
        """Parse YAML frontmatter and return metadata + remaining content."""
        match = self.FRONTMATTER_PATTERN.match(text)

        if not match:
            # No frontmatter, use defaults
            return PromptMetadata(name="untitled"), text.strip()

        yaml_text = match.group(1)
        content = text[match.end():].strip()

        try:
            data = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError as e:
            raise PromptParseError(f"Invalid YAML frontmatter: {e}")

        metadata = self._parse_metadata(data)
        return metadata, content

    def _parse_metadata(self, data: Dict[str, Any]) -> PromptMetadata:
        """Parse metadata dictionary into PromptMetadata."""
        # Parse model config
        model_data = data.get('model', {})
        if isinstance(model_data, str):
            model_config = ModelConfig(id=model_data)
        elif isinstance(model_data, dict):
            model_config = ModelConfig(
                id=model_data.get('id', 'gpt-4o'),
                temperature=float(model_data.get('temperature', 0.7)),
                max_tokens=int(model_data.get('max_tokens', 1000)),
                top_p=float(model_data.get('top_p', 1.0))
            )
        else:
            model_config = ModelConfig()

        # Parse variables
        variables = []
        var_data = data.get('variables', [])
        if isinstance(var_data, list):
            for v in var_data:
                if isinstance(v, dict):
                    variables.append(PromptVariable(
                        name=v.get('name', ''),
                        description=v.get('description', ''),
                        required=v.get('required', True),
                        default=v.get('default'),
                        enum=v.get('enum')
                    ))
                elif isinstance(v, str):
                    variables.append(PromptVariable(name=v))

        # Parse tags
        tags = data.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        # Parse goal (can be multiline)
        goal = data.get('goal')
        if isinstance(goal, str):
            goal = goal.strip()

        return PromptMetadata(
            name=data.get('name', 'untitled'),
            description=data.get('description', ''),
            author=data.get('author', 'unknown'),
            category=data.get('category', 'general'),
            tags=tags,
            model=model_config,
            goal=goal,
            variables=variables
        )

    def _parse_blocks(self, content: str) -> List[ConversationBlock]:
        """Parse conversation blocks from content."""
        blocks = []

        for match in self.BLOCK_PATTERN.finditer(content):
            role = match.group(1).lower()
            block_content = match.group(2).strip()
            blocks.append(ConversationBlock(role=role, content=block_content))

        # If no blocks found, treat entire content as a single user message
        if not blocks and content.strip():
            blocks.append(ConversationBlock(role='user', content=content.strip()))

        return blocks

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def extract_variables(self, content: str) -> List[str]:
        """Extract variable names from content."""
        matches = self.VARIABLE_PATTERN.findall(content)
        # Preserve order, remove duplicates
        seen = set()
        result = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                result.append(var)
        return result

    def render(self, content: str, values: Dict[str, str]) -> str:
        """
        Render prompt content with variable substitution.

        Supports:
        - Simple variables: {{variable_name}}
        - Conditionals: {{#if variable}}...{{/if}}
        """
        result = content

        # Handle conditionals first
        def replace_conditional(match):
            var_name = match.group(1)
            inner = match.group(2)
            if var_name in values and values[var_name]:
                return inner
            return ''

        result = self.CONDITIONAL_PATTERN.sub(replace_conditional, result)

        # Then substitute variables
        for var_name, var_value in values.items():
            pattern = rf'\{{\{{\s*{re.escape(var_name)}\s*\}}\}}'
            result = re.sub(pattern, str(var_value), result)

        return result

    def to_messages(
        self,
        blocks: List[ConversationBlock],
        values: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """
        Convert conversation blocks to LLM message format.

        Args:
            blocks: List of ConversationBlock
            values: Optional variable values for rendering

        Returns:
            List of {"role": "...", "content": "..."} dicts
        """
        messages = []
        for block in blocks:
            content = block.content
            if values:
                content = self.render(content, values)
            messages.append({
                "role": block.role,
                "content": content
            })
        return messages

    def write_file(
        self,
        path: Path,
        metadata: PromptMetadata,
        content: str
    ) -> None:
        """
        Write a .prompt file.

        Args:
            path: Output path
            metadata: Prompt metadata
            content: Prompt content (may include conversation blocks)
        """
        # Build YAML frontmatter
        frontmatter = {
            'name': metadata.name,
            'description': metadata.description,
            'author': metadata.author,
            'category': metadata.category,
            'tags': metadata.tags,
        }

        if metadata.goal:
            frontmatter['goal'] = metadata.goal

        # Model config
        frontmatter['model'] = {
            'id': metadata.model.id,
            'temperature': metadata.model.temperature,
            'max_tokens': metadata.model.max_tokens,
        }

        # Variables
        if metadata.variables:
            frontmatter['variables'] = [
                {
                    'name': v.name,
                    'description': v.description,
                    'required': v.required,
                    **(({'default': v.default} if v.default else {})),
                    **(({'enum': v.enum} if v.enum else {}))
                }
                for v in metadata.variables
            ]

        # Write file
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        output = f"---\n{yaml_str}---\n\n{content}"

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding='utf-8')


# Convenience function
def parse_prompt_file(path: Path) -> ParsedPromptFile:
    """Parse a .prompt file."""
    parser = PromptParser()
    return parser.parse_file(path)
