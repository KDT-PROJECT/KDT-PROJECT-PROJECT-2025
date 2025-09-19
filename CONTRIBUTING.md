# Contributing to Seoul Commercial Analysis LLM System

Thank you for your interest in contributing to this project! This document provides guidelines for contributing to the Seoul Commercial Analysis LLM System.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Use the issue template provided
3. Provide clear reproduction steps
4. Include relevant system information

### Suggesting Enhancements

1. Use the feature request template
2. Describe the enhancement clearly
3. Explain why it would be useful
4. Provide examples if possible

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Run code quality checks
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Git

### Setup Steps

1. Fork and clone the repository
2. Create a virtual environment
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
5. Initialize the database
6. Run tests to ensure everything works

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions and classes
- Keep functions small and focused
- Use meaningful variable names

### Code Quality

- All code must pass `ruff` linting
- All code must be formatted with `black`
- All code must pass `mypy` type checking
- All tests must pass
- Code coverage should be maintained above 80%

### Testing

- Write unit tests for new functionality
- Write integration tests for complex workflows
- Update existing tests when modifying functionality
- Ensure tests are deterministic and fast

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) for our commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for test changes
- `chore:` for maintenance tasks

### Examples

```bash
feat: add hybrid RAG search functionality
fix: resolve SQL query validation issue
docs: update README with new installation steps
style: format code with black
refactor: extract common database operations
test: add unit tests for text-to-SQL conversion
chore: update dependencies
```

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Documentation is updated if needed
- [ ] Commit messages follow conventional format

### PR Description

- Clearly describe what the PR does
- Reference any related issues
- Include screenshots for UI changes
- List any breaking changes

### Review Process

- All PRs require at least 2 reviews
- Maintainers will review code quality, functionality, and tests
- Address feedback promptly
- Keep PRs small and focused (max 400 lines)

## Project Structure

```
KDT_project/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration management
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── utils/                    # Utility modules
├── pipelines/                # Data processing pipelines
├── tests/                    # Test suite
├── docs/                     # Documentation
└── .github/                  # GitHub workflows and templates
```

## Getting Help

- Check existing issues and discussions
- Join our community discussions
- Contact maintainers directly for urgent issues

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to the Seoul Commercial Analysis LLM System! 🚀
