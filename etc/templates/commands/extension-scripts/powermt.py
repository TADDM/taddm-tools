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
#    Version 0.5 -- 01/2020  -- Initial Version --
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

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

# this is for new Python v2.5.3
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.path.append(coll_home + "/etc/templates/commands/extension-scripts") # for sudo.py
sys.prefix = jython_home + "/Lib"

########################################################
# More Standard Jython/Python Library Imports
########################################################
import traceback

########################################################
# Custom Libraries to import (Need to be in the path)
########################################################
import sensorhelper
# sometimes on a remote anchor this will cause a ClassNotFoundException
# when this import is done, TADDM should compile the sudo.py class and
# there should be a sudo$py.class file, if not this error will occur.
# To resolve, delete sudo.class from the remote anchor and run again
import sudo

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

def main():
  ##########################################################
  # Main
  # Setup the various objects required for the extension
  ##########################################################
  try:
    (os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)
    global log

    log.info("powermt discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

    try:
      if sudo.validateSudo('/sbin/powermt'):
        output = sensorhelper.executeCommand('sudo /sbin/powermt display dev=all')
      else:
        log.info('/sbin/powermt not in sudo, halting execution of disk discovery.')
        raise CommandNotFoundError('/sbin/powermt not in sudo')
    except:
      log.info('sudo /sbin/powermt command failed, halting execution of disk discovery.')
      raise CommandNotFoundError('sudo /sbin/powermt command failed')

    disk = None
    uuid = None
    vvol = None
    fcvolumes = []
    for line in output.splitlines():
      if line.startswith('Pseudo name='):
        disk = line.split('=')[1]
      if line.startswith('Logical device ID='):
        uuid = line.split('=')[1].split(' ')[0]
        if len(line.split(' ')) > 3:
          vvol = line.split(' ')[3].replace('[', '').replace(']','')
        elif len(line.split()) > 2:
          vvol = None
        else:
          log.info('Skipping line missing volume information: ' + line)
          disk = None
          uuid = None
          continue
        if disk:
          log.info(str(disk) + ' ' + str(uuid) + ' ' + str(vvol))
          
          vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
          if vvol:
            vsv.setName(vvol)
          vsv.setVirtual(True)
          # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
          # have been using it all over the place as a hack
          vsv.setManagedSystemName(uuid)
          
          fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
          fcv.setName(disk)
          fcv.setParent(computersystem)
          # create relationships
          bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
          bo.setSource(fcv)
          bo.setTarget(vsv)
          bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
          fcv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
          fcvolumes.append(fcv)
          
          # reset all values
          disk = None
          uuid = None
          vvol = None
    
    # DANGER! Do not create and store the vplex without updating ALL the virtual volume members on the vplex, you
    # open up the possibility of the StorageExtentCleanupAgent deleting a bunch of virtual volumes.

    # if any FC volumes discovered, we continue
    if len(fcvolumes) > 0:
      extents = []
      # local disks
      local_disks = os_handle.getLocalDiskVolumes()
      if local_disks:
        for local_disk in local_disks:
          log.info('disk=' + str(local_disk))
          match = False
          for fcv in fcvolumes:
            if fcv.getName() == local_disk.getName():
              log.info('Found matching disk')
              extents.append(fcv)
              fcvolumes.remove(fcv) # remove from list
              match = True
              break
          if not match:
            extents.append(local_disk)
      # disk partitions
      partitions = os_handle.getDiskPartitions()
      if partitions:
        for partition in partitions:
          log.info('partition=' + str(partition))
          extents.append(partition)
      # volumes
      try:
        volumes = os_handle.getStorageVolumes()
        if volumes:
          for volume in volumes:
            log.info('storage volume=' + str(volume))
            extents.append(volume)
      except:
        log.info('Unable to find Storage Volumes')

      # if there are any FC volumes left then add to the end of the list
      for fcv in fcvolumes:
        log.info('Adding additional FC volume=' + str(fcv))
        extents.append(fcv)

      computersystem.setStorageExtent(sensorhelper.getArray(extents, 'cdm:dev.StorageExtent'))
      
    log.info("powermt discovery extension ended.")
  except CommandNotFoundError:
    pass # quietly move on if powermt command is not found
  except:
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
    LogError(errMsg)
    result.warning(errMsg)

if __name__ == "__main__":
  main()