# Web Interface

Blogus provides a visual interface for prompt management.

## Starting the Server

```bash
pip install blogus[web]
blogus-web
```

Open `http://localhost:8000` in your browser.

## Features

### Prompt Library

Browse and manage all `.prompt` files in your project:
- List prompts with Git status (modified/clean)
- Filter by category
- Quick edit, analyze, or delete
- View version history per prompt

### Prompt Editor

Create and edit prompts with:
- YAML frontmatter validation
- Template syntax highlighting
- Variable detection
- Live preview

### Project Scanner

Visualize LLM API calls in your codebase:
- See all detected calls with file/line
- Identify versioned vs unversioned prompts
- Link detections to `.prompt` files
- Filter by Python or JavaScript

### Git Integration

Manage versions directly from the UI:
- See modified files at a glance
- Commit changes with a message
- View commit history per prompt

### Analysis Dashboard

Test and analyze prompts:
- Run analysis for effectiveness
- Generate test cases
- Execute prompts with variables
- Compare responses across models

## API Endpoints

The web interface exposes a REST API.

### Prompt Files

```
GET  /api/v1/prompt-files/           # List all prompts
GET  /api/v1/prompt-files/{name}     # Get prompt details
POST /api/v1/prompt-files/           # Create new prompt
PUT  /api/v1/prompt-files/{name}     # Update prompt
DELETE /api/v1/prompt-files/{name}   # Delete prompt
```

### Rendering

```
POST /api/v1/prompt-files/{name}/render
Body: {"variables": {"key": "value"}}
```

### Version History

```
GET /api/v1/prompt-files/{name}/history
```

### Git Operations

```
GET  /api/v1/prompt-files/git/status        # Get status
POST /api/v1/prompt-files/{name}/commit     # Commit one
POST /api/v1/prompt-files/git/commit-all    # Commit all
Body: {"message": "Commit message"}
```

### Scanning

```
POST /api/v1/prompt-files/scan
Query: ?include_python=true&include_js=true
```

### Analysis

```
POST /api/analyze-prompt
Body: {
  "prompt": "...",
  "target_model": "gpt-4o",
  "judge_model": "claude-3-opus",
  "goal": "optional"
}

POST /api/generate-test
Body: {
  "prompt": "...",
  "judge_model": "gpt-4o"
}

POST /api/execute-prompt
Body: {
  "prompt": "...",
  "target_model": "gpt-4o"
}

POST /api/infer-goal
Body: {
  "prompt": "...",
  "judge_model": "gpt-4o"
}
```

## Keyboard Shortcuts

- `Ctrl+S` - Save current prompt
- `Ctrl+Enter` - Execute prompt
- `Ctrl+Shift+A` - Analyze prompt
