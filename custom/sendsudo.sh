#!/bin/sh

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $SCRIPTPATH

#
# set comma separated email addresses
#
EMAIL=

# SA organizations
for org in `ls scopes/sudo_*invalid_*.scope | awk -F_ '{print $NF}' | awk -F\. '{print $1}' | sort | uniq`
do
  scopes=( "sudo" "sudo_lsof" "sudo_dmidecode" "sudo_hba" "sudo_hba_path" "sudo_rdm" )
  attachments=""
  for scope in "${scopes[@]}"
  do
    if [ -f "scopes/${scope}_invalid_${org}.scope" ]; then
      if [ `wc -l scopes/${scope}_invalid_${org}.scope|awk '{print $1}'` -gt 1 ]; then
        attachments="$attachments -a scopes/${scope}_invalid_${org}.scope"
      fi
    fi
  done

  if [[ ! -z "$attachments" ]]; then
    mailx -s "TADDM sudo config (${org})" -r "TADDM <${USER}@${HOSTNAME}>" $attachments $EMAIL 2>/dev/null << EOL
Attached are scope files containing hosts where sudo is either not configured or not configured properly. Note that if a particular file is not attached, then there were no issues detected for that config type. 

Key:
  sudo_invalid_${org}.scope - sudo not configured or requiretty problem
  sudo_lsof_invalid_${org}.scope - lsof not in sudo
  sudo_dmidecode_invalid_${org}.scope - dmidecode not in sudo for Linux host
  sudo_hba_invalid_${org}.scope - collectionengine not in sudo and/or fcinfo not in sudo for Solaris and/or powermt not in sudo for physical Linux if installed
  sudo_hba_path_invalid_${org}.scope - collectionengine path mismatch, most likely unexpected home dir path for service account
  sudo_rdm_invalid_${org}.scope - sg_inq not in sudo for VMware Linux VM containing RDM

Below is the combined sudoers configuration for Linux and Solaris:

Defaults !requiretty
(root) NOPASSWD: /usr/sbin/dmidecode, /usr/sbin/lsof, /usr/local/bin/lsof, /opt/VRTSvcs/bin/hastatus,
    /opt/VRTSvcs/bin/haclus, /opt/VRTSvcs/bin/hasys, /opt/VRTSvcs/bin/hares, /opt/VRTSvcs/bin/hagrp,
    /opt/VRTSvcs/bin/hatype, /opt/VRTSvcs/bin/hauser, /var/TADDM/home/tadmadm/collectionengine-linux-x86*,
    /var/TADDM/home/tadmadm/collectionengine-solaris-sparc, /usr/sbin/fcinfo, /usr/bin/sg_inq,
	/sbin/powermt display dev\=all
EOL
  fi
done
