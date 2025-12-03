# Blogus Documentation

Blogus helps you **extract, test, version, and sync** AI prompts across your codebase.

## The Workflow

```
EXTRACT → TEST → VERSION → UPDATE
```

1. **Extract**: Scan your codebase to find all LLM API calls
2. **Test**: Analyze prompts and generate test cases
3. **Version**: Store in `.prompt` files with lock file
4. **Update**: Sync improved prompts back to your code

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](getting_started.md) | Installation and first scan |
| [Core Concepts](core_concepts.md) | How extraction, versioning, and syncing work |
| [Prompt Files](prompt_files.md) | `.prompt` file format reference |
| [CLI Reference](cli.md) | All commands documented |
| [Web Interface](web_interface.md) | Using the web UI |
| [Library Usage](library.md) | Python API for programmatic use |

## Quick Reference

### Extract Prompts
```bash
blogus scan              # Find all LLM calls in your code
blogus init              # Create prompts/ directory
```

### Test Prompts
```bash
blogus analyze <prompt>  # Analyze effectiveness
blogus test <prompt>     # Generate test cases
blogus exec <name>       # Execute with variables
```

### Version Prompts
```bash
blogus prompts           # List all .prompt files
blogus lock              # Generate prompts.lock
blogus verify            # Verify against lock (for CI)
```

### Update Code
```bash
blogus check             # Find unversioned prompts
blogus fix --dry-run     # Preview code updates
blogus fix               # Sync .prompt changes to code
```

## Links

- [GitHub Repository](https://github.com/terraprompt/blogus)
- [PyPI Package](https://pypi.org/project/blogus/)
- [Issue Tracker](https://github.com/terraprompt/blogus/issues)
