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
for org in `ls scopes/sudo_*invalid_*.scope scopes/session_errors_*.scope | awk -F_ '{print $NF}' | awk -F\. '{print $1}' | sort | uniq`
do
  scopes=( "sudo" "sudo_lsof" "sudo_dmidecode" "sudo_hba" "sudo_hba_path" "sudo_rdm" "sudo_emc" )
  attachments=""
  sudoerr=""
  for scope in "${scopes[@]}"
  do
    if [ -f "scopes/${scope}_invalid_${org}.scope" ]; then
      if [ `wc -l scopes/${scope}_invalid_${org}.scope|awk '{print $1}'` -ge 1 ]; then
        attachments="$attachments -a scopes/${scope}_invalid_${org}.scope"
        sudoerr="true"
      fi
    fi
  done

  sesserr=""
  if [ -f "scopes/session_errors_${org}.scope" ]; then
    if [ `wc -l scopes/session_errors_${org}.scope 2>/dev/null |awk '{print $1}'` -ge 1 ]; then
      attachments="$attachments -a scopes/session_errors_${org}.scope"
      sesserr="true"
    fi
  fi

  if [[ ! -z "$attachments" ]]; then
    msg=
    attachments="$attachments -a sudoers.txt"
    subject="TADDM"
    if [[ ! -z "$sudoerr" ]]; then
      subject="$subject sudo"
      msg=$(eval "echo \"$(cat msg_sudo.txt)\"")
    fi
    if [[ ! -z "$sesserr" ]]; then
      if [[ ! -z "$sudoerr" ]]; then
        subject="$subject &"
        msg=$(echo "$msg" && echo "----------\n")
      fi
      subject="$subject session"
      msg=$(echo -n "$msg" && cat msg_session.txt)
    fi
    msg=$(echo "$msg" && echo "----------" && echo "Also attached is sudoers.txt, which is the official, approved sudoers configuration for TADDM.")
    subject="$subject config (${org})"
    echo -e "$msg" | mailx -s "$subject" -r "TADDM <${USER}@${HOSTNAME}>" $attachments $EMAIL 2>/dev/null
  fi
done
