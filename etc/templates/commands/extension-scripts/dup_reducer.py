############### Begin Standard Header - Do not add comments here ###############
# 
# File:     dup_reducer.py
# Version:  2.1
# Modified: 7/6/2018
# Build:    
# 
# Licensed Materials - Property of IBM
# 
# Restricted Materials of IBM
# 
# 5724-N55
# 
# (C) COPYRIGHT IBM CORP. 2007.  All Rights Reserved.
# 
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
# 
############################# End Standard Header ##############################
'''

SCRIPT OVERVIEW (Custom Server Extension)

Requirements:

    * It requires 'sensorhelper.py'
    * Requires TADDM 7.3.0+
    * Tested on TADDM 7.3.0.3, 7.3.0.4
    
    * This script can be executed by placing 
      SCRIPT: $COLLATION_HOME/etc/templates/commands/extension-scripts/dup_reducer.py
      in a Template file under etc/templates/commands

DESCRIPTION: dup_reducer.py -- This script is used to extend VM  
discovery by attempting to reduce duplicate server discovery. This is 
done by planting a tag file on the target system and ensuring that 
an OpenID is always updated with the value from the tag file. The host name of 
the target is also used to ensure that a moved VM with the same name does
not introduce duplicates.

Authors:  Mat Davis
           mdavis5@us.ibm.com

History:
   Version 2.1 -- 07/2018 -- Change location of tag files
   Version 2.0 -- 01/2018 -- Use OpenID instead of PMAC
   Version 0.1 -- 11/2011 -- Initial Version --

'''

import sys
import java

from java.lang import System
from java.lang import Thread
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

from com.collation.platform.model.util.openid import OpenId

import traceback
import string
import re
import jarray
import sensorhelper
import time

########################################################
# Some default GLOBAL Values (Typically these should be in ALL CAPS)
# Jython does not have booleans
########################################################
True = 1
False = 0

########################
# LogError      Error logger
########################
def LogError(msg):
    log.error(msg)
    result.warning(msg)
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    traceback.print_exc(ErrorTB)
    
########################
# LogDebug      Print routine for normalized messages in log
########################
def LogDebug(msg):
    '''
    Print Debug Message using debug logger (from sensorhelper)
    '''
    # assuming SCRIPT_NAME and template name are defined globally...
    # point of this is to create a consistent logging format to grep 
    # the trace out of
    log.debug(msg)

########################
# LogInfo Print routine for normalized messages in log
########################
def LogInfo(msg):
    '''
    Print INFO level Message using info logger (from sensorhelper)
    '''
    # assuming SCRIPT_NAME and template name are defined globally...
    # point of this is to create a consistent logging format to grep 
    # the trace out of
    log.info(msg)

def tag_server(server):
    # also check to see if server is virtual
    tag = None
    tagfile = '.discoverytag-' + server.getName()
    LogDebug("Using tag file name " + tagfile)

    try:
        cmd = 'cat /tmp/' + tagfile
        # different command/location for Windows
        if sensorhelper.targetIsWindows():
            cmd = 'type C:\\' + tagfile # put in C:\ you can't use env variables here
        # look for existing tag file under in home directory
        tag = sensorhelper.executeCommand(cmd)
        # if we get a result, set OpenID
        if tag:
            LogDebug('Setting OpenID using ' + tag.strip() + ' and ' + server.getName())
            server.setOpenId(OpenId(server).addId('tag', tag.strip()).addId('name', None))
        else:
            # use try/except here because if .discoverytag doesn't exist an error is thrown
            raise Exception()
    except:
        LogInfo(tagfile + ' is not present or empty')
        # use current time stamp (in millis) with the DiscoverWorker thread number appended to ensure uniqueness
        tag = str(System.currentTimeMillis()) + '-' + Thread.currentThread().getName().split('-')[1]
        LogDebug('setting ' + tagfile + ' to ' + tag)
        try:
            cmd = 'echo ' + tag + ' > /tmp/' + tagfile
            if sensorhelper.targetIsWindows():
                cmd = 'echo ' + tag + ' > C:\\' + tagfile
            # put new calculated value back out on the server
            sensorhelper.executeCommand(cmd)
            LogDebug('setting OpenID using ' + tag.strip() + ' and ' + server.getName())
            server.setOpenId(OpenId(server).addId('tag', tag).addId('name', None))
        except:
            LogError("Error occurred writing to .discoverytag, duplicate reducer discovery extension failed")

##############################################################################
#main
##############################################################################

(os_handle,result,server,seed,log) = sensorhelper.init(targets)

LogInfo('Duplicate Reducer 2.0 discovery extension started')

try:
    # check if target is not marked as virtual and model starts with 'VMware'
    if not (server.hasVirtual() and server.getVirtual()) and server.hasModel() and server.getModel().startswith('VMware'):
        LogDebug("Setting virtual to true")
        server.setVirtual(True)

    # check if target model is 'VMware Virtual Platform' but manufacturer is not set
    if server.hasModel() and server.getModel().startswith('VMware Virtual Platform') and not server.hasManufacturer():
        LogDebug("Setting manufacturer to VMware, Inc.")
        server.setManufacturer('VMware, Inc.')

    # should check to see if name is discovered, it's too dangerous to proceed without name
    if server.hasName():
        if server.hasVirtual() and server.getVirtual():
            tag_server(server)
        elif server.hasManufacturer() and server.hasModel() and not server.hasSerialNumber():
            LogDebug('Physical server is missing serial number')
        else:
            LogDebug('Server is not virtual, skipping tag file')
    else:
        log.warning('Name is not discovered, duplicate reducer discovery extension requires name discovery')
        result.warning('Name is not discovered, duplicate reducer discovery extension requires name discovery')
except:
    LogError("unexpected exception during duplicate reducer extended discovery")