# Tutorials

Learn DataJoint by building real pipelines.

These tutorials guide you through building data pipelines step by step. Each tutorial
is a Jupyter notebook that you can run interactively. Start with the basics and
progress to advanced topics.

## Getting Started

1. [Getting Started](01-getting-started.ipynb) — Your first DataJoint pipeline
2. [Schema Design](02-schema-design.ipynb) — Tables, keys, and relationships
3. [Data Entry](03-data-entry.ipynb) — Inserting and managing data
4. [Queries](04-queries.ipynb) — Operators and fetching results
5. [Computation](05-computation.ipynb) — Imported and Computed tables
6. [Object-Augmented Schemas](06-object-storage.ipynb) — Blobs, attachments, and object storage
7. [University Database](07-university.ipynb) — A complete example pipeline
8. [Fractal Pipeline](08-fractal-pipeline.ipynb) — Iterative computation patterns

## Advanced Topics

- [JSON Data Type](advanced/json-type.ipynb) — Semi-structured data in tables
- [Distributed Computing](advanced/distributed.ipynb) — Multi-process and cluster workflows
- [Custom Codecs](advanced/custom-codecs.ipynb) — Extending the type system
- [Schema Migration](advanced/migration.ipynb) — Evolving existing pipelines

## Running the Tutorials

```bash
# Clone the repository
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs

# Start the tutorial environment
docker compose up -d

# Launch Jupyter
jupyter lab src/tutorials/
```

All tutorials use a local MySQL database that resets between sessions.
