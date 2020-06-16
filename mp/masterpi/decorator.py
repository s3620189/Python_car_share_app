#!/usr/bin/env python3
# coding=UTF-8
'''
@Date: 2020-06-11 22:02:05
@LastEditTime: 2020-06-14 14:32:31
@Description: file content
'''

from flask import request, g, jsonify, redirect, url_for, abort
from functools import wraps


# Judge and parse the requested json
def parse_json(fun):
    @wraps(fun)
    def inner(*arg, **kwargs):
        if request.method == "OPTIONS":
            return jsonify(g.sc.success())
        data = request.json
        # If the request has no parameters, the parameter is missing
        if not data:
            return jsonify(g.sc.params_missing)
        return fun(data, *arg, **kwargs)
    return inner


def isAdmin(fun):
    @wraps(fun)
    def inner(*arg, **kwargs):
        if not g.account or g.account.get("role") != "admin":
            if request.method == "POST":
                return jsonify(g.sc.no_permission)

            if request.method == "GET":
                return redirect(url_for("web.index"))

            return abort(404)

        return fun(*arg, **kwargs)
    return inner


def isManager(fun):
    @wraps(fun)
    def inner(*arg, **kwargs):
        if not g.account or g.account.get("role") != "admin" and g.account.get("role") != "manager":
            if request.method == "POST":
                return jsonify(g.sc.no_permission)

            if request.method == "GET":
                return redirect(url_for("web.index"))

            return abort(404)

        return fun(*arg, **kwargs)
    return inner
