# Filename: dbmaint_wrapper.ps1

# When creating Windows scheduled task, make sure to run as taddmusr and "run with highest privileges"
# to ensure authorization to issue service stop/start

# !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
$email = "" # setting this will trigger e-mail to the recipient after maintenance is run (e.g. "taddmadmin@mycompany.com")

# change directory to the location of the batch script file
$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location -Path $dir

# file redirection during powershell execution doesn't always seem to work
Start-Transcript -Path dbmaint_wrapper.out

Write-Output "$((Get-Date).ToShortTimeString()) dbmaint_wrapper.ps1 starting"

& .\stop_taddm.ps1

# Give the servers a little more time to stop
Start-Sleep -s 30

# manually roll the error and TADDM logs once a week
Write-Output "$((Get-Date).ToShortTimeString()) Rolling logs"
& .\roll_logs.bat

# generate stats commands, technically this only needs run after an upgrade but it takes less than
# 30 seconds to run so it's inexpensive to run before each maintenance cycle
#
# If DB2 is 9.7 FP11, 10.1 FP6, or 10.5 FP7 or greater and AUTO RUNSTATS is enabled, comment out
# this section and delete dist/bin/TADDM_table_stats.sql to skip runstats. An error message will
# appear when dbmain.jy is run but it can be ignored.
Set-Location ..\bin
Write-Output "$((Get-Date).ToShortTimeString()) Generating runstats commands"
# a simple redirect will result in UTF-16 enconding, which will cause problems with Python readline
# so use ascii encoding
& .\gen_db_stats.bat 2> $null | Out-File TADDM_table_stats.sql -encoding "ascii"
Set-Location -Path $dir

# Run DB tuning/maintenance
Write-Output "$((Get-Date).ToShortTimeString()) Running DB maintenance"
& .\dbmaint.bat > dbmaint.out 2>&1

# Run additional runstats after DB tuning
# ****** This does NOT need run anymore if APAR IV47906 is installed, as it should be
# & ..\bin\db2updatestats.bat >> dbmaint.out 2>&1

# pause for just a bit, to be safe (this is probably not necessary but shouldn't hurt)
Start-Sleep 20

Write-Output "$((Get-Date).ToShortTimeString()) Starting TADDM"
& .\start_taddm.ps1
 
if ( $email -ne "" )
{
    Write-Output "$((Get-Date).ToShortTimeString()) Sending e-mail notification"
    # send e-mail notification that maintenance was complete
    & .\Notification.ps1 -from 'discovery@ibm.com' -to $email -subject 'DB Maintenance Complete'
}

Stop-Transcript