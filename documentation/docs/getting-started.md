# Getting Started

This comprehensive guide walks you through setting up Blogus in your project, from installation to your first production deployment.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed
- **Git** for version control
- **API keys** for LLM providers you plan to use (OpenAI, Anthropic, etc.)
- **An existing project** with LLM API calls (or follow along with our example)

### Verify Your Python Version

```bash
python --version
# Python 3.11.4 (or 3.9+)
```

### Set Up API Keys

Blogus uses LiteLLM under the hood, which supports multiple providers:

=== "OpenAI"

    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

=== "Anthropic"

    ```bash
    export ANTHROPIC_API_KEY="sk-ant-..."
    ```

=== "Groq"

    ```bash
    export GROQ_API_KEY="gsk_..."
    ```

=== "Azure OpenAI"

    ```bash
    export AZURE_API_KEY="..."
    export AZURE_API_BASE="https://your-resource.openai.azure.com/"
    export AZURE_API_VERSION="2024-02-15-preview"
    ```

!!! tip "API Key Management"
    For production, use a secrets manager or `.env` file (not committed to git) instead of exporting directly.

---

## Installation

### Option 1: uv (Recommended)

[uv](https://github.com/astral-sh/uv) is the fastest Python package manager:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add blogus to your project
uv add blogus

# Or try without installing (great for evaluation)
uvx blogus scan
```

### Option 2: pip

```bash
# Basic installation
pip install blogus

# With web interface
pip install blogus[web]

# With all optional dependencies
pip install blogus[web,dev]
```

### Option 3: pipx (Global Installation)

If you want `blogus` available system-wide:

```bash
pipx install blogus
```

### Option 4: From Source

```bash
git clone https://github.com/your-username/blogus.git
cd blogus
pip install -e ".[dev]"
```

### Verify Installation

```bash
blogus --version
# blogus 1.2.0

blogus --help
# Usage: blogus [OPTIONS] COMMAND [ARGS]...
# ...
```

---

## Quick Start: 5-Minute Tutorial

Let's walk through a complete example from start to finish.

### Step 1: Create a Sample Project

If you don't have an existing project, create a simple one:

```bash
mkdir my-ai-project && cd my-ai-project
git init
```

Create a sample Python file with LLM calls:

```python
# src/assistant.py
import openai

def chat_with_user(user_message: str) -> str:
    """Simple chat function using OpenAI."""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Be concise and friendly."
            },
            {"role": "user", "content": user_message}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content


def summarize_text(text: str, max_points: int = 3) -> str:
    """Summarize text into bullet points."""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"Summarize the following text into {max_points} bullet points. Be concise."
            },
            {"role": "user", "content": text}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


def translate_text(text: str, target_language: str) -> str:
    """Translate text to target language."""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"Translate the following text to {target_language}. Preserve the original meaning and tone."
            },
            {"role": "user", "content": text}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content
```

### Step 2: Scan Your Codebase

Discover all LLM calls in your project:

```bash
blogus scan
```

**Expected output:**

```
Scanning /home/user/my-ai-project...

Found 3 LLM API calls:

  Location                    Provider    Status        Prompt Preview
  ─────────────────────────────────────────────────────────────────────
  src/assistant.py:8         OpenAI      unversioned   "You are a helpful..."
  src/assistant.py:22        OpenAI      unversioned   "Summarize the foll..."
  src/assistant.py:37        OpenAI      unversioned   "Translate the foll..."

Summary:
  Total calls found: 3
  Unversioned: 3
  Versioned: 0

Run 'blogus init' to create .prompt files for these prompts.
```

!!! info "What Gets Detected?"
    Blogus uses static analysis to find LLM calls. It detects:

    - OpenAI SDK calls (`openai.chat.completions.create`, `openai.Completion.create`)
    - Anthropic SDK calls (`anthropic.messages.create`)
    - LiteLLM calls (`litellm.completion`)
    - LangChain templates (`ChatPromptTemplate`, `PromptTemplate`)
    - String patterns that look like system prompts

### Step 3: Initialize Prompt Files

Create structured `.prompt` files for each detected prompt:

```bash
blogus init
```

**Expected output:**

```
Creating prompts directory at: ./prompts/

