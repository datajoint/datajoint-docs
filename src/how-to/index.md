# How-To Guides

Practical guides for common tasks.

These guides help you accomplish specific tasks with DataJoint. Unlike tutorials,
they assume you understand the basics and focus on getting things done.

## Setup

- [Installation](installation.md) — Installing DataJoint
- [Configure Database Connection](configure-database.md) — Connection settings
- [Configure Object Storage](configure-storage.md) — S3, MinIO, file stores

## Schema Design

- [Define Tables](define-tables.md) — Table definition syntax
- [Model Relationships](model-relationships.md) — Foreign key patterns
- [Design Primary Keys](design-primary-keys.md) — Key selection strategies

## Project Management

- [Manage a Pipeline Project](manage-pipeline-project.md) — Multi-schema pipelines, team collaboration

## Data Operations

- [Insert Data](insert-data.md) — Single rows, batches, transactions
- [Query Data](query-data.md) — Operators, restrictions, projections
- [Fetch Results](fetch-results.md) — DataFrames, dicts, streaming
- [Delete Data](delete-data.md) — Safe deletion with cascades

## Computation

- [Run Computations](run-computations.md) — populate() basics
- [Distributed Computing](distributed-computing.md) — Multi-process, cluster
- [Handle Errors](handle-errors.md) — Error recovery and job management
- [Monitor Progress](monitor-progress.md) — Dashboards and status

## Object Storage

- [Use Object Storage](use-object-storage.md) — When and how
- [Create Custom Codecs](create-custom-codec.md) — Domain-specific types
- [Manage Large Data](manage-large-data.md) — Blobs, objects, garbage collection

## Maintenance

- [Migrate from 1.x](migrate-from-1x.md) — Upgrading existing pipelines
- [Alter Tables](alter-tables.md) — Schema evolution
- [Backup and Restore](backup-restore.md) — Data protection
