@echo off
setlocal EnableExtensions
pushd "%~dp0"

if not exist "PlanEvaluationVenv\Scripts\python.exe" (
  echo Missing PlanEvaluationVenv\Scripts\python.exe
  exit /b 1
)

rem Capture version from stderr+stdout, e.g. "Python 3.14.5"
set "PY_VER="
for /f "tokens=2 delims= " %%V in ('"PlanEvaluationVenv\Scripts\python.exe" -V 2^>^&1') do set "PY_VER=%%V"

rem Convert 3.14.5 -> 3.14
set "PY_TAG="
for /f "tokens=1,2 delims=." %%A in ("%PY_VER%") do set "PY_TAG=%%A.%%B"

if not defined PY_TAG (
  echo Failed to detect Python version from PlanEvaluationVenv
  exit /b 1
)

> ".python-version" echo %PY_TAG%
if errorlevel 1 (
  echo Failed to write .python-version
  exit /b 1
)

"PlanEvaluationVenv\Scripts\python.exe" -m pip freeze > "requirements.txt"
if errorlevel 1 (
  echo Failed to generate requirements.txt
  exit /b 1
)

echo Updated .python-version to %PY_TAG%
echo Updated requirements.txt from local PlanEvaluationVenv

popd
endlocal
exit /b 0
