# Dockerfile

FROM python:3.7-slim-buster

WORKDIR /app
COPY . .
RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r requirements.txt
