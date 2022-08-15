FROM python:latest

WORKDIR /main
COPY . /main
RUN pip install mkdocs mkdocs-material