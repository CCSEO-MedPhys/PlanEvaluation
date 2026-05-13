python -m venv PlanEvaluationVenv
call PlanEvaluationVenv\Scripts\activate.bat
pip install -r requirements.txt
pip freeze > requirements.txt
echo "Virtual environment setup complete. To activate, run: call PlanEvaluationVenv\Scripts\activate.bat"