# Core Concepts

Blogus provides four capabilities: **Scan**, **Version**, **Lock**, and **Sync**.

## 1. Scan

Find all LLM API calls in your codebase.

```bash
$ blogus scan

Found 4 LLM API calls:
  src/chat.py:15         OpenAI      versioned    @blogus:chat
  src/summarize.py:42    OpenAI      unversioned
  src/review.py:88       Anthropic   unversioned
  lib/translate.js:28    OpenAI      unversioned
```

### What Gets Detected

- OpenAI SDK calls (`openai.chat.completions.create`)
- Anthropic SDK calls (`anthropic.messages.create`)
- Python and JavaScript/TypeScript files

### Version Markers

Versioned code has a marker linking it to a `.prompt` file:

```python
# @blogus:summarize sha256:a1b2c3d4
content = load_prompt("summarize", text=text)
```

## 2. Version

Store prompts in `.prompt` files with Git tracking.

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

### Benefits

- Full Git history per prompt
- Variables with types and defaults
- Model configuration included
- IDE syntax highlighting (YAML)

### Testing

Blogus can analyze and test prompts:

```bash
blogus analyze prompts/summarize.prompt  # Evaluate effectiveness
blogus test prompts/summarize.prompt     # Generate test cases
blogus exec summarize --var text="..."   # Execute with variables
```

## 3. Lock

Generate `prompts.lock` with content hashes.

```bash
$ blogus lock
```

```yaml
# prompts.lock
version: 1
generated: 2024-01-15T10:30:00Z
prompts:
  summarize:
    hash: sha256:a1b2c3d4e5f6...
    commit: 4903f76
    path: prompts/summarize.prompt
```

### CI Verification

```bash
$ blogus verify || exit 1
```

Fails if:
- Prompts changed without updating the lock
- Lock file is missing
- Hash mismatch detected

### Why Lock?

Like `package.lock` for dependencies:
- **Reproducibility**: Same prompts in dev and production
- **Audit trail**: Know exactly what's deployed
- **CI enforcement**: Catch unreviewed prompt changes

## 4. Sync

Update code when `.prompt` files change.

```bash
$ blogus fix --dry-run  # Preview
$ blogus fix            # Apply
```

### Before

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Summarize: " + text}]
)
```

### After

```python
# @blogus:summarize sha256:a1b2c3d4
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": load_prompt("summarize", text=text)}]
)
```

### Find Unversioned Prompts

```bash
$ blogus check
```

Lists code locations not linked to `.prompt` files.

## The Workflow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  SCAN    │───▶│  VERSION │───▶│   LOCK   │───▶│   SYNC   │
│          │    │          │    │          │    │          │
│ Find LLM │    │ .prompt  │    │ prompts  │    │ Update   │
│ calls    │    │ files    │    │ .lock    │    │ code     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Comparison

| Approach | Discover | Version | Test | Sync | Lock |
|----------|:--------:|:-------:|:----:|:----:|:----:|
| Inline strings | - | - | - | - | - |
| Manual .txt files | - | Git | - | Manual | - |
| LangChain Hub | - | Yes | - | Manual | - |
| PromptLayer | - | Yes | Yes | Manual | - |
| **Blogus** | **Auto** | **Git** | **Yes** | **Auto** | **Yes** |

Blogus is the only tool that:
1. **Discovers** prompts in existing code
2. **Locks** versions with content hashes
3. **Syncs** changes back to source automatically
