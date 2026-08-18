#!/usr/bin/env bash

./ops/deploy_server.sh
fswatch -E --exclude '__pycache__|.cache|.idea|.git' -ro ./ | xargs -n1 ./ops/deploy_server.sh