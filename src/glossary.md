# Glossary

There are many terms that are reused throughout the documentation that we feel important to define together. We've taken careful consideration to be consistent. Below you will find how we've understood and use these terms.

| Term | Definition |
| --- | --- |
| <span id="data-pipeline">data pipeline</span> | formal definition of a directed acyclic graph (DAG)) of processes that achieves the [DataJoint Mantra](../concepts/mantra) |
| workflow | a formal representation of the steps for executing an experiment from data collection to analysis. Also the software configured for performing these steps. A typical workflow is composed of tables with inter-dependencies and processes to compute and insert data into the tables. |
| DataJoint | a software framework for database programming directly from matlab and python. Thanks to its support of automated computational dependencies, DataJoint serves as a workflow management system. |
| DataJoint pipeline | the data schemas and transformations underlying a DataJoint workflow. DataJoint allows defining code that specifies both the workflow and the data pipeline, and we have used the words "pipeline" and "workflow" almost interchangeably. |
| DataJoint schema | a software module implementing a portion of an experiment workflow. Includes database table definitions, dependencies, and associated computations. |
| DataJoint Elements | software modules implementing portions of experiment workflows designed for ease of integration into diverse custom workflows. |
| djHub | our team's internal platform for delivering cloud-based infrastructure to support online training resources, validation studies, and collaborative projects. |