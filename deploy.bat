@echo off
setlocal EnableExtensions

pushd "%~dp0"
if errorlevel 1 (
  echo Failed to enter script directory.
  exit /b 1
)

set "ROOT=."
set "DIST=deploy"
set "DEPLOY_ZIP=%DIST%.zip"
set "SEVEN_ZIP=C:\Program Files\7-Zip\7z.exe"
set "STAGE=preflight"

rem Preflight checks
if not exist "%SEVEN_ZIP%" (
  echo Missing required tool: %SEVEN_ZIP%
  goto :fail
)
if not exist "%ROOT%\requirements.txt" (
  echo Missing requirements file: %ROOT%\requirements.txt
  goto :fail
)
if not exist "%ROOT%\PlanEvaluationConfig.xml" (
  echo Missing config file: %ROOT%\PlanEvaluationConfig.xml
  goto :fail
)
if not exist "%ROOT%\PlanEvaluation.py" (
  echo Missing entry script: %ROOT%\PlanEvaluation.py
  goto :fail
)
if not exist "%ROOT%\docs\PlanEvaluation User Manual.pdf" (
  echo Missing docs\PlanEvaluation User Manual.pdf
  goto :fail
)
if not exist "%ROOT%\Icons" (
  echo Missing Icons folder: %ROOT%\Icons
  goto :fail
)

call "%~dp0get_environment_build.bat"
if errorlevel 1 (
  echo get_environment_build.bat failed.
  goto :fail
)

rem Resolve package Python version from .python-version (single line like 3.14)
set "STAGE=python-version"
if not exist ".python-version" (
  echo Missing .python-version file.
  goto :fail
)
for /f "usebackq tokens=1" %%A in (".python-version") do set "PY_TAG=%%A"
if not defined PY_TAG (
  echo .python-version is empty.
  goto :fail
)

rem Trim accidental spaces
for /f "tokens=1 delims= " %%A in ("%PY_TAG%") do set "PY_TAG=%%A"
py -%PY_TAG% --version >nul 2>&1
if errorlevel 1 (
  echo Python launcher cannot resolve version tag from .python-version: %PY_TAG%
  goto :fail
)

rem Choose runtime architecture suffix (optional arg: x64, x86, arm64)
set "ARCH_SUFFIX=-64"
if /I "%~1"=="x64" set "ARCH_SUFFIX=-64"
if /I "%~1"=="x86" set "ARCH_SUFFIX=-32"
if /I "%~1"=="arm64" set "ARCH_SUFFIX=-arm64"
if "%~1"=="" (
  if /I "%PROCESSOR_ARCHITECTURE%"=="x86" set "ARCH_SUFFIX=-32"
  if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ARCH_SUFFIX=-arm64"
) else (
  if /I not "%~1"=="x64" if /I not "%~1"=="x86" if /I not "%~1"=="arm64" (
    echo Invalid architecture override: %~1
    echo Valid values: x64, x86, arm64
    goto :fail
  )
)

rem Build tags from package version
set "RUNTIME_TAG=PythonCore/%PY_TAG%%ARCH_SUFFIX%"
set "PY_TAG_NODOT=%PY_TAG:.=%"
rem Build the expected ._pth filename from PY_TAG (3.14 -> 314)
set "PTH_FILE=%DIST%\PlanEvaluation\runtime\python%PY_TAG_NODOT%._pth"

echo Using PY_TAG=%PY_TAG%
echo Using RUNTIME_TAG=%RUNTIME_TAG%
echo Using optional PTH_FILE=%PTH_FILE%

rem Clean old output
set "STAGE=clean-output"
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%DIST%" (
  echo Failed to remove existing output folder: %DIST%
  goto :fail
)
if exist "%DEPLOY_ZIP%" del /q "%DEPLOY_ZIP%"
if exist "%DEPLOY_ZIP%" (
  echo Failed to remove existing zip: %DEPLOY_ZIP%
  goto :fail
)

mkdir "%DIST%" || goto :fail
rem make relevant subdirectories
mkdir "%DIST%\PlanEvaluation" || goto :fail
mkdir "%DIST%\DVH Files" || goto :fail
mkdir "%DIST%\Completed Reports" || goto :fail

rem Copy app source and assets
set "STAGE=copy-python"
if not exist "%ROOT%\*.py" (
  echo No Python source files found at %ROOT%\*.py
  goto :fail
)
for %%F in (%ROOT%\*.py) do (
  type "%%~fF" > "%DIST%\PlanEvaluation\%%~nxF"
  if errorlevel 1 (
    echo Python source copy failed for %%~nxF.
    goto :fail
  )
)
if exist "%DIST%\PlanEvaluation\__init__.py" del /q "%DIST%\PlanEvaluation\__init__.py"

set "STAGE=copy-config"
copy /y "%ROOT%\PlanEvaluationConfig.xml" "%DIST%\PlanEvaluation" >nul
if errorlevel 1 (
  echo PlanEvaluationConfig.xml copy failed.
  goto :fail
)
set "STAGE=patch-config"
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
  goto :fail
)
robocopy "%ROOT%\Icons" "%DIST%\PlanEvaluation\Icons" * /E /R:1 /W:1 /NFL /NDL /NJH /NJS >nul
if errorlevel 8 (
  echo Icons copy failed.
  goto :fail
)
set "STAGE=copy-manual"
copy /y "%ROOT%\docs\PlanEvaluation User Manual.pdf" "%DIST%\" >nul
if errorlevel 1 (
  echo User manual copy failed.
  goto :fail
)

