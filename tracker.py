#!/usr/bin/env python3
"""tracker.py
Description of tracker.py.
"""
import base64
import json
import os
from urllib.request import urlopen, Request
import logging
import ssl

import certifi as certifi

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
logger = logging.getLogger()


class Endpoints:
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
        return self.make_request(Endpoints.workspaces)

    def get_workspace(self, name):
        workspaces = self.get_workspaces()
        for ws in workspaces:
            if name in ws.get('name'):
                return ws

    def get_projects(self, workspace_id):
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


def split_string(input_string, separator='_'):
    return input_string.split()


def task_name_from_filename(filename, separator='_', name_index=0):
    split_name = split_string(filename, separator)
    return split_name[name_index]


def main():
    """docstring for main"""
    t = Toggl()
    # logger.info(t.get_profile())
    # logger.info(t.get_current_time_entry())
    workspace = t.get_workspaces()[0]
    logger.info(workspace)
    projects = t.get_projects(workspace['id'])
    for p in projects:
        print(p.get('name'))
    # logger.info(t.stop_timer())
    # logger.info(t.start_timer(description='Programming'))


if __name__ == '__main__':
    main()
