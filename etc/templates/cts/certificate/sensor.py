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
import os
import java
import jarray

from java.lang import System
from java.lang import Class
from java.lang import Runtime
from com.collation.platform.util import ModelFactory
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/external/jython-2.1")
System.setProperty("python.home",coll_home + "/external/jython-2.1")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import sensorhelper

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


(ctsResult,ctsSeed,log) = sensorhelper.init(targets)  # @UndefinedVariable

initValue = ctsSeed.getSeedInitiator().getValue()
computerSystem = initValue.get('computerSystem')

configFiles = []
if computerSystem.hasConfigContents():
	configFiles.extend(computerSystem.getConfigContents())
	
global type
global bits
global notValidBefore
global notValidAfter
os.system('nmap -p 443 -Pn -n -T5 --datadir=/usr/share/nmap/scripts --script=ssl-cert ' + computerSystem.getContextIp() + " > /tmp/cert_" + computerSystem.getContextIp())
file = open('/tmp/cert_'+computerSystem.getContextIp())
for character in file.readlines():
	if character.find("Public Key type") != -1:
		type = character.split(':')[1].strip()
	if character.find("Public Key bits") != -1:
		bits = character.split(':')[1].strip()
	if character.find("Not valid before") != -1:
		notValidBefore = character.split(':',1)[1].strip()
	if character.find("Not valid after") != -1:
		notValidAfter = character.split(':',1)[1].strip()


os.remove('/tmp/cert_'+computerSystem.getContextIp())

try:
	cf = sensorhelper.newModelObject('cdm:app.CertificateFile')
	cf.setURI("certificate://" + computerSystem.getContextIp() + "/CertList")

	jmap=java.util.HashMap()
	jmap.put("type",type)
	jmap.put("bits",bits)
	jmap.put("Not Valid Before",notValidBefore)
	jmap.put("Not Valid After",notValidAfter)
	bos=java.io.ByteArrayOutputStream()
	oos=java.io.ObjectOutputStream(bos)
	oos.writeObject(jmap)
	oos.flush()
	data=bos.toByteArray()
	oos.close()
	bos.close()
	cf.setExtendedAttributes(data)

	configFiles.append(cf)

	cf_array = jarray.array(configFiles, Class.forName("com.collation.platform.model.topology.core.LogicalContent"))
	computerSystem.setConfigContents(cf_array)

	ctsResult.addExtendedResult(computerSystem)
except NameError:
	LogDebug("No certificate information found")
