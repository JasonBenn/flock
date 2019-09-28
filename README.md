# flock

For all long-running commands, use tmux.

To run the server:
`cd ~/flock/server && ./manage.py runserver`

To run a sensor:
Manually: `cd ~/code/flock && python3 main.py >> /var/log/flock.log  #run`
With systemd: `sudo systemctl start flock.service`
Systemctl logs: `sudo journalctl -u flock.service -f`

To use Django admin:
1. https://flock.archive.house/admin
2. Username 'flock', password 'flock"

To use Django shell:
`cd ~/flock/server && ./manage.py shell`

Deploying:
* Server: `bash ops/sync_server.sh`
* Sensors: `bash ops/sync_sensors.sh`

Tests:
`server/manage.py test flock --debug-sql  #tests`
`server/manage.py test flock.tests.LocationEstimationTests.test_hidden_person_location --debug-sql`

Seed a development database:
`server/manage.py seed`

.env:
Create a `.env` file at the root of this directory, put env variables in it (see `settings.py`)

Formatting:
`black --line-length 119 --target-version py36 .  #black`

Database:
Backup: `pg_dump $DB_URL -a -t flock_* > backup.sql`
Restore: `psql $DB_URL < backup.sql`

SSH to all sensors (requires Cluster SSH or [Cluster SSHX](https://github.com/brockgr/csshx/issues/94)):
`csshX pi_backyard pi_study pi_middle_kingdom_kitchen pi_common_room pi_workshop pi_roof pi_jasons_room`