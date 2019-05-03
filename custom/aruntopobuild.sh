#!/bin/sh
 
#set -x
 
BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom
 
# get properties file from basename of script
BASENAME=`basename $0 | awk -F. '{print $1}'`
#PROPS=`echo $BASENAME`.properties
LOG=$COLLATION_HOME/log/`echo $BASENAME`.log
 
# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation
 
# logging
log () {
    echo `date +"%Y-%m-%d %H:%M:%S,%3N"` $1 | tee -a $LOG
}
 
# optional TIMESTAMP variable to be set to DiscoveryRun runName (--name in api.sh command)
# if TIMESTAMP is not available then method will wait for all discoveries to stop
# optional HOST variable which query another TADDM host
wait4discovery () {
 
    # set begin to right now if not exist
    if [ -z "$begin" ]; then
        begin=`date +%s`
    fi
 
    # if no timeout present set timeout to 24 hours
    if [ -z "$TIMEOUT" ]; then
        TIMEOUT=`expr 60 \* 24`
    fi
 
    if [ "$TIMESTAMP" == "" ]; then
        status=$($COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD $([ ! -z "$HOST" ] && echo -H $HOST) find -d 1 "SELECT status FROM DiscoveryRun" | awk -F'[<>]' '/status/ {print $3}' | uniq | sort | head -1)
    else
        status=$($COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD $([ ! -z "$HOST" ] && echo -H $HOST) find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$TIMESTAMP'" | awk -F'[<>]' '/status/ {print $3}')
    fi
 
    retval=0
    while [ "$status" != "2" ]
    do
        log "Sleeping 5 minutes then checking for completion"
        sleep 300
        now=`date +%s`
        total=`expr $now - $begin`
        total=`expr $total / 60` # convert to minutes
        if [ $total -ge $TIMEOUT ]
        then
            log "Timeout of $TIMEOUT minutes hit"
            retval=1
            status=2
        else
            if [ "$TIMESTAMP" == "" ]; then
                status=$($COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD $([ ! -z "$HOST" ] && echo -H $HOST) find -d 1 "SELECT status FROM DiscoveryRun" | awk -F'[<>]' '/status/ {print $3}' | uniq | sort | head -1)
            else
                status=$($COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD $([ ! -z "$HOST" ] && echo -H $HOST) find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$TIMESTAMP'" | awk -F'[<>]' '/status/ {print $3}')
            fi
        fi
    done
 
    return "$retval"
}
 
log "Waiting for discoveries to complete"
wait4discovery
log "All discovery servers are Idle"
log "Sleeping 5 minutes and verifying discovery is not running"
sleep 300 # 5 minute nap just to be sure new discovery hasn't started
log "Waiting (again) for discoveries to complete"
wait4discovery
log "All discovery servers are Idle"
 
log "Running full topology build"
 
$COLLATION_HOME/support/bin/runtopobuild.sh -bw
 
log "Full topology build complete"