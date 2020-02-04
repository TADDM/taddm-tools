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

SCRIPT OVERVIEW

checkViprVMs.py - This script is used to check if hosts in ViPR_VMs scope are being
  discovered succesfully

DESCRIPTION:


CAVEATS:

Author:  Mat Davis
     mdavis5@us.ibm.com

History:

  Version 1.0  -- 2019/07 -- Initial Version

'''

VERSION = "1.00"

# Standard Jython/Python Library Imports

import sys
import java
import time


# from Java [additional imports - not sure why]...

from java.lang import System
from java.lang import Class
from java.util import Properties
from java.io import FileInputStream
from java.lang import String
from java.lang import Boolean
from java.lang import Runtime

# Import the TADDM Java Libraries  [Following Required for api access]
from com.collation.proxy.api.client import *
from com.ibm.cdb.api import ApiFactory
from com.collation.platform.util import ModelFactory
from com.collation.platform.model.discovery.scope import IpAddressScope

# for authentication at the API level
from com.collation.platform.util import Props
from com.collation.platform.security.auth import *
from com.collation.platform.logger import LogFactory
from com.collation.proxy.api.client import *
from com.ibm.cdb.api import ApiFactory
from TaddmHelper import LogError
from TaddmHelper import LogInfo
from TaddmHelper import LogDebug

# More Standard Jython/Python Library Imports

import traceback
import string
import re
import jarray
import os
import getopt
import pprint

False = Boolean(0)
True = Boolean(1)

coll_home = System.getProperty('com.collation.home')
System.setProperty("com.collation.LogFile",coll_home + "/log/check_vipr_vms.log")

global log

log = LogFactory.getLogger("check_vipr_vms")

def usage():
  print ''' \
usage: checkViprVMs.py [options]

  Options:
  -u userid       User required to login to TADDM Server
          Defaults to 'administrator'

  -p password     Password for TADDM Server user
          Defaults to 'collation'

  -h              print this message

'''

# message to show if there are hosts in scope that aren't properly discovered
msg = '''\
The following scope elements could not be verified as being successfully
discovered via HostStorageSensor in the last 14 days. These hosts are in ViPR
and contain an RDM so they are important for storage mapping, reporting, and
billing. Ensure the following are true for each of the items:

   1) The IP is included in a scopeset that is in the normal periodic discoveries
   2) Ensure that the correct anchor/gateway is used during discovery
   3) The HostStorageSensor runs succesfully on the target host
   4) The serialNumber is properly discovered via the Linux/Windows sensor. Ensure
      that dmidecode is in the sudoers file on Linux host targets.
'''
rdmMsg = '''\
The following scope elements did not contain any RDM SCSIVolumes discovered
by the RDM.py discovery extension. Ensure that sudo is set up for sg_inq
command on the target.
'''
rdmMsgRh5 = '''\
The following scope elements did not contain any RDM SCSIVolumes discovered
by the RDM.py discovery extension. However, they are Red Hat 5, which is too
old for RDM.py discovery extension to work. These servers should be decommissioned
soon.
'''
rdmMsgWin = '''\
The following scope elements did not contain any RDM SCSIVolumes discovered
by the WindowsRDM.py discovery extension.
'''
dup_msg = '''\
The following scope elements were found multiple times by IP address. These
duplicates need to be resolved. Ensure the following are true:

   1) The serial number is being successfully discovered via sudo using dmidecode
   2) There is not a duplicate 'Powered off' VM discovered via vCenter
   3) The older/incorrect duplicates are deleted from TADDM
