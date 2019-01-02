FROM python:3.5-alpine
 ENV PYTHONUNBUFFERED 1

 RUN apk update && \
     apk add --virtual build-deps gcc python-dev libmagic musl-dev && \
     apk add postgresql-dev bash

 RUN mkdir /config
 ADD requirements.txt /config/
 RUN pip install -r /config/requirements.txt
 RUN mkdir /src
 WORKDIR /src