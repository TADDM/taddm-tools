# Filename: abulkload.ps1

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir\..\bin
cmd /c ".\common.bat > nul 2>&1 && set" | .{process{
    if ($_ -match '^([^=]+)=(.*)') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}}
Set-Location -Path $env:COLLATION_HOME\custom

Write-Output "Auto bulkload starting." | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}

# move old results files into an archive directory
New-Item -Path $env:COLLATION_HOME\bulk\archive\results -ItemType Directory -Force | Out-Null
Move-Item $env:COLLATION_HOME\bulk\results\*.results -Destination $env:COLLATION_HOME\bulk\archive\results -Force

# move old books to archive directory
New-Item -Path $env:COLLATION_HOME\bulk\archive\books -ItemType Directory -Force | Out-Null
$discolib = ((Select-String abulkload.properties -pattern "^abulkload\.discolib\=") -split ("=",2))[1]
Write-Output  "Discovery library path is $discolib." | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
Set-Location -Path $discolib
foreach ($book in Get-ChildItem *.xml -Name)
{
    $bookProcessed = Select-String $env:COLLATION_HOME\bulk\processedfiles.list -pattern "$book" -SimpleMatch -quiet
    if ($bookProcessed)
    {
        Move-Item -Force $book -Destination $env:COLLATION_HOME\bulk\archive\books
        Write-Output "$book previously processed, moved to $env:COLLATION_HOME\bulk\archive\books" | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
    }
}

# run loadidml
Set-Location -Path $env:COLLATION_HOME\custom
$flags = ((Select-String abulkload.properties -pattern "^abulkload\.flags\=") -split ("=",2))[1]
Set-Location -Path $env:COLLATION_HOME\bin
# not a true sort on the timestamp in the filename but this should be good enough
foreach ($book in Get-ChildItem $discolib\*.xml | Sort-Object -property LastWriteTime | Get-ChildItem -Name)
{
    Write-Output  "Loading $discolib\$book." | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
    & .\loadidml.bat $flags -f $discolib\$book | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
}

# check results
if ($LastExitCode -eq 0)
{
	Write-Output "Bulkload completed" | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
	Set-Location -Path $env:COLLATION_HOME\bulk\results
	foreach ($file in Get-ChildItem *.results)
	{
		#Write-Output $file
		$resError = Select-String $file -pattern "ObjectId .*: FAILURE classtype " -quiet
		if ($resError)
		{
			Write-Output "FAILURE found in result file $file" | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
		}
	}

}
else
{
	Write-Output "Error occurred (exit code $LastExitCode), check logs or results" | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}
}

# return to base path
Set-Location -Path $dir

Write-Output "Auto bulkload completed" | %{Write-Host $_; Out-File -FilePath $env:COLLATION_HOME\log\abulkload.log -InputObject $_ -Append}