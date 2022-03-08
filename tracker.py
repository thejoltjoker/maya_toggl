#!/usr/bin/env python3
"""tracker.py
Description of tracker.py.
"""
import base64
import json
import os
import certifi
import logging
import ssl
import shiboken2
import maya.OpenMayaUI as mui
from urllib.request import urlopen, Request
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from maya import cmds

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
logger = logging.getLogger()


class Endpoints:
    """Toggl endpoints"""
    profile = 'https://api.track.toggl.com/api/v8/me'
    workspaces = 'https://api.track.toggl.com/api/v8/workspaces'
    time_entries = 'https://api.track.toggl.com/api/v8/time_entries'
    start_time_entry = 'https://api.track.toggl.com/api/v8/time_entries/start'
    current_time_entry = 'https://api.track.toggl.com/api/v8/time_entries/current'

    @staticmethod
    def stop_time_entry(entry_id):
        return f'https://api.track.toggl.com/api/v8/time_entries/{entry_id}/stop'

    @staticmethod
    def projects(workspace_id):
        return f'https://api.track.toggl.com/api/v8/workspaces/{workspace_id}/projects'


class Toggl:
    def __init__(self, api_token=None):
        self.headers = {
            "Authorization": "",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "python/urllib",
        }

        if not api_token:
            api_token = os.getenv('TOGGL_TOKEN')
        if api_token:
            self.set_api_key(api_token)
        if not api_token:
            logger.error('No API token given/found')

    def set_api_key(self, api_key):
        """Set api key to headers"""
        token = f'{api_key}:api_token'
        auth_header = 'Basic ' + base64.b64encode(token.encode()).decode('ascii').rstrip()
        self.headers['Authorization'] = auth_header
        return self.headers['Authorization']

    def make_request(self, url, data=None, method='GET'):
        # Encode data to bytes
        if data:
            data = json.dumps(data).encode('utf-8')

        # Prepare request
        # context = ssl._create_unverified_context()
        request = Request(url, headers=self.headers, data=data, method=method)

        # ssl._create_default_https_context = ssl._create_unverified_context

        with urlopen(request, context=ssl.create_default_context(cafile=certifi.where())) as response:
            # Json encode the response
            return json.loads(response.read().decode('utf-8'))

    def get_profile(self):
        """Get info about the user profile"""
        return self.make_request(Endpoints.profile)

    def get_workspaces(self):
        """Get all workspaces info"""
        return self.make_request(Endpoints.workspaces)

    def get_workspace(self, name):
        """Get a workspace from the name"""
        workspaces = self.get_workspaces()
        for ws in workspaces:
            if name in ws.get('name'):
                return ws

    def get_projects(self, workspace_id):
        """Get all projects for the given workspace"""
        logger.info(workspace_id)
        return self.make_request(Endpoints.projects(workspace_id))

    def get_current_time_entry(self):
        """Get the currently running time entry"""
        return self.make_request(Endpoints.current_time_entry)

    def start_timer(self, **params):
        """Start a new time entry"""
        params['created_with'] = 'maya'
        data = {'time_entry': params}

        return self.make_request(Endpoints.start_time_entry, data=data, method='POST')

    def stop_timer(self):
        """Stop the currently running time entry"""
        entry = self.get_current_time_entry()

        if entry.get('data'):
            return self.make_request(Endpoints.stop_time_entry(entry['data']['id']))


class Window(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.api = Toggl()
        self.workspaces = {}
        self.projects = {}
        last_used = read_temp_file()
        logger.info(last_used)

        # Main layout
        self.layout_main = QVBoxLayout()

        # Description name layout
        self.layout_description = QHBoxLayout()
        self.line_description = QtWidgets.QLineEdit()
        self.fill_description()
        self.layout_description.addWidget(self.line_description)

        # Name fill
        self.button_description_fill = QtWidgets.QPushButton('<<')
        self.button_description_fill.clicked.connect(self.fill_description)
        self.layout_description.addWidget(self.button_description_fill)

        # Project layout
        self.layout_project = QHBoxLayout()

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

        self.widget_main = QWidget()
        self.widget_main.setWindowFlags(self.windowFlags() | QtCore.Qt.Dialog)
        self.widget_main.setLayout(self.layout_main)
        self.setCentralWidget(self.widget_main)
        self.setGeometry(50, 100, 500, 50)
        self.setWindowTitle("Start timer")

    def start_timer(self):
        """Start timer with selected options"""
        description = str(self.line_description.text())
        workspace_id = self.workspaces.get(str(self.combo_workspace.currentText()))
        project_id = self.projects.get(str(self.combo_project.currentText()))
        logger.info(
            f'Starting timer for project {project_id} in workspace {workspace_id} with the description "{description}"')
        self.api.start_timer(description=description, wid=workspace_id, pid=project_id, tags=['maya'])
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
        logger.info(self.projects)
        return self.projects


def write_temp_file(content):
    """Write last workspace and project to file"""
    path = temp_file()

    # Create folder if it doesn't exist
    if not os.path.isdir(os.path.dirname(path)):
        os.mkdir(os.path.dirname(path))

    with open(path, 'w') as tmp_file:
        logger.info(f'Writing {content} to file')
        tmp_file.write(str(':'.join(content)))


def read_temp_file():
    """Read last workspace and project from file"""
    path = temp_file()

    # Create folder if it doesn't exist
    logger.info(path)
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
