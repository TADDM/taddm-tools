SELECT DISTINCT
d1.EVENT_ATTRIBUTE SENSOR
,d1.EVENT_DESC
FROM
 DISCEVNT d1--, DISCEVNT_ATTR_IP dai1
 , DISCEVNT_RUN dr1
WHERE
 (d1.EVENT_RUNID = dr1.DE_RUN_ID) AND
 d1.EVENT_SEVERITY = 5 AND
 d1.EVENT_ATTRIBUTE = 'CustomTemplateSensor(vipr/devices)' AND
 dr1.DE_START_WEEK_DATE IN
  ( SELECT * FROM ( SELECT DISTINCT DE_START_WEEK_DATE FROM DISCEVNT_RUN ORDER BY DE_START_WEEK_DATE DESC )
  -- DB2
  FETCH FIRST 1 ROWS ONLY )