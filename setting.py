# !/usr/bin/env python
# coding: utf-8

LOG_PATH = '/home/vincent/Documents/git_clone/teddywalker/log'
FILTER_DIR = ['_info$']
FILTER_FILE = ['_info.log$']

PATTERN = {
    'retry': '\[(.+?)\]\[(.+?)\] \[Retry\]',
    'process': '\[(.+?)\]\[(.+?)\] \[process\]'
}

WATCH_COUNT = 1000
MAX_RETRY = 1000

SENDER = '153402996@qq.com'
RECEIVERS = ['153402996@qq.com']

MAIL_HOST = "smtp.qq.com"
MAIL_USER = "153402996@qq.com"
MAIL_PASS = ""
