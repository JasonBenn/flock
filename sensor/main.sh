#!/usr/bin/env bash

name=$(curl -s google.com)
found=$?

if [ $found -eq 0 ]; then
  echo $name | jq -aRr '{name: .}' | curl -sS -X POST -d @- localhost:9000
else
  echo 'nope'
fi
