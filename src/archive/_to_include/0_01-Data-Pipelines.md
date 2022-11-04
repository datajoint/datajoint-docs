DataJoint pipelines become the central tool in the operations of data-intensive labs or
consortia as they organize participants with different roles and skills around a common
framework. 

## How DataJoint works

DataJoint enables data scientists to build and operate scientific data
pipelines by providing a 

DataJoint provides a simple and powerful data model, which is detailed
more formally in [Yatsenko D, Walker EY, Tolias AS (2018). DataJoint: A
Simpler Relational Data Model.](https://arxiv.org/abs/1807.11104). Put
most generally, a "data model" defines how to think about data and the
operations that can be performed on them. DataJoint's model is a
refinement of the relational data model: all nodes in the pipeline are
simple tables storing data, tables are related by their shared
attributes, and query operations can combine the contents of multiple
tables. DataJoint enforces specific constraints on the relationships
between tables that help maintain data integrity and enable flexible
access. DataJoint uses a succinct data definition language, a powerful
data query language, and expressive visualizations of the pipeline. A
well-defined and principled approach to data organization and
computation enables teams of scientists to work together efficiently.
The data become immediately available to all participants with
appropriate access privileges. Some of the "participants" may be
computational agents that perform processing and analysis, and so
DataJoint features a built-in distributed job management process to
allow distributing analysis between any number of computers.

From a practical point of view, the back-end data architecture may vary
depending on project requirements. Typically, the data architecture
includes a relational database server (e.g. MySQL) and a bulk data
storage system (e.g. [AWS S3](https://aws.amazon.com/s3/) or a
filesystem). However, users need not interact with the database
directly, but via MATLAB or Python objects that are each associated with
an individual table in the database. One of the main advantages of this
approach is that DataJoint clearly separates the data model facing the
user from the data architecture implementing data management and
computing. DataJoint works well in combination with good code sharing
(e.g. with [git](https://git-scm.com/)) and environment sharing (e.g.
with [Docker](https://www.docker.com/))

DataJoint is designed for quick prototyping and continuous exploration
as experimental designs change or evolve. New analysis methods can be
added or removed at any time, and the structure of the workflow itself
can change over time, for example as new data acquisition methods are
developed.

With DataJoint, data sharing and publishing is no longer a separate step
at the end of the project. Instead data sharing is an inherent feature
of the process: to share data with other collaborators or to publish the
data to the world, one only needs to set the access privileges.

# Summary of DataJoint features

1. A free, open-source framework for scientific data pipelines and workflow management
2. Data hosting in cloud or in-house
3. MySQL, filesystems, S3, and Globus for data management
4. Define, visualize, and query data pipelines from MATLAB or Python
5. Enter and view data through GUIs
6. Concurrent access by multiple users and computational agents
7. Data integrity: identification, dependencies, groupings
8. Automated distributed computation

# Real-life example

The [Mesoscale Activity
Project](https://www.simonsfoundation.org/funded-project/%20multi-regional-neuronal-dynamics-of-memory-guided-flexible-behavior/)
(MAP) is a collaborative project between four neuroscience labs. MAP
uses DataJoint for data acquisition, processing, analysis, interfaces,
and external sharing.

<figure>
<img src="../_static/img/map-dataflow.png" class="align-center"
alt="The DataJoint pipeline for the MAP project." />
<figcaption aria-hidden="true">The DataJoint pipeline for the MAP
project.</figcaption>
</figure>

The pipeline is hosted in the cloud through [Amazon Web
Services](https://aws.amazon.com/) (AWS). MAP data scientists at the
Janelia Research Campus and Baylor College of Medicine defined the data
pipeline. Experimental scientists enter manual data directly into the
pipeline using the [Helium web
interface](https://github.com/mattbdean/Helium). The raw data are
preprocessed using the DataJoint client libraries in MATLAB and Python;
the preprocessed data are ingested into the pipeline while the bulky and
raw data are shared using [Globus](https://globus.org) transfer through
the [PETREL](https://www.alcf.anl.gov/petrel) storage servers provided
by the Argonne National Lab. Data are made immediately available for
exploration and analysis to collaborating labs, and the analysis results
are also immediately shared. Analysis data may be visualized through web
interfaces. Intermediate results may be exported into the
[NWB](https://nwb.org) format for sharing with external groups.
