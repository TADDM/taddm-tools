
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

# this is for new Python v2.5.3
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.prefix = jython_home + "/Lib"

# add extension-scripts to sys.path if not already there
ext_path = coll_home + '/etc/templates/commands/extension-scripts'
if ext_path not in sys.path:
  sys.path.append(ext_path)

import os
# when AnchorSensor copies compiled file *$py.class the $py is removed and this causes
# runtime errors on the remote anchor, so rename any *.class to *$py.class
for root, dirs, files in os.walk(ext_path):
  for filename in files:
    if filename.endswith('.class') and not filename.endswith('$py.class'):
      basename = filename.split('.')[0]
      try:
        os.rename(ext_path + '/' + filename, ext_path + '/' + basename + '$py.class')
      except:
        print 'ERROR: Unable to rename ' + filename + ' to ' + basename + '$py.class'
        pass

# now import from extension-scripts
import helper
from sudo import Validator

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

class CommandNotFoundError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

# build out basedOn for volume and return volume
def buildVolume(uuid, vol):
  
  vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
  # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
  # have been using it all over the place as a hack
  vsv.setManagedSystemName(uuid)
  log.debug('Array volume:' + str(vsv))
  
  # create relationships
  bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
  bo.setSource(vol)
  bo.setTarget(vsv)
  bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
  vol.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
  log.debug('FC volume:' + str(vol))
  
  return vol
 
def sg_inq(disk, vol):
  sg_inq_output = sensorhelper.executeCommand('sudo sg_inq -i ' + disk)
  if sg_inq_output:
    # parse out UUID
    regex = re.compile('\[0x[a-fA-F0-9]{32}\]', re.MULTILINE)
    uuid_match = regex.search(sg_inq_output)
    if uuid_match:
      uuid = uuid_match.group(0).strip()
      uuid = uuid[3:] # take off [Ox from beginning
      uuid = uuid[:-1] # take off ] from end
      uuid = uuid.upper()
      log.debug('uuid: ' + uuid)
      if uuid.startswith('6'):
        return buildVolume(uuid, vol)
      else:
        # TODO add result warning that Invista disk not found
        log.warning('WWN does not start with 6:' + uuid)
    else:
      log.warning('Could not find UUID in sq_inq output for ' + disk)

  return None
  
##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("RDM discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

  try:
    output = sensorhelper.executeCommand('lsscsi')
  except:
    log.info('lsscsi not found on server, halting execution of RDM discovery.')
    raise CommandNotFoundError('lsscsi not found')

  is_vmware = helper.is_vmware(computersystem)
  
  # check if there are any EMC Invista or DGC (V)RAID disks
  if re.search('.*EMC.*', output) or re.search('.*DGC.*', output):
    # get any previously discovered volumes
    vols = helper.get_volumes(result, log)

    try:
      # check if sg_inq installed
      if helper.validateCommand('sg_inq') is False:
        raise Exception()
      
      # check if sudo is configured for sg_inq, this way we won't trigger
      # a sudo alert if we run it and it fails
      sudo = Validator()
      if sudo.validateSudo('sg_inq') is False:
        raise Exception() # don't attempt sudo sg_inq
      
      # use sudo sg_inq -i <device>
      for line in output.splitlines():
        if re.search('.*EMC.*', line) or ( re.search('.*DGC.*', line) and re.search('.*RAID.*', line) ):
          disk = line.split()[-1]
          name = disk.split('/')[-1]
          vol = None
          if name in vols.keys():
            vol = vols[name] # use existing
            sg_inq(disk, vol)
          else:
            cdm_type = 'cdm:dev.FCVolume'
            # create SCSIVolume if RDM instead of FCVolume
            if is_vmware:
              cdm_type = 'cdm:dev.SCSIVolume'
              vol.setDescription('RDM')
            vol = sensorhelper.newModelObject(cdm_type)
            vol.setParent(computersystem)
            vol.setName(name)
            vol.setDeviceID(disk)
            sg_vol = sg_inq(disk, vol)
            if sg_vol:
              result.addExtendedResult(vol)
            
    except:
      log.warning('Failed to run sudo sg_inq on target')
      # get lsscsi version to decide how to proceed
      version = sensorhelper.executeCommand('lsscsi -V 2>&1')
      if version:
        version = Decimal(version.split()[1])
        if version > Decimal('0.26'):
          # use lsscsi --scsi_id
          for line in output.splitlines():
            if re.search('.*EMC.*', line):
              disk = line.split()[-1]
              scsi_output = sensorhelper.executeCommand('lsscsi --scsi_id | grep "' + disk +'"')
              if scsi_output:
                # parse out UUID
                uuid = scsi_output.split()[-1]
                # the scsi_id has a leading character '3'
                if len(uuid) == 33:
                  uuid = uuid[1:]
                uuid = uuid.upper()
                log.debug('uuid: ' + uuid)
                if uuid.startswith('6000144'):
                  name = disk.split('/')[-1]
                  vol = None
                  if name in vols.keys():
                    vol = vols[name] # use existing
                  else:
                    cdm_type = 'cdm:dev.FCVolume'
                    # create SCSIVolume if RDM instead of FCVolume
                    if is_vmware:
                      cdm_type = 'cdm:dev.SCSIVolume'
                      vol.setDescription('RDM')
                    vol = sensorhelper.newModelObject(cdm_type)
                    vol.setParent(computersystem)
                    vol.setName(name)
                    vol.setDeviceID(disk)
                    result.addExtendedResult(vol)
                
                  buildVolume(uuid, vol)
                else:
                  log.warning('WWN not in proper format, starting with 6000144 and 32 hex digits:' + uuid)
                  raise CommandNotFoundError('WWN not in proper format, starting with 6000144 and 32 hex digits:' + uuid) # abort
              else:
                log.warning('No output from lsscsi --scsi_id for ' + disk)
                # abort
                raise CommandNotFoundError('No output from lsscsi --scsi_id for ' + disk)
        elif version == Decimal('0.26'):
          # use lsscsi --wwn
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
                if uuid.startswith('6000144'):
                  name = disk.split('/')[-1]
                  vol = None
                  if name in vols.keys():
                    vol = vols[name] # use existing
                  else:
                    cdm_type = 'cdm:dev.FCVolume'
                    # create SCSIVolume if RDM instead of FCVolume
                    if is_vmware:
                      cdm_type = 'cdm:dev.SCSIVolume'
                      vol.setDescription('RDM')
                    vol = sensorhelper.newModelObject(cdm_type)
                    vol.setParent(computersystem)
                    vol.setName(name)
                    vol.setDeviceID(disk)
                    result.addExtendedResult(vol)
                
                  buildVolume(uuid, vol)
                else:
                  # TODO add result warning that Invista disk not found
                  log.warning('WWN not in proper format, starting with 6000144 and 32 hex digits:' + uuid)
                  raise CommandNotFoundError('WWN not in proper format, starting with 6000144 and 32 hex digits:' + uuid) # abort
              else:
                log.warning('Failed to use lsscsi command to get disk output. Configure sudo for sg_inq to resolve.')
                raise CommandNotFoundError('Failed to use lsscsi command to get disk output. Configure sudo for sg_inq to resolve.')
        else:
          log.warning('Failed to use lsscsi command to get disk output. Configure sudo for sg_inq to resolve.')
      else:
        msg = 'Could not attain lsscsi version number'
        log.warning(msg)
        #result.warning(msg)
        raise CommandNotFoundError(msg)
    
  log.info("RDM discovery extension ended.")
except CommandNotFoundError:
  pass
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)