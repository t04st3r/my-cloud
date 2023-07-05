FROM python:3.11-slim as base

# Install system packages
RUN apt-get update && apt-get upgrade -y && \
    apt-get autoremove -y && apt-get autoclean -y && \
    apt-get install -y --no-install-recommends make jq libpq-dev

WORKDIR /app/    

COPY . .    

RUN make install-ci

ENTRYPOINT [ "make" ]