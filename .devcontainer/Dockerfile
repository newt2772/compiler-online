FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc g++ \
       openjdk-17-jdk \
       nodejs npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /workspace
