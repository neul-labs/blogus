"""
Demo project setup for Blogus TUI demo.

Creates a temporary sample project with various prompt patterns
for demonstrating Blogus capabilities.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Optional

# Template files for the demo project

PROMPT_SUMMARIZE = '''---
name: summarize
description: Summarize documents concisely
model:
  id: gpt-4o-mini
  temperature: 0.3
variables:
  - name: content
    required: true
    description: The content to summarize
  - name: length
    required: false
    default: "2-3 paragraphs"
    description: Desired summary length
---
You are an expert summarizer. Create a clear, concise summary of the following content.

Content to summarize:
{{content}}

Provide a summary in {{length}}. Focus on the key points and main ideas.
'''

PROMPT_CODE_REVIEW = '''---
name: code-review
description: Review code for bugs and improvements
model:
  id: gpt-4o
  temperature: 0.2
variables:
  - name: code
    required: true
    description: The code to review
  - name: language
    required: false
    default: "python"
    description: Programming language
---
You are a senior software engineer conducting a code review.

Review this {{language}} code:

```{{language}}
{{code}}
```

Provide feedback on:
1. Potential bugs or errors
2. Code quality and readability
3. Performance considerations
4. Security concerns
5. Suggested improvements

Rate the overall code quality from 1-10.
'''

PROMPT_TRANSLATE = '''---
name: translate
description: Translate text between languages
model:
  id: gpt-4o-mini
  temperature: 0.1
variables:
  - name: text
    required: true
  - name: target_language
    required: true
---
Translate the following text to {{target_language}}.

Text: {{text}}

Provide only the translation, no explanations.
'''

CHAT_HANDLER_PY = '''"""Chat handler with tracked OpenAI calls."""
from openai import OpenAI

client = OpenAI()


# @blogus:chat-assistant sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234
def handle_chat(user_message: str) -> str:
    """Handle a chat message from the user."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides accurate and concise answers."
            },
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content
'''

SUPPORT_BOT_PY = '''"""Support bot - prompts NOT tracked (demo target for fix)."""
from anthropic import Anthropic

client = Anthropic()


def answer_support_question(question: str, context: str = "") -> str:
    """Answer a customer support question."""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a helpful customer support agent for a software company.
Answer the following question concisely and helpfully.

Context: {context}

Customer Question: {question}

Provide a friendly, professional response."""
            }
        ]
    )
    return response.content[0].text


def escalate_issue(issue_description: str) -> str:
    """Determine if an issue should be escalated."""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this customer issue and determine if it needs escalation.

Issue: {issue_description}

Respond with:
- ESCALATE: [reason] if it needs human attention
- RESOLVED: [suggested solution] if it can be handled automatically"""
            }
        ]
    )
    return response.content[0].text
'''

SUMMARIZER_PY = '''"""Summarizer service using managed prompt."""
from pathlib import Path


# @blogus:summarize sha256:matching_hash_placeholder_for_demo
def summarize_document(document: str, length: str = "2-3 paragraphs") -> str:
    """Summarize a document using the managed prompt."""
    # In real usage, this would load and execute the prompt
    # For demo purposes, this shows the pattern
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "summarize.prompt"

    # Load prompt template and render with variables
    # ... prompt execution logic ...

    return f"[Summary of document in {length}]"
'''

REVIEWER_PY = '''"""Code reviewer with inline prompt (not managed)."""
from openai import OpenAI

client = OpenAI()


def review_code(code: str, language: str = "python") -> str:
    """Review code for bugs and improvements."""
    # This inline prompt is NOT managed by Blogus yet
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Review this {language} code:

```{language}
{code}
```

Identify potential bugs, suggest improvements, and rate code quality 1-10."""
            }
        ],
        temperature=0.3,
        max_tokens=1000
    )
    return response.choices[0].message.content


def suggest_refactoring(code: str) -> str:
    """Suggest refactoring improvements for code."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this code and suggest refactoring improvements:

{code}

