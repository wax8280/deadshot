# !/usr/bin/env python
# coding: utf-8
from deadshot.config import config
from deadshot.lib.file_lib import search_files
import subprocess
import re
import os


def add_server_name(ctx):
    ctx.update({'server_name': config['SERVER_NAME']})
    return ctx


def add_author(ctx):
    files_path = search_files(config['SPIDER_SCRIPT_PATH'], [''], ['[^_].py$'])
    for each_file_path in files_path:
        command_ = "cd {} && git log -n 1 {}".format(config['SPIDER_GIT_PATH'], each_file_path)
        fh = subprocess.Popen(command_, stdout=subprocess.PIPE, shell=True)
        author = re.search('Author:\s+(.*)$', list(fh.stdout.readlines())[1].strip()).group(1)

        file_name = os.path.basename(each_file_path)
        for k, value_dict_list in ctx.items():
            for each_value_dict in value_dict_list:
                if file_name.lower() in each_value_dict['name']:
                    each_value_dict.update({'author': author})
    return ctx