Analyzing detected prompts...

Created 3 prompt files:
  ✓ prompts/assistant-chat.prompt
  ✓ prompts/assistant-summarize.prompt
  ✓ prompts/assistant-translate.prompt

Next steps:
  1. Review and customize the generated .prompt files
  2. Run 'blogus lock' to create the lock file
  3. Run 'blogus fix' to update your source code references
```

### Step 4: Review Generated Prompt Files

Let's look at one of the generated files:

```yaml
# prompts/assistant-summarize.prompt
---
name: assistant-summarize
description: Summarize text into bullet points
source:
  file: src/assistant.py
  line: 22
  function: summarize_text
model:
  id: gpt-4
  temperature: 0.3
variables:
  - name: text
    type: string
    required: true
    description: The text to summarize
  - name: max_points
    type: integer
    default: 3
    description: Number of bullet points
tags:
  - summarization
  - auto-generated
---
Summarize the following text into {{max_points}} bullet points. Be concise.

{{text}}
```

### Step 5: Customize Your Prompts

Edit the prompt files to improve them:

```yaml
# prompts/assistant-summarize.prompt (improved)
---
name: assistant-summarize
description: Summarize long-form content into clear, actionable bullet points
source:
  file: src/assistant.py
  line: 22
  function: summarize_text
model:
  id: gpt-4o
  temperature: 0.3
  max_tokens: 500
variables:
  - name: text
    type: string
    required: true
    description: The content to summarize
  - name: max_points
    type: integer
    default: 3
    description: Maximum number of bullet points (1-10)
    min: 1
    max: 10
  - name: style
    type: string
    default: professional
    enum: [professional, casual, technical]
    description: Writing style for the summary
tags:
  - summarization
  - content-processing
  - production-ready
---
You are an expert content analyst. Your task is to distill complex information into clear, actionable insights.

Guidelines:
- Extract the {{max_points}} most important points from the content
- Use {{style}} language appropriate for business communication
- Each bullet point should be:
  - Self-contained and meaningful on its own
  - Focused on actionable insights rather than general observations
  - Between 10-25 words
- Preserve any critical numbers, dates, or proper nouns
- If the content is too short for {{max_points}} points, use fewer

Content to summarize:
---
{{text}}
---

Respond with exactly {{max_points}} bullet points (or fewer if content is limited), each on its own line starting with "•".
```

### Step 6: Test Your Prompts

Before locking, test that your prompts work correctly:

```bash
# Test with sample input
blogus exec assistant-summarize \
  --var text="Artificial intelligence is transforming industries worldwide. Companies are investing billions in AI research and development. Machine learning models are becoming more sophisticated and accessible. However, concerns about AI safety and ethics continue to grow. Regulations are being developed to ensure responsible AI use." \
  --var max_points=3 \
  --var style=professional
```

**Expected output:**

```
Executing prompt: assistant-summarize
Model: gpt-4o
Temperature: 0.3

Response:
• Global AI investment is accelerating rapidly, with companies allocating billions to research and development initiatives
• Machine learning technology is becoming increasingly sophisticated while simultaneously more accessible to organizations of all sizes
• Growing concerns about AI safety and ethics are driving development of new regulatory frameworks for responsible deployment
```

### Step 7: Generate the Lock File

Create a lock file to track exact versions:

```bash
blogus lock
```

**Expected output:**

```
Generating lock file...

  Prompt                  Hash                        Status
  ───────────────────────────────────────────────────────────
  assistant-chat          sha256:7a8b9c0d...         ✓ locked
  assistant-summarize     sha256:1e2f3a4b...         ✓ locked
  assistant-translate     sha256:5c6d7e8f...         ✓ locked

