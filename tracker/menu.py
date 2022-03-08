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

        cmds.menuItem(label='Start timer...', en=True, c="from maya_toggl.tracker import app as mt_app; mt_app.main()")
        cmds.menuItem(label='Stop timer', en=False, c="")

    def delete(self):
        cmds.deleteUI(self.menu_name)
