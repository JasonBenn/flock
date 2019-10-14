#!/usr/bin/env bash
rsync .prod_env flock:/home/flock/code/server/server/.env
rsync -avhr . flock:/home/flock/code --exclude .env