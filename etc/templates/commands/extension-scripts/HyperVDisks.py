
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

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
try:
  (os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

  log.info("HyperVDisks discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

  try:
    output = sensorhelper.executeCommand('"C:\Program Files\EMC\PowerPath\Powermt.exe" display dev=all')
  except:
    log.info('Powermt.exe not found on server, halting execution of disk discovery.')
    raise CommandNotFoundError('Powermt.exe not found')

  disk = None
  uuid = None
  vol_name = None
  vplexes = {}
  for line in output.splitlines():
    if line.startswith('Pseudo name=harddisk'):
      disk = line.split('=harddisk')[1]
    if line.startswith('Logical device ID='):
      if '??' in disk:
        log.info('Malformed disk number, skipping disk harddisk??')
        continue
      uuid = line.split('=')[1].split(' ')[0]
      if len(line.split(' ')) > 3:
        vol_name = line.split(' ')[3].replace('[', '').replace(']','')
      elif len(line.split()) > 2:
        vol_name = None
      else:
        log.info('Skipping line missing volume information: ' + line)
        disk = None
        uuid = None
        continue
      if disk:
        log.info(str(disk) + ' ' + str(uuid) + ' ' + str(vol_name))
        
        lun = sensorhelper.newModelObject('cdm:dev.StorageVolume')
        if vol_name:
          lun.setName(vol_name)
        # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
        # have been using it all over the place as a hack
        lun.setManagedSystemName(uuid)
        
        fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
        fcv.setName('Disk ' + disk)
        fcv.setParent(computersystem)
        # create relationships
        bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
        bo.setSource(fcv)
        bo.setTarget(lun)
        bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
        fcv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
        result.addExtendedResult(fcv)
        
        # reset all values
        disk = None
        uuid = None
        vol_name = None
  
    # WARNING! By updating the SSS that hosts the LUN and not updating all the volume members on the 
    # SSS, you open up the possibility of the StorageExtentCleanupAgent deleting a bunch of volumes.
    # Do not store the SSS in any way

  log.info("HyperVDisks discovery extension ended.")
except CommandNotFoundError:
  pass
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)