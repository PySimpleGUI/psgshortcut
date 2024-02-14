'''
Copyright 2021-2024 PySimpleSoft, Inc. and/or its licensors. All rights reserved.

Redistribution, modification, or any other use of PySimpleGUI or any portion thereof is subject
to the terms of the PySimpleGUI License Agreement available at https://eula.pysimplegui.com.

You may not redistribute, modify or otherwise use PySimpleGUI or its contents except pursuant
to the PySimpleGUI License Agreement.
'''

import PySimpleGUI as sg
from win32com.client import Dispatch
import os
import sys

version = '5.0.0'
__version__ = version.split()[0]


"""
    Demo Program = Make Windows Shortcut

    Creates a shortcut to your python file (or EXE file or anything that you want to make a shortcut to)

    Input just the .PY or .PYW file
    or...
    Optionally Add:
        - The interpreter to use
        - An icon for your shortcut
        - A new name for the shortcut

    Copyright 2021 PySimpleGUI
"""

'''
M""M                     dP            dP dP                   
M  M                     88            88 88                   
M  M 88d888b. .d8888b. d8888P .d8888b. 88 88 .d8888b. 88d888b. 
M  M 88'  `88 Y8ooooo.   88   88'  `88 88 88 88ooood8 88'  `88 
M  M 88    88       88   88   88.  .88 88 88 88.  ... 88       
M  M dP    dP `88888P'   dP   `88888P8 dP dP `88888P' dP       
MMMM
'''


def pip_install_thread(window, sp):
    window.write_event_value('-THREAD-', (sp, 'Install thread started'))
    for line in sp.stdout:
        oline = line.decode().rstrip()
        window.write_event_value('-THREAD-', (sp, oline))



def pip_install_latest():

    if 'PSG5_PAT' in os.environ:
        pip_command = f'-m pip install --upgrade --no-cache-dir "git+https://{os.environ["PSG5_PAT"]}@github.com/PySimpleGUI/PSG5_Deploy.git#egg=PySimpleGUI&subdirectory=pip_psg"'
    else:
        pip_command = '-m pip install --upgrade --no-cache-dir PySimpleGUI>=5'

    python_command = sys.executable  # always use the currently running interpreter to perform the pip!
    if 'pythonw' in python_command:
        python_command = python_command.replace('pythonw', 'python')

    layout = [[sg.Text('Installing PySimpleGUI', font='_ 14')],
              [sg.Multiline(s=(90, 15), k='-MLINE-', reroute_cprint=True, reroute_stdout=True, echo_stdout_stderr=True, write_only=True, expand_x=True, expand_y=True)],
              [sg.Push(), sg.Button('Downloading...', k='-EXIT-'), sg.Sizegrip()]]

    window = sg.Window('Pip Install PySimpleGUI Utilities', layout, finalize=True, keep_on_top=True, modal=True, disable_close=True, resizable=True)

    window.disable_debugger()

    sg.cprint('Installing with the Python interpreter =', python_command, c='white on purple')

    sp = sg.execute_command_subprocess(python_command, pip_command, pipe_output=True, wait=False)

    window.start_thread(lambda: pip_install_thread(window, sp), end_key='-THREAD DONE-')

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or (event == '-EXIT-' and window['-EXIT-'].ButtonText == 'Done'):
            break
        elif event == '-THREAD DONE-':
            sg.cprint('\n')
            show_package_version('PySimpleGUI')
            sg.cprint('Done Installing PySimpleGUI.  Click Done and the program will restart.', c='white on red', font='default 12 italic')
            window['-EXIT-'].update(text='Done', button_color='white on red')
        elif event == '-THREAD-':
            sg.cprint(values['-THREAD-'][1])

    window.close()

