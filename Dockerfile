FROM python:3.12-alpine

WORKDIR /main
COPY mkdocs.yaml mkdocs.yaml
COPY src/ src/
COPY pip_requirements.txt pip_requirements.txt

RUN \
    apk add --no-cache git gcc g++ musl-dev linux-headers freetype-dev libpng-dev graphviz && \
    pip install --no-cache-dir -r /main/pip_requirements.txt