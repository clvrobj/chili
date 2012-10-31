#!/bin/bash

PIDFILE="./flaskapp.pid"
ERRLOG="./flaskerr.log"
OUTLOG="./flaskout.log"

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

exec python ./manage.py runfcgi --protocol=fcgi -h 127.0.0.1 -p 7777 --daemonize --pidfile=$PIDFILE --errlog=$ERRLOG --outlog=$OUTLOG
