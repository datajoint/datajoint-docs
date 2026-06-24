# DataJoint Documentation

Official documentation for [DataJoint](https://github.com/datajoint/datajoint-python) 2.0+ — an open-source framework for building scientific data pipelines.

**📖 Live site:** https://docs.datajoint.com

> **Upgrading from pre-2.0?** See the [Migration Guide](https://docs.datajoint.com/how-to/migrate-to-v20/)

## About DataJoint

DataJoint is a Python framework for scientific data pipelines built on the **Relational Workflow Model**. For installation, tutorials, and complete documentation, visit **[docs.datajoint.com](https://docs.datajoint.com)**.

## Documentation Structure

This repository contains the source for the DataJoint documentation, organized using the [Diátaxis](https://diataxis.fr/) framework:

- **[Tutorials](https://docs.datajoint.com/tutorials/)** — Learn by building real pipelines
- **[How-To Guides](https://docs.datajoint.com/how-to/)** — Practical task-oriented guides
- **[Explanation](https://docs.datajoint.com/explanation/)** — Understanding concepts and design
- **[Reference](https://docs.datajoint.com/reference/)** — Specifications and API documentation

## Local Development

### Docker (Recommended)

```bash
# Clone repositories
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs
cd ..
git clone https://github.com/datajoint/datajoint-python.git
cd datajoint-docs

# Start live preview at http://localhost:8000
MODE="LIVE" docker compose up --build

# Build static site (optional)
# MODE="BUILD" docker compose up --build
```

The Docker environment includes MySQL, MinIO, and all dependencies.

### Native Python

**Prerequisites:** Python 3.10+, MySQL 8.0+

```bash
# Setup
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r pip_requirements.txt

# Configure credentials
mkdir -p .secrets
echo "your_username" > .secrets/database.user
echo "your_password" > .secrets/database.password
chmod 600 .secrets/*

# Start live preview at http://localhost:8000
mkdocs serve
```

## Contributing

Contributions welcome! See [contribution guidelines](https://docs.datajoint.com/about/contributing/).

**Quick fixes:** Fork, edit markdown in `src/`, submit PR.

**Tutorial notebooks:** Re-execute after changes:
```bash
docker compose exec docs jupyter nbconvert --to notebook --execute --inplace \
    /main/src/tutorials/YOUR_NOTEBOOK.ipynb
```

### Notebook execution policy

Tutorial and how-to notebooks under `src/tutorials/` and `src/how-to/` are
committed **with their executed cell outputs**. The static site renders these
outputs verbatim via `mkdocs-jupyter` — the build container does not execute
notebooks, so the rendered page always matches what was committed.

Refresh outputs whenever the DataJoint version pinned in `mkdocs.yaml`
(`extra.datajoint_version`) changes, or whenever a tutorial's code changes:

```bash
# Re-execute against the bind-mounted local datajoint-python checkout
DJ_PYTHON_PATH=../datajoint-python MODE=EXECUTE    docker compose up --build
DJ_PYTHON_PATH=../datajoint-python MODE=EXECUTE_PG docker compose up --build
```

A guard script flags notebooks whose committed `DataJoint X.Y.Z connected`
banner doesn't match `extra.datajoint_version`:

```bash
python scripts/check_notebook_versions.py
```

## Related

- [datajoint-python](https://github.com/datajoint/datajoint-python) — Core library
- [DataJoint Elements](https://docs.datajoint.com/elements/) — Neuroscience pipeline modules
- [datajoint.com](https://datajoint.com) — Commercial support

## Citation

> Yatsenko D, Walker EY, Tolias AS. DataJoint: A Simpler Relational Data Model. arXiv:2303.00102. 2023. doi: [10.48550/arXiv.2303.00102](https://doi.org/10.48550/arXiv.2303.00102)

Full citation information: [docs.datajoint.com/about/citation/](https://docs.datajoint.com/about/citation/)

## License

- Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- DataJoint software: [Apache 2.0](https://github.com/datajoint/datajoint-python/blob/master/LICENSE) (LGPLv2.1 prior to v2.0)
