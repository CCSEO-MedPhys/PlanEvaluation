Net use I: “\\dkphysicspv1\e$\Gregs_Work\Plan Checking\PlanEvaluation” /persistent:no

I:

pyinstaller --noconfirm --nowindow --log-level=WARN ^
    --add-data=".\Data;Data" ^
    --add-data=".\Icons;Icons" ^
    --add-data="PlanEvaluationConfig.xml;." ^
    --icon=".\Icons\Chart_Graph_Ascending.ico" ^
    PlanEvaluation.py


pyinstaller --clean --noconfirm --hiddenimport=tkinter --hiddenimport=scipy.spatial.transform._rotation_groups --log-level=WARN --add-data=".\Data;Data" --add-data=".\DVH Files;DVH Files" --add-data=".\Icons;Icons" --add-data=".\Output;Output" --add-data="PlanEvaluationConfig.xml;." --icon=".\Icons\Chart_Graph_Ascending.ico" PlanEvaluation.py
