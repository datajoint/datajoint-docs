# Core

DataJoint Core projects are fully open-source and are built to develop, define, manage,
and visualize [data pipelines](./getting-started/data-pipelines). Below are the projects that
make up the family of core open-source projects.

## APIs

<div class="grid cards" markdown>

-   :fontawesome-brands-python:{ .lg .middle } **DataJoint Python**

    ---

    A low-level client for managing data pipelines.

    [:octicons-arrow-right-24: Interactive tutorial on GitHub Codespaces](https://github.com/datajoint/datajoint-tutorials){:target="_blank"}

    :octicons-arrow-right-24: [New docs](./datajoint-python/) coming soon!  In the meantime, refer to our [legacy docs](https://docs.datajoint.org/python/).

-   :fontawesome-brands-java:{ .lg .middle } **DataJoint MATLAB**

    ---

    A low-level client for managing data pipelines.

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](https://docs.datajoint.org/matlab/).

-   :fontawesome-solid-flask:{ .lg .middle } **Pharus**

    ---

    Expose DataJoint pipelines via a REST interface.

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./pharus/).

</div>

## Web GUIs

<div class="grid cards" markdown>

-   :fontawesome-brands-chrome:{ .lg .middle } **LabBook**

    ---

    Data entry and data model browsing for DataJoint pipelines.

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./datajoint-labbook/).

-   :fontawesome-brands-chrome:{ .lg .middle } **SciViz**

    ---

    A visualization framework for making low-code web apps for DataJoint pipelines.

    :octicons-arrow-right-24: See [documentation](./sci-viz/).

</div>

## Container Images

``` mermaid
graph
  %% Give short names
  dj["datajoint/datajoint"]
  base["datajoint/djbase"]
  lab["datajoint/djlab"]
  hub["datajoint/djlabhub"]
  test["datajoint/djtest"]
  conda3["datajoint/miniconda3"]
  mysql["datajoint/mysql"]
  %% Define connections
  conda3 --> base --> test;
  base --> dj;
  base --> lab --> hub;
  %% Add all to class
  class dj,base,lab,hub,test,conda3,mysql boxes;
  classDef boxes stroke:#333; %% Grey stroke for class
```

<div class="grid cards" markdown>

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/mysql**

    ---

    An optimized, MySQL backend for DataJoint pipelines.

    :octicons-arrow-right-24: New docs coming soon! In the meantime, refer to our [legacy docs](https://github.com/datajoint/mysql-docker#mysql-for-datajoint).

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/miniconda3**

    ---

    A minimal Python image with [conda](https://docs.conda.io/en/latest/).

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./miniconda3-docker/).

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djbase**

    ---

    Adds only dependencies for managing DataJoint pipelines.

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./djbase-docker/).

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djtest**

    ---

    Adds testing tools like [pytest](https://docs.pytest.org/en/7.1.x/).

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./djtest-docker/).

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/datajoint**

    ---

    Official image for managing DataJoint pipelines.

    :octicons-arrow-right-24: [New docs](./datajoint-python/) coming soon!  In the meantime, refer to our [legacy docs](https://docs.datajoint.org/python/).

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djlab**

    ---

    Adds a local [Jupyter Lab](https://jupyterlab.readthedocs.io/en/stable/) environment.

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./djlab-docker/).

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djlabhub**

    ---

    Adds a client to allow hosting with [Jupyter Hub](https://jupyter.org/hub).

    :octicons-arrow-right-24: New docs coming soon!  In the meantime, refer to our [legacy docs](./djlabhub-docker/).

</div>
