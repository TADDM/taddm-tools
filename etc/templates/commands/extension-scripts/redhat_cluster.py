############### Begin Standard Header - Do not add comments here ###############
# 
# File:     redhat_cluster.py
# Version:  1.0
# Modified: 04/2014
# Build:    
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
Red Hat Cluster Sensor (Custom Server Extension)

Requirements:

    * It requires 'sensorhelper.py'
    * Only tested in TADDM 7.2.2 FP1
    * The extended attributes MUST BE CREATED already.  Use rhel_cluster_ext_attrs.jy 
      to create these attributes.
    
    * This script can be executed by placing 
      SCRIPT: $COLLATION_HOME/etc/templates/commands/extension-scripts/redhat_cluster.py
      in LinuxComputerSystemTemplate file under etc/templates/commands. Make sure that the
      Linux Computer System template is enabled via the UI

Author:  Mat Davis
     mdavis5@us.ibm.com
     IBM C&SI Lab Services


History:  

    original version    4/2014    Mat Davis (MAD)

Main comment block, Beginning of C&SI Dep Jython Script
'''

# Standard Library Imports

import sys
import java

from java.lang import System
from java.lang import String

# from Java [additional imports]

from com.collation.platform.ip import ScopedProps
from javax.xml.parsers import DocumentBuilder
from javax.xml.parsers import DocumentBuilderFactory
from org.w3c.dom import Document
from org.w3c.dom import Element
from org.w3c.dom import Node
from org.w3c.dom import NodeList
from java.io import ByteArrayInputStream

# Set the Path information

coll_home = System.getProperty("com.collation.home")
System.setProperty("jython.home",coll_home + "/external/jython-2.1")
System.setProperty("python.home",coll_home + "/external/jython-2.1")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

import string
import traceback
import re

#  Local App Imports
import sensorhelper

#----------------------------------------------------------------------------------
# Define some CONSTANTS, print some info
#-----------------------------------------------------------------------------------

#----------------------------------------------------------------------------------
# Define the Functions
#-----------------------------------------------------------------------------------

########################
# LogError      Error logger
########################
def LogError(msg):
    '''
    Print Error Message using Error Logger with traceback information
    '''
    log.error(msg)
    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
    traceback.print_exc(ErrorTB)

########################
# LogDebug      Print routine for normalized messages in log
########################
def LogDebug(msg):
    '''
    Print Debug Message using debug logger (from sensorhelper)
    '''
    # assuming SCRIPT_NAME and template name are defined globally...
    # point of this is to create a consistent logging format to grep 
    # the trace out of
    log.debug(msg)

########################
# LogInfo Print routine for normalized messages in log
########################
def LogInfo(msg):
    '''
    Print INFO level Message using info logger (from sensorhelper)
    '''
    # assuming SCRIPT_NAME and template name are defined globally...
    # point of this is to create a consistent logging format to grep 
    # the trace out of
    log.info(msg)

# convert XML NodeList to Python list
def nodeListToList(nodeList):
    
    nodes = []
    for n in range(0, nodeList.getLength()):
        nodes.append(nodeList.item(n))

    return nodes

# Python list 'nodes' are read and any occurances of 'allowed_attrs' are added to 
# 'cluster_ext_attrs' list with values and named with 'tag_prefix'
def addExtendedAttributes(nodes, allowed_attrs, tag_prefix, cluster_ext_attrs):

    # initialize all attributes to blanks so that any previously discovered value will be deleted
    for attr in allowed_attrs:
        cluster_ext_attrs[tag_prefix+attr]=''
    
    # handle the first node only
    if len(nodes) > 0:
        nodeMap = nodes[0].getAttributes()
        for i in range(nodeMap.getLength()):
            attribute = nodeMap.item(i)
            tag_name = attribute.getNodeName()
            if tag_name in allowed_attrs:
                tag_value = attribute.getNodeValue()
                LogDebug('Adding ' + tag_prefix + tag_name + "=" + tag_value)
                if len(nodes) == 1:
                    # simple add if only one
                    cluster_ext_attrs[tag_prefix+tag_name]=tag_value
                else:
                    # show in array format
                    cluster_ext_attrs[tag_prefix+tag_name]='1="' + tag_value + '"'
    # handle the rest of the nodes
    for j in range(1, len(nodes)):
        nodeMap = nodes[j].getAttributes()
        for i in range(nodeMap.getLength()):
            attribute = nodeMap.item(i)
            tag_name = attribute.getNodeName()
            if tag_name in allowed_attrs:
                tag_value = attribute.getNodeValue()
                LogDebug('Adding ' + tag_prefix + tag_name + "=" + tag_value)
                # use array format
                cluster_ext_attrs[tag_prefix+tag_name]=cluster_ext_attrs[tag_prefix+tag_name] + ' ' + str(j+1) + '="' + tag_value + '"'

#---------------------------------------------------------------------------------
# MAIN
#---------------------------------------------------------------------------------

# The first thing we need to do is get the Objects that are passed to a sensor
(os_handle,result,server,seed,log) = sensorhelper.init(targets)

# os_handle  -->  Os handle object to target system
# result     -->  Results Object
# server     -->  AppServer or ComputerSystem Object that is discovered
# seed       -->  seed object which contains information that was found prior
#                 to this CSX running
# log        -->  Object to write to sensor log

# Now we can use these objects to add MORE information to the object
# that has already been found.

LogInfo(" ****** STARTING redhat_cluster.py ******* ")

LogInfo("Using sensorhelper version: " + str(sensorhelper.getVersion()))

# get cluster.conf file location from collation.properties if exists
cluster_conf_file = ScopedProps.getStringProperty('com.collation.discover.agent.command.cluster_conf', 'Linux', os_handle.getSession().getHost())
if cluster_conf_file is None or len(cluster_conf_file) == 0:
    cluster_conf_file = '/etc/cluster/cluster.conf'

multipath_conf_file = '/etc/multipath.conf'
modprobe_conf_file = '/etc/modprobe.conf'

# only run if OS discovered as RHEL and cluster.conf file exists
if server.hasOSRunning() and server.getOSRunning().hasOSVersion() and server.getOSRunning().getOSVersion().startswith('Red Hat Enterprise Linux') and int(sensorhelper.executeCommand('[ -f ' + cluster_conf_file + ' ] && echo "1" || echo "0"')):
    
    # get scoped cman_tool command from collation.properties
    cmanCommand = ScopedProps.getStringProperty('com.collation.discover.agent.command.cman', 'Linux', os_handle.getSession().getHost())
    if cmanCommand is None or len(cmanCommand) == 0:
        cmanCommand = 'cman_tool'

    # XML document for cluster.conf
    doc = None
    
    try:
        # grab cluster configuration file, this will throw exception if file is not readable 
        # Note: don't pipe command to anything or it won't throw an exception
        cluster_conf = str(sensorhelper.executeCommand('cat ' + cluster_conf_file))
        dbFactory = DocumentBuilderFactory.newInstance()
        dBuilder = dbFactory.newDocumentBuilder()
        doc = dBuilder.parse(ByteArrayInputStream(String(cluster_conf).getBytes()))
        doc.getDocumentElement().normalize()
    except:
        msg = 'redhat_cluster.py: The following file does not exist or is not readable: ' + cluster_conf_file
        LogError(msg)
        # throw up warning on discovery UI
        result.warning(msg)
    
    try:
        # get cluster name
        if doc is None:
            # use command if we can't read cluster.conf
            clustername = str(sensorhelper.executeCommand(cmanCommand + ' status | grep "Cluster Name" | awk -F: {\'print $2\'}')).strip()
            if len(clustername) == 0:
                raise Exception('cman_tool output not as expected, please make sure cman_tool command is working properly and sudo is set up if needed.')
        else:
            clustername = doc.getDocumentElement().getAttribute('name')
        cluster = sensorhelper.newModelObject('cdm:sys.ComputerSystemCluster')
        LogDebug('Setting cluster name to ' + clustername)
        cluster.setLoadBalancer(clustername)    # this is the naming rule attribute for cluster
        # very important to identify the local node or else we can't attach the cluster to that localnode
        localnodename = str(sensorhelper.executeCommand(cmanCommand + ' status | grep "Node name" | awk -F: \'{print $2}\'')).strip()
        if len(localnodename) == 0:
            raise Exception('cman_tool output not as expected, please make sure cman_tool command is working properly and sudo is set up if needed.')

        # Iterate over all nodes and create each one
        if doc is None:
            nodes_output = sensorhelper.executeCommand(cmanCommand + ' nodes | tail -n +2 | awk \'{print $6}\'')
            if len(nodes_output) == 0:
                raise Exception('cman_tool output not as expected, please make sure cman_tool command is working properly and sudo is set up if needed.')
            nodenames = nodes_output.splitlines()
            # verify that only node names are included and not quorumd devices
            for nodename in nodenames:
                if '/' in nodename:
                    nodenames.remove(nodename)
        else:
            nodenames = []
            for nodename in nodeListToList(doc.getElementsByTagName('clusternode')):
                nodenames.append(nodename.getAttribute('name'))

        clusters = []
        clusters.append(cluster)
        nodes = []
        for nodename in nodenames:
            # get node IP addresses, these addresses are not available via cluster.conf
            address = str(sensorhelper.executeCommand(cmanCommand + ' nodes -a -n ' + nodename + ' | awk \'/Addresses/ {print $2}\'')).strip()
            if len(address) == 0:
                raise Exception('cman_tool output not as expected, please make sure cman_tool command is working properly and sudo is set up if needed.')
            LogDebug('  address:' + address)
            clusternode = sensorhelper.newModelObject('cdm:sys.ComputerSystem')
            if nodename == localnodename:
                LogDebug('Found local node')
                clusternode = server
            # using PMAC to merge all the nodes
            clusternode.setPrimaryMACAddress(nodename + '-' + address)
            clusternode.setSystemsCluster(sensorhelper.getArray(clusters, 'cdm:sys.ComputerSystemCluster'))
            nodes.append(clusternode)
        
        # add all nodes to the cluster
        cluster.setComputerSystems(sensorhelper.getArray(nodes, 'cdm:sys.ComputerSystem'))

        # only set extended attributes if cluster.conf is available
        if doc is not None:
            cluster_ext_attrs = {} # extended attributes for cluster

            # TOTEM
            nodes = doc.getElementsByTagName('totem')
            allowed_attrs = ['consensus', 'join', 'token', 'token_retransmits_before_loss_const']
            tag_prefix='totem_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)

            # QUORUMD
            nodes = doc.getElementsByTagName('quorumd')
            allowed_attrs = ['device', 'interval', 'min_score', 'tko', 'votes']
            tag_prefix='quorumd_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)
            
            # HEURISTIC
            nodes = doc.getElementsByTagName('heuristic')
            allowed_attrs = ['interval', 'program', 'score', 'tko']
            tag_prefix='heuristic_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)

            # FENCEDEVICE
            nodes = doc.getElementsByTagName('fencedevice')
            allowed_attrs = ['agent','name','login', 'ipaddr', 'lanplus']
            tag_prefix='fencedevice_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)

            # CMAN
            nodes = doc.getElementsByTagName('cman')
            allowed_attrs = ['quorum_dev_poll', 'expected_votes']
            tag_prefix='cman_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)
            
            # FAILOVERDOMAIN
            nodes = doc.getElementsByTagName('failoverdomain')
            allowed_attrs = ['name', 'nofailback', 'ordered', 'restricted']
            tag_prefix='failoverdomain_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)
                        
            # FENCE_DAEMON
            nodes = doc.getElementsByTagName('fence_daemon')
            allowed_attrs = ['clean_start', 'post_fail_delay', 'post_join_delay']
            tag_prefix='fence_daemon_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)

            # LOGGING
            nodes = doc.getElementsByTagName('logging')
            allowed_attrs = ['logfile']
            tag_prefix='logging_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)

            # RM
            nodes = doc.getElementsByTagName('rm')
            allowed_attrs = ['log_facility', 'log_level', 'status_poll_interval']
            tag_prefix='rm_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)
            
            # SERVICE
            nodes = doc.getElementsByTagName('service')
            # looks like parent node returns something but the child node methods don't have the values
            allowed_attrs = ['autostart', 'exclusive', 'recovery', 'domain', 'name']
            tag_prefix='service_'
            addExtendedAttributes(nodeListToList(nodes), allowed_attrs, tag_prefix, cluster_ext_attrs)

            # IP of SERVICE
            ips = []
            for service in nodeListToList(nodes):
                ips.extend(nodeListToList(service.getElementsByTagName('ip')))
            allowed_attrs = ['monitor_link', 'sleeptime']
            tag_prefix='service_ip_'
            addExtendedAttributes(ips, allowed_attrs, tag_prefix, cluster_ext_attrs)
            
            # get dev_loss_tmo out of multipath.conf file if it exists
            if int(sensorhelper.executeCommand('[ -r ' + multipath_conf_file + ' ] && echo "1" || echo "0"')):
                dev_loss_tmo = str(sensorhelper.executeCommand('grep dev_loss_tmo ' + multipath_conf_file + ' | awk \'{print $2}\'')).strip()
                cluster_ext_attrs['dev_loss_tmo']=''
                if dev_loss_tmo is not None and len(dev_loss_tmo) > 0:
                    LogDebug('Adding dev_loss_tmo='  + dev_loss_tmo)
                    cluster_ext_attrs['dev_loss_tmo']=dev_loss_tmo
                else:
                    LogInfo('Could not read dev_loss_tmo value from ' + multipath_conf_file)
            else:
                LogInfo(multipath_conf_file + ' is not readable')
                
            # get qlport_down_retry and lpfc_devloss_tmo out of modprobe.conf file
            if int(sensorhelper.executeCommand('[ -r ' + modprobe_conf_file + ' ] && echo "1" || echo "0"')):
                qlport_down_retry = str(sensorhelper.executeCommand('grep -v \'^#\' ' + modprobe_conf_file + ' | grep -o qlport_down_retry=[0-9]* | awk -F= {\'print $2\'}')).strip()
                cluster_ext_attrs['qlport_down_retry']=''
                if qlport_down_retry is not None and len(qlport_down_retry) > 0:
                    LogDebug('Adding qlport_down_retry='  + qlport_down_retry)
                    cluster_ext_attrs['qlport_down_retry']=qlport_down_retry
                else:
                    LogInfo('Could not read qlport_down_retry value from ' + modprobe_conf_file)
                lpfc_devloss_tmo = str(sensorhelper.executeCommand('grep -v \'^#\' ' + modprobe_conf_file + ' | grep -o lpfc_devloss_tmo=[0-9]* | awk -F= {\'print $2\'}')).strip()
                cluster_ext_attrs['lpfc_devloss_tmo']=''
                if lpfc_devloss_tmo is not None and len(lpfc_devloss_tmo) > 0:
                    LogDebug('Adding lpfc_devloss_tmo='  + lpfc_devloss_tmo)
                    cluster_ext_attrs['lpfc_devloss_tmo']=lpfc_devloss_tmo
                else:
                    LogInfo('Could not read lpfc_devloss_tmo value from ' + modprobe_conf_file)
            else:
                LogInfo(modprobe_conf_file + ' is not readable')
            
            # query CMAN expected votes from cman command if not captured from cluster.conf
            if 'cman_expected_votes' not in cluster_ext_attrs.keys() or cluster_ext_attrs['cman_expected_votes'] == '':
                expected_votes = str(sensorhelper.executeCommand(cmanCommand + ' status | grep \'Expected votes\' | awk \'{print $3}\'')).strip()
                if len(expected_votes) == 0:
                    LogInfo('cman_tool returned no value for Expected votes')
                else:
                    LogDebug('Adding cman_expected_votes=' + expected_votes)
                    cluster_ext_attrs['cman_expected_votes'] = expected_votes

            try:
                cman_quorum_timeout = str(sensorhelper.executeCommand('grep \'^CMAN_QUORUM_TIMEOUT\' /etc/sysconfig/cman | awk -F= \'{print $2}\'')).strip()
                LogDebug('Adding CMAN_QUORUM_TIMEOUT=' + cman_quorum_timeout)
                cluster_ext_attrs['CMAN_QUORUM_TIMEOUT'] = cman_quorum_timeout
            except:
                msg = 'redhat_cluster.py: Error occurred while attempting to read CMAN_QUORUM_TIMEOUT from \'/etc/sysconfig/cman\'. Make sure that file exists and is readable by the discovery service account.'
                LogError(msg)
                result.warning(msg)
            
            LogDebug('cluster extended attributes:'+str(cluster_ext_attrs))
            sensorhelper.setExtendedAttributes(cluster, cluster_ext_attrs)
    except Exception, e:
        LogError(e.args[0])
        result.warning('redhat_cluster.py: ' + e.args[0])
else:
    LogInfo("OSRunning is not Red Hat or '" + cluster_conf_file + "' does not exist")