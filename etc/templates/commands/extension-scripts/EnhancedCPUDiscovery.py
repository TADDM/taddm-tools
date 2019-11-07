############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# CPUCoresDiscovery.py
#
# DESCRIPTION: Used to populate additional CPU information for Windows, Linux, and HP-UX.
#
# Authors:  Mat Davis
#            mdavis5@us.ibm.com
#           Andy Barclay
#            abarclay@us.ibm.com
#
# History:
#    Version 1.2 -- 6/13 -- Added HP-UX --
#    Version 1.1 -- 4/13 -- Added DiesInstalled/Enabled calculation --
#    Version 1.0 -- 3/13 -- Copied from Windows only version to add Linux --
#    Version 0.6 -- 2/13 -- Changed to run on Win2k8 64-bit --
#    Version 0.5 -- 8/12 -- Initial Version --
#
############################# End Standard Header ##############################

########################################################
# Standard Jython/Python Library Imports
########################################################
import sys
import java
import os

########################################################
# Additional from Java imports
########################################################
from java.lang import System
from java.lang import Class
from java.util import Properties
from java.util import HashMap
from java.io import FileInputStream
from java.io import ByteArrayOutputStream
from java.io import ObjectOutputStream
from java.lang import String
from java.lang import Boolean
from java.lang import Runtime
from java.lang import Integer

from com.collation.platform.ip import ScopedProps

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")
System.setProperty("jython.home",coll_home + "/external/jython-2.1")
System.setProperty("python.home",coll_home + "/external/jython-2.1")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

########################################################
# More Standard Jython/Python Library Imports
########################################################
import traceback
import string
import re
import jarray
import StringIO
import os
import getopt

########################################################
# Custom Libraries to import (Need to be in the path)
########################################################
import sensorhelper

########################################################
# Some default GLOBAL Values (Typically these should be in ALL CAPS)
# Jython does not have booleans
########################################################
True = 1
False = 0

