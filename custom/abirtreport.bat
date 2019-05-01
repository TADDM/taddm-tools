@echo off
setlocal
set rc=0

cd /d %0\..
cd ..\bin
call common.bat
echo off
cd %COLLATION_HOME%\custom

REM Get current timestamp 
REM Note: tokens 2-4 contain the proper variables only when run via task scheduler.
REM if this is run directly via the command line then a value will be missing
For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)

set BIRT_HOME=%COLLATION_HOME%\deploy-tomcat\birt-viewer

cd %COLLATION_HOME%\deploy-tomcat\birt-viewer\WEB-INF\resources

REM generate the reports
call genReport.bat -f HTML -o %COLLATION_HOME%\custom\reports\sample1-%mydate%.html -F %COLLATION_HOME%\custom\reports\sample1.properties %COLLATION_HOME%\deploy-tomcat\birt-viewer\WEB-INF\report\taddm_server_affinity_byScope_withLogConn.rptdesigncompiled
call genReport.bat -f HTML -o %COLLATION_HOME%\custom\reports\sample2-%mydate%.html -F %COLLATION_HOME%\custom\reports\sample2.properties %COLLATION_HOME%\deploy-tomcat\birt-viewer\WEB-INF\report\taddm_server_affinity_byScope_withLogConn.rptdesigncompiled

cd %COLLATION_HOME%\custom

REM e-mail reports to SharePoint
call powershell.exe .\Notification.ps1 -from 'taddm@ibm.com' -to 'taddm@ibm.com' -file '%COLLATION_HOME%\custom\reports\sample1-%mydate%.html'
call powershell.exe .\Notification.ps1 -from 'taddm@ibm.com' -to 'taddm@ibm.com' -file '%COLLATION_HOME%\custom\reports\sample2-%mydate%.html'
