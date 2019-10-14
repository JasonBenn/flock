#!/usr/bin/env bash

ssh pi_$1 systemctl is-active --quiet flock.service && exit 0
echo
echo $1
echo ssh pi_$1 systemctl start flock.service
ssh pi_$1 systemctl status flock.service
echo