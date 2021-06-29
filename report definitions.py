# -*- coding: utf-8 -*-
"""
Created on Fri Jun 25 09:55:41 2021

@author: gsalomon
"""
#%% Imports
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Tuple, List
import xml.etree.ElementTree as ET
import pandas as pd
import xlwings as xw


#%% Functions
def load_report(report_definition_file: Path)->ET.Element:
    '''Load the .xml report definition file and find the first report.

    Note: Currently this assumes only one report definition per .xml file.

    Args:
        definition_file_path (Path): The .xml report definition file to be
            loaded.
    Returns:
        report_def (ET.Element): The top element in the report definition.
    '''
    # Load the .xml report definition file
    report_tree = ET.parse(report_definition_file)
    report_root = report_tree.getroot()
    report_def = report_root.find('Report')
    return report_def


def get_report_references(template_reference_file: Path, sheet_name: str,
                          table_top_cell: str = 'O3')-> pd.DataFrame:
    '''Load Report definitions from an Excel Test Template

    Args:
        template_reference_file (Path): The path to the Excel Test Template.
        sheet_name (str): The name of the Excel Worksheet.
        table_top_cell (str, optional): Top Left Cell address for the config
           table. Defaults to 'O3'.

    Returns:
        reference_data (pd.DataFrame): A Pandas DataFrame containing the
            Report configuration info.
    '''
    report_book = xw.Book(template_reference_file)
    report_sheet = report_book.sheets[sheet_name]
    ref_range = report_sheet.range(table_top_cell).expand()
    reference_data = ref_range.options(pd.DataFrame,numbers=str).value
    reference_data.reset_index(inplace=True)
    reference_data.set_index('Name', inplace=True)
    return reference_data


def update_report_definitions(report_definition_file: Path,
                              template_file: Path,
                              template_reference_file: Path,
                              sheet_name: str):
    '''Update the report  based in the data in the Excel Test Template.

    Update the cell address, Format and units for each report item.  Update
    the template file and worksheet references. Add a comment to the report
    description noting the date and source file used for the reference update.
    Note: Currently this assumes only one report definition per .xml file.

    Args:
        report_definition_file (Path): The .xml report definition file to be
            updated.
        template_file (Path): The path to the Excel Template
            used by the report definition.
        template_reference_file (Path): The path to the Excel Test Template
            used to update the report definition.
        sheet_name (str): The name of the Excel Worksheet used to update the
        report definition.
    Returns:
        None.
    '''
    def update_report_ref(report_def: ET.Element,
                          template_file: Path,
                          template_reference_file: Path,
                          sheet_name: str):
        '''Update General information about the report.

        Add a comment to the report description noting the date and source file
        used for the reference update.  Update the template file and worksheet
        references.

        Args:
            report_def (ET.Element): The .xml element at the top of the report
                definition.
            template_reference_file (Path): The path to the Excel Test Template
                used to update the report definition.
            sheet_name (str): The name of the Excel Worksheet used to update the
            report definition.
        Returns:
            None.
        '''
        # Add note to description with the update activity
        current_time = datetime.now().isoformat(sep=' ', timespec='minutes')
        #datetime.now().strftime('%H:%M %b %d %Y')  # Alternative formatting
        template_reference = template_reference_file.name
        update_description = ''.join([f'Updated on {current_time}',
                                        f' from the {sheet_name} WorkSheet in',
                                        f' file {template_reference}'])
        description_def = report_def.find(r'./Description')
        current_description = description_def.text
        new_description = '\n'.join([current_description, update_description])
        description_def.text = new_description

        # Update the template file
        template_def = report_def.find('./FilePaths/Template')
        template_file_def = template_def.find('./File')
        template_file_def.text = template_file.name

        template_path_def = template_def.find('./Path')
        if template_path_def is not None:
            # TODO Convert template file path to relative path
            template_file_def.text = str(template_file.parent)

        # Update the template worksheet
        template_sheet_def = template_def.find('./WorkSheet')
        template_sheet_def.text = sheet_name

    def update_target(report_item: str, item_definition: ET.Element,
                      reference_data: pd.DataFrame):
        '''Update the cell address, Format and units for a given report_item.

        Args:
            report_item (str): The name of the report item.
            item_definition (ET.Element): The .xml Element containing the
                report item definition.
            reference_data (pd.DataFrame): The the report configuration info
                obtained from the Excel Test Template.
        Returns:
            None.
        '''
        # Locate the target definition parameters
        cell_address_elm = item_definition.find('./Target/CellAddress')
        cell_format_elm = item_definition.find('./Target/CellFormat')
        cell_unit_elm = item_definition.find('./Target/Unit')

        # Update the target definition parameters
        cell_address_elm.text = reference_data.at[report_item,'Address']
        cell_format = reference_data.at[report_item,'Expected Format'].strip('"')
        cell_format_elm.text = cell_format
        if cell_unit_elm is not None:
            cell_units = reference_data.at[report_item,'Units']
            cell_unit_elm.text = cell_units

    def update_report_items(reference_data: pd.DataFrame,
                            report_items: ET.Element):
        '''Update the cell address, Format and units for each report item.

        Args:
            reference_data (pd.DataFrame): The the report configuration info
                obtained from the Excel Test Template.
            report_items (ET.Element): The top .xml Element containing all of
                the report item definitions.
        Returns:
            None.
        '''
        for report_item in list(reference_data.index):
            item_xquery = f'./ReportItem[@name="{report_item}"]'
            item_definition = report_items.find(item_xquery)
            if item_definition is not None:
                update_target(report_item, item_definition, reference_data)
            else:
                # TODO In future create missing report items
                print(f'The data item:\t{report_item}\t could not be found.')


    # Load the .xml report definition file
    report_tree = ET.parse(report_definition_file)
    report_root = report_tree.getroot()
    report_def = report_root.find('Report')
    report_items = report_def.find('ReportItemList')

    # Load the Reference data
    reference_data = get_report_references(template_reference_file, sheet_name)

    # Update the template file, worksheet and description
    update_report_ref(report_def, template_file,
                      template_reference_file, sheet_name)

    # Update the report items
    update_report_items(reference_data,report_items)

    #TODO Remove report items not found in definition file

    #Save the updated report definition
    report_tree.write(report_definition_file)




