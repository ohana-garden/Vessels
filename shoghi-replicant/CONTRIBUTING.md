# Contributing to Shoghi Replicant

Thank you for your interest in contributing to Shoghi Replicant! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project follows principles inspired by the Bahá'í Faith:

- **Unity**: Work together with respect and kindness
- **Truthfulness**: Be honest and transparent in all communications
- **Justice**: Treat all contributors fairly and equitably
- **Service**: Contribute for the benefit of the community

## Getting Started

### Prerequisites

- Python 3.10+
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Setting Up Development Environment

1. **Fork the repository**

   Visit the GitHub repo and click "Fork"

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/shoghi-replicant.git
   cd shoghi-replicant
   ```

3. **Start the development environment**

   ```bash
   ./start.sh
   ```

4. **Access the application**

   Open http://localhost:5000

## Development Workflow

### 1. Create a Branch

Use descriptive branch names:

```bash
# Feature
git checkout -b feature/add-new-agent-type

# Bug fix
git checkout -b fix/grant-search-timeout

# Documentation
git checkout -b docs/update-api-guide

# Refactoring
git checkout -b refactor/simplify-memory-system
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
docker exec -it shoghi-replicant pytest

# Run specific test file
docker exec -it shoghi-replicant pytest tests/test_moral_constraints.py

# Run with coverage
docker exec -it shoghi-replicant pytest --cov=shoghi
```

### 4. Commit Your Changes

Use meaningful commit messages:

```bash
git add .
git commit -m "feat: Add support for multi-language grant discovery

- Implement Spanish language support
- Add translation layer for grant descriptions
- Update documentation with language configuration"
```

**Commit Message Format:**

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 5. Push to Your Fork

```bash
git push origin feature/add-new-agent-type
```

### 6. Open a Pull Request

- Go to the original repository
- Click "New Pull Request"
- Select your branch
- Fill out the PR template
- Link any related issues

## Pull Request Process

### PR Checklist

Before submitting, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] PR description explains changes

### Review Process

1. **Automated Checks**: CI/CD will run tests automatically
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

### After Merge

- Delete your branch
- Pull latest changes from main
- Celebrate your contribution! 🎉

## Coding Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [flake8](https://flake8.pycqa.org/) for linting

```bash
# Format code
docker exec -it shoghi-replicant black .

# Lint code
docker exec -it shoghi-replicant flake8
```

### Code Organization

- Keep functions focused and small
- Use meaningful variable names
- Add docstrings to all functions and classes
- Comment complex logic

**Example:**

```python
def calculate_virtue_score(state: AgentState) -> float:
    """
    Calculate the virtue alignment score for an agent state.

    Args:
        state: The current agent state in 12D phase space

    Returns:
        float: Virtue score between 0.0 (misaligned) and 1.0 (aligned)

    Raises:
        ValueError: If state dimensions are invalid
    """
    # Implementation here
    pass
```

### Docker Best Practices

- Keep images small
- Use multi-stage builds
- Don't store secrets in images
- Add .dockerignore appropriately

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── fixtures/       # Test fixtures and data
```

### Writing Tests

```python
import pytest
from shoghi.constraints import BahaiManifold

def test_virtue_projection():
    """Test that virtue projection maintains manifold invariants"""
    manifold = BahaiManifold()
    state = create_test_state()

    projected = manifold.project(state)

    assert manifold.is_valid(projected)
    assert projected.dimension == 12
```

### Running Tests

```bash
# All tests
./start.sh shell
pytest

# Specific module
pytest tests/test_moral_constraints.py

# With coverage
pytest --cov=shoghi --cov-report=html

# Verbose output
pytest -vv
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints

### README Updates

- Update README.md for significant changes
- Add examples for new features
- Keep installation instructions current

### API Documentation

- Document all API endpoints
- Provide request/response examples
- Note authentication requirements

## Areas for Contribution

### High Priority

- **Moral Constraint Enhancements**: Improve virtue inference algorithms
- **Agent Templates**: Create new agent types for common use cases
- **Testing**: Increase test coverage, especially integration tests
- **Documentation**: API docs, tutorials, examples

### Medium Priority

- **Performance**: Optimize database queries, caching strategies
- **UI/UX**: Improve voice interface, add visualizations
- **Integrations**: Add connectors for more external services

### Good First Issues

Look for issues tagged `good-first-issue` - these are great entry points!

## Project Structure

Understanding the codebase:

```
shoghi-replicant/
├── shoghi/                 # Moral constraint system
│   ├── constraints/        # Manifold and validation
│   ├── measurement/        # State tracking
│   ├── gating/            # Action gating
│   └── intervention/      # Interventions
├── agent_zero_core.py     # Meta-coordination
├── community_memory.py    # Persistent memory
├── content_generation.py  # Content creation
├── grant_coordination_system.py  # Grant discovery
└── kala.py               # Value tracking
```

## Getting Help

### Resources

- **Documentation**: See [README.md](README.md)
- **Architecture**: Read [SHOGHI_FINAL_COMPLETE.md](SHOGHI_FINAL_COMPLETE.md)
- **Issues**: Check [GitHub Issues](https://github.com/ohana-garden/shoghi/issues)

### Questions?

- Open a GitHub Discussion
- Tag maintainers in issues
- Join our community chat (if available)

## Recognition

Contributors are recognized in:

- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for making Shoghi Replicant better! 🌺**
