# Filename: stop_taddm.ps1

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir\..\bin
.\common.bat

Set-Location -Path $dir

# Stopping discovery servers
$dses = Get-Content discovery-servers.txt | Select-String -pattern "#" -notMatch
ForEach ( $ds in $dses )
{
  if ( $ds -ne $null )
  {
    Write-Output "Stopping DS $ds"
    # Change CDTService to CDTService7.2.1 for TADDM 7.2.1
    & $env:WINDIR\system32\sc.exe \\$ds stop CDTService
  }
}

Start-Sleep -s 5

# Stopping secondary storage servers
$ssses = Get-Content secondary-storage-servers.txt | Select-String -pattern "#" -notMatch
ForEach ( $sss in $ssses )
{
  if ( $sss -ne $null )
  {
    Write-Output "Stopping SSS $sss"
    # Change CDTService to CDTService7.2.1 for TADDM 7.2.1
    & $env:WINDIR\system32\sc.exe \\$sss stop CDTService
  }
}

Start-Sleep -s 5

Set-Location -Path $dir\..\bin

# Stopping primary storage server
Write-Output "Stopping PSS"
# Change CDTService to CDTService7.2.1 for TADDM 7.2.1
& $env:WINDIR\system32\sc.exe stop CDTService

# sleep 5 seconds to allow stop
Start-Sleep -s 5

Set-Location -Path $dir