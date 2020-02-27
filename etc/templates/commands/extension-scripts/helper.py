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