#!/bin/sh

#set -x

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=operator
PASSWORD=collation

usage() {
  echo "Usage: $0 { -p <prefix> }"
  echo "  Use -p to feed in scopeset name prefix to filter results"
}

while getopts ":p:h" o; do
  case "${o}" in
    p)
      p=${OPTARG}
      ;;
    h)
      usage
      exit 1
      ;;
  esac
done

SQL="select name from Scope"
if [ ! -z "${p}" ]; then
  SQL="$SQL where name starts-with '${p}'"
fi

../sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "${SQL}" | awk -F'[<>]' '/name/ {print $3}' | while read line
do
    ./queryscopes.jy -u $USER -p $PASSWORD -s "$line" > scopes/`echo $line | tr ' ' _`.scope
done