Lock file written to: prompts.lock

Tip: Commit both prompts/ and prompts.lock to version control.
```

### Step 8: Update Your Source Code

Automatically update your code to use managed prompts:

```bash
blogus fix
```

**Expected output:**

```
Analyzing source files...

Proposed changes:

  src/assistant.py:8-14
  ─────────────────────
  - response = openai.chat.completions.create(
  -     model="gpt-4",
  -     messages=[
  -         {"role": "system", "content": "You are a helpful assistant..."},
  -         {"role": "user", "content": user_message}
  -     ],
  -     temperature=0.7
  - )
  + # @blogus:assistant-chat sha256:7a8b9c0d
  + from blogus import load_prompt
  + prompt = load_prompt("assistant-chat", user_message=user_message)
  + response = openai.chat.completions.create(**prompt.to_openai())

  [Similar changes for other prompts...]

Apply changes? [y/N]: y

✓ Updated src/assistant.py (3 changes)
✓ Backup created: .blogus/backups/assistant.py.20240115-103000

Summary:
  Files modified: 1
  Prompts synced: 3
```

### Step 9: Commit Your Changes

```bash
# Review changes
git status
git diff

# Stage and commit
git add prompts/ prompts.lock src/
git commit -m "Add prompt versioning with Blogus

- Extract 3 prompts from assistant.py
- Add structured .prompt files with improved prompts
- Generate lock file for version tracking"
```

### Step 10: Set Up CI Verification

Add verification to your CI pipeline:

=== "GitHub Actions"

    ```yaml
    # .github/workflows/ci.yml
    name: CI

    on: [push, pull_request]

    jobs:
      verify-prompts:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - name: Set up Python
            uses: actions/setup-python@v5
            with:
              python-version: '3.11'

          - name: Install Blogus
            run: pip install blogus

          - name: Verify prompt lock file
            run: blogus verify --strict
    ```

=== "GitLab CI"

    ```yaml
    # .gitlab-ci.yml
    verify-prompts:
      image: python:3.11
      script:
        - pip install blogus
        - blogus verify --strict
      rules:
        - changes:
            - prompts/**/*
            - prompts.lock
    ```

=== "CircleCI"

    ```yaml
    # .circleci/config.yml
    version: 2.1
    jobs:
      verify-prompts:
        docker:
          - image: python:3.11
        steps:
          - checkout
          - run:
              name: Install Blogus
              command: pip install blogus
          - run:
              name: Verify prompts
              command: blogus verify --strict
    ```

---

## Understanding the Workflow

### The Blogus Lifecycle

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                  DEVELOPMENT CYCLE                       │
                    │                                                          │
   ┌─────────┐      │   ┌─────────┐    ┌─────────┐    ┌─────────┐           │
   │  Write  │──────┼──▶│  Edit   │───▶│  Test   │───▶│  Lock   │───────────┼───┐
   │  Code   │      │   │ .prompt │    │ Prompt  │    │ Version │           │   │
   └─────────┘      │   └─────────┘    └─────────┘    └─────────┘           │   │
        │           │        ▲                             │                 │   │
        │           │        │                             │                 │   │
        │           │        └─────────────────────────────┘                 │   │
        │           │              (iterate until satisfied)                 │   │
        │           │                                                          │
        │           └─────────────────────────────────────────────────────────┘
        │                                                                        │
        │                                                                        ▼
        │                                                                ┌─────────────┐
        │                                                                │   Commit    │
        │                                                                │   + Push    │
        │                                                                └─────────────┘
        │                                                                        │
        ▼                                                                        ▼
   ┌─────────┐                                                          ┌─────────────┐
   │  Scan   │◀─────────────────────────────────────────────────────────│   CI/CD     │
   │  Code   │                                                          │   Verify    │
   └─────────┘                                                          └─────────────┘
```

### When to Run Each Command

