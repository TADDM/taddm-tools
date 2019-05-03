#!/bin/sh

# This script will copy chunks of ASD output files and run discovery for them
 
#set -x
 
BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom
 
# get properties file from basename of script
BASENAME=`basename $0 | awk -F. '{print $1}'` 
PROPS=`echo $BASENAME`.properties
LOG=$COLLATION_HOME/log/`echo $BASENAME`.log
 
# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation
PROFILE="Level 3 Discovery"
# get profile out of properties file if present
if [ -e $PROPS ]; then
    PROFILE=`awk -F= '/^PROFILE/ { print $2 }' $PROPS`
fi
# kill discovery after this many minutes
TIMEOUT=10080 # default is 1 week
# get timeout out of properties file if present
if [ -e $PROPS ]; then
    TIMEOUT=`awk -F= '/^TIMEOUT/ { print $2 }' $PROPS`
fi
 
# capture begin time for script
begin=`date +%s`
 
# logging
log () {
    echo `date +"%Y-%m-%d %H:%M:%S,%3N"` $1 | tee -a $LOG
}
 
# optional RUNNAME variable to be set to DiscoveryRun runName (--name in api.sh command)
# if RUNNAME is not available then method will wait for all discoveries to stop
wait4discovery () {
    if [ "$RUNNAME" == "" ]; then
        # this line waits for all discoveries to complete across all discovery servers
        #status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun" | awk -F'[<>]' '/status/ {print $3}' | uniq | sort | head -1`
        status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover status`
        status=`[ "$status" == "Idle" ] && echo 2 || echo 1`
    else
        status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$RUNNAME'" | awk -F'[<>]' '/status/ {print $3}'`
    fi
 
    retval=0
    while [ "$status" != "2" ]
    do
        log "sleeping 5 minutes then checking for completion"
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
            if [ "$RUNNAME" == "" ]; then
                # this line waits for all discoveries to complete across all discovery servers
                #status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun" | awk -F'[<>]' '/status/ {print $3}' | uniq | sort | head -1`
                status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover status`
                status=`[ "$status" == "Idle" ] && echo 2 || echo 1`
            else
                status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$RUNNAME'" | awk -F'[<>]' '/status/ {print $3}'`
            fi
        fi
    done
 
    return "$retval"
}
 
###############################################################################
# Start Discoveries
###############################################################################
 
# maximum number of packages to process on this run
CHUNKSIZE=2000 # default
# get timeout out of properties file if present
if [ -e $PROPS ]; then
    CHUNKSIZE=`awk -F= '/^CHUNKSIZE/ { print $2 }' $PROPS`
fi
# get source directory
if [ -e $PROPS ]; then
    SOURCEDIR=`awk -F= '/^SOURCEDIR/ { print $2 }' $PROPS`
else
    log "$PROPS file is not found, please populate with SOURCEDIR property and try again"
    exit 1
fi
 
# don't start until all running discoveries complete
log "Checking for running discoveries before beginning"
wait4discovery
retval=$?
if [ "$retval" != "0" ]; then
    log "Timed out waiting for existing discoveries to complete, aborting discovery. Sorry."
    exit 1
fi
 
TIMESTAMP=`date +"%Y%m%d%H%M%S"`
RUNNAME=`hostname`-${TIMESTAMP}
 
log "Moving max $CHUNKSIZE ASD package files from $SOURCEDIR to $COLLATION_HOME/var/asdd"
# copy ASD packages
for f in `ls -t1 $SOURCEDIR | grep tar | tail -${CHUNKSIZE}`; do
    mkdir -p archive/asd/$TIMESTAMP 2>/dev/null
    cp $SOURCEDIR/$f archive/asd/$TIMESTAMP
    mv $SOURCEDIR/$f $COLLATION_HOME/var/asdd 
    # unzip if needed
    if [ "`file $COLLATION_HOME/var/asdd/$f | grep 'gzip compressed data'`" != "" ]; then
        gunzip $COLLATION_HOME/var/asdd/$f 2>/dev/null
        # if gunzip failed then move file back into source directory
        if [ "$?" != "0" ]; then
            log "$COLLATION_HOME/var/asdd/$f failed gunzip and will be removed from processing"
            mv $COLLATION_HOME/var/asdd/$f $SOURCEDIR
            continue
        fi
    fi
    # gzip was successful, check if tar file is empty
    f=`echo $f | sed s/\.gz//` # remove .gz extension if exists
    if [ "`file $COLLATION_HOME/var/asdd/$f | grep ' empty'`" != "" ]; then
        log "$COLLATION_HOME/var/asdd/$f is an empty file and will be removed from processing"
        mv $COLLATION_HOME/var/asdd/$f $SOURCEDIR
    fi
done
 
MOVED=`ls $COLLATION_HOME/var/asdd/*.tar 2>/dev/null| wc -l`
log "Moved $MOVED ASD packages for processing"
 
# end script if no packages to process
if [ "$MOVED" == "0" ]; then
    log "No packages to process, aborting"
    exit 1
fi
 
# get scopesets out of properties file if present
if [ -e $PROPS ]; then
    SCOPESETS=`awk -F= '/^SCOPESETS/ { print $2 }' $PROPS`
else
    log "$PROPS file is not found, please populate with SCOPESETS property and try again"
    exit 1
fi
 
# get file names to process so we can clean them up later
files=`ls $COLLATION_HOME/var/asdd/*.tar 2>/dev/null`
log "Starting discovery"
$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover start --name $RUNNAME --profile "$PROFILE" $SCOPESETS
retval=$?
 
if [ "$retval" = "0" ]; then
    sleep 30
    wait4discovery
    retval=$?
    if [ "$retval" != "0" ]; then
        log "Stopping all running discoveries"
        # for some reason the runID parameter for stopping discoveries doesn't work, so you have to stop all discoveries
        $COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover stop
    fi
 
    if [ "$files" != "" ]; then
        # check if other discovery running before cleaning up ASD files
        status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover status`
        if [ "$status" = "Idle" ]; then
            # clear out output directories
            (cd $COLLATION_HOME/var/asdd; find taddmasd-* -type d -maxdepth 0 -exec rm -fr {} \; 2>/dev/null)
            # clear out DONE results
            (cd $COLLATION_HOME/var/asdd; rm *_DONE  2>/dev/null)
        fi
    fi
 
    #
    # check logs for errors
    #
    log "Checking the discovery log files for errors"
    ./checklogs.sh -u $USER -p $PASSWORD -n $RUNNAME
    log "Discovery complete"
else
    log "Discovery failed to start with error code $retval" 1>&2
    exit $retval
fi
