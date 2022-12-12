# DataJoint Documentation

This is the home for DataJoint software documentation as hosted at https://datajoint.com/docs

## Test Locally

To run locally, ensure you have `Docker` and `Docker Compose` installed.

Then run the following:

`MODE="LIVE" HOST_UID=$(id -u) docker compose up --build`

Navigate to `http://localhost/` to preview the changes.

This setup supports live-reloading so all that is needed is to save the markdown files
and/or `mkdocs.yaml` file to trigger a reload.

## Linters and Settings

The following extensions were used in developing these docs, with the corresponding
settings files:

- [MarkdownLinter](https://github.com/DavidAnson/markdownlint):
  - `.markdownlint.yaml` establishes settings for various
  [linter rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
  - `.vscode/settings.json` formatting on save to fix linting

- [CSpell](https://github.com/streetsidesoftware/vscode-spell-checker): `cspell.json`
has various ignored words.

- [ReWrap](https://github.com/stkb/Rewrap/): `.vscode/settings.json` allows toggling
automated hard wrapping for files at 88 characters. This can also be keymapped to be
performed on individual paragraphs, see documentation.
