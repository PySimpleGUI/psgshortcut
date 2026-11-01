'''
Copyright 2021-2026 PySimpleGUI. All rights reserved.

Licensed under LGPL3
'''

import PySimpleGUI as sg
import os
import sys
import re
import io
import base64
import hashlib
import subprocess

try:                                                # Windows only - pywin32 writes the .lnk files and sets their taskbar App ID
    import pythoncom
    from win32com.shell import shell as win_shell, shellcon
    from win32com.propsys import propsys, pscon
    HAVE_WIN32 = True
except ImportError:
    HAVE_WIN32 = False
try:
    import psgdnd                                   # drag and drop from Explorer (optional:  python -m pip install psgdnd)
except ImportError:
    psgdnd = None
try:
    from PIL import Image                           # converts the icons found in programs into .ico files (optional:  python -m pip install pillow)
except ImportError:
    Image = None

version = '6.1'
__version__ = version.split()[0]

"""
    psgshortcut - Make Windows Shortcuts

    Creates a shortcut to your Python file (or EXE file or anything else you want a shortcut to).

    * Drop a .py / .pyw / .exe file anywhere on the window (or Browse to it)
    * The icon embedded in a PySimpleGUI program (ICON = b'iVBOR...') is found automatically and turned into the shortcut's .ico
    * Choose where the shortcut goes - next to the program, Desktop, Start Menu (for pinning to the taskbar) or any folder
    * The .lnk carries the program's Windows taskbar App ID, so a pinned program's window groups under its own pinned icon
    * One click makes a shortcut to psgshortcut itself

    Changelog since last major release
        6.0     16-Apr-2026      Moved to LGPL3 license
        6.1     31-Oct-2026      Claude: Rework.  HarborMist dark theme and new layout, new program icon, drag and drop of files onto the window
                                 (psgdnd), automatic extraction of the base64 icon found in PySimpleGUI programs (converted to .ico with Pillow),
                                 PySimpleGUI's default icon used when a program has none, icon preview, destination choice (target folder /
                                 Desktop / Start Menu / custom), shortcut description, auto python <-> pythonw for .py/.pyw, shortcut name
                                 auto-filled, "Shortcut to this program" button replaces the 7-step README procedure, Settings window,
                                 command-line argument pre-fills the target, Escape closes, crash reporting with popup_error_with_traceback.
                                 Taskbar pinning: .lnk is written with IShellLink + IPropertyStore (not WScript.Shell) so it carries the same
                                 System.AppUserModel.ID that PySimpleGUI 6.3.17+ gives the running program ('PySimpleGUI.App.' + md5 of the
                                 script path as passed on the command line, or the program's own set_options(win_app_id=...)) - the running
                                 window groups under its pinned icon.  Programs run with an older PySimpleGUI get its fixed ID instead (the
                                 interpreter the shortcut uses is asked for its PySimpleGUI version).  Extracted .ico files are saved next to
                                 the script by default.  The icon search only counts icon= keyword arguments (a plain  icon = x  assignment
                                 is not the program's icon), skips blank / solid placeholder images and never picks an image under 32 px
                                 (button glyphs, tray icons) - a program with only those gets the PySimpleGUI default icon.  SHChangeNotify
                                 after writing the .lnk; a changed icon is written as <name>_<hash>.ico instead of over the old file, because
                                 Explorer's icon cache keeps showing the old picture for a path it has already seen
"""

