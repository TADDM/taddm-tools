#!/bin/sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation
PROFILE="Level 2 Discovery"

# requires TIMESTAMP variable to be set to DiscoveryRun runName (--name in api.sh command)
wait4discovery () {
    status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$TIMESTAMP'" | awk -F'[<>]' '/status/ {print $3}'`
    while [ "$status" != "2" ]
    do
        sleeptime=`date`
        echo "sleeping 5 minutes at $sleeptime then checking for completion"
        sleep 300
        status=`$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$TIMESTAMP'" | awk -F'[<>]' '/status/ {print $3}'`
    done
}
###############################################################################
# SystemP HMC discovery
###############################################################################

# load scope file for system p discovery
for fileName in `cd scopes;ls systemp_hmc_*.scope`
do
    echo "Processing $fileName"
    # remove comment character, trim leading and trailing space, and replace blanks from scope name
    scopeName=`head -1 scopes/$fileName | tr -d '#' | sed -e 's/^ *//' -e 's/ *$//' | tr ' ' '_'`
    echo "Scope name is $scopeName"
    allScopes="$scopeName $allScopes"
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/$fileName"
    cd $COLLATION_HOME/custom
done

echo "Starting System P discovery for $allScopes"
TIMESTAMP=`date +"%Y%m%d%H%M%S"`
$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "$PROFILE" $allScopes

if [ "$?" = "0" ]; then
    sleep 30
    wait4discovery

    #
    # check logs for errors
    #
    echo "Checking SystemP HMC discovery log files for errors"
    checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP
else
    echo "Discovery failed to start with error code $?" 1>&2
    exit $?
fi

# clear scopes
allScopes=

###############################################################################
# SystemP LPAR scope building
###############################################################################

# build out the SystemP LPAR scopeset
for fileName in `cd scopes;ls systemp_hmc_*.scope`
do
    geo=`echo $fileName | awk -F_ '{print $NF}' | awk -F. '{print $1}'`
    scopeName="SystemP LPARs $geo"
    echo "Building scope for $scopeName"
    echo "# $scopeName" > scopes/systemp_lpar_${geo}.scope
    query="select ComputerSystem.contextIp, ComputerSystem.fqdn, ComputerSystem.name, ComputerSystem.ipInterfaces from ComputerSystem, SystemPComputerSystem where ComputerSystem.hostSystem.guid == SystemPComputerSystem.guid AND ComputerSystem.virtualMachineState != '3' AND ComputerSystem.type != 'VIOS' AND ComputerSystem.type != 'HMC' AND SystemPComputerSystem.contextIp IN ( "
    firstrow=1
    for hmc in `grep -v '#' scopes/systemp_hmc_${geo}.scope | awk -F, '{print $1}'`
    do
        if [ "$firstrow" = "1" ]; then
            query="$query '$hmc'"
            firstrow=0
        else
            query="${query}, '$hmc'"
        fi
    done
    query="$query )"
    buildscope.jy -u $USER -p $PASSWORD -q "$query" >> scopes/systemp_lpar_${geo}.scope
    # TESTING WITH LIMIT, DELETE FOR PRODUCTION
    #buildscope.jy -u $USER -p $PASSWORD -l 10 -q "$query" >> scopes/systemp_lpar_${geo}.scope

    # load SystemP LPAR scopeset
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/systemp_lpar_${geo}.scope"
    cd $COLLATION_HOME/custom
done

#echo "Starting SystemP LPAR discovery"
#TIMESTAMP=`date +"%Y%m%d%H%M%S"`
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "$PROFILE" "SystemP LPAR"

#sleep 30
#wait4discovery

#
# check logs for errors
#
#echo "Checking SystemP LPAR discovery for errors"
#checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP

###############################################################################
# vCenter discovery
###############################################################################

# load scope file for vcenter discovery
for fileName in `cd scopes;ls vcenter_*.scope`
do
    echo "Processing $fileName"
    # remove comment character, trim leading and trailing space, and replace blanks from scope name
    scopeName=`head -1 scopes/$fileName | tr -d '#' | sed -e 's/^ *//' -e 's/ *$//' | tr ' ' '_'`
    echo "Scope name is $scopeName"
    allScopes="$scopeName $allScopes"
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/$fileName"
    cd $COLLATION_HOME/custom
done

echo "Starting vCenter discovery for $allScopes"
TIMESTAMP=`date +"%Y%m%d%H%M%S"`
$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "$PROFILE" $allScopes

if [ "$?" = "0" ]; then
    sleep 30
    wait4discovery

    #
    # check logs for errors
    #
    echo "Checking vCenter discovery log files for errors"
    checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP
else
    echo "Discovery failed to start with error code $?" 1>&2
    exit $?
fi

# clear scopes
allScopes=

###############################################################################
# vCenter Windows guest scope building
###############################################################################

