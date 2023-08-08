# Additional Resources

A collection of additional open-source tools for building and operating scientific data pipelines.

## APIs

<div class="grid cards" markdown>

-   :fontawesome-brands-java:{ .lg .middle } **DataJoint MATLAB**

    ---

    A MATLAB client for defining, operating, and querying data pipelines.

    :octicons-arrow-right-24: [Legacy docs](https://docs.datajoint.org/matlab/) | 
    [Source code](https://github.com/datajoint/datajoint-matlab)

-   :fontawesome-solid-flask:{ .lg .middle } **DataJoint Pharus**

    ---

    A REST API server for interacting with DataJoint pipelines.

    :octicons-arrow-right-24: [Docs](https://datajoint.com/docs/core/pharus) | 
    [Source code](https://github.com/datajoint/pharus/)
 
</div>

## Web Applications

<div class="grid cards" markdown>

-   :fontawesome-brands-chrome:{ .lg .middle } **DataJoint LabBook**

    ---

    A browser-based graphical user interface for data entry and navigation. 

    :octicons-arrow-right-24: [Legacy 
    docs](https://datajoint.com/docs/core/datajoint-labbook/) | 
    [Source code](https://github.com/datajoint/datajoint-labbook/)

-   :fontawesome-brands-chrome:{ .lg .middle } **DataJoint SciViz**

    ---

    A framework for making low-code web apps for data visualization.

    :octicons-arrow-right-24: [Legacy docs](https://datajoint.com/docs/core/sci-viz/) | 
    [Source code](https://github.com/datajoint/sci-viz)

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
    MySQL server configured to work with DataJoint.

    :octicons-arrow-right-24: [Docker 
    image](https://hub.docker.com/r/datajoint/mysql) | 
    [Source code](https://github.com/datajoint/mysql-docker)

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/miniconda3**

    ---

    Minimal Python Docker image with [conda](https://docs.conda.io/en/latest/).

    :octicons-arrow-right-24: [Docker
    image](https://hub.docker.com/r/datajoint/miniconda3) | 
    [Legacy docs](https://datajoint.github.io/miniconda3-docker/) | 
    [Source code](https://github.com/datajoint/miniconda3-docker)

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djbase**

    ---

    Minimal base Docker image with DataJoint Python dependencies installed. 

    :octicons-arrow-right-24: [Docker 
    image](https://hub.docker.com/r/datajoint/djbase) | 
    [Legacy docs](https://datajoint.github.io/djbase-docker/) | 
    [Source code](https://github.com/datajoint/djbase-docker)

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djtest**

    ---

    Docker image for running tests related to DataJoint Python. 

    :octicons-arrow-right-24: [Docker 
    image](https://hub.docker.com/r/datajoint/djtest) | 
    [Legacy docs](https://datajoint.github.io/djtest-docker/) | 
    [Source code](https://github.com/datajoint/djtest-docker)

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/datajoint**

    ---

    Official DataJoint Docker image.

    :octicons-arrow-right-24: [Docker
    image](https://hub.docker.com/r/datajoint/datajoint) | 
    [Source code](https://github.com/datajoint/datajoint-python)

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djlab**

    ---

    Docker image optimized for running a JupyterLab environment with DataJoint Python. 

    :octicons-arrow-right-24: [Docker 
    image](https://hub.docker.com/r/datajoint/djlab) | 
    [Legacy docs](https://datajoint.github.io/djlab-docker/) | 
    [Source code](https://github.com/datajoint/djlab-docker)

-   :fontawesome-brands-docker:{ .lg .middle } **datajoint/djlabhub**

    ---

    Docker image optimized for deploying to JupyterHub a JupyterLab environment with 
    DataJoint Python. 

    :octicons-arrow-right-24: [Docker 
    image](https://hub.docker.com/r/datajoint/djlabhub) | 
    [Legacy docs](https://datajoint.github.io/djlabhub-docker/) | 
    [Source code](https://github.com/datajoint/djlabhub-docker)

</div>
