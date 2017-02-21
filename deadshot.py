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
import datetime
from copy import deepcopy

from lib.template import Templite
from lib.file_lib import FileIO
from lib.deadshot_log import UsualLogging
from setting import *

RetryShotLogger = UsualLogging('RetryShot')
SupervisorShotLogger = UsualLogging('SupervisorShot')
ProcessLogger = UsualLogging('Process')


class RetryShot(object):
    pattern = PATTERN

    @staticmethod
    def count(file_path, num=100):
        """
        统计log中错误与成功的数目

        >>> RetryShot.count('./test_data/spider/huskywalker/RL0066')
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

    @staticmethod
    def shot(retry_result_list):
        retry_result_context = []

        for each in retry_result_list:
            for spider_name, v in each.items():

                # 找出 retry 大于　MAX_RETRY　的
                if v['retry_count'] >= MAX_RETRY:
                    diff_time = time.time() - time.mktime(
                        time.strptime(v['retry_last_time'], "%Y-%m-%d %H:%M:%S,%f"))
                    ProcessLogger.info(message='[debug] now_time - last_retry_time:' + str(diff_time))
                    if diff_time < MAX_TIME:
                        retry_result_context.append(
                            {'name': spider_name, 'count': v['retry_count'], 'time': v['retry_last_time']})

        return retry_result_context


class SupervisorShot(object):
    @staticmethod
    def get_status():
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

    @staticmethod
    def shot(supervisor_result_list):
        return [each for each in supervisor_result_list
                if each['status'] not in SUPERVISOR_NORMAL_STATUS and each['name'] not in SUPERVISOR_FILTERED_NAME]


class Process(object):
    def __init__(self, log_path, filter_dirname_list, filter_filename_list, sended_list_filename):
        self.log_path = log_path
        self.filter_dirname_list = filter_dirname_list
        self.filter_filename_list = filter_filename_list
        self.sended_filename = sended_list_filename

        with open(self.sended_filename, 'r') as f:
            self.sended = json.load(f)

    def just_send_new(self, context):
        new_sended = deepcopy(self.sended)
        to_send = {'fixed_context': []}

        # 如在之前失败的，但是如今running（比如bug已经修复了），就要从sended列表里面去掉
        for k, v in new_sended.items():
            if new_sended[k]:
                # 注意:要更新Python的list，推荐使用切片
                for each in new_sended[k][:]:
                    # context 里面保存这次失败的爬虫
                    if each not in str(context[k]):
                        new_sended[k].remove(each)
                        to_send['fixed_context'].append(each)

        if datetime.datetime.now().hour == ALL_SEND_TIME:
            to_send = context
            for k, w in context.items():
                for each in context[k]:
                    new_sended[k].append(each['name'])
        else:
            for k, w in context.items():
                to_send.update({k: []})
                for each in context[k]:
                    # 没发送过的
                    if each['name'] not in self.sended[k]:
                        to_send[k].append(each)
                        # 添加到sended列表里面
                        new_sended[k].append(each['name'])

        # 写入文件
        with open(self.sended_filename, 'w') as f:
            json.dump(new_sended, f)

        return to_send

    def get_shot(self, callback=None, **kwargs):
        context = {}

        # -------------------检查retry----------------------------------
        if kwargs.has_key('retry_result_list'):
            retry_result_context = RetryShot.shot(kwargs['retry_result_list'])
            ProcessLogger.info(message='retry_result_list: ' + str(retry_result_context))
            context.update({'retry_result_context': retry_result_context})

        # ------------------检查Supervisor----------------------------
        if kwargs.has_key('supervisor_result_list'):
            supervisor_result_context = SupervisorShot.shot(kwargs['supervisor_result_list'])
            ProcessLogger.info(message='supervisor_result_context: ' + str(supervisor_result_context))
            context.update({'supervisor_result_context': supervisor_result_context})

        if callback:
            return callback(context)

    @staticmethod
    def make_report(context):
        for k, v in context.items():
            # 如果有一个不为空
            if context[k]:
                # 读取并渲染模板
                with codecs.open(E_MAIL_TEMPLATE_PATH, 'r', 'utf-8') as f:
                    lines = f.readlines()
                template_email_body = Templite(u"".join(lines))
                text = template_email_body.render(context)
                ProcessLogger.info(message='text:' + text)
                return text

    @staticmethod
    def send_mail(content):
        d = json.dumps({'spider': content})
        parmas = urllib.urlencode({'private_key': PRIVATE_KEY, 'template_name': TEMPLATE_NAME, 'params': d})
        try:
            r = urllib.urlopen(EMAIL_API_URL, parmas)
            print r.code
        except Exception as e:
            ProcessLogger.waring(message='cant send email.err_info: ' + str(e))

    def run(self):
        # -------------------start 检查retry----------------------------------

        # 搜索目录以及子目录下相关的文件
        file_list = FileIO.search_files(self.log_path, self.filter_dirname_list, self.filter_filename_list)

        # 分析所有相关文件的最后 WATCH_COUNT 行
        # 按照 retry_count 排序
        rows_by_retey = sorted([RetryShot.count(each_file, WATCH_COUNT) for each_file in file_list],
                               key=lambda x: x[x.keys()[0]]['retry_count'], reverse=True)

        # ------------------start 检查Supervisor----------------------------
        supervisor_result_list = SupervisorShot.get_status()

        ctx = self.get_shot(retry_result_list=rows_by_retey,
                            supervisor_result_list=supervisor_result_list,
                            callback=self.just_send_new)
        content = self.make_report(ctx)

        if content:
            print content
            self.send_mail(content)


if __name__ == '__main__':
    p = Process(LOG_PATH, FILTER_DIR, FILTER_FILE, SENDED_LOGFILE)
    p.run()
