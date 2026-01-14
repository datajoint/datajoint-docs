# Contributing to DataJoint

DataJoint is developed openly and welcomes contributions from the community.

## Ways to Contribute

### Report Issues

Found a bug or have a feature request? Open an issue on GitHub:

- [datajoint-python issues](https://github.com/datajoint/datajoint-python/issues)
- [datajoint-docs issues](https://github.com/datajoint/datajoint-docs/issues)

### Propose Enhancements (RFC Process)

For significant changes to DataJoint—new features, API changes, or specification updates—we use an RFC (Request for Comments) process via GitHub Discussions.

**When to use an RFC:**

- API changes or new features in datajoint-python
- Changes to the DataJoint specification
- Breaking changes or deprecations
- Major documentation restructuring

**RFC Process:**

1. **Propose** — Create a new Discussion using the RFC template in the appropriate repository:
   - [datajoint-python Discussions](https://github.com/datajoint/datajoint-python/discussions/new?category=rfc)
   - [datajoint-docs Discussions](https://github.com/datajoint/datajoint-docs/discussions/new?category=rfc)

2. **Discuss** — Community and maintainers provide feedback (2-4 weeks). Use 👍/👎 reactions to signal support. Prototyping in parallel is encouraged.

3. **Final Comment Period** — Once consensus emerges, maintainers announce a 1-2 week final comment period. No changes during this time.

4. **Decision** — RFC is accepted, rejected, or postponed. Accepted RFCs become tracking issues for implementation.

**RFC Labels:**

| Label | Meaning |
|-------|---------|
| `rfc` | All enhancement proposals |
| `status: proposed` | Initial submission |
| `status: under-review` | Active discussion |
| `status: final-comment` | Final comment period |
| `status: accepted` | Approved for implementation |
| `status: rejected` | Not accepted |
| `status: postponed` | Deferred to future |

**Tips for a good RFC:**

- Search existing discussions first
- Include concrete use cases and code examples
- Consider backwards compatibility
- Start with motivation before diving into design

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

See the [Developer Guide](https://github.com/datajoint/datajoint-python/blob/main/CONTRIBUTING.md)
for current testing instructions using `pixi` and `testcontainers`.

## Questions?

- Open a [GitHub Discussion](https://github.com/datajoint/datajoint-python/discussions)
