#!/usr/bin/env bash

~/code/flock/ops/deploy_sensors.sh
fswatch sensor/main.py ~/ | xargs -n1 ~/code/flock/ops/deploy_sensors.sh