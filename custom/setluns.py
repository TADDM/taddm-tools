#!/usr/bin/env ../bin/jython_coll_253

############### Begin Standard Header - Do not add comments here ###############
#
# File:     %W%
# Version:  %I%
# Modified: %G% %U%
# Build:    %R% %L%
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
Main comment block, Beginning of Script

SCRIPT OVERVIEW (This section would be used by doc gnerators)

setluns.py -- Find SCSIPath without LUN and set LUN according to hostEndPoint.parent.FCPLun

DESCRIPTION:

CAVEATS:

   Tested in 7.3.0.6

Author:  Mat Davis
     mdavis5@us.ibm.com


History:
    Version 0.5 -- 6/2019 -- Initial Version --
'''
# Standard Jython/Python Library Imports

import sys
import java
import os

# from Java [additional imports]...
from java.lang import Class
from java.lang import System
from java.util import Properties
from java.lang import Boolean
from java.sql import DriverManager
from java.sql import SQLException

# Set the Path information
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

# Import the TADDM Java Libraries  [Following Required for api access]
from com.collation.platform.util import Props
from com.collation.proxy.api.client import *
from com.ibm.cdb.api import ApiFactory
from com.collation.platform.util import ModelFactory
from com.collation.platform.model import Guid
from com.ibm.cdb.topomgr import TopologyManagerFactory
from com.ibm.cdb.topomgr import TopomgrProps

# More Standard Jython/Python Library Imports
import traceback
import string
import re
import jarray
import getopt
import pprint
import time
import threading
import logging

import sensorhelper
import ext_attr_helper as eahelper

# Some default GLOBAL Values (Typically these should be in ALL CAPS)

VERSION = "0.5"

#
# Set up logging...
#
#global log
logging.basicConfig(filename=coll_home + '/log/setluns.log',level=logging.DEBUG,
                    format='%(asctime)-15s (%(threadName)-10s) %(message)s',
                    )

########################
# LogError      Error logger
########################

def LogError(msg):
  print msg
  logging.error(msg)
  (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
  traceback.print_exc(ErrorTB)

########################
# LogInfo
########################
def LogInfo(msg):
  print msg
  logging.info(msg)

########################
# LogDebug
########################
def LogDebug(msg):
  print msg
  logging.debug(msg)

def usage():
  print """ \
usage: setluns.jy [options] 

   Sync LUN value for SCSIPath and FCVolume

    Options:

    -u userid           User required to login to TADDM Server
                        Defaults to 'administrator'

    -p password         Password for TADDM Server user
                        Defaults to 'collation'
                        
    -h                  print this message

    """


class MO_Array:
  def __init__(self, mo_array=None):
    self.lock = threading.Lock()
    self.mo_array = mo_array

  def get(self):
    self.lock.acquire()
    mo = None
    try:
      if self.mo_array:
        mo = self.mo_array.pop()
    finally:
      self.lock.release()
    return mo

class Output:
    def __init__(self, start=0):
        self.lock = threading.Lock()
        self.value = start

    def println(self, msg):
        self.lock.acquire()
        try:
            print msg
        finally:
            self.lock.release()

    def print_model_object(self, mo):
        self.lock.acquire()
        try:
            print "%32s" % (mo.getGuid())
        finally:
            self.lock.release()

    def print_guid(self, guid):
        self.lock.acquire()
        try:
            print "%32s" % (guid)
        finally:
            self.lock.release()
            
def worker(mo_array):
  conn = ApiFactory.getInstance().getApiConnection(Props.getRmiBindHostname(),-1,None,0)
  sess = ApiFactory.getInstance().getSession(conn, userid, password, ApiSession.DEFAULT_VERSION)
  api = sess.createCMDBApi()
  
  mo = mo_array.get()
  while mo:
    try:
      output.print_model_object(mo)
      output.println(" " + str(mo.getGuid()) + "  --> Updating object")
      api.update([mo], None)
      output.println(" " + str(mo.getGuid()) + "  --> Success")
    except:
      output.println(" " + str(mo.getGuid()) + "  --> Failed")
    mo = mo_array.get()
  
  api.close()
  sess.close()
  conn.close()

def jHashMaptoPyDict(hm):
  dict = {}
  iter = hm.keySet().iterator()
  while iter.hasNext():
    key = iter.next()
    dict[str(key)] = hm.get(key)
  return dict

def connectToDB(driver, url, user, password):
  LogInfo("Going to connect to database...")
  try:
    cls = Class.forName(driver);
    DriverManager.registerDriver(cls.newInstance())
    conn = DriverManager.getConnection(url, user, password)
    return conn
  except Exception, desc:
    LogError("Cannot connect to database with the username: " + user)
    raise desc

api_inst = None
def get_taddm_api():
  global api_inst
  if api_inst is None:
    api_inst = eahelper.get_taddm_api(Props.getRmiBindHostname(), userid, password)
    return api_inst
  else:
    return api_inst  
  
def main():

  try:
    LogInfo("Starting...") 
    try:
      opts, args = getopt.getopt(sys.argv[1:], 'u:p:h', ['help'] )
    except getopt.GetoptError, err:
      # print help information and exit:
      print str(err) # will print something like "option -a not recognized"
      usage()
      sys.exit(2)
    
    LogDebug("Options " + str(opts))
    global userid
    userid = None
    global password
    password = None
    for o, a in opts:
      if o == "-u":
        userid = a
      elif o == "-p":
        password = a
      elif o in ("-h", "--help"):
        usage()
        sys.exit()
      else:
        assert False, "unhandled option"

    #------------------------------------------------
    # Set Defaults...
    #------------------------------------------------
    host = "localhost"       # we default to localhost

    if userid is None:
      userid = "administrator"

    if password is None:
      password = "collation"
    #
    # Initialize
    #

    LogDebug('Initializing database connection')
    props = TopologyManagerFactory.getProps()
    dbConn = connectToDB(props.getDbDriver(), props.getDbUrl(), props.getDbUser(), props.getDbPassword())

    # cache the FCVolumes
    fcv_stmt = dbConn.createStatement()
    sql_query = (
      'SELECT ' +
       'CS.GUID_C AS CS_GUID, FCV.DEVICEID_C AS DEVICEID, FCV.FCPLUN_C AS FCPLUN, ' +
       'FCV.PORTWWN_C AS PORTWWN, FCV.NAME_C AS NAME, FCV.GUID_C AS GUID, ARRAYVOL.GUID_C AS ARRAYVOL_GUID ' +
      'FROM BB_FCVOLUME55_V FCV ' +
      'JOIN BB_COMPUTERSYSTEM40_V CS ON FCV.PK__PARENTSTORAGEEXTENT_C = CS.PK_C ' +
      'LEFT OUTER JOIN BB_STORAGEEXTENTJDO_BASEDON_J FC_BO ON FCV.PK_C = FC_BO.PK__JDOID_C ' +
      'LEFT OUTER JOIN BB_BASEDONEXTENT34_V BO ON BO.PK_C = FC_BO.PK__BASEDON_C ' +
      'LEFT OUTER JOIN BB_STORAGEVOLUME95_V ARRAYVOL ON BO.TARGET_C = ARRAYVOL.GUID_C')
    fcv_data = fcv_stmt.executeQuery(sql_query)
    volumes = {}
    while fcv_data.next():
      cs_guid = fcv_data.getString('CS_GUID')
      v = {'deviceid': fcv_data.getString('DEVICEID'), 'FCPLun': fcv_data.getString('FCPLUN'), 
           'portWWN': fcv_data.getString('PORTWWN'), 'name': fcv_data.getString('NAME'), 
           'guid': fcv_data.getString('GUID'), 'arrayvol': fcv_data.getString('ARRAYVOL_GUID')}
      if cs_guid in volumes:
        volumes[cs_guid].append(v)
      else:
        volumes[cs_guid] = [v]
    fcv_data.close()
    fcv_data = None
    fcv_stmt.close()
    
    LogDebug('ComputerSystems with FC volumes:' + str(len(volumes)))
    
    # cache the SCSIVolumes also in case there are some SCSIVolumes that should be FCVolumes
    # scsi_stmt = dbConn.createStatement()
    # sql_query = (
      # 'SELECT CS.GUID_C AS CS_GUID, SCSIVOL.DEVICEID_C AS DEVICEID, SCSIVOL.NAME_C AS NAME, SCSIVOL.SCSILUN_C AS SCSILUN, SCSIVOL.GUID_C AS SCSI_GUID ' +
      # 'FROM BB_SCSIVOLUME2_V SCSIVOL, BB_COMPUTERSYSTEM40_V CS WHERE SCSIVOL.PK__PARENTSTORAGEEXTENT_C = CS.PK_C AND CS.PK_C IN ' +
      # '( SELECT CS.PK_C ' +
      # 'FROM BB_FCVOLUME55_V FCV, BB_COMPUTERSYSTEM40_V CS WHERE FCV.PK__PARENTSTORAGEEXTENT_C = CS.PK_C )')
    # scsi_data = scsi_stmt.executeQuery(sql_query)
    # scsi_volumes = {}
    # while scsi_data.next():
      # cs_guid = scsi_data.getString('CS_GUID')
      # v = {'deviceid': scsi_data.getString('DEVICEID'), 'SCSILun': scsi_data.getString('SCSILUN'), 'name': scsi_data.getString('NAME'), 'guid': scsi_data.getString('SCSI_GUID')}
      # if cs_guid in scsi_volumes:
        # scsi_volumes[cs_guid].append(v)
      # else:
        # scsi_volumes[cs_guid] = [v]
    # scsi_data.close()
    # scsi_stmt.close()
    
    # get SCSIPaths
    stmt = dbConn.createStatement()
    sql_query = (
      'SELECT ' + 
      ' CS.GUID_C AS CS_GUID, CS.NAME_C AS CS_NAME, PATH.DESCRIPTION_C AS DESCRIPTION, ' + 
      ' HEP.WORLDWIDENAME_C AS WWN, PATH.GUID_C AS PATH_GUID, ARRAYVOL.GUID_C AS ARRAYVOL_GUID ' + 
      'FROM BB_SCSIPATH21_V PATH, BB_SCSIPROTOCOLENDPOINT3_V HEP, ' +
      ' BB_SCSIPROTOCOLCONTROLLER20_V CONT, BB_COMPUTERSYSTEM40_V CS, ' +
      ' BB_STORAGEVOLUME95_V ARRAYVOL ' +
      'WHERE PATH.LUN_C IS NULL AND ' + 
      ' PATH.PK__VOLUME_C IS NULL AND ' +
      ' PATH.PK__HOSTENDPOINT_C = HEP.PK_C AND ' +
      ' HEP.PK__PARENTSCSIPROINT_4324E367C = CONT.PK_C AND ' +
      ' CONT.PK__PARENTPROTOCOLCONTROLLER_C = CS.PK_C AND ' +
      ' PATH.PK__ARRAYVOLUME_C = ARRAYVOL.PK_C')
    mo_data = stmt.executeQuery(sql_query)
    paths = []
    while mo_data.next():
      description = mo_data.getString('DESCRIPTION')
      # parse pathname from description
      desc_dict = dict(re.findall(r'(\S+)=(".*?"|\S+)', description))
      name = None
      if 'pathname' in desc_dict:
        pathname = str(desc_dict['pathname'])
        name = pathname.split('/')[-1]
      elif 'part' in desc_dict:
        # if Windows then replace PHYSICALDRIVE with 'Disk ' 
        pathname = str(desc_dict['part']).replace('PHYSICALDRIVE', 'Disk ')
        name = pathname
      else:
        LogDebug('Could not find pathname in description field: ' + str(description))
        continue
      cs_guid = mo_data.getString('CS_GUID')
      wwn = mo_data.getString('WWN')
      path_guid = mo_data.getString('PATH_GUID')
      path_arrayvol = mo_data.getString('ARRAYVOL_GUID')
      LogDebug('pathname=' + pathname + ';path_guid=' + path_guid + ';cs_guid=' + cs_guid + ';wwn=' + wwn)
      found = False
      if cs_guid in volumes:
        # loop through all FC volumes on CS
        for volume in volumes[cs_guid]:
          # LogDebug('volume=' + str(volume))
          # look for matching WWN and path
          # TODO arrayvol could be null on both? no scipath
          if ( volume['portWWN'] == wwn or volume['arrayvol'] == path_arrayvol ) and ( volume['deviceid'] == pathname or volume['name'] == name ):
            LogDebug('volume=' + str(volume))
            # loop again and look for volumes with the same FCPLun and matching WWN
            found_match = False
            for v in volumes[cs_guid]:
              # look for another volume on this CS with same WWN and LUN and different name
              if v['portWWN'] == wwn and v['FCPLun'] == volume['FCPLun'] and not ( v['deviceid'] == pathname or v['name'] == name ):
                LogDebug('matching LUN volume=' + str(v))
                found_match = True
            found = True
            # if no matching duplicate LUN/WWN combo then update the SCSIPath and volume FCPLun is set (otherwise matching on existing arrayvol)
            if found_match is False and not volume['FCPLun'] is None:
              sPath = sensorhelper.newModelObject('cdm:dev.SCSIPath')
              sPath.setGuid(Guid(path_guid))
              sPath.setLUN(int(volume['FCPLun']))
              LogDebug(' Defining SCSIPath: ' + str(sPath))
              paths.append(sPath)
              break
            else:
              # build relationships here instead of letting topoagent build due to the matching LUN/WWN
              fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
              fcv.setGuid(Guid(volume['guid']))
              vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume') # define virtual storage volume
              vsv.setGuid(Guid(mo_data.getString('ARRAYVOL_GUID')))
              
              bo = sensorhelper.newModelObject('cdm:dev.BasedOnExtent')
              bo.setSource(fcv)
              bo.setTarget(vsv)
              bo.setType('com.collation.platform.model.topology.dev.BasedOnExtent')
              fcv.setBasedOn(sensorhelper.getArray([bo],'cdm:dev.BasedOnExtent'))
              LogDebug(' Defining FCVolume: ' + str(fcv))
              paths.append(fcv)
              
              # not messing with RealizesExtent from the other side because it has potential to cause issues
              #fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
              #fcv.setGuid(Guid(volume['guid']))
              #vsv = sensorhelper.newModelObject('cdm:dev.StorageVolume') # define virtual storage volume
              #vsv.setGuid(Guid(mo_data.getString('ARRAYVOL_GUID')))
              #realizes = sensorhelper.newModelObject('cdm:dev.RealizesExtent')
              #realizes.setSource(vsv)
              #realizes.setTarget(fcv)
              #realizes.setType('com.collation.platform.model.topology.dev.RealizesExtent')
              #vsv.setRealizedBy(realizes)
              #LogDebug(' Defining StorageVolume: ' + str(vsv))
              #paths.append(vsv)
              
              # set scsipath Volume so it won't come up next time
              fcv = sensorhelper.newModelObject('cdm:dev.FCVolume')
              fcv.setGuid(Guid(volume['guid']))
              sPath = sensorhelper.newModelObject('cdm:dev.SCSIPath')
              sPath.setGuid(Guid(path_guid))           
              sPath.setVolume(fcv)
              LogDebug(' Defining SCSIPath: ' + str(sPath))
              paths.append(sPath)
              break
      else:
        LogInfo('No volumes for host ' + cs_guid)
        
    
    mo_data.close()
    stmt.close()
    dbConn.close()
    
    num_threads = 10
    global output
    output = Output()
    mo_array = MO_Array(paths)
    threads = []
    # only create enough threads needed
    if len(paths) < num_threads:
        num_threads = len(paths)
    for c in range(0, num_threads):
      t = threading.Thread(target=worker, args=(mo_array,))
      t.start()
      threads.append(t)

    for t in threads:
      t.join()
                  
  except SystemExit, desc:
      # known exit
      pass
  except Exception, desc:
      print "General error: " 
      print desc
      (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
      traceback.print_exc(ErrorTB)
  
  sys.exit(0)

#=====================================================================================
#   MAIN
#=====================================================================================

if __name__ == "__main__":
  main()
