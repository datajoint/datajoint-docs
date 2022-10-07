FROM datajoint/miniconda3:4.10.3-py3.9-alpine
ARG GITHUB_TOKEN
WORKDIR /main
COPY --chown=anaconda:anaconda ./.docker/pip_requirements.txt ${PIP_REQUIREMENTS}
COPY --chown=anaconda:anaconda ./.docker/apk_requirements.txt ${APK_REQUIREMENTS}
RUN \
    /entrypoint.sh echo "Dependencies installed" && \
    rm ${PIP_REQUIREMENTS} && \
    rm ${APK_REQUIREMENTS}
RUN \
    pip install --no-cache git+https://${GITHUB_TOKEN}@github.com/guzman-raphael/mkdocs-material-insiders.git@master || \
    echo "using public mkdocs-material..."
COPY --chown=anaconda:anaconda ./mkdocs.yaml /main/mkdocs.yaml
COPY --chown=anaconda:anaconda ./src /main/src
