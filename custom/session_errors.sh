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

rm scopes/session_errors*.scope 2>/dev/null
SQL="$COLLATION_HOME/custom/sql/session_errors.sql"
(cd $BINDIR; ./dbquery.sh -q -c -u "$USER" -p "$PASSWORD" "`cat $SQL`" | grep -v "IP,SENSOR") | while read row
do
  ip=`echo $row | awk -F, '{print $1}'`
  ssh=false
  wmi=false
  while read ports
  do 
    for port in `echo "${ports//,}"`
    do 
      if [ "$port" -eq "135" ]
      then
        # if port 135 is found then it is WMI login
        wmi=true
      fi
      if [ "$port" -eq "22" ]
      then
        # if port 22 is found then it is SSH login
        ssh=true
      fi
    done
  done <<< $(echo $row | cut -d "[" -f2 | cut -d "]" -f1)
  
  #
  # This section checks to see if the IP target is in a "managed" scope set.
  # These are scopesets that are discovered regularly. It is best practice to
  # use a naming convention for these scope sets.
  # 
  # This assumes that the qallscopes.sh script has been run previously and all
  # the scopesets are in .scope files under custom/scopes.
  #
  # You will need to tailor the grep command below to your environment to match
  # the scope files that are part of your managed scopesets.
  #
  scope=`grep -l "$ip," scopes/B_*.scope | grep -E 'B_[a-zA-Z0-9]+_(UNIX|Win|ESXi)_[0-9]+.scope'`
  
  # make sure that IP is in a managed scope
  if [ ! -z "$scope" ]; then
    #
    # extracting the organization from the scope
    # 
    # You will need to tailor this to your environment, if the Systems Admin
    # org is somewhere in the scope description. In the example below, the
    # org is found in the description after 2 '>' symbols
    #
    org=`grep "$ip," $scope | awk -F, '{print $3}' | awk -F\> '{print $3}'`
    if [ -z "$org" ]; then
      org="UNKNOWN"
    fi
    method="unknown"
    if [ "$ssh" = true ]; then
      method="ssh"
      if [ "$wmi" = true ]; then
        method="ssh/wmi"
        fi
    elif [ "$wmi" = true ]; then
      method="wmi"
    fi
    desc=`grep "$ip," $scope | awk -F, '{print $3}'`
    echo "$ip,,$desc ($method)" >> scopes/session_errors_${org}.scope
  fi
  #grep "$ip," scopes/${scope}_invalid.scope >> scopes/${scope}_invalid_${org}.scope
done
