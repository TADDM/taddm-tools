#!/usr/bin/env ../bin/jython_coll_253
#
############### Begin Standard Header - Do not add comments here ###############
#
# Licensed Materials - Property of IBM
#
# Restricted Materials of IBM
#
# 5724-N55
#
# (C) COPYRIGHT IBM CORP. 2006, 2007, 2010, 2014.  All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
############################# End Standard Header ##############################

import sys

from java.lang import System
coll_home = System.getProperty("com.collation.home")
jython_home = System.getProperty("python.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import getopt
import traceback
import string
import re
import tempfile
import StringIO
import threading
import logging
import imp
import os.path
import shutil

import time

from java.lang import IllegalArgumentException
from com.ibm.cdb.api import ApiFactory
from com.collation.platform.model import Guid
from com.collation.proxy.api.client import ApiLoginException
from com.ibm.cdb.platform.ip import IPv4Utils
from getopt import GetoptError
from com.collation.platform.util import ModelFactory
from java.lang import Class

#
# Set up logging...
#
logging.basicConfig(filename=coll_home + '/log/loadscope.log',level=logging.INFO,
                    format='%(asctime)-15s (%(threadName)-10s) %(message)s',
                    )
                    
##############################
# usage()       prints script usage
##############################
def usage():
    print "Usage:"
    print "    loadscope.jy [-d] [-q] [-C] -u <username> -p <password> clearAll | (clearScope <name>) | (clearScopeSet <name>) | ([-s <ScopeSetName>|-g <ScopeGroupName>] load [<scopefile>])"
    print 
    print "-d"
    print "Turns on verbose debug logging."
    print 
    print "-q"
    print "Loads the scope without performing synchronization."
    print 
    print "-C"
    print "This parameter makes the loadscope.jy file delete the scope. It does not, however, delete the ScopeElements assigned to the scope that are later removed by a Topology Builder agent."
    print 
    print 
    print 'To delete scope or scope group: '
    print '              loadscope.jy -u <username> -p <password> clearScope <name>'
    print 'DEPRECATED:   loadscope.jy -u <username> -p <password> clearScopeSet <name>'
    print
    print 'To delete all scopes and scope groups: '
    print 'loadscope.jy -u <username> -p <password> clearAll'
    print
    print 'To load scope:'
    print 'loadscope.jy -u <username> -p <password> -s <ScopeSetName> load <scopefile>'
    print
    print 'To load scope group:'
    print 'loadscope.jy -u <username> -p <password> -g <ScopeGroupName> load <scopefile>'
    print
    print "The format of the <scopefile> for loading scope sets is:"
    print "scope,[exclude_scope:exclude_scope:exclude_scope...],[description]"
    print
    print "'scope' takes one of the following three forms:"
    print "\tsubnet scopes"
    print "\t\t1.2.3.4/255.255.255.0"
    print "\taddress scopes"
    print "\t\t1.2.3.4"
    print "\trange scopes"
    print "\t\t1.2.3.4-5.6.7.8"
    print
    print "\tThe scope file may contain any number of scopes and the scopes may be any combination of the above three types.  Obviously, address scopes should not have exclusions."
    print
    print
    print "The format of the <scopefile> for loading scope groups is:"
    print "\tscopeSet1"
    print "\tscopeSet2"
    print 
    print "\t'scopeSet' is name of existing scope set to be added into group"
    print 

##############################
# LogError print exception information
##############################
def LogError(msg):
    if msg:
        print "\n\nError: ", msg
    else:
        # Quick-and-dirty error logging: This code prints the
        # stack-trace that you see normally when an unhandled
        # exception crashes your script.
        (ErrorType, ErrorValue, ErrorTB) = sys.exc_info() 
        print "\n\n***ERROR:"
        print sys.exc_info()
        traceback.print_exc(ErrorTB)

##############################
# Synchronized array of model objects
##############################
class MO_Array(object):
    def __init__(self, mo_array=None):
        self.lock = threading.Lock()
        self.mo_array = mo_array

    def get(self):
        logging.debug('Waiting for mo_array lock')
        self.lock.acquire()
        mo = None
        try:
            logging.debug('Acquired mo_array lock')
            if self.mo_array:
                mo = self.mo_array.pop()
        finally:
            self.lock.release()
        return mo

def worker(mo_array):
    logging.debug("Creating TADDM API Connection")
    conn = ApiFactory.getInstance().getApiConnection(-1,None,0)
    sess = ApiFactory.getInstance().getSession(conn, user_name, password, 0)
    api = sess.createCMDBApi()
    logging.debug("TADDM API Connection CREATED")
    
    mo = mo_array.get()
    while mo:
        try:
            #output.print_model_object(mo,print_laststored)
            #output.println(" " + str(mo.getGuid()) + "  --> Removing object")
            logging.info(" " + mo.toString() + "  --> Removing object")
            api.delete([mo], None)
            #output.println(" " + str(mo.getGuid()) + "  --> Success")
            logging.info(" " + mo.toString() + "  --> Success")
        except Exception, desc:
            LogError("Failed to delete")
            print desc
            #output.println(" " + str(mo.getGuid()) + "  --> Failed")
        mo = mo_array.get()
    
    api.close()
    sess.close()
    conn.close()
        
############################################
# clear_scopeSet should clear only the scope set or scope group with the name
#
###############################################
def clear_scopeSet(api, scope_name, doNotExit, clearParent):
    try:
        depth = 2
        if shallow_delete != 0:
            depth = 1
        scope_guid = api.find("Select guid from Scope where name == '" + scope_name +"'" ,1, None, None)
        i = 0
        delete_list = list([])
        if int(len(scope_guid)) == 0:
            print "Nothing to be deleted"
            return

        scope_elements = str(scope_guid[0]).split(";")
        while (i < int(len(scope_elements))):
            check = scope_elements[i].split("=")
            if check[0] == "guid" or check[0] == "{guid":
                elements = api.find("select guid from ScopeElement where keyGuid == '" + check[1] + "'",1, None, None)
                for element in elements:
                    y=str(element).split(";")
                    j = 0
                    while (j < int(len(y))):
                        incheck = y[j].split("=");
                        if incheck[0] == "guid" or incheck[0] == "{guid":
                            delete_list.append(Guid(incheck[1]))
                        j = j + 1
                if clearParent:
                    delete_list.append(Guid(check[1]))
            i = i + 1
        if int(len(delete_list)) > 0:
            logging.info("Deleting: " + str(delete_list))
            print "Deleting: " + str(delete_list)
            #api.delete(delete_list, None)
            #to_process_mos.reverse()
            num_threads = 10
            mo_array = MO_Array(delete_list)
            threads = []
            # only create enough threads needed
            while len(delete_list) < num_threads*3 and num_threads > 1:
                num_threads = num_threads-1
            for c in range(0, num_threads):
                t = threading.Thread(target=worker, args=(mo_array,))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()
        
            logging.info("Delete finished")
            api.synchScopes()
            logging.info("Sync complete")
        else:
            print "Nothing to be deleted"
        if doNotExit == 0:
            exit(0)
    except:
        LogError("Problem deleting Scope: " + scope_name)
        if doNotExit == 0:
            exit(1)

##############################
# clear_all_scopes      Removes all the scopes presently in the system
#                       uses XPath on the XML scope data returned by the API
#                       to extract the ScopeSet name and objectId in the database.
##############################
def clear_all_scopes(api):
    try:
        depth = 2
        if shallow_delete != 0:
            depth = 1
        scopes = api.find("Scope",depth, None, None)
        delete_list = list([])
        for x in scopes:
            for line in  str(x).split(";"):
                check = line.split("=")
                if check[0] == 'guid':
                    delete_list.append( Guid (check[1]) )
                    if shallow_delete == 0 and x.hasElements():
                        elements=x.getElements();
                        k = 0
                        while (k < int(len(elements))):
                            print 'guid to delete ' + str( elements[k].getGuid() )
                            delete_list.append( elements[k].getGuid() )
                            if elements[k].hasExcludes():
                                excludes=elements[k].getExcludes();
                                h = 0
                                while(h<int(len(excludes))):
                                    print 'guid to delete ' + str( excludes[h].getGuid() )
                                    delete_list.append( excludes[h].getGuid() )
                                    h = h + 1
                            k = k + 1
                    print 'guid to delete ' + check[1]
        if len(delete_list) > 0:
            logging.info("Deleting: " + str(delete_list))
            print "Deleting: " + str(delete_list)
            #api.delete(delete_list, None)
            #to_process_mos.reverse()
            num_threads = 10
            mo_array = MO_Array(delete_list)
            threads = []
            # only create enough threads needed
            while len(delete_list) < num_threads*3 and num_threads > 1:
                num_threads = num_threads-1
            for c in range(0, num_threads):
                t = threading.Thread(target=worker, args=(mo_array,))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()
        
            logging.info("Delete finished")
            api.synchScopes()
            logging.info("Sync complete")
        else :
            print "Nothing to be deleted"
            exit(0)
    except:
        LogError("Problem deleting Scopes")
        exit(1)

def load_groups(api, scope_set, scope_file, quick_load):
    clear_scopeSet(api, scope_set, 1, 0)
        
def load_scope(api, scope_set, scope_file, quick_load):
    global fuid
    clear_scopeSet(api, scope_set, 1, 0)
    
def exit(code):
    if api_ses != None:
        print "Closing session"
        api_ses.close()
    System.exit(code)

def import_(filename):
    (path, name) = os.path.split(filename)
    (name, ext) = os.path.splitext(name)

    try:
        (file, filename, data) = imp.find_module(name, [path])
    except:
        print '****************************************************************'
        print 'IMPORTANT: Make sure that bin/loadscope.jy has been copied to   '
        print 'bin/loadscope.py (.py extension)                                              '
        print '****************************************************************'
        raise
    return imp.load_module(name, file, filename, data)

#################################
#   Main function
#################################
def main():
    global debug
    global shallow_delete
    global api_ses
    global user_name
    global password
    
    # options
    debug=0
    # quick_load won't call api.synchScopes() - to be used when bulk-loading multiple scopes
    # the last scope loaded must not use this flag, so all scopes get synchronized then 
    quick_load=0
    shallow_delete=0
    user_name = ""
    password = ""
    scope_set = ""
    load_scopegroups = 0
    load_scopesets = 0
    
    # Parse command line    
    try:
        (opts, pargs) = getopt.getopt(sys.argv[1:], 'dqCu:p:s:g:')

        for (opt, opt_val) in opts:
            if opt == '-u':
                user_name = opt_val
            elif opt == '-p':
                password = opt_val
            elif opt == '-s':
                scope_set = opt_val
                load_scopesets = 1
            elif opt == '-g':
                scope_set = opt_val
                load_scopegroups = 1
            elif opt == '-d':
                debug=1
            elif opt == '-q':
                quick_load=1
            elif opt == '-C':
                shallow_delete=1

        operation = pargs[0]
        if operation == "load" or operation == "clearScope" or operation == "clearScopeSet":
            op_arg = pargs[1]

        # check operation
        if operation != "load" and operation != "clearScope" and operation != "clearScopeSet" and operation != "clearAll":
            raise IllegalArgumentException("Unknown command: " + operation)
            
        # check options
        if user_name == "" or password == "":
            raise IllegalArgumentException("Username and Password are required")
        if operation == "load" and scope_set == "":
            raise IllegalArgumentException("ScopeSet is required for load")
        if operation != "load" and scope_set != "":
            raise IllegalArgumentException("ScopeSet option is only applicable for load command")
        if load_scopegroups==1 and load_scopesets==1:
            raise IllegalArgumentException("Only one option of -g and -s can be specified at the same time")
        
        # check invalid characters
        if "." in scope_set or "/" in scope_set or "'" in scope_set:
            print "Scope Set name cannot contain following characters: , ' / \nScoping properties to such Scope Set will not work.\n"
        
    except GetoptError, e:  # unknown option  
        print str(e)
        usage()
        exit(1)
    except IllegalArgumentException, e:
        print e.getMessage()
        usage()
        exit(1)
    except:
        usage()
        exit(1)

    # Execute command
    try:
        print "Connecting to TADDM"
        api_con = ApiFactory.getInstance().getApiConnection(-1,None,0)
        api_ses = ApiFactory.getInstance().getSession(api_con,user_name,password,0)
        api = api_ses.createCMDBApi()

        if operation == 'clearAll':
            clear_all_scopes(api)
        elif operation == 'clearScope' or operation == "clearScopeSet":
            clear_scopeSet(api, op_arg, 0, 1)
        elif operation == 'load' and load_scopesets==1:
            load_scope(api, scope_set, op_arg, quick_load)
        elif operation == 'load' and load_scopegroups==1:
            load_groups(api, scope_set,op_arg, quick_load)
            
    except ApiLoginException, ale:
        LogError("Login failure: " + ale.getMessage().replace("com.collation.proxy.api.client.ApiException: ", ""))
        exit(1)
    except Exception, e:
        LogError(str(e))
        exit(1)

    # copy .jy file to .py so that import will work
    shutil.copyfile(coll_home + '/bin/loadscope.jy', coll_home + '/bin/loadscope.py')
    m = import_(coll_home + '/bin/loadscope.py')
    m.main()

#################################
#  Main section
#################################
if __name__ == '__main__':
    # globals declarations
    debug = 0
    fuid = None
    api_ses = None 
    
    main()
