@echo off
setlocal

rem Run from the folder containing this launcher so relative paths always resolve.
pushd "%~dp0"
CALL ".\PlanEvaluation\PlanEvaluationVenv\Scripts\python.exe" ".\PlanEvaluation\PlanEvaluation.py"
popd

endlocal
