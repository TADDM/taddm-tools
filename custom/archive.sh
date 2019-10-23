#!/bin/sh

#  HISTORY
#     2016/01/07 : mdavis5@us.ibm.com : Remove req for script to be in custom dir

#set -x

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
 
# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}
 
BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
 
# get properties file from base name of script by default
SCRIPT=`basename $0`
ARCHIVEPROPS=$SCRIPTPATH/`echo $SCRIPT | awk -F. '{print $1}'`.properties
# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
AGE=182
USER=administrator
PASSWORD=collation
LIMIT=1000000
# err on side of caution
DELETE=false
ARCHIVEDELETEAFTER=60
SKIPZOS=false
SKIPFAILED=2

# if properties file exists use values
if [ -e $ARCHIVEPROPS ]; then
    AGE=`awk -F= '/^archive.age/ {print $2}' $ARCHIVEPROPS`
    LIMIT=`awk -F= '/^archive.limit/ {print $2}' $ARCHIVEPROPS`
    DELETE=`awk -F= '/^archive.delete/ {print $2}' $ARCHIVEPROPS`
    EMAIL=`awk -F= '/^archive.email/ {print $2}' $ARCHIVEPROPS`
    ARCHIVEDELETEAFTER=`awk -F= '/^archive.cleanup/ {print $2}' $ARCHIVEPROPS`
    SKIPZOS=`awk -F= '/^archive.skipzos/ {print $2}' $ARCHIVEPROPS`
    SKIPFAILED=`awk -F= '/^archive.skipfailed/ {print $2}' $ARCHIVEPROPS`
else
    echo "Properties file $ARCHIVEPROPS not found, using defaults"
fi

# if SKIPFAILED not present then set to 0
if [ -z "$SKIPFAILED" ]; then
    SKIPFAILED=0
fi

# set e-mail address if found in properties
if [ "$EMAIL" != "" ]; then
    emailAddress=$EMAIL
fi 

##################################################################
#### main - probably no reason to make changes below this point
ARCHIVEDIR=$COLLATION_HOME/custom/archive
mkdir -p $ARCHIVEDIR 2> /dev/null

mydate=`date +%Y-%m-%d_%H%M`

# create directory for archive if it doesn't yet exist, ignore errors
mkdir -p $ARCHIVEDIR/$mydate 2> /dev/null

# classes that require superior check
sups=(LogicalContent Fqdn IpAddress BindAddress WebSphereNamedEndpoint ServiceAccessPoint SoftwareResource WebSphereJ2EEResourceProperty)

for i in `cat $SCRIPTPATH/classes.txt | tr ' ' '_' | grep -v '^#'`
do
    echo `date` Processing $i | tee -a $SCRIPTPATH/archive_${mydate}.out
    cd $COLLATION_HOME/custom

    # run delete / don't archive b/c not necessary, should be doing database backups instead
    if [ "$i" == "Vlan" ]
    then
        # Using -c with Vlan so subclasses do not get archived
        ./taddm_archive.jy -u $USER -p $PASSWORD -q -A $AGE `[ "$DELETE" == "true" ] && echo -D` `[ "$SKIPZOS" == "true" ] && echo --skip_zos` -C $i -L $LIMIT -c -t 5 > $ARCHIVEDIR/$mydate/${i}.txt 2>&1
    elif [ "$i" == "L2Interface" ] 
    then
        # Age is specifically set to zero that it will clean up all orphans
        ./taddm_archive.jy -u $USER -p $PASSWORD -q -A 0 `[ "$DELETE" == "true" ] && echo -D` `[ "$SKIPZOS" == "true" ] && echo --skip_zos` -C $i -L $LIMIT --l2orphans -t 5 > $ARCHIVEDIR/$mydate/${i}.txt 2>&1
    elif [[ " ${sups[@]} " =~ " ${i} " ]]
    then
        # checking superiors before deleting these
        ./taddm_archive.jy -u $USER -p $PASSWORD -q -A $AGE `[ "$DELETE" == "true" ] && echo -D` `[ "$SKIPZOS" == "true" ] && echo --skip_zos` `[ $SKIPFAILED -gt 0 ] && echo --skip_failed=$SKIPFAILED` -C $i -L $LIMIT --chk_sups -t 10 > $ARCHIVEDIR/$mydate/${i}.txt 2>&1
    else
        ./taddm_archive.jy -u $USER -p $PASSWORD -q -A $AGE `[ "$DELETE" == "true" ] && echo -D` `[ "$SKIPZOS" == "true" ] && echo --skip_zos` `[ $SKIPFAILED -gt 0 ] && echo --skip_failed=$SKIPFAILED` -C $i -L $LIMIT -t 10 > $ARCHIVEDIR/$mydate/${i}.txt 2>&1
    fi
    
    if [ $? != "0" ]
    then
        echo "  *** Error occurred while running archive, please investigate ***"
    fi

    awk '/^Aged / {print " Found "$3}' $ARCHIVEDIR/$mydate/${i}.txt | tee -a $SCRIPTPATH/archive_${mydate}.out
    skipped=`grep -c "Skipping for failed discovery" $ARCHIVEDIR/$mydate/${i}.txt`
    if [ $skipped -gt 0 ]; then
        echo " Skipped $skipped" | tee -a $SCRIPTPATH/archive_${mydate}.out
    fi
 
    cd - >/dev/null
done

# clean up the archive dir
if [ $ARCHIVEDELETEAFTER -ne 0 ]
then
    cd $ARCHIVEDIR
    find * -depth -type d -mtime +$ARCHIVEDELETEAFTER -exec rm -rf {} \;
    cd - >/dev/null
fi

if [ -n "$emailAddress" ]
then
    echo -e "Output of archive job attached.\n\n-TADDM Discovery" | mailx -s 'Archive Complete' -r "TADDM <${USER}@${HOSTNAME}>" -a $SCRIPTPATH/archive_${mydate}.out $emailAddress 2>/dev/null
fi

rm $SCRIPTPATH/archive_${mydate}.out