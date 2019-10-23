#!/bin/sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# get current umask
umask=`umask`
# change umask so that scripts are world readable
umask 022

# find scriptHelper
if [ -f $BINDIR/scriptHelper.sh ]
then
  SCRIPTHELPER=$BINDIR/scriptHelper.sh
else
  # location moved in 7.3
  SCRIPTHELPER=$COLLATION_HOME/osgi/scripts/Unix/scriptHelper.sh
fi

# add read for scriptHelper in case it's not there
chmod o+r $SCRIPTHELPER

# customize which script packages you want to generate here
rm -f taddmasd_AIX.tar 2>/dev/null
$BINDIR/makeASDScriptPackage.sh . AIX tar
rm -f taddmasd_SunOS.tar 2>/dev/null
../bin/makeASDScriptPackage.sh . SunOS tar
rm -f taddmasd_Linux.tar 2>/dev/null
$BINDIR/makeASDScriptPackage.sh . Linux tar

umask $umask
chmod --reference=$COMMONPART $SCRIPTHELPER
