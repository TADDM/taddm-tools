# Filename: autoloadscopes.ps1

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir\..\bin
.\common.bat
Set-Location -Path $dir

$fileEntries = [IO.Directory]::GetFiles($dir + "\scopes"); 
foreach($fileName in $fileEntries) 
{ 
    [Console]::WriteLine('Processing ' + $fileName);
	[string]$firstLine = (Get-Content $fileName)[0 .. 0]
	# remove comment character and trim scope name
	$scopeName = ($firstLine -replace "#").trim()
	[Console]::WriteLine('Scope name is ' + $scopeName);
	Set-Location -Path ..\bin
	.\loadscope.bat -u administrator -p collation -s "${scopeName}" load "${fileName}"
	Set-Location -Path $dir
}