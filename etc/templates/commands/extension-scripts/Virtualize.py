############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# Virtualize.py
#
# DESCRIPTION: Sets virtual attribute to true if sensor detects that it is VMware. For some reason
#   the default sensor behavior doesn't do this.
#
# Authors:  Mat Davis
#			mdavis5@us.ibm.com
#
# History:
#    Version 0.5 -- 3/13 -- Initial Version --
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
System.setProperty("jython.home",coll_home + "/external/jython-2.1")
System.setProperty("python.home",coll_home + "/external/jython-2.1")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

########################################################
# More Standard Jython/Python Library Imports
########################################################
import traceback

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

log.info("Virtualize discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

# check if target is not marked as virtual and model starts with 'VMware'
if not (computersystem.hasVirtual() and computersystem.getVirtual()) and computersystem.hasModel() and computersystem.getModel().startswith('VMware'):
    log.debug("Setting virtual to true")
    computersystem.setVirtual(True)

# check if target model is 'VMware Virtual Platform' but manufacturer is not set
if computersystem.hasModel() and computersystem.getModel().startswith('VMware Virtual Platform') and not computersystem.hasManufacturer():
    log.debug("Setting manufacturer to VMware, Inc.")
    computersystem.setManufacturer('VMware, Inc.')
    
if computersystem.hasUUID() and not computersystem.hasSystemBoardUUID():
    uuid = computersystem.getUUID().lower()
    log.debug('Setting systemBoardUUID to ' + uuid)
    computersystem.setSystemBoardUUID(uuid)
    
log.info("Virtualize discovery extension ended.")