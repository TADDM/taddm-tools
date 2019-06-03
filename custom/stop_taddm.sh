#!/bin/sh
# Filename: stop_taddm.sh

# NOTE this script depends on public key trust to secondary and discovery servers

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

echo "Stopping DS"
# STOPPING DISCOVERY SERVERS
for server in `grep -v '^#' $SCRIPTPATH/discovery-servers.txt`
do
  echo " Stopping $server"
  ssh -q -oStrictHostKeyChecking=no $server $COLLATION_HOME/bin/control stop
done

sleep 5

echo "Stopping SSS"
# STOPPING SECONDARY STORAGE SERVERS
for server in `grep -v '^#' $SCRIPTPATH/secondary-storage-servers.txt`
do
  echo " Stopping $server"
  ssh -q -oStrictHostKeyChecking=no $server $COLLATION_HOME/bin/control stop
done

sleep 5

echo "Stopping PSS"
# STARTING LOCAL PRIMARY STORAGE SERVER
$COLLATION_HOME/bin/control stop
