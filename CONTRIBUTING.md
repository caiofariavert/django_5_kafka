# Contributing to Django Kafka

Thank you for your interest in contributing to Django Kafka! This document provides guidelines for contribution.

## 🚀 How to contribute

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/django_kafka.git
cd django_kafka
```

### 2. Setup development environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requeriments.txt
```

### 3. Create branch for your feature

```bash
git checkout -b feature/new-functionality
# or
git checkout -b fix/bug-fix
```

## 📝 Code standards

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import organization
- **flake8** for linting

```bash
# Format code
black django_kafka/
isort django_kafka/

# Check code
flake8 django_kafka/
```

### Naming conventions

- **Functions and variables**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_CASE
- **Files**: snake_case

### Docstrings

Use Google format docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Returns:
        Description of return value

    Raises:
        ValueError: When error X occurs
    """
    pass
```

## 🧪 Tests

### Run tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=django_kafka
```

### Write tests

- Create tests for all new features
- Maintain coverage above 80%
- Use descriptive names for tests

```python
def test_producer_should_send_message_successfully():
    """Test that producer sends message successfully."""
    # Arrange
    topic = "test-topic"
    message = "test message"

    # Act
    result = producer(topic, message)

    # Assert
    assert result is None  # Producer returns no value on success
```

## 📋 Pull Request checklist

Before submitting your PR, check:

- [ ] Code is formatted with black/isort
- [ ] Passed flake8 without warnings
- [ ] Tests were added/updated
- [ ] Documentation was updated
- [ ] CHANGELOG was updated
- [ ] Commit messages are clear

### Commit template

```
type(scope): brief description

More detailed description if necessary.

Closes #123
```

Valid types:
- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation
- `style`: formatting
- `refactor`: refactoring
- `test`: tests
- `chore`: maintenance

## 🐛 Report bugs

Use the GitHub issue template with:

1. **Problem description**
2. **Steps to reproduce**
3. **Expected behavior**
4. **Current behavior**
5. **Environment** (Python, Django, OS)
6. **Relevant logs**

## 💡 Suggest features

For new features:

1. Open an issue first for discussion
2. Describe the use case
3. Propose the API
4. Consider performance impact
5. Check version compatibility

## 📚 Documentation

When modifying features:

1. Update docstrings
2. Update README if necessary
3. Add usage examples
4. Update CHANGELOG

## ❓ Questions

- Open an issue with "question" label
- Contact: thiago@vert-capital.com.br

## 📄 License

By contributing, you agree that your contributions will be licensed under the same MIT license of the project.
