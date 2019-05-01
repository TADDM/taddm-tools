@echo off

setlocal

REM change directory to the location of the batch script file (%0)
CD /d "%~dp0"

call powershell.exe .\abulkload.ps1 > abulkload_wrapper.out

REM send e-mail notification that job was completed
call powershell.exe .\Notification.ps1 -from '%COMPUTERNAME%@mycompany.com' -to 'taddm-admin@mycompany.com' -subject 'Auto Bulkload Completed' -body abulkload_wrapper.out

endlocal