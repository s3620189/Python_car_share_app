#!/usr/bin/env python3
# coding=UTF-8
'''
@Date: 2020-06-11 17:52:08
@LastEditTime: 2020-06-11 19:57:04
@Description: file content
'''
from masterpi import create_app

# 初始化app
app = create_app()

if __name__ == '__main__':
    app.run(host='localhost', debug=True, port=5000)
