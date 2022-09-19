# Core

## Relational Database

- MySQL usage
- Optimal configuration
- Maintenance
- Permission management and access control 


## Programming Interfaces

Below are the projects that make up the family of core open-source projects:

- **[Python API](https://datajoint.com/docs/core/datajoint-python/)**: Relational framework that allows for intuitive queries and reproducible computation.
- **[MATLAB API](https://datajoint.com/docs/core/datajoint-matlab/)**: Relational framework that allows for intuitive queries and reproducible computation.
- **[Pharus](https://datajoint.com/docs/core/pharus/)**: REST interface for communicating with data pipelines.

## Web Interfaces

- **[LabBook](https://datajoint.com/docs/core/datajoint-labbook/)**: Data entry and data model browsing web GUI.
- **[SciViz](https://datajoint.com/docs/core/sci-viz/)**: Visualization framework for making low-code web apps.

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

- **[datajoint/mysql](https://datajoint.com/docs/core/mysql-docker/)**: Optimized MySQL image for use with DataJoint Engine.
- **[datajoint/miniconda3](https://datajoint.com/docs/core/miniconda3-docker/)**: Minimal Python image with `conda`.
- **[datajoint/djbase](https://datajoint.com/docs/core/djbase-docker/)**: DataJoint engine dependencies only.
- **[datajoint/djtest](https://datajoint.com/docs/core/djtest-docker/)**: Includes testing tools like `pytest`.
- **[datajoint/datajoint](https://datajoint.com/docs/core/datajoint-python/)**: Official DataJoint engine image.
- **[datajoint/djlab](https://datajoint.com/docs/core/djlab-docker/)**: Includes local Jupyter Lab environment.
- **[datajoint/djlabhub](https://datajoint.com/docs/core/djlabhub-docker/)**: Includes necessary dependencies for launching with Jupyter Hub.