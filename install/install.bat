Miniconda3-latest-Windows-x86_64.exe /s /InstallationType=AllUsers /RegisterPython=1 /D=C:\ProgramData\Miniconda3
C:\ProgramData\Miniconda3\Scripts\activate.bat C:\ProgramData\Miniconda3
conda config --append channels conda-forge
conda create --name PlanEvaluation --file PlanEvaluation_spec.txt

