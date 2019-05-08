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

try:
  import simplejson as json
except ImportError:
  print 'Add simplejson directory to ' + jython_home + '/Lib'
  raise

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
  
# ctsSeed is CustomTemplateSensorSeed with following methods
# Map<String, Object> getResultMap()
# CTSTemplate getTemplate()
# Tuple<String, Object> getSeedInitiator()
# String getEngineId()
(ctsResult,ctsSeed,log) = sensorhelper.init(targets)

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
          log.warning('Unable to make a REST connection to EMC ViPR SRM using user name ' + username + '. Caused by ' + siteConnection.getResponseMessage())
          log.error('Problem in URLConnection : ' + conn.getURL().toString())
          log.error('### Response code for REST request: ' + str(conn.getResponseCode()))
            
        conn.disconnect()
        
        log.debug('### Response for getStorageSubSystem request:  -' + output)
        if output:
          # parse json
          obj = json.loads(output)
          values = obj['values']
          # iterate over all VPlex
          for value in values:
            serialnb = value['serialnb']
            model = value['model']
            vendor = value['vendor']
            device = value['device']
            sss = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
            # add storage function
            func = sensorhelper.newModelObject('cdm:sys.function.StorageSubSystemFunction')
            func.setParent(sss)
            func.setName("Storage")
            sss.setFunctions(sensorhelper.getArray([func],'cdm:sys.Function'))
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
            ctsResult.addExtendedResult(sss)
            discovered = True
        else:
          log.debug('### VPlex output is null')
       
        # if(viprStorageSubSystemList != null && viprStorageSubSystemList.size() > 0)
        # {
            # logger.info((new StringBuilder()).append("No. of StorageSubSystem found = ").append(viprStorageSubSystemList.size()).toString());
            # Iterator iterator = viprStorageSubSystemList.iterator();
            # do
            # {
                # if(!iterator.hasNext())
                    # break;
                # ViprStorageSubSystem viprStorageSubSystem = (ViprStorageSubSystem)iterator.next();
                # if(arraysDiscoveryChunk != 0 && count > arraysDiscoveryChunk)
                # {
                    # logger.warning("Total array count discovered are reached to configured arraysDiscoveryChunk");
                    # break;
                # }
                # count++;
                # logger.debug((new StringBuilder()).append("Array#").append(count).append(", Details=").append(viprStorageSubSystem.toString()).toString());
                # String serialNumber = viprStorageSubSystem.getSerialnb();
                # String name = viprStorageSubSystem.getDevice();
                # String manufacturer = viprStorageSubSystem.getVendor();
                # String type = viprStorageSubSystem.getDevtype();
                # String model = viprStorageSubSystem.getModel();
                # String microcodeVersion = viprStorageSubSystem.getUcodefam();
                # String status = viprStorageSubSystem.getVstatus();
                # if(serialNumber == null || serialNumber.trim().equals(""))
                # {
                    # logger.debug("No value for serialNumber for array, skipping");
                # } else
                # {
                    # logger.trace("Serial Number checked for null");
                    # if(!AbstractOs.isAttributeSane(serialNumber, com.collation.platform.os.AbstractOs.SanityCheckAttributes.SERIAL_NUMBER))
                    # {
                        # logger.debug((new StringBuilder()).append("SerialNumber not valid = ").append(serialNumber).toString());
                    # } else
                    # {
                        # logger.trace("Serial Number validation completed");
                        # if(manufacturer == null || manufacturer.trim().equals(""))
                        # {
                            # logger.debug("No value for manufacturer for array, skipping");
                        # } else
                        # {
                            # logger.trace("Manufacturer checked for null");
                            # if(model == null || model.trim().equals(""))
                            # {
                                # logger.debug("No value for model for array, skipping");
                            # } else
                            # {
                                # logger.trace("Model checked for null");
                                # StorageSubSystem sss = (StorageSubSystem)helperMaps.storageSubSystemMap.get(serialNumber);
                                # if(sss != null)
                                # {
                                    # logger.debug((new StringBuilder()).append("Found duplicate storage subsystem by serial number : ").append(serialNumber).append(", skipping").toString());
                                # } else
                                # {
                                    # logger.trace("Duplication checked for StorageSubSystem");
                                    # sss = (StorageSubSystem)ModelFactory.newInstance(com/collation/platform/model/topology/storage/StorageSubSystem);
                                    # sss.setAnsiT10Id(name);
                                    # sss.setFqdn(name);
                                    # sss.setSerialNumber(serialNumber);
                                    # sss.setManufacturer(manufacturer);
                                    # sss.setType(type);
                                    # sss.setModel(model.trim());
                                    # sss.setROMVersion(microcodeVersion);
                                    # int availabilityState = 1;
                                    # if(status.equals("active"))
                                        # availabilityState = 2;
                                    # else
                                    # if(status.equals("inactive"))
                                        # availabilityState = 1;
                                    # else
                                        # availabilityState = 0;
                                    # sss.setAvailabilityState(availabilityState);
                                    # sss.setIsNetworkAttached(false);
                                    # boolean inListSize = inList(runList, "ARRAY_SIZE");
                                    # logger.info((new StringBuilder()).append("Checking the Array Size is in List or not = ").append(inListSize).toString());
                                    # if(inListSize)
                                    # {
                                        # logger.debug("ARRAY_SIZE in the list");
                                        # String url_array_capacity = getURL("ARRAY_SIZE");
                                        # String periodFilter = RESTConnectionParser.getSeriesFilter("", "");
                                        # url_array_capacity = url_array_capacity.replace("$PERIODFILTER$", periodFilter);
                                        # logger.debug((new StringBuilder()).append("url_array_capacity=").append(url_array_capacity).toString());
                                        # com.ibm.cdb.discover.app.srm.emc.vipr.elements.ViprCapacities capacities = rc.getCapacities(url_array_capacity);
                                        # long configuredUsableCapacity = RESTConnectionParser.getCapacityByName(capacities, "ConfiguredUsableCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#configuredUsableCapacity = ").append(configuredUsableCapacity).toString());
                                        # long configuredRawCapacity = RESTConnectionParser.getCapacityByName(capacities, "ConfiguredRawCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#configuredRawCapacity = ").append(configuredRawCapacity).toString());
                                        # long freeCapacity = RESTConnectionParser.getCapacityByName(capacities, "FreeCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#freeCapacity = ").append(freeCapacity).toString());
                                        # long poolFreeCapacity = RESTConnectionParser.getCapacityByName(capacities, "PoolFreeCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#poolFreeCapacity = ").append(poolFreeCapacity).toString());
                                        # long poolUsedCapacity = RESTConnectionParser.getCapacityByName(capacities, "PoolUsedCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#poolUsedCapacity = ").append(poolUsedCapacity).toString());
                                        # long usedCapacity = RESTConnectionParser.getCapacityByName(capacities, "UsedCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#usedCapacity = ").append(usedCapacity).toString());
                                        # long rawCapacity = RESTConnectionParser.getCapacityByName(capacities, "RawCapacity", "device", name);
                                        # logger.debug((new StringBuilder()).append("#rawCapacity = ").append(rawCapacity).toString());
                                        # sss.setVolumeGroupCapacity(configuredUsableCapacity);
                                        # long volumeGroupFreeSpace = poolFreeCapacity + freeCapacity;
                                        # sss.setVolumeGroupFreeSpace(volumeGroupFreeSpace);
                                        # sss.setAllocatedCapacity(poolUsedCapacity);
                                        # long availableCapacity = configuredUsableCapacity - poolUsedCapacity;
                                        # sss.setAvailableCapacity(availableCapacity);
                                    # }
                                    # boolean inListDisk = inList(runList, "ARRAY_DISK");
                                    # logger.info((new StringBuilder()).append("Checking the Array Disk is in List or not = ").append(inListDisk).toString());
                                    # if(inListDisk)
                                    # {
                                        # logger.debug("ARRAY_DISK in the list");
                                        # ArrayList devices = setDisksDetails(sss);
                                        # if(devices != null && devices.size() > 0)
                                        # {
                                            # sss.setDevices((com.collation.platform.model.topology.dev.MediaAccessDevice[])devices.toArray(new DiskDrive[0]));
                                            # logger.debug("Storage SubSystem is updated with Disk Drives");
                                        # }
                                    # }
                                    # boolean inListPool = inList(runList, "ARRAY_POOL");
                                    # logger.info((new StringBuilder()).append("Checking the Array Pool is in List or not = ").append(inListPool).toString());
                                    # if(inListPool)
                                    # {
                                        # logger.debug("ARRAY_POOL in the list");
                                        # ArrayList iPools = setPoolsDetails(sss);
                                        # if(iPools != null && iPools.size() > 0)
                                        # {
                                            # sss.setStoragePools((StoragePool[])iPools.toArray(new StoragePool[0]));
                                            # logger.debug("Storage SubSystem is updated with Storage Pools");
                                        # }
                                    # }
                                    # boolean inListVolume = inList(runList, "ARRAY_VOLUME");
                                    # logger.info((new StringBuilder()).append("Checking the Array Volumes is in List or not = ").append(inListVolume).toString());
                                    # if(inListVolume)
                                    # {
                                        # logger.debug("ARRAY_VOLUME in the list");
                                        # ArrayList volumes = setVolumeDetails(sss);
                                        # if(volumes != null && volumes.size() > 0)
                                        # {
                                            # sss.setMembers((StorageVolume[])volumes.toArray(new StorageVolume[0]));
                                            # logger.debug("Storage SubSystem is updated with Storage Volumes");
                                        # }
                                    # }
                                    # boolean inListPort = inList(runList, "ARRAY_PORT");
                                    # logger.info((new StringBuilder()).append("Checking the Array Port is in List or not = ").append(inListPort).toString());
                                    # if(inListPort)
                                    # {
                                        # logger.debug("ARRAY_PORT in the list");
                                        # ArrayList arrayPorts = setPortsDetails(sss);
                                        # if(arrayPorts != null && arrayPorts.size() > 0)
                                        # {
                                            # sss.setFCPorts((FCPort[])arrayPorts.toArray(new FCPort[0]));
                                            # logger.debug("Storage SubSystem is updated with Ports");
                                        # }
                                    # }
                                    # logger.debug("Storage SubSystem is set now and read to set in result");
                                    # result.getArrays().add(sss);
                                    # helperMaps.storageSubSystemMap.put(serialNumber, sss);
                                    # logger.info((new StringBuilder()).append("Created StorageSubSystem#").append(helperMaps.storageSubSystemMap.size()).append(", key=").append(serialNumber).toString());
                                # }
                            # }
                        # }
                    # }
                # }
            # } while(true);
        # } else
        # {
            # logger.info("No StorageSubSystem found");
        # }
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

    #except Exception, e:
    #    log.error("Sensor failed " + str(e))

# return resulting model object
#ctsResult.addExtendedResult(server)
