#!/usr/bin/env bash

/Users/jasonbenn/code/flock/ops/deploy_sensors.sh
fswatch sensor/main.py ~/ | xargs -n1 ~/code/flock/ops/deploy_sensors.sh