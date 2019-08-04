@echo off

setlocal

REM change directory to the location of the batch script file (%0)
CD /d "%~dp0"

REM SET SOURCE/TARGET FILES HERE
SET SRC=E:\ibm\taddm\dist\custom\efix\files.list
SET SHARE=E$
SET TARGET=ibm\taddm\dist\custom\efix\files.list

echo "Transfering %SRC%"

REM Secondary storage
for /f "tokens=* eol=#" %%x in (secondary-storage-servers.txt) do (
  echo "Transfering to \\%%x\%SHARE%\%TARGET%"
  xcopy /Y %SRC% \\%%x\%SHARE%\%TARGET%
)

REM Discovery servers
for /f "tokens=* eol=#" %%x in (discovery-servers.txt) do (
  echo "Transfering to \\%%x\%SHARE%\%TARGET%"
  xcopy /Y %SRC% \\%%x\%SHARE%\%TARGET%
)

endlocal