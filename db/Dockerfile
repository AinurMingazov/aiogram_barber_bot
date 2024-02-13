FROM postgres:14.1

RUN apt update && apt install -y gettext-base

COPY db/initial.sql /tmp/initial.sql
RUN mkdir -p "/var/log/postgresql/"

ARG POSTGRES_USER
ARG POSTGRES_DB
ARG POSTGRES_PASSWORD
RUN POSTGRES_USER=${POSTGRES_USER} POSTGRES_DB=${POSTGRES_DB} POSTGRES_PASSWORD=${POSTGRES_PASSWORD} envsubst < /tmp/initial.sql > /docker-entrypoint-initdb.d/initial.sql

EXPOSE 5335
