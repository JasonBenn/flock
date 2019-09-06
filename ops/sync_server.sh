#!/usr/bin/env bash

~/code/flock/ops/deploy_server.sh
fswatch -E --exclude '__pycache__|.cache|.idea|.git' -ro ~/code/flock/ | xargs -n1 ~/code/flock/ops/deploy_server.sh