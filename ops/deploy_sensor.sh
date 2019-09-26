#!/usr/bin/env bash
rsync -avhr ~/code/flock/sensor/* pi_$1:/home/pi/code/flock/
