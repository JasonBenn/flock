SHELL := /usr/bin/env bash

# Testing
test_post_scans:
	curl -v localhost:8000/scans -X POST -d '{"location": "common_room", "scan_results": [{"mac": "5C:F9:38:95:06:17", "rssi": null, "scanned_at": "2019-10-26 15:43:50.351126"}]}'

test:
	server/manage.py test flock

test_one:
	server/manage.py test -s flock.tests:LocationEstimationTests.test_hidden_person_location

# Sensors
check_sensors:
	bash ops/run_on_all_sensors.sh ops/check_sensor.sh

deploy_sensors:
	bash ops/run_on_all_sensors.sh ops/deploy_sensor.sh

init_sensors:
	bash ops/run_on_all_sensors.sh ops/init_sensor.sh

pip_install_sensors:
	bash ops/run_on_all_sensors.sh ops/pip_install_sensor.sh

# Server
deploy_server:
	bash ops/server/deploy.sh

reload_server:
	bash ops/load_prod_data.sh
	server/manage.py runserver

reload_db:
	bash ops/load_prod_data.sh
