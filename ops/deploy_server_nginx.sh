#!/usr/bin/env bash

scp /Users/jasonbenn/code/flock/ops/flock-nginx.conf ml-box:/etc/nginx/sites-enabled/flock.conf
ssh ml-box "nginx -s reload"