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

################################################################################
#
#  This TADDM custom server extension has been designed to emulate the functionality
#  of the TADDM locationTagging feature to populate the locationTag attribute of computerSystem
#  by assigning the location that is associated with the anchor host that support the scope in
#  in which the ipAddress of the computerSystem is included. If ipAddress belongs to multiple
#  scopes, and thereby can be discovered through multiple anchor hosts, the location of the anchor 
#  host with the highest suffix will be populated into the value of the locationTag attribute.  
#
#  If the TADDM locationTagging feature is enabled for the current Discovery Server, the value to be assigned to 
#  the locationTag attribute is controlled by TADDM, and therefore this script terminates (almost)
#  immediately if it is discovered that locationTagging is enabled.
#
#  If the TADDM locationTagging is disabled, and the com.ibm.cdb.locationTag property has been specified, you
#  will many warning messages in the log files. For that reason, this script uses  a new property:
#
#                com.ibm.cdb.customLocationTag=<your default location>
#
#  to allow you to specify a default location that will be assigned to computerSystem that are relate to the local anchor,
#  or is not included in a scope that can be associated with a specific anchor host. If the com.ibm.cdb.customLocationTag
#  property has not been specified, the value 'UNKNOWN' will be used. 
#
##################################################################################
import sys
import java
from java.lang import *
from java.io import *



### initialize environment when running under TADDM Control
try:

    collation_home = System.getProperty("com.collation.home")

    System.setProperty("jython.home", collation_home + "/external/jython-2.1")
    System.setProperty("python.home", collation_home + "/external/jython-2.1")

    jython_home = System.getProperty("jython.home")
    sys.path.append(jython_home + "/Lib")
    sys.path.append(collation_home + "/lib/sensor-tools")
    sys.prefix = jython_home + "/Lib"

    ## TADDM imports
    import sensorhelper
    
except:
    ##  initialization for the non-TADDM (testing)
    pass


## These jython classes can only be loaded after the jython environment has been initialized
import traceback
import string
import re
import StringIO
import jarray
import commands


###############################################################################
###############################################################################
###############################################################################
##  
##   COMMON TADDM FUNCTIONS
##
###############################################################################
###############################################################################
###############################################################################


################################
## LogError      Error logger
################################
def LogError(msg):
    '''
    Print Error Message using Error Logger with traceback information
    '''
    try:
        log.error(msg)
    except:
        print msg    
        
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()        
    traceback.print_exc(ErrorTB)

##############################################################
## LogDebug      Print routine for normalized messages in log
##############################################################
def LogDebug(msg):
    '''
    Print Debug Message using debug logger (from sensorhelper)
    '''
    # assuming SCRIPT_NAME and template name are defined globally...
    # point of this is to create a consistent logging format to grep 
    # the trace out of
    msg = "\t" + msg
    try:
        log.debug(msg)
    except:
        if (logLevel == "DEBUG") :
            print msg
########################################################
# LogInfo Print routine for normalized messages in log
########################################################
def LogInfo(msg):
    '''
    Print INFO level Message using info logger (from sensorhelper)
    '''
    # assuming SCRIPT_NAME and template name are defined globally...
    # point of this is to create a consistent logging format to grep 
    # the trace out of
    try:
        log.info(msg)
    except:
        print msg



###############################################################################
###############################################################################
###############################################################################
##  
##   PRIVATE FUNCTIONS
##
###############################################################################
###############################################################################
###############################################################################
        

###########################################################
##  define True and False (not supported in Jython 2.1
###########################################################
def true_and_false():
    global False
    global True
    
    try:
        True and False
    except NameError:
        class bool(type(1)):
            def __init__(self, val=0):
                if val:
                    type(1).__init__(self, 1)
                else:
                    type(1).__init__(self, 0)
            def __repr__(self):
                if self:
                    return "True"
                else:
                    return "False"

            __str__ = __repr__

        bool = bool
         
        False = bool(0)
        True = bool(1)
                
