SELECT T1.guid_c      AS FIRST_GUID,
       T2.guid_c      AS SECOND_GUID,
       T1.signature_c AS FIRST_SIG,
       T2.signature_c AS SECOND_SIG,
       T1.fqdn_c
FROM   bb_computersystem40_v T1,
       bb_computersystem40_v T2,
       bb_operatingsystem62_v OS1,
       bb_operatingsystem62_v OS2
WHERE  T1.fqdn_c = T2.fqdn_c
       AND T1.guid_c != T2.guid_c
       AND T1.pk__osrunning_c = OS1.pk_c
       AND T2.pk__osrunning_c = OS2.pk_c
       AND OS1.osconfidence_c = 100
       AND OS2.osconfidence_c = 100  