#!/usr/bin/env ../../../../bin/jython_coll_253

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
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.prefix = jython_home + "/Lib"

# add extension-scripts to sys.path if not already there
ext_path = coll_home + '/lib/sensor-tools'
if ext_path not in sys.path:
  sys.path.append(ext_path)

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

# Custom helper library from extension-scripts
import helper
  
########################################################
# More Standard Jython/Python Library Imports
########################################################
import traceback
import re
import getopt

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

class Validator():
  def __init__(self, sudo_list=None):
    self.sudo_list = sudo_list
    
  def validateSudo(self, cmd=None):
    try:
      if cmd:
        if self.sudo_list is None:
          self.sudo_list = sensorhelper.executeCommandWithTimeout('sudo -l 2>/dev/null', 30*1000)
        # look for line containing (root) NOPASSWD: .*cmd.*
        regex = re.compile('\(((root)|(ALL))\) NOPASSWD: .*' + cmd + '.*', re.MULTILINE | re.DOTALL)
        if regex.search(self.sudo_list):
          return True
        else:
          return False
      else:
        try:
          self.sudo_list = sensorhelper.executeCommandWithTimeout('sudo -l 2>&1', 30*1000)
          return True
        except:
          return False
    except:
      return False

  # return full path(s) of command in sudoers
  def commandPath(self, cmd):
    paths = []
    if self.sudo_list is None:
      try:
        self.sudo_list = sensorhelper.executeCommandWithTimeout('sudo -l 2>/dev/null', 30*1000)
      except:
        pass
    for s in self.sudo_list.split():
      if cmd in s:
        paths.append(s.replace(',', ''))
    return paths
      
def main():
  ##########################################################
  # Main
  # Setup the various objects required for the extension
  ##########################################################
  global log
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
    xa['sudo_hba_path'] = '' # verify CE path matches home directory
    xa['sudo_lsof'] = ''
    xa['sudo_dmidecode'] = ''
    xa['sudo_rdm'] = ''

    val = Validator()
    if val.validateSudo() is False:
      # sudo is not set up for this host
      log.info('sudo is invalid')
      xa['sudo_verified'] = 'invalid'
    else:
      log.info('sudo is valid')
      xa['sudo_verified'] = 'valid'
      if val.validateSudo('lsof') is False:
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
          ce = 'collectionengine-linux-x86'
        elif "Sun" == os_type:
          ce = 'collectionengine-solaris-sparc'
          
        # if /etc/hba.conf does not exist, then CE is not deployed
        hba_conf_exists = helper.does_exist('/etc/hba.conf')
        if val.validateSudo(ce) or not hba_conf_exists:
          log.info(ce + ' found in sudo or /etc/hba.conf does not exist')
          # check for fcinfo on Sun required by SolarisFC.py ext
          if "Sun" == os_type and val.validateSudo('fcinfo') is False:
            log.info('fcinfo for SolarisFC.py discovery extension not found in sudo')
            xa['sudo_hba'] = 'invalid'
          elif "Linux" == os_type and is_virtual is False and helper.validateCommand('/sbin/powermt') and val.validateSudo('powermt') is False:
            log.info('/sbin/powermt for powermt.py discovery extension not found in sudo')
            xa['sudo_hba'] = 'invalid'
          else:
            xa['sudo_hba'] = 'valid'

          # make sure /etc/hba.conf exists to ensure CE deploy is valid
          if hba_conf_exists:
            # check collectionengine sudo path against CE directory
            paths = val.commandPath(ce)
            ce_path = sensorhelper.executeCommand('pwd').strip()
            # if CE is under /usr/local/bin, then use this path instead
            if helper.does_exist('/usr/local/bin/' + ce):
              ce_path = '/usr/local/bin'
            xa['sudo_hba_path'] = 'invalid'
            for path in paths:
              log.debug('Checking path ' + path + ' against ' + ce_path)
              log.debug('Split path ' + '/'.join(path.split('/')[:-1]))
              if '/'.join(path.split('/')[:-1]) == ce_path:
                xa['sudo_hba_path'] = 'valid'
            log.info('sudo hba (collectionengine) path is ' + str(xa['sudo_hba_path']))
        else:
          log.info(ce + ' not found in sudo')
          xa['sudo_hba'] = 'invalid'
        log.info('sudo hba (collectionengine) is ' + str(xa['sudo_hba']))
        
      # check for Linux specific
      if "Linux" == os_type:
        if val.validateSudo('dmidecode'):
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
            if val.validateSudo('sg_inq'):
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
                
    helper.setExtendedAttributes(computersystem, xa)
    log.info("sudo discovery extension ended")
  except:
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
    LogError(errMsg)
    result.warning(errMsg)

def usage():
    print """ \
usage: sudo.py [options]

   Define extended attributes

    Options:

    -u userid           User required to login to TADDM Server
                        Defaults to 'administrator'

    -p password         Password for TADDM Server user
                        Defaults to 'collation'

    -h                  print this message

    """

if __name__ == "__main__":
  try:
    opts, args = getopt.getopt(sys.argv[1:], 'u:p:', ['help'] )
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

  global userid
  userid = None
  global password
  password = None
  for o, a in opts:
    if o == "-u":
      userid = a
    elif o == "-p":
      password = a
    elif o in ("-h", "--help"):
      usage()
      sys.exit()

  create_ea = True
  try:
    # if this throws an error that we are local and creating EA
    sensorhelper.init(targets)
    create_ea = False
  except:
    pass
    
  if create_ea:
    import ext_attr_helper as ea
    # Import TADDM Pros library
    from com.collation.platform.util import Props

    #------------------------------------------------
    # Set Defaults...
    #------------------------------------------------
    if userid is None:
      userid = "administrator"

    if password is None:
      password = "collation"
    #
    # Initialize
    #
    api = ea.get_taddm_api(Props.getRmiBindHostname(), userid, password)
    attr_names = [ 'sudo_verified', 'sudo_lsof', 'sudo_dmidecode', 'sudo_hba', 'sudo_hba_path', 'sudo_rdm' ]
    for attr_name in attr_names:
      print 'Creating ' + attr_name + ' String EA on UnitaryComputerSystem'
      created = ea.createExtendedAttributes(api, attr_name, 'String', 'com.collation.platform.model.topology.sys.UnitaryComputerSystem')
      print ' Success: ' + str(created)
    api.close()
  else:
    main()