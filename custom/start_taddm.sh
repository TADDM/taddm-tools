#!/bin/sh
# Filename: start_taddm.sh

# NOTE this script depends on public key trust to secondary and discovery servers

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

echo "Starting PSS"
# STARTING LOCAL PRIMARY STORAGE SERVER
$COLLATION_HOME/bin/control start

sleep 60

# Wait for PSS to start before continuing
echo "Checking server status."
tstatus=`$COLLATION_HOME/bin/control status | awk -F": " '/TADDM/ {print $2}'`
while [ "$tstatus" != "Running" ]
do
    echo "Server status is '${tstatus}' at `date`"
    # sleep 1 minute and check again
    echo "Sleeping 1 minute"
    sleep 60
    tstatus=`$COLLATION_HOME/bin/control status | awk -F": " '/TADDM/ {print $2}'`
done
echo "Server is running."


echo "Starting SSS"
# STARTING SECONDARY STORAGE SERVERS
for server in `grep -v '^#' $SCRIPTPATH/secondary-storage-servers.txt`
do
  echo " Starting $server"
  ssh -q -oStrictHostKeyChecking=no $server $COLLATION_HOME/bin/control start
  sleep 5
done

sleep 60

echo "Starting DS"
# STARTING DISCOVERY SERVERS
for server in `grep -v '^#' $SCRIPTPATH/discovery-servers.txt`
do
  echo " Starting $server"
  ssh -q -oStrictHostKeyChecking=no $server $COLLATION_HOME/bin/control start
  sleep 5
done
