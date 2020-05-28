#!/bin/sh
# Filename: dbmaint_wrapper.sh

# get path of script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# if not set, use default
COLLATION_HOME=${COLLATION_HOME:-/opt/IBM/taddm/dist}

BINDIR=$COLLATION_HOME/bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

while getopts "a" o; do
  case "${o}" in
    a)
	  # alternate, run every other execution
      a=true
      ;;
  esac
done

if [ ! -z "${a}"]
then
  mark_file=$SCRIPTPATH/.dbmaint-marker
  # only run every other execution
  if [ -e $mark_file ]; then
	rm -f $mark_file
  else
	touch $mark_file
	exit 0
  fi
fi

echo "`date` dbmaint_wrapper.sh starting"

if [ -e $SCRIPTPATH/dbmaint.properties ]; then
    TADENV=`awk -F= '/^TADENV/ {print $2}' $SCRIPTPATH/dbmaint.properties`
    EMAIL=`awk -F= '/^EMAILADDRESS/ {print $2}' $SCRIPTPATH/dbmaint.properties`
    PURGE_CH=`awk -F= '/^PURGE_CH/ {print $2}' $SCRIPTPATH/dbmaint.properties`
    PURGE_FLAGS=`awk -F= '/^PURGE_FLAGS/ {print $2}' $SCRIPTPATH/dbmaint.properties`
else
    TADENV="Unknown"
    echo "Properties file $SCRIPTPATH/dbmaint.properties not found, using defaults" 
fi

# remove old dbmaint.out if exists
rm -f $SCRIPTPATH/dbmaint.out 2>/dev/null

$SCRIPTPATH/stop_taddm.sh
 
# Give the servers a little more time to stop
sleep 30

# run offline backup hook (optional) if offline backup is desired
# then place this script function in dbmaint_olbkp.sh
if [ -x $SCRIPTPATH/dbmaint_offbkp.sh ]; then
    echo "`date` Executing off-line backup script"
    $SCRIPTPATH/dbmaint_offbkp.sh >> $SCRIPTPATH/dbmaint.out 2>&1
    echo "`date` Off-line backup script completed"
else
    echo "dbmaint_offbkp.sh either does not exist or is not executable. Skipping off-line backup" >> $SCRIPTPATH/dbmaint.out 2>&1
fi
 
# Purge change history
if [ "$PURGE_CH" == "true" ] && [ -x $SCRIPTPATH/purge_change_history.jy ]; then
    echo "`date` Purging change history"
    $SCRIPTPATH/purge_change_history.jy $PURGE_FLAGS >> $SCRIPTPATH/dbmaint.out 2>&1
    echo "`date` Change history purge completed"
else
    echo "Skipping purge_change_history.jy"
fi

# generate stats commands, technically this only needs run after an upgrade but it takes less than
# 30 seconds to run so it's inexpensive to run before each maintenance cycle
echo "`date` Generating runstats commands" | tee -a $SCRIPTPATH/dbmaint.out 2>&1
cd $COLLATION_HOME/bin
./gen_db_stats.jy >TADDM_table_stats.sql 2>/dev/null
cd - >/dev/null
 
# Run DB tuning/maintenance
echo "`date` Running DB maintenance" | tee -a $SCRIPTPATH/dbmaint.out 2>&1
$SCRIPTPATH/dbmaint.jy --rebuild >> $SCRIPTPATH/dbmaint.out 2>&1
echo "`date` Running DB complete" | tee -a $SCRIPTPATH/dbmaint.out 2>&1
 
# Run additional runstats after DB tuning
# ****** This does NOT need run anymore if APAR IV47906 is installed, as it should be
#type=`awk -F= '/^com.collation.db.type/ {print $2}' $COLLATION_HOME/etc/collation.properties`
#if [[ "$type" = "db2" ]]
#then
#  $COLLATION/bin/db2updatestats.sh >> $SCRIPTPATH/dbmaint.out 2>&1
#fi
 
# pause for just a bit, to be safe (this is probably not necessary but shouldn't hurt)
sleep 20

echo "`date` Starting TADDM"
$SCRIPTPATH/start_taddm.sh

# send e-mail notification that maintenance was complete
if [ "$EMAIL" != "" ]; then
    echo "`date` Sending email"
    echo -e "Output of database maintenance job attached.\n\n-TADDM Discovery" | mailx -s "Database Maintenance Complete in environment $TADENV" -r "TADDM <${USER}@${HOSTNAME}>" -a $SCRIPTPATH/dbmaint.out $EMAIL 2>/dev/null
fi
