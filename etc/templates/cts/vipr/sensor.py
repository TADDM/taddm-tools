#!/usr/bin/env ../../../../bin/jython_coll_253

from com.collation.platform.security.auth import AuthManager
from com.collation.platform.security.auth import EMCViprSRMAuth
from com.collation.discover.agent import AgentException
from javax.net.ssl import SSLContext
from javax.net.ssl import HttpsURLConnection
from java.net import *
from javax.xml.bind import DatatypeConverter
from java.lang import StringBuilder
from java.nio.charset import StandardCharsets
from java.io import *
from java.util import *
from java.security import *

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

########################################################
# Some default GLOBAL Values (Typically these should be in ALL CAPS)
# Jython does not have booleans
########################################################
True = 1
False = 0

testmode = False

from javax import net

class TrustManager(net.ssl.X509TrustManager):
    def getAcceptedIssuers(*args):
        return None
    def checkServerTrusted(*args):
        pass
    def checkClientTrusted(*args):
        pass

class MyHostnameVerify(net.ssl.HostnameVerifier):
    def verify(*args):
        return True

# initialize HTTPS
sc = SSLContext.getInstance("TLSv1.2")

sc.init(None, [ TrustManager() ], None)
HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory())
HttpsURLConnection.setDefaultHostnameVerifier(MyHostnameVerify())

def getConnection(url):
  siteURL = URL(url)
  siteConnection = siteURL.openConnection()
  userpassword = java.lang.String(java.lang.StringBuilder().append(username).append(':').append(password).toString())
  encodedUserPassword = DatatypeConverter.printBase64Binary(userpassword.getBytes(StandardCharsets.UTF_8))
  siteConnection.setRequestProperty("Authorization", java.lang.StringBuilder().append("Basic ").append(encodedUserPassword).toString())
  siteConnection.setConnectTimeout(30000)
  siteConnection.setReadTimeout(30000)
  siteConnection.setRequestMethod("GET")
  siteConnection.setUseCaches(False)
  siteConnection.setDoInput(True)
  siteConnection.setDoOutput(True)

  return siteConnection

def getVPlexPorts(host, port, device):
  url_array = ('filter=parttype%3D%27Port%27%26devtype%3D%27VirtualStorage%27%26%21iftype%3D%27null%27%26device%3D'+device+
               '&fields=iftype,maxspeed,director,portwwn,part,vendor,portstat,nodewwn')
  log.debug('url_array=' + url_array)
  url = 'https://' + host + ':' + str(port) + '/APG-REST/metrics/properties/values?' + url_array
  if testmode:
    url = 'https://' + host + ':' + str(port) + '/rest/discovery/status'
  return getConnection(url)

def getVPlexConnection(host, port):
  url_array = 'filter=devtype%3D%27VirtualStorage%27&fields=serialnb,model,vendor,device'
  log.debug('url_array=' + url_array)
  url = 'https://' + host + ':' + str(port) + '/APG-REST/metrics/properties/values?' + url_array
  if testmode:
    url = 'https://' + host + ':' + str(port) + '/rest/discovery/status'
  return getConnection(url)

def getResponse(conn):
  sb = StringBuilder()
  
  try:
    br = BufferedReader(InputStreamReader(conn.getInputStream()))
    line = br.readLine()
    while line:
      sb.append(line)
      line = br.readLine()
  except Exception, e:
    log.error('Exception occurred during InputStream reading')

  return sb.toString()

def getVPlexOutput():
  f = open(coll_home + '/etc/templates/cts/vipr/vplex.json')
  return f.read()

def getVPlexPortsOutput():
  f = open(coll_home + '/etc/templates/cts/vipr/vplex-ports.json')
  return f.read()
  
# ctsSeed is CustomTemplateSensorSeed with following methods
# Map<String, Object> getResultMap()
# CTSTemplate getTemplate()
# Tuple<String, Object> getSeedInitiator()
# String getEngineId()
(ctsResult,ctsSeed,log) = sensorhelper.init(targets)

