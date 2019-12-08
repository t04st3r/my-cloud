FROM python:3.6-alpine
 ENV PYTHONUNBUFFERED 1

 RUN apk update && \
     apk add --virtual build-deps gcc python-dev libmagic musl-dev libffi-dev openssl-dev python3-dev && \
     apk add postgresql-dev bash

 RUN mkdir /config
 ADD requirements.txt /config/
 RUN pip install --upgrade pip && pip install -r /config/requirements.txt
 RUN mkdir /src
 WORKDIR /src