# Blogus

**Extract, test, version, and sync AI prompts across your codebase.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/blogus.svg)](https://badge.fury.io/py/blogus)

## The Problem

Prompts are scattered as string literals throughout your code. They're hard to find, impossible to test systematically, and when you improve one, you have to manually update every place it's used.

## The Solution

Blogus provides a complete prompt engineering workflow:

1. **Extract** - Scan your codebase to discover all LLM API calls and their prompts
2. **Test** - Analyze prompts for effectiveness, generate test cases, validate across models
3. **Version** - Store prompts in `.prompt` files with full Git history
4. **Update** - When you improve a `.prompt` file, sync changes back to your code

## Quick Start

```bash
pip install blogus
```

### Step 1: Extract Prompts

Scan your project to find all LLM API calls:

```bash
blogus scan
```

```
Scanning project...

Found 4 LLM API calls:

  src/summarizer.py:42     OpenAI      "Summarize this text..."
  src/chat.py:15           OpenAI      "You are a helpful assistant..."
  src/review.py:88         Anthropic   "Review this code for bugs..."
  lib/translate.js:28      OpenAI      "Translate from {{source}} to..."

Run 'blogus init' to create prompt files.
```

### Step 2: Create Prompt Files

```bash
blogus init
```

Convert discovered prompts into versioned `.prompt` files:

```yaml
# prompts/summarize.prompt
---
name: summarize
description: Summarize text concisely
model:
  id: gpt-4o
  temperature: 0.3
variables:
  - name: text
    required: true
---

Summarize the following text in 2-3 sentences:

{{text}}
```

### Step 3: Test Prompts

Analyze effectiveness and generate test cases:

```bash
# Analyze a prompt
blogus analyze prompts/summarize.prompt

# Generate test cases
blogus test prompts/summarize.prompt

# Execute with variables
blogus exec summarize --var text="Long article content here..."
```

### Step 4: Version with Lock File

Lock prompt versions for reproducible deployments:

```bash
blogus lock
```

Generates `prompts.lock`:
```yaml
version: 1
prompts:
  summarize:
    hash: sha256:a1b2c3d4e5f6...
    commit: 4903f76
  code-review:
    hash: sha256:b2c3d4e5f6a7...
    commit: 4903f76
```

Verify in CI:
```bash
blogus verify || exit 1
```

### Step 5: Update Inline Code

When you improve a `.prompt` file, sync changes back to your source code:

```bash
# See what would change
blogus fix --dry-run

# Apply updates
blogus fix
```

Before:
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Summarize: " + text}]
)
```

After:
```python
# @blogus:summarize@v2 sha256:a1b2c3d4
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": load_prompt("summarize", text=text)}]
)
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `blogus scan` | Extract all LLM API calls from your codebase |
| `blogus init` | Create prompts directory and sample files |
| `blogus prompts` | List all .prompt files with status |
| `blogus analyze <prompt>` | Analyze prompt effectiveness |
| `blogus test <prompt>` | Generate test cases for a prompt |
| `blogus exec <name>` | Execute a prompt with variables |
| `blogus check` | Find code using unversioned prompts |
| `blogus fix` | Update inline code when .prompt files change |
| `blogus lock` | Generate prompts.lock file |
| `blogus verify` | Verify prompts match lock file (for CI) |

## Web Interface

```bash
pip install blogus[web]
blogus-web
```

Visual interface at `http://localhost:8000`:
- **Prompt Library** - Browse and edit all .prompt files
- **Project Scanner** - Visualize extracted prompts from code
- **Analysis Dashboard** - Test and analyze prompts
- **Git Integration** - Commit changes directly from UI

## .prompt File Format

```yaml
---
name: code-review
description: Review code for quality and bugs
model:
  id: gpt-4o
  temperature: 0.3
  max_tokens: 2000
variables:
  - name: language
    description: Programming language
    required: true
  - name: code
    description: Code to review
    required: true
  - name: focus
    description: Areas to focus on
    required: false
    default: "bugs, performance, readability"
---

Review this {{language}} code:

```{{language}}
{{code}}
```

Focus on: {{focus}}

Provide specific, actionable feedback.
```

## The Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EXTRACT   │────▶│    TEST     │────▶│   VERSION   │────▶│   UPDATE    │
│             │     │             │     │             │     │             │
│ blogus scan │     │ blogus test │     │ blogus lock │     │ blogus fix  │
│             │     │ blogus      │     │ blogus      │     │             │
│ Find all    │     │   analyze   │     │   verify    │     │ Sync back   │
│ LLM calls   │     │             │     │             │     │ to code     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Documentation

- [Getting Started](docs/getting_started.md) - Installation and setup
- [Core Concepts](docs/core_concepts.md) - Extract, test, version, update
- [Prompt Files](docs/prompt_files.md) - .prompt format reference
- [CLI Reference](docs/cli.md) - All commands
- [Web Interface](docs/web_interface.md) - Web UI guide

## License

MIT - See [LICENSE](LICENSE)
