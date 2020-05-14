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
    eval "echo \"$(cat msg_sudo.txt)\"" | mailx -s "TADDM sudo config (${org})" -r "TADDM <${USER}@${HOSTNAME}>" $attachments $EMAIL 2>/dev/null
  fi
done