Focus on:
- Code organization
- Design patterns
- Maintainability"""
            }
        ]
    )
    return response.choices[0].message.content
'''

TRANSLATOR_PY = '''"""Translator service using managed prompt."""


# @blogus:translate sha256:another_hash_placeholder_demo
def translate_text(text: str, target_language: str) -> str:
    """Translate text to target language using managed prompt."""
    # Uses the translate.prompt file
    return f"[Translated to {target_language}]"
'''

PROMPTS_UTILS_PY = '''"""Prompt constants and utilities."""

# Common system prompts used across the application
ASSISTANT_PERSONA = """You are a helpful AI assistant. You provide accurate,
concise, and friendly responses. When you don\'t know something, you say so
rather than making up information."""

FORMATTING_INSTRUCTIONS = """Format your response using markdown:
- Use headers for sections
- Use bullet points for lists
- Use code blocks for code
- Keep paragraphs short and readable"""
'''

ANALYZE_DOCS_JS = '''// Document analyzer using Claude
import Anthropic from \'@anthropic-ai/sdk\';

const client = new Anthropic();

// @blogus:doc-analyzer sha256:f7g8h9i0j1k2l3m4n5o6p7q8r9s0
async function analyzeDocument(content) {
  const message = await client.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 1024,
    messages: [
      {
        role: "user",
        content: `Analyze this document and extract key themes:

${content}

Provide:
1. Main themes (3-5)
2. Key insights
3. Suggested actions`
      }
    ]
  });
  return message.content[0].text;
}

async function generateSummary(documents) {
  // Another prompt that IS tracked
  const message = await client.messages.create({
    model: "claude-3-haiku-20240307",
    max_tokens: 500,
    messages: [
      {
        role: "user",
        content: `Summarize these documents briefly: ${documents.join("\\n---\\n")}`
      }
    ]
  });
  return message.content[0].text;
}

export { analyzeDocument, generateSummary };
'''

LOCK_FILE = '''{
  "version": 1,
  "prompts": {
    "summarize": {
      "version": "v1",
      "content_hash": "matching_hash_placeholder_for_demo",
      "commit_sha": null,
      "file": "prompts/summarize.prompt"
    },
    "code-review": {
      "version": "v1",
      "content_hash": "code_review_hash_placeholder",
      "commit_sha": null,
      "file": "prompts/code-review.prompt"
    },
    "translate": {
      "version": "v1",
      "content_hash": "another_hash_placeholder_demo",
      "commit_sha": null,
      "file": "prompts/translate.prompt"
    }
  }
}
'''

README_MD = '''# Demo Project

This is a sample project for demonstrating Blogus capabilities.

## Structure

- `prompts/` - Managed prompt files
- `src/api/` - API handlers with LLM calls
- `src/services/` - Business logic services
- `scripts/` - Utility scripts

## Prompt Status

- 3 managed prompts in `prompts/`
- 2 tracked API calls
- 3 untracked API calls (for demo)
'''


def setup_demo_project(base_path: Optional[Path] = None) -> Path:
    """
    Create a demo project with sample files for Blogus demo.

    Args:
        base_path: Optional base path for the demo project.
                   If None, creates in system temp directory.

    Returns:
        Path to the created demo project
    """
    if base_path is None:
        base_path = Path(tempfile.mkdtemp(prefix="blogus_demo_"))
    else:
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    dirs = [
        ".blogus",
        "prompts",
        "src/api",
        "src/services",
        "src/utils",
        "scripts",
    ]
    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)

    # Write prompt files
    (base_path / "prompts" / "summarize.prompt").write_text(PROMPT_SUMMARIZE)
    (base_path / "prompts" / "code-review.prompt").write_text(PROMPT_CODE_REVIEW)
    (base_path / "prompts" / "translate.prompt").write_text(PROMPT_TRANSLATE)

    # Write Python source files
    (base_path / "src" / "api" / "__init__.py").write_text("")
    (base_path / "src" / "api" / "chat_handler.py").write_text(CHAT_HANDLER_PY)
    (base_path / "src" / "api" / "support_bot.py").write_text(SUPPORT_BOT_PY)

    (base_path / "src" / "services" / "__init__.py").write_text("")
    (base_path / "src" / "services" / "summarizer.py").write_text(SUMMARIZER_PY)
    (base_path / "src" / "services" / "reviewer.py").write_text(REVIEWER_PY)
    (base_path / "src" / "services" / "translator.py").write_text(TRANSLATOR_PY)

    (base_path / "src" / "utils" / "__init__.py").write_text("")
    (base_path / "src" / "utils" / "prompts.py").write_text(PROMPTS_UTILS_PY)

    (base_path / "src" / "__init__.py").write_text("")

    # Write JavaScript file
    (base_path / "scripts" / "analyze_docs.js").write_text(ANALYZE_DOCS_JS)

    # Write lock file
    (base_path / ".blogus" / "prompts.lock").write_text(LOCK_FILE)

    # Write README
    (base_path / "README.md").write_text(README_MD)

    return base_path


def cleanup_demo_project(project_path: Path) -> None:
    """
    Clean up a demo project directory.

    Args:
        project_path: Path to the demo project to remove
    """
    if project_path.exists() and "blogus_demo_" in str(project_path):
        shutil.rmtree(project_path)


def get_demo_prompts_summary() -> dict:
    """
    Get a summary of prompts in the demo project.

    Returns:
        Dict with prompt statistics and details
    """
    return {
        "managed_prompts": [
            {"name": "summarize", "model": "gpt-4o-mini", "has_variables": True},
            {"name": "code-review", "model": "gpt-4o", "has_variables": True},
            {"name": "translate", "model": "gpt-4o-mini", "has_variables": True},
        ],
        "tracked_calls": [
            {"file": "src/api/chat_handler.py", "api": "openai", "linked": "chat-assistant"},
            {"file": "src/services/summarizer.py", "api": "local", "linked": "summarize"},
            {"file": "src/services/translator.py", "api": "local", "linked": "translate"},
            {"file": "scripts/analyze_docs.js", "api": "anthropic", "linked": "doc-analyzer"},
        ],
        "untracked_calls": [
            {"file": "src/api/support_bot.py", "api": "anthropic", "count": 2},
            {"file": "src/services/reviewer.py", "api": "openai", "count": 2},
        ],
    }
