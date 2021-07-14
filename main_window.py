'''Creates the main GUI window
'''

#%% imports etc.
import os
import sys
import textwrap as tw
from pathlib import Path
from copy import deepcopy
from functools import partial
from operator import attrgetter
import xml.etree.ElementTree as ET
from collections import OrderedDict
from typing import Optional, Union, Any, Dict, Tuple, List, Set, NamedTuple, TypeVar, Generic

import xlwings as xw
import PySimpleGUI as sg

from build_plan_report import load_config, update_reports, load_reports, run_report, load_dvh
from build_plan_report import IconPaths
from plan_report import Report, ReferenceGroup, MatchList, MatchHistory, rerun_matching
from plan_data import DvhFile, Plan, PlanItemLookup, PlanElements, scan_for_dvh, PlanDescription, get_default_units, get_laterality_exceptions, find_plan_files
from match_window import manual_match
from update_reports import update_report_definitions
from update_directories import main_menu
from gui_helper import ButtonSettings, ElementConfig, WindowConfig

Values = Dict[str, List[str]]
ConversionParameters = Dict[str, Union[str, float, None]]
Settings = TypeVar('Settings')
SettingsGroup = Tuple[str, Settings]
SettingsList = List[SettingsGroup]


#%% Plan Header
def create_plan_header()->sg.Frame:
    '''Create a Frame GUI element containing patient and plan info.
    Returns:
        sg.Frame -- A group of text GUI s with Dose, Course,
        export date, patient name and ID for the plan.
    '''
    def build_patient_header():
        # Set Patient Label
        pt_name_label = sg.Text('Name:', size=(6,1))
        pt_name_text = sg.Text('', key='pt_name_text', size=(20,1))
        pt_id_label = sg.Text('ID:', size=(6,1))
        pt_id_text = sg.Text('', key='id_text', size=(20,1))
        patient_desc = [[pt_name_label, pt_name_text],
                        [pt_id_label, pt_id_text]]
        patient_header = sg.Frame('Patient:', patient_desc,
                                  key='patient_header',
                                  title_location=sg.TITLE_LOCATION_TOP_LEFT,
                                  font=('Calibri', 12),
                                  element_justification='left')
        return patient_header

    def build_plan_info_layout():
        dose_label = sg.Text('Dose:', size=(6,1))
        dose_text = sg.Text('', key='dose_text', size=(30,1))
        course_label = sg.Text('Course:', size=(6,1))
        course_text = sg.Text('', key='course_text', size=(30,1))
        exported_label = sg.Text('Exported:', size=(6,1))
        exported_text = sg.Text('', key='exported_text', size=(30,1))
        plan_header_layout = [[dose_label, dose_text],
                              [course_label, course_text],
                              [exported_label, exported_text]]
        return plan_header_layout


    # Set Main Label
    plan_title = sg.Text(text='', key='plan_title', size=(12,1),
                         font=('Calibri', 14, 'bold'), pad=((5, 0), (5, 10)),
                         justification='center')
    load_plan_button = sg.Button(key='load_plan', button_text='Select a Plan',
                                 disabled=True, button_color=('red', 'white'),
                                 border_width=5, pad=((10, 0), (0, 0)),
                                 size=(12, 1), auto_size_button=False,
                                 font=('Times New Roman', 12, 'normal'))
    header_layout = [[plan_title, load_plan_button]]
    header_layout += build_plan_info_layout()
    header_layout += [[build_patient_header()]]
    plan_header = sg.Frame('Plan', header_layout, key='plan_header',
                           font=('Arial Black', 14, 'bold'),
                           element_justification='center',
                           title_location=sg.TITLE_LOCATION_TOP,
                           relief=sg.RELIEF_GROOVE, border_width=5,
                           visible=True)
    return plan_header


def update_plan_header(window: sg.Window, desc: PlanDescription):
    '''Update the text values for the patient and plan info.
    Arguments:
        desc {PlanDescription} -- Summary data for the plan.
        window {} -- The GUI window containing the text.
    '''
    dose_text = desc.format_dose()
    id_text = desc.format_id()
    window['plan_title'].update(value=desc.plan_name)
    window['exported_text'].update(value=desc.export_date)
    window['course_text'].update(value=desc.course)
    window['dose_text'].update(value=dose_text)
    window['pt_name_text'].update(value=desc.patient_name)
    window['id_text'].update(value=id_text)
    window.refresh()


