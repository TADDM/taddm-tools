
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

# build out result model objects and return as list
def buildVolume(uuid, disk):
  
  vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
  # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
  # have been using it all over the place as a hack
  vsv.setManagedSystemName(uuid)
  log.debug('VPLEX volume:' + str(vsv))
  
  scsi_vol = sensorhelper.newModelObject('cdm:dev.SCSIVolume')
  scsi_vol.setName(disk.split('/')[-1])
  scsi_vol.setDeviceID(disk)
  scsi_vol.setDescription('RDM')
  scsi_vol.setParent(computersystem)
  # create relationships
  bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
  bo.setSource(scsi_vol)
  bo.setTarget(vsv)
  bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
  scsi_vol.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
  log.debug('SCSI volume:' + str(scsi_vol))
  
  return scsi_vol
 
def sg_inq(disk):
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
      if uuid.startswith('6000144'):
        return buildVolume(uuid, disk)
      else:
        # TODO add result warning that Invista disk not found
        log.warning('WWN does not start with 6000144:' + uuid)
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

  if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform'):
  
    try:
      output = sensorhelper.executeCommand('lsscsi')
    except:
      log.info('lsscsi not found on server, halting execution of RDM discovery.')
      raise CommandNotFoundError('lsscsi not found')

    # check if there are any EMC Invista disks
    if re.search('.*EMC.*', output):
      rdm_volumes = []
      try:
        # check if sudo is configured for sg_inq first, this way we won't trigger
        # a sudo alert if we run it and it fails
        sudo_list = sensorhelper.executeCommand('sudo -l')
        if sudo_list:
          if not re.search('.*sg_inq.*', sudo_list):
            raise Exception() # don't attempt sudo sg_inq
        else:
          raise Exception() # don't attempt sudo sg_inq
        
        # use sudo sg_inq -i <device>
        for line in output.splitlines():
          if re.search('.*EMC.*', line):
            disk = line.split()[-1]
            scsi_vol = sg_inq(disk)
            if scsi_vol:
              rdm_volumes.append(scsi_vol)
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
                    rdm_volumes.append(buildVolume(uuid, disk))
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
                    rdm_volumes.append(buildVolume(uuid, disk))
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
      
      # if any RDM volumes discovered, we continue
      if len(rdm_volumes) > 0:
        extents = []
        local_disks = os_handle.getLocalDiskVolumes()
        if local_disks:
          for local_disk in local_disks:
            log.info('disk=' + str(local_disk))
            match = False
            for rdm_vol in rdm_volumes:
              if rdm_vol.getName() == local_disk.getName():
                log.info('Found matching RDM disk')
                extents.append(rdm_vol)
                rdm_volumes.remove(rdm_vol) # remove from list
                match = True
                break
            if not match:
              extents.append(local_disk)
        partitions = os_handle.getDiskPartitions()
        if partitions:
          for partition in partitions:
            log.info('partition=' + str(partition))
            extents.append(partition)
        try:
          volumes = os_handle.getStorageVolumes()
          if volumes:
            for volume in volumes:
              log.info('storage volume=' + str(volume))
              extents.append(volume)
        except:
          log.info('Unable to find Storage Volumes')

        # if there are any RDM volumes left then add to the end of the list
        for rdm_vol in rdm_volumes:
          log.info('Adding additional RDM volume=' + str(rdm_vol))
          extents.append(rdm_vol)

        computersystem.setStorageExtent(sensorhelper.getArray(extents, 'cdm:dev.StorageExtent'))
        
  log.info("RDM discovery extension ended.")
except CommandNotFoundError:
  pass
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)