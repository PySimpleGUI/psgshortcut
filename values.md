
[description]
PySimpleGUI Shortcut Tool

Creates Windows shortcuts

[features]
* Makes shortcuts for any file
* Shortcuts can be added to your desktop or pin to the taskbar
* Click (or double click) to launch the shortcut
* Enables interacting with Python programs more "Windows-like"

[extras]

## Create a Windows 1-Click Shortcut

psgdemos is your first stop when implementing any new feature for your
application. To keep psgdemos at your fingertips, on Windows, you can
create a shortcut that keeps psgdemos as close as a single click. Use
the [`psgshortcut` application](https://pypi.org/project/psgshortcut/)
app to make such shortcuts. You can then add the shortcut to your
desktop or taskbar and launch psgdemos with a single click!

To do this, follow these steps:

1. `pip install psgshortcut`
1. Open a command window (We promise, it's the last time you'll need the command line for psgdemos)
2. Type `where psgdemos`
3. Copy the resulting line into psgshortcut first input
4. Run psgdemos by typing `psgdemos` in your command window
5. Right click and choose "File Location"
6. Copy the file location results, but change the extension from .py to .ico and paste into the Icon file input of the shortcut maker
7. Click "Create Shortcut"

These steps create a shortcut in the same folder as the target file. You can now move this shortcut file to any place you want (like to your desktop). Double-click the shortcut and your program will launch.

[extras]
## Create a Shortcut To This Program

Use this program to make a shortcut to itself so that you can then put
on your desktop or pin to your taskbar or ???


To do this, follow these steps:

1. Open a command window (I promise, it's the last time you'll need to for this program)
2. Type - `where psgshortcut`
3. Copy the line that `where psgshortcut` gave you into the first input of the shortcut maker program
4. Run psgshortcut by typing `psgshortcut` in your command window
5. Right click and choose "File Location"
6. Copy the file location results, but change the extension from .py to .ico and paste into the Icon file input of the shortcut maker
7. Click "Create Shortcut"

These steps will create a shortcut in the same folder as the target
file.  You can safely move this shortcut file any place you want (like
to your desktop). Double-click the shortcut and your program should
launch.

## Make Shortcuts To Anything

You can not only make shortcuts to Python programs, but you can make
shortcuts to EXE and other files.  The GUI is self-explanatory.  Fill
in the inputs, click the Make Shortcut button and you'll find the
shortcut in the same folder as the target program.

## Important Note - Pinning To Taskbar Requires "Python Command"

If you wish to pin your shortcut to the taskbar, then be sure to fill
in the "Python Command" field with the full path to your pythonw.exe
file.  Without it you'll get "IDLE" as the program that's pinned.  You
can skip filling in this field if you're going to place the shortcut
on your desktop or other location.
