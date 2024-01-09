# User setup instructions

The following document describes how to setup a development environment and connect to
a database so that you can use the DataJoint Elements to build and run a workflow on 
your local machine. 

Any of the DataJoint Elements can be combined together to create a workflow that matches
your experimental setup. We have a number of [example workflows](#example-workflows)
to get you started. Each focuses on a specific modality, but they can be adapted for
your custom workflow. 

1. Getting up and running will require a couple items for a good [development
  environment](#development-environment). If any of these items are already familiar to
  you and installed on your machine, you can skip the corresponding section.

    1. [Python](#python)

    2. [Conda](#conda)

    3. [Integrated Development Environment](#integrated-development-environment)

    4. [Version Control (git)](#version-control-git)

    5. [Visualization packages](#visualization-packages-jupyter-notebooks-datajoint-diagrams)

2. Next, you'll need to download one of the [example workflows](#example-workflows) and 
  corresponding [example data](#example-data). 

3. Finally, there are a couple different approaches to
  [connecting to a database](#relational-databases). Here, we highlight three approaches:

    1. [First Time](#first-time): Beginner. Temporary storage to learn the ropes.
    
    2. [Local Database](#local-database): Intermediate. Deployed on local hardware, managed 
        by you.
    
    3. [Central Database](#central-database): Advanced: Deployed on dedicated hardware.

## Development Environment

This diagram describes the general components for a local DataJoint environment. 

```mermaid
flowchart LR
  py_interp  -->|DataJoint| db_server[("Database Server\n(e.g., MySQL)")]
  subgraph conda["Conda environment"]
    direction TB
    py_interp[Python Interpreter]
  end
  subgraph empty1[" "] %% Empty subgraphs prevent overlapping titles
    direction TB
    style empty1 fill:none, stroke-dasharray: 0 1
    conda
  end
  subgraph term["Terminal or Jupyter Notebook"]
    direction TB
    empty1
  end
  subgraph empty2[" "] %% Empty subgraphs prevent overlapping titles
    direction TB
    style empty2 fill:none, stroke-dasharray: 0 1
    term
  end
  class py_interp,conda,term,ide,db_server,DataJoint boxes;
  classDef boxes fill:#ddd, stroke:#333;
```

### Python

DataJoint Elements are written in Python. The DataJoint Python API supports Python 
versions 3.7 and up. We recommend downloading the latest stable
release of 3.9 [here](https://wiki.python.org/moin/BeginnersGuide/Download), and
following the install instructions. 

### Conda

Python projects each rely on different dependencies, which may conflict across projects.
We recommend working in a Conda environment for each project to isolate the
dependencies. For more information on why Conda, and setting up the version of Conda
that best suits your needs, see 
[this article](https://towardsdatascience.com/get-your-computer-ready-for-machine-learning-how-what-and-why-you-should-use-anaconda-miniconda-d213444f36d6).

To get going quickly, we recommend you ...

1. [Download Miniconda](https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links)
and go through the setup, including adding Miniconda to your `PATH` (full
  instructions 
  [here](https://developers.google.com/earth-engine/guides/python_install-conda#add_miniconda_to_path_variable)).

2. Declare and initialize a new conda environment with the following commands. Edit
   `<name>` to reflect your project.

    ``` console
    conda create --name datajoint-workflow-<name> python=3.9 
    conda activate datajoint-workflow-<name> 
    ```

??? Warning "Apple M1 users: Click to expand"

    Running analyses with Element DeepLabCut or Element Calcium imaging may require
    tensorflow, which can cause issues on M1 machines. By saving the <code>yaml</code> 
    file below, this environment can be loaded with <code>conda create -f my-file.yaml
    </code>. If you encounter errors related to <code>clang</code>, try launching xcode 
    and retrying.

    ```yaml
    name: dj-workflow-<name>
    channels:
        - apple 
        - conda-forge
        - defaults
    dependencies:
        - tensorflow-deps
        - opencv
        - python=3.9
        - pip>=19.0 
        - pip:
            - tensorflow-macos
            - tensorflow-metal
            - datajoint
    ```

### Integrated Development Environment (IDE)

Development and use can be done with a plain text editor in the terminal. However, an
integrated development environment (IDE) can improve your experience. Several IDEs are
available. We recommend 
[Microsoft's Visual Studio Code](https://code.visualstudio.com/download), also called 
VS Code. To set up VS Code with Python for the first time, follow 
[this tutorial](https://code.visualstudio.com/docs/python/python-tutorial).

### Version Control (git)

Table definitions and analysis code can change over time, especially with multiple
collaborators working on the same project. Git is an open-source, distributed version
control system that helps keep track of what changes where made when, and by whom.
GitHub is a platform that hosts projects managed with git. The example DataJoint
Workflows are hosted on GitHub, we will use git to clone (i.e., download) this
repository.

1. Check if you already have git by typing `git --version` in a terminal window.
2. If git is not installed on your system, please
[install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). 
3. You can read more about git basics [here](https://www.atlassian.com/git).

### Visualization packages (Jupyter Notebooks, DataJoint Diagrams)

To run the demo notebooks and generate visualizations associated with an example
workflow, you'll need a couple extra packages. 

**Jupyter Notebooks** help structure code (see
[here](https://code.visualstudio.com/docs/datascience/jupyter-notebooks) for full
instructions on Jupyter within VS Code).

1. Install Jupyter packages
    ```console
    conda install jupyter ipykernel nb_conda_kernels
    ```

2. Ensure your VS Code python interpreter is set to your Conda environment path.
   
    <details> <!-- Can't use `??? Note` format within list  -->
    <summary>Click to expand more details.</summary>
    <ul>
        <li>View > Command Palette</li>
        <li>Type "Python: Select Interpreter", hit enter.</li>
        <li>If asked, select the workspace where you plan to download the workflow.</li>
        <li>If present, select your Conda environment. If not present, enter in the 
        path.</li>
    </ul>
    </details>

**DataJoint Diagrams** rely on additional packages. To install these packages,
enter the following command...
    ```console
    conda install graphviz python-graphviz pydotplus
    ```

## Example Config, Workflows and Data

Of the [options below](#example-workflows), pick the workflow that best matches your 
needs.

1. Change the directory to where you want to download the workflow.

    ```console
    cd ~/Projects
    ```

2. Clone the relevant repository, and change directories to this new directory.
    ```console
    git clone https://github.com/datajoint/<repository>
    cd <repository>
    ```

3. Install this directory as editable with the `-e` flag.
    ```console
    pip install -e .
    ```
    <details>
    <summary>Why editable? Click for details</summary>
        This lets you modify the code after installation and experiment with different
        designs or adding additional tables. You may wish to edit `pipeline.py` or 
        `paths.py` to better suit your needs. If no modification is required, 
        using `pip install .` is sufficient.
    </details>

4. Install `element-interface`, which has utilities used across different Elements and 
   Workflows.

    ```console
    pip install "element-interface @ git+https://github.com/datajoint/element-interface"
    ```

5. <a name="config">&#8203</a>Set up a local DataJoint config file by saving the 
    following block as a json in your workflow directory as `dj_local_conf.json`. Not
    sure what to put for the `< >` values below? We'll cover this when we 
    [connect to the database](#relational-databases)
  
    ```json
    {
        "database.host": "<hostname>",
        "database.user": "<username>",
        "database.password": "<password>",
        "loglevel": "INFO",
        "safemode": true,
        "display.limit": 7,
        "display.width": 14,
        "display.show_tuple_count": true,
        "custom": {
            "database.prefix": "<username_>"
        }
    }
    ```

### Example Workflows

<div class="grid cards" markdown>

-   :fontawesome-brands-python:{ .lg .middle } **Workflow Session**

    ---

    An example workflow for session management.

    [:octicons-repo-forked-24: Clone from GitHub](https://github.com/datajoint/workflow-session/)

-   :fontawesome-brands-python:{ .lg .middle } **Workflow Array Electrophysiology**

    ---

    An example workflow for Neuropixels probes.

    [:octicons-repo-forked-24: Clone from GitHub](https://github.com/datajoint/workflow-array-ephys/)

-   :fontawesome-brands-python:{ .lg .middle } **Workflow Calcium Imaging**

    ---

    An example workflow for calcium imaging microscopy.

    [:octicons-repo-forked-24: Clone from GitHub](https://github.com/datajoint/element-calcium-imaging/)

-   :fontawesome-brands-python:{ .lg .middle } **Workflow Miniscope**

    ---

    An example workflow for miniscope calcium imaging.

    [:octicons-repo-forked-24: Clone from GitHub](https://github.com/datajoint/workflow-miniscope/)

-   :fontawesome-brands-python:{ .lg .middle } **Workflow DeepLabCut**

    ---

    An example workflow for pose estimation with DeepLabCut.

    [:octicons-repo-forked-24: Clone from GitHub](https://github.com/datajoint/workflow-deeplabcut/)

</div>

### Example Data

The first notebook in each workflow will guide you through downloading example data
from DataJoint's AWS storage archive. You can also process your own data. To use the 
example data, you would ...

1. Install `djarchive-client`

    ```console
    pip install git+https://github.com/datajoint/djarchive-client.git
    ```

2. Use a python terminal to import the `djarchive` client and view available datasets, 
   and revisions.

    ```python
    import djarchive_client
    client = djarchive_client.client()
    list(client.datasets())  # List available datasets, select one
    list(client.revisions()) # List available revisions, select one
    ```

3. Prepare a directory to store the download data, for example in `/tmp`, then download
   the data with the `djarchive` client. This may take some time with larger datasets.

    ```python
    import os
    os.makedirs('/tmp/example_data/', exist_ok=True)
    client.download(
        '<workflow-dataset>',
        target_directory='/tmp/example_data',
        revision='<revision>'
    )
    ```

#### Example Data Organization

??? Note "Array Ephys: Click to expand details"

    - **Dataset**: workflow-array-ephys-benchmark
    - **Revision**: 0.1.0a4
    - **Size**: 293 GB

    The example <code>subject6/session1</code> data was recorded with SpikeGLX and
    processed with Kilosort2. 
    ```
    /tmp/example_data/
    - subject6
    - session1
        - towersTask_g0_imec0
        - towersTask_g0_t0_nidq.meta
        - towersTask_g0_t0.nidq.bin
    ```
    Element and Workflow Array Ephys also support data recorded with 
    OpenEphys.

??? Note "Calcium Imaging: Click to expand details"
    - **Dataset**: workflow-array-calcium-imaging-test-set
    - **Revision**: 0_1_0a2
    - **Size**: 142 GB
    
    The example `subject3` data was recorded with Scanbox. 
    The example `subject7` data was recorded with ScanImage.
    Both datasets were processed with Suite2p.
    ```
    /tmp/example_data/
    - subject3/
        - 210107_run00_orientation_8dir/
            - run00_orientation_8dir_000_000.sbx
            - run00_orientation_8dir_000_000.mat
            - suite2p/
                - combined
                - plane0
                - plane1
                - plane2
                - plane3
    - subject7/
        - session1
            - suite2p
                - plane0
    ```
    Element and Workflow Calcium Imaging also support data collected with ...
    - Nikon
    - Prairie View
    - CaImAn

??? Note "DeepLabCut: Click to expand details"
    - **Dataset**: workflow-dlc-data
    - **Revision**: v1
    - **Size**: .3 GB
    
    The example data includes both training data and pretrained models.
    ```
    /tmp/test_data/from_top_tracking/
    - config.yml
    - dlc-models/iteration-0/from_top_trackingFeb23-trainset95shuffle1/
        - test/pose_cfg.yaml
        - train/
            - checkpoint
            - checkpoint_orig
            ─ learning_stats.csv
            ─ log.txt
            ─ pose_cfg.yaml
            ─ snapshot-10300.data-00000-of-00001
            ─ snapshot-10300.index
            ─ snapshot-10300.meta   # same for 103000
    - labeled-data/
        - train1/
            - CollectedData_DJ.csv
            - CollectedData_DJ.h5
            - img00674.png          # and others
        - train2/                   # similar to above
    - videos/
        - test.mp4
        - train1.mp4
    ```

??? Note "FaceMap: Click to expand details"

    **Associated workflow still under development**

    - **Dataset**: workflow-facemap
    - **Revision**: 0.0.0
    - **Size**: .3 GB

#### Using Your Own Data

Some of the workflows carry some assumptions about how your file directory will be 
organized, and how some files are named.

??? Note "Array Ephys: Click to expand details"

    - In your [DataJoint config](#config), add another item under `custom`, 
        `ephys_root_data_dir`, for your local root data directory. This can include 
        multiple roots.

        ```json
        "custom": {
            "database.prefix": "<username_>",
            "ephys_root_data_dir": ["/local/root/dir1", "/local/root/dir2"]
        }
        ```

    - The `subject` directory names must match the subject IDs in your subjects table. 
        The `ingest.py` script (
        [demo ingestion notebook](https://github.com/datajoint/workflow-array-ephys/blob/main/notebooks/04-automate-optional.ipynb)
        ) can help load these values from `./user_data/subjects.csv`.

    - The `session` directories can have any naming convention, but must be specified 
        in the session table (see also
        [demo ingestion notebook](https://github.com/datajoint/workflow-array-ephys/blob/main/notebooks/04-automate-optional.ipynb)
        ). 

    - Each session can have multiple probes.
    
    - The `probe` directory names must end in a one-digit number corresponding to the 
        probe number.
    
    - Each `probe` directory should contain:
        - One neuropixels meta file named `*[0-9].ap.meta`
        - Optionally, one Kilosort output folder
        
    Folder structure:
    ```
    <ephys_root_data_dir>/
    └───<subject1>/                       # Subject name in `subjects.csv`
    │   └───<session0>/                   # Session directory in `sessions.csv`
    │   │   └───imec0/
    │   │   │   │   *imec0.ap.meta
    │   │   │   └───ksdir/
    │   │   │       │   spike_times.npy
    │   │   │       │   templates.npy
    │   │   │       │   ...
    │   │   └───imec1/
    │   │       │   *imec1.ap.meta
    │   │       └───ksdir/
    │   │           │   spike_times.npy
    │   │           │   templates.npy
    │   │           │   ...
    │   └───<session1>/
    │   │   │   ...
    └───<subject2>/
    │   │   ...
    ```

??? Note "Calcium Imaging: Click to expand details"

    **Note:** While Element Calcium Imaging can accommodate multiple scans per 
    session, Workflow Calcium Imaging assumes there is only one scan per session.

    - In your [DataJoint config](#config), add another item under `custom`, 
        `imaging_root_data_dir`, for your local root data directory. 

        ```json
        "custom": {
            "database.prefix": "<username_>",
            "imaging_root_data_dir": "/local/root/dir1"
        }
        ```
        
    - The `subject` directory names must match the subject IDs in your subjects table. 
        The `ingest.py` script (
        [tutorial notebook](https://github.com/datajoint/element-calcium-imaging/blob/main/notebooks/tutorial.ipynb)
        ) can help load these values from `./user_data/subjects.csv`.

    - The `session` directories can have any naming convention, but must be specified 
        in the session table (see also
        [tutorial notebook])(https://github.com/datajoint/element-calcium-imaging/blob/main/notebooks/tutorial.ipynb)
        . 

    - Each `session` directory should contain:
        - All `.tif` or `.sbx` files for the scan, with any naming convention.
        - One `suite2p` subfolder, containing the analysis outputs in the default naming 
            convention.
        - One `caiman` subfolder, containing the analysis output `.hdf5` file, with any
            naming convention.
        
    Folder structure:
    ```
    imaging_root_data_dir/
    └───<subject1>/                     # Subject name in `subjects.csv`
    │   └───<session0>/                 # Session directory in `sessions.csv`
    │   │   │   scan_0001.tif
    │   │   │   scan_0002.tif
    │   │   │   scan_0003.tif
    │   │   │   ...
    │   │   └───suite2p/
    │   │       │   ops1.npy
    │   │       └───plane0/
    │   │       │   │   ops.npy
    │   │       │   │   spks.npy
    │   │       │   │   stat.npy
    │   │       │   │   ...
    │   │       └───plane1/
    │   │           │   ops.npy
    │   │           │   spks.npy
    │   │           │   stat.npy
    │   │           │   ...
    │   │   └───caiman/
    │   │       │   analysis_results.hdf5
    │   └───<session1>/                 # Session directory in `sessions.csv`
    │   │   │   scan_0001.tif
    │   │   │   scan_0002.tif
    │   │   │   ...
    └───<subject2>/                     # Subject name in `subjects.csv`
    │   │   ...
    ```

??? Note "DeepLabCut: Click to expand details"

    **Note:** Element DeepLabCut assumes you've already used the DeepLabCut GUI to 
    set up your project and label your data. This can include multiple roots.

    - In your [DataJoint config](#config), add another item under 
        `custom`, `dlc_root_data_dir`, for your local root 
        data directory.
        ```json
        "custom": {
            "database.prefix": "<username_>",
            "dlc_root_data_dir": ["/local/root/dir1", "/local/root/dir2"]
        }
        ```
        
    - You have preserved the default DeepLabCut project directory, shown below.
        
    - The paths in your various `yaml` files reflect the current folder structure.

    - You have generated the `pickle` and `mat` training files. If not, follow the 
        DeepLabCut guide to 
        [create a training dataset](https://github.com/DeepLabCut/DeepLabCut/blob/master/docs/standardDeepLabCut_UserGuide.md#f-create-training-datasets)

    Folder structure:
    ```
    /dlc_root_data_dir/your_project/
    - config.yaml                   # Including correct path information
    - dlc-models/iteration-*/your_project_date-trainset*shuffle*/
        - test/pose_cfg.yaml        # Including correct path information
        - train/pose_cfg.yaml       # Including correct path information
    - labeled-data/any_names/*{csv,h5,png}
    - training-datasets/iteration-*/UnaugmentedDataSet_your_project_date/
        - your_project_*shuffle*.pickle
        - your_project_scorer*shuffle*.mat
    - videos/any_names.mp4
    ```

??? Note "Miniscope: Click to expand details"

    - In your [DataJoint config](#config), add another item under `custom`, 
        `miniscope_root_data_dir`, for your local root data directory.
        
        ```json
        "custom": {
            "database.prefix": "<username_>",
            "miniscope_root_data_dir": "/local/root/dir"
        }
        ```

## Relational databases

DataJoint helps you connect to a database server from your programming environment 
(i.e., Python or MATLAB), granting a number of benefits over traditional file hierarchies 
(see [YouTube Explainer](https://www.youtube.com/watch?v=q-PMUSC5P5o)). We offer two 
options:

1. The [First Time](#first-time) beginner approach loads example data to a temporary existing 
   database, saving you setup time. But, because this data will be purged intermittently,
   it should not be used in a true experiment.
2. The [Local Database](#local-database) intermediate approach will walk you through 
   setting up your own database on your own hardware. While easier to manage, it may be 
   difficult to expose this to outside collaborators.
3. The [Central Database](#central-database) advanced approach has the benefits of running
on dedicated hardware, but may require significant IT expertise and infrastructure
depending on your needs.

### First time

*Temporary storage. Not for production use.*

1. Make an account at [accounts.datajoint.io](https://accounts.datajoint.io/).
2. In a workflow directory, make a <a href="#config">config</a> `json` file called
   `dj_local_conf.json` using your DataJoint account information and 
   `tutorial-db.datajoint.io` as the host.
    ```json
    {
        "database.host": "tutorial-db.datajoint.io",
        "database.user": "<datajoint-username>",
        "database.password": "<datajoint-password>",
        "loglevel": "INFO",
        "safemode": true,
        "display.limit": 7,
        "display.width": 14,
        "display.show_tuple_count": true,
        "custom": {
        "database.prefix": "<datajoint-username_>"
        }
    }
    ```
    <b>Note:</b> Your database prefix must begin with your username in order to have 
    permission to declare new tables.
3. Launch a Python terminal and start interacting with the workflow.

### Local Database

1. Install [Docker](https://docs.docker.com/engine/install/).
   <details> <!-- Can't use `??? Note "Title" notation within list, must use HTML -->
   <summary>Why Docker? Click for details.</summary>

        Docker makes it easy to package a program, including the file system and related 
        code libraries, in a <i>container</i>. This container can be distributed to any 
        machine, both automating and standardizing the setup process.
   
   </details>
2. Test that docker has been installed by running the following command:
   ```console
   docker run --rm hello-world
   ```
3. Launch the DataJoint MySQL server with the following command:
   ```console
    docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=tutorial datajoint/mysql
   ```
    <details>
    <summary>What's this doing? Click for details.</summary>
    <ul>
    <li>Download a container image called datajoint/mysql, which is pre-installed and 
        configured MySQL database with appropriate settings for use with DataJoint
    </li>
    <li>Open up the port 3306 (MySQL default) on your computer so that your database 
        server can accept connections.
    </li>
    <li>Set the password for the root database user to be tutorial, which are then used 
        in the config file.
    </li>
    </ul>
    </details>  
4. In a workflow directory, make a <a href="#config">config</a> `json` file called
   `dj_local_conf.json` using the following details. The prefix can be set to any value.
    ```json
    {
        "database.host": "localhost",
        "database.password": "tutorial",
        "database.user": "root",
        "database.port": 3306,
        "loglevel": "INFO",
        "safemode": true,
        "display.limit": 7,
        "display.width": 14,
        "display.show_tuple_count": true,
        "custom": {
            "database.prefix": "neuro_"
        }
    }
    ```

??? Note "Already familiar with Docker? Click here for details."

    This document is written to apply to all example workflows. Many have a docker 
    folder used by developers to set up both a database and a local environment for 
    integration tests. Simply `docker compose up` the relevant file and 
    `docker exec` into the relevant container.

### Central Database

To set up a database on dedicated hardware may require expertise to set up and maintain.
DataJoint's [MySQL Docker image project](https://github.com/datajoint/mysql-docker) 
provides all the information required to set up a dedicated database.

## Interacting with the Workflow

### In Python

1. Connect to the database and import tables

    ```python
    from <relevant-workflow>.pipeline import *
    ```

2. View the declared tables. For a more in depth explanation of how to run the workflow
    and explore the data, refer to the 
    [Jupyter notebooks](#visualization-packages-jupyter-notebooks-datajoint-diagrams) 
    in the workflow directory.
    <details>  <!-- Can't use `??? Note "Title" notation within list, must use HTML -->
    <summary>Array Ephys: Click to expand details</summary>
        ```python
        subject.Subject()
        session.Session()
        ephys.ProbeInsertion()
        ephys.EphysRecording()
        ephys.Clustering()
        ephys.Clustering.Unit()
        ```
    </details>
    <details>
    <summary>Calcium Imaging: Click to expand details</summary>
        ```python
        subject.Subject()
        session.Session()
        scan.Scan()
        scan.ScanInfo()
        imaging.ProcessingParamSet()
        imaging.ProcessingTask()
        ```
    </details>
    <details>
    <summary>DeepLabCut: Click to expand details</summary>
        ```python
        subject.Subject()
        session.Session()
        train.TrainingTask()
        model.VideoRecording.File()
        model.Model()
        model.PoseEstimation.BodyPartPosition()
        ```
    </details>

### DataJoint LabBook

DataJoint LabBook is a graphical user interface to facilitate data entry for existing
DataJoint tables.

- [Labbook Website](https://labbook.datajoint.io/) - If a database is public (e.g., 
    `tutorial-db`) and you have access, you can view the contents here.

- [DataJoint LabBook Documentation](https://datajoint.github.io/datajoint-labbook/), 
    including prerequisites, installation, and running the application

- [DataJoint LabBook GitHub Repository](https://github.com/datajoint/datajoint-labbook)
