# DataJoint Documentation

Official documentation for [DataJoint](https://github.com/datajoint/datajoint-python),
an open-source framework for building scientific data pipelines.

**Live site:** https://docs.datajoint.com

## What is DataJoint?

DataJoint is a Python framework for building scientific data pipelines using relational
databases. It implements the **Relational Workflow Model**—a paradigm that extends
relational databases with native support for computational workflows.

Key features:

- **Declarative schema design** — Define tables and relationships in Python
- **Automatic dependency tracking** — Foreign keys encode workflow dependencies
- **Built-in computation** — Imported and Computed tables run automatically
- **Data integrity** — Referential integrity and transaction support
- **Reproducibility** — Immutable data with full provenance

## Documentation Structure

This documentation follows the [Diátaxis](https://diataxis.fr/) framework:

| Section | Purpose |
|---------|---------|
| [Concepts](src/explanation/) | Understand the principles behind DataJoint |
| [Tutorials](src/tutorials/) | Learn by building real pipelines (Jupyter notebooks) |
| [How-To](src/how-to/) | Practical guides for common tasks |
| [Reference](src/reference/) | Specifications and API documentation |

## Local Development

### Setup

```bash
# Clone the repository
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r pip_requirements.txt
```

### Preview

```bash
mkdocs serve
```

Navigate to http://127.0.0.1:8000/

### With Docker

```bash
MODE="LIVE" docker compose up --build
```

## Contributing

Contributions are welcome! See our [contribution guidelines](src/about/contributing.md).

### Quick Fixes

1. Fork the repository
2. Edit the relevant markdown file in `src/`
3. Submit a pull request

### Larger Changes

1. Open an issue to discuss the change
2. Fork and create a feature branch
3. Make changes with `mkdocs serve` for preview
4. Submit a pull request

## Related Repositories

- [datajoint-python](https://github.com/datajoint/datajoint-python) — Core DataJoint library
- [datajoint-elements](https://github.com/datajoint) — Neuroscience pipeline elements

## Citation

If you use DataJoint in your research, please cite:

> Yatsenko D, Reimer J, Ecker AS, Walker EY, Sinz F, Berens P, Hoenselaar A,
> Cotton RJ, Siapas AS, Tolias AS. DataJoint: managing big scientific data
> using MATLAB or Python. bioRxiv. 2015:031658. doi: [10.1101/031658](https://doi.org/10.1101/031658)

## License

Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

DataJoint software: [Apache 2.0](https://github.com/datajoint/datajoint-python/blob/main/LICENSE)
