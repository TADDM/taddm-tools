#!/usr/bin/env ../../../../bin/jython_coll_253

# Initialising the environment
import sys
import java

from java.lang import System
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import traceback

# Importing sensorhelper
import sensorhelper

#  Initialising script input
(resultMap,returnList,log) = sensorhelper.init(targets)
log.debug("REST CTS result matcher script running")

try:
    log.debug("resultMap" + str(resultMap))
    #  get list of ports discovered
    log.debug('grabbing portList')
    portList = resultMap['portList']
    log.debug('Looking for port')
    if 9431 in portList:
      log.debug('Found port 9431')
      returnList.add("ports", portList)
    else:
      log.debug('Port 9431 not found')
except Exception, e:
    log.error("Error occurred " + str(e))
