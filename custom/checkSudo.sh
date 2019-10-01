#!/bin/sh

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

EMAIL=

echo "# sudo_invalid" > scopes/sudo_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_verified\"]=\"invalid\"]'" >> scopes/sudo_invalid.scope
echo "# sudo_lsof_invalid" > scopes/sudo_lsof_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_lsof\"]=\"invalid\"]'" >> scopes/sudo_lsof_invalid.scope
echo "# sudo_hba_invalid" > scopes/sudo_hba_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_hba\"]=\"invalid\"]'" >> scopes/sudo_hba_invalid.scope

attachments=""
if [ `wc -l scopes/sudo_invalid.scope|awk '{print $1}'` -gt 1 ]; then
  attachments="-a scopes/sudo_invalid.scope"
fi
if [ `wc -l scopes/sudo_lsof_invalid.scope|awk '{print $1}'` -gt 1 ]; then
  attachments="$attachments -a scopes/sudo_lsof_invalid.scope"
fi
if [ `wc -l scopes/sudo_hba_invalid.scope|awk '{print $1}'` -gt 1 ]; then
  attachments="$attachments -a scopes/sudo_hba_invalid.scope"
fi

if [[ ! -z "$attachments" ]]; then
  mailx -s "sudo errors" -r "TADDM PROD dis02p <cmdbusr1@v2ibmtdmdis02p>" $attachments $EMAIL 2>/dev/null << EOL
Attached are scope files containing hosts where sudo is either not configured or not configured properly. Below are the required sudoers configurations for Linux and Solaris:

Defaults !requiretty
(root) NOPASSWD: /usr/sbin/dmidecode, /usr/sbin/lsof, /usr/local/bin/lsof, /opt/VRTSvcs/bin/hastatus,
    /opt/VRTSvcs/bin/haclus, /opt/VRTSvcs/bin/hasys, /opt/VRTSvcs/bin/hares, /opt/VRTSvcs/bin/hagrp,
    /opt/VRTSvcs/bin/hatype, /opt/VRTSvcs/bin/hauser, /var/TADDM/home/tadmadm/collectionengine-linux-x86*,
    /var/TADDM/home/tadmadm/collectionengine-solaris-sparc, /usr/sbin/fcinfo, /usr/bin/sg_inq
    
EOL
else
  mailx -s "sudo errors" -r "TADDM PROD dis02p <cmdbusr1@v2ibmtdmdis02p>" $EMAIL 2>/dev/null << EOL
No invalid sudo configurations found. You might want to check the script execution to ensure that this is truly the case.

EOL
fi