def suggest_upgrade_gui():
    layout = [[sg.Image(sg.EMOJI_BASE64_HAPPY_GASP), sg.Text(f'PySimpleGUI 5+ Required', font='_ 15 bold')],
              [sg.Text(f'PySimpleGUI 5+ required for this program to function correctly.')],
              [sg.Text(f'You are running PySimpleGUI {sg.version}')],
              [sg.Text('Would you like to upgrade to the latest version of PySimpleGUI now?')],
              [sg.Push(), sg.Button('Upgrade', size=8, k='-UPGRADE-'), sg.Button('Cancel', size=8)]]

    window = sg.Window(title=f'Newer version of PySimpleGUI required', layout=layout, font='_ 12')

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Cancel'):
            window.close()
            break
        elif event == '-UPGRADE-':
            window.close()
            pip_install_latest()
            sg.execute_command_subprocess(sys.executable, __file__, pipe_output=True, wait=False)
            break


def make_str_pre_38(package):
    return f"""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import pkg_resources
try:
    ver=pkg_resources.get_distribution("{package}").version.rstrip()
except:
    ver=' '
print(ver, end='')
"""

def make_str(package):
    return f"""
import importlib.metadata

try:
    ver = importlib.metadata.version("{package}")
except importlib.metadata.PackageNotFoundError:
    ver = ' '
print(ver, end='')
"""


def show_package_version(package):
    """
    Function that shows all versions of a package
    """
    interpreter = sg.execute_py_get_interpreter()
    sg.cprint(f'{package} upgraded to ', end='', c='red')
    # print(f'{interpreter}')
    if sys.version_info.major == 3 and sys.version_info.minor in (6, 7):  # if running Python version 3.6 or 3.7
        pstr = make_str_pre_38(package)
    else:
        pstr = make_str(package)
    temp_file = os.path.join(os.path.dirname(__file__), 'temp_py.py')
    with open(temp_file, 'w') as file:
        file.write(pstr)
    sg.execute_py_file(temp_file, interpreter_command=interpreter, pipe_output=True, wait=True)
    os.remove(temp_file)



def upgrade_check():
    if not sg.version.startswith('5'):
        suggest_upgrade_gui()
        exit()



'''
MM""""""""`M                                        
MM  mmmmmmmM                                        
M'      MMMM .d8888b. 88d888b.    88d888b. dP    dP 
MM  MMMMMMMM 88'  `88 88'  `88    88'  `88 88    88 
MM  MMMMMMMM 88.  .88 88          88.  .88 88.  .88 
MM  MMMMMMMM `88888P' dP          88Y888P' `8888P88 
MMMMMMMMMMMM                      88            .88 
                                  dP        d8888P  
.8888b oo dP                   
88   "    88                   
88aaa  dP 88 .d8888b. .d8888b. 
88     88 88 88ooood8 Y8ooooo. 
88     88 88 88.  ...       88 
dP     dP dP `88888P' `88888P'
'''


def create_shortcut_for_python_file(arguments='', target='', icon='', new_name=''):
    """
    Create a shortcut for a given target filename
    :param arguments str: full arguments and filename to make link to
    :param target str: what to launch (e.g. python)
    :param icon str: .ICO file
    :return: filename of the created shortcut file
    :rtype: str
    """
    filename, ext = os.path.splitext(arguments)
    working_dir = os.path.dirname(target)
    shell = Dispatch('WScript.Shell')
    if new_name:
        shortcut_filename = new_name + ".lnk"
    else:
        shortcut_filename = filename + ".lnk"
    shortcut_filename = os.path.join(os.path.dirname(arguments), shortcut_filename)
    shortcut = shell.CreateShortCut(f'{shortcut_filename}')
    shortcut.Targetpath = str(target)
    shortcut.Arguments = f'"{arguments}"'
    shortcut.WorkingDirectory = working_dir
    if icon == '':
        pass
    else:
        shortcut.IconLocation = icon
    shortcut.save()
    return shortcut_filename


