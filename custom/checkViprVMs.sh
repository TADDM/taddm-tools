#!/bin/sh

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

# comma separated list of email addresses
EMAIL=

./checkViprVMs.py | mailx -s "Results from ViPR VM hosts with RDM validation" -r "TADDM PROD <cmdbusr1@taddm>" $EMAIL 2>/dev/null
