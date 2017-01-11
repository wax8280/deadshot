# !/usr/bin/env python
# coding: utf-8
import codecs
import json
import os
import time
import urllib
import re
from collections import OrderedDict
import subprocess

from lib.template import Templite
from lib.file_lib import FileIO
from setting import *


class RetryShot(object):
    pattern = PATTERN

    @staticmethod
    def shot(file_path, num=100):
        """
        统计log中错误与成功的数目

        >>> RetryShot.shot('./test_data/spider/huskywalker/RL0066')
        {'RL0066': OrderedDict([('process_count', 78), ('process_last_time', '2017-01-07 10:22:31,000'), ('retry_count', 22), ('retry_last_time', '2016-12-27 20:30:49,973')])}

        :param file_path:   string
        :param num:         int
        :return:            dict
        """
        lines = FileIO.read_last_lines(file_path, num)
        # 以文件名作为key
        file_name = os.path.basename(file_path)

        result = {file_name: OrderedDict()}

        for name, pattern in RetryShot.pattern.items():
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


class SupervisorShot(object):
    @staticmethod
    def shot(file_path, num=100):
        command_ = "supervisorctl status"
        fh = subprocess.Popen(command_, stdout=subprocess.PIPE, shell=True)
        return list(fh.stdout.readlines())


class Process(object):
    def __init__(self, log_path, filter_dirname_list, filter_filename_list):
        self.log_path = log_path
        self.filter_dirname_list = filter_dirname_list
        self.filter_filename_list = filter_filename_list

    @staticmethod
    def make_report(**kwargs):
        context = {}

        # -------------------检查retry----------------------------------
        retry_result_context = []

        if kwargs.has_key('retry_result_list'):
            for each in kwargs['retry_result_list']:
                for spider_name, v in each.items():

                    # 找出 retry 大于　MAX_RETRY　的
                    if v['retry_count'] >= MAX_RETRY:
                        print '[debug] now_time - last_retry_time:' + str(
                            time.time() - time.mktime(time.strptime(v['retry_last_time'], "%Y-%m-%d %H:%M:%S,%f")))
                        if time.time() - time.mktime(
                                time.strptime(v['retry_last_time'], "%Y-%m-%d %H:%M:%S,%f")) < MAX_TIME:
                            retry_result_context.append(
                                {'name': spider_name, 'count': v['retry_count'], 'time': v['retry_last_time']})
        context.update({'retry_result_context': retry_result_context})
        # TODO
        # ------------------检查Supervisor----------------------------

        if context:
            # 读取并渲染模板
            with codecs.open(r'./e_mail.html', 'r', 'utf-8') as f:
                lines = f.readlines()
            template_email_body = Templite(u"".join(lines))
            text = template_email_body.render(context)
            return text
        else:
            return None

    @staticmethod
    def send_mail(content):
        d = json.dumps({'spider': content})
        parmas = urllib.urlencode({'private_key': PRIVATE_KEY, 'template_name': TEMPLATE_NAME, 'params': d})
        try:
            r = urllib.urlopen(EMAIL_API_URL, parmas)
            print r.code
        except Exception as e:
            print 'failed to send email.status code{}'.format(r.code)

    def run(self):
        # -------------------start 检查retry----------------------------------

        # 搜索目录以及子目录下相关的文件
        file_list = FileIO.search_files(self.log_path, self.filter_dirname_list, self.filter_filename_list)

        # 分析所有相关文件的最后 WATCH_COUNT 行
        result = []
        for each_file in file_list:
            result.append(RetryShot.shot(each_file, WATCH_COUNT))

        # 按照 retry_count 排序
        rows_by_retey = sorted(result, key=lambda x: x[x.keys()[0]]['retry_count'], reverse=True)

        # -------------------end 检查retry----------------------------------


        # ------------------start 检查Supervisor----------------------------

        # ------------------end 检查Supervisor----------------------------


        content = self.make_report(retry_result_list=rows_by_retey)
        if content:
            print content
            self.send_mail(content)


if __name__ == '__main__':
    p = Process(LOG_PATH, FILTER_DIR, FILTER_FILE)
    p.run()
