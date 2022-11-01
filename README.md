# DataJoint Documentation

This is the home for all DataJoint's open-source and commercial documentation.

## Test Locally

To run locally, ensure you have `Docker` and `Docker Compose` installed.

Then run the following:

`MODE="LIVE" HOST_UID=$(id -u) docker compose up --build`

Navigate to `http://localhost/` to preview the changes.

This setup supports live-reloading so all that is needed is to save the markdown files
and/or `mkdocs.yaml` file to trigger a reload.
