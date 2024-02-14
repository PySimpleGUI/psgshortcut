import setuptools

def readme():
    try:
        with open('README.md') as f:
            return f.read()
    except IOError:
        return ''


setuptools.setup(
name="psgshortcut",
version="5.0.0",
author="PySimpleSoft Inc.",
install_requires=["PySimpleGUI>=5","pywin32"],
description="Utility made with PySimpleGUI to create shortcuts of files or programs",
long_description=readme(),
long_description_content_type="text/markdown",
license='Free To Use But Restricted',
keywords="GUI UI PySimpleGUI tkinter psgshortcut shortcut windows taskbar",
url="https://github.com/PySimpleGUI/psgshortcut",
packages=setuptools.find_packages(),
python_requires=">=3.6",
classifiers=[
"Intended Audience :: Developers",
"License :: Free To Use But Restricted",
"Operating System :: OS Independent",
"Framework :: PySimpleGUI",
"Framework :: PySimpleGUI :: 5",
"Programming Language :: Python :: 3",
"Programming Language :: Python :: 3.6",
"Programming Language :: Python :: 3.7",
"Programming Language :: Python :: 3.8",
"Programming Language :: Python :: 3.9",
"Programming Language :: Python :: 3.10",
"Programming Language :: Python :: 3.11",
"Programming Language :: Python :: 3.12",
"Programming Language :: Python :: 3.13",
"Topic :: Multimedia :: Graphics",
],
package_data={"":
["*","*.*"]
        },
entry_points={"gui_scripts": ["psgshortcut=psgshortcut.psgshortcut:main", ], },

)

