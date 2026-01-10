# CLI Reference

Complete reference documentation for all Blogus command-line interface commands.

---

## Overview

```bash
blogus [OPTIONS] COMMAND [ARGS]...
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version number and exit |
| `--help` | Show help message and exit |
| `--quiet, -q` | Suppress non-essential output |
| `--verbose, -v` | Enable verbose output (use -vv for debug) |
| `--no-color` | Disable colored output |
| `--config FILE` | Use specific config file |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOGUS_PROMPTS_DIR` | Default prompts directory | `./prompts` |
| `BLOGUS_LOCK_FILE` | Default lock file path | `./prompts.lock` |
| `BLOGUS_CONFIG` | Config file path | `./.blogus/config.yaml` |
| `BLOGUS_MODEL` | Default model for execution | `gpt-4o` |
| `BLOGUS_JUDGE_MODEL` | Default model for analysis | `gpt-4o` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GROQ_API_KEY` | Groq API key | - |

---

## Commands

### scan

Scan your codebase to discover LLM API calls.

```bash
blogus scan [OPTIONS] [PATH]
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Directory or file to scan | Current directory |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--include PATTERN` | Glob patterns to include (repeatable) | `**/*.py`, `**/*.js`, etc. |
| `--exclude PATTERN` | Glob patterns to exclude (repeatable) | `**/node_modules/**`, etc. |
| `--provider PROVIDER` | Filter by provider (openai, anthropic, etc.) | All |
| `--status STATUS` | Filter by status (versioned, unversioned) | All |
| `--json` | Output as JSON | `false` |
| `--output FILE` | Write output to file | stdout |
| `--recursive / --no-recursive` | Scan subdirectories | `true` |
| `--follow-imports` | Follow Python imports to find prompts | `false` |

#### Examples

```bash
# Basic scan of current directory
blogus scan

# Scan specific directory
blogus scan ./src

# Scan only Python files
blogus scan --include "**/*.py"

# Exclude test files
blogus scan --exclude "**/test_*.py" --exclude "**/tests/**"

# Filter by provider
blogus scan --provider openai

# Show only unversioned prompts
blogus scan --status unversioned

# Output as JSON for scripting
blogus scan --json > prompts.json

# Combine multiple options
blogus scan ./src \
  --include "**/*.py" \
  --exclude "**/tests/**" \
  --provider openai \
  --json
```

#### Output Format

**Standard output:**

```
Scanning /home/user/project...

Found 5 LLM API calls:

  Location                    Provider    Status        Prompt Preview
  ─────────────────────────────────────────────────────────────────────
  src/chat.py:15             OpenAI      unversioned   "You are a helpful..."
  src/chat.py:42             OpenAI      versioned     "Summarize the foll..."
  src/translate.py:28        Anthropic   unversioned   "Translate the foll..."
  lib/api.py:156             OpenAI      unversioned   "Generate a respons..."
  utils/ai.py:89             LangChain   versioned     "You are an expert..."

Summary:
  Total calls found: 5
  Versioned: 2
  Unversioned: 3
