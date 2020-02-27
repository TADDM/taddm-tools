
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
import os
from decimal import Decimal

########################################################
# Additional from Java imports
########################################################
from java.lang import System

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

# this is for new Python v2.5.3
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.prefix = jython_home + "/Lib"

ext_paths = [ jython_home + '/Lib', coll_home + '/lib/sensor-tools', coll_home + '/etc/templates/commands/extension-scripts' ]
for ext_path in ext_paths:
  # add to sys.path if not already there
  if ext_path not in sys.path:
    sys.path.append(ext_path)

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

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
def main():
  try:
    global log
    (os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

    log.info("EMC INQ discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")
    
    is_vm = False
    if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform'):
      is_vm = True
    else:
      log.info('Target is not VMware VM, skipping EMC INQ')
      log.info("EMC INQ discovery extension ended.")
      return

    try:
      output = sensorhelper.executeCommand('lsscsi')
      # check if there are any EMC Invista disks
      if re.search('.*EMC.*', output) is None:
        log.info('lsscsi did not detect any EMC disks to discover')
        log.info("EMC INQ discovery extension ended.")
        return
    except:
      log.info('lsscsi not found on server, halting execution')
      log.info("EMC INQ discovery extension ended.")
      return

    # INQ is needed only if sg_inq not installed and lsscsi version < 0.26
    # check if sg_inq installed
    if helper.validateCommand('sg_inq'):
      log.info('sg_inq is installed, do not need EMC INQ')
      log.info("EMC INQ discovery extension ended.")
      return
    else:
      # check if lsscsi version > 0.25
      version = sensorhelper.executeCommand('lsscsi -V 2>&1')
      if version and Decimal(version.split()[1]) > Decimal('0.25'):
        log.info('lsscsi is at version 0.26+, do not need EMC INQ')
        log.info("EMC INQ discovery extension ended.")
        return
    
    # EMC inquiry tool can be downloaded from ftp://ftp.emc.com/pub/symm3000/inquiry/
    inq = 'inq.LinuxAMD64'
    remotePath = '/usr/local/bin/'
    
    # check if INQ installed in /usr/local/bin/inq
    if not helper.does_exist(remotePath + inq):
      # copy inq to targets
      lpath = coll_home + "/etc/templates/commands/extension-scripts/" + inq
      # TODO verify local binary exists
      
      pwd = os_handle.executeCommand('pwd').strip()
      if not pwd.endswith('/'):
        pwd = pwd + '/'
      os_handle.copyToRemote(lpath, pwd + inq)
      sensorhelper.executeCommand('chmod +x ' + pwd + inq) # grant execute permission
      
      log.info(inq + ' not installed under ' + remotePath + ', binary was staged in ' + pwd)
      log.info("EMC INQ discovery extension ended.")
      return
  
    # check if command in sudo
    cmd = remotePath + inq
    sudo = Validator()
    if not sudo.validateSudo(cmd):
      log.info(cmd + ' not found in sudoers')
      log.info("EMC INQ discovery extension ended.")
      return
    
    cmd = 'sudo ' + remotePath + inq
    
    # get any previously discovered volumes
    vols = {}
    ext_results = result.getExtendedResults()
    iter = ext_results.iterator()
    while iter.hasNext():
      ext_result = iter.next()
      class_name = helper.get_class_name(ext_result)
      if re.search("FCVolume",class_name,re.I):
        log.debug('Found existing FCVolume:' + str(ext_result))
        vols[ext_result.getName()] = ext_result
      elif re.search("SCSIVolume",class_name,re.I):
        vols[ext_result.getName()] = ext_result
        log.debug('Found existing SCSIVolume:' + str(ext_result))
        
    try:
      output = sensorhelper.executeCommand(cmd + ' -no_dots -vplex_wwn')
      
      for line in output.splitlines():
        # if line starts with /dev/ then we use this disk
        if line.startswith('/dev/'):
          s = line.split()
          if len(s) == 5:
            device = s[0]
            name = device.split('/')[-1]
            uuid = s[4]
            # make sure wwn is in format of a VPLEX UUID
            if len(uuid) == 32:
              uuid = uuid.upper()
              vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
              # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
              # have been using it all over the place as a hack
              vsv.setManagedSystemName(uuid)
              
              vol = None
              if name in vols.keys():
                vol = vols[name] # use existing
              else:
                cdm_type = 'cdm:dev.FCVolume'
                # create SCSIVolume if RDM instead of FCVolume
                if is_vm:
                  cdm_type = 'cdm:dev.SCSIVolume'
                vol = sensorhelper.newModelObject(cdm_type)
                vol.setParent(computersystem)
                vol.setName(name)
                result.addExtendedResult(vol)
              # create relationship
              bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
              bo.setSource(vol)
              bo.setTarget(vsv)
              bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
              vol.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))

            else:
              #result.warning('line parse unexpected:' + uuid)
              log.warning('UUID not 32 hex number:' + uuid)
          else:
            #result.warning('line parse unexpected:' + line)
            log.warning('line parse unexpected:' + line)
    except:
      log.info(remotePath + ' command failed, halting execution of disk discovery.')
      (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
      errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
      LogError(errMsg)
      result.warning(errMsg)
    
    log.info("EMC INQ discovery extension ended.")
  except:
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
    LogError(errMsg)
    result.warning(errMsg)

if __name__ == "__main__":
  main()