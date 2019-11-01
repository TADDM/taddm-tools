#!/bin/sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

echo "*** Querying ViPR for hosts"
echo "# ViPR_Linux_hosts" > scopes/ViPR_Linux_hosts.scope
./viprLinuxHosts.sh >> scopes/ViPR_Linux_hosts.scope

echo "# ViPR_Solaris_hosts" > scopes/ViPR_Solaris_hosts.scope
./viprSolarisHosts.sh >> scopes/ViPR_Solaris_hosts.scope

echo "# ViPR_Windows_hosts" > scopes/ViPR_Windows_hosts.scope
./viprWindowsHosts.sh >> scopes/ViPR_Windows_hosts.scope

echo "# ViPR_HyperV" > scopes/ViPR_HyperV.scope
./viprHyperV.sh >> scopes/ViPR_HyperV.scope

echo "# ViPR_VMs" > scopes/ViPR_VMs.scope
./viprVMs.sh >> scopes/ViPR_VMs.scope

echo "*** ViPR query for hosts complete"

# create a combined scope for restrictions (do not include VMs)
echo "# ViPR_hosts" > scopes/ViPR_hosts.scope
tail -n +2 scopes/ViPR_Linux_hosts.scope >> scopes/ViPR_hosts.scope
tail -n +2 scopes/ViPR_Solaris_hosts.scope >> scopes/ViPR_hosts.scope
tail -n +2 scopes/ViPR_Windows_hosts.scope >> scopes/ViPR_hosts.scope
tail -n +2 scopes/ViPR_HyperV.scope >> scopes/ViPR_hosts.scope

cd $COLLATION_HOME/bin

echo "*** Loading scopes"
# check if files are populated before loading
if [ `cat $COLLATION_HOME/custom/scopes/ViPR_Linux_hosts.scope | wc -l` -gt 1 ]
then
   ./loadscope.jy -u administrator -p collation -s ViPR_Linux_hosts load $COLLATION_HOME/custom/scopes/ViPR_Linux_hosts.scope 
fi
if [ `cat $COLLATION_HOME/custom/scopes/ViPR_Solaris_hosts.scope | wc -l` -gt 1 ]
then
   ./loadscope.jy -u administrator -p collation -s ViPR_Solaris_hosts load $COLLATION_HOME/custom/scopes/ViPR_Solaris_hosts.scope
fi
if [ `cat $COLLATION_HOME/custom/scopes/ViPR_Windows_hosts.scope | wc -l` -gt 1 ]
then
   ./loadscope.jy -u administrator -p collation -s ViPR_Windows_hosts load $COLLATION_HOME/custom/scopes/ViPR_Windows_hosts.scope
fi
if [ `cat $COLLATION_HOME/custom/scopes/ViPR_HyperV.scope | wc -l` -gt 1 ]
then
   ./loadscope.jy -u administrator -p collation -s ViPR_HyperV load $COLLATION_HOME/custom/scopes/ViPR_HyperV.scope
fi
if [ `cat $COLLATION_HOME/custom/scopes/ViPR_VMs.scope | wc -l` -gt 1 ]
then
   ./loadscope.jy -u administrator -p collation -s ViPR_VMs load $COLLATION_HOME/custom/scopes/ViPR_VMs.scope
fi
if [ `cat $COLLATION_HOME/custom/scopes/ViPR_hosts.scope | wc -l` -gt 1 ]
then
   ./loadscope.jy -u administrator -p collation -s ViPR_hosts load $COLLATION_HOME/custom/scopes/ViPR_hosts.scope
fi
echo "*** Scope loading complete"

cd $COLLATION_HOME/custom
# run jobs to check vipr hosts that will send out email with hosts to fix
./checkViprVMs.sh
./checkViprLinux.sh
./checkViprWindows.sh
