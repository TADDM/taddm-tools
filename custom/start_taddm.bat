@echo off

setlocal

REM change directory to the location of the batch script file (%0)
CD /d "%~dp0"

REM STARTING PRIMARY STORAGE SERVER
REM Change CDTService to CDTService7.2.1 for TADDM 7.2.1
call %WINDIR%\system32\sc.exe start CDTService

timeout /t 300 /nobreak > NUL

REM STARTING SECONDARY STORAGE SERVERS
for /f "tokens=* eol=#" %%x in (secondary-storage-servers.txt) do (
  REM Change CDTService to CDTService7.2.1 for TADDM 7.2.1
  call %WINDIR%\system32\sc.exe \\%%x start CDTService
  timeout /t 5 /nobreak > NUL
)

timeout /t 60 /nobreak > NUL

REM STARTING DISCOVERY SERVERS
for /f "tokens=* eol=#" %%x in (discovery-servers.txt) do (
  REM Change CDTService to CDTService7.2.1 for TADDM 7.2.1
  call %WINDIR%\system32\sc.exe \\%%x start CDTService
  timeout /t 5 /nobreak > NUL
)

endlocal