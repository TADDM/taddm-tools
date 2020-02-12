-- query all VPLEX virtual volumes that are not connected to a host
SELECT
VPLEX.SERIALNUMBER_C AS VPLEXSerialNumber,
VPLEXSV.NAME_C AS VirtualVolume,
VPLEXSV.CAPACITY_C*512/(1024*1024*1024) as VirtualVolumeCapacityGB,
VPLEXSV.MANAGEDSYSTEMNAME_C AS LUNWWN
FROM
BB_STORAGESUBSYSTEM16_V VPLEX,
BB_STORAGESUBSYBERS_8D5F5384J VPLEX_SV,
BB_STORAGEVOLUME95_V VPLEXSV
WHERE VPLEX.PK_C = VPLEX_SV.PK__JDOID_C
AND VPLEXSV.PK_C = VPLEX_SV.PK__MEMBERS_C
AND VPLEX.MODEL_C LIKE '%VPLEX%'
AND VPLEXSV.GUID_C NOT IN (
	-- all VPLEX virtual volumes that are connected to a host
	SELECT DISTINCT VPLEXSV.GUID_C FROM 
	BB_STORAGEVOLUME95_V SV
	LEFT JOIN BB_STORAGEEXTENTJDO_BASEDON_J SV_BOE ON SV.PK_C = SV_BOE.PK__JDOID_C
	LEFT JOIN BB_BASEDONEXTENT34_V BOE ON BOE.PK_C = SV_BOE.PK__BASEDON_C
	LEFT JOIN BB_STORAGEVOLUME95_V VPLEXSV ON BOE.TARGET_C = VPLEXSV.GUID_C
	LEFT JOIN BB_STORAGESUBSYSTEM16_V VPLEX ON VPLEXSV.PK__PARENTSTORAGEEXTENT_C = VPLEX.PK_C
	WHERE
	VPLEX.MODEL_C LIKE '%VPLEX%'
)

-- find any orphaned storage volumes
--SELECT VPLEXSV.NAME_C AS VirtualVolume, VPLEXSV.MANAGEDSYSTEMNAME_C AS LUNWWN FROM BB_STORAGEVOLUME95_V VPLEXSV WHERE VPLEXSV.PK_C NOT IN ( SELECT PK__MEMBERS_C FROM BB_STORAGESUBSYBERS_8D5F5384J ) AND VPLEXSV.PK__PARENTSTORAGEEXTENT_C IN ( SELECT PK_C FROM BB_STORAGESUBSYSTEM16_V )