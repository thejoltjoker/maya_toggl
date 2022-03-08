#!/usr/bin/env python3
"""app.py
Description of app.py.
"""
import os
import logging
import sys
import shiboken2
import maya.OpenMayaUI as mui
from PySide2 import QtWidgets, QtCore
from maya import cmds

from maya_toggl.toggl import Toggl

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

TAGS = ['anim', 'animation', 'capture', 'comp', 'compositing', 'fx', 'layout', 'light', 'lighting', 'lookdev',
        'realtime', 'script', 'storyboard']

if sys.platform == 'darwin':
    try:
        import certifi
    except ImportError as e:
        cmds.warning("Certifi couldn't be imported")


def write_temp_file(content):
    """Write last workspace and project to file"""
    path = temp_file()

    # Create folder if it doesn't exist
    if not os.path.isdir(os.path.dirname(path)):
        os.mkdir(os.path.dirname(path))

    with open(path, 'w') as tmp_file:
        tmp_file.write(str(':'.join(content)))


def read_temp_file():
    """Read last workspace and project from file"""
    path = temp_file()

    # Create folder if it doesn't exist
    if not os.path.isfile(path):
        return None

    with open(path, 'r') as tmp_file:
        return tmp_file.read().split(':')


def temp_file(folder=None, filename='.maya_toggl'):
    """Get the path to the temp file to store last workspace and project"""
    if not folder:
        folder = temp_folder()

    path = os.path.join(folder, filename)
    return path


def temp_folder():
    """Get the path to the temp folder"""
    return os.getenv('TMPDIR', os.path.expanduser('~/tmp'))


def get_maya_window():
    """Get maya main window"""
    ptr = mui.MQtUtil.mainWindow()
    maya_window = shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)

    return maya_window


def description_from_filename(separator='_', name_index=0):
    """Get the task description from filename"""
    filename = cmds.file(q=True, sn=True)
    if filename:
        filename = os.path.basename(filename)
        split_name = filename.split(separator)
        return split_name[name_index]
    return ''


def tags_from_filename(separator='_'):
    """Get tags from filename"""
    filename = cmds.file(q=True, sn=True)
    tags = []
    if filename:
        filename = os.path.basename(filename)
        split_name = filename.split(separator)
        tags = [x.lower() for x in split_name if x.lower() in TAGS]
    tags.append('maya')
    return tags


def stop_timer():
    """Stop the currently running timer"""
    api = Toggl()
    api.stop_timer()
    logger.info('Timer stopped')


def ask_to_update_timer():
    """Display a popup that asks to update the timer when another scene is opened."""
    dialog_title = 'Maya Toggl'
    dialog_message = 'Do you want to update the timer?'
    default_button = 'OK'
    cancel_button = 'Cancel'
    dialog = cmds.confirmDialog(
        title=dialog_title,
        message=dialog_message,
        button=[default_button, cancel_button],
        defaultButton=default_button,
        cancelButton=cancel_button,
        dismissString=cancel_button)

    if dialog == default_button:
        main()
    else:
        # If dialog is cancelled
        logger.info('Timer was not updated')


def scene_change_script_job():
    job = cmds.scriptJob(event=["SceneOpened", "from maya_toggl import app as mt_app; mt_app.ask_to_update_timer()"],
                         protected=True)
    return job


