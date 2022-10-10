# Developer instructions

## Development mode installation

- This method allows you to modify the source code for example DataJoint
  workflows (e.g. `workflow-array-ephys`, `workflow-calcium-imaging`) and their
  dependencies (i.e., DataJoint Elements).

- Launch a new terminal and change directory to where you want to clone the
  repositories
  `bash cd ~/Projects `

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

- If required to drop all schemas, the following is the dependency order.
  Also refer to `notebooks/06-drop-optional.ipynb` within the respective
  `workflow`.

- `workflow-array-ephys`
    <details>
    <summary>Click to expand details</summary>
    
    ```
    from workflow_array_ephys.pipeline import *

    ephys.schema.drop()
    probe.schema.drop()
    session.schema.drop()
    subject.schema.drop()
    lab.schema.drop()
    ```

    </details>


- `workflow-calcium-imaging`
    <details>
    <summary>Click to expand details</summary>
    
    ```
    from workflow_calcium_imaging.pipeline import *

    imaging.schema.drop()
    scan.schema.drop()
    session.schema.drop()
    subject.schema.drop()
    lab.schema.drop()
    ```

    </details>

- `workflow-miniscope`
    <details>
    <summary>Click to expand details</summary>
    
    ```
    from workflow_miniscope.pipeline import *

    miniscope.schema.drop()
    session.schema.drop()
    subject.schema.drop()
    lab.schema.drop()
    ```

    </details>

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
TODO: Configuration and syncing

## Release process
TODO: git tag and git push upstream