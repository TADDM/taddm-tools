
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
from decimal import Decimal

########################################################
# Additional from Java imports
########################################################
from java.lang import System
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
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("RDM discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

  if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform'):
  
    # build skinny computersystem for storage performance
    cs = sensorhelper.newModelObject('cdm:sys.linux.LinuxUnitaryComputerSystem')
    if computersystem.hasSignature():
      cs.setSignature(computersystem.getSignature())
    elif computersystem.hasSerialNumber() and computersystem.hasModel() and computersystem.hasManufacturer():
      cs.setSerialNumber(computersystem.getSerialNumber())
      cs.setModel(computersystem.getModel())
      cs.setManufacturer(computersystem.getManufacturer())
    else:
      log.info('Could not find naming rules to build skinny computer system, storage performance might suffer from using full computer system')
      cs = computersystem
    
    try:
      output = sensorhelper.executeCommand('lsscsi')
    except:
      log.info('lsscsi not found on server, halting execution of RDM discovery.')
      raise CommandNotFoundError('lsscsi not found')

    if re.search('.*EMC.*', output):
      # check if lsscsi is at version 0.26 or greater because we need the --wwn flag
      version = sensorhelper.executeCommand('lsscsi -V 2>&1')
      if version:
        log.debug('version output:' + version)
        version = Decimal(version.split()[1])
        log.debug('decimal version: ' + str(version))
        if version < Decimal('0.26'):
          msg = 'lsscsi version is not at 0.26 or greater. Version is ' + str(version)
          log.warning(msg)
          result.warning(msg)
          raise CommandNotFoundError(msg)
        else:
          log.debug('version ' + str(version) + ' is 0.26 or greater')
      else:
        log.debug('version empty')
      
    disk = None
    uuid = None
    for line in output.splitlines():
      if re.search('.*EMC.*', line):
        disk = line.split()[-1]
        wwnOutput = sensorhelper.executeCommand('lsscsi --wwn | grep "' + disk + '" | awk \'{print $3}\'')
        if wwnOutput:
          # parse out UUID
          uuid = wwnOutput.strip()
          if uuid.startswith('0x'):
            uuid = uuid[2:]
          uuid = uuid.upper()
          log.debug('uuid: ' + uuid)
          if len(uuid) == 32:
            vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
            # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
            # have been using it all over the place as a hack
            vsv.setManagedSystemName(uuid)
            log.debug('VPLEX volume:' + str(vsv))
            result.addExtendedResult(vsv)
            
            fcv = sensorhelper.newModelObject('cdm:dev.SCSIVolume')
            fcv.setName(disk.split('/')[-1])
            fcv.setDeviceID(disk)
            fcv.setDescription('RDM')
            fcv.setParent(cs)
            # create relationships
            bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
            bo.setSource(fcv)
            bo.setTarget(vsv)
            bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
            fcv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
            log.debug('SCSI volume:' + str(fcv))
            result.addExtendedResult(fcv)
            
            realizes = sensorhelper.newModelObject('cdm:dev.RealizesExtent')
            realizes.setSource(vsv)
            realizes.setTarget(fcv)
            realizes.setType('com.collation.platform.model.topology.dev.RealizesExtent')
            result.addExtendedResult(realizes)
          else:
            # TODO add result warning that Invista disk not found
            log.warning('WWN not 32 hex number:' + uuid)

        # reset all values
        disk = None
        uuid = None
  log.info("RDM discovery extension ended.")
except CommandNotFoundError:
  pass
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)