'''

########################
# GetScope
########################
def GetScope(element):
  try:
    # assume it's an IpAddressScope
    scope = element.getIp()
  except AttributeError:
    try:
      # next try NetworkScope
      scope = element.getIpAddress() + '/' + element.getSubnetMask()
    except AttributeError:
      try:
        # finally IpRangeScope
        scope = element.getStart() + '-' + element.getEnd()
      except AttributeError:
        pass
  return scope

def get_class_name(model_object):
  cn = model_object.__class__.__name__
  real_class_name = cn.replace("Impl","")
  return real_class_name

#=====================================================================================
#   MAIN
#=====================================================================================

if __name__ == "__main__":

#
# Handle the options
#
  try:
    opts, args = getopt.getopt(sys.argv[1:], "u:p:h", ["help"])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  userid = None
  password = None
  scopeset = None
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

  scopeset = 'ViPR_VMs'

  host = "localhost"       # we default to localhost, it COULD be changed but this script will run ON the TADDM Server

  if userid is None:
    userid = "administrator"

  if password is None:
    password = "collation"

  res = CommandLineAuthManager.authorize(userid, password)
  if res == 0 :
    print 'Authentication Failed!!!'
    sys.exit(8);
  #else:
    #print 'Authentication successful'

  #print '**** Querying scope set \'' + scopeset + '\' ****'

  conn = ApiFactory.getInstance().getApiConnection(Props.getRmiBindHostname(),-1,None,0)
  sess = ApiFactory.getInstance().getSession(conn, userid, password, ApiSession.DEFAULT_VERSION)
  api = sess.createCMDBApi()

  query = 'select name, elements from Scope where name == \'' + scopeset + '\''
  data = api.executeQuery(query,3,None,None)
  if data.next():
    age = 14 #days
    now = time.time()
    age_l = long(60*60*24*age)
    # Convert to Milliseconds...
    end_time =  (now - age_l)*1000

    scope = data.getModelObject(3)
    if scope.hasElements():
      notverified = []
      notverifiedRDMWin = []
      notverifiedRDMLin = []
      notverifiedRDMrh5 = []
      dups = []
      for element in scope.getElements():
        verified = False
        verifiedRDM = False
        scope = GetScope(element)
        #print scope + ',' + ':'.join([str(e) for e in excludes]) + ',' + element.getName()
        q = ('select fqdn, name, storageExtent, OSRunning from ComputerSystem ' +
             ' where signature is-not-null and serialNumber is-not-null ' +
             ' and exists ( ipInterfaces.displayName == \'' + scope + '\' ) ' +
             ' and ( not XA eval \'/xml[attribute[@name="decom"]]\' ' +
             '    or XA eval \'/xml[attribute[@name="decom"]="false"]\'' +
             '    or XA eval \'/xml[attribute[@name="decom"]="no"]\')' )
        hosts = api.executeQuery(q, 2, None, None)
        cs_type = None
        count = 0
        while hosts.next():
          count = count + 1
          cs = hosts.getModelObject(2)
          cs_type = get_class_name(cs)
          #print str(cs)
          if cs.hasStorageExtent():
            #print 'hasStorageExtent'
            for se in cs.getStorageExtent():
              #print str(se)
              if get_class_name(se).endswith('SCSIVolume'):
                #print str(get_class_name(se))
                #print str(end_time)
                if end_time < se.getLastStoredTime():
                  verified = True
                # include Windows check
                if se.hasDescription() and se.getDescription() == 'RDM':
                  verifiedRDM = True
        if count > 1:
          dups.append(scope + ',,' + element.getName())
        if verified is False:
          notverified.append(scope + ',,' + element.getName())
        if verifiedRDM is False:
          if cs_type is not None and cs_type.endswith('WindowsComputerSystem'):
            notverifiedRDMWin.append(scope + ',,' + element.getName())
          else:
            if cs_type is not None and cs.hasOSRunning():
              os = cs.getOSRunning()
              #print str(os.getOSVersion())
              if os.getOSVersion().startswith('Red Hat Enterprise Linux Server release 5'):
                notverifiedRDMrh5.append(scope + ',,' + element.getName())
              else:
                notverifiedRDMLin.append(scope + ',,' + element.getName())
            else:
              notverifiedRDMLin.append(scope + ',,' + element.getName())

      if len(notverified) > 0 or len(notverifiedRDMWin) > 0 or len(notverifiedRDMLin) > 0 or len(notverifiedRDMrh5) > 0 or len(dups) > 0:
        if len(notverified) > 0:
          print msg
          for nv in notverified:
            print str(nv)
          print ''
        if len(notverifiedRDMWin) > 0:
          print rdmMsgWin
          for nv in notverifiedRDMWin:
            if nv not in notverified:
              print str(nv)
          print ''
        if len(notverifiedRDMLin) > 0:
          printheader = True
          for nv in notverifiedRDMLin:
            if nv not in notverified:
              if printheader:
                print rdmMsg
                printheader = False
              print str(nv)
          print ''
        if len(notverifiedRDMrh5) > 0:
          print rdmMsgRh5
          for nv in notverifiedRDMrh5:
            print str(nv)
          print ''
        if len(dups) > 0:
          print dup_msg
          for dup in dups:
            print str(dup)
      else:
        print 'All VMs with RDM have been successfully discovered in the last 14 days.'
    else:
      print scopeset + ' does not contain any scope elements'
  else:
    api.close()
    sess.close()
    conn.close()

    print scopeset + ' not found'
    sys.exit(1)
  api.close()
  sess.close()
  conn.close()

  sys.exit(0)