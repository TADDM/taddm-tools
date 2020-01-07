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
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  log.error(errMsg)
  log.error('TB:' + str(traceback.format_tb(ErrorTB)))

def get_class_name(model_object):
  cn = model_object.__class__.__name__
  real_class_name=cn.replace("Impl","")
  return real_class_name
  
# copied from ext_attr_helper because of CNF error while running on anchor
def get_os_type(os_handle):
  '''
  Return OS we are on --> UNIX or WINDOWS
  '''
  cs = sensorhelper.getComputerSystem(os_handle)
  class_name = get_class_name(cs)
  #LogInfo("OS Classname is:  " + str(class_name))
  if re.search("Linux",class_name,re.I):
    os_type = "Linux"
  elif re.search("Windows",class_name,re.I):
    os_type = "Windows"
  elif re.search("AIX",class_name,re.I):
    os_type = "Aix"
  elif re.search("Sun",class_name,re.I):
    os_type = "Sun"
  else:
    os_type = "UNKNOWN"
  return os_type
  
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
  appserver.setLabel(computersystem.getFqdn() + ':' + path)
  # build process pool
  procpool = sensorhelper.newModelObject('cdm:app.ProcessPool')
  procpool.setParent(appserver)
  procpool.setName('ProcessPool')
  procpool.setCmdLine(path)
  appserver.setProcessPools(sensorhelper.getArray([procpool,], 'cdm:app.ProcessPool'))
  
  return appserver

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("Installed applications discovery extension started (written by Mat Davis - mdavis5@us.ibm.com)")

  os_type = get_os_type(os_handle)
  
  # Java
  try:
    if "Windows" == os_type:
      version_out = sensorhelper.executeCommand('java -version 2>&1').strip()
      second_line = version_out.splitlines()[1].split()
      
      version = version_out.splitlines()[0].split("\"")[1]
      vendor  = version_out.splitlines()[2].split()[0]
      product = second_line[0]
      desc    = ' '.join(second_line[:4])
      #sp      = version_out.splitlines()[3]
      # System Java on Windows does not print the 4th line that has the service pack
      sp      = None
      path    = sensorhelper.executeCommand('where java').strip()
      if len(path.splitlines()) > 1:
        path = path.splitlines()[0]
    else:
      version = sensorhelper.executeCommand('java -version 2>&1 | head -n 1 | awk -F \'"\' \'{print $2}\'').strip()
      vendor  = sensorhelper.executeCommand('java -version 2>&1 | sed -n 3p | awk \'{print $1}\'').strip()
      product = sensorhelper.executeCommand('java -version 2>&1 | sed -n 2p | awk \'{print $1}\'').strip()
      desc    = sensorhelper.executeCommand('java -version 2>&1  | sed -n 2p | awk \'{print $1,$2,$3,$4}\'').strip()
      sp      = sensorhelper.executeCommand('java -version 2>&1 | sed -n 4p').strip()
      path    = sensorhelper.executeCommand('which java').strip()
    
    appserver = buildAppServer(version, vendor, product, desc, sp, path, 'System Java')
    result.addExtendedResult(appserver)
    
  except:
    #LogError('Java failed')
    log.info('One of the java commands failed or java is not installed on path')
    pass

  # Python (default)
  try:
    if "Windows" != os_type:
      version = sensorhelper.executeCommand('python --version 2>&1 | awk \'{print $2}\'').strip()
      vendor  = 'Python'
      product = 'Python'
      desc    = None
      sp      = None
      path    = sensorhelper.executeCommand('readlink -f `which python`').strip()
    
      appserver = buildAppServer(version, vendor, product, desc, sp, path, 'Python')
      result.addExtendedResult(appserver)
    
  except:
    LogError('Python failed')
    log.info('One of the python commands failed or python is not installed on path')
    pass

  # Ant
  try:
    if "Windows" != os_type:
      version = sensorhelper.executeCommand('ant -version | awk \'{print $4}\'').strip()
      path    = sensorhelper.executeCommand('which ant').strip()
      
      appserver = buildAppServer(version, 'The Apache Group', 'Ant', None, None, path, 'Ant')
      
      result.addExtendedResult(appserver)
  except:
    log.info('One of the ant commands failed or ant is not installed on path')
    pass
    
  # SAP BO client
  try:
    if "Windows" == os_type:
      path = 'C:\\Program Files (x86)\\SAP BusinessObjects'
      inventory_txt = sensorhelper.getFile(path + '\\InstallData\\inventory.txt')
      version = ' '.join(str(inventory_txt.getContent()).splitlines()[0].split()[4:8])
            
      appserver = buildAppServer(version, 'SAP', 'BusinessObjects Client', None, None, path, 'BusinessObjects Client')
      
      result.addExtendedResult(appserver)
  except:
    log.info('BO client not installed')
    pass

  # DataStage Windows client
  try:
    if "Windows" == os_type:
      path = 'C:\\IBM\\InformationServer'
      version_txt = sensorhelper.getFile(path + '\\Version.xml')
      # Version.xml file exists, continue by querying version from registory b/c it's easier than parsing XML
      version = sensorhelper.executeCommand('FOR /F "skip=2 tokens=2,*" %A IN (\'reg.exe query "HKLM\SOFTWARE\WOW6432Node\IBM\InformationServer\CurrentVersion " /v "Version"\') DO @echo %B')
      
      # take out extra line if there
      if len(version.splitlines()) > 1:
        version = version.splitlines()[0]
      
      appserver = buildAppServer(version, 'IBM', 'InformationServer Client', None, None, path, 'InformationServer Client')
      
      result.addExtendedResult(appserver)
  except:
    log.info('DataStage Windows client not installed')
    pass

  # DB2 client
  try:
    if "Windows" == os_type:
      cmd = 'powershell -Command ' \
            '"& { get-wmiobject -class win32_product | where-object {$_.Name -match \'IBM Data Server (Runtime )*Client\'} | format-list -property Name,Version,InstallLocation}"'
      # running with 10 minute timeout because WMI query of product can run long on Windows
      db2_prod = sensorhelper.executeCommandWithTimeout(cmd, 600000)
      for line in db2_prod.splitlines():
        if line.startswith('Name'):
          name = line.split(':')[1].strip()
        if line.startswith('Version'):
          version = line.split(':')[1].strip()
        if line.startswith('InstallLocation'):
          path = ':'.join(line.split(':')[1:]).strip()
          appserver = buildAppServer(version, 'IBM', 'DB2 Client', None, None, path, 'DB2 Client')
          appserver.setLabel(computersystem.getFqdn() + ':' + name) # override label
          result.addExtendedResult(appserver)
    else:
      db2ls_out = sensorhelper.executeCommand('db2ls -c')
      for line in db2ls_out.splitlines()[1:]:
        path = line.split(':')[0]
        db2ls_prod = sensorhelper.executeCommand('db2ls -q -p -c -b ' + path)
        for pline in db2ls_prod.splitlines()[1:]:
          prod = pline.split(':')[0]
          version = pline.split(':')[1]
          if prod == 'RUNTIME_CLIENT' or prod == 'CLIENT':
            appserver = buildAppServer(version, 'IBM', 'DB2 Client', None, None, path, 'DB2 Client')
            result.addExtendedResult(appserver)
  except:
    log.info('DB2 client not installed')
    pass
    
  log.info("Installed applications discovery extension ended")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)