@echo off
setlocal
set rc=0

cd /d %0\..
cd ..\bin
call common.bat
echo off
cd %COLLATION_HOME%\custom

REM !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
SET AGE=365
SET USER=administrator
SET PASSWORD=collation
SET LIMIT=4000

MKDIR %COLLATION_HOME%\custom\archive 2> NUL

REM get current timestamp
For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
For /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a%%b)

REM if space found at beginning replace with 0
if "%mytime:~0,1%" == " " set mytime=0%mytime:~1,3%

for /f "tokens=* eol=#" %%x in (classes.txt) do (
	echo Processing %%x
	REM create directory for class archive if it doesn't yet exist, ignore errors
	MKDIR %COLLATION_HOME%\custom\archive\%%x 2> NUL
		
	MKDIR %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%
	CD %COLLATION_HOME%\custom
    
	if "%%x" == "Vlan" (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% -c -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ) else (
	if "%%x" == "L2Interface" (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% --l2orphans -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ) else (
	if "%%x" == "LogicalContent" (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% --chk_sups -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ) else (
	if "%%x" == "Fqdn" (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% --chk_sups -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ) else (
	if "%%x" == "IpAddress" (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% --chk_sups -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ) else (
	if "%%x" == "BindAddress" (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% --chk_sups -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ) else (
        REM run delete / don't archive b/c not necessary, should be doing database backups instead
        call taddm_archive.bat -u %USER% -p %PASSWORD% -q -A %AGE% -D -C %%x -L %LIMIT% -E %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime% > %COLLATION_HOME%\custom\archive\%%x\%mydate%_%mytime%\output.txt 2>&1
    ))))))
    
	set rc=%errorlevel%
)

REM !!! CHANGE THESE VARIABLES TO APPLY TO YOUR ENVIRONMENT !!!
powershell.exe .\Notification.ps1 -from 'discovery@mycompany.com' -to 'discovery-admin@mycompany.com' -subject 'Archive Complete' -body 'classes.txt'
exit /b %rc%