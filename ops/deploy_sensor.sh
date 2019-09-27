#!/usr/bin/env bash
ssh pi_$1 mkdir -p /home/pi/code/flock
rsync -avhr ~/code/flock/sensor/* pi_$1:/home/pi/code/flock/
