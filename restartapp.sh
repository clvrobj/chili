#!/bin/bash

PIDFILE="/var/run/flaskapp.pid"

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

exec python ./manage.py runfcgi --protocol=fcgi -h 127.0.0.1 -p 7777 --daemonize --pidfile=/var/run/flaskapp.pid