###########################################################
##  read property files
###########################################################     
def readPropFile(prop_file_name):
        
        #Get the CDM FileSystemContent object for TADDM's collation.properties
        ##coll_props_file = sensorhelper.getFile(collation_home + "/etc/collation.properties");
        LogDebug("Reading properties from: " + prop_file_name)
    
        
        f = open(prop_file_name, 'r')      
        in_stream = str(f.read())
        f.flush()
        f.close()
        
        
        #Create a Java StringBufferInputStream attached to the captured collation.properties
        ##propStream = java.io.StringBufferInputStream(x)
        propStream = java.io.StringBufferInputStream(in_stream)
        
        #Create and load a Java Properties object
        props = java.util.Properties()
        props.load(propStream)
        
        
        ## Testing

        keys = props.keySet()
        LogDebug("Found " + str(keys.size()) + " properties in " + prop_file_name)
        for key in keys:
            LogDebug("read key: " + key + ": " + props.getProperty(key))
    

        return(props)

###########################################################
##  run a command on the TADDM Discovery Server
###########################################################     
def runCommand(command):    
    try:
        p = Runtime.getRuntime().exec(command);
            
        #BufferedReader stdInput = new BufferedReader(new InputStreamReader(p.getInputStream()));
        #BufferedReader stdError = new BufferedReader(new InputStreamReader(p.getErrorStream()));

        
        
        stdInput = BufferedReader(InputStreamReader(p.getInputStream()));
        stdError = BufferedReader(InputStreamReader(p.getErrorStream()));


        LogDebug("StdOut from the command:\n");
        sysout = []
        s = ""
        while s != None :
            s = stdInput.readLine()
            if s == None:
                break
            LogDebug(s);
            sysout.append(s)
            
        LogDebug("StdErr from the command:\n");
        syserr = []
        e = ""
        while e != None: 
            e = stdInput.readLine()
            if e == None:
                break
            LogDebug(e)         
            
    except IOException, e:            
         
        ##catch (IOException e) {
            LogError("exception happened - here's what I know: ");
            e.printStackTrace();
            
    return(sysout, syserr)


##############################
# get_ip_netmask        parses a scope element of the form
#                       ipaddress/netmask
#                       into a python sequence of (ip,netmask)
#                       also, if the netmask does not seem valid
#                       the netmask is set to 255.255.255.255
##############################
def get_ip_netmask(scope_element):

    #first see if the scope element consists of an address and a netmask
    if re.search(r'\/', scope_element) != None:
        #it does
        (ip, netmask) = string.split(scope_element, '/')
        if re.search(r'\d+\.\d+\.\d+\.\d+', netmask) == None:
            LogDebug(netmask, " is invalid; setting Netmask to 255.255.255.255 for ", ip)
            netmask = '255.255.255.255'
    else:
        #it does not
        ip = scope_element
        netmask = '255.255.255.255'
    return(ip, netmask)

##############################
# get_scope_type        determines the type of the provided scope
#                       either, address, subnet, or range
##############################
def get_scope_type(scope_element):

    #See if it has a '-' in it, if so then it is range
    if re.search(r'-', scope_element) != None:
        return('range')

    #Now it is either a subnet scope or a ip scope, call get_ip_netmask
    #to figure it it out
    (ip, netmask) = get_ip_netmask(scope_element)
    if netmask == '255.255.255.255':
        return('address');

    #must be a subnet
    return('subnet')


###############################################
#  call healthcheck to get the scopes
###############################################
def get_scopes_from_healthcheck():
    LogDebug("Executing command: " + healthCheck_command)
    
    output, syserr = runCommand(healthCheck_command)
                
    #scopes = {}
    taddm_scopes = []
    i = 0
        
    for line in output:
        if logLevel == "DEBUG":
            LogDebug ("read line " + str(i) + "  " + line.rstrip())
        
        inp = line.rstrip()
        
        #  filter out the header lines
        if (inp[:14] != "GROUP:  config" and inp != "" and inp[:2] != "**" and inp[:23] != "Label,Value,Description"):
                
            s = string.split(inp, ",")
            scope_name = string.strip(s[0])
            scope_elements = string.strip(s[1])
                
            if scope_elements != "":    
                taddm_scope = scope(scope_name)
                taddm_scopes.append(taddm_scope)
                
                for element in string.split(scope_elements, "|"):                
                    element = string.strip(element)
                    if element != "":     
                        LogDebug("Adding element '" + str(element) + "' to scope ' " + taddm_scope.getName())
                        taddm_scope.addElement(element)
                
    return taddm_scopes


