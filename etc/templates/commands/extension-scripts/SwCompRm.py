############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# SwCompRm.py
#
# DESCRIPTION: Removes SoftwareComponent components from computer systems.
#
# Authors:  Mat Davis
#			mdavis5@us.ibm.com
#
# History:
#    Version 0.5 -- 3/13/15   -- Initial Version --
#    Version 0.6 -- 10/30/15  -- Made generic for other CS types
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

# this is for default (old) Python v2.1
#System.setProperty("jython.home",coll_home + "/external/jython-2.1")
#System.setProperty("python.home",coll_home + "/external/jython-2.1")

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

log.info("SoftwareComponent Removal discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

# check if target has software components
if computersystem.hasOSRunning() and computersystem.getOSRunning().hasSoftwareComponents():
    log.debug("Removing software components")
    computersystem.getOSRunning().setSoftwareComponents(sensorhelper.getArray([],'cdm:sys.SoftwareComponent'))
else:
    log.debug("No software components found to remove.")
    
    
log.info("SoftwareComponent Removal discovery extension ended.")