#%% check report definitions
def check_report_references(report_definition_file: Path,
                            template_reference_file: Path,
                            sheet_name: str,
                            table_top_cell: str = 'AA4'):
    '''    Insert the .xml report definitions into the Excel Test Template.

    Used to verify the definitions by comparing them to configuration data.

    Args:
        report_definition_file (Path): The .xml report definition file to be
            inserted.
        template_reference_file (Path): The path to the Excel Test Template.
        sheet_name (str): The name of the Excel Worksheet.
        table_top_cell (str, optional): Top Left Cell address for the
        definitions table. Defaults to 'AA4'.
    Returns:
        None.
    '''

    def report_info(report_def: ET.Element)->Dict[str, str]:
        '''Load general report parameters into a dictionary.

        Extracts the Description, Template Dir, Template File Name and
        Template Sheet from the report definition.

        Args:
            report_def (ET.Element): The .xml element at the top of the report
                definition.
        Returns:
            Dict[str, str]: Report definition general parameters.
        '''
        report_dict = {
            'Description': report_def.findtext('./Description'),
            'Template Dir': report_def.findtext('./FilePaths/Template/Path'),
            'Template File': report_def.findtext('./FilePaths/Template/File'),
            'Template Sheet': report_def.findtext('./FilePaths/Template/WorkSheet')
            }
        return report_dict


    def find_elements(report_def: ET.Element)->pd.DataFrame:
        '''Load the report item definitions into a DataFrame.

        Returns the report item parameters:
            Name, Reference, Type, Address, Format, Label,
            Laterality, Constructor and Units
        Args:
            report_def (ET.Element): The .xml element at the top of the report
            definition.

        Returns:
            report_item_definitions (pd.DataFrame): A table containing the
            definition parameters for each item in the report.
        '''
        report_items = report_def.find('ReportItemList')
        report_item_list = list()
        for report_item in report_items.findall('./ReportItem'):
            report_item_dict = {
                'Name': report_item.get('name'),
                'Reference': report_item.findtext('./PlanReference/Name'),
                'Type': report_item.findtext('./PlanReference/Type'),
                'Address': report_item.findtext('./Target/CellAddress'),
                'Format': report_item.findtext('./Target/CellFormat'),
                'Label': report_item.findtext('./Label'),
                'Laterality': report_item.findtext('./PlanReference/Laterality'),
                'Constructor': report_item.findtext('./Constructor'),
                'Units': report_item.findtext('./Target/Unit')
                }
            report_item_list.append(report_item_dict)
        report_item_definitions = pd.DataFrame(report_item_list)
        report_item_definitions.set_index('Name', inplace=True)
        return report_item_definitions

    def get_report_sheet(report_dict: Dict[str, str])->xw.Sheet:
        '''Open the Excel worksheet referenced by the report definition.

        Args:
            report_dict (Dict[str, str]): The Report definition general
                parameters.
        Returns:
            report_sheet (xw.Sheet): The Excel worksheet referenced by the
                report definition.
        '''
        template_file_name = report_dict['Template File']
        template_path_str = report_dict['Template Dir']
        if template_path_str:
            template_file = Path(report_dict['Template Dir']) / template_file_name
        else:
            template_file = Path.cwd() / 'Data' / template_file_name
        template_sheet = report_dict['Template Sheet']
        report_book = xw.Book(template_file)
        report_sheet = report_book.sheets[template_sheet]
        return report_sheet

    def get_cell_formats(report_sheet: xw.Sheet,
                         report_item_definitions: pd.DataFrame)->pd.Series:
        '''Get the cell number format for each cell referenced in the report.

        For each report item in the definition table, query the referenced
        cell in the workshe and return the number format being used.

        Args:
            report_sheet (xw.Sheet): The Excel worksheet referenced by the
                report definition.
            report_item_definitions (pd.DataFrame): A table containing the
                definition parameters for each item in the report.
        Returns:
            format_data (pd.Series): The number format being used for each
                report item in the definition table.
        '''
        report_item_list = list(report_item_definitions.index)
        extracted_format = dict()
        for report_item in report_item_list:
            cell = report_item_definitions.at[report_item, 'Address']
            format = report_sheet.range(cell).number_format
            extracted_format[report_item] = f'"{format}"'
            extracted_format[report_item] = format
        format_data = pd.Series(extracted_format, name='Extracted Format')
        return format_data

    def insert_report_definition(report_item_definitions: pd.DataFrame,
                                 template_sheet: xw.Sheet,
                                 table_top_cell: str = 'AA4'):
        '''Insert the report definitions as a table into the template
            worksheet.

        Args:
            report_item_definitions (pd.DataFrame): A table containing the
                definition parameters for each item in the report.
            template_sheet (xw.Sheet): The Excel worksheet referenced by the
                report definition.
            table_top_cell (str, optional): Top Left Cell address for the
                definition table. Defaults to 'AA4'.
        Returns:
            None.
        '''
        # The expected order of the data columns in the Excel Test Sheet
        columns_selection = [
            'Name',
            'Address',
            'Format',
            'Extracted Format',
            'Units',
            'Label',
            'Reference',
            'Type',
            'Laterality',
            'Constructor'
            ]
        ref_range = template_sheet.range(table_top_cell).expand()
        report_data = report_item_definitions.reset_index()
        ref_range.options(pd.DataFrame,
                          index=False,
                          header=False).value = report_data[columns_selection]

    report_def = load_report(report_definition_file)
    report_dict = report_info(report_def)
    template_sheet = get_report_sheet(report_dict)
    report_item_definitions = find_elements(report_def)
    format_data = get_cell_formats(template_sheet, report_item_definitions)
    report_item_definitions = report_item_definitions.join(format_data)
    insert_report_definition(report_item_definitions,template_sheet)


#%% Main
def main():
    base_dir = Path.cwd()
    data_dir = base_dir / 'Data'
    template_file_name = 'SABR  Plan Evaluation Worksheet BLANK May 2021 For Testing.xlsx'
    template_reference_file_name = 'SABR  Plan Evaluation Worksheet BLANK May 2021 For Testing.xlsx'
    report_definition_file_name = '34 in 1.xml'
    sheet_name = 'EvalutionSheet 34Gy 1F'

    template_file = data_dir / template_file_name
    template_reference_file = data_dir / template_reference_file_name
    report_definition_file = data_dir / '34 in 1.xml'

    update_report_definitions(report_definition_file, template_file,
                              template_reference_file, sheet_name)
    check_report_references(report_definition_file,
                            template_reference_file, sheet_name)
if __name__ == '__main__':
    main()
