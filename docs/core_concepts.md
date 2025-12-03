# Core Concepts

Blogus provides four key capabilities: **Extract**, **Test**, **Version**, and **Update**.

## 1. Prompt Extraction

Blogus scans your codebase to find LLM API calls across Python and JavaScript files.

### What Gets Detected

- OpenAI API calls (`openai.chat.completions.create`, etc.)
- Anthropic API calls (`anthropic.messages.create`, etc.)
- Other LLM SDKs

### The Scan Command

```bash
blogus scan
```

Output:
```
Found 4 LLM API calls:

  src/chat.py:15         OpenAI      versioned    @blogus:chat
  src/summarize.py:42    OpenAI      unversioned
  src/review.py:88       Anthropic   unversioned
  lib/translate.js:28    OpenAI      unversioned
```

Each detection shows:
- File and line number
- API provider
- Whether it's linked to a `.prompt` file
- The linked prompt name (if versioned)

### Version Markers

Code linked to a prompt file has a version marker:

```python
# @blogus:summarize@v3 sha256:a1b2c3d4
response = client.chat.completions.create(...)
```

The marker includes:
- Prompt name (`summarize`)
- Version (`v3`)
- Content hash for verification

## 2. Prompt Testing

Blogus helps you test prompts before deployment.

### Analysis

Evaluate prompt effectiveness:

```bash
blogus analyze prompts/summarize.prompt
```

Returns:
- Goal alignment score
- Effectiveness assessment
- Improvement suggestions

### Test Generation

Generate test cases automatically:

```bash
blogus test prompts/summarize.prompt
```

Creates test inputs with expected outputs.

### Execution

Run prompts with variables:

```bash
blogus exec summarize --var text="Long article..."
```

### Target vs Judge Models

Blogus separates:
- **Target model**: Executes prompts (e.g., gpt-4o for production)
- **Judge model**: Analyzes prompts (can be a different, more capable model)

```bash
blogus analyze prompt.txt --target-model gpt-4o --judge-model claude-3-opus
```

## 3. Prompt Versioning

### .prompt Files

Store prompts in version-controlled files:

```yaml
---
name: summarize
description: Summarize text
model:
  id: gpt-4o
  temperature: 0.3
variables:
  - name: text
    required: true
---

Summarize this text: {{text}}
```

Benefits:
- Full Git history per prompt
- Clear ownership and documentation
- Variable definitions with types
- Model configuration included

### Lock File

Generate a lock file for reproducible deployments:

```bash
blogus lock
```

Creates `prompts.lock`:
```yaml
version: 1
generated: 2024-01-15T10:30:00Z
prompts:
  summarize:
    hash: sha256:a1b2c3d4e5f6...
    commit: 4903f76
    path: prompts/summarize.prompt
  code-review:
    hash: sha256:b2c3d4e5f6a7...
    commit: 4903f76
    path: prompts/code-review.prompt
```

### CI Verification

Verify prompts match their locked versions:

```bash
blogus verify
```

Exits with non-zero status if:
- Prompts have changed without updating the lock
- Lock file is missing
- Hash mismatches detected

Add to CI:
```yaml
- run: blogus verify || exit 1
```

## 4. Code Sync (Update)

When you improve a `.prompt` file, sync changes back to your source code.

### Check for Unversioned Prompts

```bash
blogus check
```

Lists code locations using prompts that aren't linked to `.prompt` files.

### Preview Updates

```bash
blogus fix --dry-run
```

Shows what would change without modifying files.

### Apply Updates

```bash
blogus fix
```

Updates version markers and can refactor inline prompts to use `load_prompt()`.

### Before and After

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

## The Complete Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EXTRACT   │────▶│    TEST     │────▶│   VERSION   │────▶│   UPDATE    │
│             │     │             │     │             │     │             │
│ blogus scan │     │ analyze     │     │ blogus lock │     │ blogus fix  │
│             │     │ test        │     │ verify      │     │             │
│ Find LLM    │     │ exec        │     │             │     │ Sync to     │
│ API calls   │     │             │     │ Lock file   │     │ source code │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

1. **Extract**: Discover prompts scattered in your code
2. **Test**: Analyze and validate before deploying
3. **Version**: Lock with content hashes for reproducibility
4. **Update**: Keep code in sync when prompts improve
