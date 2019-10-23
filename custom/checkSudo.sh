#!/bin/sh

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $SCRIPTPATH

# clear out old scopes
rm -f scopes/*.scope 2>/dev/null
# download all scopes
./qallscopes.sh
./sudoscopes.sh
./splitsudo.sh
./sendsudo.sh
