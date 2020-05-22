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
#    Version 0.1 -- 01/2020   -- Initial Version --
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

# add sensor-tools to sys.path if not already there
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
  def __init__(self):
    pass
    
  def validateCommand(self, cmd):
    try:
      log.info('validating command = ' + cmd)
      path = sensorhelper.executeCommand('command -v ' + cmd + ' 2>/dev/null')
      log.info('path found = ' + path)
      return True
    except:
      log.info('command not found')
      return False

def main():
  ##########################################################
  # Main
  # Setup the various objects required for the extension
  ##########################################################
  global log
  (os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)
  
  try:

    log.info("commands discovery extension started (written by Mat Davis - mdavis5@us.ibm.com)")

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
    xa['cmd_lsof'] = ''

    val = Validator()
      
    os_type = get_os_type(os_handle)
    if "Sun" == os_type:
      if val.validateCommand('lsof'):
        xa['cmd_lsof'] = 'valid'
      else:
        xa['cmd_lsof'] = 'invalid'
      log.info('command lsof is ' + str(xa['cmd_lsof']))
    
    helper.setExtendedAttributes(computersystem, xa)
    
    log.info("commands discovery extension ended")
  except:
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
    LogError(errMsg)
    result.warning(errMsg)

def usage():
    print """ \
usage: commands.py [options]

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
    attr_names = [ 'cmd_lsof' ]
    for attr_name in attr_names:
      print 'Creating ' + attr_name + ' String EA on UnitaryComputerSystem'
      created = ea.createExtendedAttributes(api, attr_name, 'String', 'com.collation.platform.model.topology.sys.UnitaryComputerSystem')
      print ' Success: ' + str(created)
    api.close()
  else:
    main()