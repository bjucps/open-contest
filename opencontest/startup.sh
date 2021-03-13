#!/bin/bash

# This script runs in the Docker container and starts the Django application

STARTUP_CMD="uwsgi --threads 50 --http 0.0.0.0:8000 --module opencontest.wsgi --ini uwsgi.ini $*"

if [ "$OC_MONITORING" = 1 ]; then
    if [ -r /db/newrelic.ini ]; then
        echo -e "Starting CMS application in Docker with New Relic monitoring ...\n$STARTUP_CMD"
        NEW_RELIC_CONFIG_FILE=/db/newrelic.ini newrelic-admin run-program $STARTUP_CMD
    else
        echo "** New Relic monitoring enabled but newrelic.ini not found in database folder, starting without New Relic"
    fi
fi
echo -e "Starting CMS application in Docker... \n$STARTUP_CMD"
$STARTUP_CMD


