# About DataJoint

DataJoint is an open-source framework for building scientific data pipelines.
It was created to address the challenges of managing complex, interconnected
data in research laboratories.

## What is DataJoint?

DataJoint implements the **Relational Workflow Model**—a paradigm that extends
relational databases with native support for computational workflows. Unlike
traditional databases that only store data, DataJoint pipelines define how data
flows through processing steps, when computations run, and how results depend
on inputs.

Key characteristics:

- **Declarative schema design** — Define tables and relationships in Python
- **Automatic dependency tracking** — Foreign keys encode workflow dependencies
- **Built-in computation** — Imported and Computed tables run automatically
- **Data integrity** — Referential integrity and transaction support
- **Reproducibility** — Immutable data with full provenance

## History

DataJoint was developed at Baylor College of Medicine starting in 2009 to
support neuroscience research. It has since been adopted by laboratories
worldwide for a variety of scientific applications.

[:octicons-arrow-right-24: Read the full history](history.md)

## Citation

If you use DataJoint in your research, please cite it appropriately.

[:octicons-arrow-right-24: Citation guidelines](citation.md)

## Contributing

DataJoint is developed openly on GitHub. Contributions are welcome.

[:octicons-arrow-right-24: Contribution guidelines](contributing.md)

## License

DataJoint is released under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

Copyright 2024 DataJoint Inc. and contributors.
