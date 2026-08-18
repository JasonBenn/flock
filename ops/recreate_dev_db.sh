#!/usr/bin/env bash

source .env
dropdb flock
createdb -O flock -p 5432 flock
server/manage.py migrate
server/manage.py seed
