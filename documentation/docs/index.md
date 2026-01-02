# Blogus

**`package.lock` for AI prompts.**

Extract prompts from your codebase, version them like dependencies, and keep everything in sync.

---

## The Problem

Managing AI prompts in production applications is challenging:

- **Scattered Prompts**: Prompts are embedded as strings throughout your codebase, making them hard to find and manage
- **No Version Control**: When prompts change, there's no way to track what changed, when, or why
- **Drift**: The prompt in your code diverges from what's actually running in production
- **No Testing**: Prompts are rarely tested systematically before deployment
- **Team Collaboration**: Multiple developers editing prompts leads to conflicts and inconsistencies

### The Current State of Prompt Management

```python
# This is how most teams manage prompts today
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": user_input}
    ]
)
# Where did this prompt come from? Who wrote it? When did it change?
# Is this the same prompt running in production?
```

---

## The Solution: Blogus

Blogus brings the same rigor to prompt management that `package.lock` brought to dependency management:

| Feature | Without Blogus | With Blogus |
|---------|---------------|-------------|
| **Discovery** | Manually search codebase | `blogus scan` finds all prompts |
| **Versioning** | Hope git history helps | Content-addressed hashes |
| **Testing** | Manual testing | Automated test generation |
| **Sync** | Manual copy-paste | `blogus fix` auto-syncs |
| **CI/CD** | No verification | `blogus verify` in pipelines |
| **Collaboration** | Merge conflicts | Structured `.prompt` files |

---

## How Blogus Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BLOGUS WORKFLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  SCAN    │───▶│  VERSION │───▶│   LOCK   │───▶│   SYNC   │             │
│   │          │    │          │    │          │    │          │             │
│   │ Find LLM │    │ .prompt  │    │ prompts  │    │ Update   │             │
│   │ calls in │    │ files    │    │ .lock    │    │ source   │             │
│   │ codebase │    │          │    │          │    │ code     │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│        │                │                │                │                 │
│        ▼                ▼                ▼                ▼                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ Detects  │    │ Creates  │    │ Tracks   │    │ Updates  │             │
│   │ OpenAI,  │    │ YAML +   │    │ hashes,  │    │ imports  │             │
│   │ Anthropic│    │ template │    │ commits, │    │ and refs │             │
│   │ LangChain│    │ format   │    │ metadata │    │ in code  │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Scan - Discover Prompts

Blogus scans your codebase to find all LLM API calls:

```bash
$ blogus scan

Scanning /home/user/myproject...

Found 5 LLM API calls:

  Location                    Provider    Status        Prompt Preview
  ─────────────────────────────────────────────────────────────────────
  src/chat.py:15             OpenAI      unversioned   "You are a helpful..."
  src/summarize.py:42        OpenAI      unversioned   "Summarize the foll..."
  src/translate.py:28        Anthropic   unversioned   "Translate the foll..."
  lib/sentiment.py:56        OpenAI      unversioned   "Analyze the sentim..."
  api/generate.py:103        LangChain   unversioned   "Generate a product..."

Summary:
  Total calls found: 5
  Unversioned: 5
  Versioned: 0
```

**Supported Providers:**

- OpenAI SDK (`openai.chat.completions.create`)
- Anthropic SDK (`anthropic.messages.create`)
- LiteLLM (`litellm.completion`)
- LangChain (`ChatPromptTemplate`, `PromptTemplate`)
- Azure OpenAI
- Google Vertex AI / Gemini
- Cohere
- Custom patterns (configurable)

### Step 2: Version - Create Prompt Files

Initialize structured `.prompt` files:

```bash
$ blogus init

Creating prompts directory...

Created 5 prompt files:
  prompts/chat.prompt
  prompts/summarize.prompt
  prompts/translate.prompt
  prompts/sentiment.prompt
  prompts/generate.prompt

Next steps:
  1. Review and edit the generated .prompt files
  2. Run 'blogus lock' to generate the lock file
  3. Run 'blogus fix' to update your source code
```

Each `.prompt` file has a structured format:

