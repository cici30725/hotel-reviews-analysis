# Dockerfile

FROM python:3.8-slim-buster

WORKDIR /app
COPY . .
RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r requirements.txt

# install nginx
#RUN apk update && apk add --update --no-cache gcc libxslt-dev musl-dev libffi-dev libressl-dev
#COPY nginx.default /etc/nginx/sites-available/default
#RUN ln -sf /dev/stdout /var/log/nginx/access.log \
#    && ln -sf /dev/stderr /var/log/nginx/error.log
