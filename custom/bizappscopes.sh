#!/bin/sh

#set -x

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
USER=administrator
PASSWORD=collation

# make scopes directory if it doesn't exist
mkdir scopes 2>/dev/null

rm scopes/BizApp_* 2>/dev/null # remove old scopes

echo "Building scope files from existing business applications"
IFS=$'\n'; for bizapp in `$COLLATION_HOME/sdk/bin/api.sh -u $USER -p $PASSWORD find -d 1 "select name from Application where exists ( groups.groupName == 'Computer Systems' )" |awk -F '[<>]' '/name/ {print $3}'`
do
	echo "Building scope for $bizapp"
	scopeName=`echo BizApp_${bizapp} | tr ' ' '_'` # replace spaces with underscore
	echo "#${scopeName}" > scopes/${scopeName}.scope
	./buildscope.jy -P -q "select ComputerSystem.name, ComputerSystem.fqdn, ComputerSystem.ipInterfaces from ComputerSystem, FunctionalGroup where FunctionalGroup.app.name == '${bizapp}' and exists ( FunctionalGroup.members.guid == ComputerSystem.guid ) and FunctionalGroup.groupName == 'Computer Systems' and ComputerSystem.manufacturer != 'Cisco' and not ( ComputerSystem.OSRunning instanceof VmwareESX )" >> scopes/${scopeName}.scope
done

echo "Loading scope files"
# load scopes into TADDM
for fileName in `(cd scopes; ls -1 BizApp_*)`
do
    echo "Processing $fileName"
    # remove comment character and trim leading and trailing space from scope name
    scopeName=`head -1 scopes/$fileName | tr -d '#' | sed -e 's/^ *//' -e 's/ *$//'`
    echo "Scope name is $scopeName"
    cd ../bin
    loadscope.jy -u $USER -p $PASSWORD -s "$scopeName" load "$COLLATION_HOME/custom/scopes/$fileName"
    cd $COLLATION_HOME/custom
done