```yaml
# prompts/summarize.prompt
---
name: summarize
description: Summarize long-form content into key bullet points
version: 1.0.0
author: engineering-team
created: 2024-01-15
model:
  id: gpt-4o
  temperature: 0.3
  max_tokens: 500
variables:
  - name: content
    type: string
    required: true
    description: The content to summarize
  - name: num_points
    type: integer
    default: 5
    description: Number of bullet points to generate
  - name: style
    type: string
    default: professional
    enum: [professional, casual, technical]
    description: Writing style for the summary
tags:
  - summarization
  - content-processing
  - production
---
You are an expert content summarizer. Your task is to distill complex information into clear, actionable bullet points.

Guidelines:
- Extract the {{num_points}} most important points
- Use {{style}} language appropriate for business communication
- Each bullet should be self-contained and meaningful
- Prioritize actionable insights over general observations

Content to summarize:
{{content}}

Provide exactly {{num_points}} bullet points, each on its own line starting with "•".
```

### Step 3: Lock - Track Versions

Generate a lock file that tracks exact versions:

```bash
$ blogus lock

Generating lock file...

  Prompt          Hash                    Status
  ────────────────────────────────────────────────
  summarize       sha256:a1b2c3d4...     locked
  translate       sha256:b2c3d4e5...     locked
  chat            sha256:c3d4e5f6...     locked
  sentiment       sha256:d4e5f6a7...     locked
  generate        sha256:e5f6a7b8...     locked

Lock file written to: prompts.lock
```

The lock file (`prompts.lock`) provides a complete audit trail:

```yaml
# prompts.lock - DO NOT EDIT MANUALLY
version: 1
generated: 2024-01-15T10:30:00Z
generator: blogus v1.2.0

prompts:
  summarize:
    file: prompts/summarize.prompt
    hash: sha256:a1b2c3d4e5f6789012345678901234567890abcdef
    content_hash: sha256:1234567890abcdef1234567890abcdef12345678
    commit: 4903f76
    author: jane@company.com
    modified: 2024-01-15T10:30:00Z
    variables:
      - content
      - num_points
      - style
    model: gpt-4o

  translate:
    file: prompts/translate.prompt
    hash: sha256:b2c3d4e5f6a7890123456789012345678901bcdef0
    content_hash: sha256:234567890abcdef1234567890abcdef123456789
    commit: 4903f76
    author: john@company.com
    modified: 2024-01-14T15:22:00Z
    variables:
      - text
      - source_language
      - target_language
    model: gpt-4o

# ... more prompts
```

### Step 4: Sync - Update Source Code

Automatically update your source code to use managed prompts:

```bash
$ blogus fix

Analyzing source files...

Changes to apply:
  src/summarize.py:42
    - content = "Summarize the following: " + text
    + # @blogus:summarize sha256:a1b2c3d4
    + content = load_prompt("summarize", content=text)

  src/translate.py:28
    - prompt = f"Translate from {src} to {tgt}: {text}"
    + # @blogus:translate sha256:b2c3d4e5
    + prompt = load_prompt("translate", text=text, source_language=src, target_language=tgt)

Apply changes? [y/N]: y

Updated 2 files.
Backup files created in .blogus/backups/
```

---

## Why Blogus?

### Comparison with Other Approaches

| Approach | Discover | Version | Test | Sync | Lock | Collaborate |
|----------|:--------:|:-------:|:----:|:----:|:----:|:-----------:|
| Inline strings | - | - | - | - | - | - |
| Manual .txt files | - | Git | - | Manual | - | - |
| LangChain Hub | - | Yes | - | Manual | - | Yes |
| PromptLayer | - | Yes | Yes | Manual | - | Yes |
| Humanloop | - | Yes | Yes | Manual | - | Yes |
| **Blogus** | **Auto** | **Git** | **Yes** | **Auto** | **Yes** | **Yes** |

### Key Differentiators

1. **Zero Migration**: Works with your existing code - no need to rewrite anything
2. **Content-Addressed**: Prompts are tracked by content hash, not arbitrary version numbers
3. **Git-Native**: Integrates seamlessly with your existing git workflow
4. **Bi-directional Sync**: Changes flow from code → prompts AND prompts → code
5. **CI/CD Ready**: Built-in verification for continuous integration

