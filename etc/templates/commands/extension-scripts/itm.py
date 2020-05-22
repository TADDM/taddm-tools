############### Begin Standard Header - Do not add comments here ###############
# 
# File:     itm.py
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
import sensorhelper

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

##############################################################################
#main
##############################################################################

(os_handle, result, appserver, seed, log, env) = sensorhelper.init(targets)

LogInfo('ITM discovery extension started')

try:
  if appserver.hasPrimarySAP():
    ba = appserver.getPrimarySAP()
    if ba.hasPortNumber() and not ba.getPortNumber == 0:
      # do not use ipAddress because it's often set to 127.0.0.1
      if ba.hasIpAddress():
        ip = ba.getIpAddress()
        if appserver.hasProcessPools():
          pp = appserver.getProcessPools()[0]
          if pp.hasRuntimeProcesses():
            rtp = pp.getRuntimeProcesses()[0]
            if rtp.hasCmdLine():
              LogInfo('Setting OpenId to ip=' + ip.getStringNotation() + ' path=' + rtp.getCmdLine())
              # feeding in CI to OpenId() will set attribute from CI if None used
              appserver.setOpenId(OpenId().addId('ip', ip.getStringNotation()).addId('path', rtp.getCmdLine()))
except:
  LogError("unexpected exception during ITM extended discovery")