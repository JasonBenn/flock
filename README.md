# flock

For all long-running commands, use tmux.

To run the server:
`cd ~/flock/server && ./manage.py runserver`

To run a sensor:
`cd ~/code/flock && python3 main.py`

To use Django admin:
1. https://flock.archive.house/admin
2. Username 'flock', password 'flock"

To use Django shell:
`cd ~/flock/server && ./manage.py shell`

Deploying:
* Server: bash ops/sync_server.sh
* Sensors: bash ops/sync_sensors.sh
