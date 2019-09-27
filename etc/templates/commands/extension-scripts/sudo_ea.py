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

SCRIPT OVERVIEW (This section would be used by doc generators)

sudo_ea.py -- This script is used to define extended attributes for the sudo
 discovery extension

DESCRIPTION:

CAVEATS:

   Tested in 7.3.0.6


Author:  Mat Davis (current author)
     mdavis5@us.ibm.com

History:

'''
# Standard Jython/Python Library Imports

import sys
import java
import os

# from Java [additional imports - not sure why]...
from java.lang import Boolean
from java.lang import System

# Set the Path information
coll_home = System.getProperty("com.collation.home")

System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

# Import the TADDM Java Libraries
from com.collation.platform.util import Props

# More Standard Jython/Python Library Imports
import traceback
import getopt

import sensorhelper
import ext_attr_helper as ea

# Some default GLOBAL Values (Typically these should be in ALL CAPS)

False = Boolean(0)
True = Boolean(1)

VERSION = "1.0"

def usage():
    print """ \
usage: sudo_ea.py [options]


   Delete Model Objects returned by query or listed via guid

    Options:

    -u userid           User required to login to TADDM Server
                        Defaults to 'administrator'

    -p password         Password for TADDM Server user
                        Defaults to 'collation'

    -h                  print this message

    """

def main():

  try:
    try:
      opts, args = getopt.getopt(sys.argv[1:], 'u:p:hm:g:t:', ['help'] )
    except getopt.GetoptError, err:
      # print help information and exit:
      print str(err) # will print something like "option -a not recognized"
      usage()
      sys.exit(2)
    
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
    if userid is None:
      userid = "administrator"

    if password is None:
      password = "collation"
    #
    # Initialize
    #
    api = ea.get_taddm_api(Props.getRmiBindHostname(), userid, password)
    attr_names = [ 'sudo_verified', 'sudo_lsof', 'sudo_hba' ]
    for attr_name in attr_names:
      print 'Creating ' + attr_name + ' String EA on UnitaryComputerSystem'
      created = ea.createExtendedAttributes(api, attr_name, 'String', 'com.collation.platform.model.topology.sys.UnitaryComputerSystem')
      print ' Success: ' + str(created)
    api.close()
          
  except SystemExit, desc:
    # known exit
    pass
  except Exception, desc:
    print "General error: " 
    print desc

  sys.exit(0)

#=====================================================================================
#   MAIN
#=====================================================================================

if __name__ == "__main__":
  main()