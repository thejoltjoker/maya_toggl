#!/usr/bin/env python3
"""menu.py
Description of menu.py.
"""
import os
from maya import cmds, mel


class Menu:
    def __init__(self):
        self.menu_name = 'maya_toggl'
        cmds.menu(self.menu_name, allowOptionBoxes=True, parent='MayaWindow', label='Toggl', tearOff=True)
        start_command = "from maya_toggl import app as mt_app; mt_app.scene_change_script_job(); mt_app.main()"
        cmds.menuItem(label='Start timer...', en=True, c=start_command)
        stop_command = "from maya_toggl import app as mt_app; mt_app.stop_timer()"
        cmds.menuItem(label='Stop timer', en=True, c=stop_command)

    def delete(self):
        cmds.deleteUI(self.menu_name)
