#!/bin/sh
 
#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT") 
 
# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}
 
BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
 
# get properties file from base name of script by default
SCRIPT=`basename $0`
PROPS=$SCRIPTPATH/`echo $SCRIPT | awk -F. '{print $1}'`.properties
 
# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation
PROFILE="Level 3 Discovery"
 
# read properties file path from arguments
while getopts ":p:" o; do
    case "${o}" in
        p)
            PROPS=${OPTARG}
            ;;
    esac
done
 
echo "Using properties file $PROPS"
 
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
# location for tagging (if applicable)
LOCATION=
# get location out of properties file if present
if [ -e $PROPS ]; then
    LOCATION=`awk -F= '/^LOCATION/ { print $2 }' $PROPS`
fi
 
# capture begin time for script
begin=`date +%s`
 
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
        echo "sleeping 5 minutes at `date` then checking for completion"
        sleep 300
        now=`date +%s`
        total=`expr $now - $begin`
        total=`expr $total / 60` # convert to minutes
        if [ $total -ge $TIMEOUT ]
        then
            echo "Timeout of $TIMEOUT minutes hit at `date`"
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
 
# get scopesets out of properties file if present
if [ -e $PROPS ]; then
    SCOPESETS=`awk -F= '/^SCOPESETS/ { print $2 }' $PROPS`
else
    echo "$PROPS file is not found, please populate with SCOPESETS property and try again"
    exit 1
fi
 
# don't start until all running discoveries complete
echo "Checking for running discoveries before beginning"
wait4discovery
retval=$?
if [ "$retval" != "0" ]; then
    echo "Timed out waiting for existing discoveries to complete, aborting discovery. Sorry."
    exit 1
fi
 
RUNNAME=`hostname`-`date +"%Y%m%d%H%M%S"`
echo "Starting discovery at `date` with name $RUNNAME"
$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover start $([ ! -z "$LOCATION" ] && echo "--locationTag $LOCATION") --name $RUNNAME --profile "$PROFILE" $SCOPESETS
retval=$?
 
if [ "$retval" = "0" ]; then
    echo "Quick 30 second nap to allow discovery to start"
    sleep 30
    echo "Going into sleep cycles until discovery complete"
    wait4discovery
    retval=$?
    if [ "$retval" != "0" ]; then
        echo "Stopping all running discoveries"
        # for some reason the runID parameter for stopping discoveries doesn't work, so you have to stop all discoveries
        $COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover stop
    fi
 
    echo "Discovery completed before `date`"
 
    #
    # check logs for errors
    #
    if [ -e $SCRIPTPATH/checklogs.sh ]; then
        echo "Checking the discovery log files for errors"
        $SCRIPTPATH/checklogs.sh -u $USER -p $PASSWORD -n $RUNNAME
    fi
else
    echo "Discovery failed to start with error code $retval" 1>&2
    exit $retval
fi
