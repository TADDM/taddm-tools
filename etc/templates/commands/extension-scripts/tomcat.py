############### Begin Standard Header - Do not add comments here ############### 
# 
# File:     %W% 
# Version:  %I% 
# Modified: %G% %U% 
# Build:    %R% %L% 
# 
# Licensed Materials - Property of IBM 
# 
# 5724-N55 
# 
# (C) COPYRIGHT IBM CORP. 2007.  All Rights Reserved. 
# 
# US Government Users Restricted Rights - Use, duplication or 
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp. 
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

coll_home = System.getProperty("com.collation.home") 
  
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

######################## 
# LogError      Error logger 
######################## 
def LogError(msg): 
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  log.error(msg + '\n' + str(ErrorValue))
  log.error('traceback:' + str(traceback.format_tb(ErrorTB)))
  
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

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, appserver, seed, log, env) = sensorhelper.init(targets)

try:

  args = sensorhelper.splitArgs(seed.getCmdLine())
  if args is not None:
    if 'java' in args[0]:
      java_cmd = args[0].replace('"', '')
      if ' ' in java_cmd:
        java_path = '\\'.join(java_cmd.split('\\')[:-1])
        if java_path == '':
          java_cmd = 'java'
        else:
          # add java to path and execute java
          java_cmd = 'cd "' + java_path + '" & .\\java'
      log.info("Setting java command = " + java_cmd)
    next = False
    for t in args[1:]:
      LogDebug('Looking at argument: ' + t)
      if t.find("-Dcatalina.home=") != -1 or next:
        LogDebug('Found argument: ' + t)
        if t == '-Dcatalina.home=':
          next = True # Windows and the value is quoted, the next arg is what is needed
          continue
        if next:
          catalina_home = t
          next = False
        else:
          catalina_home = t.split("=")[1]
        catalina_home = catalina_home.replace('"', '')
        log.info("Catalina Home from command line = " + catalina_home)
      elif t.find("-Djava.library.path") and not java_cmd:
        LogDebug('Found argument: ' + t)
        java_cmd = 'cd "' + t.replace('"', '').split("=")[1] + '" & .\java'
        log.info("Setting java command = " + java_cmd)

    slash = '/'
    if sensorhelper.targetIsWindows(os_handle):
      slash = '\\'
    server_info = sensorhelper.executeCommand(java_cmd + ' -cp ' +'"'+catalina_home + slash+'lib'+slash+'catalina.jar" org.apache.catalina.util.ServerInfo')
    version = re.findall("^Server number:.*", server_info ,re.MULTILINE)[0].split()[2].strip()
    log.info('Setting productVersion to ' + version)
    appserver.setVendorName('The Apache Group')
    appserver.setProductName('Tomcat')
    appserver.setProductVersion(version)
except:
  #Something failed and threw an exception.  Call the error logger 
  #so that the stack trace gets logged 
  LogError("unexpected exception discovering Tomcat")

