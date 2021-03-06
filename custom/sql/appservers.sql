SELECT
	CONCAT(CONCAT('"', NVL(CS1.DISPLAYNAME_C, '')), '"') AS FQDN,
  CONCAT(CONCAT('"', NVL(A1.DISPLAYNAME_C, NVL(A1.NAME_C, NVL(A1.LABEL_C, '')))), '"') AS "Name",
  CASE WHEN A1.JDOCLASS_C LIKE '%.AppServerJdo' THEN '"Application Server"'
    WHEN A1.JDOCLASS_C LIKE '%.WebServerJdo' THEN '"Web Server"'
    WHEN A1.JDOCLASS_C LIKE '%.ApacheServerJdo' THEN '"Apache Server"'
    WHEN A1.JDOCLASS_C LIKE '%.Db2InstanceJdo' THEN '"DB2 Instance"'
    WHEN A1.JDOCLASS_C LIKE '%.JBossServerJdo' THEN '"JBoss Server"'
    WHEN A1.JDOCLASS_C LIKE '%.DatabaseServerJdo' THEN '"Database Server"'
    WHEN A1.JDOCLASS_C LIKE '%.J2EEServerJdo' THEN '"J2EE Server"'
    WHEN A1.JDOCLASS_C LIKE '%.VirtualCenterJdo' THEN '"Virtual Center"'
    ELSE REPLACE(REPLACE(A1.JDOCLASS_C, 'com.collation.topomgr.jdo.topology.', ''), 'Jdo', '')
  END AS "Type",
	CONCAT(CONCAT('"', NVL(A1.VENDORNAME_C, '')), '"') AS "Vendor",
	CONCAT(CONCAT('"', NVL(A1.PRODUCTNAME_C, NVL(A1.OBJECTTYPE_C, ''))), '"') AS "Product",
  CASE WHEN JBOSS.PRODUCTVERSION_C IS NOT NULL THEN CONCAT(CONCAT('"', JBOSS.PRODUCTVERSION_C), '"')
	  ELSE CONCAT(CONCAT('"', NVL(A1.PRODUCTVERSION_C, '')), '"') 
  END AS "Version",
  -- this is the IP used during discovery
  CONCAT(CONCAT('"', NVL(A1.CONTEXTIP_C, '')), '"') AS IP
FROM 
	BB_APPSERVER6_V A1
  LEFT OUTER JOIN ( 
    SELECT
      PK_C,
      DISPLAYNAME_C
    FROM 
      BB_COMPUTERSYSTEM40_V
  ) CS1 ON A1.PK__HOST_C = CS1.PK_C
  LEFT OUTER JOIN ( 
    -- get the JBossServers where the version is stored in majorVersion/release
    SELECT
      PK_C,
      CONCAT(CAST(MAJORVERSION_C AS VARCHAR(20)), CONCAT('.', CAST(RELEASE_C AS VARCHAR(20)))) AS PRODUCTVERSION_C
    FROM 
      BB_JBOSSSERVER75_V
    WHERE
      MAJORVERSION_C IS NOT NULL AND
      RELEASE_C IS NOT NULL AND
      PRODUCTVERSION_C IS NULL
  ) JBOSS ON A1.PK_C = JBOSS.PK_C
  ORDER BY FQDN ASC