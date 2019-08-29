############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# SQLServerAnalysisServices.py
#
# DESCRIPTION: 
#
# Authors:  Mat Davis
#			mdavis5@us.ibm.com
#
# History:
#
############################# End Standard Header ##############################

########################################################
# Standard Jython/Python Library Imports
########################################################
import sys
import java

########################################################
# Additional from Java imports
########################################################
from java.lang import System

########################################################
# Set the Path information
########################################################
coll_home = System.getProperty("com.collation.home")

# this is for default (old) Python v2.1
#System.setProperty("jython.home",coll_home + "/external/jython-2.1")
#System.setProperty("python.home",coll_home + "/external/jython-2.1")

# this is for new Python v2.5.3
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython_1.0.0/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.path.append(coll_home + "/lib/sensor-tools")
sys.prefix = jython_home + "/Lib"

########################################################
# More Standard Jython/Python Library Imports
########################################################
import traceback
import re

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
(os_handle, result, appserver, seed, log, env) = sensorhelper.init(targets)

log.info("SQL Server Analysis Services discovery extension started (written by Mat Davis - mdavis5@us.ibm.com).")

try:
    # need the port to connect to
    if appserver.hasPrimarySAP():
        # create SqlServer from AppServer so we can create databases
        # not doing this because it seems hacky and I'm not sure of unintended consequences
        # sqlserver = sensorhelper.newModelObject('cdm:app.db.mssql.SqlServer')
        # if appserver.hasVendorName():
            # sqlserver.setVendorName(appserver.getVendorName())
        # if appserver.hasProductName():
            # sqlserver.setProductName(appserver.getProductName())
        # if appserver.hasStatus():
            # sqlserver.setStatus(appserver.getStatus())
        # if appserver.hasPrimarySAP():
            # sqlserver.setPrimarySAP(appserver.getPrimarySAP())
        # if appserver.hasKeyName():
            # sqlserver.setKeyName(appserver.getKeyName())
        # if appserver.hasHost():
            # sqlserver.setHost(appserver.getHost())
        # if appserver.hasProcessPools():
            # sqlserver.setProcessPools(appserver.getProcessPools())
        
        pSAP = appserver.getPrimarySAP()
        if pSAP.hasPortNumber():
            port = pSAP.getPortNumber()
            
            # use IP address if we can, otherwise use localhost
            if pSAP.hasPrimaryIpAddress():
                ip = pSAP.getPrimaryIpAddress().getStringNotation()
                log.debug('Using IP ' + ip)
            else:
                ip = 'localhost'

            # powershell command to get Edition and SP
            cmd = 'powershell -Command ' \
                   '"& {Import-Module SQLPS -DisableNameChecking; ' \
                   '$SSASServer = New-Object Microsoft.AnalysisServices.Server; ' \
                   '$SSASServer.connect(\'' + ip + ':' + str(port) + '\'); ' \
                   'Write-Host \'SSAS Edition =\' $SSASServer.Edition; ' \
                   'Write-Host \'SSAS Service Pack =\' $SSASServer.ProductLevel; ' \
                   'Write-Host \'SSAS Backup folder =\' $SSASServer.ServerProperties[\'BackupDir\'].Value; ' \
                   'Write-Host \'SSAS Collation =\' $SSASServer.ServerProperties[\'CollationName\'].Value; ' \
                   'Write-Host \'SSAS Creation Date =\' $SSASServer.CreatedTimestamp; ' \
                   'Write-Host \'SSAS Data directory =\' $SSASServer.ServerProperties[\'DataDir\'].Value; ' \
                   'Write-Host \'SSAS ID =\' $SSASServer.ID; ' \
                   'Write-Host \'SSAS Language =\' $SSASServer.ServerProperties[\'Language\'].value; ' \
                   'Write-Host \'SSAS Last Schema Update =\' $SSASServer.LastSchemaUpdate; ' \
                   'Write-Host \'SSAS Log Folder =\' $SSASServer.ServerProperties[\'LogDir\'].Value; ' \
                   'Write-Host \'SSAS Product Name =\' $SSASServer.ProductName; ' \
                   'Write-Host \'SSAS Mode =\' $SSASServer.ServerMode; ' \
                   'Write-Host \'SSAS Temp Folder =\' $SSASServer.ServerProperties[\'TempDir\'].Value; ' \
                   'Write-Host \'SSAS Version =\' $SSASServer.Version;}"'
                   
            try:
                # run command, get output
                output = sensorhelper.executeCommand(cmd)
            except:
                LogError("Command execution failed")
                raise

            ea = {}
            # look for SSAS edition and parse out
            edition = None
            m = re.search('SSAS Edition .*', output)
            if m is not None:
                match = str(m.group(0))
                split = match.split('=')
                if len(split) > 1:
                    value = split[1].strip()
                    if value != '':
                        log.debug('Setting extended attribute edition:' + value)
                        ea['Edition'] = value
                        edition = value
                else:
                    log.warning("No value found for extended attribute 'Edition'")
            
            # look for SSAS SP and parse out
            m = re.search('SSAS Service Pack .*', output)
            if m is not None:
                match = str(m.group(0))
                split = match.split('=')
                if len(split) > 1:
                    sp = split[1].strip()
                    if sp != '':
                        log.debug('Setting extended attribute ServicePack:' + sp)
                        ea['ServicePack'] = sp
                        appserver.setServicePack(sp)
                else:
                    log.warning("No value found for extended attribute 'ServicePack'")

            # look for data directory
            m = re.search('Data directory .*', output)
            dataDir = None
            if m is not None:
                match = str(m.group(0))
                split = match.split('=')
                if len(split) > 1:
                    value = split[1].strip()
                    if value != '':
                        log.debug('Found data directory:' + value)
                        dataDir = value
                else:
                    log.warning("No value found for data directory")

            # look for SSAS Collation and parse out
            m = re.search('SSAS Collation .*', output)
            if m is not None:
                match = str(m.group(0))
                split = match.split('=')
                if len(split) > 1:
                    value = split[1].strip()
                    if value != '':
                        log.debug('Setting extended attribute SortOrder:' + value)
                        ea['SortOrder'] = value
                else:
                    log.warning("No value found for extended attribute 'SortOrder'")

            # look for SSAS ServerMode and parse out
            m = re.search('SSAS Mode .*', output)
            if m is not None:
                match = str(m.group(0))
                split = match.split('=')
                if len(split) > 1:
                    value = split[1].strip()
                    if value != '':
                        log.debug('Setting extended attribute ServerMode:' + value)
                        ea['ServerMode'] = value
                else:
                    log.warning("No value found for extended attribute 'ServerMode'")

            # look for SSAS Version and parse out, adding name
            m = re.search('SSAS Version .*', output)
            if m is not None:
                match = str(m.group(0))
                split = match.split('=')
                if len(split) > 1:
                    value = split[1].strip()
                    if value != '':
                        version = None
                        # value mapping comes from http://sqlserverbuilds.blogspot.co.uk/ as of June 2016
                        if value.find('12.0.') >= 0:
                            version = '2014'
                        elif value.find('11.0.') >= 0:
                            version = '2012'
                        elif value.find('10.50.') >= 0:
                            version = '2008R2'
                        elif value.find('10.0.') >= 0:
                            version = '2008'
                        elif value.find('9.0.') >= 0:
                            version = '2005'
                        elif value.find('8.0.') >= 0:
                            version = '2000'
                        elif value.find('7.0.') >= 0:
                            version = '7.0'
                        else:
                            LogError('Version matching ' + value + ' not found in known list. Might be a newer model that needs added')

                        if version is not None:
                            log.debug('Setting attribute ProductVersion:' + version)
                            appserver.setProductVersion(version)
                            
                        # Originally I built out the version to match the format the SqlSensor uses, but this was not wanted
                        # Saving it here because it's pretty and I like it
                        # if value.find('12.0.') >= 0:
                            # version = 'SQL Server 2014'
                        # elif value.find('11.0.') >= 0:
                            # version = 'SQL Server 2012'
                        # elif value.find('10.50.') >= 0:
                            # version = 'SQL Server 2008 R2'
                        # elif value.find('10.0.') >= 0:
                            # version = 'SQL Server 2008'
                        # elif value.find('9.0.') >= 0:
                            # version = 'SQL Server 2005'
                        # elif value.find('8.0.') >= 0:
                            # version = 'SQL Server 2000'
                        # elif value.find('7.0.') >= 0:
                            # version = 'SQL Server 7.0'
                        # else:
                            # LogError('Version matching ' + value + ' not found in known list. Might be a newer model that needs added')
                            
                        # if version is not None and sp is not None:
                            # version = version + ' ' + sp
                            # if edition is not None:
                                # version = version + ' (' + edition + ')'
                                
                        # if version is not None:
                            # log.debug('Setting attribute ProductVersion:' + version)
                            # appserver.setProductVersion(version)
                        
                        log.debug('Setting attribute VersionString:' + value)
                        appserver.setVersionString(value)
                else:
                    log.warning("No value found for attribute 'Version'")
                    
            # powershell command to get database information
            # db attrs @ https://msdn.microsoft.com/en-us/library/microsoft.analysisservices.database.aspx
            cmd = 'powershell -Command ' \
                  '"& {Import-Module SQLPS -DisableNameChecking; ' \
                  '$SSASServer = New-Object Microsoft.AnalysisServices.Server; ' \
                  '$SSASServer.connect(\'' + ip + ':' + str(port) + '\'); ' \
                  '$SSASDBS = $SSASServer.databases; ' \
                  'FOREACH ($DB in $SSASDBS) { ' \
                  '  write-host \'DB Name = \' $DB.name; ' \
                  '  write-host \'DB Create Date = \' $DB.createdtimestamp; ' \
                  '  write-host \'DB Collation = \' $DB.collation; ' \
                  '  $ssasdbsize =  [math]::round($DB.estimatedsize / 1024 / 1024 / 1024, 2); ' \
                  '  write-host \'DB Size = \' $ssasdbsize; ' \
                  '  write-host \'List of Cubes in DB = \' $DB.cubes; ' \
                  '  write-host \'List of Dimensions in DB = \' $DB.dimensions; ' \
                  '}}"'

            try:
                # run command, get output
                output = sensorhelper.executeCommand(cmd)
            except:
                LogError("Command execution failed")
                raise
            
            # make sure data directory is discovered so we can create the databases properly
            if dataDir is not None:
                # look for databases and parse out
                m = re.search('DB Name .*', output)
                # m2 = re.search('DB Create Date .*', output)
                if m is not None:
                    match = str(m.group(0))
                    split = match.split('=')
                    if len(split) > 1:
                        value = split[1].strip()
                        if value != '':
                            log.debug('Defining database with name:' + value)
                            module = sensorhelper.newModelObject('cdm:app.db.mssql.SqlServerModule')
                            #db = sensorhelper.newModelObject('cdm:app.db.mssql.SqlServerDatabase')
                            module.setName(value)
                            #db.setName(value)
                            module.setFileName(dataDir + '\\' + value + '.mdf')
                            #db.setPrimaryDataFile(dataDir + '\\' + value + '.mdf')
                            #module.setParent(sqlserver)
                            module.setParent(appserver)
                            #db.setParent(sqlserver)
                            # get creation time
                            # match = str(m2.group(0))
                            # split = match.split('=')
                            # if len(split) > 1:
                                # value = split[1].strip()
                                # if value != '':
                                    # db.setCreationDate(value)
                            result.addModule(module)
                            # dbs = []
                            # dbs.append(db)
                            # sqlserver.setDatabases(sensorhelper.getArray(dbs,'cdm:app.db.mssql.SqlServerDatabase'))
                    else:
                        log.warning("No value found for extended attribute 'Collation'")
            
            log.debug('Extended attributes: ' + str(ea))
            # set extended attributes
            # sensorhelper.setExtendedAttributes(sqlserver, ea)
            sensorhelper.setExtendedAttributes(appserver, ea)
            # replace AppServer with SqlServer so that we can create databases
            # result.setServer(sqlserver)
        else:
            LogError("No port number found on discovered appserver")
    else:
        LogError("No priimary SAP found on discovered appserver")

except Exception, e:
    LogError("Unexpected error occurred during discovery:" + str(e))