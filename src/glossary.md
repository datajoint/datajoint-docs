# Glossary

There are many terms that are reused throughout the documentation that we feel important
to define together. We've taken careful consideration to be consistent. Below you will
find how we've understood and use these terms.

<!-- Contributors: Please keep this table in alphabetical order -->

| Term | Definition |
| --- | --- |
| <span id="DAG">DAG</span> | directed acyclic graph (DAG) is a set of nodes and unidirectional edges with no cyclic dependencies. No child node points to a parent node. |
| <span id="data-pipeline">data pipeline</span> | formal definition of a directed acyclic graph (DAG) of processes that achieves the [DataJoint Mantra](../concepts/mantra) |
| <span id="datajoint">DataJoint</span> | a software framework for database programming directly from matlab and python. Thanks to its support of automated computational dependencies, DataJoint serves as a workflow management system. |
| <span id="datajoint-elements">DataJoint Elements</span> | software modules implementing portions of experiment workflows designed for ease of integration into diverse custom workflows. |
| <span id="datajoint-pipeline">DataJoint pipeline</span> | the data schemas and transformations underlying a DataJoint workflow. DataJoint allows defining code that specifies both the workflow and the data pipeline, and we have used the words "pipeline" and "workflow" almost interchangeably. |
| <span id="datajoint-schema">DataJoint schema</span> | a software module implementing a portion of an experiment workflow. Includes database table definitions, dependencies, and associated computations. |
| <span id="djhub">djHub</span> | our team's internal platform for delivering cloud-based infrastructure to support online training resources, validation studies, and collaborative projects. |
| <span id="foreign-key">foreign key</span> | a field that is linked to another table's primary key. |
| <span id="primary-key">primary key</span> | the subset of table attributes that uniquely identify each entity in the table. |
| <span id="seconday-attribute">seconday attribute</span> | any field in a table not in the primary key. |
| <span id="workflow">workflow</span> | a formal representation of the steps for executing an experiment from data collection to analysis. Also the software configured for performing these steps. A typical workflow is composed of tables with inter-dependencies and processes to compute and insert data into the tables. |
