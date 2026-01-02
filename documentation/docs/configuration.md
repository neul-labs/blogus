# Configuration

Configure Blogus to match your project's needs.

---

## Configuration File

Blogus uses a YAML configuration file located at `.blogus/config.yaml` in your project root.

### Creating a Configuration File

```bash
# Create config directory
mkdir -p .blogus

# Create config file
cat > .blogus/config.yaml << 'EOF'
# Blogus Configuration
version: 1

prompts:
  directory: ./prompts
  lock_file: ./prompts.lock

defaults:
  model: gpt-4o
  judge_model: gpt-4o
  temperature: 0.7

scan:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/venv/**"
    - "**/.venv/**"
    - "**/dist/**"
    - "**/build/**"
    - "**/__pycache__/**"

output:
  color: true
  verbose: false
EOF
```

---

## Configuration Options

### version

Configuration file format version.

```yaml
version: 1
```

---

### prompts

Prompt file locations.

```yaml
prompts:
  # Directory containing .prompt files
  directory: ./prompts

  # Lock file location
  lock_file: ./prompts.lock

  # File extension for prompt files
  extension: .prompt

  # Template for new prompt files
  template: standard  # minimal, standard, detailed

  # Naming convention for auto-generated prompts
  naming: function  # function, file-function, custom
```

---

### defaults

Default values for commands.

```yaml
defaults:
  # Default model for execution
  model: gpt-4o

  # Default model for analysis/judging
  judge_model: gpt-4o

  # Default temperature
  temperature: 0.7

  # Default max tokens
  max_tokens: 1000

  # Default timeout in seconds
  timeout: 60
```

---

### scan

Configuration for the `scan` command.

```yaml
scan:
  # Glob patterns to include
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.jsx"
    - "**/*.tsx"
    - "**/*.mjs"
    - "**/*.cjs"

  # Glob patterns to exclude
  exclude:
    - "**/node_modules/**"
    - "**/venv/**"
    - "**/.venv/**"
    - "**/dist/**"
    - "**/build/**"
    - "**/__pycache__/**"
    - "**/.*/**"
    - "**/*.min.js"
    - "**/*.bundle.js"

  # Follow Python imports to find prompts
  follow_imports: false

  # Scan recursively
  recursive: true

  # Provider patterns to detect
  providers:
    openai:
      enabled: true
      patterns:
        - "openai.chat.completions.create"
        - "openai.Completion.create"
        - "ChatCompletion.create"
    anthropic:
      enabled: true
      patterns:
        - "anthropic.messages.create"
        - "anthropic.completions.create"
    litellm:
      enabled: true
      patterns:
        - "litellm.completion"
        - "litellm.acompletion"
    langchain:
      enabled: true
      patterns:
        - "ChatPromptTemplate"
        - "PromptTemplate"
        - "SystemMessagePromptTemplate"

    # Custom provider detection
    custom:
      enabled: false
      patterns: []
```

---

### analysis

Configuration for analysis commands.

```yaml
analysis:
  # Default judge model for analysis
  judge_model: gpt-4o

  # Number of suggestions to generate
  suggestions: 3

  # Include fragment analysis by default
  detailed: false

  # Analysis aspects to check
  aspects:
    - goal_alignment
    - effectiveness
    - clarity
    - specificity
    - safety

  # Minimum scores to pass (for CI)
  thresholds:
    goal_alignment: 6
    effectiveness: 6
    clarity: 7
```

---

### output

Output formatting options.

```yaml
output:
  # Enable colored output
  color: true

  # Default verbosity (0=quiet, 1=normal, 2=verbose, 3=debug)
  verbosity: 1

  # Default output format
  format: text  # text, json, yaml

  # Progress indicators
  progress: true

  # Show token usage
  show_usage: true

  # Show cost estimates
  show_cost: true
```

---

### ci

CI/CD specific settings.

```yaml
ci:
  # Strict mode for verify command
  strict: true

  # Fail on warnings
  fail_on_warnings: false

  # Required minimum scores
  quality_gate:
    enabled: true
    min_alignment: 7
    min_effectiveness: 6

  # Auto-fix in CI (not recommended)
  auto_fix: false
```

---

### backup

Backup settings for the `fix` command.

```yaml
backup:
  # Enable backups when modifying files
  enabled: true

  # Backup directory
  directory: .blogus/backups

  # Keep backups for N days
  retention_days: 30

  # Maximum backup size in MB
  max_size_mb: 100
```

---

### models

Model-specific configurations.

```yaml
models:
  # Model aliases
  aliases:
    gpt4: gpt-4o
    claude: claude-3-sonnet-20240229
    fast: gpt-3.5-turbo
    smart: claude-3-opus-20240229

  # Model-specific settings
  settings:
    gpt-4o:
      max_tokens: 4096
      timeout: 60

    claude-3-opus-20240229:
      max_tokens: 4096
      timeout: 120

    gpt-3.5-turbo:
      max_tokens: 4096
      timeout: 30

  # Fallback models (in order of preference)
  fallbacks:
    - gpt-4o
    - claude-3-sonnet-20240229
    - gpt-3.5-turbo
```

---

### api

API configuration.