---

## Quick Start

### Installation

=== "uv (Recommended)"

    ```bash
    # Add to project
    uv add blogus

    # Or run directly without installing
    uvx blogus scan
    ```

=== "pip"

    ```bash
    pip install blogus
    ```

=== "pipx (Global Install)"

    ```bash
    pipx install blogus
    ```

### Your First Workflow

```bash
# 1. Scan your codebase
blogus scan

# 2. Initialize prompt files
blogus init

# 3. Edit the generated .prompt files as needed
# (use your favorite editor)

# 4. Lock the versions
blogus lock

# 5. Update your source code
blogus fix

# 6. Commit everything
git add prompts/ prompts.lock src/
git commit -m "Add prompt versioning with Blogus"
```

### Verify in CI

Add to your CI pipeline:

```yaml
# .github/workflows/ci.yml
- name: Verify prompts
  run: blogus verify
```

---

## Web Interface

Blogus includes a visual interface for managing prompts:

```bash
# Install with web extras
pip install blogus[web]

# Start the server
blogus-web

# Or with uvx
uvx --with blogus[web] blogus-web
```

Open `http://localhost:8000` to:

- **Browse** all prompts with syntax highlighting
- **Search** across prompt content and metadata
- **Edit** prompts with live preview
- **Test** prompts with sample inputs
- **Analyze** prompt effectiveness with AI feedback
- **Compare** versions side-by-side
- **Scan** projects for new LLM calls

---

## Use Cases

### 1. Enterprise Prompt Governance

Large organizations need to track and audit AI prompts for compliance:

```bash
# Generate audit report
blogus audit --format pdf --output prompts-audit-2024-Q1.pdf
```

### 2. A/B Testing Prompts

Test different prompt versions in production:

```python
from blogus import load_prompt

# Load specific version for A/B test
prompt_a = load_prompt("summarize", version="sha256:a1b2c3d4")
prompt_b = load_prompt("summarize", version="sha256:e5f6a7b8")
```

### 3. Prompt Development Workflow

Develop prompts like code with review and testing:

```bash
# Create feature branch
git checkout -b improve-summarize-prompt

# Edit prompt
vim prompts/summarize.prompt

# Test changes
blogus exec summarize --var content="Test content here"

# Analyze quality
blogus analyze prompts/summarize.prompt

# Lock and commit
blogus lock
git add -A && git commit -m "Improve summarize prompt clarity"
git push -u origin improve-summarize-prompt
# Create PR for review
```

### 4. Multi-Environment Deployment

Manage prompts across dev/staging/production:

```bash
# Different lock files per environment
blogus lock --output prompts.dev.lock
blogus lock --output prompts.staging.lock
blogus lock --output prompts.prod.lock
```

---

## Documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Getting Started](getting-started.md)**

    Complete setup guide with step-by-step instructions

- :material-console: **[CLI Reference](cli-reference.md)**

    Comprehensive documentation for all CLI commands

- :material-language-python: **[Python Library](python-library.md)**

    Use Blogus programmatically in your applications

- :material-file-document: **[Prompt Format](prompt-format.md)**

    Complete `.prompt` file format specification

- :material-chip: **[Model Selection](models.md)**

    Guide to choosing the right models for analysis and execution

- :material-lightning-bolt: **[Advanced Features](advanced-features.md)**

    Power user features and integration patterns

- :material-cog: **[Configuration](configuration.md)**

    Configure Blogus for your project

- :material-book-open-variant: **[Examples](examples.md)**

    Real-world examples and use cases

- :material-lifebuoy: **[Troubleshooting](troubleshooting.md)**

    Common issues and solutions

</div>

---

## Community & Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/your-username/blogus/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/your-username/blogus/discussions)
- **Contributing**: See [CONTRIBUTING.md](https://github.com/your-username/blogus/blob/main/CONTRIBUTING.md)

---

## License

Blogus is open source under the [MIT License](https://github.com/your-username/blogus/blob/main/LICENSE).
