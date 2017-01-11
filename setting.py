# !/usr/bin/env python
# coding: utf-8

LOG_PATH = './test_data/spider/'
# LOG_PATH = '/mnt/teddywalker/log'

FILTER_DIR = ['_info$']
FILTER_FILE = ['_info.log$']
DEADSHOT_LOG_PATH = './log/'

PATTERN = {
    'retry': '\[(.+?)\]\[(.+?)\] \[Retry\]',
    'process': '\[(.+?)\]\[(.+?)\] \[process\]'
}

WATCH_COUNT = 500
MAX_RETRY = 500

# 最大通知时间，在这之前的retry会发送邮件通知
MAX_TIME = float('inf')

PRIVATE_KEY = '1140923668'
TEMPLATE_NAME = 'spider'
EMAIL_API_URL = 'http://120.25.237.246:13150/api/5857cd86a542e930cc9c8dd5/emails'
