SELECT
  CONCAT(CONCAT('"', NVL(A1.NAME_C, NVL(A1.DISPLAYNAME_C, NVL(A1.LABEL_C, '')))), '"') AS "APP_NAME",
  -- TODO use CASE here
  CASE WHEN A1.JDOCLASS_C LIKE '%.AppServerJdo' THEN '"Application Server"'
    ELSE REPLACE(REPLACE(A1.JDOCLASS_C, 'com.collation.topomgr.jdo.topology.', ''), 'Jdo', '')
  END AS "TYPE",
	--REPLACE(REPLACE(A1.JDOCLASS_C, 'com.collation.topomgr.jdo.topology.', ''), 'Jdo', '') AS "TYPE",
	CONCAT(CONCAT('"', NVL(A1.VENDORNAME_C, '')), '"') AS VENDOR_NAME,
	CONCAT(CONCAT('"', NVL(A1.PRODUCTNAME_C, NVL(A1.OBJECTTYPE_C, ''))), '"') AS PRODUCT_NAME,
	CONCAT(CONCAT('"', NVL(A1.PRODUCTVERSION_C, '')), '"') AS PRODUCT_VERSION,
	CONCAT(CONCAT('"', NVL(CS1.DISPLAYNAME_C, '')), '"') AS FQDN
FROM 
	BB_APPSERVER6_V A1
	
LEFT OUTER JOIN ( 
	SELECT
		PK_C,
		DISPLAYNAME_C
	FROM 
		BB_COMPUTERSYSTEM40_V
) CS1 ON A1.PK__HOST_C = CS1.PK_C