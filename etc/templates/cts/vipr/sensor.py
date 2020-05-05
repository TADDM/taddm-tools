from com.collation.platform.security.auth import AuthManager
from com.collation.platform.security.auth import EMCViprSRMAuth
from com.collation.discover.agent import AgentException
from com.collation.platform.os.storage.util import WorldWideNameUtils
from com.collation.platform.model.util.openid import OpenId
from javax.net.ssl import SSLContext
from javax.net.ssl import HttpsURLConnection
from java.net import *
from javax.xml.bind import DatatypeConverter
from java.lang import StringBuilder
from java.nio.charset import StandardCharsets
from java.io import *
from java.util import *
from java.security import *
from java.io import StringReader
from java.text import SimpleDateFormat

import sys
import java
import time
from math import pow

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

def getConnection(url, timeout = 30000):
  log.info('url='+url)
  siteURL = URL(url)
  conn = siteURL.openConnection()
  userpassword = java.lang.String(java.lang.StringBuilder().append(username).append(':').append(password).toString())
  encodedUserPassword = DatatypeConverter.printBase64Binary(userpassword.getBytes(StandardCharsets.UTF_8))
  conn.setRequestProperty("Authorization", java.lang.StringBuilder().append("Basic ").append(encodedUserPassword).toString())
  conn.setConnectTimeout(timeout)
  conn.setReadTimeout(timeout)
  conn.setRequestMethod("GET")
  conn.setUseCaches(False)
  conn.setDoInput(True)
  conn.setDoOutput(True)
  
  return conn

def getValues(conn):
  responseCode = conn.getResponseCode()
  log.info(conn.getURL().toString() + ' ### ResponseCode() == ' + str(responseCode))
  if responseCode == 200:
    output = getResponse(conn)
  else:
    log.warning('Unable to make a REST connection to EMC ViPR SRM using user name ' + username + '. Caused by ' + conn.getResponseMessage())
    log.error('Problem in URLConnection : ' + conn.getURL().toString())
    log.error('### Response code for REST request: ' + str(conn.getResponseCode()))
    output = None

  conn.disconnect()
  
  return output

def getSeriesValues(filter, properties):

  sdf = SimpleDateFormat("yyyy-MM-dd")
  currDateTime = Date()
  c = Calendar.getInstance()
  c.setTime(currDateTime)
  c.add(5, -7)
  endTime = str(sdf.format(currDateTime)) + 'T00:00:00'
  startTime = str(sdf.format(c.getTime())) + 'T00:00:00'
  url = ('https://' + ip + ':' + str(sslport) + '/APG-REST/metrics/series/values?limit=10000&' +
         filter + '&period=86400&start=' + startTime + '&end=' + endTime + '&' + properties)
  conn = getConnection(url, 60000) # use 60 second timeout for series because there can be more data
  return getValues(conn)
  
def getPropertiesValues(filter, fields):
  conn = getConnection('https://' + ip + ':' + str(sslport) + '/APG-REST/metrics/properties/values?' + filter + '&' + fields)
  return getValues(conn)
  
def getVPlexPorts(device):
  filter = 'filter=parttype%3D%27Port%27%26devtype%3D%27VirtualStorage%27%26%21iftype%3D%27null%27%26device%3D%27'+device+'%27'
  fields = 'fields=iftype,maxspeed,director,portwwn,part,vendor,portstat,nodewwn'
  return getPropertiesValues(filter, fields)

def getVPlexConnection():
  filter = 'filter=devtype%3D%27VirtualStorage%27'
  fields = 'fields=serialnb,model,vendor,device,devdesc'
  return getPropertiesValues(filter, fields)

def getVnxArrayVolumes(device):
  filter = ('filter=parttype%3D%27LUN%27'+
    '%26(!dgstype%3D%27Thin%27%7Cdgstype%3D%27Thin%27%26poolname%26!poolname%3D%27N/A%27%26!poolname%3D%27Unbound%27)'+
    '%26device%3D%27'+device+'%27')
  fields = ('fields=device,part,devconf,svclevel,purpose,poolname,pooltype,'+
    'sgname,datatype,devdesc,dgname,dgraid,dgroup,dgstype,dgtype,diskrpm,disksize,'+
    'disktype,hexid,host,luntagid,partdesc,partid,partsn,sstype')
  return getPropertiesValues(filter, fields)

def getVirtualDisks():
  fields='fields=device,part,partsn'
  filter='filter=devtype%3D%27VirtualStorage%27%26parttype%3D%27VirtualDisk%27'
  return getPropertiesValues(filter, fields)

# get all array volumes/luns
def getArrayLuns():
  fields='fields=device,part,partsn'
  filter='filter=parttype%3D%27LUN%27'
  return getPropertiesValues(filter, fields)
  
def getVirtualVolumes(device):
  # if you include psvclvl in the query it removes a vvol if the service level is null
  # In ViPR UI volumes with view = 'N/A' are not shown but they are shown in reporting so we are including here
  fields = 'fields=device,vvol,psvclvl,partsn'
  #filter = ('filter=parttype%3D%27VirtualVolume%27%26devtype%3D%27VirtualStorage%27%26%21view%3D%27N/A%27'+
  filter = ('filter=parttype%3D%27VirtualVolume%27%26devtype%3D%27VirtualStorage%27'+
    '%26device%3D%27'+device+'%27%26%21vstatus%3D%27inactive%27')
  return getPropertiesValues(filter, fields)

