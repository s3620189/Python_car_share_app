from flask import has_app_context
from flask import current_app
import requests
from datetime import datetime
from datetime import timezone


class RestUtils:
    '''Utilities for accesss database via RESTful API'''

    _rest_api_tmpl = "http://localhost:5000/api/%s"

    @classmethod
    def execRestApi(cls, endpoint, method, data=None):
        '''Making a RESTful request for access to database

        Args:
            endpoint (str)  : URI
            method:  (str)  : GET/POST/PUT
            data     (dict) : arguments/data sent with API

        Returns:
            (dict) response info, including rc, msg and data
        '''

        # for unit tests on web which indirectly invoke RESTful API
        if has_app_context() and current_app.testing:
            return cls.execTestRestApi(endpoint, method, data=data)

        if method == "POST":
            r = requests.post(cls._rest_api_tmpl % (endpoint,), data=data)
        elif method == "PUT":
            r = requests.put(cls._rest_api_tmpl % (endpoint,), data=data)
        else:  # GET
            r = requests.get(cls._rest_api_tmpl % (endpoint,), params=data)

        if r.status_code != 200:
            return None

        return r.json()

    @classmethod
    def execTestRestApi(cls, endpoint, method, data=None):
        _rest_api_tmpl = "/api/%s"

        with current_app.app_context():
            client = current_app.test_client()

            if method == "POST":
                r = client.post(cls._rest_api_tmpl % (endpoint,), data=data)
            elif method == "PUT":
                r = client.put(cls._rest_api_tmpl % (endpoint,), data=data)
            else:  # GET
                r = client.get(cls._rest_api_tmpl %
                               (endpoint,), query_string=data)

        if r.status_code != 200:
            return None

        return r.get_json()

    @classmethod
    def utcToLocal(cls, dt):
        '''Convert datetime from UTC to local time

        Args:
            dt (datetime): datetime object in UTC time zone

        Returns:
            (datetime) a datetime object in local time zone
        '''

        return dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    @classmethod
    def localToUtc(cls, dt):
        '''Convert datetime from local time to UTC

        Args:
            dt (datetime): datetime object in local time zone

        Returns:
            (datetime) a datetime object in UTC time zone
        '''

        return dt.replace(tzinfo=None).astimezone(tz=timezone.utc)