###############################################
## read scopes from scope.properties
###############################################
def get_scopes_from_scope_properties(scope_prop_file_name):
    props = readPropFile(scope_prop_file_name)
    taddm_scopes = []
    for scope_name in props.keys():
        LogDebug("Processing scope: " + scope_name)
        scope_elements = props[scope_name]
        
        if scope_elements != "":    
            taddm_scope = scope(scope_name)
            taddm_scopes.append(taddm_scope)
                
        #if string.find(scope_elements,",") > -1:
            for element in string.split(scope_elements, ","):                
                element = string.strip(element)
                if element != "":     
                    LogDebug("Adding element '" + str(element) + "' to scope ' " + taddm_scope.getName())
                    taddm_scope.addElement(element)
                
    return taddm_scopes







###############################################################################
##  class to support scopes
###############################################################################
class scope:
    
    def __init__(self, name):
        self.__name__ = name        
        self.__elements__ = {}
        
       
    def hasName(self):
        hasName = False
        if self.__name__ != None:
            hasName = True
        return hasName
    
    def getName(self):
        return self.__name__
    
    def setName(self, name):
        self.__name__ = name
        
    def addElement(self, element):
        method = "include"
        x = len(element) - 1
        if element[:1] == "(" and element[x:] == ")":
            method = "exclude" 
            element = element[1:x]
                    
        e = None
        if self.hasElement(element) == False:
            e = scopeElement(self.__name__,element, method)    
            self.__elements__[element] = e
        elif method == "exclude":   # force exclude if the element has already been created
            e = self.getElement(element)
            if e.getMethod() != method:
                e.setMethod(method)        
            
        return e

    def hasElement(self, element):
        return self.__elements__.has_key(element)

    def hasElements(self):
        hasElements = False    
        if len(self.__elements__) > 0:
            hasElements = True
        return hasElements

    def getElements(self):
        return self.__elements__.values()

    def getElement(self, element):
        return self.__elements__[element]


###############################################################################
###############################################################################
###############################################################################
##  
##   PRIVATE CLASSES
##
###############################################################################
###############################################################################
###############################################################################



###############################################################################
##  class to support scope-elements
###############################################################################
class scopeElement:

    def __init__(self, scope, name, method):
        self.__parent__ = scope
        self.__name__ = name
        self. __method__ = method        
        self.__type__ = get_scope_type(name)
        self.__network__ = None
        self.__mask__ = None
        self.__rangeStart__ = None
        self.__rangeEnd__ = None
        
        if self.__type__ == "subnet":
            try:
                (self.__ip__, self.__mask__) = string.split(self.__name__, "/")
                self.__network__ = sensorhelper.calcNetworkAddress(self.__ip__, self.__mask__)               
            except:
                pass
        elif self.__type__ == "range":
            (self.__rangeStart__, self.__rangeEnd__) = string.split(self.__name__, "-")    
    
    def isIncluded(self, ip, mask=None):        
        isIncluded = False
        if self.containsIp(ip) and self.__method__ == "include":
            isIncluded = True
        return isIncluded

    def isExcluded(self, ip):        
        isExcluded = False
        if self.containsIp(ip) and self.__method__ == "exclude":
            isExcluded = True
        return isExcluded    
            
    def containsIp(self, ip):
        containsIp = False

        
        if self.__type__ == "address":
            if ip == self.__name__:
                containsIp = True
        
        if self.__type__ == "subnet":
            network = None
            try:
                network = sensorhelper.ipInSubnet(ip, self.__network__, self.__mask__)
            except:
                network="192.168.1"
            
            if network == self.__network__:
                containsIp = True

                
        if self.__type__ == "range":
            (i1, i2, i3, i4) = string.split(ip, ".")
            (s1, s2, s3, s4) = string.split(self.__rangeStart__, ".")
            (e1, e2, e3, e4) = string.split(self.__rangeEnd__, ".")
            
            if i1 >= s1 and i1 < e1:
                containsIp = True
            elif  i1 == s1 and i1 == e1:
                if i2 >= s2 and i2 < e2:
                    containsIp = True
                elif  i2 == s2 and i2 == e2:
                    if i3 >= s3 and i3 < e3:
                        containsIp = True
                    elif  i3 == s3 and i3 == e3:
                        if i4 >= s4 and i4 <= e4:
                            containsIp = True
            
        return containsIp
                
           
    def hasName(self):
        hasName = False
        if self.__name__ != None:
            hasName = True
        return hasName
    
    def getName(self):
        return self.__name__
    
    def setName (self, name):
        self.__name__ = name
        
    def hasMethod(self):
        hasMethod = False
        if self.__method__ != None:
            hasMethod = True
        return hasMethod    

    def getMethod(self):
        return self.__method__    

    def setMethod(self, method):
        self.__method__ = method    
        
    def hasType(self):
        hasType = False
        if self.__type__ != None:
            hasType = True
        return hasType    

    def getType(self):
        return self.__type__    

    def setType(self, elem_type):
        self.__type__ = elem_type    





