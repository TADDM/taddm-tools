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
    attachments="$attachments -a sudoers.txt"
    cat msg_session.txt | mailx -s "TADDM session errors (${org})" -r "TADDM <${USER}@${HOSTNAME}>" $attachments $EMAIL 2>/dev/null
  fi
done