```

**JSON output:**

```json
{
  "path": "/home/user/project",
  "scan_time": "2024-01-15T10:30:00Z",
  "prompts": [
    {
      "location": {
        "file": "src/chat.py",
        "line": 15,
        "column": 4,
        "function": "chat_with_user"
      },
      "provider": "openai",
      "status": "unversioned",
      "prompt_preview": "You are a helpful...",
      "model": "gpt-4",
      "temperature": 0.7
    }
  ],
  "summary": {
    "total": 5,
    "versioned": 2,
    "unversioned": 3
  }
}
```

---

### init

Initialize prompt files for detected LLM calls.

```bash
blogus init [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dir PATH` | Directory to create prompts in | `./prompts` |
| `--force` | Overwrite existing prompt files | `false` |
| `--interactive / --no-interactive` | Prompt for each file | `true` |
| `--template TEMPLATE` | Template style (minimal, standard, detailed) | `standard` |
| `--name-format FORMAT` | Naming format (function, file-function, custom) | `function` |
| `--scan-path PATH` | Path to scan for prompts | Current directory |

#### Examples

```bash
# Basic initialization
blogus init

# Use custom directory
blogus init --dir ./my-prompts

# Force overwrite existing files
blogus init --force

# Non-interactive mode (accept all defaults)
blogus init --no-interactive

# Use detailed template
blogus init --template detailed

# Custom naming format
blogus init --name-format file-function

# Combine options
blogus init \
  --dir ./prompts \
  --template detailed \
  --no-interactive \
  --force
```

#### Templates

**Minimal template:**

```yaml
---
name: {{name}}
model:
  id: {{model}}
---
{{prompt_content}}
```

**Standard template (default):**

```yaml
---
name: {{name}}
description: {{description}}
source:
  file: {{source_file}}
  line: {{source_line}}
model:
  id: {{model}}
  temperature: {{temperature}}
variables: {{variables}}
tags:
  - auto-generated
---
{{prompt_content}}
```

**Detailed template:**

```yaml
---
name: {{name}}
description: {{description}}
version: 1.0.0
author: {{git_user}}
created: {{date}}
source:
  file: {{source_file}}
  line: {{source_line}}
  function: {{function_name}}
model:
  id: {{model}}
  temperature: {{temperature}}
  max_tokens: {{max_tokens}}
  top_p: {{top_p}}
variables: {{variables}}
examples: []
tests: []
tags:
  - auto-generated
  - needs-review
metadata:
  provider: {{provider}}
  original_hash: {{hash}}
---
{{prompt_content}}
```

---

### prompts

List all managed prompt files.

```bash
blogus prompts [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dir PATH` | Prompts directory | `./prompts` |
| `--json` | Output as JSON | `false` |
| `--verbose` | Show detailed information | `false` |
| `--filter TAG` | Filter by tag (repeatable) | All |
| `--sort FIELD` | Sort by field (name, modified, model) | `name` |

#### Examples

```bash
# List all prompts
blogus prompts

# Verbose output with details
blogus prompts --verbose

# Filter by tag
blogus prompts --filter production

# Multiple tag filters (AND)
blogus prompts --filter production --filter summarization

# Sort by modification time
blogus prompts --sort modified

# JSON output
blogus prompts --json
```

#### Output

**Standard output:**

```
Prompts (5 total):

  Name                    Model       Variables   Tags
  ─────────────────────────────────────────────────────────
  assistant-chat          gpt-4o      1           chat, production
  assistant-summarize     gpt-4o      3           summarization
  assistant-translate     gpt-4o      3           translation
  code-review             claude-3    2           code, review
  email-generator         gpt-4o      4           email, generation
```

**Verbose output:**

```
Prompts (5 total):

  assistant-chat
    Description: Chat with users in a friendly, helpful manner
    Model: gpt-4o (temperature: 0.7)
    Variables: user_message (required)
    Tags: chat, production
    Modified: 2024-01-15 10:30:00
    Hash: sha256:7a8b9c0d...

  assistant-summarize
    Description: Summarize content into bullet points
    Model: gpt-4o (temperature: 0.3)
    Variables: text (required), max_points (default: 3), style (default: professional)
    Tags: summarization
    Modified: 2024-01-14 15:22:00
    Hash: sha256:1e2f3a4b...

  [...]
```

---

### exec

Execute a prompt with specified variables.

```bash
blogus exec <NAME> [OPTIONS]
```

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `NAME` | Name of the prompt to execute | Yes |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--var KEY=VALUE` | Set variable value (repeatable) | - |
| `--var-file FILE` | Load variables from JSON/YAML file | - |
| `--model MODEL` | Override model from prompt file | From prompt |
| `--temperature FLOAT` | Override temperature | From prompt |
| `--max-tokens INT` | Override max tokens | From prompt |
| `--json` | Output response as JSON | `false` |
| `--stream` | Stream response in real-time | `false` |
| `--dry-run` | Show what would be sent without executing | `false` |
| `--save FILE` | Save response to file | - |
| `--version VERSION` | Use specific prompt version | Latest |
| `--timeout SECONDS` | Request timeout | 60 |

#### Examples

```bash
# Basic execution
blogus exec assistant-chat --var user_message="Hello!"

# Multiple variables
blogus exec assistant-summarize \
  --var text="Long article content here..." \
  --var max_points=5 \
  --var style=technical

# Load variables from file
blogus exec assistant-summarize --var-file ./test-input.json

# Override model settings
blogus exec assistant-chat \
  --var user_message="Hello" \
  --model gpt-3.5-turbo \
  --temperature 0.9

# Stream response
blogus exec assistant-chat \
  --var user_message="Tell me a story" \
  --stream

# Dry run (show what would be sent)
blogus exec assistant-chat \
  --var user_message="Hello" \
  --dry-run

# Save response to file
blogus exec assistant-summarize \
  --var text="Content..." \
  --save ./output.txt

# Use specific version
blogus exec assistant-chat \
  --var user_message="Hello" \
  --version sha256:7a8b9c0d

# JSON output for scripting
blogus exec assistant-chat \
  --var user_message="Hello" \
  --json
```

#### Variable File Format

```json
// test-input.json
{
  "text": "Long article content here...",
  "max_points": 5,
  "style": "professional"
}
```

```yaml
# test-input.yaml
text: |
  Long article content here...
  Can be multi-line.
max_points: 5
style: professional
```

#### Output

**Standard output:**

```
Executing prompt: assistant-summarize
Model: gpt-4o
Temperature: 0.3

Response:
───────────────────────────────────────────────────
• First key point from the summarized content
• Second important insight extracted
• Third actionable takeaway

───────────────────────────────────────────────────
Tokens: 156 (prompt) + 48 (completion) = 204 total
Cost: $0.0031
```

**JSON output:**

```json
{
  "prompt_name": "assistant-summarize",
  "model": "gpt-4o",
  "temperature": 0.3,
  "response": "• First key point...\n• Second...",
  "usage": {
    "prompt_tokens": 156,
    "completion_tokens": 48,
    "total_tokens": 204
  },
  "cost_usd": 0.0031,
  "latency_ms": 1234
}
```

**Dry run output:**

```
[DRY RUN] Would send to gpt-4o:

System: You are an expert content analyst...

User: Content to summarize:
---
Long article content here...
---

Variables applied:
  text: "Long article content here..."
  max_points: 5
  style: professional
```

---

### analyze

Analyze prompt effectiveness using an AI judge model.

```bash
blogus analyze <PROMPT> [OPTIONS]
```

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `PROMPT` | Prompt text, file path, or prompt name | Yes |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--judge-model MODEL` | Model to use for analysis | `gpt-4o` |
| `--goal TEXT` | Expected goal of the prompt | Auto-inferred |
| `--json` | Output as JSON | `false` |
| `--detailed` | Include fragment analysis | `false` |
| `--suggestions INT` | Number of improvement suggestions | 3 |
| `--output FILE` | Save analysis to file | stdout |

#### Examples

```bash
# Analyze prompt text directly
blogus analyze "You are a helpful assistant."

# Analyze from prompt file
blogus analyze prompts/assistant-summarize.prompt

# Analyze by prompt name
blogus analyze assistant-summarize

# Specify goal
blogus analyze assistant-summarize \
  --goal "Summarize content into clear, actionable bullet points"

# Use different judge model
blogus analyze assistant-summarize \
  --judge-model claude-3-opus-20240229

# Detailed analysis with fragment breakdown
blogus analyze assistant-summarize --detailed

# More suggestions
blogus analyze assistant-summarize --suggestions 5

# JSON output
blogus analyze assistant-summarize --json

# Save to file
blogus analyze assistant-summarize --output analysis.md
```

#### Output

**Standard output:**

```
Prompt Analysis: assistant-summarize
═══════════════════════════════════════════════════════════════════

Goal (inferred): Summarize content into clear, actionable bullet points

Scores:
  Goal Alignment:      8/10  ████████░░
  Effectiveness:       7/10  ███████░░░
  Clarity:             9/10  █████████░
  Specificity:         7/10  ███████░░░

Overall: Good prompt with room for improvement

Suggestions:
  1. Add explicit examples of good vs. poor bullet points to guide output
  2. Specify maximum word count per bullet point for consistency
  3. Include handling for edge cases (very short or very long content)

Strengths:
  ✓ Clear role definition ("expert content analyst")
  ✓ Specific guidelines for bullet point format
  ✓ Includes variable for customization (style, max_points)

Potential Issues:
  ⚠ No explicit handling for non-English content
  ⚠ Could benefit from output format examples
```

**Detailed output (with --detailed):**

```
Prompt Analysis: assistant-summarize
═══════════════════════════════════════════════════════════════════

[... scores as above ...]

Fragment Analysis:
───────────────────────────────────────────────────────────────────

Fragment 1: Role Definition
  Text: "You are an expert content analyst."
  Type: instruction
  Alignment: 4/5  ████░
  Suggestion: Consider adding specific domain expertise if applicable

Fragment 2: Task Description
  Text: "Your task is to distill complex information..."
  Type: instruction
  Alignment: 5/5  █████
  Suggestion: No changes needed

Fragment 3: Guidelines
  Text: "Guidelines:\n- Extract the {{max_points}}..."
  Type: constraint
  Alignment: 4/5  ████░
  Suggestion: Add examples of good bullet points

Fragment 4: Output Format
  Text: "Respond with exactly {{max_points}} bullet points..."
  Type: format
  Alignment: 4/5  ████░
  Suggestion: Specify what to do if content doesn't support full count

[... more fragments ...]
```

---

### test

Generate test cases for a prompt.

```bash
blogus test <PROMPT> [OPTIONS]
```

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `PROMPT` | Prompt text, file path, or prompt name | Yes |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--judge-model MODEL` | Model for test generation | `gpt-4o` |
| `--count INT` | Number of test cases to generate | 5 |
| `--output FILE` | Save tests to file | stdout |
| `--format FORMAT` | Output format (json, yaml, markdown) | `yaml` |
| `--include-edge-cases` | Include edge case tests | `true` |
| `--goal TEXT` | Expected goal for test generation | Auto-inferred |

#### Examples

```bash
# Generate tests for a prompt
blogus test assistant-summarize

# Generate more test cases
blogus test assistant-summarize --count 10

# Save to file
blogus test assistant-summarize --output tests.yaml

# JSON format
blogus test assistant-summarize --format json --output tests.json

# With specific goal
blogus test assistant-summarize \
  --goal "Accurately summarize business documents"

# Use different model
blogus test assistant-summarize \
  --judge-model claude-3-opus-20240229
```

#### Output

```yaml
# Generated test cases for: assistant-summarize
# Generated: 2024-01-15T10:30:00Z
# Model: gpt-4o

tests:
  - name: "standard_article"
    description: "Test with a typical news article"
    input:
      text: |
        Climate scientists have released new findings showing
        accelerated ice melt in Antarctica. The study, published
        in Nature, indicates sea levels could rise faster than
        previously predicted. Coastal cities may need to adapt
        their infrastructure within the next decade.
      max_points: 3
      style: professional
    expected_output_contains:
      - "Antarctica"
      - "sea level"
      - "coastal"
    goal_relevance: 5

  - name: "technical_content"
    description: "Test with technical documentation"
    input:
      text: |
        The new API endpoint supports OAuth 2.0 authentication
        with refresh tokens. Rate limiting is set to 100 requests
        per minute. Response format is JSON with optional XML.
      max_points: 3
      style: technical
    expected_output_contains:
      - "OAuth"
      - "rate limit"
      - "JSON"
    goal_relevance: 5

  - name: "edge_case_short"
    description: "Test with very short content"
    input:
      text: "The meeting is at 3pm."
      max_points: 3
      style: professional
    expected_behavior: "Should return fewer than 3 points"
    goal_relevance: 4

  - name: "edge_case_long"
    description: "Test with very long content"
    input:
      text: "[5000 word article...]"
      max_points: 5
      style: casual
    expected_behavior: "Should extract exactly 5 key points"
    goal_relevance: 5

  - name: "edge_case_non_english"
    description: "Test with non-English content"
    input:
      text: "La conferencia tratará sobre inteligencia artificial..."
      max_points: 3
      style: professional
    expected_behavior: "Should handle or indicate language limitation"
    goal_relevance: 3
```

---

### lock

Generate or update the lock file.

```bash
blogus lock [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dir PATH` | Prompts directory | `./prompts` |
| `--output FILE` | Lock file path | `./prompts.lock` |
| `--force` | Regenerate all hashes | `false` |
| `--include PATTERN` | Include only matching prompts | All |
| `--exclude PATTERN` | Exclude matching prompts | None |
| `--check` | Check if lock file needs update (exit 1 if yes) | `false` |
| `--json` | Output as JSON | `false` |

#### Examples

```bash
# Generate lock file
blogus lock

# Custom paths
blogus lock --dir ./my-prompts --output ./my-prompts.lock

# Force regenerate all hashes
blogus lock --force

# Lock only production prompts
blogus lock --include "*-prod.prompt"

# Exclude test prompts
blogus lock --exclude "*-test.prompt"

# Check if update needed (useful in CI)
blogus lock --check || echo "Lock file needs update"
```

#### Output

```
Generating lock file...

  Prompt                  Current Hash            Status
  ───────────────────────────────────────────────────────
  assistant-chat          sha256:7a8b9c0d...     ✓ unchanged
  assistant-summarize     sha256:1e2f3a4b...     ✓ unchanged
  assistant-translate     sha256:5c6d7e8f...     ↻ updated
  code-review             sha256:9a0b1c2d...     + new

Lock file written to: prompts.lock

Changes:
  Unchanged: 2
  Updated: 1
  New: 1
  Removed: 0
```

---

### verify

Verify that the lock file is up to date.

```bash
blogus verify [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dir PATH` | Prompts directory | `./prompts` |
| `--lock FILE` | Lock file path | `./prompts.lock` |
| `--strict` | Fail on any warnings | `false` |
| `--json` | Output as JSON | `false` |
| `--fix` | Automatically fix issues | `false` |

#### Examples

```bash
# Basic verification
blogus verify

# Strict mode (for CI)
blogus verify --strict

# Custom paths
blogus verify --dir ./my-prompts --lock ./my-prompts.lock

# Auto-fix issues
blogus verify --fix

# JSON output for scripting
blogus verify --json
```

#### Output

**Success:**

```
Verifying prompts...

  Prompt                  Lock Hash               File Hash               Status
  ─────────────────────────────────────────────────────────────────────────────────
  assistant-chat          sha256:7a8b9c0d...     sha256:7a8b9c0d...     ✓ match
  assistant-summarize     sha256:1e2f3a4b...     sha256:1e2f3a4b...     ✓ match
  assistant-translate     sha256:5c6d7e8f...     sha256:5c6d7e8f...     ✓ match

✓ All prompts verified successfully
```

**Failure:**

```
Verifying prompts...

  Prompt                  Lock Hash               File Hash               Status
  ─────────────────────────────────────────────────────────────────────────────────
  assistant-chat          sha256:7a8b9c0d...     sha256:7a8b9c0d...     ✓ match
  assistant-summarize     sha256:1e2f3a4b...     sha256:9x8y7z6w...     ✗ mismatch
  assistant-translate     sha256:5c6d7e8f...     sha256:5c6d7e8f...     ✓ match
  new-prompt              (not in lock)           sha256:abc123...       ⚠ unlocked

✗ Verification failed

Errors:
  - assistant-summarize: Hash mismatch (file was modified)

Warnings:
  - new-prompt: Not in lock file

Run 'blogus lock' to update the lock file.
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All prompts verified successfully |
| `1` | Hash mismatch or missing prompts |
| `2` | Lock file not found |
| `3` | Prompts directory not found |

---

### check

Find prompts in code that aren't versioned.

```bash
blogus check [OPTIONS] [PATH]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--json` | Output as JSON | `false` |
| `--include PATTERN` | Glob patterns to include | All supported |
| `--exclude PATTERN` | Glob patterns to exclude | Defaults |
| `--fail-on-unversioned` | Exit with code 1 if unversioned found | `false` |

#### Examples

```bash
# Check current directory
blogus check

# Check specific path
blogus check ./src

# Fail if unversioned found (for CI)
blogus check --fail-on-unversioned
```

---

### fix

Sync source code with prompt files.

```bash
blogus fix [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dir PATH` | Prompts directory | `./prompts` |
| `--dry-run` | Show changes without applying | `false` |
| `--backup / --no-backup` | Create backup of modified files | `true` |
| `--interactive / --no-interactive` | Confirm each change | `true` |
| `--include PATTERN` | Only fix matching files | All |
| `--exclude PATTERN` | Skip matching files | None |

#### Examples

```bash
# Interactive fix (default)
blogus fix

# Preview changes
blogus fix --dry-run

# Non-interactive (apply all)
blogus fix --no-interactive

# Skip backups
blogus fix --no-backup

# Fix specific files
blogus fix --include "src/api/**/*.py"
```

---

### fragments

Analyze prompt fragments for goal alignment.

```bash
blogus fragments <PROMPT> [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--judge-model MODEL` | Model for analysis | `gpt-4o` |
| `--goal TEXT` | Expected goal | Auto-inferred |
| `--json` | Output as JSON | `false` |

---

### goal

Infer the goal of a prompt.

```bash
blogus goal <PROMPT> [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--judge-model MODEL` | Model for inference | `gpt-4o` |
| `--json` | Output as JSON | `false` |

---

### logs

Generate diagnostic logs for a prompt.

```bash
blogus logs <PROMPT> [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--judge-model MODEL` | Model for analysis | `gpt-4o` |
| `--goal TEXT` | Expected goal | Auto-inferred |
| `--json` | Output as JSON | `false` |

---

## Web Commands

### blogus-web

Start the web interface server.

```bash
blogus-web [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host HOST` | Host to bind to | `127.0.0.1` |
| `--port PORT` | Port to listen on | `8000` |
| `--reload` | Enable auto-reload for development | `false` |
| `--prompts-dir PATH` | Prompts directory | `./prompts` |
| `--open` | Open browser automatically | `false` |

#### Examples

```bash
# Start with defaults
blogus-web

# Custom host/port
blogus-web --host 0.0.0.0 --port 3000

# Development mode with auto-reload
blogus-web --reload

# Open browser automatically
blogus-web --open
```

---

## Exit Codes Reference

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error or verification failure |
| `2` | Invalid arguments or configuration |
| `3` | File or directory not found |
| `4` | API error (rate limit, auth, etc.) |
| `5` | Parse error (invalid prompt file) |
| `130` | Interrupted (Ctrl+C) |

---

## Shell Completions

### Bash

```bash
# Add to ~/.bashrc
eval "$(_BLOGUS_COMPLETE=bash_source blogus)"
```

### Zsh

```zsh
# Add to ~/.zshrc
eval "$(_BLOGUS_COMPLETE=zsh_source blogus)"
```

### Fish

```fish
# Add to ~/.config/fish/completions/blogus.fish
_BLOGUS_COMPLETE=fish_source blogus | source
```