def getParsedJsonArray(output):

  # parse json
  reader = Json.createReader(StringReader(output))
  obj = reader.readObject()
  reader.close()
  
  return obj.getJsonArray('values')

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

def testConnection():
  testURL = '/APG-REST/metrics/properties'
  log.info('Trying to connect with Port:' + str(sslport) + ' Username:' + username + ' Password:XXXX')

  conn = getConnection('https://' + ip + ':' + str(sslport) + testURL)

  responseCode = conn.getResponseCode()
  log.info(conn.getURL().toString() + ' ### ResponseCode() == ' + str(responseCode))
  success = False
  if responseCode == 200:
    getResponse(conn) # need to read response or next response will be this one
    success = True
  elif responseCode == 301 or responseCode == 302:
    log.warning('### URL Redirection is ON')
    log.warning('### Response code for REST request: ' + str(responseCode) + ' Message: ' + conn.getResponseMessage())
    log.warning('Connection was not established with given parameters : user =' + username + ' for host =' + ip + ' with port =' + str(sslport))
  else:
    log.error('### Response code for REST request: ' + str(responseCode) + ' Message: ' + conn.getResponseMessage())
    log.warning('Connection was not established with given parameters : user =' + username + ' for host =' + ip + ' with port =' + str(sslport))
  conn.disconnect()
  return success

# pad 'HARD DISK X' with a leading 0 if X < 10
def padDiskNumber(diskname):
  if diskname.startswith('HARD DISK '):
    # pad hard disk number with 0
    disknbr = diskname.replace('HARD DISK ', '')
    if int(disknbr) < 10:
      return 'HARD DISK 0' + disknbr
    else:
      return diskname
  else:
    log.info('Bad disk name (' + diskname + ') returning None')
    return None

# for development purposes, skip storage of results that are not commented
skipStorage = {}
#skipStorage['VNX'] = True
#skipStorage['VPlex'] = True
#skipStorage['XtremIO'] = True
#skipStorage['Unity'] = True
#skipStorage['Switch'] = True
skipStorage['Solaris'] = True

def storeResult(mo, type):
  if type in skipStorage: # skip storage if key listed
    if skipStorage[type] is True:
      skipStorage[type] = False # only print warning once
      ctsResult.warning('DEVELOPER - Skipping storage of ' + type + ' objects')
  else:
    log.debug('Storing result: ' + str(mo))
    ctsResult.addExtendedResult(mo)

# get volume capacity and volume capacity used map for the array   
def getVolumeCapacities(arraySerial, property, parttype = 'LUN'):
  volumeCapMap = {}
  volumeUsedCapMap = {}
  try:
    # only get values with units in GB b/c that is all we handle in this code
    filter='filter=unit%3D%27GB%27%26(name%3D%27UsedCapacity%27%7Cname%3D%27Capacity%27)%26parttype%3D%27' + parttype + '%27%26serialnb%3D%27' + arraySerial + '%27'
    properties='properties=name,unit,' + property
    volumeCapOutput = getSeriesValues(filter, properties)
  
    if volumeCapOutput:
      volumeCaps = getParsedJsonArray(volumeCapOutput)
      for volumeCap in volumeCaps:
        points = volumeCap.getJsonArray('points')
        if points and not points.isNull(0):
          # get last point
          point = points.getJsonArray(points.size()-1).getString(1)
          properties = volumeCap.getJsonObject('properties')
          unit = properties.getJsonString('unit').getString()
          name = properties.getJsonString('name').getString()
          keyStr = properties.getJsonString(property)
          if keyStr:
            key = keyStr.getString()
            # code assumes everything is same unit
            if name == 'Capacity':
              volumeCapMap[key] = point
            elif name == 'UsedCapacity':
              volumeUsedCapMap[key] = point
      #log.debug('volumeCapMap:' + str(volumeCapMap))
      #log.debug('volumeUsedCapMap:' + str(volumeUsedCapMap))
      if len(volumeCapMap) == 0 and len(volumeUsedCapMap) == 0:
        msg = 'Volume capacity values not found for array with serial ' + arraySerial
        log.warning(msg)
        ctsResult.warning(msg)
  except: # catch all errors because we don't want to halt on volume capacity query errors
    e = sys.exc_info()[0]
    msg = 'Error occurred during volume capacity query, capacity values not updated for ' + arraytyp + ' array ' + sss.getFqdn()
    log.warning(msg)
    log.info('Error : ' + str(e))
    ctsResult.warning(msg)
  return volumeCapMap, volumeUsedCapMap

# set volume capacity and used capacity on the storage volume
def setVolumeCapacity(sv, name, volumeCapMap, volumeUsedCapMap, blksize = 512):
  if blksize is None:
    blksize = 512
  if name in volumeCapMap:
    cap = volumeCapMap[name]
    if cap:
      # assuming GB unit
      cap = long(pow(1024,3)*float(cap)/long(blksize))
      sv.setCapacity(cap)
    if name in volumeUsedCapMap:
      usedCap = volumeUsedCapMap[name]
      if usedCap:
        # assuming GB unit
        usedCap = long(pow(1024,3)*float(usedCap)/long(blksize))
        # sometimes ViPR shows used cap greater than capacity
        if usedCap <= cap:
          sv.setFreeSpace(cap-usedCap)
        else:
          # TODO should we make this negative if usedCap > cap
          sv.setFreeSpace(long(0))

