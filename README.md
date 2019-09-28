# flock

For all long-running commands, use tmux.

To run the server:
`cd ~/flock/server && ./manage.py runserver`

To run a sensor:
Manually: `cd ~/code/flock && python3 main.py >> /var/log/flock.log  #run`
With systemd: `sudo systemctl start flock.service`
Systemctl logs (not very useful atm): `sudo journalctl -u flock.service -f`

To use Django admin:
1. https://flock.archive.house/admin
2. Username 'flock', password 'flock"

To use Django shell:
`cd ~/flock/server && ./manage.py shell`

Deploying:
* Server: `bash ops/sync_server.sh`
* Sensors: `bash ops/sync_sensors.sh`

Tests:
`./manage.py test --debug-sql`

.env:
Create a `.env` file at the root of this directory, put env variables in it (see `settings.py`)

Formatting:
`black --line-length 119 --target-version py36 .  #black`