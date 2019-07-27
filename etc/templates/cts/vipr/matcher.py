#!/usr/bin/env ../../../../bin/jython_coll_253

# Initialising the environment
import sys
import java

from java.lang import System
from java.util import HashMap
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
  #  get arrays discovered
  arrays = resultMap['arrays']
  #  get switches discovered
  switches = resultMap['switches']

  results = HashMap()
  if len(arrays) > 0:
    results.put('arrays', arrays)
  else:
    log.debug("No arrays found in resultMap")

  if len(switches) > 0:
    results.put('switches', switches)
  else:
    log.debug("No switches found in resultMap")

  if results.size() > 0:
    returnList.add("devices", results)
except Exception, e:
  log.error("Error occurred " + str(e))
