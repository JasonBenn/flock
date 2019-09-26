#!/usr/bin/env bash

# Is this needed? ssh pi "sudo chown pi /lib/systemd/system"

# scp authorized_keys
ssh pi_$1 "mkdir -p /home/pi/.ssh"
scp ops/authorized_keys pi_$1:/home/pi/.ssh/.

# should match an ssh config
#scp /Users/jasonbenn/code/flock/ops/sensor_startup_systemd pi:/lib/systemd/system/flock.service
#sudo systemctl enable flock.service
