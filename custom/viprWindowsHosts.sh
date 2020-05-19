#!/bin/sh

USER=
ANCHOR=
# base64 encoded user:password
AUTH=
VIPR=

for line in `ssh -q ${USER}@${ANCHOR} "curl -s -k -H \"Authorization: Basic ${AUTH}\" \"https://${VIPR}:58443/APG-REST/metrics/properties/values?filter=parttype='Disk'%26devtype='Host'%26devdesc='%25Windows%25'&fields=device,ip\"" | python parseViprWindows.py`
do
  hostname=`echo $line | awk -F: '{printf $1}'`
  found="false"
  for ip in `echo $line | awk -F: '{printf $2}' | tr "," " "`
  do
    if nslookup $ip | grep "$hostname\." >/dev/null
    then
      echo $ip",,"$hostname
      found="true"
    # else
      # echo " "$ip",,"$hostname
    fi
  done

  if [ "$found" == "false" ]
  then
    # try to use hostname to find IP
    ip=`nslookup $hostname | tail -2 | grep '^Address' | awk '{printf $2}'`
    if [ ! -z "$ip" ]
    then
      found="true"
      echo $ip",,"$hostname
    fi
  fi

  if [ "$found" == "false" ]
  then
    # use the first lookup with any results
    for ip in `echo $line | awk -F: '{printf $2}' | tr "," " "`
    do
      if nslookup $ip >/dev/null
      then
        echo $ip",,"$hostname
        found="true"
        break
      fi
    done
  fi

  if [ "$found" == "false" ]
  then
    # still nothing, use the first IP
    firstip=`echo $line | awk -F: '{printf $2}' | tr "," " " | awk '{printf $1}'`
    echo $firstip",,"$hostname
  fi
done | sort | uniq


