#!/usr/bin/env bash
rsync -avhr . flock:/home/flock/code --exclude .env
