#!/bin/sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation

# requires TIMESTAMP variable to be set to DiscoveryRun runName (--name in api.sh command)
wait4discovery () {
    status=`api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$TIMESTAMP'" | awk -F'[<>]' '/status/ {print $3}'`
    while [ "$status" != "2" ]
    do
        sleeptime=`date`
        echo "sleeping 5 minutes at $sleeptime then checking for completion"
        sleep 300
        status=`api.sh -u $USER -p $PASSWORD find -d 1 "SELECT status FROM DiscoveryRun WHERE runName == '$TIMESTAMP'" | awk -F'[<>]' '/status/ {print $3}'`
    done
}
###############################################################################
# SystemP HMC discovery
###############################################################################

# load scope file for SystemP HMCs 
#fileName=systemp_hmc.scope
#echo "Processing $fileName"
# remove comment character and trim leading and trailing space from scope name
#scopeName=`head -1 scopes/$fileName | tr -d '#' | sed -e 's/^ *//' -e 's/ *$//'`
#echo "Scope name is $scopeName"
#cd ../bin
#loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/$fileName"
#cd $COLLATION_HOME/custom

#echo "Starting SystemP HMC discovery"
#TIMESTAMP=`date +"%Y%m%d%H%M%S"`
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "IGA Standard V2" "SystemP HMC" 

#sleep 30
#wait4discovery

#
# check logs for errors
#
#echo "Checking SystemP HMC discovery for errors"
#checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP

###############################################################################
# SystemP LPAR discovery
###############################################################################

# now build out the SystemP LPAR scopeset
#echo "# SystemP LPAR" > scopes/systemp_lpar.scope
#buildscope.jy -u $USER -p $PASSWORD -q "select ComputerSystem.fqdn, ComputerSystem.name, ComputerSystem.ipInterfaces from ComputerSystem, SystemPComputerSystem where ComputerSystem.hostSystem.guid == SystemPComputerSystem.guid AND ComputerSystem.virtualMachineState != '3' AND ComputerSystem.type != 'VIOS' AND ComputerSystem.type != 'HMC'" >> scopes/systemp_lpar.scope
# TESTING WITH LIMIT, DELETE FOR PRODUCTION
#buildscope.jy -u $USER -p $PASSWORD -l 10 -q "select ComputerSystem.fqdn, ComputerSystem.name, ComputerSystem.ipInterfaces from ComputerSystem, SystemPComputerSystem where ComputerSystem.hostSystem.guid == SystemPComputerSystem.guid AND ComputerSystem.virtualMachineState != '3' AND ComputerSystem.type != 'VIOS' AND ComputerSystem.type != 'HMC'" >> scopes/systemp_lpar.scope

# load SystemP LPAR scopeset
#cd ../bin
#loadscope.jy -u $USER -p $PASSWORD -s "SystemP LPAR" load "$COLLATION_HOME/custom/scopes/systemp_lpar.scope"
#cd $COLLATION_HOME/custom

#echo "Starting SystemP LPAR discovery"
#TIMESTAMP=`date +"%Y%m%d%H%M%S"`
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "IGA Standard V2" "SystemP LPAR"

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
api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "IGA Standard V2" $allScopes

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

# now build out the vCenter Windows guests scopeset
echo "# VMware Windows guests" > scopes/vmware_guests_win.scope
#buildscope.jy -u $USER -p $PASSWORD -q "SELECT WindowsComputerSystem.fqdn, WindowsComputerSystem.name, WindowsComputerSystem.ipInterfaces FROM WindowsComputerSystem, VmwareUnitaryWindowsComputerSystem WHERE WindowsComputerSystem.hostSystem.guid == VmwareUnitaryWindowsComputerSystem.guid AND WindowsComputerSystem.virtualMachineState != '3'" >> scopes/vmware_guests.scope
# TESTING WITH LIMIT, DELETE FOR PRODUCTION
buildscope.jy -u $USER -p $PASSWORD -l 10 -q "SELECT WindowsComputerSystem.fqdn, WindowsComputerSystem.name, WindowsComputerSystem.ipInterfaces FROM WindowsComputerSystem, VmwareUnitaryWindowsComputerSystem WHERE WindowsComputerSystem.hostSystem.guid == VmwareUnitaryWindowsComputerSystem.guid AND WindowsComputerSystem.virtualMachineState != '3'" >> scopes/vmware_guests.scope

# load VMware Windows guests scopeset
cd ../bin
loadscope.jy -u $USER -p $PASSWORD -s "VMware Windows guests" load "$COLLATION_HOME/custom/scopes/vmware_guests_win.scope"
cd $COLLATION_HOME/custom

#echo "Starting VMware guests discovery"
#TIMESTAMP=`date +"%Y%m%d%H%M%S"`
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "IGA Standard V2" "VMware guests"

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
#api.sh -u $USER -p $PASSWORD discover start --name $TIMESTAMP --profile "IGA Standard V2" "zLinux guests"

#sleep 30
#wait4discovery

#
# check logs for errors
#
#echo "Checking zLinux guest discovery log files for errors"
#checklogs.sh -u $USER -p $PASSWORD -n $TIMESTAMP