set "STAGE=copy-data"
robocopy "%ROOT%\Data" "%DIST%\PlanEvaluation\Data" * /E /R:1 /W:1 /NFL /NDL /NJH /NJS >nul
if errorlevel 8 (
  echo Data copy failed.
  goto :fail
)

rem Extract embedded Python runtime into distribution
set "STAGE=install-runtime"
py install "%RUNTIME_TAG%" --target="%DIST%\PlanEvaluation\runtime"
if errorlevel 1 (
  echo Failed to install embedded runtime. Check Python Install Manager and tag.
  goto :fail
)
if not exist "%DIST%\PlanEvaluation\runtime\python.exe" (
  echo Embedded runtime missing executable: %DIST%\PlanEvaluation\runtime\python.exe
  goto :fail
)

rem Configure runtime ._pth when present (PythonCore may not use one)
set "STAGE=configure-pth"
if exist "%PTH_FILE%" (
  > "%PTH_FILE%" (
    echo python%PY_TAG_NODOT%.zip
    echo .
    echo Lib\site-packages
    echo import site
  )
  findstr /x /c:"python%PY_TAG_NODOT%.zip" "%PTH_FILE%" >nul || goto :fail
  findstr /x /c:"." "%PTH_FILE%" >nul || goto :fail
  findstr /x /c:"Lib\site-packages" "%PTH_FILE%" >nul || goto :fail
  findstr /x /c:"import site" "%PTH_FILE%" >nul || goto :fail
) else (
  echo Runtime has no python._pth file. Using default PythonCore search paths.
)

rem Install dependencies directly into portable runtime
set "STAGE=vendor-dependencies"
"%DIST%\PlanEvaluation\runtime\python.exe" -m pip install --no-compile -r "%ROOT%\requirements.txt"
if errorlevel 1 (
  echo Dependency vendoring failed.
  goto :fail
)

rem Create portable launcher
set "STAGE=create-launcher"
> "%DIST%\PlanEvaluation.bat" (
  echo @echo off
  echo setlocal EnableExtensions
  echo.
  echo set "SCRIPT_DIR=%%~dp0"
  echo set "APP_DIR=%%SCRIPT_DIR%%PlanEvaluation"
  echo set "RUNTIME_DIR=%%APP_DIR%%\runtime"
  echo set "PATH=%%RUNTIME_DIR%%;%%RUNTIME_DIR%%\DLLs;%%PATH%%"
  echo "%%RUNTIME_DIR%%\python.exe" "%%APP_DIR%%\PlanEvaluation.py"
  echo set "EXITCODE=%%ERRORLEVEL%%"
  echo exit /b %%EXITCODE%%
)
if not exist "%DIST%\PlanEvaluation.bat" (
  echo Missing deploy launcher: %DIST%\PlanEvaluation.bat
  goto :fail
)

rem Create UNC-safe launcher that bypasses cmd.exe
> "%DIST%\PlanEvaluation.vbs" (
  echo Set shell = CreateObject("WScript.Shell")
  echo Set fso = CreateObject("Scripting.FileSystemObject")
  echo scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
  echo appDir = scriptDir ^& "\\PlanEvaluation"
  echo runtimeDir = appDir ^& "\\runtime"
  echo shell.CurrentDirectory = scriptDir
  echo shell.Environment("PROCESS")("PATH") = runtimeDir ^& ";" ^& runtimeDir ^& "\\DLLs;" ^& shell.Environment("PROCESS")("PATH")
  echo cmd = Chr(34) ^& runtimeDir ^& "\\python.exe" ^& Chr(34) ^& " " ^& Chr(34) ^& appDir ^& "\\PlanEvaluation.py" ^& Chr(34)
  echo shell.Run cmd, 1, False
)
if not exist "%DIST%\PlanEvaluation.vbs" (
  echo Missing deploy launcher: %DIST%\PlanEvaluation.vbs
  goto :fail
)

rem Zip output
set "STAGE=zip-output"
pushd "%DIST%" || goto :fail
"%SEVEN_ZIP%" a -tzip "..\%DEPLOY_ZIP%" "." >nul
popd
if errorlevel 1 (
  echo Zip creation failed.
  goto :fail
)

if not exist "%DEPLOY_ZIP%" (
  echo Zip output not found: %DEPLOY_ZIP%
  goto :fail
)

set "STAGE=validate-zip"
"%SEVEN_ZIP%" l "%DEPLOY_ZIP%" > "%TEMP%\deploy_zip_list.txt"
if errorlevel 1 (
  echo Unable to inspect zip output.
  goto :fail
)
findstr /i /c:"PlanEvaluation.bat" "%TEMP%\deploy_zip_list.txt" >nul
if errorlevel 1 (
  echo Zip validation failed: PlanEvaluation.bat missing from archive.
  goto :fail
)
findstr /i /c:"PlanEvaluation.vbs" "%TEMP%\deploy_zip_list.txt" >nul
if errorlevel 1 (
  echo Zip validation failed: PlanEvaluation.vbs missing from archive.
  goto :fail
)
findstr /i /c:"deploy\\" "%TEMP%\deploy_zip_list.txt" >nul
if not errorlevel 1 (
  echo Zip validation failed: deploy\ folder found in archive root.
  goto :fail
)

echo Portable build complete: %DEPLOY_ZIP%

popd
endlocal
exit /b 0

:fail
echo Failed stage: %STAGE%
echo Deployment build failed.
popd
endlocal
exit /b 1
