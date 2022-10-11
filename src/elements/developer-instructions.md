# Developer instructions

## Development mode installation

- We recommend doing development work in a conda environment. For information on setting up conda for the first time, see [this article](https://towardsdatascience.com/get-your-computer-ready-for-machine-learning-how-what-and-why-you-should-use-anaconda-miniconda-d213444f36d6).

- This method allows you to modify the source code for example DataJoint
  workflows (e.g. `workflow-array-ephys`) and their
  dependencies (e.g., `element-array-ephys`).

- Launch a new terminal and change directory to where you want to clone the
  repositories (e.g., `bash cd ~/Projects`)

- `workflow-array-ephys`
    <details>
    <summary>Click to expand details</summary>

  - Clone the repositories

    ```bash
    git clone https://github.com/datajoint/element-lab
    git clone https://github.com/datajoint/element-animal
    git clone https://github.com/datajoint/element-session
    git clone https://github.com/datajoint/element-interface
    git clone https://github.com/datajoint/element-array-ephys
    git clone https://github.com/datajoint/workflow-array-ephys
    ```

  - Install each package with the `-e` option

    ```bash
    pip install -e ./element-lab
    pip install -e ./element-animal
    pip install -e ./element-session
    pip install -e ./element-interface
    pip install -e ./element-array-ephys
    pip install -e ./workflow-array-ephys
    ```

    </details>

- `workflow-calcium-imaging`
    <details>
    <summary>Click to expand details</summary>

  - Clone the repositories

    ```bash
    git clone https://github.com/datajoint/element-lab
    git clone https://github.com/datajoint/element-animal
    git clone https://github.com/datajoint/element-session
    git clone https://github.com/datajoint/element-interface
    git clone https://github.com/datajoint/element-calcium-imaging
    git clone https://github.com/datajoint/workflow-calcium-imaging
    ```

  - Install each package with the `-e` option

    ```bash
    pip install -e ./element-lab
    pip install -e ./element-animal
    pip install -e ./element-session
    pip install -e ./element-interface
    pip install -e ./element-calcium-imaging
    pip install -e ./workflow-calcium-imaging
    ```

    </details>

## Optionally drop all schemas

If you need to drop all schemas to start fresh, you'll need to do following the dependency order. Refer to the workflow's notebook (`notebooks/06-drop-optional.ipynb`) for the drop order.

## Run integration tests

- Download the test dataset to your local machine. Note the directory where the
  dataset is saved (e.g. `/tmp/testset`).

- Create an `.env` file within the `docker` directory with the following content. 
  Replace `/tmp/testset` with the directory where you have the test dataset downloaded.
  `TEST_DATA_DIR=/tmp/testset`

- If testing an unreleased version of the `element` or your fork of an `element`
  or the `workflow`, within the `Dockerfile` uncomment the lines from the
  different options presented. This will allow you to install the repositories
  of interest and run the integration tests on those packages. Be sure that the
  `element` package version matches the version in the `requirements.txt` of the
  `workflow`.

- Run the Docker container.
  ```
  docker-compose -f ./docker/docker-compose-test.yaml up --build
  ```

## Jupytext
We maintain `.py` script copies of all didactic notebooks to facilitate the GitHub review process. From the main workflow directory, we recommend the following command to generate these copies. You may wish to save this as an alias in your `.bash_profile`. Note that the jupytext sync features may cause issues with the original notebooks.

    ```bash
    pip install jupytext
    jupytext --to py notebooks/0*ipynb; mv notebooks/*py notebooks/py_scripts
    ```