```yaml
api:
  # Retry settings
  retry:
    max_attempts: 3
    backoff_factor: 2
    max_delay: 60

  # Timeout settings
  timeout:
    connect: 10
    read: 60
    total: 120

  # Rate limiting
  rate_limit:
    requests_per_minute: 60
    tokens_per_minute: 90000
```

---

### web

Web interface configuration.

```yaml
web:
  # Server settings
  host: 127.0.0.1
  port: 8000

  # Enable auto-reload for development
  reload: false

  # CORS settings
  cors:
    enabled: true
    origins:
      - "http://localhost:3000"
      - "http://localhost:8000"

  # Authentication (optional)
  auth:
    enabled: false
    type: api_key  # api_key, oauth
```

---

## Environment Variables

All configuration options can be overridden with environment variables:

```bash
# Prompts directory
export BLOGUS_PROMPTS_DIR="./my-prompts"

# Lock file
export BLOGUS_LOCK_FILE="./my-prompts.lock"

# Default model
export BLOGUS_MODEL="gpt-4o"

# Judge model
export BLOGUS_JUDGE_MODEL="claude-3-opus-20240229"

# Default temperature
export BLOGUS_TEMPERATURE="0.7"

# Verbosity
export BLOGUS_VERBOSE="1"

# Color output
export BLOGUS_COLOR="true"

# Config file location
export BLOGUS_CONFIG="./.blogus/config.yaml"

# API keys (provider-specific)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk_..."
```

---

## Project-Specific Configuration

### Monorepo Configuration

For monorepos with multiple prompt directories:

```yaml
# .blogus/config.yaml
version: 1

prompts:
  # Use a shared prompts directory
  directory: ./shared/prompts
  lock_file: ./shared/prompts.lock

scan:
  include:
    - "packages/*/src/**/*.py"
    - "packages/*/src/**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/dist/**"
```

Or use separate configs per package:

```bash
# packages/api/.blogus/config.yaml
# packages/web/.blogus/config.yaml
# packages/worker/.blogus/config.yaml
```

---

### Team Configuration

For team-wide settings, commit the config file:

```yaml
# .blogus/config.yaml (committed)
version: 1

prompts:
  directory: ./prompts
  lock_file: ./prompts.lock

defaults:
  model: gpt-4o
  judge_model: gpt-4o

# Team standards
analysis:
  thresholds:
    goal_alignment: 7
    effectiveness: 7
    clarity: 8

ci:
  strict: true
  quality_gate:
    enabled: true
    min_alignment: 7
```

For personal overrides, use `.blogus/config.local.yaml` (add to `.gitignore`):

```yaml
# .blogus/config.local.yaml (not committed)
defaults:
  model: gpt-3.5-turbo  # Use cheaper model locally

output:
  verbosity: 2  # More verbose locally
```

---

### Language-Specific Configuration

#### Python Projects

```yaml
# .blogus/config.yaml
version: 1

scan:
  include:
    - "**/*.py"
  exclude:
    - "**/venv/**"
    - "**/.venv/**"
    - "**/site-packages/**"
    - "**/__pycache__/**"
    - "**/test_*.py"
    - "**/tests/**"
  providers:
    openai:
      enabled: true
    anthropic:
      enabled: true
    langchain:
      enabled: true
```

#### JavaScript/TypeScript Projects

```yaml
# .blogus/config.yaml
version: 1

scan:
  include:
    - "**/*.js"
    - "**/*.ts"
    - "**/*.jsx"
    - "**/*.tsx"
    - "**/*.mjs"
  exclude:
    - "**/node_modules/**"
    - "**/dist/**"
    - "**/build/**"
    - "**/*.min.js"
    - "**/*.test.js"
    - "**/*.spec.ts"
```

---

## Configuration Precedence

Configuration is applied in this order (later overrides earlier):

1. Built-in defaults
2. Global config (`~/.config/blogus/config.yaml`)
3. Project config (`.blogus/config.yaml`)
4. Local config (`.blogus/config.local.yaml`)
5. Environment variables (`BLOGUS_*`)
6. Command-line arguments

---

## Validating Configuration

```bash
# Check configuration
blogus config validate

# Show effective configuration
blogus config show

# Show specific setting
blogus config get defaults.model
```

---

## Example Configurations

### Minimal Configuration

```yaml
version: 1

prompts:
  directory: ./prompts

defaults:
  model: gpt-4o
```

### Development Configuration

```yaml
version: 1

prompts:
  directory: ./prompts
  lock_file: ./prompts.lock

defaults:
  model: gpt-3.5-turbo  # Cheaper for development
  temperature: 0.7

output:
  verbosity: 2
  show_usage: true
  show_cost: true

backup:
  enabled: true
```

### Production Configuration

```yaml
version: 1

prompts:
  directory: ./prompts
  lock_file: ./prompts.lock

defaults:
  model: gpt-4o
  temperature: 0.3  # More deterministic

analysis:
  thresholds:
    goal_alignment: 8
    effectiveness: 7
    clarity: 8

ci:
  strict: true
  quality_gate:
    enabled: true
    min_alignment: 8
    min_effectiveness: 7

api:
  retry:
    max_attempts: 5
    backoff_factor: 2
```