'''
MM""""""""`M                                 dP   dP                         
MM  mmmmmmmM                                 88   88                         
M'      MMMM .d8888b. 88d888b.    .d8888b. d8888P 88d888b. .d8888b. 88d888b. 
MM  MMMMMMMM 88'  `88 88'  `88    88'  `88   88   88'  `88 88ooood8 88'  `88 
MM  MMMMMMMM 88.  .88 88          88.  .88   88   88    88 88.  ... 88       
MM  MMMMMMMM `88888P' dP          `88888P'   dP   dP    dP `88888P' dP       
MMMMMMMMMMMM                                                                 

.8888b oo dP                   
88   "    88                   
88aaa  dP 88 .d8888b. .d8888b. 
88     88 88 88ooood8 Y8ooooo. 
88     88 88 88.  ...       88 
dP     dP dP `88888P' `88888P'
'''


def create_shortcut_exe_or_other(arguments='', target='', icon='', new_name=''):
    """
    Create a shortcut for a given target filename
    :param arguments str: full arguments and filename to make link to
    :param target str: what to launch (e.g. python)
    :param icon str: .ICO file
    :return: filename of the created shortcut file
    :rtype: str
    """
    filename, ext = os.path.splitext(target)
    working_dir = os.path.dirname(target)
    shell = Dispatch('WScript.Shell')
    if new_name:
        shortcut_filename = new_name + ".lnk"
    else:
        shortcut_filename = filename + ".lnk"
    shortcut_filename = os.path.join(os.path.dirname(target), shortcut_filename)
    shortcut = shell.CreateShortCut(shortcut_filename)
    shortcut.Targetpath = str(target)
    shortcut.Arguments = f'"{arguments}"'
    shortcut.WorkingDirectory = working_dir
    if icon == '':
        pass
    else:
        shortcut.IconLocation = icon
    shortcut.save()
    return shortcut_filename


def shortcut_exists(target, new_name=''):
    filename, ext = os.path.splitext(target)
    filename = new_name if new_name != '' else filename
    shortcut_filename = filename + ".lnk"
    shortcut_filename = os.path.join(os.path.dirname(target), shortcut_filename)
    print('looking for exists filename', shortcut_filename)
    return os.path.exists(shortcut_filename)


def shortcut_delete(target, new_name=''):
    filename, ext = os.path.splitext(target)
    filename = new_name if new_name != '' else filename
    shortcut_filename = filename + ".lnk"
    shortcut_filename = os.path.join(os.path.dirname(target), shortcut_filename)
    os.remove(shortcut_filename)


'''
                    oo          

88d8b.d8b. .d8888b. dP 88d888b. 
88'`88'`88 88'  `88 88 88'  `88 
88  88  88 88.  .88 88 88    88 
dP  dP  dP `88888P8 dP dP    dP
'''


