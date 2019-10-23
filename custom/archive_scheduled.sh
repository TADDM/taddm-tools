#!/bin/sh

#set -x

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
ARCHIVEPROPS=$COLLATION_HOME/custom/archive.properties
AGE=182
USER=administrator
PASSWORD=collation
DELETE=false
SKIPZOS=false
SKIPFAILED=1

# if properties file exists use values
if [ -e $ARCHIVEPROPS ]; then
    AGE=`awk -F= '/archive.age/ {print $2}' $ARCHIVEPROPS`
    EMAIL=`awk -F= '/archive.email/ {print $2}' $ARCHIVEPROPS`
    SKIPZOS=`awk -F= '/archive.skipzos/ {print $2}' $ARCHIVEPROPS`
    SKIPFAILED=`awk -F= '/archive.skipfailed/ {print $2}' $ARCHIVEPROPS`
else
    echo "Properties file $ARCHIVEPROPS not found, using defaults"
fi

# if SKIPFAILED not present then set to 0
if [ -z "$SKIPFAILED" ]; then
    SKIPFAILED=0
elif [ "$SKIPFAILED" -ne "0" ]; then
    SKIPFAILED=`expr $SKIPFAILED - 1`
fi

# subtract 7 days from age
AGE=`expr $AGE - 7`

# set e-mail address if found in properties
if [ "$EMAIL" != "" ]; then
    emailAddress=$EMAIL
fi 

mydate=`date +%Y-%m-%d_%H%M`

echo "*************************************************************************" | tee -a archive_${mydate}.txt
echo "The following components are scheduled for deletion in one week if they are not successfully discovered" | tee -a archive_${mydate}.txt
echo "*************************************************************************" | tee -a archive_${mydate}.txt
echo | tee -a archive_${mydate}.txt
cd $COLLATION_HOME/custom
./taddm_archive.jy -u $USER -p $PASSWORD -A $AGE `[ "$SKIPZOS" == "true" ] && echo --skip_zos` `[ $SKIPFAILED -gt 0 ] && echo --skip_failed=$SKIPFAILED` -C ComputerSystem | tee -a archive_${mydate}.txt
echo | tee -a archive_${mydate}.txt
./taddm_archive.jy -u $USER -p $PASSWORD -A $AGE `[ "$SKIPZOS" == "true" ] && echo --skip_zos` `[ $SKIPFAILED -gt 0 ] && echo --skip_failed=$SKIPFAILED` -C AppServer | tee -a archive_${mydate}.txt

if [ -n "$emailAddress" ]
then
    echo -e "Check attached output for components scheduled for deletion.\n\n-TADDM Discovery" | mailx -s 'Scheduled for deletion' -r "TADDM <${USER}@${HOSTNAME}>" -a archive_${mydate}.txt $emailAddress 2>/dev/null
fi

rm archive_${mydate}.txt