def plan_tree_data(plan_dict: OrderedDict)->sg.TreeData():
    '''Load tree with plan data.
    '''
    if plan_dict:
        patients = {plan.name_str() for plan in plan_dict.values()}
        patient_list = sorted(patients)
    else:
        patient_list = None
    treedata = sg.TreeData()
    if patient_list:
        for patient in patient_list:
            treedata.Insert('', patient, patient, [])
        for plan_info, plan in plan_dict.items():
            patient = plan.name_str()
            treedata.Insert(patient, plan_info, plan.plan_name, plan)
    return treedata


def update_plan_tree_data(window: sg.Window, plan_dict: OrderedDict):
    '''Update the Plan Selector tree with plan data.
    Arguments:
        desc {PlanDescription} -- Summary data for the plan.
        window {} -- The GUI window containing the text.
    '''
    treedata = plan_tree_data(plan_dict)
    window['Plan_tree'].update(treedata)
    window.refresh()


def plan_selector(plan_dict: OrderedDict):
    '''Plan Selection GUI
    '''
    treedata = plan_tree_data(plan_dict)
    column_settings = [
        ('File', False, 30),
        ('Type', False, 6),
        ('Patient Name', False, 12),
        ('Patient ID', False, 10),
        ('Plan Name', False, 6),
        ('Course', False, 5),
        ('Dose', True, 5),
        ('Fractions', False, 3),
        ('Exported On', True, 25)
        ]
    column_names = [col[0] for col in column_settings]
    show_column = [col[1] for col in column_settings]
    column_widths = [col[2] for col in column_settings]
    tree_settings = dict(key='Plan_tree',
                         headings=column_names,
                         visible_column_map=show_column,
                         col0_width=12,
                         col_widths=column_widths,
                         auto_size_columns=False,
                         justification='left',
                         num_rows=5,
                         font=('Verdana', 8, 'normal'),
                         show_expanded=True,
                         select_mode='browse',
                         enable_events=True)
    return sg.Tree(data=treedata, **tree_settings)


#%% Report Header
def create_report_header()->sg.Frame:
    template_layout = [
        [sg.Text('File:', size=(10,1)),
         sg.Text('', key='template_file', pad=(0, 5), size=(25,2))],
        [sg.Text('WorkSheet:', size=(10,1)),
         sg.Text('', key='template_sheet', pad=(0, 5), size=(25,1))],
        ]
    report_title = sg.Text(text='',
                           key='report_title',
                           font=('Calibri', 14, 'bold'),
                           size=(30,1),
                           pad=((0, 0), (4, 5)),
                           justification='center',
                           visible=True)
    report_desc = sg.Text(text='',
                          key='report_desc',
                          size=(30,2),
                          pad=((15, 0), (0, 20)),
                          visible=True)
    template_header = sg.Frame('Template:', template_layout,
                                   key='template_header',
                                   title_location=sg.TITLE_LOCATION_TOP_LEFT,
                                   font=('Calibri', 12),
                                   pad=(0, 0),
                                   element_justification='left')
    header_layout = [
        [report_title],
        [report_desc],
        [template_header]
        ]
    report_header = sg.Frame('Report', header_layout,
                             key='report_header',
                             title_location=sg.TITLE_LOCATION_TOP,
                             font=('Arial Black', 14, 'bold'),
                             element_justification='center',
                             relief=sg.RELIEF_GROOVE, border_width=5)
    return report_header


def update_report_header(window: sg.Window, report: Report):
    '''Update the text values for the report header.
    Arguments:
        window {} -- The GUI window containing the text.
        report {Report} -- The selected report.
    '''
    wrapped_desc = tw.fill(report.description, width=40)
    wrapped_file = tw.fill(report.template_file.name, width=30)
    wrapped_sheet = tw.fill(report.worksheet, width=30)
    window['report_title'].update(value=report.name)
    window['report_desc'].update(value=wrapped_desc)
    window['template_file'].update(value=wrapped_file)
    window['template_sheet'].update(value=wrapped_sheet)
    window.refresh()


