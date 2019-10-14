#!/usr/bin/env bash

echo Deploying $1
rsync -avhr ~/code/flock/sensor/* pi_$1:/home/pi/code/flock/
ssh pi_$1 sudo systemctl restart flock.service