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
# USE FOLLOWING TO IMPORT HELPER IN YOUR SENSOR CODE
########################################################
## add extension-scripts to sys.path if not already there
#ext_path = coll_home + '/etc/templates/commands/extension-scripts'
#if ext_path not in sys.path:
#  sys.path.append(ext_path)

#import os
## when AnchorSensor copies compiled file *$py.class the $py is removed and this causes
## runtime errors on the remote anchor, so rename any *.class to *$py.class
#for root, dirs, files in os.walk(ext_path):
#  for filename in files:
#    if filename.endswith('.class') and not filename.endswith('$py.class'):
#      basename = filename.split('.')[0]
#      try:
#        os.rename(ext_path + '/' + filename, ext_path + '/' + basename + '$py.class')
#      except:
#        print 'ERROR: Unable to rename ' + filename + ' to ' + basename + '$py.class'
#        pass

## now import from extension-scripts
#import helper


########################################################
# Standard Jython/Python Library Imports
########################################################
import sys
import java
import re

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
sys.prefix = jython_home + "/Lib"

import sensorhelper

# Import the TADDM Java Libraries
from com.collation.platform.model.util.ea import ExtendedAttributesData

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
  print "OS Classname is:  " + str(class_name)
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

########################
# setExtendedAttributes Takes a CDM ModelObject and a python dictionary of name
#                       value pairs and sets the name value pairs as
#                       extended attributes for the ModelObject.  The values
#                       must be strings.  This feature
#                       requires TADDM 7.1 or higher.
#
#                       Parameters
#                               mo      CDM ModelObject
#                               exattrs python dictionary of name/value pairs.
#                                       name is extended attribute name
#                                       value is string
#
#                       Returns
#
#                       Exceptions
#                               IoException
########################
def setExtendedAttributes(mo,exattrs,category=None):
    ead = ExtendedAttributesData()
    # merge with existing if already set
    if mo.hasXA():
      ead = mo.getXA()
    if category:
       for name,value in exattrs.items():
        ead.addAttribute(category,name,value)
    else:
       for name,value in exattrs.items():
        ead.addAttribute(name,value)
    ead.attachTo(mo)

########################
# validateCommand Runs command -v on target
#
#                       Parameters
#                               cmd command name
#
#                       Returns
#                               True if command is valid
#                               False if command invalid
#
#                       Exceptions
#                               
########################
def validateCommand(cmd):
  try:
    print 'validating command = ' + cmd
    path = sensorhelper.executeCommand('command -v ' + cmd + ' 2>/dev/null')
    print 'path found = ' + path
    return True
  except:
    print 'command not found'
    return False
    
########################
# does_exist  Runs ls on target to see if file exists
#
#                       Parameters
#                               file  file to check
#
#                       Returns
#                               True if file exists
#                               False if file does not exist
#
#                       Exceptions
#                               
########################
def does_exist(file):
  try:
    print 'checking for accessible file = ' + file
    out = sensorhelper.executeCommand('ls ' + file + ' 2>/dev/null')
    print 'file found = ' + out
    return True
  except:
    print 'file not found'
    return False

########################
# is_exec  Runs test on target to see if file executable
#
#                       Parameters
#                               file  file to check
#
#                       Returns
#                               True if file executable
#                               False if file not executable
#
#                       Exceptions
#                               
########################
def is_exec(file):
  try:
    print 'checking for executable file = ' + file
    sensorhelper.executeCommand('test -x ' + file + ' 2>/dev/null')
    print 'file executable'
    return True
  except:
    print 'file not executable'
    return False

########################
# is_writable  Runs test on target to see if file/directory writable
#
#                       Parameters
#                               file  file/directory to check
#
#                       Returns
#                               True if file/directory writable
#                               False if file/directory not writable
#
#                       Exceptions
#                               
########################
def is_writable(file):
  try:
    print 'checking for writable file = ' + file
    sensorhelper.executeCommand('test -w ' + file + ' 2>/dev/null')
    print 'file writable'
    return True
  except:
    print 'file not writable'
    return False

########################
# is_vmware  Check if computersystem is vmware
#
#                       Parameters
#                               computersystem  discovered computersystem
#
#                       Returns
#                               True if vmware
#                               False if not vmware
#
#                       Exceptions
#                               
########################
def is_vmware(computersystem):
  is_vmware = False
  if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform'):
    is_vmware = True
  return is_vmware

def is_virtual(computersystem):
  is_virtual = True # assume virtual
  if computersystem.hasModel() and not 'virtual' in computersystem.getModel().lower():
    # model is set and does not contain 'virtual'
    if computersystem.hasVirtual():
      if not computersystem.getVirtual():
        is_virtual = False # virtual is set to False
    else:
      # virtual is not set and model does not contain 'virtual'
      is_virtual = False

  print 'Is server virtual? ' + str(is_virtual)
  
  return is_virtual

# get any previously discovered volumes from result
def get_volumes(result, log=None):
  # get any previously discovered volumes
  vols = {}
  ext_results = result.getExtendedResults()
  iter = ext_results.iterator()
  while iter.hasNext():
    ext_result = iter.next()
    class_name = get_class_name(ext_result)
    if re.search("FCVolume",class_name,re.I):
      if log:
        log.debug('Found existing FCVolume:' + str(ext_result))
      vols[ext_result.getName()] = ext_result
    elif re.search("SCSIVolume",class_name,re.I):
      vols[ext_result.getName()] = ext_result
      if log:
        log.debug('Found existing SCSIVolume:' + str(ext_result))
  return vols