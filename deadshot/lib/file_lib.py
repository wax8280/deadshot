# !/usr/bin/env python
# coding: utf-8
import subprocess
import re
import os


class FileIO(object):
    @staticmethod
    def read_last_lines(file_path, num):
        """
        调用　linux 中的　tail 去从后面读取文件

        >>> FileIO.read_last_lines('~/Documents/git_clone/teddywalker/log/RL0064_info/RL0064_info.log', 3)
        ['[2016-12-28 09:38:06,072][RL0064_info] [process] 200 http://wsgs.fjaic.gov.cn/webquery/basicQuery.do?method=list&loginId= search_name: 350400900000009 error_count: 9 thread: 1\n', '[2016-12-28 09:38:06,158][RL0064_info] [process] 200 http://wsgs.fjaic.gov.cn/webquery/basicQuery.do?method=list&loginId= search_name: 350825000000032 error_count: 0 thread: 0\n', '[2016-12-28 09:38:06,754][RL0064_info] [process] 200 http://wsgs.fjaic.gov.cn/webquery/basicQuery.do?method=list&loginId= search_name: 350602200000006 error_count: 2 thread: 4\n']

        :param file_path:       string
        :param num:             int
        :return:                list
        """
        command_ = "tail -n {num} {file_path}".format(num=num, file_path=file_path)

        fh = subprocess.Popen(command_, stdout=subprocess.PIPE, shell=True)
        return list(fh.stdout.readlines())

    @staticmethod
    def search_files(log_path, filter_dirname_list=None, filter_filename_list=None):
        """
        遍历 log_path　目录下的所有文件，并根据filer_dirname与filter_filename　过滤出符合的文件

        >>> list(os.walk('../test_data/spider'))
        [('../test_data/spider', ['teddywalker', 'huskywalker'], []), ('../test_data/spider/teddywalker', [], ['ZY00983']), ('../test_data/spider/huskywalker', [], ['RL0012', 'RL0066', 'YH0082'])]
        >>> FileIO.search_files('../test_data/spider',['teddywalker','huskywalker'],['RL','ZY'])
        ['../test_data/spider/teddywalker/ZY00983', '../test_data/spider/huskywalker/RL0012', '../test_data/spider/huskywalker/RL0066']
        >>> FileIO.search_files('../test_data/spider', ['teddywalker', 'huskywalker'], [''])
        ['../test_data/spider/teddywalker/ZY00983', '../test_data/spider/huskywalker/RL0012', '../test_data/spider/huskywalker/RL0066', '../test_data/spider/huskywalker/YH0082']
        >>> FileIO.search_files('../test_data/spider', [''], [''])
        ['../test_data/spider/teddywalker/ZY00983', '../test_data/spider/huskywalker/RL0012', '../test_data/spider/huskywalker/RL0066', '../test_data/spider/huskywalker/YH0082']

        你也可以使用正则，如，搜索目录下所有目录以walker结尾，文件以Ｒ开头并且以数字结尾的文件
        >>> FileIO.search_files('../test_data/spider', ['walker$'], ['R.*?\d+$'])
        ['../test_data/spider/huskywalker/RL0012', '../test_data/spider/huskywalker/RL0066']

        :param log_path:                    string
        :param filter_dirname_list:         list
        :param filter_filename_list:        list
        :return:                            list
        """
        file_walker = os.walk(log_path)

        filter_dirname_list = [] if filter_dirname_list is None else filter_dirname_list
        filter_filename_list = [] if filter_filename_list is None else filter_filename_list

        file_list = []
        for item in file_walker:
            # 如果存在文件
            if item[0] and item[2]:
                filtered = True
                dir_name = item[0].replace(log_path, '')

                for filter_dirname in filter_dirname_list:
                    if re.search(filter_dirname, dir_name):
                        filtered = False
                        break

                if not filtered:
                    for each_file in item[2]:
                        for filter_filename in filter_filename_list:
                            if re.search(filter_filename, each_file):
                                file_list.append(os.path.join(item[0], each_file))
        return file_list
