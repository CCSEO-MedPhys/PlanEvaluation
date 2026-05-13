# 03 Maintenance Workflow

## 1) Safe Change Process

1. Copy production config and report files to a test area.
2. Make one focused change at a time (config, report XML, or code).
3. Rebuild report definitions cache if XML changed.
4. Test with representative DVH files.
5. Verify key worksheet outputs against manual reference values.
6. Promote change to distribution package only after sign-off.

## 2) Routine Maintenance Tasks

Task: Add a new report template
- Add template file to ReportTemplates location.
- Add or update report XML under ReportDefinitions directory.
- Include mapping for all required fields.
- Run Update all Report Definitions.
- Validate generated worksheet.

Task: Modify field mappings for an existing template
- Open the worksheet and update the Definitions table entries for changed fields.
- Sync XML report items with mapping updates (Name, Reference, Type, Laterality, Constructor).
- Confirm target cell and format mappings still match the template.
- Run Update all Report Definitions.
- Validate with representative test DVH files.

Task: Create a new report template from 60Gy/8F pattern
- Copy a baseline worksheet pattern and create a new Definitions mapping table.
- Map all required report fields to worksheet cells and expected formats.
- Update or create corresponding report XML definitions.
- Run Update all Report Definitions.
- Validate generated outputs with representative test DVH files before release.

Task: Improve matching success
- Add aliases in report item or global AliasList.
- Adjust laterality mapping if naming convention changed.
- Re-run matching and check unmatched list.

Task: Change default paths
- Use Set Default Locations in GUI.
- Confirm PlanEvaluationConfig.xml was saved correctly.
- Verify path accessibility for all users.

## 3) Validation Checklist

Functional
- App opens and plan tree populates.
- Report list loads.
- Plan loads from selected DVH.
- Match Structures opens manual match and returns.
- Generate Report writes output workbook.

Data quality
- Patient demographics are correct.
- Dose and fraction values are correct units.
- At least five high-impact metrics checked manually.
- No required report cells left blank unexpectedly.
- Definitions-to-ReportItem coverage is one-to-one for required fields.
- Address Check passes for mapped rows.
- Format Check passes for mapped rows.
- Unit Check passes for mapped rows.
- No unresolved placeholders (for example ?? or Check) remain before release.

Environment
- Excel COM automation works on target machine.
- Python dependencies installed and versions locked.

## 4) Release Packaging Checklist

1. Confirm root package state is validated.
2. Copy updated source/config/data into For Distribution/PlanEvaluation.
3. Ensure PlanEvaluation.bat points to intended environment/interpreter.
4. Perform smoke test from distribution folder, not only from source root.
5. Archive release with date stamp and validation notes.

## 5) Incident Response

If output values look wrong:
- Stop clinical use for that report profile.
- Reproduce with known test DVH.
- Check matching map and direct entries.
- Check report XML constructor and target units.
- Check config defaults and laterality tables.
- Document root cause and corrective action in change record.
