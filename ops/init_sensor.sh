#!/usr/bin/env bash

# scp authorized_keys
ssh pi_$1 "mkdir -p /home/pi/.ssh"
scp ops/authorized_keys pi_$1:/home/pi/.ssh/.

# Enable flock.service
ssh pi_$1 sudo chown pi /lib/systemd/system
scp ~/code/flock/ops/sensor_startup_systemd pi_$1:/lib/systemd/system/flock.service
ssh pi_$1 sudo systemctl enable flock.service

# First deploy
ssh pi_$1 mkdir -p /home/pi/code/flock
rsync -avhr ~/code/flock/sensor/* pi_$1:/home/pi/code/flock/
ssh pi_$1 pip install -r code/flock/requirements.txt

# Install the only environment variable
ssh pi_$1 mkdir -p /home/pi/.config/flock
ssh pi_$1 touch /home/pi/.config/flock/$1
