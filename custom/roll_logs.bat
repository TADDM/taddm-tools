@echo off

setlocal

cd /d %0\..
cd ..\bin
call common.bat
echo off
cd %COLLATION_HOME%\custom

echo Rolling logs on PSS
if exist %COLLATION_HOME%\log\error.log move %COLLATION_HOME%\log\error.log %COLLATION_HOME%\log\error.bkp
if exist %COLLATION_HOME%\log\TADDM.log move %COLLATION_HOME%\log\TADDM.log %COLLATION_HOME%\log\TADDM.bkp

REM rolling error and TADDM log manually on other servers
for /f "tokens=* eol=#" %%x in (discovery-servers.txt secondary-storage-servers.txt) do (
  echo Rolling logs on %%x
  if exist \\%%x\%COLLATION_HOME%\log\error.log move \\%%x\%COLLATION_HOME%\log\error.log \\%%x\%COLLATION_HOME%\log\error.bkp
  if exist \\%%x\%COLLATION_HOME%\log\TADDM.log move \\%%x\%COLLATION_HOME%\log\TADDM.log \\%%x\%COLLATION_HOME%\log\TADDM.bkp
)

endlocal