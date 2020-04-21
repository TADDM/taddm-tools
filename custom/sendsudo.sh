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
  scopes=( "sudo" "sudo_lsof" "sudo_dmidecode" "sudo_hba" "sudo_hba_path" "sudo_rdm" "sudo_emc" )
  attachments=""
  for scope in "${scopes[@]}"
  do
    if [ -f "scopes/${scope}_invalid_${org}.scope" ]; then
      if [ `wc -l scopes/${scope}_invalid_${org}.scope|awk '{print $1}'` -ge 1 ]; then
        attachments="$attachments -a scopes/${scope}_invalid_${org}.scope"
      fi
    fi
  done

  if [[ ! -z "$attachments" ]]; then
    attachments="$attachments -a sudoers.txt"
    mailx -s "TADDM sudo config (${org})" -r "TADDM <${USER}@${HOSTNAME}>" $attachments $EMAIL 2>/dev/null << EOL
Attached are text files (.scope) containing hosts where sudo is either not configured or not configured properly. Note that if a particular file is not attached, then there were no issues detected for that config type.

Key:
  sudo_invalid_${org}.scope - sudo not configured or requiretty problem
  sudo_lsof_invalid_${org}.scope - lsof not in sudo
  sudo_dmidecode_invalid_${org}.scope - dmidecode not in sudo for Linux host
  sudo_hba_invalid_${org}.scope - collectionengine not in sudo and/or fcinfo not in sudo for Solaris and/or powermt not in sudo for physical Linux if installed
  sudo_emc_invalid_${org}.scope - EMC INQ tool not in sudo, also move inq.<platform> binary from service account home directory to /usr/local/bin
  sudo_hba_path_invalid_${org}.scope - collectionengine path mismatch, most likely unexpected home dir path for service account
  sudo_rdm_invalid_${org}.scope - sg_inq not in sudo for VMware Linux VM containing RDM

Also attached is sudoers.txt, which is the official, approved sudoers configuration for TADDM.
Use these values to configure sudo for the TADDM service account.

EOL
  fi
done