def create_skinny_vvol(serialnb, vvol):
  vsv = None
  if serialnb + vvol in uuidBySerialVol:
    uuid = uuidBySerialVol[serialnb + vvol] # uuidBySerialVol is global mapping
    #log.debug('Processing connection from ' + uuid + ' and ' + array_vol_wwn)
    
    # create skinny volume for storage performance
    vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
    vsv.setManagedSystemName(uuid)
  else:
    #log.debug('Processing connection from ' + vvol + ' and ' + array_vol_wwn)
    # create skinny volume for storage performance
    vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
    vsv.setName(vvol)
    
    # create skinny VPlex for storagevolume naming rule
    vplex = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
    vplex.setOpenId(OpenId(vplex).addId('vplexserial', serialnb))    
    vsv.setParent(vplex)
    
  return vsv

def set_array_to_vplex(array, array_svolume, storage_tag):
  array_vol_wwn = array_svolume.getManagedSystemName()
  vdiskinfo = vdiskByLun[array_vol_wwn]
  serialnb = vdiskinfo['serialnb']
  vvol = vdiskinfo['vvol']
  
  # create skinny array volume for storage performance
  ssv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
  ssv.setManagedSystemName(array_vol_wwn)
    
  vdiskByLunUsed.append(array_vol_wwn) # keep track of the ones used
  
  vsv = create_skinny_vvol(serialnb, vvol)
  
  # create relationships
  bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
  bo.setSource(vsv)
  bo.setTarget(ssv)
  bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
  vsv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
  #log.debug('Storing basedOn:' + str(vsv) + ':' + str(ssv))
  storeResult(vsv, storage_tag)
  
  # 2019-09-30: disabling realizes b/c there are some weird storage things going on
  # and the basedOn relationship above already relates the two storage volumes
  
  # create another virtual volume for storage performance
  #vsv = create_skinny_vvol(serialnb, vvol)
  
  #realizes = sensorhelper.newModelObject('cdm:dev.RealizesExtent')
  #realizes.setSource(array_svolume)
  #realizes.setTarget(vsv)
  #realizes.setType('com.collation.platform.model.topology.dev.RealizesExtent')
  #array_svolume.setRealizedBy(realizes) # this causes StorageError without MSN set on vsv
  
  if not serialnb in usesRelnAdded:
    # uses relationship has not yet been added for this VPlex
    # create skinny VPlex
    vplex = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
    vplex.setOpenId(OpenId(vplex).addId('vplexserial', serialnb))
    # create skinny array
    skinny_array = sensorhelper.newModelObject('cdm:storage.StorageSubSystem')
    skinny_array.setAnsiT10Id(array.getAnsiT10Id())
    # create uses relation
    uses = sensorhelper.newModelObject('cdm:relation.Uses')
    uses.setSource(vplex)
    uses.setTarget(skinny_array)
    uses.setType('com.collation.platform.model.topology.relation.Uses')
    storeResult(uses, storage_tag)
    log.debug('Added Uses relationship for ' + serialnb + ' and ' + array.getSerialNumber())
    usesRelnAdded.append(serialnb)
     
# ctsSeed is CustomTemplateSensorSeed with following methods
# Map<String, Object> getResultMap()
# CTSTemplate getTemplate()
# Tuple<String, Object> getSeedInitiator()
# String getEngineId()
(ctsResult,ctsSeed,log) = sensorhelper.init(targets)

