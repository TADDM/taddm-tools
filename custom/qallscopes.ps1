# Filename: qallscopes.ps1

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir\..\bin
.\common.bat
Set-Location -Path $dir

New-Item scopes -type directory -force >$null 2>&1

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
$user = 'operator'
$password = 'collation'

Set-Location -Path $dir\..\bin
$scopes = .\dbquery.bat -q -u $user -p $password "SELECT NAME_C FROM BB_SCOPE6_V"
Set-Location -Path $dir
foreach($scope in $scopes) 
{
    if ($scope -ne 'NAME_C')
    {
        # replace spaces with underscores for file name
        $file = $scope -Replace ' ', '_'
        # need to replace spaces with underscores
        .\queryscopes.bat -u $user -p $password -s "$scope" > scopes/$file.scope
    }
}