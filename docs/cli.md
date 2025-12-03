# CLI Reference

Complete reference for all Blogus commands.

## Overview

```bash
blogus [command] [options]
```

Commands are organized by the workflow: **Extract → Test → Version → Update**.

## Extract Commands

### scan

Find all LLM API calls in your codebase.

```bash
blogus scan [OPTIONS]
```

Options:
- `--path PATH` - Project path to scan (default: current directory)
- `--python/--no-python` - Include Python files (default: yes)
- `--js/--no-js` - Include JavaScript/TypeScript files (default: yes)

Example:
```bash
blogus scan
blogus scan --path ./src --python --no-js
```

Output:
```
Found 3 LLM API calls:

  src/chat.py:15         OpenAI      versioned    @blogus:chat
  src/summarize.py:42    OpenAI      unversioned
  lib/translate.js:28    Anthropic   unversioned
```

### init

Create a prompts directory with sample files.

```bash
blogus init [OPTIONS]
```

Options:
- `--path PATH` - Path to initialize (default: current directory)

Example:
```bash
blogus init
```

Creates:
```
prompts/
├── example.prompt
└── README.md
```

## Test Commands

### analyze

Analyze a prompt for effectiveness.

```bash
blogus analyze [OPTIONS] PROMPT
```

Options:
- `--target-model MODEL` - Model for execution
- `--judge-model MODEL` - Model for analysis
- `--goal TEXT` - Explicit goal (inferred if not provided)

Example:
```bash
blogus analyze "You are a helpful assistant."
blogus analyze prompts/summarize.prompt --judge-model gpt-4o
```

### test

Generate test cases for a prompt.

```bash
blogus test [OPTIONS] PROMPT
```

Options:
- `--target-model MODEL` - Model for execution
- `--judge-model MODEL` - Model for test generation
- `--goal TEXT` - Explicit goal

Example:
```bash
blogus test prompts/summarize.prompt
blogus test "Translate {text} to French" --judge-model gpt-4o
```

### exec

Execute a .prompt file with variables.

```bash
blogus exec [OPTIONS] PROMPT_NAME
```

Options:
- `--var KEY=VALUE` - Variable substitution (repeatable)
- `--model MODEL` - Override model from prompt file

Example:
```bash
blogus exec summarize --var text="Long article..."
blogus exec code-review --var language=python --var code="def foo(): pass"
```

### execute

Execute a raw prompt string.

```bash
blogus execute [OPTIONS] PROMPT
```

Options:
- `--target-model MODEL` - Model to use

Example:
```bash
blogus execute "Explain quantum computing" --target-model gpt-4o
```

### goal

Infer the goal of a prompt.

```bash
blogus goal [OPTIONS] PROMPT
```

Options:
- `--judge-model MODEL` - Model for analysis

Example:
```bash
blogus goal "You are a Python tutor."
```

### fragments

Analyze prompt fragments for goal alignment.

```bash
blogus fragments [OPTIONS] PROMPT
```

Options:
- `--target-model MODEL` - Model for execution
- `--judge-model MODEL` - Model for analysis
- `--goal TEXT` - Explicit goal

Example:
```bash
blogus fragments "You are a helpful assistant. Be concise." --judge-model gpt-4o
```

## Version Commands

### prompts

List all .prompt files in the project.

```bash
blogus prompts [OPTIONS]
```

Options:
- `--path PATH` - Project path
- `--category TEXT` - Filter by category
- `--dirty` - Show only modified files

Example:
```bash
blogus prompts
blogus prompts --dirty
blogus prompts --category development
```

### lock

Generate prompts.lock file with content hashes.

```bash
blogus lock [OPTIONS]
```

Options:
- `--path PATH` - Project path
- `--output FILE` - Output file (default: prompts.lock)

Example:
```bash
blogus lock
blogus lock --output .blogus.lock
```

### verify

Verify prompts match their locked versions.

```bash
blogus verify [OPTIONS]
```

Options:
- `--path PATH` - Project path
- `--lockfile FILE` - Path to lock file

Example:
```bash
blogus verify
blogus verify || exit 1  # In CI
```

Exit codes:
- `0` - All prompts match
- `1` - Mismatch detected or lock file missing

## Update Commands

### check

Find code using unversioned prompts.

```bash
blogus check [OPTIONS]
```

Options:
- `--path PATH` - Project path

Example:
```bash
blogus check
```

### fix

Add version markers and sync code with .prompt files.

```bash
blogus fix [OPTIONS]
```

Options:
- `--path PATH` - Project path
- `--dry-run` - Show changes without applying

Example:
```bash
blogus fix --dry-run  # Preview
blogus fix            # Apply
```

## Global Options

All commands support:
- `--help` - Show help message

## Supported Models

Blogus supports any model available through LiteLLM:

**OpenAI:**
- `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`

**Anthropic:**
- `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

**Groq:**
- `groq/llama3-70b-8192`, `groq/mixtral-8x7b-32768`

Set API keys:
```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GROQ_API_KEY=...
```
