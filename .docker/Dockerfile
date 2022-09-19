FROM datajoint/miniconda3:4.10.3-py3.9-alpine
WORKDIR /main
COPY --chown=anaconda:anaconda ./.docker/pip_requirements.txt ${PIP_REQUIREMENTS}
RUN /entrypoint.sh echo "Dependencies installed"
COPY --chown=anaconda:anaconda ./mkdocs.yaml /main/mkdocs.yaml
COPY --chown=anaconda:anaconda ./src /main/src
