SHELL := /usr/bin/env bash

test_post_macs:
	curl -v localhost:8000/scans -X POST -d '{"location": "common_room", "scan_results": [{"mac": "5C:F9:38:95:06:17", "rssi": null, "scanned_at": "2019-10-26 15:43:50.351126"}]}'

check_sensors:
	bash ops/run_on_all_sensors.sh ops/check_sensor.sh

deploy_sensors:
	bash ops/run_on_all_sensors.sh ops/deploy_sensor.sh

init_sensors:
	bash ops/run_on_all_sensors.sh ops/init_sensor.sh

pip_install_sensors:
	bash ops/run_on_all_sensors.sh ops/pip_install_sensor.sh