@echo off

setlocal

REM change directory to the location of the batch script file (%0)
CD /d "%~dp0"

time /t && echo dbmaint_wrapper.bat starting

call stop_taddm.bat

REM Give the servers a little more time to stop
timeout /t 30 /nobreak > NUL

REM manually roll the error and TADDM logs once a week
time /t && echo Rolling logs
call roll_logs.bat

REM generate stats commands, technically this only needs run after an upgrade but it takes less than
REM 30 seconds to run so it's inexpensive to run before each maintenance cycle
REM
REM If DB2 is 9.7 FP11, 10.1 FP6, or 10.5 FP7 or greater and AUTO RUNSTATS is enabled, comment out
REM this section and delete dist/bin/TADDM_table_stats.sql to skip runstats. An error message will
REM appear when dbmain.jy is run but it can be ignored.
..\bin
time /t && echo Generating runstats commands
gen_db_stats.bat >TADDM_table_stats.sql 2> NUL
cd ..\custom

REM Run DB tuning/maintenance
time /t && echo Running DB maintenance
call dbmaint.bat > dbmaint.out 2>&1

REM Run additional runstats after DB tuning
REM ****** This does NOT need run anymore if APAR IV47906 is installed, as it should be
REM call ..\bin\db2updatestats.bat >> dbmaint.out 2>&1

rem pause for just a bit, to be safe (this is probably not necessary but shouldn't hurt)
timeout /t 20 /nobreak > NUL

time /t && echo Starting TADDM
call start_taddm.bat

REM send e-mail notification that maintenance was complete
call powershell.exe .\Notification.ps1 -from 'discovery@mycompany.com' -to 'taddm-admin@mycompany.com' -subject 'DB Maintenance Complete'

endlocal