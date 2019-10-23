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

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

log.info("Windows RDM discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

try:

  if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform'):
  
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
    if invista is not None:

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
        
        remoteCmd = remotePath
        # set flag according to whether it's invista or symmetrix
        if invista is not None:
          remoteCmd = remoteCmd + ' -invista_wwn'
        # symmetrix RDMs are not connected to the VPLEX in ViPR
        #elif symmetrix is not None:
        #  remoteCmd = remoteCmd + ' -sym_wwn'
          
        output = os_handle.getSession().executeCommand('cmd.exe /C "' + remoteCmd + ' 2> ' + remotePath + '_stderr.out"')
        vplexes = {}
        for line in output.splitlines():
          #log.debug('line:' + line)
          # backspaces are escaped here, line actually starts with \\.\PHYSICALDRIVE
          if line.startswith('\\\\.\\PHYSICALDRIVE'):
            s = line.split()
            if len(s) == 4:
              device = s[0]
              array_serial = s[1]
              lunhex = s[2]
              wwn = s[3]
              # make sure wwn is in format of a VPLEX UUID
              if len(wwn) == 32:
                # capture VPLEX to create uses relationship at the end
                if array_serial not in vplexes:
                  # filling out a few basic details of VPlex just in case ViPR sensor has not discovered yet
                  sss = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
                  # add storage function
                  func = sensorhelper.newModelObject('cdm:storage.StorageControllerFunction')
                  func.setParent(sss)
                  func.setName("Storage")
                  sss.setFunctions(sensorhelper.getArray([func],'cdm:sys.Function'))
                  # set openID serial so that this will merge with ViPR discovered VPlex
                  sss.setOpenId(OpenId(sss).addId('vplexserial', array_serial))
                  sss.setSerialNumber(array_serial)
                  sss.setAnsiT10Id(array_serial) # this should also cause merge with ViPR discovered VPlex
                  sss.setType('VirtualStorage')
                  vplexes[array_serial] = sss # cache sss
                  
                # continue creating
                wwn = wwn.upper()
                #log.debug('device:' + device + ';serial:' + array_serial + ';wwn:' + wwn)
                vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
                # have been using it all over the place as a hack
                vsv.setManagedSystemName(wwn)
                #log.debug('VPLEX volume:' + str(vsv))
                #result.addExtendedResult(vsv)
                
                scsi_vol = sensorhelper.newModelObject('cdm:dev.SCSIVolume')
                disk = 'Disk ' + device.replace('\\\\.\\PHYSICALDRIVE', '')
                scsi_vol.setName(disk)
                scsi_vol.setDeviceID(disk)
                scsi_vol.setDescription('RDM')
                scsi_vol.setParent(cs)
                # create relationships
                bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
                bo.setSource(scsi_vol)
                bo.setTarget(vsv)
                bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
                scsi_vol.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
                #log.debug('SCSI volume:' + str(scsi_vol))
                result.addExtendedResult(scsi_vol)
                
                # redefine so basedOn not included twice
                scsi_vol = sensorhelper.newModelObject('cdm:dev.SCSIVolume')
                scsi_vol.setName(disk)
                scsi_vol.setDeviceID(disk)
                scsi_vol.setDescription('RDM')
                scsi_vol.setParent(cs)

                realizes = sensorhelper.newModelObject('cdm:dev.RealizesExtent')
                realizes.setSource(vsv)
                realizes.setTarget(scsi_vol)
                realizes.setType('com.collation.platform.model.topology.dev.RealizesExtent')
                result.addExtendedResult(realizes)
                
              else:
                log.warning('WWN not 32 hex number:' + wwn)
            else:
              log.warning('line parse unexpected:' + line)
              
        for vplex in vplexes.values():
          # create uses relation for each vplex
          uses = sensorhelper.newModelObject('cdm:relation.Uses')
          uses.setSource(cs)
          uses.setTarget(vplex)
          uses.setType('com.collation.platform.model.topology.relation.Uses')
          # DANGER! By updating the vplex and not updating all the virtual volume members on the vplex, you
          # open up the possibility of the StorageExtentCleanupAgent deleting a bunch of virtual volumes.
          # Do not store the VPLEX
          #result.addExtendedResult(uses)
            
      except:
        LogError("Command execution failed")
        raise
    else:
      log.debug('No EMC Invista disks found on VM')
  log.info("Windows RDM discovery extension ended.")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)