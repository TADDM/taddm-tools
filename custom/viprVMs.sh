#!/bin/sh

USER=
ANCHOR=
# base64 encoded user:password
AUTH=
VIPR=

for line in `ssh -q ${USER}@${ANCHOR} "curl -s -k -H \"Authorization: Basic ${AUTH}\" \"https://${VIPR}:58443/APG-REST/metrics/properties/values?filter=devtype=%27VirtualMachine%27%26parttype=%27Virtual%20Disk%27%26dtype=%27RDM%27&fields=device,ip,fqdn\"" | python parseViprVMs.py`
do
  hostname=`echo $line | awk -F: '{printf $1}'`
  fqdn=`echo $line | awk -F: '{printf $3}'`
  found="false"
  for ip in `echo $line | awk -F: '{printf $2}' | tr "," " "`
  do
    if nslookup $ip | grep "$hostname\." >/dev/null
    then
      echo $ip",,"$fqdn
      found="true"
    # else
      # echo " "$ip",,"$hostname
    fi
  done
  if [ "$found" == "false" ]
  then
    ip=`nslookup $hostname | tail -2 | grep '^Address' | awk '{printf $2}'`
    if [ "$ip" == "" ]; then
      echo -n "#"
    fi
    echo $ip",,"$fqdn
  fi
done | sort | uniq