######################################################## 
# LogError Error Logging 
########################################################
def LogError(msg):
        log.error(msg)
        (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
        traceback.print_exc(ErrorTB)

##########################################################
# Main
# Setup the various objects required for the extension
##########################################################
(os_handle, result, computersystem, seed, log) = sensorhelper.init(targets)

#If this was an AppServer instead of a ComputerSystem, the previous
#line would be:
#(os_handle,result,appserver,seed,log,env) = sensorhelper.init(targets)

log.info("Windows CPU cores discovery extension started.")

# check if target is virtual, we don't need to discover cores on a virtual system
isVirtual = False
if computersystem.hasModel() and computersystem.getModel().startswith("VMware"):
    isVirtual = True
    
if computersystem.hasOSRunning() and not computersystem.hasCPUCoresInstalled() and not isVirtual:
    CPUCoresInstalled = 0
    CPUCoresEnabled = 0
    CPUDiesInstalled = 0
    CPUDiesEnabled = 0
    os = computersystem.getOSRunning()
    # startswith makes sure to include "Windows Server 2008 64-bit"
    if os.hasOSName() and os.getOSName().startswith("Windows Server 2008"):
        procs = sensorhelper.getWmiCimV2Class('Win32_Processor')
        members = []
        for idx in range(len(procs)):
            mo = sensorhelper.newModelObject('cdm:sys.CPU')
            mo.setParent(computersystem)
            mo.setIndexOrder(str(idx))
            mo.setNumCPUs(Integer.parseInt(procs[idx]['NumberOfLogicalProcessors']))
            CPUCoresInstalled = CPUCoresInstalled + Integer.parseInt(procs[idx]['NumberOfCores'])
            CPUDiesInstalled = CPUDiesInstalled + 1
            members.append(mo)
        computersystem.setCPU(sensorhelper.getArray(members,'cdm:sys.CPU'))

    elif os.hasOSName() and os.getOSName().startswith("Windows Server 2003"):
        log.info("OSRunning is Windows Server 2003")
        cs = sensorhelper.getWmiCimV2Class('Win32_ComputerSystem')
        if cs:
            # if this value is available then KB932370 has been applied
            if cs[0].has_key('NumberOfLogicalProcessors'):
                procs = sensorhelper.getWmiCimV2Class('Win32_Processor')
                log.debug('Win32_Processor:' + str(procs))
                members = []
                for idx in range(len(procs)):
                    mo = sensorhelper.newModelObject('cdm:sys.CPU')
                    mo.setParent(computersystem)
                    mo.setIndexOrder(str(idx))
                    mo.setNumCPUs(Integer.parseInt(procs[idx]['NumberOfLogicalProcessors']))
                    mo.setCPUCoresInstalled(Integer.parseInt(procs[idx]['NumberOfCores']))
                    CPUCoresInstalled = CPUCoresInstalled + int(procs[idx]['NumberOfCores'])
                    CPUDiesInstalled = CPUDiesInstalled + 1
                    members.append(mo)
                computersystem.setCPU(sensorhelper.getArray(members,'cdm:sys.CPU'))
            else:
                log.warning("Hotfix KB932370 not found on system, skipping CPU core discovery.")
                result.warning("Hotfix KB932370 not found on system, skipping CPU core discovery.")
        else:
            log.warning("No results returned from WMI command to get Win32_ComputerSystem instance.")
            result.warning("No results returned from WMI command to get Win32_ComputerSystem instance.")

    elif os.hasOSName() and os.getOSName().startswith("Linux"):
        #
        # This section attempts core discovery through dmidecode command, though TADDM default is to
        # use /proc/cpuinfo to discovery CPU, this method will allow us to discover the cores enabled
        # in addition to the cores installed so we will attempt this first
        # 
        dmiDecodeCommand = ScopedProps.getDmidecodeCommand('Linux', os_handle.getSession().getHost())
        if dmiDecodeCommand is None or len(dmiDecodeCommand) == 0:
            dmiDecodeCommand = 'dmidecode'

        try:
            # append -t processor to make sure we get that info in case '-t system' is the only flags enabled
            dmiDecodeCommand = dmiDecodeCommand + ' -t processor'
            output = os_handle.executeCommand(dmiDecodeCommand)
            members = []
            lines = output.splitlines()
            for line in lines:
                m = re.search('\tCore Count: (.*)', line)
                if m is not None:
                    CPUCoresInstalled = CPUCoresInstalled + int(m.group(1))
                    CPUDiesInstalled = CPUDiesInstalled + 1
                    # create CPU member for array
                    mo = sensorhelper.newModelObject('cdm:sys.CPU')
                    mo.setParent(computersystem)
                    mo.setCPUCoresInstalled(int(m.group(1)))
                    members.append(mo)
                    m = re.search('\tCore Enabled: (.*)', line)
                if m is not None:
                    CPUCoresEnabled = CPUCoresEnabled + int(m.group(1))
                    CPUDiesEnabled = CPUDiesEnabled + 1
            # set CPU array if members were created
            if len(members) > 0:
                computersystem.setCPU(sensorhelper.getArray(members,'cdm:sys.CPU'))
            
        except:
            msg = 'CPU core discovery via \'' + dmiDecodeCommand + '\' failed.'
            LogError(msg)

        # get CPU core info using /proc/cpuinfo, this is not needed if the dmidecode method above is successful
        try:
            # only run this if dmidecode method above failed
            if CPUCoresInstalled == 0:
                output = os_handle.executeCommand('test -f /proc/cpuinfo || exit 1')
                numPhysical = os_handle.executeCommand('grep "physical id" /proc/cpuinfo | sort -u | wc -l')
                # this gives us the number of cores per physical CPU
                numCoresPerPhysical = os_handle.executeCommand('grep "cpu cores" /proc/cpuinfo | awk \'{print $4}\' | sort -u')
                # calculate the total cores by multiplying the number of cores by the number of physical processors
                if int(numPhysical) > 0 and int(numCoresPerPhysical) > 0:
                    CPUCoresInstalled = int(numPhysical) * int(numCoresPerPhysical)
                    # create CPU members
                    members = []
                    for idx in range(int(numPhysical)):
                        mo = sensorhelper.newModelObject('cdm:sys.CPU')
                        mo.setParent(computersystem)
                        mo.setIndexOrder(str(idx))
                        mo.setCPUCoresInstalled(int(numCoresPerPhysical))
                        members.append(mo)
                    computersystem.setCPU(sensorhelper.getArray(members,'cdm:sys.CPU'))
        except:
            msg = 'CPU core discovery via /proc/cpuinfo failed. Make sure service account has access to /proc/cpuinfo.'
            LogError(msg)
            result.warning(msg)
    ########## end Linux ###########

    ###############################################
    # HP-UX discovery
    ###############################################
    elif os.hasOSName() and os.getOSName().startswith("HP-UX"):
        # Used machinfo 
        # See the man page for details, but the short story is that
        # the first three lines define the physical characteristics of the
        # processors. There is also something called LCPU attribute which
        # defines if hyper-threading is enabled.
        # Note I am populating CPUCoresEnabled and CPUDiesEnabled, not the
        # CPUCoresInstalled or CPUDiesInstalled because of something I read
        # in the man page:
        #  "processors with no active cores are not counted"
        #
        output = os_handle.executeCommand("machinfo")
        # 
        members = []
        lines = output.splitlines()
        
        # start finite state machine
        STATE = "start"
        for line in lines:
            if (STATE == "start"):
                m = re.search('CPU info:', line)
                if m is not None:
                    STATE = "cpu"
                continue

            if (STATE == "cpu"):
                # newer machine
                m = re.search('Itanium\(R\)', line)
                if m is not None:
                    cpuDisplayName = line
                # older machine
                m = re.search('Itanium ', line)
                if m is not None:
                    m = re.search('(.*)(Intel.*)', line)
                    # m.group(1) might be a number or it might be spaces...
                    try:
                        CPUDiesEnabled = int(m.group(1))
                        CPUCoresEnabled = int(m.group(1))
                    except:
                        pass
                    cpuDisplayName = m.group(2)
                m = re.search('.*\(([^ ]*)', line)
                ghz = m.group(1)
                STATE = "coresperproc"
                continue

            if (STATE == "coresperproc"):
                # look for cores per socket
                m = re.search('Active processor count:', line)
                if m is not None:
                    STATE = "inActiveArea"
                    continue
                # this should match core or cores because of the regex
                m = re.search('(.*)cores*,', line)
                if m is not None:
                    coresperproc = int(m.group(1))

            if (STATE == "inActiveArea"):
                # once we are in the Active Area, if we find the
                # phrase "logical processor" or "Memory", we are done
                m = re.search('logical processor', line)
                if m is not None:
                    STATE = "done"
                m = re.search('^Memory', line)
                if m is not None:
                    STATE = "done"

            # searches for a line that contains socket but doesn't
            # end with a close paren
            m = re.search('(.*)socket[^\)]$', line)
            if m is not None:
               CPUDiesEnabled = int(m.group(1))
            m = re.search('(.*)core', line)
            if m is not None:
               CPUCoresEnabled = int(m.group(1))
            if (STATE == "done"):
                break
        # end finite state machine
        
        i = 0
        while (i < CPUDiesEnabled):
            # create chip member for array
            mo = sensorhelper.newModelObject('cdm:sys.CPU')
            mo.setParent(computersystem)
            mo.setIndexOrder(str(i))
            mo.setManufacturer("Intel")
            mo.setDescription(cpuDisplayName)
            mo.setCPUSpeed(long(float(ghz)*1000*1000*1000))
            # type is more of an "enum". Doc details what the options are
            mo.setCPUType("itanium")
            # Thought about setting CPUCoresEnabled here, but the commands
            # machinfo and ioscan -k don't tell me how many cores are enabled
            # on each socket. Found machine with two sockets and 5 cores enabled
            # Probably best just not to set this.
            #mo.setCPUCoresEnabled(int(CPUCoresEnabled/CPUDiesEnabled))
            try:
                mo.setCPUCoresInstalled(coresperproc)
            except:
                # if the output had no cores info, then assume 1
                mo.setCPUCoresInstalled(1)
            members.append(mo)
            i = i + 1
        if len(members) > 0:
            computersystem.setCPU(sensorhelper.getArray(members,'cdm:sys.CPU'))
    ########## end HP-UX ###########
        
    if CPUCoresInstalled != 0:
        log.info("Setting CPUCoresInstalled to " + str(CPUCoresInstalled))
        computersystem.setCPUCoresInstalled(CPUCoresInstalled)
        
    if CPUCoresEnabled != 0:
        log.info("Setting CPUCoresEnabled to " + str(CPUCoresEnabled))
        computersystem.setCPUCoresEnabled(CPUCoresEnabled)
    
    if CPUDiesInstalled != 0:
        log.info("Setting CPUDiesInstalled to " + str(CPUDiesInstalled))
        computersystem.setCPUDiesInstalled(CPUDiesInstalled)
        
    if CPUDiesEnabled != 0:
        log.info("Setting CPUDiesEnabled to " + str(CPUDiesEnabled))
        computersystem.setCPUDiesEnabled(CPUDiesEnabled)
    
    # strip out extra whitespace from CPU type attribute
    if computersystem.hasCPUType():
        cpuType = computersystem.getCPUType()
        computersystem.setCPUType(' '.join(cpuType.split()))

else:
    log.info("OSRunning not discovered, CPUCoresInstalled already discovered, or target is virtual.")