# build out the vCenter Windows guests scopeset
for fileName in `cd scopes;ls vcenter_*.scope`
do
    geo=`echo $fileName | awk -F_ '{print $NF}' | awk -F. '{print $1}'`
    scopeName="VMware Windows guests $geo"
    echo "Building scope for $scopeName"
    echo "# $scopeName" > scopes/vmware_guests_win_${geo}.scope
    query="SELECT WindowsComputerSystem.contextIp, WindowsComputerSystem.fqdn, WindowsComputerSystem.name, WindowsComputerSystem.ipInterfaces FROM WindowsComputerSystem, VmwareUnitaryComputerSystem WHERE WindowsComputerSystem.hostSystem.guid == VmwareUnitaryComputerSystem.guid AND WindowsComputerSystem.virtualMachineState != '3' AND VmwareUnitaryComputerSystem.contextIp IN ( "
    firstrow=1
    for vcenter in `grep -v '#' scopes/vcenter_${geo}.scope | awk -F, '{print $1}'`
    do
        if [ "$firstrow" = "1" ]; then
            query="$query '$vcenter'"
            firstrow=0
        else
            query="${query}, '$vcenter'"
        fi
    done
    query="$query )"
    buildscope.jy -u $USER -p $PASSWORD -q "$query" >> scopes/vmware_guests_win_${geo}.scope
    # TESTING WITH LIMIT, DELETE FOR PRODUCTION
    #buildscope.jy -u $USER -p $PASSWORD -l 10 -q "$query" >> scopes/vmware_guests_win_${geo}.scope

    # load VMware Windows guests scopeset
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/vmware_guests_win_${geo}.scope"
    cd $COLLATION_HOME/custom
done

# build out the vCenter Linux guests scopeset
for fileName in `cd scopes;ls vcenter_*.scope`
do
    geo=`echo $fileName | awk -F_ '{print $NF}' | awk -F. '{print $1}'`
    scopeName="VMware Linux guests $geo"
    echo "Building scope for $scopeName"
    echo "# $scopeName" > scopes/vmware_guests_linux_${geo}.scope
    query="SELECT LinuxUnitaryComputerSystem.contextIp, LinuxUnitaryComputerSystem.fqdn, LinuxUnitaryComputerSystem.name, LinuxUnitaryComputerSystem.ipInterfaces FROM LinuxUnitaryComputerSystem, VmwareUnitaryComputerSystem WHERE LinuxUnitaryComputerSystem.hostSystem.guid == VmwareUnitaryComputerSystem.guid AND LinuxUnitaryComputerSystem.virtualMachineState != '3' AND VmwareUnitaryComputerSystem.contextIp IN ( "
    firstrow=1
    for vcenter in `grep -v '#' scopes/vcenter_${geo}.scope | awk -F, '{print $1}'`
    do
        if [ "$firstrow" = "1" ]; then
            query="$query '$vcenter'"
            firstrow=0
        else
            query="${query}, '$vcenter'"
        fi
    done
    query="$query )"
    buildscope.jy -u $USER -p $PASSWORD -q "$query" >> scopes/vmware_guests_linux_${geo}.scope
    # TESTING WITH LIMIT, DELETE FOR PRODUCTION
    #buildscope.jy -u $USER -p $PASSWORD -l 10 -q "$query" >> scopes/vmware_guests_linux_${geo}.scope

    # load VMware Linux guests scopeset
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/vmware_guests_linux_${geo}.scope"
    cd $COLLATION_HOME/custom
done

#echo "Starting VMware guests discovery"
#TIMESTAMP=`date +"%Y%m%d%H%M%S"`
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "$PROFILE" "VMware guests"

#sleep 30
#wait4discovery

#
# check logs for errors
#
#echo "Checking vCenter guest discovery log files for errors"
#checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP

###############################################################################
# zLinux guest discovery
###############################################################################

# build out the zLinux guest scopeset
#echo "# zLinux guests" > scopes/zlinux_guests.scope
#buildscope.jy -u $USER -p $PASSWORD -q "SELECT ComputerSystem.fqdn, ComputerSystem.name, ComputerSystem.ipInterfaces FROM ComputerSystem, ZVMGuest WHERE ComputerSystem.hostSystem.guid == ZVMGuest.guid" >> scopes/zlinux_guests.scope
# TESTING WITH LIMIT, DELETE FOR PRODUCTION
#buildscope.jy -u $USER -p $PASSWORD -l 10 -q "SELECT ComputerSystem.fqdn, ComputerSystem.name, ComputerSystem.ipInterfaces FROM ComputerSystem, ZVMGuest WHERE ComputerSystem.hostSystem.guid == ZVMGuest.guid" >> scopes/zlinux_guests.scope

# load zLinux guests scopeset
#cd ../bin
#loadscope.jy -u $USER -p $PASSWORD -s "zLinux guests" load "$COLLATION_HOME/custom/scopes/zlinux_guests.scope"
#cd $COLLATION_HOME/custom

#echo "Starting zLinux guests discovery"
#TIMESTAMP=`date +"%Y%m%d%H%M%S"`
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "$PROFILE" "zLinux guests"

#sleep 30
#wait4discovery

#
# check logs for errors
#
#echo "Checking zLinux guest discovery log files for errors"
#checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP