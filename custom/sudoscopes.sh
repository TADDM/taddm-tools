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

echo "# sudo_invalid" > scopes/sudo_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_verified\"]=\"invalid\"]'" >> scopes/sudo_invalid.scope

echo "# sudo_lsof_invalid" > scopes/sudo_lsof_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_lsof\"]=\"invalid\"]'" >> scopes/sudo_lsof_invalid.scope

echo "# sudo_dmidecode_invalid" > scopes/sudo_dmidecode_invalid.scope
./buildscope.jy -P -q "select * from LinuxUnitaryComputerSystem where XA eval '/xml[attribute[@name=\"sudo_dmidecode\"]=\"invalid\"]'" >> scopes/sudo_dmidecode_invalid.scope

echo "# sudo_hba_invalid" > scopes/sudo_hba_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_hba\"]=\"invalid\"]' and ( virtual is-null or not virtual )" >> scopes/sudo_hba_invalid.scope

echo "# sudo_rdm_invalid" > scopes/sudo_rdm_invalid.scope
./buildscope.jy -P -q "select * from LinuxUnitaryComputerSystem where XA eval '/xml[attribute[@name=\"sudo_rdm\"]=\"invalid\"]'" >> scopes/sudo_rdm_invalid.scope
