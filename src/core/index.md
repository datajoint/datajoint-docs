# Core

DataJoint Core is a collection of open-source tools for building and operating scientific data pipelines.

## APIs

<div class="grid cards" markdown>

-   :fontawesome-brands-python:{ .lg .middle } **DataJoint for Python**

    ---

    A Python client for defining, operating, and querying data pipelines.

    :octicons-arrow-right-24: [Documentation](https://datajoint.com/docs/core/datajoint-python/) | [Source code](https://github.com/datajoint/datajoint-python)

-   :fontawesome-brands-java:{ .lg .middle } **DataJoint for MATLAB**

    ---

    A MATLAB client for defining, operating, and querying data pipelines.

    :octicons-arrow-right-24: [Documentation](https://datajoint.com/docs/core/datajoint-matlab) | [Source code](https://github.com/datajoint/datajoint-matlab)

-   :fontawesome-solid-flask:{ .lg .middle } **Pharus**

    ---

    A REST API server for interacting with DataJoint pipelines.

    :octicons-arrow-right-24: [Documentation](https://datajoint.github.io/pharus/) | [Source code](https://github.com/datajoint/pharus/)
 
</div>

## Web Applications

<div class="grid cards" markdown>


-   :fontawesome-brands-chrome:{ .lg .middle } **LabBook**

    ---

	A browser-based graphical user interface for data entry and navigation. 

    :octicons-arrow-right-24: [Documentation](https://datajoint.github.io/datajoint-labbook/) | [Source code](https://github.com/datajoint/datajoint-labbook/)

-   :fontawesome-brands-chrome:{ .lg .middle } **SciViz**

    ---

    A framework for making low-code web apps for data visualization.

    :octicons-arrow-right-24: [Source code](https://github.com/datajoint/sci-viz)

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

-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/mysql**](https://hub.docker.com/r/datajoint/mysql)

    ---
    MySQL server pre-configured to work smoothly with DataJoint. 

-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/miniconda3**](https://hub.docker.com/r/datajoint/miniconda3)

    ---

    A minimal Python image with [conda](https://docs.conda.io/en/latest/).

-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/djbase**](https://hub.docker.com/r/datajoint/djbase)

    ---

    A minimal base docker image with DataJoint Python dependencies installed. 

-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/djtest**](https://hub.docker.com/r/datajoint/djtest)

    ---

    A docker image for running tests related to DataJoint Python. 

-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/datajoint**](https://hub.docker.com/r/datajoint/datajoint)

    ---

    Official DataJoint Docker image.

-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/djlab**](https://hub.docker.com/r/datajoint/djlab)

    ---

	A docker image optimized for running a JupyterLab environment with DataJoint Python. 


-   :fontawesome-brands-docker:{ .lg .middle } [**datajoint/djlabhub**](https://hub.docker.com/r/datajoint/djlabhub)

    ---

	A docker image optimized for deploying to JupyterHub a JupyterLab environment with DataJoint Python. 


</div>
