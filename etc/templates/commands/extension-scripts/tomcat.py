############### Begin Standard Header - Do not add comments here ############### 
# 
# File:     %W% 
# Version:  %I% 
# Modified: %G% %U% 
# Build:    %R% %L% 
# 
# Licensed Materials - Property of IBM 
# 
# 5724-N55 
# 
# (C) COPYRIGHT IBM CORP. 2007.  All Rights Reserved. 
# 
# US Government Users Restricted Rights - Use, duplication or 
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp. 
# 
############################# End Standard Header ############################## 

########################################################
# Standard Jython/Python Library Imports
########################################################
import sys
import java

########################################################
# Additional from Java imports
########################################################
from java.lang import System

coll_home = System.getProperty("com.collation.home") 
  
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib") 
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib") 
  
jython_home = System.getProperty("jython.home") 
sys.path.append(jython_home + "/Lib") 
sys.path.append(coll_home + "/lib/sensor-tools") 
sys.prefix = jython_home + "/Lib" 
  
########################################################
# More Standard Jython/Python Library Imports
########################################################
import traceback
import re

########################################################
# Custom Libraries to import (Need to be in the path)
########################################################
import sensorhelper  

######################## 
# LogError      Error logger 
######################## 
def LogError(msg): 
  print "LogError",msg 
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info() 
  traceback.print_exc(ErrorTB) 
  
# LogDebug      Print routine for normalized messages in log
########################
def LogDebug(msg):
  '''
  Print Debug Message using debug logger (from sensorhelper)
  '''
  # assuming SCRIPT_NAME and template name are defined globally...
  # point of this is to create a consistent logging format to grep
  # the trace out of
  log.debug(msg)

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, appserver, seed, log, env) = sensorhelper.init(targets)

try:

  args = sensorhelper.splitArgs(seed.getCmdLine())
  if args is not None:
    for t in args:
      if t.find("-Dcatalina.home=") != -1:
        catalina_home = t.split("=")[1]
        log.info("Catalina Home from command line = " + catalina_home)
        version = sensorhelper.executeCommand(catalina_home + '/bin/version.sh | grep \'^Server number:\' | awk \'{print $3}\'')
        appserver.setVendorName('The Apache Group')
        appserver.setProductName('Tomcat')
        appserver.setProductVersion(version)
        break

		# if isWindows == 1:
			# homeDir = sensorhelper.executeCommand("mysql -u " + auth.getUserName() + " --password="+auth.getPassword()+" -s -e  \"SHOW VARIABLES LIKE '%basedir%'\"")
		# else:
			# homeDir = sensorhelper.executeCommand("mysql -u " + auth.getUserName() + " --password="+auth.getPassword()+" --socket=" + socketPath + " -s -e  \"SHOW VARIABLES LIKE '%basedir%'\" | grep basedir | awk '{print $NF}'")
		# appserver.setHome(homeDir.strip())
		# configFile = sensorhelper.newModelObject('cdm:app.ConfigFile')
                # configFile.setURI("config://" + seed.getPrimaryIpAddress().getStringNotation() + ":" + str(seed.getPort()) + "/MySql/databaselist")

		# if isWindows == 1:
			# res = sensorhelper.executeCommand("mysql -u " + auth.getUserName() + " --password="+auth.getPassword()+" -s -e \"show databases;\"")
		# else:
			# res = sensorhelper.executeCommand("mysql -u " + auth.getUserName() + " --password="+auth.getPassword()+" --socket=" + socketPath + " -s -e \"show databases;\"")
		# configFile.setContent(res)
		# ac = sensorhelper.newModelObject('cdm:app.AppConfig');
		# ac.setParent(appserver)
		# ac.setContent(configFile)

except: 
  #Something failed and threw an exception.  Call the error logger 
  #so that the stack trace gets logged 
  LogError("unexpected exception discovering Tomcat")

