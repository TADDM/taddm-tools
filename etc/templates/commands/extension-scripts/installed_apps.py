############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# DESCRIPTION:
#
# Authors:  Mat Davis
#                       mdavis5@us.ibm.com
#
# History:
#    Version 0.1 -- 12/2019   -- Initial Version --
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
from decimal import Decimal

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

# this is for new Python v2.5.3
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

########################################################
# LogError Error Logging
########################################################
def LogError(msg):
  log.error(msg)
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  traceback.print_exc(ErrorTB)

sudo_list = None
def validateSudo(cmd=None):
  try:
    if cmd:
      global sudo_list
      if sudo_list is None:
        sudo_list = sensorhelper.executeCommand('sudo -l 2>/dev/null')
      # look for line containing (root) NOPASSWD: .*cmd.*
      regex = re.compile('\(((root)|(ALL))\) NOPASSWD: .*' + cmd + '.*', re.MULTILINE | re.DOTALL)
      if regex.search(sudo_list):
        return True
      else:
        return False
    else:
      try:
        sudo_list = sensorhelper.executeCommand('sudo -l 2>&1')
        return True
      except:
        return False
  except:
    return False

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("Installed applications discovery extension started (written by Mat Davis - mdavis5@us.ibm.com)")

  # Java
  try:
    java_version = sensorhelper.executeCommand('/opt/IBM/taddm/dist/external/jdk-Linux-x86_64/bin/java -version 2>&1 | grep \'^java version\' | awk \'{print $3}\'')
    java_path = sensorhelper.executeCommand('which /opt/IBM/taddm/dist/external/jdk-Linux-x86_64/bin/java')
    
    appserver = sensorhelper.newModelObject('cdm:app.AppServer')
    appserver.setKeyName('AppServer')
    appserver.setHost(computersystem)
    appserver.setObjectType('System Java')
    appserver.setProductVersion(java_version.replace('"', '', 2))
    # build bind address
    bindaddr = sensorhelper.newModelObject('cdm:net.CustomBindAddress')
    bindaddr.setPortNumber(0)
    bindaddr.setPath(java_path)
    # build IP for bind address
    ipaddr = sensorhelper.newModelObject('cdm:net.IpV4Address')
    ipaddr.setStringNotation(str(seed))
    bindaddr.setPrimaryIpAddress(ipaddr)
    bindaddr.setIpAddress(ipaddr)
    appserver.setPrimarySAP(bindaddr)
    #appserver.setLabel(server.getFqdn() + ':System Java')
    # build process pool
    procpool = sensorhelper.newModelObject('cdm:app.ProcessPool')
    procpool.setParent(appserver)
    procpool.setName('ProcessPool')
    procpool.setCmdLine(java_path)
    appserver.setProcessPools(sensorhelper.getArray([procpool,], 'cdm:app.ProcessPool'))
    
    result.addExtendedResult(appserver)
    
  except:
    pass
    
  log.info("Installed applications discovery extension ended")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)