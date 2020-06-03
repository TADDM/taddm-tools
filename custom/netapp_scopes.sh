#!/bin/sh
# This script has been tested with Netapp OCUM 9.6

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

cd $SCRIPTPATH

PROPS=$SCRIPTPATH/custom.properties
if [ -e $PROPS ]; then
  # get Netapp OCUM credentials from properties file
  OCUM_CRED=`awk -F= '/^OCUM_CRED/ {print $2}' $PROPS`
  # get Netapp OCUM credentials from properties file
  OCUM_HOST=`awk -F= '/^OCUM_HOST/ {print $2}' $PROPS`
else
  echo "Properties file $PROPS not found"
  exit 1
fi

output=
if $(curl -k -m 5 -u $OCUM_CRED -s -X GET --header 'Accept: application/vnd.netapp.object.inventory.performance.hal+json;charset=UTF-8' "https://${OCUM_HOST}/api/ontap/clusters?max_records=100")
then
  output=$(curl -k -m 5 -u $OCUM_CRED -s -X GET --header 'Accept: application/vnd.netapp.object.inventory.performance.hal+json;charset=UTF-8' "https://${OCUM_HOST}/api/ontap/clusters?max_records=100")
elif [[ -f netapp_clusters.json ]]
then
  # network connection problem, use static output from netapp_clusters.json
  output=$(cat netapp_clusters.json)
else
  echo "REST failed and no static netapp_clusters.json file found"
  exit 2
fi

for line in $(echo $output | python -c '
import sys, json
values=json.load(sys.stdin)["_embedded"]["netapp:clusterInventoryList"]
for v in values:
  print str(v["cluster_fqdn"]) + ":" + str(v["network_address"])
')
do
  fqdn=$(echo $line | awk -F: '{printf $1}')
  ip=$(echo $line | awk -F: '{printf $2}')
  # check if IP is valid, sometimes it's the fqdn
  if ! [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
    # IP is not valid, find IP from fqdn
    ip=$(nslookup $fqdn | tail -2 | grep '^Address' | awk '{printf $2}')
    if [[ "$ip" == "" ]]; then
      echo -n "#" # comment out this one because we can't find IP
    fi
  fi
  echo $ip",,"$fqdn
done | sort | uniq
