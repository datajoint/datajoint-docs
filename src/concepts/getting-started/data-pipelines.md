# Data Pipelines

DataJoint is a free open-source framework for creating scientific data pipelines
directly from Python or MATLAB (or both). The data are stored in a language-independent
way, accessible via both Python and MATLAB. In DataJoint, a data pipeline is a sequence
of steps (see also [DAGs](./diagrams))) with integrated data storage at each step, as defined
by the [tables](../reproduce/tabletiers). 

Formally, a scientific **data pipeline** is a collection of processes and systems
for organizing the data, computations, and workflows used by a research
group as they jointly perform complex sequences of data acquisition,
processing, and analysis. A full-featured data pipeline framework may also be described
as a 
[scientific workflow system](https://en.wikipedia.org/wiki/Scientific_workflow_system).

In practice, a data pipeline is some definition of how should flow from its origin 
through publication-ready analysis. In its most basic form, this could be a set of 
spreadsheets and a checklist of each processing step that should be applied to each.

DataJoint APIs give researches a set of tools for defining and automating all the steps
of data management and processing for an experiment across the whole team, and play a 
key role in a broader pipeline.

```mermaid
flowchart LR
  subgraph repo["<b>Data Repository</b>
                #8226;Deposit & Retrieve
                #8226;Access Control"]
    direction TB
  end
  subgraph empty1[" "] %% Empty subgraphs prevent overlapping titles
    direction LR
    style empty1 fill:none, stroke-dasharray: 0 1
    emptyone[" "]
    repo
  end
  subgraph db["<center><b>Database</b></center>#8226;Structure <i>(schema)
              #8226;Data Integrity 
              <i>(identity, references, groups)</i>
              #8226;Queries"]
    direction LR
    empty1
  end
  subgraph pipe["<center><b>Data Pipeline</b></center>#8226;Workflow
                #8226;Computation"]
    class pipe vertical-align:bottom;
    direction LR
    emptytwo[" "]
    db
  end
  class emptyone,emptytwo void;
  classDef void fill:none, stroke-dasharray: 0 1
  class repo,db,pipe boxes;
  classDef boxes fill:#ddd, stroke:#333;
```

### Data repositories

A shared **data repository** gives all team members access to the data.
This might include a collection of files with standard naming conventions,
organized into folders and sub-folders. Or, a data repository might be a collection of 
S3 buckets hosted on a cloud server.

### Database systems

**Databases** are a form of data repository, with additional capabilities:

1. Define, communicate, and enforce structure in the stored data. 

2. Maintain data integrity: correct identification of data and consistent
cross-references, dependencies, and groupings among the data. 

3. Support queries that retrieve various cross-sections and transformation of the
 deposited data.

Most scientists have some familiarity with these concepts, for example the notion of
maintaining consistency between data and the metadata that describes it, or applying a
filter to an Excel spreadsheet to retrieve specific subsets of information. However,
usually the more advanced concepts involved in building and using
[relational databases](../ref-integrity/relational-databases) fall under the specific
expertise of data scientists.

### Data pipelines

**Data pipeline** frameworks may include all the features of a database
system along with additional functionality:

 1. Integrating computations to perform analyses and manage intermediate results in a 
 principled way.
 
 2. Supporting distributed computations without conflict.
 
 3. Defining, communicating, and enforcing **workflow**, making clear the sequence of
 steps that must be performed for data entry, acquisition, and processing.

The informal notion of an analysis "workflow" will be familiar to most scientists. This
could include the the logistical difficulties associated making sure each file is 
preprocessed, while distributing the load across multiple team members or compute 
resources.

