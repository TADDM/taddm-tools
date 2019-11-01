#!/bin/sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation

for fileName in `ls -1 scopes`
do
    echo "Processing $fileName"
    # remove comment character and trim leading and trailing space from scope name
    scopeName=`head -1 scopes/$fileName | tr -d '#' | sed -e 's/^ *//' -e 's/ *$//'`
    echo "Scope name is $scopeName"
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/$fileName"
    cd $COLLATION_HOME/custom
done