#!/usr/bin/env python3
# coding=UTF-8
'''
@Date: 2020-02-28 02:35:31
@LastEditTime: 2020-06-12 13:18:01
@Description: file content
'''


class StatusCode:
    def __init__(self):
        self.init()

    def init(self):
        self._data = {"msg": "success", "data": [],
                      "code": 0, "total": 0, "pageCount": 0}

    def success(self, data=None, total=0, page_count=0, msg=None):
        self.init()
        self._data["data"] = data or []
        self._data["total"] = total
        if msg:
            self._data["msg"] = msg if msg != "null" else ""
        else:
            self._data["msg"] = "success"
        self._data["code"] = 0

        return self._data

    @property
    def data(self):
        return self._data

    @property
    def no_permission(self):
        self.init()
        self._data["code"] = 1001
        self._data["msg"] = 'Permission denied'

        return self._data

    @property
    def system_inner_error(self):

        self.init()
        self._data["code"] = 1002
        self._data["msg"] = 'System is busy, please try again later'

        return self._data

    @property
    def method_error(self):

        self.init()
        self._data["code"] = 1003
        self._data["msg"] = 'Request method error'

        return self._data

    @property
    def login_error(self):

        self.init()
        self._data["code"] = 1004
        self._data["msg"] = 'Login failed'

        return self._data

    @property
    def token_not_found(self):
        self.init()
        self._data["code"] = 1005
        self._data["msg"] = 'The token does not exist or has expired, please log in again'
        return self._data

    @property
    def token_parsing_failed(self):
        self.init()
        self._data["code"] = 1006
        self._data["msg"] = 'Token resolution failed. Unknown reason, please log in again!'
        return self._data

    @property
    def token_become_invalid(self):
        self.init()
        self._data["code"] = 1007
        self._data["msg"] = 'Token is invalid, please log in again'
        return self._data

    @property
    def token_is_expired(self):
        self.init()
        self._data["code"] = 1008
        self._data["msg"] = 'tonken has expired, please log in again'
        return self._data

    @property
    def args_missing(self):
        self.init()
        self._data["code"] = 1009
        self._data["msg"] = 'Missing parameter'

        return self._data

    @property
    def get_user_info_error(self):
        self.init()
        self._data["code"] = 1010
        self._data["msg"] = 'Failed to get login information! Please login first'

        return self._data

    def action_error(self, msg):
        self.init()
        self._data["code"] = 1011
        self._data["msg"] = msg or 'operation failed'

        return self._data

    @property
    def data_not_found(self):
        self.init()
        self._data["code"] = 1012
        self._data["msg"] = 'Data not found'

        return self._data

    @property
    def username_already_exists(self):
        self.init()
        self._data["code"] = 1013
        self._data["msg"] = 'Username already exists, please change username and try again'

        return self._data

    @property
    def wrong_username_password(self):
        self.init()
        self._data["code"] = 1014
        self._data["msg"] = 'Wrong user name or password'

        return self._data

    @property
    def already_exists(self):
        self.init()
        self._data["code"] = 1015
        self._data["msg"] = 'The data already exists, please do not submit it again'

        return self._data