| Command | When to Run | Purpose |
|---------|-------------|---------|
| `blogus scan` | After writing new LLM code | Discover new prompts |
| `blogus init` | After scan finds unversioned prompts | Create `.prompt` files |
| `blogus exec` | During prompt development | Test prompts interactively |
| `blogus analyze` | Before finalizing prompts | Get AI feedback on quality |
| `blogus lock` | After editing `.prompt` files | Update version hashes |
| `blogus verify` | In CI/CD pipelines | Ensure lock file is current |
| `blogus fix` | After changing prompts | Sync code with prompt files |
| `blogus check` | Before commits | Find unversioned prompts |

---

## Project Structure

After setup, your project structure should look like:

```
my-ai-project/
├── .blogus/                    # Blogus working directory
│   ├── backups/               # Backup of modified files
│   │   └── assistant.py.20240115-103000
│   └── config.yaml            # Local configuration
├── prompts/                    # Prompt files directory
│   ├── assistant-chat.prompt
│   ├── assistant-summarize.prompt
│   └── assistant-translate.prompt
├── prompts.lock               # Lock file (commit this!)
├── src/
│   └── assistant.py           # Your source code
├── .gitignore
└── pyproject.toml
```

### What to Commit

**Always commit:**

- `prompts/` directory and all `.prompt` files
- `prompts.lock` file
- Updated source files

**Never commit:**

- `.blogus/backups/` (add to `.gitignore`)
- API keys or secrets

Add to your `.gitignore`:

```gitignore
# Blogus
.blogus/backups/
.blogus/cache/

# Environment
.env
.env.local
```

---

## Common Workflows

### Adding a New Prompt

```bash
# 1. Write your new LLM code
# 2. Scan to detect it
blogus scan

# 3. Initialize the new prompt
blogus init

# 4. Edit the generated .prompt file
vim prompts/my-new-prompt.prompt

# 5. Test it
blogus exec my-new-prompt --var key=value

# 6. Lock and sync
blogus lock
blogus fix

# 7. Commit
git add -A && git commit -m "Add my-new-prompt"
```

### Updating an Existing Prompt

```bash
# 1. Edit the prompt file
vim prompts/assistant-summarize.prompt

# 2. Test your changes
blogus exec assistant-summarize --var text="Test content"

# 3. Analyze quality (optional)
blogus analyze prompts/assistant-summarize.prompt

# 4. Update the lock file
blogus lock

# 5. Sync to source code (if needed)
blogus fix

# 6. Commit
git add -A && git commit -m "Improve summarize prompt"
```

### Reviewing Prompt Changes in PRs

When reviewing a PR that modifies prompts:

```bash
# Check what changed
git diff main -- prompts/

# Verify lock file is updated
blogus verify

# Test the changed prompts
blogus exec <prompt-name> --var ...
```

### Rolling Back a Prompt

```bash
# Find previous version in git
git log --oneline -- prompts/assistant-summarize.prompt

# Restore previous version
git checkout <commit-hash> -- prompts/assistant-summarize.prompt

# Update lock file
blogus lock

# Sync and commit
blogus fix
git add -A && git commit -m "Rollback summarize prompt to previous version"
```

---

## Next Steps

Now that you have Blogus set up, explore these resources:

- **[CLI Reference](cli-reference.md)** - Complete documentation for all commands
- **[Prompt Format](prompt-format.md)** - Learn the full `.prompt` file specification
- **[Python Library](python-library.md)** - Use Blogus programmatically
- **[Examples](examples.md)** - Real-world use cases and patterns
- **[Configuration](configuration.md)** - Customize Blogus for your project
- **[Troubleshooting](troubleshooting.md)** - Solutions to common issues

---

## Getting Help

If you run into issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Search [GitHub Issues](https://github.com/your-username/blogus/issues)
3. Ask in [GitHub Discussions](https://github.com/your-username/blogus/discussions)
4. File a [bug report](https://github.com/your-username/blogus/issues/new?template=bug_report.md)
