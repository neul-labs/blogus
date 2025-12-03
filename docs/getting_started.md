# Getting Started

This guide walks you through setting up Blogus and running your first prompt extraction.

## Try Without Installing

Use `uvx` to run Blogus directly from PyPI:

```bash
# Scan your project
uvx blogus scan

# Run any command
uvx blogus --help
```

## Installation

```bash
uv add blogus
```

For web interface:
```bash
uv add blogus[web]
```

## API Keys

Set environment variables for the LLM providers you use:

```bash
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
```

## Your First Extraction

### 1. Scan Your Project

Navigate to your project and run:

```bash
blogus scan
```

Blogus finds all LLM API calls in Python and JavaScript files:

```
Scanning project...

Found 3 LLM API calls:

  src/chat.py:15         OpenAI      "You are a helpful..."
  src/summarize.py:42    OpenAI      "Summarize this text..."
  lib/translate.js:28    Anthropic   "Translate from..."

Run 'blogus init' to create prompt files.
```

### 2. Initialize Prompt Files

```bash
blogus init
```

This creates a `prompts/` directory with sample files. Now create `.prompt` files for your discovered prompts:

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

### 3. Test Your Prompt

```bash
# Analyze effectiveness
blogus analyze prompts/summarize.prompt

# Generate test cases
blogus test prompts/summarize.prompt

# Execute with a variable
blogus exec summarize --var text="Your long text here..."
```

### 4. Lock Versions

```bash
blogus lock
```

This generates `prompts.lock` with content hashes for each prompt.

### 5. Link Code to Prompts

Update your code to use the versioned prompt:

```python
from blogus import load_prompt

# @blogus:summarize
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": load_prompt("summarize", text=text)}]
)
```

### 6. Keep Code in Sync

When you improve a `.prompt` file, sync changes:

```bash
blogus fix --dry-run  # Preview
blogus fix            # Apply
```

## Verify in CI

Add to your CI pipeline:

```bash
blogus verify || exit 1
```

This fails the build if prompts have changed without updating the lock file.

## Next Steps

- [Core Concepts](core_concepts.md) - Understand extraction, versioning, syncing
- [Prompt Files](prompt_files.md) - Full `.prompt` format reference
- [CLI Reference](cli.md) - All commands
- [Web Interface](web_interface.md) - Visual prompt management
