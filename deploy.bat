@echo off
setlocal EnableExtensions

pushd "%~dp0"

call "%~dp0get_environment_build.bat"
if errorlevel 1 (
  echo get_environment_build.bat failed.
  exit /b 1
)

set "ROOT=."
set "DIST=deploy"

rem Resolve package Python version from .python-version (single line like 3.14)
if not exist ".python-version" (
  echo Missing .python-version file.
  exit /b 1
)
set /p PY_TAG=<.python-version

rem Trim accidental spaces
for /f "tokens=* delims= " %%A in ("%PY_TAG%") do set "PY_TAG=%%A"

rem Choose runtime architecture suffix
set "ARCH_SUFFIX=-64"
if /I "%PROCESSOR_ARCHITECTURE%"=="x86" set "ARCH_SUFFIX=-32"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ARCH_SUFFIX=-arm64"

rem Build tags from package version
set "RUNTIME_TAG=PythonEmbed/%PY_TAG%%ARCH_SUFFIX%"
set "PY_TAG_NODOT=%PY_TAG:.=%"
rem Build the expected ._pth filename from PY_TAG (3.14 -> 314)
set "PTH_FILE=%DIST%\PlanEvaluation\runtime\python%PY_TAG_NODOT%._pth"

echo Using PY_TAG=%PY_TAG%
echo Using RUNTIME_TAG=%RUNTIME_TAG%
echo Using PTH_FILE=%PTH_FILE%

rem Clean old output
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%DIST%.zip" del /q "%DIST%.zip"

mkdir "%DIST%" || exit /b 1
rem make relevant subdirectories
mkdir "%DIST%\PlanEvaluation" || exit /b 1
mkdir "%DIST%\DVH Files" || exit /b 1
mkdir "%DIST%\Completed Reports" || exit /b 1

rem Copy app source and assets
copy /y "%ROOT%\*.py" "%DIST%\PlanEvaluation" >nul || exit /b 1
if exist "%DIST%\PlanEvaluation\__init__.py" del /q "%DIST%\PlanEvaluation\__init__.py"

copy /y "%ROOT%\PlanEvaluationConfig.xml" "%DIST%\PlanEvaluation" >nul || exit /b 1
set "DIST_CONFIG=%DIST%\PlanEvaluation\PlanEvaluationConfig.xml"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p='%DIST_CONFIG%';" ^
  "$c=Get-Content -Raw -Path $p;" ^
  "$c=[regex]::Replace($c,'<DVH>[\s\S]*?</DVH>','<DVH>..\DVH Files</DVH>');" ^
  "$c=[regex]::Replace($c,'<Save>[\s\S]*?</Save>','<Save>..\Completed Reports\SABR Plan Evaluation Worksheet.xlsx</Save>');" ^
  "$utf8NoBom=New-Object System.Text.UTF8Encoding($false);" ^
  "[System.IO.File]::WriteAllText($p,$c,$utf8NoBom)"
if errorlevel 1 (
  echo Failed to update distribution PlanEvaluationConfig.xml.
  exit /b 1
)
robocopy "%ROOT%\Icons" "%DIST%\PlanEvaluation\Icons" * /E /R:1 /W:1 /NFL /NDL /NJH /NJS >nul
if errorlevel 8 (
  echo Icons copy failed.
  exit /b 1
)
if not exist "%ROOT%\docs\PlanEvaluation User Manual.pdf" (
  echo Missing docs\PlanEvaluation User Manual.pdf
  exit /b 1
)
copy /y "%ROOT%\docs\PlanEvaluation User Manual.pdf" "%DIST%\" >nul || exit /b 1

robocopy "%ROOT%\Data" "%DIST%\PlanEvaluation\Data" * /E /R:1 /W:1 /NFL /NDL /NJH /NJS >nul
if errorlevel 8 (
  echo Data copy failed.
  exit /b 1
)

rem Extract embedded Python runtime into distribution
py install "%RUNTIME_TAG%" --target="%DIST%\PlanEvaluation\runtime"
if errorlevel 1 (
  echo Failed to install embedded runtime. Check Python Install Manager and tag.
  exit /b 1
)

rem Locate the runtime ._pth file and enforce isolated search paths
if not exist "%PTH_FILE%" (
  echo Could not find runtime ._pth file: %PTH_FILE%
  exit /b 1
)
> "%PTH_FILE%" (
  echo python%PY_TAG_NODOT%.zip
  echo .
  echo Lib\site-packages
  echo import site
)

rem Vendor dependencies into runtime\Lib\site-packages using build-host Python
py -%PY_TAG% -m pip install --no-compile --target "%DIST%\runtime\Lib\site-packages" -r "%ROOT%\requirements.txt"
if errorlevel 1 (
  echo Dependency vendoring failed.
  exit /b 1
)

rem Create portable launcher
> "%DIST%\PlanEvaluation.bat" (
  echo @echo off
  echo setlocal
  echo rem Run from the folder containing this launcher so relative paths always resolve.
  echo pushd "%~dp0"
  echo CALL "%%~dp0PlanEvaluation\runtime\python.exe" "%%~dp0PlanEvaluation\PlanEvaluation.py"
  echo popd
  echo endlocal
)

rem Zip output
pushd "%DIST%"
"C:\Program Files\7-Zip\7z.exe" a -tzip "..\%DIST%.zip" "." >nul
popd
if errorlevel 1 (
  echo Zip creation failed.
  exit /b 1
)

echo Portable build complete: %DIST%.zip

popd
endlocal
exit /b 0