try:
  # if simplejson has not been installed on top of 2.5.3 this will throw ImportError
  # and we can't continue unless simplejson is installed
  import simplejson as json
  
  #log.debug(''.join(list(targets)))

  #log.debug(targets.get('cts'))
  #log.debug('ctsSeed:'+ctsSeed.toString())

  # IpAddress CI
  ipAddress = ctsSeed.getIpAddress()
  # string IP
  ip = ipAddress.getStringNotation()

  authList = AuthManager.getAuth(java.lang.Class.forName("com.collation.platform.security.auth.EMCViprSRMAuth"), ipAddress)

  if authList.size() <= 0:
    log.error('No EMC ViPR SRM access list is available')
    raise AgentException('No EMC ViPR SRM access list is available')

  discovered = False
  authIterator = authList.iterator()

  while (not discovered and authIterator.hasNext()):

      auth = authIterator.next()
      
      log.info("CTS Sensor script running for ViPR")
      #  get value passed by result matcher
      portList = ctsSeed.getSeedInitiator().getValue()
      if 9431 in portList:
        # if port 9431 is in the list then we are looking at a TADDM server and are in testmode
        log.info('Found port 9431, entering testmode')
        testmode = True
      
      port = 58443 # default REST API port for ViPR
      testURL = '/APG-REST/metrics/properties'
      if testmode:
        port = 9431 # test
        testURL = '/rest/discovery/status' # test
      username = auth.getUserName()
      password = auth.getPassword()

      log.info('Trying to connect with Port:' + str(port) + ' Username:' + username + ' Password:XXXX')

      conn = getConnection('https://' + ip + ':' + str(port) + testURL)
      
      responseCode = conn.getResponseCode()
      log.info(conn.getURL().toString() + ' ### ResponseCode() == ' + str(responseCode))
      if responseCode == 200:
        conn.disconnect()
        try:
          conn = getVPlexConnection(ip, str(port))
          
          responseCode = conn.getResponseCode()
          log.info(conn.getURL().toString() + ' ### ResponseCode() == ' + str(responseCode))
          if responseCode == 200:
            output = getResponse(conn)
            if testmode:
              output = getVPlexOutput()
          else:
            log.warning('Unable to make a REST connection to EMC ViPR SRM using user name ' + username + '. Caused by ' + conn.getResponseMessage())
            log.error('Problem in URLConnection : ' + conn.getURL().toString())
            log.error('### Response code for REST request: ' + str(conn.getResponseCode()))
              
          conn.disconnect()
          
          log.debug('### Response for getStorageSubSystem request:  -' + output)
          if output:
            # parse json
            obj = json.loads(output)
            vplexes = obj['values']
            # iterate over all VPlex
            for vplex in vplexes:
              serialnb = vplex['serialnb']
              model = vplex['model']
              vendor = vplex['vendor']
              device = vplex['device']
              devdesc = vplex['devdesc']
              sss = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
              # add storage function
              func = sensorhelper.newModelObject('cdm:storage.StorageControllerFunction')
              func.setParent(sss)
              func.setName("Storage")
              sss.setFunctions(sensorhelper.getArray([func],'cdm:sys.Function'))
              if devdesc:
                sss.setROMVersion(devdesc)
              if serialnb:
                sss.setSerialNumber(serialnb)
              if model:
                sss.setModel(model)
              if device:
                # ViPR sensor sets Fqdn instead of name during array discovery
                sss.setName(device)
                sss.setAnsiT10Id(device)
              # this might be better set to default StorageDevice in case topo agents look for that
              sss.setType('VirtualStorage')
              if vendor:
                sss.setManufacturer(vendor)
              sss.setContextIp(ip)
              
              # discover ports
              conn = getVPlexPorts(ip, str(port), device)
              responseCode = conn.getResponseCode()
              log.info(conn.getURL().toString() + ' ### ResponseCode() == ' + str(responseCode))
              if responseCode == 200:
                portOutput = getResponse(conn)
                if testmode:
                  portOutput = getVPlexPortsOutput()
              else:
                log.warning('Unable to make a REST connection to EMC ViPR SRM using user name ' + username + '. Caused by ' + conn.getResponseMessage())
                log.error('Problem in URLConnection : ' + conn.getURL().toString())
                log.error('### Response code for REST request: ' + str(conn.getResponseCode()))
                
              conn.disconnect()
              
              # TODO collect FCPorts and set on SSS
              if portOutput:
                # parse json
                obj = json.loads(portOutput)
                ports = obj['values']
                fcports = []
                # iterate over all VPlex
                for port in ports:
                  log.debug('port:' + str(port))
                  iftype = port['iftype']
                  maxspeed = port['maxspeed']
                  director = port['director']
                  portwwn = port['portwwn']
                  part = port['part']
                  vendor = port['vendor']
                  portstat = port['portstat']
                  nodewwn = port['nodewwn']
                  
                  fcport = sensorhelper.newModelObject('cdm:dev.FCPort')
                  fcport.setParent(sss)
                  fcport.setPermanentAddress(portwwn)
                  speed = float(maxspeed) * 1024 * 1024 * 1024
                  fcport.setSpeed(long(speed))
                  fcport.setDescription(director+':'+iftype)
                  if portstat == 'up':
                    fcport.setStatus(3)
                  fcports.append(fcport)
                sss.setFCPorts(sensorhelper.getArray(fcports,'cdm:dev.FCPort'))
              ctsResult.addExtendedResult(sss)
              discovered = True
          else:
            log.debug('### VPlex output is null')
         
        except Exception, e:
          log.warning('Problem occurs while processing the VPlex data ' + str(e))
          ctsResult.warning('Problem occurs while processing the VPlex data')
      elif responseCode == 301 or responseCode == 302:
        log.warning('### URL Redirection is ON')
        log.warning('### Response code for REST request: ' + str(responseCode) + ' Message: ' + siteConnection.getResponseMessage())
        log.warning('Connection was not established with given parameters : user =' + username + ' for host =' + ip + ' with port =' + str(port))
        siteConnection.disconnect()
      else:
        log.error('### Response code for REST request: ' + str(responseCode) + ' Message: ' + siteConnection.getResponseMessage())
        log.warning('Connection was not established with given parameters : user =' + username + ' for host =' + ip + ' with port =' + str(port))
        siteConnection.disconnect()  
except ImportError:
  log.error('Add simplejson directory to ' + jython_home + '/Lib')
  ctsResult.warning('simplejson library missing, install in ' + jython_home + '/Lib')