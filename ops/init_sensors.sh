#!/usr/bin/env bash

# Is this needed? ssh pi "sudo chown pi /lib/systemd/system"
scp /Users/jasonbenn/code/flock/ops/sensor_startup_systemd pi:/lib/systemd/system/flock.service
sudo systemctl enable flock.service