try:
  # if javax.json library has not been added to jre this will throw ImportError
  # and we can't continue unless it is available
  # https://docs.oracle.com/javaee/7/api/javax/json/package-summary.html
  from javax.json import *
  
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
      results = ctsSeed.getSeedInitiator().getValue()
      log.info('results:' + str(results))
      arrays = results.get('arrays')
      switches = results.get('switches')

      sslport = 58443 # default REST API port for ViPR
      username = auth.getUserName()
      password = auth.getPassword()

      if testConnection():
        try:
          output = getVPlexConnection()

          log.debug('### Response for getStorageSubSystem request:  -' + output)
          global uuidBySerialVol
          uuidBySerialVol = {}
          if output:
            vplexes = getParsedJsonArray(output)
            
            # get physical host information for scsi path
            filter='filter=devtype%3D%27Host%27%26parttype%3D%27Path%27%26%21inwwn%3D%27N/A%27'
            #fields='fields=tgtwwn,pathname,inwwn,lunid,hostname,osfamily' # get osfamily so we can build out Solaris
            fields='fields=tgtwwn,pathname,inwwn,lunid'
            hostPathOutput = getPropertiesValues(filter, fields)
            hostPathsByLun = {}
            if hostPathOutput:
              hostPaths = getParsedJsonArray(hostPathOutput)
              for hostPath in hostPaths:
                tgtwwn = hostPath.getJsonString('tgtwwn').getString()
                pathname = hostPath.getJsonString('pathname').getString()
                inwwn = hostPath.getJsonString('inwwn').getString()
                lunid = hostPath.getJsonString('lunid').getString()
                #hostname = hostPath.getJsonString('hostname').getString()
                #osfamily = hostPath.getJsonString('osfamily').getString()
                log.debug('Adding host path:' + lunid + '=' + str({ 'tgtwwn': tgtwwn, 'pathname': pathname, 'inwwn': inwwn }))
                if lunid in hostPathsByLun:
                  hostPathsArray = hostPathsByLun[lunid]
                  hostPathsArray.append({ 'tgtwwn': tgtwwn, 'pathname': pathname, 'inwwn': inwwn })
                else:
                  hostPathsByLun[lunid] = [{ 'tgtwwn': tgtwwn, 'pathname': pathname, 'inwwn': inwwn }]
                  
            log.debug('len(hostPathsByLun):' + str(len(hostPathsByLun)))

            # get windows disk information for scsi path
            filter='filter=devtype%3D%27Host%27%26parttype%3D%27Disk%27%26devdesc=%27%25Windows%25%27%26!partsn%3D%27N/A%27%26!vstatus=%27inactive%27'
            fields='fields=part,portwwn,partsn,device'
            hostDiskOutput = getPropertiesValues(filter, fields)
            hostDisksByLun = {}
            if hostDiskOutput:
              hostDisks = getParsedJsonArray(hostDiskOutput)
              for hostDisk in hostDisks:
                part = hostDisk.getJsonString('part').getString()
                portwwn = hostDisk.getJsonString('portwwn').getString()
                partsn = hostDisk.getJsonString('partsn').getString()
                device = hostDisk.getJsonString('device').getString()
                if partsn in hostDisksByLun:
                  hostPathsArray = hostDisksByLun[partsn]
                  hostPathsArray.append({ 'part': part, 'portwwn': portwwn, 'device': device })
                else:
                  hostDisksByLun[partsn] = [{ 'part': part, 'portwwn': portwwn, 'device': device }]
            log.debug('len(hostDisksByLun):' + str(len(hostDisksByLun)))
            
            vplexPortWWN = [] # collect VPlex ports WWN to connect to switch ports later
            hostPathsByLunUsed = []
            hostDisksByLunUsed = []
            global usesRelnAdded
            # iterate over all VPlex
            for vplex in vplexes:
              usesRelnAdded = [] # track uses relationships defined
              serialnb = vplex.getJsonString('serialnb').getString()
              model = vplex.getJsonString('model').getString()
              vendor = vplex.getJsonString('vendor').getString()
              device = vplex.getJsonString('device').getString()
              devdesc = vplex.getJsonString('devdesc').getString()
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
                # set openID serial so that HyperVDisks.py extension can create relationship to virtual volume
                sss.setOpenId(OpenId(sss).addId('vplexserial', serialnb))
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
              portOutput = getVPlexPorts(device)

              # collect FCPorts and set on SSS
              if portOutput:
                ports = getParsedJsonArray(portOutput)
                fcports = []
                # iterate over all VPlex ports
                for port in ports:
                  #log.debug('port:' + str(port))
                  iftype = port.getJsonString('iftype').getString()
                  maxspeed = port.getJsonString('maxspeed').getString()
                  director = port.getJsonString('director').getString()
                  portwwn = port.getJsonString('portwwn').getString()
                  part = port.getJsonString('part').getString()
                  vendor = port.getJsonString('vendor').getString()
                  portstat = port.getJsonString('portstat').getString()
                  nodewwn = port.getJsonString('nodewwn').getString()

                  fcport = sensorhelper.newModelObject('cdm:dev.FCPort')
                  fcport.setParent(sss)
                  try:
                    fcport.setPermanentAddress(WorldWideNameUtils.toUniformString(portwwn))
                  except:
                    e = sys.exc_info()[1]
                    msg = 'VPlex portwwn address malformed, skipping ' + portwwn
                    log.warning(msg)
                    log.info('Error : ' + str(e))
                    continue
                  speed = float(maxspeed) * 1024 * 1024 * 1024
                  fcport.setSpeed(long(speed))
                  fcport.setPortNumber(0)
                  fcport.setDescription(director+':'+iftype)
                  if portstat == 'up':
                    fcport.setStatus(3)
                  fcports.append(fcport)
                  
                  # add port WWN to list to connect to switch later
                  vplexPortWWN.append(portwwn)
                sss.setFCPorts(sensorhelper.getArray(fcports,'cdm:dev.FCPort'))
                
              # query volumes for vplex
              vvolumeOutput = getVirtualVolumes(device)
              
              members = [] # collect all the vvols
              if vvolumeOutput:
                vvolumes = getParsedJsonArray(vvolumeOutput)
                
                # query vvol capacity
                volumeCapMap, volumeUsedCapMap = getVolumeCapacities(sss.getSerialNumber(), 'vvol', 'VirtualVolume')
                
                # iterate over all volumes
                for vvolume in vvolumes:
                  #log.debug('vvolume:' + str(vvolume))
                  vvol = vvolume.getJsonString('vvol').getString()
                  partsn = vvolume.getJsonString('partsn').getString()

                  vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                  vsv.setParent(sss)
                  vsv.setName(vvol)
                  vsv.setVirtual(True)
                  # ManagedSystemName is SUPPOSED to be reserved for ITM/TMS integration, however the developers
                  # have been using it all over the place as a hack, including for the basedOn StorageExtent for VMwareDataStore
                  vsv.setManagedSystemName(partsn)
                  uuidBySerialVol[sss.getSerialNumber() + vvol] = partsn
                  
                  # set vvol capacity
                  setVolumeCapacity(vsv, vvol, volumeCapMap, volumeUsedCapMap)
                  
                  paths = []
                  if partsn in hostPathsByLun:
                    hostPathsByLunUsed.append(partsn) # keep track of used to find gaps in code
                    hostPathArray = hostPathsByLun[partsn]
                    log.debug('Found host path(s) for ' + partsn)
                    for hostPath in hostPathArray:
                      log.debug('Adding host path for ' + hostPath['pathname'] + ' ' + hostPath['inwwn'] + ' ' + hostPath['tgtwwn'])
                      sPath = sensorhelper.newModelObject('cdm:dev.SCSIPath')
                      sPath.setArrayVolume(vsv)
                      # b/c we don't have LUN for virtual volume, TADDM topo agent 
                      # will not create FCVolume to StorageVolume relationship
                      # sPath.setLUN()
                      # as workaround, setting pathname in description field for post-discovery
                      # processing to set LUN on SCSIPath (via setLuns.py)
                      sPath.setDescription('pathname=' + str(hostPath['pathname']))
                      
                      targetPE = sensorhelper.newModelObject('cdm:dev.SCSIProtocolEndPoint')
                      #targetPE.setName(WorldWideNameUtils.toUniformString(partsn))
                      #targetPE.setWorldWideName(WorldWideNameUtils.toUniformString(partsn))
                      targetPE.setName(WorldWideNameUtils.toUniformString(hostPath['tgtwwn']))
                      targetPE.setWorldWideName(WorldWideNameUtils.toUniformString(hostPath['tgtwwn']))
                      #log.debug('Adding parent endpoint: ' + str(targetPE))
                      sPath.setParent(targetPE)
                      
                      hep = sensorhelper.newModelObject('cdm:dev.SCSIProtocolEndPoint')
                      hep.setWorldWideName(WorldWideNameUtils.toUniformString(hostPath['inwwn']))
                      #log.debug('Adding host endpoint: ' + str(hep))
                      sPath.setHostEndPoint(hep)
                      
                      #log.debug('Adding SCSIPath: ' + str(sPath))
                      paths.append(sPath)
                  
                  # Windows disks
                  if partsn in hostDisksByLun:
                    #log.debug('Found host disk(s) for ' + partsn)
                    hostDisksByLunUsed.append(partsn)
                    hostDiskArray = hostDisksByLun[partsn]
                    for hostDisk in hostDiskArray:
                      sPath = sensorhelper.newModelObject('cdm:dev.SCSIPath')
                      sPath.setArrayVolume(vsv)
                      # b/c we don't have LUN for virtual volume, TADDM topo agent 
                      # will not create FCVolume to StorageVolume relationship
                      # sPath.setLUN()
                      # as workaround, setting pathname in description field for post-discovery
                      # processing to set LUN on SCSIPath (via setLuns.py)
                      sPath.setDescription('part=' + str(hostDisk['part']))
                      
                      # TODO set this to the VPlex port WWN (will need to cache before starting this vvol loop)
                      targetPE = sensorhelper.newModelObject('cdm:dev.SCSIProtocolEndPoint')
                      targetPE.setName(WorldWideNameUtils.toUniformString(partsn))
                      targetPE.setWorldWideName(WorldWideNameUtils.toUniformString(partsn))
                      #log.debug('Adding parent endpoint: ' + str(targetPE))
                      sPath.setParent(targetPE)
                      
                      hep = sensorhelper.newModelObject('cdm:dev.SCSIProtocolEndPoint')
                      hep.setWorldWideName(WorldWideNameUtils.toUniformString(hostDisk['portwwn']))
                      #log.debug('Adding host endpoint: ' + str(hep))
                      sPath.setHostEndPoint(hep)
                      
                      #log.debug('Adding SCSIPath: ' + str(sPath))
                      paths.append(sPath)

                  if len(paths) > 0:
                    vsv.setHostPaths(sensorhelper.getArray(paths,'cdm:dev.SCSIPath'))

                  members.append(vsv)
                  
              # now get vvolumes where partsn is empty
              fields='fields=device,vvol,psvclvl'
              filter = ('filter=parttype%3D%27VirtualVolume%27%26devtype%3D%27VirtualStorage%27'+
                '%26device%3D%27'+device+'%27%26%21vstatus%3D%27inactive%27%26partsn%3D%27%27')
              vvolumeOutput = getPropertiesValues(filter, fields)
              if vvolumeOutput:
                vvolumes = getParsedJsonArray(vvolumeOutput)
                
                # query vvol capacity
                volumeCapMap, volumeUsedCapMap = getVolumeCapacities(sss.getSerialNumber(), 'vvol', 'VirtualVolume')
                
                # iterate over all volumes
                for vvolume in vvolumes:
                  #log.debug('vvolume:' + str(vvolume))
                  vvol = vvolume.getJsonString('vvol').getString()

                  vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                  vsv.setParent(sss)
                  vsv.setName(vvol)
                  vsv.setVirtual(True)
                  
                  # set vvol capacity
                  setVolumeCapacity(vsv, vvol, volumeCapMap, volumeUsedCapMap)
                  
                  members.append(vsv)
              
              # ViPR sensor only sets members, not storageExtents
              sss.setMembers(sensorhelper.getArray(members,'cdm:dev.StorageVolume'))
              
              storeResult(sss, 'VPlex')
              discovered = True
            
            # print all hostPathsByLun not used
            log.debug('Host paths not used:')
            for partsn in hostPathsByLun:
              if not partsn in hostPathsByLunUsed:
                log.debug(partsn + ': ' + str(hostPathsByLun[partsn]))
                
            # print all hostDisksByLun not used
            log.debug('Host disks not used:')
            for partsn in hostDisksByLun:
              if not partsn in hostDisksByLunUsed:
                log.debug(partsn + ': ' + str(hostDisksByLun[partsn]))
          else:
            log.debug('### VPlex output is null')
            
          # cache Host/Hypervisor/VirtualStorage Disk/VirtualDisk for SCSI path generation
          disks = {}
          fields='fields=device,part,partsn'
          # one of the VPlex devices has all vdisks set to 'inactive' so we are leaving that off for VPlex
          filters=['filter=%21vstatus%3D%27inactive%27%26devtype%3D%27Host%27%26parttype%3D%27Disk%27',
                   'filter=%21vstatus%3D%27inactive%27%26devtype%3D%27Hypervisor%27%26parttype%3D%27Disk%27',
                   'filter=devtype%3D%27VirtualStorage%27%26parttype%3D%27VirtualDisk%27']
          for filter in filters:
            diskOutput = getPropertiesValues(filter, fields)
            if diskOutput:
              values = getParsedJsonArray(diskOutput)
              for value in values:
                #log.debug('disk:' + str(value))
                device = value.getJsonString('device').getString()
                part = value.getJsonString('part').getString()
                partsn = value.getJsonString('partsn').getString()
                if partsn in disks:
                  diskArray = disks[partsn]
                  #log.debug('Adding to existing diskArray:' + str(diskArray))
                else:
                  diskArray = []
                  #log.debug('Creating new diskArray for ' + str(partsn))
                diskArray.append({'device': device, 'part': part, 'partsn': partsn})
                disks[partsn] = diskArray
          log.debug('Number of disks found:' + str(len(disks)))

          # query array luns
          arrayluns = []
          fields='fields=device,part,partsn'
          filter='filter=!vstatus%3D%27inactive%27%26devtype%3D%27Array%27%26parttype%3D%27LUN%27'
          arraylunsOutput = getPropertiesValues(filter, fields)
          if arraylunsOutput:
            values = getParsedJsonArray(arraylunsOutput)
            for value in values:
              #log.debug('arraylun:' + str(value))
              device = value.getJsonString('device').getString()
              part = value.getJsonString('part').getString()
              partsn = value.getJsonString('partsn').getString()
              arrayluns.append({'device': device, 'part': part, 'partsn': partsn})
          log.debug('Number of array luns found:' + str(len(arrayluns)))
          
          # build scsi path list
          scsipaths = []
          for arraylun in arrayluns:
            array = arraylun['device']
            lun = arraylun['part']
            partsn = arraylun['partsn']
            if partsn in disks:
              diskArray = disks[partsn]
              for disk in diskArray:
                hostname = disk['device']
                path = disk['part']
                scsipath = {'hostname': hostname, 'HBA': path, 'WWN': partsn, 'array': array, 'LUN': lun}
                #log.debug('Adding scsipath: ' + str(scsipath))
                scsipaths.append(scsipath)
            else:
              scsipath = {'hostname': None, 'HBA': None, 'WWN': partsn, 'array': array, 'LUN': lun}
              scsipaths.append(scsipath)
            
          for wwn in disks:
            for disk in disks[wwn]:
              hostname = disk['device']
              path = disk['part']
              partsn = disk['partsn']
              scsipath = {'hostname': hostname, 'HBA': path, 'WWN': partsn, 'array': None, 'LUN': None}
              scsipaths.append(scsipath)

          log.debug('scsipath size ' + str(len(scsipaths)))

          # collect VirtualDisk information from VPlex for storage mapping to array volumes
          vDiskFields = 'fields=vdisk,lunwwn,vvol,serialnb,arraysn'
          vDiskFilter = 'filter=parttype%3D%27VirtualDisk%27%26devtype%3D%27VirtualStorage%27%26%21vvol%3D%27N/A%27%26vstatus%3D%27active%27'
          vdiskOutput = getPropertiesValues(vDiskFilter, vDiskFields)
          global vdiskByLun
          vdiskByLun = {}
          if vdiskOutput:
            vdisks = getParsedJsonArray(vdiskOutput)
            for vd in vdisks:
              #log.debug('vdisk:' + str(vd))
              vdisk = vd.getJsonString('vdisk').getString()
              lunwwn = vd.getJsonString('lunwwn').getString()
              vvol = vd.getJsonString('vvol').getString()
              serialnb = vd.getJsonString('serialnb').getString()
              arraysn = vd.getJsonString('arraysn').getString()
              if lunwwn in vdiskByLun:
                log.debug(lunwwn + ' already exists in vdiskByLun: ' + str(vdiskByLun[lunwwn]))
              else:
                vdiskByLun[lunwwn] = {'vdisk': vdisk, 'vvol': vvol, 'serialnb': serialnb, 'arraysn': arraysn}
          
          global vdiskByLunUsed
          vdiskByLunUsed = []
          # enhance existing arrays
          for sss in arrays:
            log.debug('array:' + str(sss))
            
            filter='filter=serialnb=\'' + sss.getSerialNumber() + '\''
            fields='fields=arraytyp'
            arrayOutput = getPropertiesValues(filter, fields)
            
            arraytyp = None
            if arrayOutput:
              arraytyp = getParsedJsonArray(arrayOutput).getJsonObject(0).getJsonString('arraytyp').getString()
              log.debug('arraytyp:' + arraytyp)
            else:
              log.debug('Could not get arraytyp, skipping array')
              continue
            
            usesRelnAdded = []
            # handle by array type
            if arraytyp == 'VNX':
              # query volumes for array
              volumeOutput = getVnxArrayVolumes(sss.getFqdn())

              if volumeOutput:
                # get volumes
                volumes = getParsedJsonArray(volumeOutput)
                
                # cache capacities for all volumes
                volumeCapMap, volumeUsedCapMap = getVolumeCapacities(sss.getSerialNumber(), 'partdesc')
                
                members = []
                # iterate over all volumes
                for volume in volumes:
                  #log.debug('volume:' + str(volume))
                  # part,partsn,lun,blksize
                  partdesc = volume.getJsonString('partdesc').getString()
                  partsn = volume.getJsonString('partsn').getString()
                  partid = volume.getJsonString('partid').getString() # shown as UUID in ViPR

                  sv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                  sv.setParent(sss)
                  sv.setName(partdesc)
                  sv.setLUN(int(partid))
                  sv.setBlockSize(long(512))
                  # partsn is the WWN associated with the volume
                  sv.setManagedSystemName(partsn)
                  
                  setVolumeCapacity(sv, partdesc, volumeCapMap, volumeUsedCapMap)
                  
                  # check VPlex vdisks for connection to this LUN
                  if partsn in vdiskByLun:
                    #log.debug('Found matching wwn: ' + partsn)
                    set_array_to_vplex(sss, sv, 'VNX')

                  members.append(sv)
                # ViPR sensor only sets members, not storageExtents
                sss.setMembers(sensorhelper.getArray(members,'cdm:dev.StorageVolume'))
                discovered = True
                storeResult(sss, 'VNX')
              else:
                log.debug('No volumes returned for ' + sss.getFqdn())
            elif arraytyp == 'XtremIO':
              ######
              #
              # XtremIO
              #
              ######
              filter = 'filter=parttype=%27LUN%27%26%21vstatus%3D%27inactive%27%26serialnb=%27' + sss.getSerialNumber() + '%27'
              fields = 'fields=part,lun,blksize,disktype,partsn'
              volumeOutput = getPropertiesValues(filter, fields)

              members = []
              volumeCapMap, volumeUsedCapMap = getVolumeCapacities(sss.getSerialNumber(), 'part')
              if volumeOutput:
                volumes = getParsedJsonArray(volumeOutput)
                
                # iterate over all volumes
                for volume in volumes:
                  #log.debug('volume:' + str(volume))

                  part = volume.getJsonString('part').getString()
                  lunJ = volume.getJsonString('lun')
                  lun = None
                  if lunJ:
                    lun = lunJ.getString()
                  blksizeJ = volume.getJsonString('blksize')
                  blksize = None
                  if blksizeJ:
                    blksize = blksizeJ.getString()
                  #volid = volume.getJsonString('volid').getString()
                  disktype = volume.getJsonString('disktype').getString()
                  partsn = volume.getJsonString('partsn').getString()

                  sv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                  sv.setParent(sss)
                  sv.setName(part)
                  if lun:
                    sv.setLUN(int(lun))
                  if blksize:
                    sv.setBlockSize(long(blksize))
                  # use MSN for storageVolume to allow sv.setBasedOn(bo) (a hack)
                  sv.setManagedSystemName(partsn)
                  
                  setVolumeCapacity(sv, part, volumeCapMap, volumeUsedCapMap, blksize)
                  
                  # check VPlex vdisks for connection to this LUN
                  if partsn in vdiskByLun:
                    log.debug('Found matching wwn: ' + partsn)
                    set_array_to_vplex(sss, sv, 'XtremIO')
                      
                  members.append(sv)

              # add flash drive volumes (no lun or blksize and partsn corresponds to vdisk)
              filter = 'filter=(lun=%27%27%7Cblksize=%27%27)%26parttype=%27LUN%27%26%21vstatus%3D%27inactive%27%26serialnb=%27' + sss.getSerialNumber() + '%27'
              fields = 'fields=part,disktype,partsn'
              volumeOutput = getPropertiesValues(filter, fields)
              
              if volumeOutput:
                # TODO - make this function b/c it's identical to above
                volumes = getParsedJsonArray(volumeOutput)
                
                # iterate over all volumes
                for volume in volumes:
                  #log.debug('volume:' + str(volume))

                  part = volume.getJsonString('part').getString()
                  lunJ = volume.getJsonString('lun')
                  lun = None
                  if lunJ:
                    lun = lunJ.getString()
                  blksizeJ = volume.getJsonString('blksize')
                  blksize = None
                  if blksizeJ:
                    blksize = blksizeJ.getString()
                  #volid = volume.getJsonString('volid').getString()
                  disktype = volume.getJsonString('disktype').getString()
                  partsn = volume.getJsonString('partsn').getString()

                  sv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                  sv.setParent(sss)
                  sv.setName(part)
                  if lun:
                    sv.setLUN(int(lun))
                  if blksize:
                    sv.setBlockSize(long(blksize))
                  # use MSN for storageVolume to allow sv.setBasedOn(bo) (a hack)
                  sv.setManagedSystemName(partsn)
                  
                  setVolumeCapacity(sv, part, volumeCapMap, volumeUsedCapMap, blksize)
                  
                  # check VPlex vdisks for connection to this LUN
                  if partsn in vdiskByLun:
                    log.debug('Found matching wwn: ' + partsn)
                    set_array_to_vplex(sss, sv, 'XtremIO')
                      
                  members.append(sv)

              # ViPR sensor only sets members, not storageExtents
              sss.setMembers(sensorhelper.getArray(members,'cdm:dev.StorageVolume'))
              discovered = True
              storeResult(sss, 'XtremIO')
            elif arraytyp.startswith('Unity/VNXe'):
              ######
              #
              # Unity/VNXe
              #
              ######
              filter = 'filter=parttype=%27LUN%27%26serialnb=%27' + sss.getSerialNumber() + '%27%26%21vstatus%3D%27inactive%27'
              fields = 'fields=part,srclun,wwn'
              volumeOutput = getPropertiesValues(filter, fields)

              if volumeOutput:
                volumes = getParsedJsonArray(volumeOutput)
                
                volumeCapMap, volumeUsedCapMap = getVolumeCapacities(sss.getSerialNumber(), 'part')
                
                members = []
                # iterate over all volumes
                for volume in volumes:
                  #log.debug('volume:' + str(volume))

                  part = volume.getJsonString('part').getString()
                  srclun = volume.getJsonString('srclun').getString()
                  wwn = volume.getJsonString('wwn').getString()

                  sv = sensorhelper.newModelObject('cdm:dev.StorageVolume')
                  sv.setParent(sss)
                  sv.setName(part)
                  sv.setLUN(int(srclun))
                  sv.setBlockSize(long(512))
                  sv.setManagedSystemName(wwn) # this is the UUID for the LUN

                  setVolumeCapacity(sv, part, volumeCapMap, volumeUsedCapMap)
                  
                  # Unity is not connected through VPLEX, so this should never be True
                  if wwn in vdiskByLun:
                    #log.debug('Found matching wwn: ' + partsn)
                    set_array_to_vplex(sss, sv, 'Unity')
                  
                  members.append(sv)
                # ViPR sensor only sets members, not storageExtents
                sss.setMembers(sensorhelper.getArray(members,'cdm:dev.StorageVolume'))
                discovered = True
                storeResult(sss, 'Unity')
              else:
                log.debug('No volumes returned for ' + sss.getFqdn())
            else:
              log.debug('Unknown arraytyp')
          
          # print all vdisks that were not used to create VPlex volume to array volume relationships
          log.debug('All vDisks not used:')
          for wwn in vdiskByLun:
            if not wwn in vdiskByLunUsed:
              log.debug(wwn + ': ' + str(vdiskByLun[wwn]))
          
          if switches:
            # VPLex ports collected earlier in vplexPortWWN dict
            # query switch ports
            filter='filter=%21vstatus%3D%27inactive%27%26devtype%3D%27FabricSwitch%27%26parttype%3D%27Port%27'
            fields='fields=device,part,portwwn,partwwn'
            switchPortOutput = getPropertiesValues(filter, fields)
            if switchPortOutput:
              switchPorts = getParsedJsonArray(switchPortOutput)
              
              switchPortWWN = [] # cache switch ports for switch to switch connectivity
              for switchPort in switchPorts:
                switchPortWWN.append(switchPort.getJsonString('partwwn').getString())
                
              for switchPort in switchPorts:
                portwwn = switchPort.getJsonString('portwwn').getString()
                partwwn = switchPort.getJsonString('partwwn').getString()
                switchPortWWN.append(partwwn)
                if portwwn in vplexPortWWN or portwwn in switchPortWWN:
                  source = sensorhelper.newModelObject('cdm:dev.FCPort') # define skinny switch port
                  source.setPermanentAddress(WorldWideNameUtils.toUniformString(partwwn))
                  target = sensorhelper.newModelObject('cdm:dev.FCPort') # define skinny vplex port
                  target.setPermanentAddress(WorldWideNameUtils.toUniformString(portwwn))
                  con = sensorhelper.newModelObject('cdm:relation.ConnectedTo') # define connectedTo relationship
                  con.setSource(source)
                  con.setTarget(target)
                  con.setType("com.collation.platform.model.topology.relation.ConnectedTo")
                  log.debug('ConnectedTo: ' + str(partwwn) + ':' + str(portwwn))
                  storeResult(con, 'Switch')
            
            for switch in switches:
              log.debug('switch:' + str(switch))
              # query switch ports

          # Build Solaris physical hosts because HBA discovery not working
          # THIS IS NOT COMPLETE AND DOESN'T STORE ANY RESULTS
          filter='filter=devtype%3D%27Host%27%26osfamily%3D%27Solaris%27'
          fields='fields=device,hostname,fqdn'
          solarisOutput = getPropertiesValues(filter, fields)
          if solarisOutput:
            for solaris in getParsedJsonArray(solarisOutput):
              hostname = solaris.getJsonString('hostname').getString()
              device   = solaris.getJsonString('device').getString()
              if hostname.lower() == 'tx342bkpnwsn01':
                log.debug('Building Solaris machine: ' + hostname.lower())
                host = sensorhelper.newModelObject('cdm:sys.sun.SunSPARCUnitaryComputerSystem')
                host.setOpenId(OpenId(host).addId('solaris', hostname.lower()))
                # add FC volumes
                filter='filter=device%3D%27' + device + '%27%26parttype%3D%27Disk%27'
                fields='fields=hostname'
                solarisDiskOutput = getPropertiesValues(filter, fields)
                #if solarisDiskOutput:
                #  for solarisDisk in getParsedJsonArray(solarisDiskOutput):
                #storeResult(host, 'Solaris')
        except Exception, e:
          log.warning('Problem occurs while processing the data: ' + str(e))
          ctsResult.warning('Problem occurs while processing the data:' + str(e))
except ImportError:
  java_home= str(System.getProperty("java.home"))
  log.error('Add javax.json libraries (javax.json-api-1.0.jar, javax.json-1.1.jar) to ' + java_home + '/lib/ext')
  ctsResult.warning('javax.json libraries  (javax.json-api-1.0.jar, javax.json-1.1.jar) missing, install in ' + java_home + '/lib/ext')