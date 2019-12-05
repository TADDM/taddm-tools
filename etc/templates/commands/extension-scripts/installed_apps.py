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

def buildAppServer(version, vendor, product, desc, sp, path, obj_type):
  appserver = sensorhelper.newModelObject('cdm:app.AppServer')
  appserver.setKeyName('AppServer')
  appserver.setHost(computersystem)
  if obj_type:
    appserver.setObjectType(obj_type)
  if version:
    appserver.setProductVersion(version)
  if vendor:
    appserver.setVendorName(vendor)
  if product:
    appserver.setProductName(product)
  if desc:
    appserver.setDescription(desc)
  if sp:
    appserver.setServicePack(sp)
  # build bind address
  bindaddr = sensorhelper.newModelObject('cdm:net.CustomBindAddress')
  bindaddr.setPortNumber(0)
  bindaddr.setPath(path)
  # build IP for bind address
  ipaddr = sensorhelper.newModelObject('cdm:net.IpV4Address')
  ipaddr.setStringNotation(str(seed))
  bindaddr.setPrimaryIpAddress(ipaddr)
  bindaddr.setIpAddress(ipaddr)
  appserver.setPrimarySAP(bindaddr)
  appserver.setLabel(server.getFqdn() + ':' + path)
  # build process pool
  procpool = sensorhelper.newModelObject('cdm:app.ProcessPool')
  procpool.setParent(appserver)
  procpool.setName('ProcessPool')
  procpool.setCmdLine(path)
  appserver.setProcessPools(sensorhelper.getArray([procpool,], 'cdm:app.ProcessPool'))

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("Installed applications discovery extension started (written by Mat Davis - mdavis5@us.ibm.com)")

  # Java
  try:
    version = sensorhelper.executeCommand('java -version 2>&1 | head -n 1 | awk -F \'"\' \'{print $2}\'').strip()
    vendor  = sensorhelper.executeCommand('java -version 2>&1 | sed -n 3p | awk \'{print $1}\'').strip()
    product = sensorhelper.executeCommand('java -version 2>&1 | sed -n 2p | awk \'{print $1}\'').strip()
    desc    = sensorhelper.executeCommand('java -version 2>&1  | sed -n 2p | awk \'{print $1,$2,$3,$4}\'').strip()
    sp      = sensorhelper.executeCommand('java -version 2>&1 | sed -n 4p').strip()
    path    = sensorhelper.executeCommand('which java').strip()
    
    appserver = buildAppServer(version, vendor, product, desc, sp, path, 'System Java')
    result.addExtendedResult(appserver)
    
  except:
    log.info('One of the java commands failed or java is not installed on path')
    pass

  # Ant
  try:
    version = sensorhelper.executeCommand('ant -version | cut -c 24-28').strip()
    path    = sensorhelper.executeCommand('which ant').strip()
    
    appserver = buildAppServer(version, 'The Apache Group', 'Ant', None, None, path, 'Ant')
    
    result.addExtendedResult(appserver)
    
  except:
    log.info('One of the ant commands failed or ant is not installed on path')
    pass
    
  log.info("Installed applications discovery extension ended")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)