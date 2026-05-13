# 01 Architecture

## 1) Purpose

PlanEvaluation imports DVH plan data, matches plan elements to report definitions, and writes values into Excel template worksheets.

## 2) Main Runtime Path

1. Application starts in PlanEvaluation.py.
2. Config is loaded from PlanEvaluationConfig.xml.
3. Report definitions are loaded from Data/Reports.pkl.
4. Plan list is populated from DVH directory scan.
5. User selects plan and report in GUI.
6. Plan loads from selected DVH file.
7. Matching runs (auto + optional manual corrections).
8. Report values are calculated and written to Excel workbook.

## 3) Module Responsibilities

PlanEvaluation.py
- Event loop and top-level GUI orchestration.
- Connects menu actions and workflow states.

main_window.py
- Main window layout and state-based button behavior.
- Plan and report header rendering.

match_window.py
- Manual matching interface.
- Match updates and direct-entry support.

build_plan_report.py
- Config I/O.
- Report definition pickle loading/building.
- Plan loading and report execution helpers.

plan_data.py
- DVH parsing and plan model.
- Unit conversion, laterality extraction, and plan element classes.
- Plan file discovery.

plan_report.py
- Report model and report element model.
- Alias/laterality matching logic.
- Excel write behavior.
- Match history and rematch behavior.

update_reports.py
- GUI flow for selecting report definition directories.
- Rebuild of report definition dictionary and pickle.

update_directories.py
- GUI flow for editing default paths and saving config.

## 4) Data Flow

Input
- DVH text file exported from TPS.
- Report definitions in XML.
- Configuration in PlanEvaluationConfig.xml.

Intermediate
- Report objects loaded into memory and serialized in Reports.pkl.
- Plan object containing properties, structures, and reference points.
- Reference match map with match method metadata.

Output
- Populated Excel workbook at configured Save file path.

## 5) External Dependencies

- PySimpleGUI for desktop interface.
- xlwings for Excel automation.
- numpy and scipy for DVH interpolation and calculations.
- pandas appears in requirements but is not central in the current runtime path.
- pywin32 underlies Windows COM interaction for Excel.

## 6) Distribution Layout

For Distribution/PlanEvaluation is a packaged copy of runtime source plus a virtual environment. Keep source-of-truth in root package, then copy intentionally during release preparation.