#%% Actions
# Plan Status  Text Colour disabled
def make_report_selection_list(report_definitions):
    report_list = ['Select a Report']
    report_list += [str(ky) for ky in report_definitions.keys()]
    return report_list


def make_actions_column(report_definitions: Dict[str, Report]):
    '''Report Selection GUI
    '''
    button_style = dict(
        disabled=True,
        button_color=('red', 'white'),
        border_width=5,
        pad=(5, 5),
        size=(15, 1),
        auto_size_button=False,
        font=('Times New Roman', 12, 'normal')
        )
    report_list = make_report_selection_list(report_definitions)
    report_selector_box = sg.Combo(report_list,
                                    key='report_selector',
                                    default_value = 'Select a Report',
                                    pad=((10,10), (20,10)), size=(15, 5),
                                    enable_events=True,
                                    readonly=True)
    match_structures_button = sg.Button(key='match_structures',
                                        button_text='Match Structures',
                                        **button_style)
    generate_report_button = sg.Button(key='generate_report',
                                       button_text='Show Report',
                                       **button_style)
    exit_button = sg.Button(key='EXIT', button_text='Exit',
                            button_color=('black', 'grey'),
                            border_width=5, pad=(5, 5),
                            size=(15, 1), auto_size_button=False,
                            font=('Times New Roman', 12, 'normal'))
    actions = sg.Column([[report_selector_box],
                         [match_structures_button],
                         [generate_report_button],
                         [exit_button]
                         ])
    return actions


#%% Action Status Based Settings
def action_settings_config():
    element_settings =[
        ElementConfig(name='load_plan',
                        setting_type=ButtonSettings, settings = [
                            ('No Plan', ButtonSettings(
                                text='Select Plan',
                                button_color=('red', 'white'),
                                disabled=True)),
                            ('Selected', ButtonSettings(
                                text='Load Plan',
                                button_color=('black', 'blue'),
                                disabled=False)),
                            ('Loading', ButtonSettings(
                                text='Loading ...',
                                button_color=('red', 'yellow'),
                                disabled=True)),
                            ('Loaded', ButtonSettings(
                                text='Plan Loaded',
                                button_color=('black', 'green'),
                                disabled=False))]),
        ElementConfig(name='match_structures',
                        setting_type=ButtonSettings,
                        settings = [
                            ('Not Selected', ButtonSettings(
                                text='Select Report',
                                button_color=('red', 'white'),
                                disabled=True)),
                            ('Report Selected', ButtonSettings(
                                text='Report Selected',
                                button_color=('black', 'blue'),
                                disabled=True)),
                            ('Both Selected', ButtonSettings(
                                text='Match Structures',
                                button_color=('black', 'blue'),
                                disabled=False)),
                            ('Matching', ButtonSettings(
                                text='Matching ...',
                                button_color=('red', 'yellow'),
                                disabled=True)),
                            ('Matched', ButtonSettings(
                                text='Structured Matched',
                                button_color=('black', 'green'),
                                disabled=False))]),
        ElementConfig(name='generate_report',
                        setting_type=ButtonSettings,
                        settings = [
                            ('Not Matched', ButtonSettings(
                                text='Select Plan and Report',
                                button_color=('red', 'white'),
                                disabled=True)),
                            ('Matched', ButtonSettings(
                                text='Generate Report',
                                button_color=('black', 'blue'),
                                disabled=False)),
                            ('Generating', ButtonSettings(
                                text='Generating Report ...',
                                button_color=('red', 'yellow'),
                                disabled=True)),
                            ('Generated', ButtonSettings(
                                text='Report Generated',
                                button_color=('black', 'green'),
                                disabled=False))
                                ])
        ]
    status_groups = {'Nothing Selected': [
                        ('load_plan', 'No Plan'),
                        ('match_structures', 'Not Selected'),
                        ('generate_report', 'Not Matched')],
                    'Plan Selected': [
                        ('load_plan', 'Selected'),
                        ('match_structures', 'Not Selected'),
                        ('generate_report', 'Not Matched')],
                    'Report Selected': [
                        ('match_structures', 'Report Selected'),
                        ('generate_report', 'Not Matched')],
                    'Plan Loading': [
                        ('load_plan', 'Loading'),
                        ('match_structures', 'Not Selected'),
                        ('generate_report', 'Not Matched')],
                    'Plan Loaded': [
                        ('load_plan', 'Loaded'),
                        ('generate_report', 'Not Matched')],
                    'Invalid Plan': [
                        ('load_plan', 'No Plan')],
                    'Plan and Report Ready': [
                        ('load_plan', 'Loaded'),
                        ('match_structures', 'Both Selected'),
                        ('generate_report', 'Not Matched')],
                    'Matching': [
                        ('match_structures', 'Matching'),
                        ('generate_report', 'Not Matched')],
                    'Matched': [
                        ('match_structures', 'Matched'),
                        ('generate_report', 'Matched')],
                    'Generating': [
                        ('generate_report', 'Generating')],
                    'Generated': [
                        ('generate_report', 'Generated')]
                    }

    config_settings = WindowConfig(element_settings, status_groups)
    return config_settings


