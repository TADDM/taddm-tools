
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

# this is for new Python v2.5.3
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.prefix = jython_home + "/Lib"

# add sensor-tools to sys.path if not already there
ext_path = coll_home + '/lib/sensor-tools'
if ext_path not in sys.path:
  sys.path.append(ext_path)

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

# run fcinfo command
def fcinfo():
  fc_vols = {}
  
  # check if sudo is configured for fcinfo first, this way we won't trigger
  # a sudo alert if we run it and it fails
  sudo_list = sensorhelper.executeCommand('sudo -l')
  if sudo_list:
    if not re.search('.*fcinfo.*', sudo_list):
      log.info('fcinfo not in sudo') # don't attempt sudo fcinfo
      return fc_vols
  else:
    log.info('fcinfo not in sudo') # don't attempt sudo fcinfo
    return fc_vols
    
  try:
    output = sensorhelper.executeCommand('sudo /usr/sbin/fcinfo hba-port')
  except:
    log.info('fcinfo command failed, halting execution of disk discovery.')
    return fc_vols
    
  for hba_line in output.splitlines():
    if re.search('HBA Port WWN: [a-fA-F0-9]{16}', hba_line):
      hba_port_wwn = hba_line.split()[-1]
      hba_node_wwn = None
    elif re.search('Node WWN: [a-fA-F0-9]{16}', hba_line):
      hba_node_wwn = hba_line.split()[-1]
      log.info('Found HBA Port ' + hba_port_wwn + ' and Node ' + hba_node_wwn)
      scsi_pc = sensorhelper.newModelObject('cdm:dev.SCSIProtocolController')
      scsi_pc.setName(WorldWideNameUtils.toUniformString(hba_node_wwn))
      #scsi_pc.setParent(cs) # parent set later at the end

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
            if dev_name.startswith('/dev/rmt/'):
              log.info('Skipping tape drive: ' + dev_name)
              continue
            if dev_name == 'Unknown':
              log.info('Skipping OS Device Name \'Unknown\'')
              continue
            if dev_name.startswith('/devices/'):
              log.info('Skipping device under /devices: ' + dev_name)
              continue
            # build FCVolume
            log.info('Found LUN ' + lun + ' and device name ' + dev_name)
            name = dev_name.split('/')[-1][:-2]
            fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
            fcv.setSCSILun(long(lun))
            fcv.setFCPLun(int(lun))
            fcv.setName(name)
            fcv.setPortWWN(WorldWideNameUtils.toUniformString(hba_port_wwn))
            fcv.setNodeWWN(WorldWideNameUtils.toUniformString(hba_node_wwn))
            fcv.setController(scsi_pc)
            log.debug(str(fcv))
            fc_vols[name] = fcv
  return fc_vols

# use EMC inq to discover VPLEX remote UUID
def emc_inq(remotePath, fc_vols):
  
  try:
    output = sensorhelper.executeCommand(remotePath + ' -no_dots -vplex_wwn')
  except:
    log.info(remotePath + ' command failed, halting execution of disk discovery.')
    return fc_vols
  
  for line in output.splitlines():
    # TODO look for other valid startswith lines if they exist
    if line.startswith('/dev/rdsk/'):
      s = line.split()
      if len(s) == 5:
        device = s[0]
        name = device.split('/')[-1][:-2] # remove s2 from the end
        uuid = s[4]
        # make sure wwn is in format of a VPLEX UUID
        if len(uuid) == 32:
          uuid = uuid.upper()
          vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
          # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
          # have been using it all over the place as a hack
          vsv.setManagedSystemName(uuid)
          
          if name in fc_vols.keys():
            fcv = fc_vols[name] # use existing
          else:
            fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
          fcv.setName(name)
          # create relationships
          bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
          bo.setSource(fcv)
          bo.setTarget(vsv)
          bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
          fcv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
          fc_vols[name] = fcv

        else:
          #result.warning('line parse unexpected:' + uuid)
          log.warning('UUID not 32 hex number:' + uuid)
      else:
        #result.warning('line parse unexpected:' + line)
        log.warning('line parse unexpected:' + line)
  return fc_vols

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
def main():
  try:
    global log
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
    
    fc_vols = fcinfo()
    
    # only run EMC INQ if physical
    is_virtual = True # assume virtual
    if computersystem.hasModel() and not 'virtual' in computersystem.getModel().lower():
      # model is set and does not contain 'virtual'
      if computersystem.hasVirtual():
        if not computersystem.getVirtual():
          is_virtual = False # virtual is set to False
      else:
        # virtual is not set and model does not contain 'virtual'
        is_virtual = False
    
    if is_virtual is False:
      # EMC inquiry tool can be downloaded from ftp://ftp.emc.com/pub/symm3000/inquiry/
      # copy inq to targets
      inq = 'inq.sol64'
      path = coll_home + "/etc/templates/commands/extension-scripts/" + inq
      # TODO verify local path
      remotePath = os_handle.executeCommand('pwd').strip()
      if not remotePath.endswith('/'):
        remotePath = remotePath + '/'
      remotePath = remotePath + inq
      os_handle.copyToRemote(path, remotePath)
      sensorhelper.executeCommand('chmod +x ' + remotePath) # grant execute permission
    
      fc_vols = emc_inq(remotePath, fc_vols)
    else:
      log.info('Virtual server detected, skipping EMC INQ discovery')      
    
    # add all the FCVolumes to the extended result
    for fc_vol in fc_vols.values():
      fc_vol.setParent(cs) # set parent
      if fc_vol.hasController():
        fc_vol.getController().setParent(cs)
      result.addExtendedResult(fc_vol)
    
    log.info("Solaris Fibre Channel discovery extension ended.")
  except:
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
    LogError(errMsg)
    result.warning(errMsg)

if __name__ == "__main__":
  main()