#!/usr/bin/env bash

scp ops/flock-nginx.conf root@flock:/etc/nginx/sites-enabled/flock.conf
ssh root@flock "nginx -s reload"