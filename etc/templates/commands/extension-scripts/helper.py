#!/usr/bin/env ../../../../bin/jython_coll_253

############### Begin Standard Header - Do not add comments here ##
# Licensed Materials - Property of IBM
# 5724-N55
# (C) COPYRIGHT IBM CORP. 2007. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# SCRIPT OVERVIEW (This section would be used by doc generators)
#
# DESCRIPTION:
#
# Authors:  Mat Davis
#                       mdavis5@us.ibm.com
#
# History:
#    Version 0.1 -- 01/2020   -- Initial Version --
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

# this is for new Python v2.5.3
System.setProperty("jython.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")
System.setProperty("python.home",coll_home + "/osgi/plugins/com.ibm.cdb.core.jython253_2.5.3/lib")

jython_home = System.getProperty("jython.home")
sys.path.append(jython_home + "/Lib")
sys.prefix = jython_home + "/Lib"

# Import the TADDM Java Libraries
from com.collation.platform.model.util.ea import ExtendedAttributesData
 
########################
# setExtendedAttributes Takes a CDM ModelObject and a python dictionary of name
#                       value pairs and sets the name value pairs as
#                       extended attributes for the ModelObject.  The values
#                       must be strings.  This feature
#                       requires TADDM 7.1 or higher.
#
#                       Parameters
#                               mo      CDM ModelObject
#                               exattrs python dictionary of name/value pairs.
#                                       name is extended attribute name
#                                       value is string
#
#                       Returns
#
#                       Exceptions
#                               IoException
########################
def setExtendedAttributes(mo,exattrs,category=None):
    ead = ExtendedAttributesData()
    # merge with existing if already set
    if mo.hasXA():
      ead = mo.getXA()
    if category:
       for name,value in exattrs.items():
        ead.addAttribute(category,name,value)
    else:
       for name,value in exattrs.items():
        ead.addAttribute(name,value)
    ead.attachTo(mo)