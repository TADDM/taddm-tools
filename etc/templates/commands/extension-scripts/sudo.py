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
#    Version 0.1 -- 09/2019   -- Initial Version --
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
from decimal import Decimal

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

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

def get_class_name(model_object):
  cn = model_object.__class__.__name__
  real_class_name=cn.replace("Impl","")
  return real_class_name

# copied from ext_attr_helper because of CNF error while running on anchor
def get_os_type(os_handle):
  '''
  Return OS we are on --> UNIX or WINDOWS
  '''
  cs = sensorhelper.getComputerSystem(os_handle)
  class_name = get_class_name(cs)
  #LogInfo("OS Classname is:  " + str(class_name))
  if re.search("Linux",class_name,re.I):
    os_type = "Linux"
  elif re.search("Windows",class_name,re.I):
    os_type = "Windows"
  elif re.search("AIX",class_name,re.I):
    os_type = "Aix"
  elif re.search("Sun",class_name,re.I):
    os_type = "Sun"
  else:
    os_type = "UNKNOWN"
  return os_type

sudo_list = None
def validateSudo(cmd=None):
  try:
    if cmd:
      global sudo_list
      if sudo_list is None:
        sudo_list = sensorhelper.executeCommand('sudo -l 2>/dev/null')
      # look for line containing (root) NOPASSWD: .*cmd.*
      regex = re.compile('\(((root)|(ALL))\) NOPASSWD: .*' + cmd + '.*', re.MULTILINE | re.DOTALL)
      if regex.search(sudo_list):
        return True
      else:
        return False
    else:
      try:
        sudo_list = sensorhelper.executeCommand('sudo -l 2>&1')
        return True
      except:
        return False
  except:
    return False

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("sudo discovery extension started (written by Mat Davis - mdavis5@us.ibm.com)")

  is_virtual = True # assume virtual
  if computersystem.hasModel() and not 'virtual' in computersystem.getModel().lower():
    # model is set and does not contain 'virtual'
    if computersystem.hasVirtual():
      if not computersystem.getVirtual():
        is_virtual = False # virtual is set to False
    else:
      # virtual is not set and model does not contain 'virtual'
      is_virtual = False

  log.info('Is server virtual? ' + str(is_virtual))
  
  is_vmware = False
  if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform'):
    is_vmware = True
  log.info('Is server VMware? ' + str(is_vmware))
  
  xa = {}
  xa['sudo_hba'] = '' # for collectionengine and fcinfo on Solaris
  xa['sudo_lsof'] = ''
  xa['sudo_dmidecode'] = ''
  xa['sudo_rdm'] = ''

  if validateSudo() is False:
    # sudo is not set up for this host
    log.info('sudo is invalid')
    xa['sudo_verified'] = 'invalid'
  else:
    log.info('sudo is valid')
    xa['sudo_verified'] = 'valid'
    if validateSudo('lsof') is False:
      xa['sudo_lsof'] = 'invalid'
    else:
      xa['sudo_lsof'] = 'valid'
    log.info('sudo lsof is ' + str(xa['sudo_lsof']))
    
    os_type = get_os_type(os_handle)
    # if physical host check for collectionengine in sudo
    if is_virtual is False:
      log.info('Checking for HBA discovery commands on physical server')
      ce = 'collectionengine'
      if "Linux" == os_type:
        ce = 'collectionengine-linux'
      elif "Sun" == os_type:
        ce = 'collectionengine-solaris-sparc'
        
      if validateSudo(ce):
        log.info(ce + ' found in sudo')
        # check for fcinfo on Sun required by SolarisFC.py ext
        if "Sun" == os_type and validateSudo('fcinfo') is False:
          log.info('fcinfo for SolarisFC.py discovery extension not found in sudo')
          xa['sudo_hba'] = 'invalid'
        else:
          xa['sudo_hba'] = 'valid'
      else:
        log.info(ce + ' not found in sudo')
        xa['sudo_hba'] = 'invalid'
      log.info('sudo hba (collectionengine) is ' + str(xa['sudo_hba']))

    # check for Linux specific
    if "Linux" == os_type:
      if validateSudo('dmidecode'):
        xa['sudo_dmidecode'] = 'valid'
      else:
        xa['sudo_dmidecode'] = 'invalid'
      log.info('sudo dmidecode is ' + str(xa['sudo_dmidecode']))
      
      if is_vmware:
        # VMware Linux VM
        lsscsi_out = ''
        try:
          log.info('Running lsscsi on VMware Linux VM to look for RDMs')
          lsscsi_out = sensorhelper.executeCommand('lsscsi')
        except:
          log.info('lsscsi command failed')
          pass
        
        if re.search('.*EMC.*', lsscsi_out):
          log.info('Linux VM contains RDM, checking if sg_inq in sudo')
          if validateSudo('sg_inq'):
            xa['sudo_rdm'] = 'valid'
          else:
            log.info('sg_inq for RDM.py discovery extension not found in sudo')
            # get lsscsi version, 0.26 or higher will work for RDM.py
            lsscsi_ver = sensorhelper.executeCommand('lsscsi -V 2>&1')
            if lsscsi_ver:
              version = Decimal(lsscsi_ver.split()[1])
              log.info('Found lsscsi version ' + str(version))
              if version > Decimal('0.25'):
                log.info('lsscsi version is equal or greater than 0.26, valid')
                xa['sudo_rdm'] = 'valid'
              else:
                log.info('lsscsi version is less than 0.26, invalid')
                xa['sudo_rdm'] = 'invalid'
            else:
              log.info('No output for lsscsi version command')
              xa['sudo_rdm'] = 'invalid'
          log.info('sudo rdm (sg_inq/lsscsi) is ' + str(xa['sudo_rdm']))
        else:
          log.info('lsscsi output does not contain RDM')
              
  sensorhelper.setExtendedAttributes(computersystem, xa)
  log.info("sudo discovery extension ended")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)