class Window(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.api = Toggl()
        self.workspaces = {}
        self.projects = {}
        last_used = read_temp_file()

        # Main layout
        self.layout_main = QtWidgets.QVBoxLayout()

        # Description name layout
        self.layout_description = QtWidgets.QHBoxLayout()
        self.line_description = QtWidgets.QLineEdit()
        self.fill_description()
        self.layout_description.addWidget(self.line_description)

        # Name fill
        self.button_description_fill = QtWidgets.QPushButton('<<')
        self.button_description_fill.clicked.connect(self.fill_description)
        self.layout_description.addWidget(self.button_description_fill)

        # Project layout
        self.layout_project = QtWidgets.QHBoxLayout()

        # Workspace dropdown
        self.combo_workspace = QtWidgets.QComboBox()
        self.combo_workspace.addItem('No workspaces')
        self.update_workspaces()
        self.combo_workspace.currentTextChanged.connect(self.update_projects)
        self.layout_project.addWidget(self.combo_workspace)

        # Project dropdown
        self.combo_project = QtWidgets.QComboBox()
        self.combo_project.addItem('No projects')
        self.init_projects()
        self.combo_project.currentTextChanged.connect(self.store_dropdown_to_file)
        self.layout_project.addWidget(self.combo_project)

        # Set from last used
        if last_used:
            for i in range(self.combo_workspace.count()):
                if self.combo_workspace.itemText(i) == last_used[0]:
                    self.combo_workspace.setCurrentIndex(i)

            for i in range(self.combo_project.count()):
                if self.combo_project.itemText(i) == last_used[1]:
                    self.combo_project.setCurrentIndex(i)
        # Start button
        self.button_start = QtWidgets.QPushButton('Start')
        self.button_start.clicked.connect(self.start_timer)
        self.layout_project.addWidget(self.button_start)

        # Add layouts to main layout
        self.layout_main.addLayout(self.layout_description)
        self.layout_main.addLayout(self.layout_project)

        self.widget_main = QtWidgets.QWidget()
        self.widget_main.setWindowFlags(self.windowFlags() | QtCore.Qt.Dialog)
        self.widget_main.setLayout(self.layout_main)
        self.setCentralWidget(self.widget_main)
        # self.setGeometry(50, 100, 500, 50)
        self.setWindowTitle("Start timer")

    def start_timer(self):
        """Start timer with selected options"""
        description = str(self.line_description.text())
        workspace_id = self.workspaces.get(str(self.combo_workspace.currentText()))
        project_id = self.projects.get(str(self.combo_project.currentText()))
        tags = tags_from_filename()
        logger.info(
            f'Starting timer for project {project_id} in workspace {workspace_id} with the description "{description}"')
        self.api.start_timer(description=description, wid=workspace_id, pid=project_id, tags=tags)
        self.close()

    def fill_description(self):
        """Fill the description field from filename"""
        description = description_from_filename()
        self.line_description.setText(description)
        return description

    def update_workspaces(self):
        """Update and populate workspaces dropdown"""
        self.get_workspaces()
        self.combo_workspace.clear()

        for p in self.workspaces.keys():
            self.combo_workspace.addItem(p)

    def get_workspaces(self):
        """Get workspaces"""
        workspaces = self.api.get_workspaces()
        if workspaces:
            self.workspaces = {x.get('name'): x.get('id') for x in workspaces}
        return self.workspaces

    def init_projects(self):
        """Populate projects dropdown"""
        self.get_projects()
        self.combo_project.clear()

        for p in self.projects.keys():
            self.combo_project.addItem(p)

    def update_projects(self):
        """Update projects dropdown"""
        self.get_projects()
        self.combo_project.clear()

        for p in self.projects.keys():
            self.combo_project.addItem(p)

        self.store_dropdown_to_file()

    def store_dropdown_to_file(self):
        """Store currently selected dropdown options to temp file"""
        write_temp_file((str(self.combo_workspace.currentText()), str(self.combo_project.currentText())))

    def get_projects(self):
        """Get all projects for the selected workspace"""
        workspace_id = self.workspaces.get(str(self.combo_workspace.currentText()))
        projects = self.api.get_projects(workspace_id)
        if projects:
            self.projects = {x.get('name'): x.get('id') for x in projects}
        return self.projects


def main():
    """docstring for main"""
    global tracker_window
    try:
        tracker_window.close()
    except:
        pass
    tracker_window = Window(parent=get_maya_window())
    tracker_window.show()


if __name__ == '__main__':
    main()
