############### Begin Standard Header - Do not add comments here ###############
# 
# File:     swg_csx_template.py
# Version:  2.0
# Modified: 4/14/2009
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
ScheduledTasks (Custom Server Extension)

Requirements:

Author:  Mat Davis
	 mdavis5@us.ibm.com


History:  

	original version    8/2013    Mat Davis

Main comment block, Beginning of Tivoli Dep Jython Script
'''

# Standard Library Imports

import sys
import java

from java.lang import System

# from Java [additional imports - not sure why]...

from java.util import Properties

from java.io import FileInputStream
from java.io import FileNotFoundException

# Set the Path information

coll_home = System.getProperty("com.collation.home")
System.setProperty("jython.home",coll_home + "/external/jython-2.1")
System.setProperty("python.home",coll_home + "/external/jython-2.1")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import string
import traceback
#import re
#import jarray
#import StringIO
#import zlib

#  Local App Imports
import sensorhelper

#----------------------------------------------------------------------------------
# Define some CONSTANTS, print some info
#-----------------------------------------------------------------------------------

#----------------------------------------------------------------------------------
# Define the Functions
#-----------------------------------------------------------------------------------

########################
# LogError      Error logger
########################
def LogError(msg):
	'''
	Print Error Message using Error Logger with traceback information
	'''
	log.error(msg)
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

def load_property_file(filename):

    propfile = Properties()

    try:
        fin = FileInputStream(filename)
        propfile.load(fin)
        fin.close()
        return propfile
    except FileNotFoundException:
        LogError("File Not Found" + filename)
        sys.exit(1)
    except:
        LogError("Could not open Properties File" + filename)
        sys.exit(1)

#---------------------------------------------------------------------------------
# MAIN
#---------------------------------------------------------------------------------

# The first thing we need to do is get the Objects that are passed to a sensor
(os_handle,result,server,seed,log) = sensorhelper.init(targets)

# os_handle  -->  Os handle object to target system
# result     -->  Results Object
# server     -->  AppServer or ComputerSystem Object that is discovered
# seed       -->  seed object which contains information that was found prior
#                 to this CSX running
# Logger     -->  Object to write to sensor log

# Now we can use these objects to add MORE information to the AppServer object
# that has already been found.

LogInfo(" ****** STARTING ScheduledTasks.py ******* ")

LogInfo("Using sensorhelper version: " + str(sensorhelper.getVersion()))

properties_file = coll_home + "/etc/templates/scheduled_tasks.properties"
sch_task_dict = {}
LogInfo("Using the properties file: " + str(properties_file))

try:
	task_dict = load_property_file(properties_file)
	taskList = task_dict['forcedTaskList'].split(';')
	LogDebug('taskList:' + str(taskList))
	output = sensorhelper.executeCommand('SCHTASKS /Query /FO CSV /V')

	firstFolder = 0
	for line in output.splitlines():
		columns = line.split('","')
		if len(columns) > 1:
			hostName = columns[0][1:]
			if hostName == 'HostName':
				if firstFolder:
					break
				else:
					firstFolder = 1
					continue
			task2run = columns[8]
			taskName = columns[1]
			status = columns[3]
			for task in taskList:
				# check if the executable contains the task to force and make sure it is enabled
				if task2run.find(task) != -1:
					if status == 'Disabled':
						LogInfo('Task ' + task + ' found but it is disabled, skipping discovery')
						continue
					LogInfo('Processing:' + taskName + ' ' + task2run)
					appserver = sensorhelper.newModelObject('cdm:app.AppServer')
					appserver.setKeyName('AppServer')
					appserver.setHost(server)
					appserver.setObjectType(task)
					# build bind address
					bindaddr = sensorhelper.newModelObject('cdm:net.CustomBindAddress')
					bindaddr.setPortNumber(0)
					bindaddr.setPath('ForcedServer.' + task)
					# build IP for bind address
					ipaddr = sensorhelper.newModelObject('cdm:net.IpV4Address')
					ipaddr.setStringNotation(str(seed))
					bindaddr.setPrimaryIpAddress(ipaddr)
					bindaddr.setIpAddress(ipaddr)
					appserver.setPrimarySAP(bindaddr)
					appserver.setLabel(server.getFqdn() + ':ForcedServer.' + task)
					# build process pool
					procpool = sensorhelper.newModelObject('cdm:app.ProcessPool')
					procpool.setParent(appserver)
					procpool.setName('ProcessPool')
					procpool.setCmdLine(task2run)
					appserver.setProcessPools(sensorhelper.getArray([procpool,], 'cdm:app.ProcessPool'))
					
					result.addExtendedResult(appserver)
					# remove task from taskList so we don't process again
					taskList.remove(task)
					break
except:
	LogError("Error occurred.")
