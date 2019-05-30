#!/usr/bin/env ../bin/jython_coll

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

delete.jy -- This script is used to delete data and adds threading

DESCRIPTION:

CAVEATS:

   Tested in 7.3.0.2


Author:  Mat Davis (current author)
     mdavis5@us.ibm.com

History:

'''
# Standard Jython/Python Library Imports

import sys
import java
import os

# from Java [additional imports - not sure why]...
from java.sql import DriverManager
from java.sql import Statement
from java.sql import SQLException
from java.lang import Class
from java.lang import System
from java.util import Properties
from java.lang import Boolean


# Set the Path information
coll_home = System.getProperty("com.collation.home")
#System.setProperty("jython.home",coll_home + "/external/jython-2.1")
#System.setProperty("python.home",coll_home + "/external/jython-2.1")
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

# Import the TADDM Java Libraries  [Following Required for api access]
from com.collation.platform.util import Props
from com.collation.proxy.api.client import *
from com.ibm.cdb.api import ApiFactory
from com.collation.platform.util import ModelFactory
from com.collation.platform.model import Guid
from com.collation.platform.os import OsUtils
from com.collation.platform.logger import LogFactory
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

import sensorhelper

# Some default GLOBAL Values (Typically these should be in ALL CAPS)

False = Boolean(0)
True = Boolean(1)

VERSION = "1.0"

def usage():
    print """ \
usage: delete [options] [ -t num ] -m query | -g guids


   Delete Model Objects returned by query or listed via guid

    Options:

    -u userid           User required to login to TADDM Server
                        Defaults to 'administrator'

    -p password         Password for TADDM Server user
                        Defaults to 'collation'

    -h                  print this message


    Arguments:

    -m                 MQL query
    -g                 GUID list to delete. Comma separated GUIDs.
    -t num             Number of threads to use for deletion, defaults to single thread
    """

def print_options(*args):
    for line in args:
        print "    " + str(line)

def print_action_header(msg):
    print 75*"="
    l = len(msg)
    padding = (75-l)/2
    print padding*" " + msg
    print 75*"="

def print_model_objects(mo_list):
    print_model_object_header()
    for mo in mo_list:
        print_model_object(mo)

def print_model_object_header():
    print ""
    print 65*"-"
    print "%32s" % ("GUID")
    print 65*"-"
    
def print_model_object(mo):
    print "%32s" % (mo.getGuid())

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
            output.println(" " + str(mo.getGuid()) + "  --> Removing object")
            api.delete([mo], None)
            output.println(" " + str(mo.getGuid()) + "  --> Success")
        except:
            output.println(" " + str(mo.getGuid()) + "  --> Failed")
        mo = mo_array.get()
    
    api.close()
    sess.close()
    conn.close()

def guid_worker(guid_array):
    conn = ApiFactory.getInstance().getApiConnection(Props.getRmiBindHostname(),-1,None,0)
    sess = ApiFactory.getInstance().getSession(conn, userid, password, ApiSession.DEFAULT_VERSION)
    api = sess.createCMDBApi()
    
    guid = guid_array.get()
    while guid:
        try:
            output.print_guid(guid)
            output.println(" " + str(guid) + "  --> Removing object")
            api.delete([guid], None)
            output.println(" " + str(guid) + "  --> Success")
        except:
            output.println(" " + str(guid) + "  --> Failed")
        guid = guid_array.get()
    
    api.close()
    sess.close()
    conn.close()
    
def main():

    # define DB connection
    dbConn = None
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
        mql_query = None
        guid_list = None
        num_threads = 1
        for o, a in opts:
            if o == "-u":
                userid = a
            elif o == "-p":
                password = a
            elif o == "-m":
                mql_query = a
            elif o == "-g":
                guid_list = a.split(',')
            elif o == "-t":
                num_threads = int(a)
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

        if mql_query is not None or guid_list is not None:
            model_objects = []
            conn = ApiFactory.getInstance().getApiConnection(Props.getRmiBindHostname(),-1,None,0)
            sess = ApiFactory.getInstance().getSession(conn, userid, password, ApiSession.DEFAULT_VERSION)
            api = sess.createCMDBApi()
        else:
            usage()
            sys.exit()
        
        if mql_query is not None:
            to_expire_count = api.findCount(str(mql_query), None)
        else:
            to_expire_count = len(guid_list)
		
        print "Deleting: " + str(to_expire_count)
		
        if mql_query is not None:
            mo_data = api.executeQuery(str(mql_query), 0 , None, None)

        # Now we take mo_data and process it... 

        print_model_object_header()
        to_process_mos = []
        if mql_query is not None:
            while (mo_data.next()):
                mo = mo_data.getModelObject(0)
                to_process_mos.append(mo)
        else:
            for guid in guid_list:
                to_process_mos.append(Guid(guid))
                
        if to_process_mos:
            global output
            output = Output()
            to_process_mos.reverse()
            mo_array = MO_Array(to_process_mos)
            threads = []
            # only create enough threads needed
            if len(to_process_mos) < num_threads:
                num_threads = len(to_process_mos)
            for c in range(0, num_threads):
                if mql_query is not None:
                    t = threading.Thread(target=worker, args=(mo_array,))
                else:
                    t = threading.Thread(target=guid_worker, args=(mo_array,))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()
            
    except SQLException, desc:
        print "SQL Error: " 
        print desc
        warn = desc.getNextException()
        if (warn is not None):
          print "getNextException: " + warn.getMessage()
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