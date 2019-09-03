#!/usr/bin/env bash

FLASK_DEBUG=1 FLASK_APP=server FLASK_ENV=development FLASK_RUN_PORT=8004 flask run --host=0.0.0.0