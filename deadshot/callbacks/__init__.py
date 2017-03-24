# !/usr/bin/env python
# coding: utf-8
import deadshot.config
from deadshot.lib.file_lib import search_files
import subprocess
import re
import os


def add_server_name(ctx):
    ctx.update({'server_name': deadshot.config.config['SERVER_NAME']})
    return ctx


def add_author(ctx):
    reload(deadshot.config)
    config = deadshot.config.config

    for each_project_name in config['SPIDER_SCRIPT_PATH'].keys():
        # 获得该目录下所有不以"_"开头，并且以".py"结尾的文件路径
        files_path = search_files(config['SPIDER_SCRIPT_PATH'][each_project_name], [''], ['[^_].py$'])
        for each_file_path in files_path:
            command_ = "cd {} && git log -n 1 {}".format(config['SPIDER_GIT_PATH'][each_project_name], each_file_path)
            fh = subprocess.Popen(command_, stdout=subprocess.PIPE, shell=True)

            output = ''
            for i in fh.stdout.readlines():
                if i.startswith('Author'):
                    output = i
                    break

            if output:
                author = re.search('Author:\s+(.*)$', output).group(1)
            else:
                author = 'Anonymous'

            file_name = os.path.basename(each_file_path)
            for k, value_dict_list in ctx.items():
                for each_value_dict in value_dict_list:
                    if file_name.lower().replace('.py', '') in each_value_dict['name'].lower():
                        each_value_dict.update({'author': author.decode('utf-8')})
                    else:
                        if not each_value_dict.has_key('author'):
                            each_value_dict.update({'author': 'Anonymous'})
    return ctx
