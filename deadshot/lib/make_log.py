# !/usr/bin/env python
# coding: utf-8

import datetime


def make_log(file_name, lines, last_time):
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")
    line = '[{}][{}]'.format()
    with open(file_name, 'w') as f:
        f.write()
