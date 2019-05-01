#!/bin/sh
 
BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom
 
# Get current timestamp
mydate=`date +"%Y%m%d%H%M%Z"`
 
export BIRT_HOME=$COLLATION_HOME/deploy-tomcat/birt-viewer
 
cd $COLLATION_HOME/deploy-tomcat/birt-viewer/WEB-INF/resources
 
# generate the reports
./genReport.sh -f HTML -o $COLLATION_HOME/custom/reports/sample1-${mydate}.html -F $COLLATION_HOME/custom/reports/sample1.properties $COLLATION_HOME/deploy-tomcat/birt-viewer/WEB-INF/report/taddm_server_affinity_byScope_withLogConn.rptdesigncompiled
 
cd $COLLATION_HOME/custom
 
# add script here to e-mail reports
