
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

  log.info("HyperVDisks discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

  # build skinny computersystem for storage performance
  cs = sensorhelper.newModelObject('cdm:sys.windows.WindowsComputerSystem')
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
    output = sensorhelper.executeCommand('"C:\Program Files\EMC\PowerPath\Powermt.exe" display dev=all')
  except:
    log.info('Powermt.exe not found on server, halting execution of disk discovery.')
    raise CommandNotFoundError('Powermt.exe not found')

  disk = None
  vplexid = None
  uuid = None
  vvol = None
  vplexes = {}
  for line in output.splitlines():
    if line.startswith('Pseudo name=harddisk'):
      disk = line.split('=harddisk')[1]
    if line.startswith('VPLEX ID='):
      vplexid = line.split('=')[1].strip()
    if line.startswith('Logical device ID='):
      uuid = line.split('=')[1].split(' ')[0]
      if len(line.split(' ')) > 3:
        vvol = line.split(' ')[3].replace('[', '').replace(']','')
      elif len(line.split()) > 2:
        vvol = None
      else:
        log.info('Skipping line missing volume information: ' + line)
        disk = None
        vplexid = None
        uuid = None
        continue
      if disk and vplexid:
        log.info(str(disk) + ' ' + str(vplexid) + ' ' + str(uuid) + ' ' + str(vvol))
        
        if vplexid in vplexes:
          # VPlex already defined
          sss = vplexes[vplexid]
        else:
          # filling out a few basic details of VPlex just in case ViPR sensor has not discovered yet
          sss = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
          # add storage function
          func = sensorhelper.newModelObject('cdm:storage.StorageControllerFunction')
          func.setParent(sss)
          func.setName("Storage")
          sss.setFunctions(sensorhelper.getArray([func],'cdm:sys.Function'))
          # set openID serial so that this will merge with ViPR discovered VPlex
          sss.setOpenId(OpenId(sss).addId('vplexserial', vplexid))
          sss.setSerialNumber(vplexid)
          sss.setAnsiT10Id(vplexid) # this should also cause merge with ViPR discovered VPlex
          sss.setType('VirtualStorage')
          vplexes[vplexid] = sss # cache sss

        vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
        if vvol:
          vsv.setName(vvol)
        vsv.setVirtual(True)
        # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
        # have been using it all over the place as a hack
        vsv.setManagedSystemName(uuid)
        
        # do not set members array, ViPR sensor extension will set this
        
        #result.addExtendedResult(vsv)
        
        fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
        fcv.setName('Disk ' + disk)
        fcv.setParent(cs)
        # create relationships
        bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
        bo.setSource(fcv)
        bo.setTarget(vsv)
        bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
        fcv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
        result.addExtendedResult(fcv)
        
        vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
        if vvol:
          vsv.setName(vvol)
        vsv.setVirtual(True)
        # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
        # have been using it all over the place as a hack
        vsv.setManagedSystemName(uuid)
        fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
        fcv.setName('Disk ' + disk)
        fcv.setParent(cs)
        realizes = sensorhelper.newModelObject('cdm:dev.RealizesExtent')
        realizes.setSource(vsv)
        realizes.setTarget(fcv)
        realizes.setType('com.collation.platform.model.topology.dev.RealizesExtent')
        result.addExtendedResult(realizes)
        
        # reset all values
        disk = None
        vplexid = None
        uuid = None
        vvol = None
  
  for vplex in vplexes.values():
    # create uses relation for each vplex
    uses = sensorhelper.newModelObject('cdm:relation.Uses')
    uses.setSource(cs)
    uses.setTarget(vplex)
    uses.setType('com.collation.platform.model.topology.relation.Uses')
    result.addExtendedResult(uses)

  log.info("HyperVDisks discovery extension ended.")
except CommandNotFoundError:
  pass
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)