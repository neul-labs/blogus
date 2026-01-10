# Prompt Format

Blogus uses `.prompt` files to manage prompts. Each file contains YAML frontmatter and a prompt body.

## Basic Structure

```yaml
---
name: my-prompt
description: A brief description
model:
  id: gpt-4o
  temperature: 0.7
variables:
  - name: input_var
    required: true
---
Your prompt content goes here.

Use {{input_var}} to insert variables.
```

## Frontmatter Fields

### name (required)

Unique identifier for the prompt. Used for referencing in code and CLI.

```yaml
---
name: customer-support
---
```

**Rules:**

- Must be unique across all prompts
- Use lowercase with hyphens
- No spaces or special characters

---

### description

Human-readable description of the prompt's purpose.

```yaml
---
name: summarize
description: Summarize long-form content into key points
---
```

---

### model

Configuration for the LLM model.

```yaml
---
model:
  id: gpt-4o
  temperature: 0.3
  max_tokens: 1000
  top_p: 0.9
---
```

**Subfields:**

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `id` | string | Model identifier | Required if model specified |
| `temperature` | float | Sampling temperature (0-2) | `1.0` |
| `max_tokens` | int | Maximum response tokens | Model default |
| `top_p` | float | Nucleus sampling parameter | `1.0` |

**Common Model IDs:**

| Model | ID |
|-------|-----|
| GPT-4o | `gpt-4o` |
| GPT-4 Turbo | `gpt-4-turbo` |
| GPT-3.5 Turbo | `gpt-3.5-turbo` |
| Claude 3 Opus | `claude-3-opus-20240229` |
| Claude 3 Sonnet | `claude-3-sonnet-20240229` |
| Claude 3 Haiku | `claude-3-haiku-20240307` |

---

### variables

Define input variables for the prompt template.

```yaml
---
variables:
  - name: text
    required: true
    description: The text to summarize
  - name: style
    default: formal
    description: Output style (formal/casual)
  - name: max_length
    type: integer
    default: 100
---
```

**Variable Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Variable name (required) |
| `required` | bool | Whether variable is required |
| `default` | any | Default value if not provided |
| `type` | string | Type hint (string, integer, etc.) |
| `description` | string | Human-readable description |

---

### tags

Categorize prompts with tags.

```yaml
---
tags:
  - summarization
  - content
  - gpt-4
---
```

---

### version

Manual version number (optional, auto-generated hash is preferred).

```yaml
---
version: 1.2.0
---
```

---

## Prompt Body

The body contains the actual prompt text, after the closing `---`.

### Basic Text

```yaml
---
name: assistant
---
You are a helpful assistant. Answer questions clearly and concisely.
```

### Variables

Use Mustache-style syntax `{{variable_name}}`:

```yaml
---
name: translate
variables:
  - name: text
    required: true
  - name: language
    default: French
---
Translate the following text to {{language}}:

{{text}}
```

### Multi-line Content

```yaml
---
name: code-review
variables:
  - name: code
    required: true
  - name: language
    default: python
---
Review the following {{language}} code for:
- Bugs and errors
- Performance issues
- Security vulnerabilities
- Code style

Code:
```{{language}}
{{code}}
```

Provide specific, actionable feedback.
```

---

## Complete Examples

### Simple Prompt

```yaml
---
name: greeting
description: Generate a friendly greeting
model:
  id: gpt-3.5-turbo
  temperature: 0.7
---
Generate a friendly, professional greeting for a customer service interaction.
```

### Parameterized Prompt

```yaml
---
name: summarize
description: Summarize content to key points
model:
  id: gpt-4o
  temperature: 0.3
variables:
  - name: content
    required: true
    description: The content to summarize
  - name: num_points
    type: integer
    default: 3
    description: Number of key points
  - name: style
    default: bullet
    description: Output style (bullet/paragraph)
tags:
  - summarization
  - content-processing
---
Summarize the following content into {{num_points}} key points.

Format: {{style}} points

Content:
{{content}}
```

### Complex Prompt with System Context

```yaml
---
name: code-assistant
description: AI coding assistant for development tasks
model:
  id: claude-3-sonnet-20240229
  temperature: 0.2
  max_tokens: 2000
variables:
  - name: task
    required: true
    description: The coding task to perform
  - name: language
    required: true
    description: Programming language
  - name: context
    description: Additional context or constraints
tags:
  - coding
  - development
  - assistant
---
You are an expert {{language}} developer. Your role is to help with coding tasks while following best practices.

Guidelines:
- Write clean, maintainable code
- Include appropriate error handling
- Add comments for complex logic
- Follow {{language}} conventions and idioms

Task: {{task}}

{{#context}}
Additional context: {{context}}
{{/context}}

Provide your solution with explanations.
```

---

## Template Syntax

### Basic Substitution

```
Hello, {{name}}!
```

### Conditional Sections

Show content only if variable is truthy:

```
{{#show_examples}}
Here are some examples:
- Example 1
- Example 2
{{/show_examples}}
```

### Inverted Sections

Show content only if variable is falsy:

```
{{^has_context}}
No additional context provided.
{{/has_context}}
```

### Escaping

Use triple braces to avoid HTML escaping (if needed):

```
{{{raw_html}}}
```

---

## Lock File Format

The `prompts.lock` file tracks versions:

```yaml
version: 1
generated: 2024-01-15T10:30:00Z
prompts:
  summarize:
    hash: sha256:a1b2c3d4e5f6789...
    commit: 4903f76
    modified: 2024-01-15T10:30:00Z
    file: prompts/summarize.prompt
  translate:
    hash: sha256:b2c3d4e5f6a7890...
    commit: 4903f76
    modified: 2024-01-14T08:15:00Z
    file: prompts/translate.prompt
```

**Lock File Fields:**

| Field | Description |
|-------|-------------|
| `version` | Lock file format version |
| `generated` | When lock file was generated |
| `prompts` | Map of prompt names to metadata |
| `hash` | SHA-256 hash of prompt content |
| `commit` | Git commit hash when last modified |
| `modified` | Last modification timestamp |
| `file` | Path to the prompt file |

---

## Best Practices

### Naming Conventions

- Use descriptive, lowercase names with hyphens
- Group related prompts with prefixes: `chat-greeting`, `chat-farewell`
- Avoid generic names like `prompt1`

### Variable Design

- Use clear, descriptive variable names
- Provide defaults where sensible
- Mark truly required variables as `required: true`
- Add descriptions for complex variables

### Model Configuration

- Set temperature based on use case:
    - Creative tasks: 0.7-1.0
    - Factual/analytical: 0.1-0.3
    - Balanced: 0.5
- Set `max_tokens` to prevent runaway responses

### Organization

- Keep one prompt per file
- Use consistent directory structure
- Add tags for discoverability
- Include meaningful descriptions

### Version Control

- Commit prompt files with your code
- Run `blogus lock` before committing
- Review prompt changes in PRs
- Use `blogus verify` in CI
