#!/usr/bin/env ./../bin/jython_coll_253

############### Begin Standard Header - Do not add comments here ###############
#
# File:     storage.jy
# Version:  1.0
# Modified: 5/31/13
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

import sys
import java
import traceback

from com.collation.platform.util import Props
from com.collation.discover.util import InterMessageUtils
from com.collation.monitor.agent import Severity
from java.lang import *
from java.util import *
from java.io import *

class getEvents:
  def getEvents( self,runId ):
    property = System.getProperty("file.separator");
    events = ArrayList(4);
    fileName = Props.getHome() + property + Props.getDirectoryToStoreEvents() + property + runId + ".ser";
    file = File(fileName);
    if (file.exists()):
      fileInputStream = FileInputStream(fileName);
      ois = ObjectInputStream(fileInputStream);
      while (1) :
        try:
          event = ois.readObject();
          events.add(event);
        except:
          #print "end of file"
          break
      ois.close();
    else:
      print "RunID:  " + str(runId) + " Not Found!!!"
      System.exit(1)
    return events

  def getRunIDs( self):
    property = System.getProperty("file.separator")
    eventDirectory = Props.getHome() + property + Props.getDirectoryToStoreEvents() + property
    idList = []
    #print "Possible RunIDs: "
    for f in java.io.File(eventDirectory).listFiles():
      #print str(f)
      run_id = str(f.getName()).split(".")[0]
      idList.append(run_id)

    return  idList

  def getLatestID(self):
    RunIDs = self.getRunIDs() 
    RunIDs.sort()
    id = RunIDs.pop()
    return id

  def printRunIDs(self):
    # place the Highest Number in first
    RunIDs = self.getRunIDs()
    RunIDs.sort()
    print "Listing available RunIDs"
    for id in RunIDs:
      print "    " + str(id)
    return
    
def getDescription( event ):
  try:
    desc = event.getDescription()
  except:
    eventString = event.toString()
    parts=eventString.split(";")
    subparts=parts[7].split("!")
    partsToChange = []
    i = 0
    for subpart in subparts:
      if (subpart.find(".R.") > -1):
        partsToChange.append(i-2)
      i = i + 1
    i = 0
    newDescription = "";
    for subpart in subparts:
      if ( i > 0 ):
        newDescription = newDescription + "!"
      if ( i in partsToChange ):
        newDescription = newDescription + "com.collation.discover.result.messages.DiscoverResultLocalizedMessages"
      else:
        newDescription = newDescription + subpart
      i = i + 1

    try:
      desc = InterMessageUtils.getMessage(newDescription)
    except:
      import sys
      print 'uncaught exception', sys.exc_type, sys.exc_value, sys.exc_traceback
      desc = "Unknown"
  return desc

def getSeverity( event ):
  try:
    severity = Severity.getDescription( event.getNewSeverity() )
  except:
    severity = "Unknown"
  return severity

def getName( event ):
  try:
    name = event.getAttributeName()
  except:
    name = "Unknown"
  return name

def getSensor( event ):
  try:
    name = event.getAttributeName()
    sensor = name.split('(')[0]
  except:
    sensor = "Unknown"
  return sensor

def getHostName( event ):
  try:
    hostname = event.getDetails().getHostName()
  except:
    hostname = "Unknown"
  return hostname
  
def getIp( event ):
  try:
    name = event.getAttributeName()
    ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', name )[0]
  except:
    ip = "Unknown"
  return ip

def convertMilliToString( millis ):
  hours, ms = divmod(millis, 3600000)
  min, ms = divmod(millis, 60000)
  sec = float(millis) / 1000
  sec = sec - (min * 60)
  min = min - (hours * 60)
  return "%i:%02i:%06.3f" % (hours, min, sec)
    
def usage():
    print """ \

Usage : hba_report.py [list|latest|all|RunID]

This script looks for HostStorageSensor errors and tries to match those against
physical targets to help identify where there might be HBA issues with discovery.

Arguments:

list   -- List available RunIds from the dist/events directory

latest -- Use the 'latest' RunID from the dist/events directory

all    -- Use all RunID from the dist/events directory combined

RunID  --  A specific RunID. (use 'list' to see what's available)  
"""

if __name__=='__main__':
  
  try:

    if sys.argv[1] == "list":
      t = getEvents()
      t.printRunIDs()
      System.exit(1)
    elif sys.argv[1] == "latest":
      t = getEvents()
      RunID = [t.getLatestID()]
    elif sys.argv[1] == "all":
      t = getEvents()
      RunID = t.getRunIDs()
    elif sys.argv[1]:
      # if its anything else, we call it TRUE...
      RunID = [sys.argv[1]]
      t = getEvents()
    else:
      usage()
      System.exit(1)
  except:
      usage()
      System.exit(1)

  bad = {}
  good = {}
  indifferent = {}
  for id in RunID:
    s = t.getEvents( id )
    it = s.iterator()
    bysensor = {}
    # iterate over all events and look for storage events
    while it.hasNext() :
      event= it.next()
      
      sensor = getSensor( event )
      if not 'HostStorageSensor' in sensor:
        continue # only interested in HSS
        
      sev = getSeverity( event )
      name = getName( event )
      ip = getIp( event )
      host = getHostName( event )
      dt = Date( event.getTimeStamp() )
      desc = getDescription( event )
      if desc != None:
        desc = desc.replace('\n', ' ')

      # tuple with all values 
      t = host, sensor, sev, name, dt, desc, ip

      if sev == 'minor' or sev == 'normal':
        # check if good event was already added for ip/sensor combo
        if good.has_key(name):
          # replace old event with newer event (like discovery UI does)
          if good[name][4].before(dt):
            #print 'replacing good...'
            #print good[name]
            #print 'with newer good...'
            #print t
            good[name] = t
          #else:
            #print 'skipping good...'
            #print t
        else:
          good[name] = t
      elif sev == 'info':
        #if indifferent.has_key(name):
        #    print 'indifferent key exists: ' + name
        indifferent[name] = t
        #print 'indifferent...'
        #print t
      elif sev == 'critical' or sev == 'major':
        # check if bad event was already added for ip/sensor combo
        if bad.has_key(name):
          # replace old event with newer event (like discovery UI does)
          if bad[name][4].before(dt):
            #print 'replacing bad...'
            #print bad[name]
            #print 'with newer bad...'
            #print t
            bad[name] = t
          #else:
            #print 'skipping bad...'
            #print t
        else:
          bad[name] = t
      else:
        print "UNKNOWN EVENT TYPE FOUND..."
        print t
      
  # iterate over all bad events, sort by IP before iteration
  keylist = bad.keys()
  keylist.sort()
  for k in keylist:
    # get value for key
    v = bad[k]
    sensor = v[1]
    host = v[0]
    #severity = v[2]
    # skip session sensor failures where snmpmib2 was successful
    if sensor == 'SessionSensor' and severity == 'critical' and good.has_key('SnmpMib2Sensor(' + ip + ')'):
      #print 'found good snmp for bad session...'
      #print good['SnmpMib2Sensor(' + ip + ')']
      continue
    name = v[3]
    dt = v[4]
    desc = v[5]
    ip = v[6]
    #s = '\"' + sensor + '\",\"' + host + '\",\"' + dt.toString() + '\",\"' + name + '\",\"' + severity + '\",\"' + desc + '\"'
    s = '\"' + host + '\",\"' + ip + '\",\"' + dt.toString() + '\",\"' + name + '\",\"' + desc + '\"'
    print s