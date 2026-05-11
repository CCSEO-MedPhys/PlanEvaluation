# 02 Report Definitions and Config

## 1) Configuration File

Primary file: PlanEvaluationConfig.xml

Important sections:

DefaultDirectories
- DVH: folder scanned for plan files.
- DVH_File: optional default file name.
- ReportDefinitions/Directory: one or more folders with report XML files.
- ReportTemplates: base folder for Excel templates.
- ReportPickleFile: serialized report definitions cache.
- Save: default output Excel file.

LateralityCodeExceptions
- Body region suffix exceptions that should not be interpreted as laterality.

PlanDefaults
- DoseUnit, VolumeUnit, DistanceUnit defaults.

LateralityTable
- Mapping table converting plan laterality + report laterality + indicator size to text tokens.

DefaultLateralityPatterns
- Format strings for auto-generating laterality variants from base names.

AliasList
- Global alias references for PlanReference matching.

## 2) Report Definition XML Structure

Each XML file with root ReportDefinitions can contain one or more Report nodes.

Report-level fields:
- Name
- Description
- FilePaths/Template/File
- FilePaths/Template/WorkSheet
- FilePaths/Save/Path
- FilePaths/Save/File
- FilePaths/Save/WorkSheet
- ReportItemList

Each ReportItem supports:
- name attribute
- Label
- Category optional
- Constructor optional
- PlanReference required for plan data mapping
- Target optional for Excel output

PlanReference fields:
- Type (Plan Property, Structure, Reference Point, Ratio)
- Name
- Laterality optional
- Aliases optional (with Join behavior)

Target fields:
- Unit optional
- CellAddress
- CellFormat optional

## 2A) Spreadsheet Mapping Source
The hidden columns from O through AJ in each template worksheet contain a spreadsheet mapping table that connects worksheet cells to the XML report definitions.
This region contains two tables The Definitions table columns (AA to AJ) map directly to elements in the xml table.  The config table contains formulas that compare the address, format and expected units from the template with the values in the Definitions table.  The combination of these two tables simplify the process of maintaining the template report definition files.

Conceptual column mapping:
- Name -> ReportItem name attribute
- Reference, Type, Laterality, Constructor -> PlanReference fields
- Address, Format -> Target CellAddress and CellFormat
- Units -> conversion and validation expectations

Concrete mapping examples from Definitions60Gy8F:
- Patient -> cell C3, Label Patient:, Reference Patient Name, Type Plan Property
- Dose -> cell G3, Label Prescription Dose (cGy):, Reference Total dose, Type Plan Property
- PTV_V100 -> cell F16, Label PTV - V100(%), Reference PTV, Type Structure, Constructor V 100 %
- LungV20 -> cell F27, Label V20 (Total Lung), Reference Lung, Type Structure, Laterality Both, Constructor V 2000 cGy
- ProxBronchMaxDose -> cell F41, Label Bronchus (max point dose), Reference BronchialTree, Type Structure, Laterality Ipsilateral, Constructor Max Dose

## 2B) Hidden Formula Validation Logic

The hidden helper logic in config60Gy8F Formulas validates that worksheet mappings and XML definitions are aligned.

Formula patterns:
- INDIRECT(Qx) extracts the value from the mapped worksheet cell.
- CELL("address", <cell>) extracts the source address; SUBSTITUTE normalizes formatting.
- CELL("format", INDIRECT(Qx)) extracts Excel format codes.
- VLOOKUP against Definitions60Gy8F retrieves expected address, expected format, and related metadata.
- Address Check compares extracted address to expected address.
- Format Check compares extracted and expected formats, with special handling for text format.
- Unit Check verifies unit text consistency with label content.

Clinical-release warning:
- Rows marked ?? or Check must be reviewed and resolved before clinical release.

## 3) Matching Algorithm

For each report element reference:

1. Attempt exact match by reference name.
2. Attempt laterality name transform using:
   - plan laterality from Plan model
   - reference laterality in report item
   - default laterality patterns
   - laterality lookup table
3. Attempt aliases from both:
   - item-local alias list
   - global alias list from config

If matched, method is Auto.
If changed in manual match window, method is Manual or Direct Entry.

## 4) Unit Conversion

Main conversion logic is in plan_data.py convert_units.

Supported conversion families:
- Dose: cGy, Gy, percent of prescription dose
- Volume: cc, percent of reference volume

Some constructors and conversions rely on reference dose or volume. Ensure those values are present in the plan and report context.

## 5) Updating Report Definitions

Two paths exist in GUI:

Load Report Definition File
- Loads a single XML immediately into memory for the active session.

Update all Report Definitions
- Prompts for definition directories.
- Rebuilds report definition dictionary.
- Writes Data/Reports.pkl cache.

Recommended practice:
- After any report XML change, run Update all Report Definitions before clinical use.