##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
#
#   MAIN
#
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################


# include definition of True and False (not included in Jython 2.1
true_and_false()


LogInfo(" ====== STARTING location Tagging script ====== ")

try:
    # The first thing we need to do is get the Objects that are passed to a sensor
    (os_handle, result, computer_system, seed, log) = sensorhelper.init(targets)
    # os_handle  -->  Os handle object to target system
    # result     -->  Results Object
    # server     -->  AppServer or ComputerSystem Object that is discovered
    # seed       -->  seed object which contains information that was found prior
    #                 to this CSX running
    # Logger     -->  Object to write to sensor log

    addr = targets.get("IpAddressSeed")          # seed object which contains information that was found prior
    LogInfo("seed: " + str(seed) + "     " + seed.getClass().getName())               # to this CSX running
    LogInfo("addr: " + str(addr))               # to this CSX running

    IpAddress = str(seed)
    LogInfo("IpAddress: " + IpAddress)
    
    LogInfo(" ====== On IP Address: " + str(seed) + " ====== ")
    LogInfo(" ====== Using sensorhelper version: " + str(sensorhelper.getVersion()))
    LogDebug(" ====== Jython sys.path=" + str(sys.path))
    LogDebug(" ====== Jython script_dep.jy: sys.prefix=" + str(sys.prefix))


    api_major_version = sensorhelper.getApiMajorVersion()
    api_minor_version = sensorhelper.getApiMinorVersion()
    LogDebug("sensorhelper version is " + str(api_major_version) + "." + str(api_minor_version))
    LogDebug("TADDM is version " + sensorhelper.getTADDMVersion())

    healthCheck_command = collation_home + "/bin/healthcheck  -c checkTaddmScopes"

    
except:

    ## The following variables are used to simulate expected TADDM behavior 
    ## so the script can be tested without connecting to TADDM
    logLevel = "INFO"
    collation_home = "C:/dev/taddm7213_sdk/sdk/etc"
    IpAddress = "192.168.81.135"
    healthCheck_command = "cat \"" + collation_home + "/etc/healthcheck_checkTaddmScopes\""