# --------------------------------------------------------------------------------------------------------------------------------------------
#  Theme - HarborMist (one of the custom dark themes) and the accent colors used by the layout
# --------------------------------------------------------------------------------------------------------------------------------------------
THEME = 'HarborMist'
HARBOR_MIST = {'BACKGROUND': '#121826', 'TEXT': '#cbd5e0', 'INPUT': '#1e2740', 'TEXT_INPUT': '#dfe6ee', 'SCROLL': '#1e2740',
               'BUTTON': ('#ffffff', '#40628c'), 'PROGRESS': ('#6488b3', '#1e2740'), 'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}
BG = '#121826'                  # window background
PANEL = '#1e2740'               # cards / drop zone / status bar
ACCENT = '#40628c'              # primary button, labels
ACCENT_LIGHT = '#6488b3'        # highlights, header title
MUTED = '#8a9bb5'               # hints
C_OK = '#5fc38f'                # status: success
C_WARN = '#e0b45a'              # status: warning
C_ERR = '#e07a7a'               # status: error

# --------------------------------------------------------------------------------------------------------------------------------------------
#  Keys
# --------------------------------------------------------------------------------------------------------------------------------------------
K_TARGET = '-TARGET-'
K_TARGET_BROWSE = '-TARGET BROWSE-'
K_NAME = '-NAME-'
K_DEST = '-DEST-'
K_CUSTOM_DIR = '-CUSTOM DIR-'
K_CUSTOM_BROWSE = '-CUSTOM BROWSE-'
K_ICON_AUTO = '-ICON AUTO-'
K_ICON_FILE_SRC = '-ICON FILE SRC-'
K_ICON_NONE = '-ICON NONE-'
K_ICON_FILE = '-ICON FILE-'
K_ICON_BROWSE = '-ICON BROWSE-'
K_PYTHON = '-PYTHON-'
K_PYTHON_BROWSE = '-PYTHON BROWSE-'
K_PYTHONW = '-PYTHONW-'
K_ARGS = '-ARGS-'
K_DESC = '-DESC-'
K_PREVIEW = '-PREVIEW-'
K_PREVIEW_NOTE = '-PREVIEW NOTE-'
K_DROPZONE = '-DROPZONE-'
K_STATUS = '-STATUS-'
K_CREATE = '-CREATE-'
K_SELF = '-SELF-'
K_CLEAR = '-CLEAR-'
K_ESC = '-ESC-'
# settings window
K_SET_ICON_DIR = '-SET ICON DIR-'
K_SET_DEST = '-SET DEST-'
K_SET_ON_TOP = '-SET ON TOP-'

DEST_SAME = 'Same folder as the target'
DEST_DESKTOP = 'Desktop'
DEST_START = 'Start Menu  (right-click it there to pin to the taskbar)'
DEST_CUSTOM = 'Custom folder...'
DESTINATIONS = [DEST_SAME, DEST_DESKTOP, DEST_START, DEST_CUSTOM]

ICON_DIR_CENTRAL = 'One central folder (%LOCALAPPDATA%\\psgshortcut\\icons)'
ICON_DIR_NEXT = 'Next to the target program'
ICON_DIR_CHOICES = [ICON_DIR_NEXT, ICON_DIR_CENTRAL]
ICON_DIR_DEFAULT = ICON_DIR_NEXT
APP_ID_PREFIX = 'PySimpleGUI.App.'          # PySimpleGUI 6.3.17+ : taskbar App ID = prefix + md5(abspath of the main script)
APP_ID_LEGACY = 'mycompany.myproduct.subproduct.version'   # every PySimpleGUI program before 6.3.17 used this one fixed ID
APP_ID_NEW_SCHEME_VERSION = (6, 3, 17)

SETTING_PYTHON = '-python command-'
SETTING_DEST = '-destination-'
SETTING_CUSTOM_DIR = '-custom dir-'
SETTING_ICON_DIR = '-icon dir mode-'
SETTING_ON_TOP = '-keep on top-'
SETTING_PYTHONW = '-auto pythonw-'

PYTHON_EXTS = ('.py', '.pyw')
IMAGE_EXTS = ('.ico', '.png', '.gif', '.jpg', '.jpeg', '.bmp', '.webp')

# The program's own icon.  A PySimpleGUI program keeps its icon as a base64 PNG in a constant like this one - psgshortcut finds it
# in any program dropped on the window and uses it for the shortcut.  (Yes, it finds this one too - try "Shortcut to this program")
ICON = b'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'

# --------------------------------------------------------------------------------------------------------------------------------------------
#  Icon extraction & conversion
# --------------------------------------------------------------------------------------------------------------------------------------------
_B64_ASSIGN = re.compile(r'''(?m)^[ \t]*([A-Za-z_]\w*)\s*=\s*b?(['"])((?:iVBORw0KGgo|R0lGOD)[A-Za-z0-9+/=\s]*?)\2''')
_ICON_KWARG = re.compile(r'''[(,]\s*icon\s*=\s*([A-Za-z_][\w.]*)''')                 # icon=NAME as a keyword argument only (not  icon = x  assignments)
_ICON_GLOBAL = re.compile(r'''(?:set_options\([^)]*?\bicon\s*=\s*|set_global_icon\(\s*)([A-Za-z_][\w.]*)''', re.DOTALL)
_ICON_PATH = re.compile(r'''[(,]\s*icon\s*=\s*[rR]?(['"])([^'"\n]+?\.(?:ico|png|gif))\1''', re.IGNORECASE)
_APP_ID_LITERAL = re.compile(r'''win_app_id\s*=\s*[rRfF]?(['"])([^'"\n]+)\1''')
_APP_ID_VARIABLE = re.compile(r'''win_app_id\s*=\s*([A-Za-z_]\w*)\s*[,)]''')


_psg_version_cache = {}


def psg_version_of(python_cmd):
    """Ask an interpreter which PySimpleGUI it has -> (6, 3, 19) or None.  Cached per interpreter; runs hidden (no console flash)."""
    if python_cmd in _psg_version_cache:
        return _psg_version_cache[python_cmd]
    result = None
    try:
        folder, exe = os.path.split(python_cmd)
        console_python = os.path.join(folder, exe.lower().replace('pythonw', 'python'))      # pythonw.exe has no stdout - use python.exe beside it
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        out = subprocess.run([console_python, '-c', 'import PySimpleGUI as sg; print(sg.version)'], capture_output=True, text=True, timeout=30, creationflags=flags)
        if out.returncode == 0:
            result = tuple(int(p) for p in re.findall(r'\d+', out.stdout.split()[0])[:3])
    except Exception:
        result = None
    _psg_version_cache[python_cmd] = result
    return result


def taskbar_app_id(script_path_as_passed, python_cmd):
    """
    The Windows taskbar App ID the program will have when it runs, so the .lnk can carry the same one and the running window groups under its pin.
      * PySimpleGUI 6.3.17+ : 'PySimpleGUI.App.' + md5(os.path.abspath(sys.modules['__main__'].__file__)).  __file__ is the path exactly as the
        command line passed it, so the md5 is taken of the exact (case-sensitive) string the shortcut uses
      * older PySimpleGUI : the one fixed ID 'mycompany.myproduct.subproduct.version' - decided by asking the interpreter the shortcut will use
      * a program that calls sg.set_options(win_app_id='...') (literal, or a simple NAME = '...' variable) uses that instead
      * not a PySimpleGUI program : no ID - Windows groups by the launcher exe like it always did
    :return: (app_id or '', note)
    """
    try:
        with open(script_path_as_passed, 'r', encoding='utf-8', errors='replace') as f:
            src = f.read()
    except Exception:
        src = ''
    if 'PySimpleGUI' not in src:
        return '', 'not a PySimpleGUI program - no App ID set'
    m = _APP_ID_LITERAL.search(src)
    if m:
        return m.group(2), 'set_options(win_app_id=...) in the program'
    m = _APP_ID_VARIABLE.search(src)
    if m:
        v = re.search(r'''(?m)^\s*%s\s*=\s*[rR]?(['"])([^'"\n]+)\1''' % re.escape(m.group(1)), src)
        if v:
            return v.group(2), f'set_options(win_app_id={m.group(1)}) in the program'
    ver = psg_version_of(python_cmd)
    if ver is None:
        return APP_ID_LEGACY, 'could not read the PySimpleGUI version of that interpreter - used the pre-6.3.17 ID'
    if ver < APP_ID_NEW_SCHEME_VERSION:
        return APP_ID_LEGACY, f'PySimpleGUI {".".join(map(str, ver))} - the fixed pre-6.3.17 ID'
    return APP_ID_PREFIX + hashlib.md5(os.path.abspath(script_path_as_passed).encode('utf-8')).hexdigest(), f'PySimpleGUI {".".join(map(str, ver))} - md5 of the script path'


def default_psg_icon():
    """The icon PySimpleGUI puts on windows that have none - base64 bytes"""
    data = sg.DEFAULT_BASE64_ICON
    return data if isinstance(data, bytes) else data.encode()


MIN_ICON_PX = 32                                    # images smaller than this are button glyphs / tray icons, never a shortcut icon


def image_size(b64):
    """(width, height) of a base64 image, (0, 0) when it cannot be decoded.  Without Pillow every image counts as big enough."""
    if Image is None:
        return (MIN_ICON_PX, MIN_ICON_PX)
    try:
        with Image.open(io.BytesIO(base64.b64decode(b64))) as im:
            return im.size
    except Exception:
        return (0, 0)


def looks_blank(b64):
    """True when the image is one solid colour / fully transparent (a placeholder, not an icon).  Without Pillow nothing is judged blank."""
    if Image is None:
        return False
    try:
        with Image.open(io.BytesIO(base64.b64decode(b64))) as im:
            im = im.convert('RGBA')
            if im.getextrema()[3][1] == 0:                                      # every pixel transparent
                return True
            return all(lo == hi for lo, hi in im.getextrema())                 # every channel constant -> one solid colour
    except Exception:
        return True                                                             # not decodable -> not usable as an icon either


def extract_icon_from_source(path):
    """
    Look through a Python source file for the icon a PySimpleGUI program uses.
      1. the icon the program explicitly passes:  set_options(icon=X) / set_global_icon(X), then Window(..., icon=X)  (names with "icon" first)
      2. an icon file next to the program, or PySimpleGUI's default when the program asks for it
      3. otherwise the best base64 image in the file:  at least MIN_ICON_PX wide, biggest first, "icon" in the name as tie-breaker
         (a 16-24 px button glyph or tray icon is never picked, however it is named - PySimpleGUI's default is used instead)
    Blank placeholder images are skipped everywhere.
    :return: (base64 bytes or None, note explaining what was found)
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            src = f.read()
    except Exception as e:
        return None, f'Could not read the file: {e}'
    found = {m.group(1): m.group(3) for m in _B64_ASSIGN.finditer(src) if not looks_blank(m.group(3))}
    strip = lambda names: [n.split('.')[-1] for n in names]
    globals_ = strip(_ICON_GLOBAL.findall(src))
    kwargs = strip(_ICON_KWARG.findall(src))
    for n in globals_:
        if n in found:
            return found[n].encode(), f'Found icon "{n}" set for the whole program'
    used = [n for n in kwargs if n in found]
    if used:
        n = sorted(used, key=lambda n: 'icon' not in n.lower())[0]
        return found[n].encode(), f'Found icon "{n}" used by the program'
    m = _ICON_PATH.search(src)                                                  # icon='some_file.ico' next to the program
    if m:
        icon_path = m.group(2) if os.path.isabs(m.group(2)) else os.path.join(os.path.dirname(path), m.group(2))
        if os.path.isfile(icon_path):
            with open(icon_path, 'rb') as f:
                raw = f.read()
            return base64.b64encode(image_to_png(raw)), f'Program uses icon file {os.path.basename(icon_path)}'
    if 'DEFAULT_BASE64_ICON' in globals_ + kwargs:                              # explicitly uses PySimpleGUI's default
        return default_psg_icon(), 'Program uses the PySimpleGUI default icon'
    big = [(max(image_size(b64)), 'icon' in n.lower(), n) for n, b64 in found.items() if max(image_size(b64)) >= MIN_ICON_PX]
    if big:
        side, _, n = sorted(big, reverse=True)[0]
        return found[n].encode(), f'Using base64 image "{n}" ({side} px) found in the program'
    if found:
        return default_psg_icon(), 'Only small images in the program (buttons / tray) - the PySimpleGUI default icon will be used'
    return None, 'No icon found in the program'


def image_to_png(raw):
    """Any image bytes (ico, gif, jpg...) -> PNG bytes.  Needs Pillow for anything other than PNG."""
    if raw[:8] == b'\x89PNG\r\n\x1a\n' or Image is None:
        return raw
    with Image.open(io.BytesIO(raw)) as im:
        if im.format == 'ICO':
            im.size = max(im.info.get('sizes', {im.size}))                      # pick the biggest frame in the .ico
            im.load()
        buf = io.BytesIO()
        im.convert('RGBA').save(buf, format='PNG')
        return buf.getvalue()


def png_resize(png_bytes, size):
    """PNG bytes -> PNG bytes fitted into a size x size square (for the on-screen preview).  Returns the input unchanged without Pillow."""
    if Image is None:
        return png_bytes
    with Image.open(io.BytesIO(png_bytes)) as im:
        im = im.convert('RGBA')
        im.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
        buf = io.BytesIO()
        canvas.save(buf, format='PNG')
        return buf.getvalue()


def write_ico(png_bytes, ico_path):
    """Write a multi-size .ico from PNG bytes.  Sizes never exceed the source so nothing is blurred by upscaling."""
    if Image is None:
        raise RuntimeError('Pillow is needed to make .ico files.  Install it with:   python -m pip install pillow')
    with Image.open(io.BytesIO(png_bytes)) as im:
        im = im.convert('RGBA')
        side = max(im.size)
        canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
        canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        if side > 256:
            canvas = canvas.resize((256, 256), Image.LANCZOS)
            side = 256
        sizes = sorted({s for s in (16, 24, 32, 48, 64, 128, 256) if s <= side} | {side})
        os.makedirs(os.path.dirname(ico_path), exist_ok=True)
        buf = io.BytesIO()
        canvas.save(buf, format='ICO', sizes=[(s, s) for s in sizes])
        new = buf.getvalue()
    if os.path.isfile(ico_path):
        with open(ico_path, 'rb') as f:
            old = f.read()
        if old == new:
            return ico_path                                                     # unchanged - keep the file Explorer already knows
        # A different picture under the SAME path would keep showing the old one from Explorer's icon cache (even after ie4uinit), so the
        # changed icon gets a new name: <stem>_<6 hex of its content>.ico
        root, ext = os.path.splitext(ico_path)
        ico_path = f'{root}_{hashlib.md5(new).hexdigest()[:6]}{ext}'
        flush_icon_cache()
    with open(ico_path, 'wb') as f:
        f.write(new)
    return ico_path


def flush_icon_cache():
    """Make Explorer drop its icon cache (Windows 10/11).  Harmless if the tool is missing."""
    if sys.platform != 'win32':
        return
    try:
        subprocess.Popen(['ie4uinit.exe', '-show'], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except Exception:
        pass


def icon_folder(target):
    """Where extracted .ico files are stored, per the Settings choice"""
    if sg.user_settings_get_entry(SETTING_ICON_DIR, ICON_DIR_DEFAULT) == ICON_DIR_NEXT and target:
        return os.path.dirname(os.path.abspath(target))
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'psgshortcut', 'icons')


def ico_path_for(target):
    """Name for the .ico made from a program's icon.  Central folder gets a short hash so two programs with the same name don't collide."""
    stem = os.path.splitext(os.path.basename(target))[0]
    folder = icon_folder(target)
    if folder == os.path.dirname(os.path.abspath(target)):
        return os.path.join(folder, stem + '.ico')
    tag = hashlib.md5(os.path.abspath(target).lower().encode()).hexdigest()[:6]
    return os.path.join(folder, f'{stem}_{tag}.ico')


# --------------------------------------------------------------------------------------------------------------------------------------------
#  Shortcut creation (Windows)
# --------------------------------------------------------------------------------------------------------------------------------------------
def need_win32():
    if not HAVE_WIN32:
        raise RuntimeError('Making shortcuts needs Windows and pywin32.  Install pywin32 with:   python -m pip install pywin32')


def special_folder(name):
    """'Desktop' or 'Programs' (Start Menu\\Programs) - asks Windows so OneDrive-redirected folders are right"""
    need_win32()
    csidl = shellcon.CSIDL_DESKTOPDIRECTORY if name == 'Desktop' else shellcon.CSIDL_PROGRAMS
    return win_shell.SHGetFolderPath(0, csidl, None, 0)


def destination_folder(choice, target, custom_dir):
    if choice == DEST_DESKTOP:
        return special_folder('Desktop')
    if choice == DEST_START:
        return special_folder('Programs')
    if choice == DEST_CUSTOM:
        return custom_dir.strip()
    return os.path.dirname(os.path.abspath(target))


def create_shortcut(lnk_path, target, arguments='', working_dir='', icon='', description='', app_id=''):
    """
    Write a .lnk file with IShellLink, and stamp it with a taskbar App ID through IPropertyStore (WScript.Shell cannot do that).
    :param lnk_path:    full path of the shortcut to create
    :param target:      what the shortcut launches (pythonw.exe for Python programs, the file itself for EXEs and others)
    :param arguments:   command line arguments (the .py file, plus any extra arguments)
    :param working_dir: folder the program starts in
    :param icon:        .ico file to use ('' = let Windows pick the target's own icon)
    :param description: tooltip shown when hovering the shortcut
    :param app_id:      System.AppUserModel.ID - must equal the ID the running program sets, so the window groups under the pinned icon
    :return:            lnk_path
    """
    need_win32()
    link = pythoncom.CoCreateInstance(win_shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, win_shell.IID_IShellLink)
    link.SetPath(str(target))
    link.SetArguments(arguments)
    link.SetWorkingDirectory(working_dir)
    if icon:
        link.SetIconLocation(icon, 0)
    if description:
        link.SetDescription(description)
    if app_id:
        store = link.QueryInterface(propsys.IID_IPropertyStore)
        store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(app_id))
        store.Commit()
    link.QueryInterface(pythoncom.IID_IPersistFile).Save(lnk_path, 0)
    try:                                                                        # tell Explorer the icon changed so a re-made .ico is not shown from its icon cache
        win_shell.SHChangeNotify(shellcon.SHCNE_UPDATEITEM, shellcon.SHCNF_PATH, lnk_path, None)
        if icon:
            win_shell.SHChangeNotify(shellcon.SHCNE_UPDATEITEM, shellcon.SHCNF_PATH, icon, None)
        win_shell.SHChangeNotify(shellcon.SHCNE_ASSOCCHANGED, shellcon.SHCNF_IDLIST, None, None)
    except Exception:
        pass
    return lnk_path


def matching_python(target, python_cmd):
    """.pyw -> pythonw.exe (no console),  .py -> python.exe.  Only the exe name is swapped; the folder is kept."""
    folder, exe = os.path.split(python_cmd)
    low = exe.lower()
    wanted = None
    if target.lower().endswith('.pyw') and low in ('python.exe', 'python'):
        wanted = 'pythonw.exe'
    elif target.lower().endswith('.py') and low in ('pythonw.exe', 'pythonw'):
        wanted = 'python.exe'
    if wanted and (not folder or os.path.isfile(os.path.join(folder, wanted))):
        return os.path.join(folder, wanted)
    return python_cmd


def default_python():
    cmd = sg.user_settings_get_entry(SETTING_PYTHON, '') or sg.execute_py_get_interpreter() or sys.executable
    return cmd


# --------------------------------------------------------------------------------------------------------------------------------------------
#  GUI helpers
# --------------------------------------------------------------------------------------------------------------------------------------------
VALUE_KEYS = (K_TARGET, K_NAME, K_DEST, K_CUSTOM_DIR, K_ICON_AUTO, K_ICON_FILE_SRC, K_ICON_NONE, K_ICON_FILE, K_PYTHON, K_PYTHONW, K_ARGS, K_DESC)


def current_values(window):
    """The values dict as it is right now (after update() calls), without going through window.read()"""
    return {k: window[k].get() for k in VALUE_KEYS}


def status(window, text, color=None):
    window[K_STATUS].update(text, text_color=color or sg.theme_text_color())


def set_preview(window, png_b64, note, note_color=None):
    """Show the icon (or the empty slot) in the preview card"""
    if png_b64:
        try:
            png = image_to_png(base64.b64decode(png_b64))
            window[K_PREVIEW].update(data=png_resize(png, 128))
        except Exception as e:
            window[K_PREVIEW].update(data=None)
            note, note_color = f'Icon could not be decoded: {e}', C_ERR
    else:
        window[K_PREVIEW].update(data=None)
    window[K_PREVIEW_NOTE].update(note, text_color=note_color or MUTED)


def icon_source(values):
    return 'auto' if values[K_ICON_AUTO] else 'file' if values[K_ICON_FILE_SRC] else 'none'


def refresh_icon(window, values, state):
    """Work out which icon the shortcut will get and show it"""
    target = values[K_TARGET].strip()
    src = icon_source(values)
    state['icon_b64'] = None
    if src == 'none':
        set_preview(window, None, 'No icon will be set.  Windows uses the default icon for the launcher (python / the EXE itself)')
    elif src == 'file':
        path = values[K_ICON_FILE].strip()
        if path and os.path.isfile(path):
            with open(path, 'rb') as f:
                state['icon_b64'] = base64.b64encode(f.read())
            note = os.path.basename(path) + ('' if path.lower().endswith('.ico') else '  (converted to .ico when the shortcut is made)')
            set_preview(window, state['icon_b64'], note)
        else:
            set_preview(window, None, 'Choose an icon file (.ico, .png, .gif, .jpg...) or drop one on the Icon field')
    elif not target:
        set_preview(window, None, 'Drop a program on the window and its icon shows up here')
    elif target.lower().endswith(PYTHON_EXTS):
        if os.path.isfile(target):
            b64, note = extract_icon_from_source(target)
            if b64 is None:
                b64, note = default_psg_icon(), 'No icon in the program - the PySimpleGUI default icon will be used'
                set_preview(window, b64, note, C_WARN)
            else:
                set_preview(window, b64, note, C_OK)
            state['icon_b64'] = b64
        else:
            set_preview(window, None, 'Target file not found', C_ERR)
    elif target.lower().endswith(IMAGE_EXTS):
        set_preview(window, None, "That's an image - drop it on the Icon field instead, and a program here")
    else:
        set_preview(window, None, "Windows will show the file's own icon (EXE, document...).  Pick 'Icon file' to use another one")


def target_changed(window, values, state):
    """A new target was dropped / browsed / typed:  name, python command and icon follow it"""
    target = values[K_TARGET].strip().strip('"')
    if target != values[K_TARGET]:
        window[K_TARGET].update(target)
    stem = os.path.splitext(os.path.basename(target))[0]
    if not values[K_NAME].strip() or values[K_NAME].strip() == state.get('auto_name'):
        window[K_NAME].update(stem)
        state['auto_name'] = stem
    if target.lower().endswith(PYTHON_EXTS) and values[K_PYTHONW]:
        new_cmd = matching_python(target, values[K_PYTHON].strip() or default_python())
        if new_cmd != values[K_PYTHON]:
            window[K_PYTHON].update(new_cmd)
    is_py = target.lower().endswith(PYTHON_EXTS)
    for k in (K_PYTHON, K_PYTHON_BROWSE, K_PYTHONW):
        window[k].update(disabled=not is_py)
    values = current_values(window)                                               # pick up the updates just made
    refresh_icon(window, values, state)
    if target and not os.path.exists(target):
        status(window, f'Target not found:  {target}', C_ERR)
    elif target:
        status(window, f'Ready - press Create Shortcut (or Enter)' + ('' if is_py else '   -   non-Python file: launched directly'), C_OK)


def resolve_icon_file(values, state, target):
    """Return the .ico path the shortcut should use ('' for none), making the .ico when needed"""
    src = icon_source(values)
    if src == 'none' or not state.get('icon_b64'):
        return ''
    if src == 'file':
        path = values[K_ICON_FILE].strip()
        if path.lower().endswith('.ico'):
            return path
        png = image_to_png(base64.b64decode(state['icon_b64']))
        return write_ico(png, os.path.join(icon_folder(target), os.path.splitext(os.path.basename(path))[0] + '.ico'))
    png = image_to_png(base64.b64decode(state['icon_b64']))
    return write_ico(png, ico_path_for(target))


def make_shortcut(window, values, state):
    target = values[K_TARGET].strip().strip('"')
    if not target:
        status(window, 'Drop a file on the window or Browse to one first', C_WARN)
        return
    if not os.path.exists(target):
        status(window, f'Target not found:  {target}', C_ERR)
        return
    name = values[K_NAME].strip() or os.path.splitext(os.path.basename(target))[0]
    dest_dir = destination_folder(values[K_DEST], target, values[K_CUSTOM_DIR])
    if not dest_dir or not os.path.isdir(dest_dir):
        status(window, f'Destination folder not found:  {dest_dir}', C_ERR)
        return
    lnk = os.path.join(dest_dir, name + '.lnk')
    if os.path.exists(lnk):
        if sg.popup_yes_no(f'{lnk}\n\nalready exists.  Overwrite it?', title='Shortcut exists', keep_on_top=True) != 'Yes':
            status(window, 'Cancelled - shortcut already exists', C_WARN)
            return
        os.remove(lnk)
    target = os.path.abspath(target)                                              # the exact string passed on the command line -> same md5 as the running program
    icon = resolve_icon_file(values, state, target)
    extra_args = values[K_ARGS].strip()
    app_id, app_id_note = '', ''
    if target.lower().endswith(PYTHON_EXTS):
        launcher = values[K_PYTHON].strip() or default_python()
        if values[K_PYTHONW]:
            launcher = matching_python(target, launcher)
        arguments = f'"{target}"' + (f' {extra_args}' if extra_args else '')
        app_id, app_id_note = taskbar_app_id(target, launcher)
    else:
        launcher, arguments = target, extra_args
    create_shortcut(lnk, launcher, arguments, os.path.dirname(target), icon, values[K_DESC].strip(), app_id)
    status(window, f'Created  {lnk}' + (f'     icon: {icon}' if icon else ''), C_OK)
    tip = 'To pin it to the taskbar: right-click the shortcut in the Start Menu (or on the Desktop) and choose "Pin to taskbar"'
    id_line = f'Taskbar App ID: {app_id}   ({app_id_note})' if app_id else ''
    choice = sg.popup('Shortcut created', lnk, '', tip, id_line, custom_text=('Open folder', 'Close'), title='Done', keep_on_top=True, icon=ICON)
    if choice == 'Open folder':
        sg.execute_command_subprocess('explorer.exe', '/select,', lnk)


def fill_in_self(window, state):
    """Fill the form with a shortcut to psgshortcut itself - replaces the old 7-step procedure in the README"""
    me = os.path.abspath(__file__)
    window[K_TARGET].update(me)
    window[K_NAME].update('psgshortcut')
    state['auto_name'] = 'psgshortcut'
    window[K_ICON_AUTO].update(True)
    window[K_DESC].update('Make Windows shortcuts for Python programs and more')
    if window[K_DEST].get() == DEST_SAME:
        window[K_DEST].update(DEST_DESKTOP)
    window[K_PYTHON].update(matching_python('x.pyw', sys.executable))
    target_changed(window, current_values(window), state)
    status(window, 'Shortcut to psgshortcut itself is filled in - pick where it goes and press Create Shortcut', C_OK)


def enable_drag_and_drop(window):
    """Every element and the window background accept a dropped file.  Returns a note for the drop zone."""
    if psgdnd is None:
        return 'Drag & drop is off  -  install it with:   python -m pip install psgdnd'
    try:
        if hasattr(psgdnd, 'enable'):                                                   # psgdnd 6.0.5+ : rule based
            text_only = psgdnd.Rule(files=psgdnd.EVENT_ONLY, text=psgdnd.REPLACE)                 # a file dropped on a text field still becomes the target
            rules = {K_TARGET: psgdnd.Rule(files=psgdnd.PATH, text=psgdnd.REPLACE, dirs=False),
                     K_ICON_FILE: psgdnd.Rule(files=psgdnd.PATH, text=psgdnd.REPLACE, dirs=False, ext=IMAGE_EXTS),
                     K_CUSTOM_DIR: psgdnd.Rule(files=psgdnd.PATH, text=psgdnd.REPLACE),
                     K_PYTHON: psgdnd.Rule(files=psgdnd.PATH, text=psgdnd.REPLACE, dirs=False, ext=('.exe',)),
                     K_NAME: text_only, K_ARGS: text_only, K_DESC: text_only}
            psgdnd.enable(window, rules=rules, window_rule=psgdnd.Rule(files=psgdnd.EVENT_ONLY, text=psgdnd.EVENT_ONLY, highlight=False))
            catch_all = psgdnd.Rule(files=psgdnd.EVENT_ONLY, text=psgdnd.EVENT_ONLY, highlight=False)
            zone = psgdnd.Rule(files=psgdnd.EVENT_ONLY, text=psgdnd.EVENT_ONLY, highlight=True)
            for elem in window.element_list():                                           # labels, panels, buttons... all forward to the target
                if not isinstance(elem, (sg.Input, sg.Combo)) and not (isinstance(elem, sg.Button) and elem.BType in (sg.BUTTON_TYPE_BROWSE_FILE, sg.BUTTON_TYPE_BROWSE_FOLDER)):
                    psgdnd.target(window, elem, zone if elem.key == K_DROPZONE or getattr(elem, 'metadata', None) == K_DROPZONE else catch_all)
        else:                                                                           # psgdnd 6.0.4 (PyPI) : classic registration
            for elem in window.element_list():
                if elem.widget is not None and not isinstance(elem, sg.Combo):
                    psgdnd.register_element_dnd(elem, window, psgdnd.DROP_TYPE_FILES)
        return 'or drop it on any field  -  images onto the Icon field'
    except Exception as e:
        return f'Drag & drop could not start: {e}'


def dropped_files(event, values):
    """Files from a DropEvent as a list (works with both psgdnd APIs)"""
    files = getattr(event, 'files', None)
    if files:
        return list(files)
    raw = values.get(event, '')
    if isinstance(raw, str) and raw:
        return [p for p in raw.split(',') if p] if getattr(event, 'drop_type', '') == 'FILES' or os.path.exists(raw) else []
    return []


def settings_window(window):
    """Right-click -> Settings"""
    icon_dir_mode = sg.user_settings_get_entry(SETTING_ICON_DIR, ICON_DIR_DEFAULT)
    layout = [[sg.Text('psgshortcut settings', font='_ 14 bold', text_color=ACCENT_LIGHT)],
              [sg.Text('Extracted .ico files go', s=22), sg.Combo(ICON_DIR_CHOICES, icon_dir_mode, key=K_SET_ICON_DIR, readonly=True, s=52)],
              [sg.Text('Default destination', s=22), sg.Combo(DESTINATIONS, sg.user_settings_get_entry(SETTING_DEST, DEST_SAME), key=K_SET_DEST, readonly=True, s=52)],
              [sg.Checkbox('Keep psgshortcut on top of other windows (handy while dragging)', sg.user_settings_get_entry(SETTING_ON_TOP, False), key=K_SET_ON_TOP)],
              [sg.Text(f'Settings file:  {sg.user_settings_filename()}', text_color=MUTED, font='_ 9')],
              [sg.Push(), sg.Button('Save'), sg.Button('Cancel')]]
    win = sg.Window('Settings', layout, modal=True, keep_on_top=True, icon=ICON, finalize=True)
    win.bind('<Escape>', 'Cancel')
    event, values = win.read()
    win.close()
    if event == 'Save':
        sg.user_settings_set_entry(SETTING_ICON_DIR, values[K_SET_ICON_DIR])
        sg.user_settings_set_entry(SETTING_DEST, values[K_SET_DEST])
        sg.user_settings_set_entry(SETTING_ON_TOP, values[K_SET_ON_TOP])
        window.keep_on_top_set() if values[K_SET_ON_TOP] else window.keep_on_top_clear()
        status(window, 'Settings saved', C_OK)


# --------------------------------------------------------------------------------------------------------------------------------------------
#  Layout
# --------------------------------------------------------------------------------------------------------------------------------------------
def make_window():
    if THEME not in sg.theme_list():
        sg.theme_add_new(THEME, HARBOR_MIST)
    sg.theme(THEME)
    sg.set_options(font=('Segoe UI', 11) if sys.platform == 'win32' else ('DejaVu Sans', 10), icon=ICON)
    lbl = dict(s=(18, 1), justification='r', text_color=ACCENT_LIGHT)
    inp = dict(s=(58, 1), enable_events=True)
    off = dict(disabled_readonly_background_color=PANEL, disabled_readonly_text_color=MUTED)    # disabled inputs stay dark
    hint = dict(text_color=MUTED, font='_ 9')
    dnd_note = 'Drop a program anywhere on this window' if psgdnd else 'Drag & drop needs the psgdnd package'
    dnd_sub = '.py  .pyw  .exe  or any file   -   the icon inside a PySimpleGUI program is picked up automatically'
    programs = (('Programs', '*.py *.pyw *.exe'), ('All files', '*.* *'))
    images = (('Images', '*.ico *.png *.gif *.jpg *.bmp'), ('All files', '*.* *'))
    pythons = (('Python', 'python*.exe'), ('All files', '*.* *'))
    dest_default = sg.user_settings_get_entry(SETTING_DEST, DEST_SAME)
    auto_pythonw = sg.user_settings_get_entry(SETTING_PYTHONW, True)

    header = [sg.Image(data=png_resize(base64.b64decode(ICON), 56) if Image else ICON, subsample=None if Image else 4, pad=((0, 12), 0)),
              sg.Column([[sg.Text('psgshortcut', font='_ 20 bold', text_color='#dfe6ee', pad=0)],
                         [sg.Text('Make Windows shortcuts for Python programs - or anything else', pad=0, **hint)]], pad=0, element_justification='l'),
              sg.Push(), sg.Text(f'v{version}', text_color=MUTED, font='_ 10', pad=((0, 4), (0, 18)))]

    drop_zone = sg.Column([[sg.Text('⬇', font='_ 26', text_color=ACCENT_LIGHT, background_color=PANEL, pad=((0, 0), (6, 0)), metadata=K_DROPZONE)],
                           [sg.Text(dnd_note, font='_ 12 bold', text_color='#dfe6ee', background_color=PANEL, pad=0, metadata=K_DROPZONE)],
                           [sg.Text(dnd_sub, background_color=PANEL, pad=((0, 0), (2, 8)), metadata=K_DROPZONE, **hint)]],
                          background_color=PANEL, element_justification='c', expand_x=True, pad=(0, (4, 12)), key=K_DROPZONE)

    form = [[sg.Text('Target', **lbl), sg.Input(key=K_TARGET, **inp), sg.FileBrowse(key=K_TARGET_BROWSE, target=K_TARGET, file_types=programs)],
            [sg.Text('Shortcut name', **lbl), sg.Input(key=K_NAME, s=(58, 1)), sg.Text('.lnk', **hint)],
            [sg.Text('Put shortcut in', **lbl), sg.Combo(DESTINATIONS, dest_default, key=K_DEST, readonly=True, enable_events=True, s=(56, 1))],
            [sg.Text('Custom folder', **lbl), sg.Input(key=K_CUSTOM_DIR, s=58, disabled=True, **off), sg.FolderBrowse(key=K_CUSTOM_BROWSE, target=K_CUSTOM_DIR, disabled=True)],
            [sg.Text('Icon', **lbl), sg.Radio('Auto - from the program', 'ICON', key=K_ICON_AUTO, default=True, enable_events=True),
             sg.Radio('Icon file', 'ICON', key=K_ICON_FILE_SRC, enable_events=True), sg.Radio('None', 'ICON', key=K_ICON_NONE, enable_events=True)],
            [sg.Text('Icon file', **lbl), sg.Input(key=K_ICON_FILE, **inp), sg.FileBrowse(key=K_ICON_BROWSE, target=K_ICON_FILE, file_types=images)],
            [sg.HorizontalSeparator(color=PANEL, pad=(0, 8))],
            [sg.Text('Python', **lbl), sg.Input(default_python(), key=K_PYTHON, s=(58, 1), **off), sg.FileBrowse(key=K_PYTHON_BROWSE, target=K_PYTHON, file_types=pythons)],
            [sg.Text('', **lbl), sg.Checkbox('Use pythonw.exe for .pyw (no console window) and python.exe for .py', auto_pythonw, key=K_PYTHONW, enable_events=True, **hint)],
            [sg.Text('Arguments', **lbl), sg.Input(key=K_ARGS, s=(58, 1))],
            [sg.Text('Description', **lbl), sg.Input(key=K_DESC, s=(58, 1)), sg.Text('tooltip', **hint)]]

    preview = sg.Column([[sg.Text('Shortcut icon', font='_ 11 bold', text_color=ACCENT_LIGHT, background_color=PANEL)],
                         [sg.Image(key=K_PREVIEW, size=(128, 128), background_color=BG, pad=(0, 6))],
                         [sg.Text('Drop a program on the window and its icon shows up here', key=K_PREVIEW_NOTE, s=(24, 4), background_color=PANEL, **hint)]],
                        background_color=PANEL, element_justification='c', vertical_alignment='top', pad=((14, 0), 0), expand_y=True)

    buttons = [sg.Button('Create Shortcut', key=K_CREATE, bind_return_key=True, font='_ 12 bold', s=(18, 1), button_color=('#ffffff', ACCENT)),
               sg.Button('Shortcut to this program', key=K_SELF, button_color=(ACCENT_LIGHT, PANEL), tooltip='Fill the form with a shortcut to psgshortcut itself'),
               sg.Button('Clear', key=K_CLEAR, button_color=(ACCENT_LIGHT, PANEL)), sg.Push(), sg.Button('Exit', button_color=(ACCENT_LIGHT, PANEL))]

    status_bar = [sg.Text('Welcome - drop a program on the window, or Browse to one', key=K_STATUS, expand_x=True, background_color=PANEL, pad=((8, 8), 6), font='_ 10')]

    layout = [header, [drop_zone], [sg.Column(form, pad=0), preview], [sg.Column([buttons], expand_x=True, pad=(0, (14, 6)))], status_bar]
    window = sg.Window(f'psgshortcut {version}', layout, icon=ICON, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_SETTINGS_EXIT, finalize=True,
                       auto_save_location=True, keep_on_top=sg.user_settings_get_entry(SETTING_ON_TOP, False), margins=(16, 12))
    window.bind('<Escape>', K_ESC)
    return window


# --------------------------------------------------------------------------------------------------------------------------------------------
#  Main
# --------------------------------------------------------------------------------------------------------------------------------------------
def main():
    sg.user_settings_filename(filename='psgshortcut.json')
    window = make_window()
    state = {'icon_b64': None, 'auto_name': ''}
    status(window, f'Welcome  -  {enable_drag_and_drop(window)}', MUTED if psgdnd else C_WARN)
    if not HAVE_WIN32:
        status(window, 'pywin32 is missing (or this is not Windows) - the form works but no shortcut can be written.   python -m pip install pywin32', C_WARN)
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):                                 # psgshortcut some_program.pyw   (or "Send to")
        window[K_TARGET].update(os.path.abspath(sys.argv[1]))
        target_changed(window, current_values(window), state)

    while True:
        event, values = window.read()
        if event in ('Exit', K_ESC, sg.WINDOW_CLOSED):
            break
        if psgdnd is not None and psgdnd.is_drop_event(event):
            files = dropped_files(event, values)
            if not files:
                continue
            path = files[0]
            if event.key == K_ICON_FILE:
                window[K_ICON_FILE].update(path)
                window[K_ICON_FILE_SRC].update(True)
                refresh_icon(window, current_values(window), state)
            elif event.key in (K_CUSTOM_DIR, K_PYTHON):
                window[event.key].update(path)
            elif os.path.isdir(path):
                window[K_DEST].update(DEST_CUSTOM)
                window[K_CUSTOM_DIR].update(path, disabled=False)
                window[K_CUSTOM_BROWSE].update(disabled=False)
                status(window, f'Shortcuts will be put in  {path}', C_OK)
            elif path.lower().endswith(IMAGE_EXTS) and not values[K_TARGET].strip().lower().endswith(IMAGE_EXTS):
                window[K_ICON_FILE].update(path)
                window[K_ICON_FILE_SRC].update(True)
                refresh_icon(window, current_values(window), state)
            else:
                window[K_TARGET].update(path)
                target_changed(window, current_values(window), state)
        elif event == K_TARGET:
            target_changed(window, values, state)
        elif event == K_DEST:
            custom = values[K_DEST] == DEST_CUSTOM
            window[K_CUSTOM_DIR].update(disabled=not custom)
            window[K_CUSTOM_BROWSE].update(disabled=not custom)
            sg.user_settings_set_entry(SETTING_DEST, values[K_DEST])
        elif event in (K_ICON_AUTO, K_ICON_FILE_SRC, K_ICON_NONE, K_ICON_FILE):
            if event == K_ICON_FILE and values[K_ICON_FILE].strip():
                window[K_ICON_FILE_SRC].update(True)
                values[K_ICON_AUTO], values[K_ICON_FILE_SRC], values[K_ICON_NONE] = False, True, False
            refresh_icon(window, values, state)
        elif event == K_PYTHONW:
            sg.user_settings_set_entry(SETTING_PYTHONW, values[K_PYTHONW])
            if values[K_PYTHONW] and values[K_TARGET].strip():
                target_changed(window, values, state)
        elif event == K_CREATE:
            try:
                make_shortcut(window, values, state)
                sg.user_settings_set_entry(SETTING_PYTHON, values[K_PYTHON].strip())
            except Exception as e:
                status(window, f'Error: {e}', C_ERR)
                sg.popup_error('Could not create the shortcut', e, keep_on_top=True, icon=ICON)
        elif event == K_SELF:
            fill_in_self(window, state)
        elif event == K_CLEAR:
            for k in (K_TARGET, K_NAME, K_ICON_FILE, K_ARGS, K_DESC):
                window[k].update('')
            window[K_ICON_AUTO].update(True)
            state.update(icon_b64=None, auto_name='')
            set_preview(window, None, 'Drop a program on the window and its icon shows up here')
            status(window, 'Cleared', MUTED)
        elif event == 'Version':
            sg.popup_scrolled(__file__, f'psgshortcut {version}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Settings':
            settings_window(window)
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback('psgshortcut crashed', e)
