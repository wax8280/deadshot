# !/usr/bin/env python
# coding: utf-8
import os
import re
import subprocess
import time
from collections import OrderedDict

from deadshot.lib.file_lib import FileIO
from deadshot.lib.deadshot_log import UsualLogging
from deadshot.setting import *

RetryShotLogger = UsualLogging('RetryShot')
SupervisorShotLogger = UsualLogging('SupervisorShot')
ProcessLogger = UsualLogging('Process')


class BaseShot(object):
    def count_linebase(self, file_path, pattern, num=100):
        """
        从文件后面开始读取num行，统计log中错误与成功的数目
        >>> RetryShot.count_linebase('./test_data/spider/huskywalker/RL0066')
        {'RL0066': OrderedDict([('process_count', 78), ('process_last_time', '2017-01-07 10:22:31,000'), ('retry_count', 22), ('retry_last_time', '2016-12-27 20:30:49,973')])}

        :param file_path:   string
        :param num:         int
        :return:            dict
        """
        lines = FileIO.read_last_lines(file_path, num)
        file_name = os.path.basename(file_path)
        result = {file_name: OrderedDict()}
        for name, pattern in pattern.items():
            # got 表示符合当前pattern的line
            got = []

            for line in lines:
                if re.search(pattern, line):
                    got.append(re.search(pattern, line).groups())

            if got:
                # -1 表示最后一行; 0 表示时间
                last_time = got[-1][0]
                count = len(got)

                result[file_name].setdefault(name + '_count', count)
                result[file_name].setdefault(name + '_last_time', last_time)
            else:
                result[file_name].setdefault(name + '_count', 0)
        return result

    def check_last(self, file_path, pattern, time_interval=3600):
        """
        从文件后面开始读取，满足time.time() - last_log_time < time_interval的行，返回True
        """
        last_line = FileIO.read_last_lines(file_path, 1)[0]
        file_name = os.path.basename(file_path)
        result = None
        for name, pattern in pattern.items():
            if re.search(pattern, last_line):
                last_time = re.search(pattern, last_line).groups()[0]
                diff_time = time.time() - time.mktime(time.strptime(last_time, "%Y-%m-%d %H:%M:%S,%f"))

                # time_interval之内
                if diff_time < time_interval:
                    result = {file_name: (name, last_time)}
        return result

    # def count_timebase(self, file_path, num=500, time_interval=3600):
    #     """
    #     从文件后面开始读取满足time.time() - log_time < time_interval的行，统计log中错误与成功的数目
    #     """
    #
    #     lines = FileIO.read_last_lines(file_path, num)
    #     file_name = os.path.basename(file_path)
    #     result = {file_name: OrderedDict()}
    #
    #     for name, pattern in self.pattern.items():
    #         last_time = re.search(pattern, lines[0]).groups()[-1][0]
    #         diff_time = time.time() - time.mktime(time.strptime(last_time, "%Y-%m-%d %H:%M:%S,%f"))
    #
    #         # time_interval之内
    #         if diff_time < time_interval:
    #             # got 表示符合当前pattern的line
    #             got = []
    #             for line in lines:
    #                 if re.search(pattern, line):
    #                     got.append(re.search(pattern, line).groups())
    #             if got:
    #                 # -1 表示最后一行; 0 表示时间
    #                 last_time = got[-1][0]
    #                 count = len(got)
    #
    #                 result[file_name].setdefault(name + '_count', count)
    #                 result[file_name].setdefault(name + '_last_time', last_time)
    #             else:
    #                 result[file_name].setdefault(name + '_count', 0)
    #     return result

    def shot(self):
        pass


