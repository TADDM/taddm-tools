#!/bin/sh

USER=
ANCHOR=
# base64 encoded user:password
AUTH=
VIPR=

for line in `ssh -q ${USER}@${ANCHOR} "curl -s -k -H \"Authorization: Basic ${AUTH}\" \"https://${VIPR}:58443/APG-REST/metrics/properties/values?filter=devtype='Host'%26virtual='false'%26osarch='%Linux%'%26parttype='Path'&fields=device,ip\"" | python parseViprLinux.py`
do
  hostname=`echo $line | awk -F: '{printf $1}'`
  found="false"
  for ip in `echo $line | awk -F: '{printf $2}' | tr "," " "`
  do
    if nslookup $ip | grep "$hostname\." >/dev/null
    then
      echo $ip",,"$hostname
      found="true"
    fi
  done
  # if not found, look for mgmt interface
  if [ "$found" == "false" ]
  then
    for ip in `echo $line | awk -F: '{printf $2}' | tr "," " "`
    do
      if nslookup $ip | grep "${hostname}-mgmt\." >/dev/null
      then
        echo $ip",,"$hostname
        found="true"
      fi
    done
  fi
  # if not found, put comment in scope
  if [ "$found" == "false" ]
  then
    ip=`nslookup $hostname | tail -2 | grep '^Address' | awk '{printf $2}'`
    if [ "$ip" == "" ]; then
      echo -n "#"
    fi
    echo $ip",,"$hostname
  fi
done | sort | uniq

