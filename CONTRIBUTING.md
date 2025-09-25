# Contributing to Blogus

Thank you for your interest in contributing to Blogus! We welcome contributions from the community to help improve this tool for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug in Blogus, please open an issue on our [GitHub issue tracker](https://github.com/terraprompt/blogus/issues) with the following information:

1. A clear and descriptive title
2. A detailed description of the problem
3. Steps to reproduce the issue
4. Expected behavior vs. actual behavior
5. Your environment information (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for new features or improvements to existing functionality. Please open an issue on our GitHub repository with:

1. A clear and descriptive title
2. A detailed explanation of the proposed enhancement
3. The problem this enhancement would solve
4. Any implementation ideas you might have

### Code Contributions

To contribute code to Blogus, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Commit your changes with a clear commit message
7. Push your branch to your fork
8. Open a pull request

## Development Setup

1. Clone your fork of the repository:
   ```bash
   git clone https://github.com/your-username/blogus.git
   cd blogus
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .[dev]
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

We follow the [PEP 8](https://pep8.org/) style guide for Python code. Please ensure your code adheres to these standards.

## Testing

All contributions should include appropriate tests. We use pytest for testing. To run the tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=blogus
```

## Documentation

Please ensure that your contributions include appropriate documentation updates. This includes:

1. Docstrings for new functions and classes
2. Updates to README.md if functionality changes
3. Comments in complex code sections

## Pull Request Guidelines

When submitting a pull request, please:

1. Include a clear and descriptive title
2. Provide a detailed description of the changes
3. Reference any related issues
4. Ensure all tests pass
5. Follow the existing code style
6. Keep changes focused and atomic

## Questions?

If you have any questions about contributing, feel free to open an issue or contact the maintainers directly.

Thank you for helping make Blogus better!