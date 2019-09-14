#!/usr/bin/env bash


rsync /Users/jasonbenn/code/flock/sensor/main.py pi:/home/pi/code/flock/main.py
rsync /Users/jasonbenn/code/flock/sensor/requirements.txt pi:/home/pi/code/flock/requirements.txt
#grep -qxF '192.168.86.24  flock.archive.house' /etc/hosts || echo '192.168.86.24  flock.archive.house' >> /etc/hosts
