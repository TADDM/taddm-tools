############### Begin Standard Header - Do not add comments here ###############
#
# Licensed Materials - Property of IBM
#
# Restricted Materials of IBM
#
# 5724-N55
#
# (C) COPYRIGHT IBM CORP. 2013.  All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
############################# End Standard Header ##############################

import sys

from java.lang import System
from java.util import HashMap
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/external/jython-2.1")
System.setProperty("python.home",coll_home + "/external/jython-2.1")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import sensorhelper

(resultMap,returnList,log) = sensorhelper.init(targets)  

log.error("CTS result matcher script running")

try:
    initValue = HashMap()
    print resultMap
    initValue.put('computerSystem', resultMap['computerSystem'])

    returnList.add(resultMap['computerSystem'].getName(), initValue)
    
except:
	print sys.exc_info()[0]