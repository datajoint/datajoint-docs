# DataJoint Documentation

This is the home for DataJoint software documentation as hosted at https://datajoint.com/docs

## VSCode Linter Extensions and Settings

The following extensions were used in developing these docs, with the corresponding
settings files:

- Recommended extensions are already specified in `.vscode/extensions.json`, it will ask you to install them when you open the project if you haven't installed them.
- settings in `.vscode/settings.json`
- [MarkdownLinter](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint):
  - `.markdownlint.yaml` establishes settings for various
  [linter rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
  - `.vscode/settings.json` formatting on save to fix linting

- [CSpell](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker): `cspell.json`
has various ignored words.

- [ReWrap](https://marketplace.visualstudio.com/items?itemName=stkb.rewrap): `.vscode/settings.json` allows toggling
automated hard wrapping for files at 88 characters. This can also be keymapped to be
performed on individual paragraphs, see documentation.

## With Virtual Environment

conda
```bash
conda create -n djdocs -y
conda activate djdocs
```
venv
```bash
python -m venv .venv
source .venv/bin/activate
```

Then install the required packages:
```bash
pip install -r pip_requirements.txt
```

Run mkdocs at http://127.0.0.1:8000/docs/:
```bash
# It will automatically reload the docs when changes are made
mkdocs serve --config-file ./mkdocs.yaml
```

## With Docker

> We mostly use Docker to simplify docs deployment

Ensure you have `Docker` and `Docker Compose` installed.

Then run the following:
```bash
# It will automatically reload the docs when changes are made
MODE="LIVE" docker compose up --build
```

Navigate to http://127.0.0.1:8000/docs/ to preview the changes.

This setup supports live-reloading so all that is needed is to save the markdown files
and/or `mkdocs.yaml` file to trigger a reload.
