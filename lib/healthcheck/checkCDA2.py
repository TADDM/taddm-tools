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
# (C) COPYRIGHT IBM CORP. 2010.  All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
############################# End Standard Header #############################
from check import check, LogError
from com.ibm.cdb.topomgr import TopologyManagerFactory
from com.ibm.cdb.topomgr import TopomgrProps
from java.sql import DriverManager
from java.sql import Statement
from java.sql import SQLException
from java.lang import Class
from time import localtime
from time import asctime

import TaddmHelper

from com.collation.platform.logger import LogFactory
log = LogFactory.getLogger(__name__)

def connectToDB(driver, url, user, password):
    try:
        cls = Class.forName(driver)
        DriverManager.registerDriver(cls.newInstance())
        conn = DriverManager.getConnection(url, user, password)
        return conn
    except SQLException, desc:
        raise desc


class checkCDA2(check):
   
    def __init__(self,u,p,output=None):
        check.__init__(self,u,p,output)
        self.group = "performance"
        self.name = __name__
         #123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*
        # description is better if its <80 characters
        self.description = """
        This check runs a test to see if the ConnectionDependencyAgent2 (CDA2) is completing
        It performs the following:
            - connects to taddm db
            - checks last run time for CDA2 agent
        
        The result is the last run time for the CDA2 agent
      
        """
        self.results.column_order = ["Label","LastRunTime","Description"]
        self.unsupported_modes=["discovery"]
            
    def runCheck(self):
        conn = None
        stmt = None
        rs = None
        try:
            try:
                props = TopologyManagerFactory.getProps()
                conn = connectToDB(props.getDbDriver(), props.getDbUrl(), props.getDbUser(), props.getDbPassword())
                stmt = conn.createStatement()
                rs = stmt.executeQuery('SELECT lastruntime FROM tb_agent_last_run where agentname = \'com.ibm.cdb.topomgr.topobuilder.agents.core_1.0.0:com.ibm.cdb.topomgr.topobuilder.agents.ConnectionDependencyAgent2\'')
                if rs.next():
                    lastruntime = rs.getString(1)
                    log.info('lastruntime = ' + lastruntime)
                    ltime = localtime(long(lastruntime)/1000)
                    log.info('ltime = ' + asctime(ltime))
                    self.results.append({'Label':'ConnectionDependencyAgent2', 'LastRunTime':asctime(ltime)})
            except SQLException, desc:
                LogError(desc.getMessage())
                raise desc
        finally:
            if rs is not None:
                try:
                    rs.close()
                except SQLException, e:
                    LogError(e.getMessage)
            if stmt is not None:
                try:
                    stmt.close()
                except SQLException, e:
                    LogError(e.getMessage)
            if conn is not None:
                try:
                    conn.close()
                except SQLException, e:
                    LogError(e.getMessage)
        
        self.printResults()
