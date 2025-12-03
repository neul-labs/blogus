# Contributing to Blogus

We welcome contributions to Blogus! This guide will help you get started with contributing to the project.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your feature or bug fix
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- uv (for dependency management)
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/your-username/blogus.git
cd blogus

# Install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=blogus

# Run specific test files
uv run pytest tests/test_core.py
```

## Project Structure

```
blogus/
├── blogus/              # Main package
│   ├── __init__.py      # Package initialization
│   ├── cli.py           # Command-line interface
│   ├── core.py          # Core prompt engineering functionality
│   ├── web.py           # Web interface (FastAPI)
│   └── web_cli.py       # Web interface CLI entry point
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_cli.py      # CLI tests
│   ├── test_core.py     # Core functionality tests
│   ├── test_web.py      # Web interface tests
│   └── test_web_functionality.py
├── docs/                # Documentation
├── examples/            # Usage examples
├── app/                 # Web application files
│   ├── __init__.py
│   ├── main.py          # Backward compatibility entry point
│   ├── static/          # Static files (CSS, JS, images)
│   └── templates/       # Jinja2 templates
├── pyproject.toml       # Project configuration
├── uv.lock              # Dependency lock file
├── README.md            # Project README
├── CONTRIBUTING.md      # This file
└── LICENSE              # License information
```

## Code Style

We follow the Python community standards:

1. **PEP 8**: Code should follow PEP 8 style guidelines
2. **Type Hints**: Use type hints for function parameters and return values
3. **Docstrings**: All public functions and classes should have docstrings
4. **Naming**: Use descriptive names for variables, functions, and classes

### Formatting Tools

```bash
# Format code with Black
uv run black .

# Check code style with Flake8
uv run flake8

# Type checking with MyPy
uv run mypy .
```

## Making Changes

### Branching Strategy

1. Create a new branch for each feature or bug fix
2. Use descriptive branch names (e.g., `feature/prompt-versioning`, `bugfix/analysis-error-handling`)
3. Keep branches focused on a single issue

### Commit Messages

Follow the conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Example:
```
feat(core): add prompt versioning functionality

Implement version tracking for prompts with hash-based
deduplication and metadata support.

Closes #123
```

### Pull Request Process

1. Ensure your code passes all tests
2. Update documentation if you've changed functionality
3. Add tests for new features
4. Make sure your commit messages are clear and follow the convention
5. Submit a pull request with a clear description of the changes

## Testing

### Writing Tests

1. Place tests in the `tests/` directory
2. Follow the existing test structure
3. Use pytest for test framework
4. Mock external dependencies when possible
5. Test both positive and negative cases

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test interactions between components
3. **CLI Tests**: Test command-line interface functionality
4. **Web Tests**: Test web interface functionality

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests in a specific file
uv run pytest tests/test_core.py

# Run tests with a specific marker
uv run pytest -m "slow"

# Run tests and generate coverage report
uv run pytest --cov=logus --cov-report=html
```

## Documentation

### Updating Documentation

1. Update docstrings in the code when changing functionality
2. Update markdown documentation in the `docs/` directory
3. Add new documentation files when adding significant features
4. Keep the documentation structure consistent

### API Documentation

API documentation is generated from docstrings. Ensure all public functions and classes have comprehensive docstrings.

## Adding New Features

### Before You Start

1. Check if there's already an issue or discussion about the feature
2. Create an issue to discuss the feature if one doesn't exist
3. Get feedback from maintainers before implementing

### Implementation Guidelines

1. Keep changes focused and modular
2. Follow existing code patterns and conventions
3. Add comprehensive tests
4. Update documentation
5. Consider backward compatibility

### Model Support

When adding support for new models:

1. Ensure compatibility with LiteLLM
2. Add the model to the appropriate enums
3. Update documentation
4. Add tests if necessary

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. A clear description of the issue
2. Steps to reproduce
3. Expected vs. actual behavior
4. Environment information (Python version, OS, etc.)
5. Any relevant error messages or logs

### Feature Requests

When requesting features:

1. Describe the problem you're trying to solve
2. Explain why the feature would be valuable
3. Provide examples of how you'd use the feature
4. Consider any potential drawbacks or tradeoffs

## Community

### Communication

- GitHub Issues: For bug reports and feature requests
- GitHub Discussions: For general discussion and questions
- Pull Requests: For code contributions

### Getting Help

If you need help with contributing:

1. Check the existing documentation
2. Look at previous pull requests for examples
3. Ask questions in GitHub Discussions
4. Reach out to maintainers if needed

## License

By contributing to Logus, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:

1. Git commit history
2. GitHub contributors list
3. Release notes for significant contributions

Thank you for contributing to Logus!
