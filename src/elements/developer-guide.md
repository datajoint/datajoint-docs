# Developer instructions

## Development mode installation

- We recommend doing development work in a conda environment. For information on setting
  up conda for the first time, see 
  [this article](https://towardsdatascience.com/get-your-computer-ready-for-machine-learning-how-what-and-why-you-should-use-anaconda-miniconda-d213444f36d6).

- This method allows you to modify the source code for example DataJoint
  workflows (e.g. `workflow-array-ephys`) and their
  dependencies (e.g., `element-array-ephys`).

- Launch a new terminal and change directory to where you want to clone the
  repositories (e.g., `bash cd ~/Projects`)

- Clone the relevant workflow and refer to the `requirements.txt` in the workflow for
  the list of Elements to clone and install as editable. You will also need to install
  `element-interface` 

    ```console
    deps=("lab" "animal" "session" "interface" "<others>")
    for repo in $deps # clone each
    do 
        git clone https://github.com/datajoint/element-$repo
    done
    for repo in $(ls -d ./{element,workflow}*) # editable install 
    do 
        pip install -e ./$repo
    done
    ```

## Drop schemas

If you need to drop all schemas to start fresh, you'll need to do following the
dependency order. Refer to the workflow's notebook
(`notebooks/06-drop-optional.ipynb`) for the drop order.

## Pytests

- Download the test dataset to your local machine. Note the directory where the dataset
  is saved (e.g. `/tmp/testset`).

- Create an `.env` file within the `docker` directory with the following content.
  Replace `/tmp/testset` with the directory where you have the test dataset downloaded.
  `TEST_DATA_DIR=/tmp/testset`

- If testing an unreleased version of the `element` or your fork of an `element` or the
  `workflow`, within the `Dockerfile` uncomment the lines from the different options
  presented. This will allow you to install the repositories of interest and run the
  integration tests on those packages. Be sure that the `element` package version
  matches the version in the `requirements.txt` of the `workflow`.

- Run the Docker container.
  ```console
  docker-compose -f ./docker/docker-compose-test.yaml up --build
  ```
