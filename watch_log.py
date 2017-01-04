# !/usr/bin/env python
# coding: utf-8
import subprocess
import os
import re
from collections import OrderedDict
from setting import *
import smtplib
from email.mime.text import MIMEText
from email.header import Header

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

        >>> list(os.walk('/home/vincent/spider'))
        [('/home/vincent/spider', ['teddywalker', 'huskywalker'], []), ('/home/vincent/spider/teddywalker', [], ['ZY00983']), ('/home/vincent/spider/huskywalker', [], ['RL0012', 'RL0066', 'YH0082'])]
        >>> FileIO.search_files('/home/vincent/spider',['teddywalker','huskywalker'],['RL','ZY'])
        ['/home/vincent/spider/teddywalker/ZY00983', '/home/vincent/spider/huskywalker/RL0012', '/home/vincent/spider/huskywalker/RL0066']
        >>> FileIO.search_files('/home/vincent/spider', ['teddywalker', 'huskywalker'], [''])
        ['/home/vincent/spider/teddywalker/ZY00983', '/home/vincent/spider/huskywalker/RL0012', '/home/vincent/spider/huskywalker/RL0066', '/home/vincent/spider/huskywalker/YH0082']
        >>> FileIO.search_files('/home/vincent/spider', [''], [''])
        ['/home/vincent/spider/teddywalker/ZY00983', '/home/vincent/spider/huskywalker/RL0012', '/home/vincent/spider/huskywalker/RL0066', '/home/vincent/spider/huskywalker/YH0082']

        你也可以使用正则，如，搜索目录下所有目录以walker结尾，文件以Ｒ开头并且以数字结尾的文件
        >>> FileIO.search_files('/home/vincent/spider', ['walker$'], ['R.*?\d+$'])
        ['/home/vincent/spider/huskywalker/RL0012', '/home/vincent/spider/huskywalker/RL0066']

        :param log_path:            string
        :param filter_filename:     list
        :param filer_dirname:       list
        :return:                    list
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


class Process(object):
    def __init__(self, log_path, filter_dirname_list, filter_filename_list, pattern):
        self.log_path = log_path
        self.filter_dirname_list = filter_dirname_list
        self.filter_filename_list = filter_filename_list
        self.pattern = pattern

    def check_log(self, file_path, num=100):
        """
        统计log中错误与成功的数目

        >>> p = Process('/home/vincent/Documents/git_clone/teddywalker/log', ['_info$'], ['_info.log$'], PATTERN)
        >>> p.check_log('/home/vincent/Documents/git_clone/teddywalker/log/RL0067_info/RL0067_info.log')
        {'RL0067_info.log': OrderedDict([('count_process', 77), ('last_time_process', '2016-12-27 16:15:59,962'), ('count_retry', 23), ('last_time_retry', '2016-12-27 20:30:49,973')])}

        :param file_path:   string
        :param num:         int
        :return:            dict
        """
        lines = FileIO.read_last_lines(file_path, num)
        # 以文件名作为key
        file_name = os.path.basename(file_path)

        result = {file_name: OrderedDict()}

        for name, pattern in self.pattern.items():
            got = []

            for line in lines:
                if re.search(pattern, line):
                    got.append(re.search(pattern, line).groups())

            if got:
                last_time = got[-1][0]
                count = len(got)

                result[file_name].setdefault(name + '_count', count)
                result[file_name].setdefault(name + '_last_time', last_time)
            else:
                result[file_name].setdefault(name + '_count', 0)

        return result

    @staticmethod
    def make_report(result_list):
        content = ''
        for each in result_list:
            for spider_name, v in each.items():

                # 找出 retry 大于　MAX_RETRY　的
                if v['retry_count'] >= MAX_RETRY:
                    content += spider_name + ' retry_count: ' + str(v['retry_count']) + ' last_time: ' \
                               + v['retry_last_time'] + '\n'
        return content

    @staticmethod
    def send_mail(content):
        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = Header("Teddywalker", 'utf-8')
        message['To'] = Header("Teddywalker", 'utf-8')
        message['Subject'] = Header('Teddywalker Watching', 'utf-8')

        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(MAIL_HOST, 25)  # SMTP
            smtpObj.login(MAIL_USER, MAIL_PASS)
            smtpObj.sendmail(SENDER, RECEIVERS, message.as_string())
        except Exception as e:
            print 'failed to send email'

    def run(self):
        # 搜索目录以及子目录下相关的文件
        file_list = FileIO.search_files(self.log_path, self.filter_dirname_list, self.filter_filename_list)

        # 读取所有相关文件的最后WATCH_COUNT行
        result = []
        for each_file in file_list:
            result.append(self.check_log(each_file, WATCH_COUNT))

        # 按照retry_count 排序
        rows_by_retey = sorted(result, key=lambda x: x[x.keys()[0]]['retry_count'], reverse=True)
        report = self.make_report(rows_by_retey)

        print report
        self.send_mail(report)

if __name__ == '__main__':
    p = Process(LOG_PATH, FILTER_DIR, FILTER_FILE, PATTERN)
    p.run()
