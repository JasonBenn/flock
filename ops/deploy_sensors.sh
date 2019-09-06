#!/usr/bin/env bash


#scp /Users/jasonbenn/code/flock/sensor/main.sh pi:/home/pi/code/flock/main.sh
rsync /Users/jasonbenn/code/flock/sensor/main.py pi:/home/pi/code/flock/main.py
grep -qxF '192.168.86.86  flock.archive.house' /etc/hosts || echo '192.168.86.86  flock.archive.house' >> /etc/hosts
