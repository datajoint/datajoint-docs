# DataJoint Platform

The **DataJoint Platform** extends the open-source DataJoint library with managed infrastructure and tools for team-based data operations.

## Architecture

The platform builds on the open-source core—relational database, code repository, and object storage—with functional extensions organized into four categories:

### Interactions

Tools for different users and tasks:

- **Pipeline Navigator** — Visual exploration of schema diagrams, table contents, and data dependencies
- **Electronic Lab Notebook** — Integration with laboratory documentation for manual data entry and experimental notes
- **Development Environment** — Support for Jupyter notebooks, VS Code, and other scientific programming tools
- **Visualization Dashboard** — Interactive exploration of results and pipeline status

### Infrastructure

Managed computing resources:

- **Security** — Access control integrated with institutional identity management
- **Deployment** — Cloud platforms (AWS, GCP, Azure) and hybrid configurations
- **Compute Resources** — Integration with HPC clusters, GPU resources, and cloud compute

### Automation

Intelligent workflow execution:

- **Automated Population** — The `populate()` mechanism identifies and executes missing computations
- **Job Orchestration** — Integration with workflow schedulers (Airflow, SLURM, Kubernetes)
- **AI Pipeline Agent** — Emerging capabilities for AI-assisted pipeline development and operation

### Orchestration

Coordination across the data lifecycle:

- **Data Ingest** — Tools for importing data from instruments and external systems
- **Collaboration** — Shared database access with coordinated permissions
- **Export & Integration** — Capabilities for delivering results to downstream systems

## Open-Source vs Platform

| Capability | Open-Source | Platform |
|------------|-------------|----------|
| Core library | ✅ | ✅ |
| Schema definition | ✅ | ✅ |
| Query algebra | ✅ | ✅ |
| AutoPopulate | ✅ | ✅ |
| Object storage | ✅ | ✅ Managed |
| Database hosting | Self-managed | ✅ Managed |
| User management | Self-managed | ✅ Managed |
| Visual tools | — | ✅ |
| Job orchestration | Self-managed | ✅ Managed |
| Support | Community | ✅ Enterprise |

## Learn More

- [Request a Platform account](https://www.datajoint.com/sign-up)
- [DataJoint website](https://www.datajoint.com)
