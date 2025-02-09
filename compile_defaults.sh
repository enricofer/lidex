#!/bin/bash

if [ ! -f /defaults/app-conf.json ]; then
    export $(grep -v '^#' .env | xargs)
    cat /defaults/app-conf_tmpl.json | /usr/bin/envsubst > /defaults/app-conf.json
fi



