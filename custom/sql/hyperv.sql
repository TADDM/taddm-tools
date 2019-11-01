SELECT
 upper(CS.NAME_C) AS CS_NAME,
-- CS.LASTMODIFIEDTIME_T AS CS_LMT,
 OS.OSNAME_C AS HYPERV_OS,
 lower(VM.NAME_C) AS VM_NAME,
 VM_OS.OSNAME_C AS VM_OS,
 VM.SERIALNUMBER_C AS VM_UUID
FROM
 BB_UNITARYCOMPUTERSYSTEM24_V CS
 LEFT OUTER JOIN BB_OPERATINGSYSTEM62_V OS ON CS.PK__OSRUNNING_C = OS.PK_C,
 BB_COMPUTERSYSTEM40_V VM
 LEFT OUTER JOIN BB_OPERATINGSYSTEM62_V VM_OS ON VM.PK__OSRUNNING_C = VM_OS.PK_C
WHERE 
 VM.PK__HOSTSYSTEM_C = CS.PK_C
 AND CS.PK_C IN ( SELECT PK__HOST_C FROM BB_HYPERV12_V WHERE PK__HOST_C IS NOT NULL )
 --AND (current timestamp - 14 days) < (timestamp('1970-01-01','00.00.00') + (CS.LASTMODIFIEDTIME_C/1000) seconds )