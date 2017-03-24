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
    all_project_name = set()

    # 获取supervisor所有project name
    for context_name, value_list in ctx.items():
        for value in value_list:
            project_name = value['name'].split('_')[0]
            all_project_name.add(project_name)

    for each_project_name in all_project_name:
        # 获得该目录下所有不以"_"开头，并且以".py"结尾的文件路径
        files_path = search_files(config['SPIDER_SCRIPT_PATH'][each_project_name], [''], ['[^_].py$'])
        for each_file_path in files_path:
            command_ = "cd {} && git log -n 1 {}".format(config['SPIDER_GIT_PATH'][each_project_name], each_file_path)
            fh = subprocess.Popen(command_, stdout=subprocess.PIPE, shell=True)
            author = re.search('Author:\s+(.*)$', list(fh.stdout.readlines())[1].strip()).group(1)

            file_name = os.path.basename(each_file_path)
            for k, value_dict_list in ctx.items():
                for each_value_dict in value_dict_list:
                    if file_name.lower().replace('.py', '') in each_value_dict['name'].lower():
                        each_value_dict.update({'author': author.decode('utf-8')})
                    else:
                        each_value_dict.update({'author': 'Anonymous'})
    return ctx