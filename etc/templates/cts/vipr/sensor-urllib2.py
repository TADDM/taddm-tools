from com.collation.platform.security.auth import AuthManager;
from com.collation.platform.security.auth import EMCViprSRMAuth;
from com.collation.discover.agent import AgentException;

import sys
import java
import time

from java.lang import System
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import traceback
import sensorhelper

import urllib2 # for HTTP REST API

########################################################
# Some default GLOBAL Values (Typically these should be in ALL CAPS)
# Jython does not have booleans
########################################################
True = 1
False = 0

# ctsSeed is CustomTemplateSensorSeed with following methods
# Map<String, Object> getResultMap()
# CTSTemplate getTemplate()
# Tuple<String, Object> getSeedInitiator()
# String getEngineId()
(ctsResult,ctsSeed,log) = sensorhelper.init(targets)

log.debug(''.join(list(targets)))

#log.debug(targets.get('cts'))
log.debug('ctsSeed:'+ctsSeed.toString())

authList = AuthManager.getAuth(java.lang.Class.forName("com.collation.platform.security.auth.EMCViprSRMAuth"), ctsSeed.getIpAddress());

if authList.size() <= 0:
    log.error('No EMC ViPR SRM access list is available')
    raise AgentException('No EMC ViPR SRM access list is available')

authIterator = authList.iterator()
auth = authIterator.next()

log.debug("CTS Sensor script running")
#  get value passed by result matcher
server = ctsSeed.getSeedInitiator().getValue()

#try: 

port = '4443' # default REST API port for ViPR SRM
port = '9430' # test
testURL = '/APG-REST/metrics/properties'
testURL = '/rest/discovery/status' # test
theurl = 'http://' + server.getContextIp() + ':' + port + testURL
username = auth.getUserName()
password = auth.getPassword()

log.debug(theurl)
log.debug(username + ' ' + password)

# Note: SSL is not included in the Python 2.5.3 build for TADDM, which means
# we can't use https URLs with the Python urllib2 module. We will use Java 
# instead of Python for this reason.

passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
# this creates a password manager
passman.add_password(None, theurl, username, password)
# because we have put None at the start it will always
# use this username/password combination for  urls
# for which `theurl` is a super-url

authhandler = urllib2.HTTPBasicAuthHandler(passman)
# create the AuthHandler

opener = urllib2.build_opener(authhandler)

urllib2.install_opener(opener)
# All calls to urllib2.urlopen will now use our handler
# Make sure not to include the protocol in with the URL, or
# HTTPPasswordMgrWithDefaultRealm will be very confused.
# You must (of course) use it when fetching the page though.

log.debug('opening URL')
response = urllib2.urlopen(theurl+'?feed=json')
# authentication is now handled automatically for us
log.debug('response code:' + str(response.code))
log.debug(response.read())

#except Exception, e:
#    log.error("Sensor failed " + str(e))

# return resulting model object
#ctsResult.addExtendedResult(server)
