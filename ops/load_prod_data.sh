#!/usr/bin/env bash

source .env
ssh flock "pg_dump $DB_URL -a -T social_auth*" > /tmp/backup.sql
dropdb flock
createdb -O flock -p 5432 flock
server/manage.py migrate
psql $DB_URL < /tmp/backup.sql
