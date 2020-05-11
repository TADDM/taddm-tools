############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# WindowsRDM.py
#
# DESCRIPTION: 
#
# Authors:  Mat Davis
#			mdavis5@us.ibm.com
#
# History:
#
############################# End Standard Header ##############################

########################################################
# Standard Jython/Python Library Imports
########################################################
import sys
import java
import os

########################################################
# Additional from Java imports
########################################################
from java.lang import System
from java.io import File
from java.io import FileInputStream
from java.io import FileOutputStream
from com.collation.discover.util import WindowsAgentUtils
from com.collation.platform.model.util.openid import OpenId

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

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
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

log.info("Windows RDM discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

try:

  is_vmware = helper.is_vmware(computersystem)
  
  # use powershell to check if there are any EMC Invista disks on a Windows VM, this means there is RDM
  cmd = 'powershell -Command ' \
         '"& {$AllDevices = gwmi -Class Win32_DiskDrive -Namespace \'root\\CIMV2\'; ' \
         'ForEach ($Device in $AllDevices) { ' \
         '  Write-Host \'Model =\' $Device.Model;' \
         '}}"'
  try:
    # run command, get output
    output = sensorhelper.executeCommand(cmd)
  except:
    LogError("Command execution failed")
    raise

  # if there are any EMC Invista disks on the Windows VM, copy inquiry tool and run to get VPLEX UUID
  invista = re.search('.*EMC Invista.*', output)
  # Symmetrix RDMs are not connected to VPLEX in ViPR
  #symmetrix = re.search('.*EMC SYMMETRIX.*', output)
  #if invista is not None or symmetrix is not None:
  if re.search('.*EMC Invista.*', output) or re.search('.*DGC LUNZ.*', output):
    try:
      # EMC inquiry tool can be downloaded from ftp://ftp.emc.com/pub/symm3000/inquiry/ but we require an older
      # version for it to work. The tested version:
      # Inquiry utility, Version V7.3-1305 (Rev 1.0)      (SIL Version V7.3.1.0 (Edit Level 1305)
      # copy inq to targets
      inq = 'inq.exe'
      path = coll_home + "/etc/templates/commands/extension-scripts/" + inq
      remotePath = os_handle.executeCommand('cmd.exe /C echo %TEMP%').strip()
      if not remotePath.endswith('\\'):
        remotePath = remotePath + '\\'
      remotePath = remotePath + inq
      srcInq = File(path)
      tmpInq = File.createTempFile(srcInq.getName() + '-' + os_handle.getSession().getHost() + '-' + str(System.currentTimeMillis()), None)
      if not tmpInq.exists():
        tmpInq.createNewFile()
      source = None
      destination = None
      try:
        source = FileInputStream(srcInq).getChannel()
        destination = FileOutputStream(tmpInq).getChannel()
        destination.transferFrom(source, 0, source.size())
      finally:
        if source != None:
          source.close()
        if destination != None:
          destination.close()
      try:
        os_handle.copyToRemote(tmpInq.getCanonicalPath(), remotePath)
        WindowsAgentUtils.setWindowsFilePermissions(remotePath, os_handle.getSession())
      finally:
        tmpInq.delete()
        cmdGatewayCleanup = 'cmd.exe /C del /F ' + tmpInq.getName()
        try:
          os_handle.executeCommandOnGateway(cmdGatewayCleanup, 60000, None)
        except:
          pass
      
      # get any previously discovered volumes
      vols = helper.get_volumes(result, log)
      
      # -compat does nothing to output
      # -no_filters causes output to halt if not using -wwn
      remoteCmd = remotePath + ' -no_dots' 

      invista = re.search('.*EMC Invista.*', output)
      clar = re.search('.*DGC LUNZ.*', output)
      if invista is not None:
        remoteCmd = remoteCmd + ' -invista_wwn'
      elif clar is not None:
        remoteCmd = remoteCmd + ' -clar_wwn -compat'
        
      output = os_handle.getSession().executeCommand('cmd.exe /C "' + remoteCmd + ' 2> ' + remotePath + '_stderr.out"')
      for line in output.splitlines():
        #log.debug('line:' + line)
        # backspaces are escaped here, line actually starts with \\.\PHYSICALDRIVE
        if line.startswith('\\\\.\\PHYSICALDRIVE'):
          s = line.split()
          # handle invista or clariion output
          if len(s) == 4 or len(s) == 6:
            device = s[0].strip()
            name = 'Disk ' + device.replace('\\\\.\\PHYSICALDRIVE', '')
            array_serial = s[1].strip()
            adjust = 0
            if len(s) == 6:
              adjust = 2 # skip SP and IP Address columns
            lun_hex = s[2+adjust].strip()
            wwn = s[3+adjust].strip()
            # make sure wwn is in format of a VPLEX UUID
            if len(wwn) == 32 and lun_hex != '0xffff':
              log.info('Building LUN for ' + name)
              # continue creating
              wwn = wwn.upper()
              #log.debug('device:' + device + ';serial:' + array_serial + ';wwn:' + wwn)
              vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
              # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
              # have been using it all over the place as a hack
              vsv.setManagedSystemName(wwn)
              #log.debug('VPLEX volume:' + str(vsv))
              
              vol = None
              if name in vols.keys():
                vol = vols[name] # use existing
              else:
                vol = sensorhelper.newModelObject('cdm:dev.FCVolume')
                # create SCSIVolume if RDM instead of FCVolume
                if is_vmware:
                  vol = sensorhelper.newModelObject('cdm:dev.SCSIVolume')
                  vol.setDescription('RDM')
                vol.setName(name)
                vol.setDeviceID(name)
                vol.setParent(computersystem)
                result.addExtendedResult(vol)
              # create relationship
              bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
              bo.setSource(vol)
              bo.setTarget(vsv)
              bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
              vol.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
              #log.debug('Volume:' + str(vol))
            else:
              log.info('Skipping line:' + line)
          else:
            log.warning('line parse unexpected:' + line)
    except:
      LogError("Command execution failed")
      raise
  else:
    log.debug('No EMC Invista disks found on VM')
  log.info("Windows RDM discovery extension ended.")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during EMC INQ storage discovery: ' + str(ErrorValue)
  # known error related to diskless high powered computing, ignore this error
  if 'InitializeDefaultDrives' in str(ErrorValue):
    log.info('Known error for diskless HPC: ' + str(ErrorValue))
  else:
    LogError(errMsg)
    result.warning(errMsg)
  log.info("Windows RDM discovery extension ended.")
