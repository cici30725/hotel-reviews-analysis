FROM tensorflow/tensorflow:1.15.0-gpu-py3

WORKDIR /app
COPY . .
RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r requirements.txt
