# Core

DataJoint Core projects are fully open-source and are built to develop, define, manage, and visualize [data pipelines](../glossary#data-pipeline). Below are the projects that make up the family of core open-source projects.

## [API](https://en.wikipedia.org/wiki/API)'s

- **[DataJoint Python](https://datajoint.com/docs/core/datajoint-python/)**: A low-level client for managing [data pipelines](../glossary#data-pipeline).
- **[DataJoint MATLAB](https://datajoint.com/docs/core/datajoint-matlab/)**: A low-level client for managing [data pipelines](../glossary#data-pipeline).
- **[Pharus](https://datajoint.com/docs/core/pharus/)**: Expose [data pipelines](../glossary#data-pipeline) via a [REST](https://en.wikipedia.org/wiki/Representational_state_transfer) interface.

## Web [GUI](https://en.wikipedia.org/wiki/Graphical_user_interface)'s

- **[LabBook](https://datajoint.com/docs/core/datajoint-labbook/)**: Data entry and data model browsing for [data pipelines](../glossary#data-pipeline).
- **[SciViz](https://datajoint.com/docs/core/sci-viz/)**: A visualization framework for making [low-code](https://en.wikipedia.org/wiki/Low-code_development_platform) web apps for [data pipelines](../glossary#data-pipeline).

## Container Images

``` mermaid
graph
  datajoint/mysql;
  datajoint/miniconda3 --> datajoint/djbase;
  datajoint/djbase --> datajoint/djtest;
  datajoint/djbase --> datajoint/datajoint;
  datajoint/djbase --> datajoint/djlab;
  datajoint/djlab --> datajoint/djlabhub;
```

- **[datajoint/mysql](https://datajoint.com/docs/core/mysql-docker/)**: An optimized, MySQL backend for [data pipelines](../glossary#data-pipeline).
- **[datajoint/miniconda3](https://datajoint.com/docs/core/miniconda3-docker/)**: A minimal Python image with [conda](https://docs.conda.io/en/latest/).
- **[datajoint/djbase](https://datajoint.com/docs/core/djbase-docker/)**: Adds only dependencies for managing [data pipelines](../glossary#data-pipeline).
- **[datajoint/djtest](https://datajoint.com/docs/core/djtest-docker/)**: Adds testing tools like [pytest](https://docs.pytest.org/en/7.1.x/).
- **[datajoint/datajoint](https://datajoint.com/docs/core/datajoint-python/)**: Official image for managing [data pipelines](../glossary#data-pipeline).
- **[datajoint/djlab](https://datajoint.com/docs/core/djlab-docker/)**: Adds a local [Jupyter Lab](https://jupyterlab.readthedocs.io/en/stable/) environment.
- **[datajoint/djlabhub](https://datajoint.com/docs/core/djlabhub-docker/)**: Adds a client to allow hosting with [Jupyter Hub](https://jupyter.org/hub).