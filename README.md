# Blogus

**`package.lock` for AI prompts.**

Extract prompts from your codebase, version them like dependencies, and keep everything in sync.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/blogus.svg)](https://badge.fury.io/py/blogus)

## Why Blogus?

| Approach | Discover | Version | Test | Sync | Lock |
|----------|:--------:|:-------:|:----:|:----:|:----:|
| Inline strings | - | - | - | - | - |
| Manual .txt files | - | Git | - | Manual | - |
| LangChain Hub | - | Yes | - | Manual | - |
| PromptLayer / Humanloop | - | Yes | Yes | Manual | - |
| **Blogus** | **Auto** | **Git** | **Yes** | **Auto** | **Yes** |

**Blogus is different because it:**
- **Extracts** prompts from your existing code (no migration required)
- **Locks** versions with content hashes (like `package.lock`)
- **Syncs** changes back to your source files automatically

## Quick Start

```bash
# Try it now
uvx blogus scan

# Install
uv add blogus
```

### 1. Extract

Find all LLM calls in your codebase:

```bash
$ blogus scan

Found 3 LLM API calls:
  src/chat.py:15         OpenAI      unversioned
  src/summarize.py:42    OpenAI      unversioned
  lib/translate.js:28    Anthropic   unversioned
```

### 2. Version

Create `.prompt` files:

```bash
$ blogus init
```

```yaml
# prompts/summarize.prompt
---
name: summarize
model:
  id: gpt-4o
  temperature: 0.3
variables:
  - name: text
    required: true
---
Summarize in 2-3 sentences: {{text}}
```

### 3. Lock

Generate a lock file:

```bash
$ blogus lock
```

```yaml
# prompts.lock
prompts:
  summarize:
    hash: sha256:a1b2c3d4...
    commit: 4903f76
```

### 4. Sync

Update your code when prompts change:

```bash
$ blogus fix
```

```python
# Before
content = "Summarize: " + text

# After
# @blogus:summarize sha256:a1b2c3d4
content = load_prompt("summarize", text=text)
```

### 5. Verify (CI)

```bash
$ blogus verify || exit 1
```

## Commands

| Command | Description |
|---------|-------------|
| `scan` | Find LLM API calls in your code |
| `init` | Create prompts directory |
| `prompts` | List all .prompt files |
| `exec <name>` | Run a prompt with variables |
| `analyze` | Evaluate prompt effectiveness |
| `test` | Generate test cases |
| `lock` | Generate prompts.lock |
| `verify` | Check lock file (for CI) |
| `check` | Find unversioned prompts |
| `fix` | Sync code with .prompt files |

## Web UI

```bash
uvx --with blogus[web] blogus-web
```

Browse prompts, scan projects, and commit changes at `http://localhost:8000`.

## .prompt Format

```yaml
---
name: code-review
description: Review code for bugs
model:
  id: gpt-4o
  temperature: 0.3
variables:
  - name: code
    required: true
  - name: language
    default: python
---
Review this {{language}} code for bugs:

{{code}}
```

## How It Works

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  SCAN    │───▶│  VERSION │───▶│   LOCK   │───▶│   SYNC   │
│          │    │          │    │          │    │          │
│ Find LLM │    │ .prompt  │    │ prompts  │    │ Update   │
│ calls    │    │ files    │    │ .lock    │    │ code     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Documentation

- [Getting Started](docs/getting_started.md)
- [Core Concepts](docs/core_concepts.md)
- [.prompt Format](docs/prompt_files.md)
- [CLI Reference](docs/cli.md)
- [Web Interface](docs/web_interface.md)

## License

MIT
