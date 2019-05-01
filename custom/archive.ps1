# Filename: archive.ps1

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir\..\bin
cmd /c ".\common.bat > nul 2>&1 && set" | .{process{
    if ($_ -match '^([^=]+)=(.*)') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}}
Set-Location $env:COLLATION_HOME\custom

Start-Transcript -Path archive.out

$rc=0

# get current timestamp
$timestamp = Get-Date -uformat "%Y%m%d%H%M%Z"

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
$ARCHIVEPROPS = "$env:COLLATION_HOME\custom\archive.properties"
$AGE = "365"
$USER = "administrator"
$PASSWORD = "collation"
$LIMIT = "4000"
# err on side of caution
$DELETE = "false"
$ARCHIVEDELETEAFTER = 60
$SKIPZOS = "false"

# if properties file exists use values
if ( Test-Path $ARCHIVEPROPS ) 
{
    $AGE = ((Select-String $ARCHIVEPROPS -pattern "^archive\.age\=") -split ("=",2))[1]
    $LIMIT = ((Select-String $ARCHIVEPROPS -pattern "^archive\.limit\=") -split ("=",2))[1]
    $DELETE = ((Select-String $ARCHIVEPROPS -pattern "^archive\.delete\=") -split ("=",2))[1]
    $EMAIL = ((Select-String $ARCHIVEPROPS -pattern "^archive\.email\=") -split ("=",2))[1]
    $ARCHIVEDELETEAFTER = ((Select-String $ARCHIVEPROPS -pattern "^archive\.cleanup\=") -split ("=",2))[1]
    $SKIPZOS = ((Select-String $ARCHIVEPROPS -pattern "^archive\.skipzos\=") -split ("=",2))[1]
    $SKIPFAILED = ((Select-String $ARCHIVEPROPS -pattern "^archive\.skipfailed\=") -split ("=",2))[1]
}
else
{
    Write-Output "Properties file $ARCHIVEPROPS not found, using defaults" | Tee-Object -file archive_$timestamp.out
}

# if SKIPFAILED not present then set to 0
if ( $SKIPFAILED -eq $null ) { $SKIPFAILED = "0" }

# set e-mail address if found in properties
if ( $EMAIL -ne $null ) { $emailAddress = "$EMAIL" }

$ARCHIVEDIR = "$env:COLLATION_HOME\custom\archive"
New-Item $ARCHIVEDIR -type directory -force > $null

# create directory for class archive if it doesn't yet exist, ignore errors
New-Item $ARCHIVEDIR\$timestamp -type directory -force > $null

# classes that require superior check
$sups = "LogicalContent", "Fqdn", "IpAddress", "BindAddress", "WebSphereNamedEndpoint", "ServiceAccessPoint", "SoftwareResource", "WebSphereJ2EEResourceProperty"

Set-Location $env:COLLATION_HOME\custom

$classes = Get-Content classes.txt | Select-String -pattern "#" -notMatch
ForEach ( $class in $classes )
{
	Write-Output "Processing '$class'" | Tee-Object -file archive_$timestamp.out
		
    # purposefully not running 'archive' with the delete because it's such a huge performance hit
    # do full database backups regularly instead on the DB side
	if ( "$class" -eq "Vlan" ) 
    {
        # using -c so that we don't clean up Vlan subclasses
        & .\taddm_archive.bat -u $USER -p $PASSWORD -q -A $AGE (&{if ("$DELETE" -eq "true") { Write-Output "-D" }}) (&{if ("$SKIPZOS" -eq "true") { Write-Output "--skip_zos" }}) -C $class -L $LIMIT -c -t 5 > $ARCHIVEDIR\$timestamp\$class.txt 2>&1
    }
	elseif ( "$class" -eq "L2Interface" )
    {
        # using the --l2orphans option to clean up orphaned L2s
        & .\taddm_archive.bat -u $USER -p $PASSWORD -q -A 0 (&{if ("$DELETE" -eq "true") { Write-Output "-D" }}) (&{if ("$SKIPZOS" -eq "true") { Write-Output "--skip_zos" }}) -C $class -L $LIMIT --l2orphans -t 5 > $ARCHIVEDIR\$timestamp\$class.txt 2>&1
    }
	elseif ( $sups -contains $class )
    {
        # checking for superiors before deleting with --chk_sups flag
        & .\taddm_archive.bat -u $USER -p $PASSWORD -q -A $AGE (&{if ("$DELETE" -eq "true") { Write-Output "-D" }}) (&{if ("$SKIPZOS" -eq "true") { Write-Output "--skip_zos" }}) (&{if ("$SKIPFAILED" -ne "0") { Write-Output "--skip_failed=$SKIPFAILED" }}) -C $class -L $LIMIT --chk_sups -t 10 > $ARCHIVEDIR\$timestamp\$class.txt 2>&1
    } 
    else 
    {
        # plain jane delete
        & .\taddm_archive.bat -u $USER -p $PASSWORD -q -A $AGE (&{if ("$DELETE" -eq "true") { Write-Output "-D" }}) (&{if ("$SKIPZOS" -eq "true") { Write-Output "--skip_zos" }}) (&{if ("$SKIPFAILED" -ne "0") { Write-Output "--skip_failed=$SKIPFAILED" }}) -C $class -L $LIMIT -t 10 > $ARCHIVEDIR\$timestamp\$class.txt 2>&1
    }
    
    # if any fail, use this as the exit code
    if ( !$? ) 
    {
        Write-Output "  *** Error occurred while running archive, please investigate ***" | Tee-Object -file archive_$timestamp.out
        $rc = $LASTEXITCODE 
    }
    
    $aged = ((Select-String -pattern "^Aged " $ARCHIVEDIR\$timestamp\$class.txt) -split (" "))[2]
    Write-Output " Found $aged" | Tee-Object -file archive_$timestamp.out
}

#
# Deletion of historical archives older than 60 days
#
Get-Childitem "archive" |? {$_.psiscontainer -and $_.lastwritetime -le (Get-Date).adddays(-$ARCHIVEDELETEAFTER)} |% {Remove-Item archive\$_ -force -recurse}

# send e-mail if email address is provided
if ( $emailAddress )
{
    & .\Notification.ps1 -to $emailAddress -subject 'Archive Complete' -body 'Output of archive job attached. -TADDM Discovery' -file archive_$timestamp.out 2> $null
    #echo -e "Output of archive job attached.\n\n-TADDM Discovery" | mailx -s 'Archive Complete' -a archive_${mydate}.out $emailAddress 2>/dev/null
}

Remove-Item archive_$timestamp.out

Stop-Transcript

exit $rc