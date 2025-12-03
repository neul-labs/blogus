# CLI Reference

```bash
blogus [command] [options]
```

## Scan

### scan

Find LLM API calls in your codebase.

```bash
blogus scan [--path PATH] [--python] [--no-python] [--js] [--no-js]
```

```bash
$ blogus scan
Found 3 LLM API calls:
  src/chat.py:15         OpenAI      versioned    @blogus:chat
  src/summarize.py:42    OpenAI      unversioned
  lib/translate.js:28    Anthropic   unversioned
```

### init

Create prompts directory.

```bash
blogus init [--path PATH]
```

## Version

### prompts

List all .prompt files.

```bash
blogus prompts [--path PATH] [--category CAT] [--dirty]
```

### exec

Execute a .prompt file with variables.

```bash
blogus exec NAME [--var KEY=VALUE]... [--model MODEL]
```

```bash
$ blogus exec summarize --var text="Long article..."
```

### analyze

Evaluate prompt effectiveness.

```bash
blogus analyze PROMPT [--target-model MODEL] [--judge-model MODEL] [--goal TEXT]
```

### test

Generate test cases.

```bash
blogus test PROMPT [--target-model MODEL] [--judge-model MODEL] [--goal TEXT]
```

### execute

Execute a raw prompt string.

```bash
blogus execute PROMPT [--target-model MODEL]
```

### goal

Infer prompt goal.

```bash
blogus goal PROMPT [--judge-model MODEL]
```

### fragments

Analyze prompt fragments.

```bash
blogus fragments PROMPT [--target-model MODEL] [--judge-model MODEL] [--goal TEXT]
```

## Lock

### lock

Generate prompts.lock file.

```bash
blogus lock [--path PATH] [--output FILE]
```

### verify

Check prompts match lock file.

```bash
blogus verify [--path PATH] [--lockfile FILE]
```

```bash
$ blogus verify || exit 1  # CI usage
```

Exit codes:
- `0` - All prompts match
- `1` - Mismatch or missing lock

## Sync

### check

Find unversioned prompts in code.

```bash
blogus check [--path PATH]
```

### fix

Update code when .prompt files change.

```bash
blogus fix [--path PATH] [--dry-run]
```

```bash
$ blogus fix --dry-run  # Preview
$ blogus fix            # Apply
```

## Models

Supported via LiteLLM:

**OpenAI**: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`

**Anthropic**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

**Groq**: `groq/llama3-70b-8192`, `groq/mixtral-8x7b-32768`

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GROQ_API_KEY=...
```