class UnknowShot(BaseShot):
    name = 'unknown_result_context'

    def __init__(self, log_path, filter_dirname_list=[''], filter_filename_list=[''], unknown_time_interval=3600,
                 pattern=UNKNOWN_PATTERN):
        """

        :param log_path:                日志所在的文件夹        '/mnt/teddywalker/log'
        :param filter_dirname_list:     需要监控的文件夹名字      ['_info$']
        :param filter_filename_list:    需要监控的文件名字       ['_info.log$']
        """
        self.pattern = pattern
        self.log_path = log_path
        self.filter_dirname_list = filter_dirname_list
        self.filter_filename_list = filter_filename_list
        # 根据筛选条件，得出符合条件的文件路径
        self.file_list = FileIO.search_files(self.log_path, self.filter_dirname_list, self.filter_filename_list)
        self.unknown_time_interval = unknown_time_interval

        """
        self.unknown_result_list data structure
        [
            {'spider_name':(pattern_name, last_time)}
            ...
        ]
        """
        self.unknown_result_list = []
        for each_file in self.file_list:
            r = self.check_last(each_file, self.pattern, self.unknown_time_interval)
            if r:
                self.unknown_result_list.append(r)

    def shot(self):
        ctx = {self.name: []}

        for each in self.unknown_result_list:
            for spider_name, item in each.items():
                pattern_name, last_time = item
                ctx[self.name].append({
                    'name': spider_name,
                    'pattern_name': pattern_name,
                    'last_time': last_time,
                })
        return ctx


class RetryShot(BaseShot):
    pattern = PATTERN
    name = 'retry_result_context'

    def __init__(self, log_path, filter_dirname_list, filter_filename_list):
        """
        :param log_path:                日志所在的文件夹        '/mnt/teddywalker/log'
        :param filter_dirname_list:     需要监控的文件夹名字      ['_info$']
        :param filter_filename_list:    需要监控的文件名字       ['_info.log$']
        """
        self.log_path = log_path
        self.filter_dirname_list = filter_dirname_list
        self.filter_filename_list = filter_filename_list
        # 根据筛选条件，得出符合条件的文件路径
        self.file_list = FileIO.search_files(self.log_path, self.filter_dirname_list, self.filter_filename_list)

        # 分析所有相关文件的最后 WATCH_COUNT 行
        # 按照 retry_count 排序
        self.retry_result_list = sorted(
            [self.count_linebase(each_file, self.pattern, WATCH_COUNT) for each_file in self.file_list],
            key=lambda x: x[x.keys()[0]]['retry_count'], reverse=True)

    def shot(self):
        ctx = {self.name: []}
        for each in self.retry_result_list:
            for spider_name, v in each.items():

                # 找出 retry 大于　MAX_RETRY　的
                if v['retry_count'] >= MAX_RETRY:
                    diff_time = time.time() - time.mktime(time.strptime(v['retry_last_time'], "%Y-%m-%d %H:%M:%S,%f"))
                    ProcessLogger.info(message='[debug] now_time - last_retry_time:' + str(diff_time))
                    # 时间差大于MAX_TIME
                    if diff_time < MAX_TIME:
                        ctx[self.name].append({
                            'name': spider_name,
                            'count': v['retry_count'],
                            'time': v['retry_last_time']
                        })
        ProcessLogger.info(message='retry_result_list: ' + str(ctx[self.name]))
        return ctx


class SupervisorShot(BaseShot):
    name = 'supervisor_result_context'

    def __init__(self):
        self.supervisor_result_list = self.get_status()

    def get_status(self):
        result = []
        command_ = "sudo supervisorctl status"
        fh = subprocess.Popen(command_, stdout=subprocess.PIPE, shell=True)

        for i in fh.stdout.readlines():
            grp = re.search('([\d\w]+?)[\s]+?([\d\w]+?)[\s]+(.*?)\n', i)
            result.append(
                {
                    'name': grp.group(1),
                    'status': grp.group(2),
                    'message': re.sub('pid [\d]+, ', '', grp.group(3)),
                }
            )
        return result

    def shot(self):
        ctx = {self.name: []}
        for each in self.supervisor_result_list:
            if (
                            each['status'] not in SUPERVISOR_NORMAL_STATUS
                    and each['name'] not in SUPERVISOR_FILTERED_NAME \
                    ):
                ctx[self.name].append(each)

        return ctx