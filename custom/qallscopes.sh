#!/bin/sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

mkdir scopes 2> /dev/null

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=operator
PASSWORD=collation

../sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "select name from Scope" | awk -F'[<>]' '/name/ {print $3}' | while read line
do 
    ./queryscopes.jy -u $USER -p $PASSWORD -s "$line" > scopes/`echo $line | tr ' ' _`.scope
done