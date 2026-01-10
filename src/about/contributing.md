# Contributing to DataJoint

DataJoint is developed openly and welcomes contributions from the community.

## Ways to Contribute

### Report Issues

Found a bug or have a feature request? Open an issue on GitHub:

- [datajoint-python issues](https://github.com/datajoint/datajoint-python/issues)
- [datajoint-docs issues](https://github.com/datajoint/datajoint-docs/issues)

### Improve Documentation

Documentation improvements are valuable contributions:

1. Fork the [datajoint-docs](https://github.com/datajoint/datajoint-docs) repository
2. Make your changes
3. Submit a pull request

### Contribute Code

For code contributions to datajoint-python:

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

See the [Developer Guide](https://github.com/datajoint/datajoint-python/blob/main/CONTRIBUTING.md)
for detailed instructions.

## Development Setup

### datajoint-python

```bash
git clone https://github.com/datajoint/datajoint-python.git
cd datajoint-python
pip install -e ".[dev]"
pre-commit install
```

### datajoint-docs

```bash
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs
pip install -r pip_requirements.txt
mkdocs serve
```

## Code Style

- Python code follows [PEP 8](https://pep8.org/)
- Docstrings use [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html)
- Pre-commit hooks enforce formatting

## Testing

```bash
# Run unit tests
pytest tests/unit

# Run integration tests (requires Docker)
DOCKER_HOST=unix:///path/to/docker.sock pytest tests/
```

## Questions?

- Open a [GitHub Discussion](https://github.com/datajoint/datajoint-python/discussions)
- Join the [DataJoint Slack](https://datajoint.slack.com)
