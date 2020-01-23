
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
#    Version 0.5 -- 07/2019   -- Initial Version --
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
from com.collation.platform.os.storage.util import WorldWideNameUtils
from com.collation.platform.model.util.openid import OpenId

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

# this is for default (old) Python v2.1
#System.setProperty("jython.home",coll_home + "/external/jython-2.1")
#System.setProperty("python.home",coll_home + "/external/jython-2.1")

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
# Some default GLOBAL Values (Typically these should be in ALL CAPS)
# Jython does not have booleans
########################################################
True = 1
False = 0

########################################################
# LogError Error Logging
########################################################
def LogError(msg):
  log.error(msg)
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  traceback.print_exc(ErrorTB)

class CommandNotFoundError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
try:
  (os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

  log.info("Solaris Fibre Channel discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

  # build skinny computersystem for storage performance
  cs = sensorhelper.newModelObject('cdm:sys.sun.SunSPARCUnitaryComputerSystem')
  if computersystem.hasSignature():
    cs.setSignature(computersystem.getSignature())
  elif computersystem.hasSerialNumber() and computersystem.hasModel() and computersystem.hasManufacturer():
    cs.setSerialNumber(computersystem.getSerialNumber())
    cs.setModel(computersystem.getModel())
    cs.setManufacturer(computersystem.getManufacturer())
  else:
    log.info('Could not find naming rules to build skinny computer system, storage performance might suffer from using full computer system')
    cs = computersystem
  
  # check if sudo is configured for fcinfo first, this way we won't trigger
  # a sudo alert if we run it and it fails
  sudo_list = sensorhelper.executeCommand('sudo -l')
  if sudo_list:
    if not re.search('.*fcinfo.*', sudo_list):
      raise CommandNotFoundError('fcinfo not in sudo') # don't attempt sudo fcinfo
  else:
    raise CommandNotFoundError('fcinfo not in sudo') # don't attempt sudo fcinfo
  
  try:
    output = sensorhelper.executeCommand('sudo /usr/sbin/fcinfo hba-port')
  except:
    log.info('fcinfo command failed, halting execution of disk discovery.')
    raise CommandNotFoundError('fcinfo command failed')
    
  for hba_line in output.splitlines():
    if re.search('HBA Port WWN: [a-fA-F0-9]{16}', hba_line):
      hba_port_wwn = hba_line.split()[-1]
      hba_node_wwn = None
    elif re.search('Node WWN: [a-fA-F0-9]{16}', hba_line):
      hba_node_wwn = hba_line.split()[-1]
      log.info('Found HBA Port ' + hba_port_wwn + ' and Node ' + hba_node_wwn)
      scsi_pc = sensorhelper.newModelObject('cdm:dev.SCSIProtocolController')
      scsi_pc.setName(WorldWideNameUtils.toUniformString(hba_node_wwn))
      scsi_pc.setParent(cs)

      scsi_pe = sensorhelper.newModelObject('cdm:dev.SCSIProtocolEndPoint')
      scsi_pe.setName(WorldWideNameUtils.toUniformString(hba_port_wwn))
      scsi_pe.setWorldWideName(WorldWideNameUtils.toUniformString(hba_port_wwn))
      scsi_pe.setParent(scsi_pc)
      scsi_pc.setEndPoints(sensorhelper.getArray([scsi_pe], 'cdm:dev.SCSIProtocolEndPoint'))

      # continue now that we have the HBA port and node WWN
      rport_output = sensorhelper.executeCommand('sudo /usr/sbin/fcinfo remote-port -ls -p ' + hba_port_wwn)
      if rport_output:
        for line in rport_output.splitlines():
          if re.search('LUN: [0-9]+', line):
            lun = line.split()[-1]
          elif re.search('OS Device Name: ', line):
            dev_name = line.split()[-1]
            # build FCVolume
            if dev_name != 'Unknown':
              log.info('Found LUN ' + lun + ' and device name ' + dev_name)
              fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
              fcv.setSCSILun(long(lun))
              fcv.setFCPLun(int(lun))
              fcv.setName(dev_name.split('/')[-1][:-2])
              fcv.setPortWWN(WorldWideNameUtils.toUniformString(hba_port_wwn))
              fcv.setNodeWWN(WorldWideNameUtils.toUniformString(hba_node_wwn))
              fcv.setParent(cs)
              fcv.setController(scsi_pc)
              log.debug(str(fcv))
              result.addExtendedResult(fcv)
            else:
              log.info('Skipping OS Device Name \'Unknown\'')

  log.info("Solaris Fibre Channel discovery extension ended.")
except CommandNotFoundError:
  pass
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)