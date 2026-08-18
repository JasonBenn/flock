SHELL := /usr/bin/env bash

# Testing
test_post_scans:
	curl -v 127.0.0.1:8000/scans -d '{"location": "common_room", "scan_results": [{"mac": "AA:BB:CC:DD:00:11", "rssi": null, "scanned_at": "2019-10-26 15:43:50.351126"}]}'

test:
	server/manage.py test flock

test_one:
	server/manage.py test -s flock.tests:LocationEstimationTests.test_hidden_person_location

# Local development
reload_runserver:
	bash ops/load_prod_data.sh
	FREEZE_TIME=1 server/manage.py runserver

reload_db:
	bash ops/load_prod_data.sh

runserver:
	FREEZE_TIME=1 server/manage.py runserver

DB_URL=postgresql://flock:flock@127.0.0.1:5432/flock
dump_db:
	pg_dump $(DB_URL) -a > backup_2.sql

# All sensors
check_sensors:
	bash ops/run_on_all_sensors.sh ops/check_sensor.sh

deploy_sensors:
	bash ops/run_on_all_sensors.sh ops/deploy_sensor.sh

init_sensors:
	bash ops/run_on_all_sensors.sh ops/init_sensor.sh

pip_install_sensors:
	bash ops/run_on_all_sensors.sh ops/pip_install_sensor.sh

# Single sensor
SENSOR = common_room
deploy_sensor:
	ops/deploy_sensor.sh $(SENSOR)

init_sensor:
	ops/init_sensor.sh $(SENSOR)

pip_install_sensor:
	ops/pip_install_sensor.sh $(SENSOR)


# Server
deploy_server:
	bash ops/server/deploy.sh

update_crontab:
	# crontab -e, copy ./ops/crontab over
	ssh flock sudo systemctl restart cron

download_prod_env:
	scp flock:/home/flock/code/server/server/.env /Users/jasonbenn/code/flock/.prod_env

upload_prod_env:
	scp /Users/jasonbenn/code/flock/.prod_env flock:/home/flock/code/server/server/.env
    # log in, reboot server
