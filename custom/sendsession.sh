#!/bin/sh

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $SCRIPTPATH

EMAIL=

# SA organizations
for org in `ls scopes/session_errors_*.scope | awk -F_ '{print $NF}' | awk -F\. '{print $1}' | sort | uniq`
do
  attachments=""
  if [ `wc -l scopes/session_errors_${org}.scope|awk '{print $1}'` -ge 1 ]; then
    attachments="$attachments -a scopes/session_errors_${org}.scope"
  fi

  if [[ ! -z "$attachments" ]]; then
    mailx -s "TADDM session errors (${org})" -r "TADDM <${USER}@${HOSTNAME}>" $attachments $EMAIL 2>/dev/null << EOL
Attached are scope files containing hosts where service account login failed.

If fixing Unix host, below is the combined sudoers configuration needed:

Defaults !requiretty
(root) NOPASSWD: /usr/sbin/dmidecode, /usr/sbin/lsof, /usr/local/bin/lsof, /opt/VRTSvcs/bin/hastatus,
    /opt/VRTSvcs/bin/haclus, /opt/VRTSvcs/bin/hasys, /opt/VRTSvcs/bin/hares, /opt/VRTSvcs/bin/hagrp,
    /opt/VRTSvcs/bin/hatype, /opt/VRTSvcs/bin/hauser, /var/TADDM/home/tadmadm/collectionengine-linux-x86*,
    /var/TADDM/home/tadmadm/collectionengine-solaris-sparc, /usr/sbin/fcinfo, /usr/bin/sg_inq
EOL
  fi
done