#!/bin/sh
# This script runs only BindAddress archiving, this needs run nightly because there are so many
 
#set -x
 
BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom
 
TIMESTAMP=`date +"%Y%m%d%H%M"`
 
# copy current state
cp classes.txt classes.${TIMESTAMP}
# crate new file with only BindAddress
echo "BindAddress" > classes.txt
# run the archive in the background
./archive.sh >archive.out 2>&1 &
# sleep to allow archive to read modified classes.txt
sleep 10
# restore state
mv classes.${TIMESTAMP} classes.txt