def main():

    sg.user_settings_filename(filename='psgshortcut.json')
    upgrade_check()

    main_icon = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACWElEQVRYR7WXO2tVQRSFv7QWRmMIIggKAUW0SKNFGvMjFLsUooWPNIqVoqI2ShpFQbCwFNME/QMWggqCj0pQJIiSIkSSQgVRkHWZCTs7Z85rxg2Xe8+ZuXuts2ftNXOG+D+xE9gL7AH+AB+Aj8A3DzdUGH8CuAAcS+R9CpwLZAZTShK4HMA3tXioK8DVkgQErqQ2VoEvwF9gF7DFjYvorxIVqAJfe0ID+hg4Yq5vABdzCbQFj7h+/lgOga7gkcQKMBwupvoS6Asu3PfAgUDgdB8COeDZBMaBV8CIEVOV4Oo6MWsJbgNnM8CzRDgKLBnwOeBoC9OJU24B5838O8BMFw1MAs9DApVxq0n2ANgGvI0O54gJ7Iy59x04BHzqQuAkcD8kEZB8X3EKuGuS7wAWzfU1GY4j1MuKUwT0JC8NwKwptcS6nALX/VQFZJn7gHfAfEhQtwRenGNBL/L7H3WirSJglboA7A4JvAgHIjLJ17UX8CyMxYd5AzzxovUEfJt8BXS4iCENaCliTBmgdQ4H3GvTIZZAlcNdAq6bRCKjLTbGCUAdoMgiUOVwKq/K7ENEDwKfnSmllqC2ELECXkQyDKm5bWxwOGdayTwikOtwHtyLs7ECde3VVAEPvuZwTX+M46pAymCacuRuy4P8fQkUAY8Eui5BMfBIoIsIi4JHAvp+CEybRW9zrNb0rqehDbqKPrAZ0IuEDdnwi7CZHA4vF3Y8G9xWQL+rylvVCT+Bm4mDR1PnJCsQB7YH7z+eyPQogGtnKxKp88B+QN2hz++w470Or9lFgGOSf3MNjp/Wcz63AAAAAElFTkSuQmCC'
    sg.set_options(keep_on_top=True)
    python_command = sg.execute_py_get_interpreter()
    if not python_command:
        python_command = sys.executable
    sg.theme('dark grey 13')
    txt_size = 45

    layout = [[sg.Text('Create Windows shortcut (Click Create Shortcut or return key to start)', font='_ 15')],
              [sg.T('Python (.PY/.PYW), EXE or other file - (absolute path)', s=txt_size), sg.Input(key='-IN FILE-'),
               sg.FileBrowse(file_types=(("Python Files", "*.py *.pyw *.PY *.PYW"),), )],
              [sg.T('Icon file (optional)', s=txt_size), sg.Input(key='-ICON-'), sg.FileBrowse(file_types=(("Icon Files", "*.ico *.ICO",),), )],
              [sg.T('Shortcut Name (optional)', s=txt_size), sg.Input(key='-SHORTCUT NAME-')],
              [sg.T('Python Command (optional, required for pinning to taskbar)', s=txt_size), sg.Input(python_command, key='-PYTHON COMMAND-')],
              [sg.T('Arguments (optional)', s=txt_size), sg.Input(key='-ARGUMENTS-')],
              [sg.Button('Create Shortcut', bind_return_key=True), sg.Button('Exit')]]

    window = sg.Window('Create Windows Shortcut', layout, icon=main_icon, right_click_menu=['', ['Edit Me', 'Version', 'File Location', 'Exit']])

    while True:
        event, values = window.read()
        # print(event, values)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'Create Shortcut':
            infile = values['-IN FILE-'].lower()
            py_cmd = values['-PYTHON COMMAND-']
            if shortcut_exists(infile, values['-SHORTCUT NAME-']):
                if sg.popup_yes_no('The shortcut already exists.  Do you want to overwrite it?') == 'Yes':
                    shortcut_delete(infile, values['-SHORTCUT NAME-'])
                else:
                    continue
            try:
                if '.pyw' in infile or '.py' in infile:
                    if values['-PYTHON COMMAND-']:
                        if '.pyw' in values['-IN FILE-'].lower():  # if a .pyw file specified, use pythonw to launch it
                            if 'pythonw' not in py_cmd:
                                py_cmd = py_cmd.replace('python.exe', 'pythonw.exe')
                    if py_cmd:
                        shortcut_name = create_shortcut_for_python_file(target=fr'{py_cmd}', arguments=values['-IN FILE-'], icon=values['-ICON-'],
                                                                        new_name=values['-SHORTCUT NAME-'])
                    else:
                        shortcut_name = create_shortcut_exe_or_other(target=values['-IN FILE-'], icon=values['-ICON-'], new_name=values['-SHORTCUT NAME-'])
                else:
                    shortcut_name = create_shortcut_exe_or_other(target=infile, arguments=values['-ARGUMENTS-'], icon=values['-ICON-'],
                                                                 new_name=values['-SHORTCUT NAME-'])
                choice = sg.popup('Done!', 'Created shortcut:', shortcut_name, custom_text=('Take me there', 'Close'))
                if choice == 'Take me there':
                    sg.execute_command_subprocess(r'explorer.exe', os.path.dirname(shortcut_name))
            except Exception as e:
                sg.popup_error('Error encountered', e)
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Version':
            sg.popup_scrolled(sg.get_versions(), keep_on_top=True)
        elif event == 'File Location':
            sg.popup_scrolled('This Python file is:', __file__)
    window.close()


if __name__ == '__main__':
    main()