try:
    #######################################
    ## Get the collation_home property
    ######################################
    LogDebug("Collation home is: " + str(collation_home))
    if collation_home == None:
        LogError("Unable to locate com.collation.home");
        raise RuntimeError, "Unable to locate com.collation.home"
    
    # get the default location        
    coll_props_file_name = collation_home + "/etc/collation.properties";
    
    props = readPropFile(coll_props_file_name)
    
    #################################################################
    ##   Leave if locationTagging is enabled
    #################################################################
    
    locationTaggingEnabled = props.getProperty("com.ibm.cdb.locationTaggingEnabled")
    if locationTaggingEnabled != None:
        if string.upper(locationTaggingEnabled) == "TRUE" :
            LogInfo("*** LocationTagging is enabled - leaving")
            sys.exit()
        
        
    #################################################################
    ##  set default location
    #################################################################
    locationTag_property = "com.ibm.cdb.customLocationTag"
    defaultLocation = props.getProperty(locationTag_property)
    if (defaultLocation != None):
        LogDebug("Default location from " + locationTag_property + " property is: " + defaultLocation)
    else:    
        LogDebug("Unable to locate " + locationTag_property + " property - assuming defaultValue of UNKNOWN")
        defaultLocation = "UNKNOWN"

    #########################################################################################
    ##  Get the scopes that are defined to the discovery server:
    ##
    ##  Scopes can be read from either the scopes.properties file, of from the output of
    ##  the 'healthcheck checkTaddmScopes' command
    ##  
    ##  The healthcheck command method is included to demonstrate how to execute a command
    ##  on the Discovery Server and capture the output 
    ##########################################################################################
    #taddm_scopes = get_scopes_from_healthcheck()    
    taddm_scopes = get_scopes_from_scope_properties(collation_home + "/etc/scope.properties")
                
    #########################################################    
    ## find the scopes that the current IpAddress belongs to   
    ## by reading the scopes.properties file, and use the 
    ## private scope and scopeElement classes to find the 
    ## scope  
    #########################################################
    included_in_scopeElements={}     
    excluded_in_scopeElements={}
    
    # loop over scopes, extract the scope-elements, and validate if the IpAddress is included
    scope_elements = []     
    included_in_scopes = {}    
    for scope in taddm_scopes:       
        scope_name = scope.getName()
        excluded = False        
        for scope_element in scope.getElements():            
            included = False 
            scope_element_name = scope_element.getName()
            scope_element_type = scope_element.getType()
            scope_and_element_name = scope_name + ":" + scope_element_name
            LogDebug("Analyzing element: " + scope_and_element_name)
                    
            if scope_element.isExcluded(IpAddress):
                excluded = True
                LogInfo("*** " + IpAddress + " is EXCLUDED from scope element " + scope_name + ":" + scope_element_name)
                #excluded_in_scopeElements[scope_and_element_name]=True
            elif scope_element.isIncluded(IpAddress):                
                included = True
                LogInfo("*** " + IpAddress + " is INCLUDED in scope element " + scope_name + ":" + scope_element_name)
                #included_in_scopeElements[scope_and_element_name]=True
                included_in_scopeElements[scope_and_element_name] = scope_name

            #  bypass further processing if this scope if the IpAddress exists in an EXCLUDE scope element
            if excluded:
                break

        # build a dictionary of scopes that include the IpAddress                
        for element_name, scope_name in included_in_scopeElements.items():
            if not included_in_scopes.has_key(scope_name):
                included_in_scopes[scope_name] = element_name
    
    # Print a nice message that shows which scopes the IpAddress belongs to                 
    incl = None
    for scope_name in included_in_scopes.keys():
        if incl == None:
            incl = "'" +scope_name+"'"
        else:    
            incl = incl + ", '" + scope_name+"'"
    LogInfo("Computer System with IpAddress " + IpAddress + " is incluced in " + str(len(included_in_scopes)) + " socpes: " + incl)
           
    #############################################################
    ## find the anchor hosts from the anchor.properties file
    ## and identify related scopes and locations
    #############################################################
    anchor_props_file_name = collation_home + "/etc/anchor.properties";
    anchor_props = readPropFile(anchor_props_file_name)
    
    ## find the anchor hosts, scopes and locations
    ## and save them in three dicts using the anchor number as key  
    anchor_hosts = {}
    anchor_scopes = {}
    anchor_locations = {}
    anchor_locations["0"] = defaultLocation
    anchor_host_prefix = "anchor_host_"
    hst = len(anchor_host_prefix)
    anchor_scope_prefix = "anchor_scope_"
    sco = len(anchor_scope_prefix)
    anchor_location_prefix = "anchor_location_"
    loc = len(anchor_location_prefix)
    
    for prop in anchor_props.keys():
        if prop[:hst] == anchor_host_prefix:
            anchor = prop[hst:]
            anchor_hosts[anchor] = anchor_props[anchor_host_prefix+anchor]
            val = anchor_props[anchor_scope_prefix+anchor]
            if val == None:
                val = ""
            anchor_scopes[anchor] = val
            if anchor != "0":
                val = anchor_props[anchor_location_prefix+anchor]
                if val == None:
                    val = ""
                anchor_locations[anchor] = val
         
    
    # sort the anchors    
    anchors = anchor_hosts.keys()
    anchors.sort()
    
    # print anchor scope assignments 
    for anchor in anchors:
        LogInfo("*** Anchor 'anchor_host_" + str(anchor) + "' is assigned scope '" + anchor_scopes[anchor] + "' and location '"  + anchor_locations[anchor]+ "'")    


    ###############################################################
    ##  assign location based on scope-anchor-location assignment
    ##
    ##  use the ascending sequence so that the highest anchor number
    ##  that supports a scope is assigned
    ###############################################################
    location = defaultLocation
    
    i = len(anchors) - 1
    
    while (i >= 0): 
        anchor = anchors[i]
        scope = anchor_scopes[anchor]
        
        if included_in_scopes.has_key(scope):
            location = anchor_locations[anchor]
            break
        i = i-1;
    LogInfo("ComputerSystem with IpAddress " + IpAddress + " will be assigned a location of: " + str(location))

finally:
    pass

##########################################################################
##########################################################################
##   assign a value ot the locationTag attribute,
##   and save the results
##########################################################################
##########################################################################
try:
    computer_system.setLocationTag(location)
    result.setComputerSystem(computer_system)
    
except:
    pass




