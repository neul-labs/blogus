# Getting Started

## Quick Try

```bash
uvx blogus scan
```

## Install

```bash
uv add blogus
```

For web interface:
```bash
uv add blogus[web]
```

## API Keys

```bash
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
```

## First Scan

### 1. Scan Your Project

```bash
$ blogus scan

Found 3 LLM API calls:
  src/chat.py:15         OpenAI      unversioned
  src/summarize.py:42    OpenAI      unversioned
  lib/translate.js:28    Anthropic   unversioned
```

### 2. Initialize

```bash
$ blogus init
```

Creates `prompts/` directory.

### 3. Create a .prompt File

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

### 4. Test It

```bash
$ blogus exec summarize --var text="Your text here..."
```

### 5. Lock Versions

```bash
$ blogus lock
```

### 6. Sync Code

```bash
$ blogus fix --dry-run  # Preview
$ blogus fix            # Apply
```

### 7. Verify in CI

```bash
$ blogus verify || exit 1
```

## Next Steps

- [Core Concepts](core_concepts.md) - How it all works
- [.prompt Format](prompt_files.md) - File format reference
- [CLI Reference](cli.md) - All commands
- [Web Interface](web_interface.md) - Visual management
