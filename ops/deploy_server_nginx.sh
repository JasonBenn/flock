#!/usr/bin/env bash

scp ops/flock-nginx.conf flock:/etc/nginx/sites-enabled/flock.conf
ssh flock "nginx -s reload"