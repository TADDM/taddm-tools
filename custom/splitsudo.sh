#!/bin/sh

# this script takes the sudo scopes created by sudoscopes.sh and creates new scopes
# split up by SA org, this script is sample of how to split up the scopes if needed
# so that separate lists can be sent to separate SA orgs

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

# cleanup and previous scopes
rm -f scopes/sudo_*invalid_*.scope 2>/dev/null

scopes=( "sudo" "sudo_lsof" "sudo_dmidecode" "sudo_hba" "sudo_hba_path" "sudo_rdm" )
for scope in "${scopes[@]}"
do
  if [ `wc -l scopes/${scope}_invalid.scope|awk '{print $1}'` -gt 1 ]; then
    for ip in `grep -v "#" scopes/${scope}_invalid.scope | awk -F, '{print $1}'` 
    do
	  # Find the SA org for this IP, assuming that the managed scopes are
	  # extracted to scopes/ and the file names start with B_*. Removing
	  # any scopeset files that have "rescan" in the name. Also assuming that
	  # description field in scopeset is of the form "hostname>datacenter>org"
      org=`grep "$ip," scopes/B_*.scope | grep -v "rescan" | awk -F, '{print $3}' | awk -F\> '{print $3}'`
      if [ -z "$org" ]; then
        echo "$ip not found in any organization"
        grep "$ip," scopes/${scope}_invalid.scope >> scopes/${scope}_invalid_UNKNOWN.scope
      else
        grep "$ip," scopes/${scope}_invalid.scope >> scopes/${scope}_invalid_${org}.scope
      fi
    done
  fi
done