#%% Main Window
def create_main_window(plan_dict, report_definitions):
    plan_header = create_plan_header()
    report_header = create_report_header()
    plan_selection = plan_selector(plan_dict)
    report_actions = make_actions_column(report_definitions)
    layout = [[main_menu()],
              [plan_header, report_header, report_actions],
              [plan_selection]
              ]

    window = sg.Window('Plan Evaluation',
                       layout=layout,
                       resizable=True,
                       debugger_enabled=True,
                       finalize=True,
                       element_justification="left")
    return window


#%% Testing
def main():
    '''Define Folder Paths, load report and plan data.
    '''
    base_path = Path.cwd()
    icon_path = base_path / 'icons'
    icons = IconPaths(icon_path)
    #%% Load Config file and Report definitions
    config_file = 'PlanEvaluationConfig.xml'
    config = load_config(base_path, config_file)
    report_definitions = load_reports(config)
    plan_dict = find_plan_files(config)

    code_exceptions_def = config.find('LateralityCodeExceptions')
    plan_parameters = dict(
        default_units=get_default_units(config),
        laterality_exceptions=get_laterality_exceptions(code_exceptions_def),
        name='Plan'
        )



    #%% Create Main Window
    report = None
    active_plan = None
    selected_plan_desc = None
    history = MatchHistory()

    window = create_main_window(plan_dict, report_definitions)
    action_settings = action_settings_config()
    action_settings.set_status(window, 'Nothing Selected')

    while True:
        event, values = window.Read(timeout=2000)
        if event is None:
            break
        elif event in 'EXIT':
            window.close()
            break
        elif event == sg.TIMEOUT_KEY:
            continue
        elif event in 'Plan_tree':
            plan_desc = values['Plan_tree'][0]
            selected_plan_desc = plan_dict.get(plan_desc)
            if selected_plan_desc:
                update_plan_header(window, selected_plan_desc)
                action_settings.set_status(window, 'Plan Selected')
        elif event in 'report_selector':
            selected_report = values['report_selector']
            report = deepcopy(report_definitions.get(selected_report))
            if report:
                update_report_header(window, report)
                if active_plan:
                    action_settings.set_status(window, 'Plan and Report Ready')
                else:
                    action_settings.set_status(window, 'Report Selected')
        elif event in 'load_plan':
            action_settings.set_status(window, 'Plan Loading')
            active_plan = load_dvh(selected_plan_desc, **plan_parameters)
            if active_plan:
                if report is not None:
                    action_settings.set_status(window, 'Plan and Report Ready')
                else:
                    action_settings.set_status(window, 'Plan Loaded')
            else:
                action_settings.set_status(window, 'Invalid Plan')
        elif event in 'match_structures':
            action_settings.set_status(window, 'Matching')
            rerun_matching(report, active_plan, history)
            report = manual_match(report, active_plan, icons)
            action_settings.set_status(window, 'Matched')
        elif event in 'generate_report':
            action_settings.set_status(window, 'Generating')
            run_report(active_plan, report)
            action_settings.set_status(window, 'Generated')





if __name__ == '__main__':
    main()





