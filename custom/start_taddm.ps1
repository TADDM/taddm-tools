# Filename: start_taddm.ps1

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir\..\bin
.\common.bat

# Starting primary storage server
Write-Output "Starting PSS"
# Change CDTService to CDTService7.2.1 for TADDM 7.2.1
& $env:WINDIR\system32\sc.exe start CDTService

Start-Sleep -s 60

# Wait for PSS to start before continuing
Write-Output " Checking server status"
$tstatus = (((.\control.bat status) | Select-String -pattern "TADDM:" ) -split (": ", 2))[1]
while ( $tstatus -ne "Running" )
{
    Write-Output " Server status is '$tstatus'"
    # sleep 1 minute and check again
    Write-Output " Sleeping 1 minute"
    Start-Sleep -s  60
    $tstatus = (((.\control.bat status) | Select-String -pattern "TADDM:" ) -split (": ", 2))[1]
}

Write-Output  " Server is running."

Set-Location -Path $dir

# Starting secondary storage servers
$ssses = Get-Content secondary-storage-servers.txt | Select-String -pattern "#" -notMatch
ForEach ( $sss in $ssses )
{
  if ( $sss -ne $null )
  {
    Write-Output "Starting SSS $sss"
    # Change CDTService to CDTService7.2.1 for TADDM 7.2.1
    & $env:WINDIR\system32\sc.exe \\$sss start CDTService
    Start-Sleep -s 5
  }
}

# Starting discovery servers
$dses = Get-Content discovery-servers.txt | Select-String -pattern "#" -notMatch
ForEach ( $ds in $dses )
{
  if ( $ds -ne $null )
  {
    Write-Output "Starting DS $ds"
    # Change CDTService to CDTService7.2.1 for TADDM 7.2.1
    & $env:WINDIR\system32\sc.exe \\$ds start CDTService
    Start-Sleep -s 5
  }
}