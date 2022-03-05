#!/usr/bin/env python3
"""tracker.py
Description of tracker.py.
"""
import base64
import json
import os
import urllib
from urllib.request import urlopen, Request
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
logger = logging.getLogger()


class Endpoints:
    PROFILE = 'https://api.track.toggl.com/api/v8/me'
    TIME_ENTRIES = 'https://api.track.toggl.com/api/v8/time_entries'
    START_TIME_ENTRY = 'https://api.track.toggl.com/api/v8/time_entries/start'
    CURRENT_TIME_ENTRY = 'https://api.track.toggl.com/api/v8/time_entries/current'

    @staticmethod
    def STOP_TIME_ENTRY(entry_id):
        return f'https://api.track.toggl.com/api/v8/time_entries/{entry_id}/stop'


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

    def set_api_key(self, api_key):
        token = f'{api_key}:api_token'
        auth_header = 'Basic ' + base64.b64encode(token.encode()).decode('ascii').rstrip()
        self.headers['Authorization'] = auth_header
        logger.info(self.headers)
        return self.headers['Authorization']

    def make_request(self, url, data=None, method='GET'):
        # Encode data to bytes
        if data:
            data = json.dumps(data).encode('utf-8')

        # Prepare request
        request = Request(url, headers=self.headers, data=data, method=method)

        # Send request
        # urlopen(request)
        with urlopen(request) as response:
            # Json encode the response
            return json.loads(response.read().decode('utf-8'))

    def get_profile(self):
        return self.make_request(Endpoints.PROFILE)

    def get_current_time_entry(self):
        return self.make_request(Endpoints.CURRENT_TIME_ENTRY)

    def start_timer(self, **params):
        data = {'time_entry': params}
        data['time_entry']['created_with'] = 'Maya'
        return self.make_request(Endpoints.START_TIME_ENTRY, data=data, method='POST')

    def stop_timer(self):
        entry = self.get_current_time_entry()
        # logger.info(entry['data']['id'])
        logger.info(entry)
        if entry.get('data'):
            return self.make_request(Endpoints.STOP_TIME_ENTRY(entry['data']['id']))


def main():
    """docstring for main"""
    t = Toggl()
    # logger.info(t.get_profile())
    # logger.info(t.get_current_time_entry())
    # logger.info(t.stop_timer())
    logger.info(t.start_timer(description='Programming'))
    pass


if __name__ == '__main__':
    main()
