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

USER=administrator
PASSWORD=collation

rm scopes/session_errors*.scope
SQL="$COLLATION_HOME/custom/sql/session_errors.sql"
for ip in $(cd $BINDIR; ./dbquery.sh -q -c -u "$USER" -p "$PASSWORD" "`cat $SQL`" | grep -v "IP")
do
  scope=`grep -l "$ip," scopes/B_*.scope | grep -E 'B_[a-zA-Z0-9]+_(UNIX|Win|ESXi)_[0-9]+.scope'`
  if [ ! -z "$scope" ]; then
    org=`grep "$ip," $scope | awk -F, '{print $3}' | awk -F\> '{print $3}'`
    if [ -z "$org" ]; then
      org="UNKNOWN"
    fi
    desc=`grep "$ip," $scope | awk -F, '{print $3}'`
    echo "$ip,,$desc" >> scopes/session_errors_${org}.scope
  fi
  #grep "$ip," scopes/${scope}_invalid.scope >> scopes/${scope}_invalid_${org}.scope
done
