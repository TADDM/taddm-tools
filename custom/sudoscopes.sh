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

# calculate epoch for 7 days ago
day=$((60*60*24))
now=`date +%s`
epoch=$((($now - 7*$day)*1000))

echo "# sudo_invalid" > scopes/sudo_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_verified\"]=\"invalid\"]' and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_invalid.scope

echo "# sudo_lsof_invalid" > scopes/sudo_lsof_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_lsof\"]=\"invalid\"]' and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_lsof_invalid.scope

echo "# sudo_dmidecode_invalid" > scopes/sudo_dmidecode_invalid.scope
./buildscope.jy -P -q "select * from LinuxUnitaryComputerSystem where XA eval '/xml[attribute[@name=\"sudo_dmidecode\"]=\"invalid\"]' and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_dmidecode_invalid.scope

echo "# sudo_hba_invalid" > scopes/sudo_hba_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_hba\"]=\"invalid\"]' and ( virtual is-null or not virtual ) and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_hba_invalid.scope

echo "# sudo_hba_path_invalid" > scopes/sudo_hba_path_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_hba_path\"]=\"invalid\"]' and ( virtual is-null or not virtual ) and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_hba_path_invalid.scope

echo "# sudo_rdm_invalid" > scopes/sudo_rdm_invalid.scope
./buildscope.jy -P -q "select * from LinuxUnitaryComputerSystem where XA eval '/xml[attribute[@name=\"sudo_rdm\"]=\"invalid\"]' and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_rdm_invalid.scope

echo "# sudo_emc_invalid" > scopes/sudo_emc_invalid.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_emc\"]=\"invalid\"]' and not XA eval '/xml[attribute[@name=\"decom\"]]' and lastModifiedTime > $epoch" >> scopes/sudo_emc_invalid.scope

echo "# sudo_emc_unexpected" > scopes/sudo_emc_unexpected.scope
./buildscope.jy -P -q "select * from ComputerSystem where XA eval '/xml[attribute[@name=\"sudo_emc\"]=\"unexpected\"]' and lastModifiedTime > $epoch" >> scopes/sudo_emc_unexpected.scope
