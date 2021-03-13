#!/bin/bash

# This script runs in the Docker container and starts the Django application

STARTUP_CMD="uwsgi --threads 50 --http 0.0.0.0:8000 --module opencontest.wsgi --ini uwsgi.ini $*"
if [ "$OC_MONITORING" -eq 1 ]; then
    echo "Starting CMS application in Docker with newrelic monitoring: $STARTUP_CMD"
    NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program $STARTUP_CMD
else
    echo "Starting CMS application in Docker: $STARTUP_CMD"
    $STARTUP_CMD
fi

