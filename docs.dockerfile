FROM python:slim

WORKDIR /main
COPY . /main
RUN pip install mkdocs mkdocs-material