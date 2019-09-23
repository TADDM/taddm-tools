
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

def validateSudo(cmd=None):
  try:
    if cmd:
      output = sensorhelper.executeCommand('sudo -l 2>&1')
      # look for line containing (root) NOPASSWD: .*cmd.*
      regex = re.compile('\(root\) NOPASSWD: .*' + cmd + '.*', re.MULTILINE)
      if regex.search(output):
        return True
      else:
        return False
    else:
      output = sensorhelper.executeCommand('sudo -v 2>&1;echo -n')
      global requiretty
      if re.search('.*sudo: sorry, you must have a tty to run sudo.*', output):
        requiretty = True
        return False
      elif re.search('.*Sorry, user .* may not run sudo on .*\..*', output):
        return False
      else:
        log.debug('match not found')
        return True
    return True
  except:
    return False

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

try:

  log.info("sudo discovery extension started (written by Mat Davis - mdavis5@us.ibm.com)")

  xa = {}
  requiretty = None
  if validateSudo() is False:
    # sudo is not set up for this host
    log.info('sudo is invalid')
    xa['sudo_verified'] = 'invalid'
  else:
    requiretty = False
    log.info('sudo is valid')
    xa['sudo_verified'] = 'valid'
    if validateSudo('lsof') is False:
      log.info('sudo lsof is invalid')
      xa['sudo_lsof'] = 'invalid'
    else:
      log.info('sudo lsof is valid')
      xa['sudo_lsof'] = 'valid'
  if requiretty is True:
    log.info('requiretty invalid')
    xa['sudo_requiretty'] = 'invalid'
  elif requiretty is False:
    log.info('requiretty is valid')
    xa['sudo_requiretty'] = 'valid'

  sensorhelper.setExtendedAttributes(computersystem, xa)
  log.info("sudo discovery extension ended")
except:
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  errMsg = 'Unexpected error occurred during discover: ' + str(ErrorValue)
  LogError(errMsg)
  result.warning(errMsg)