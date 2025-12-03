# Blogus Documentation

**`package.lock` for AI prompts.**

## Quick Try

```bash
uvx blogus scan
```

## The Workflow

```
SCAN → VERSION → LOCK → SYNC
```

1. **Scan** - Find all LLM API calls in your codebase
2. **Version** - Store prompts in `.prompt` files
3. **Lock** - Generate `prompts.lock` with content hashes
4. **Sync** - Update code when prompts change

## Guides

| Guide | Description |
|-------|-------------|
| [Getting Started](getting_started.md) | Installation and first scan |
| [Core Concepts](core_concepts.md) | How scanning, versioning, and syncing work |
| [.prompt Format](prompt_files.md) | File format reference |
| [CLI Reference](cli.md) | All commands |
| [Web Interface](web_interface.md) | Web UI guide |

## Quick Reference

```bash
# Scan
blogus scan              # Find LLM calls
blogus init              # Create prompts/

# Version
blogus prompts           # List .prompt files
blogus exec <name>       # Run with variables
blogus analyze           # Evaluate effectiveness
blogus test              # Generate test cases

# Lock
blogus lock              # Generate prompts.lock
blogus verify            # Check lock (for CI)

# Sync
blogus check             # Find unversioned prompts
blogus fix               # Update code
```

## Links

- [GitHub](https://github.com/terraprompt/blogus)
- [PyPI](https://pypi.org/project/blogus/)
- [Issues](https://github.com/terraprompt/blogus/issues)
