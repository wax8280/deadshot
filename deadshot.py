# !/usr/bin/env python
# coding: utf-8
import datetime
import json
from copy import deepcopy
import os

from deadshot.lib.deadshot_log import UsualLogging
from deadshot.lib.send_email import make_report
from deadshot.setting import *
from deadshot.shoters import RetryShot, SupervisorShot, UnknowShot

DeadShotLogger = UsualLogging('DeadShot')


class DeadShot(object):
    def __init__(self, sended_list_filename, **kwargs):
        self.sended_filename = sended_list_filename

        self.retryshot_ins = RetryShot(**kwargs['supervisor_shot_ctx'])

        self.unknowshot_ins = UnknowShot(**kwargs['unknowshot_shot_ctx'])

        self.supervisorshot_ins = SupervisorShot()

    def just_send_new(self, context):

        if os.path.exists(self.sended_filename):
            with open(self.sended_filename, 'r') as f:
                sended = json.load(f)
        else:
            sended = {"retry_result_context": [], "supervisor_result_context": []}

        new_sended = deepcopy(sended)
        nex_context = {'fixed_context': []}

        # 如在之前失败的，但是如今running（比如bug已经修复了），就要从sended列表里面去掉
        for k, v in new_sended.items():
            if new_sended[k]:
                # 注意:要更新Python的list，推荐使用切片
                for each in new_sended[k][:]:
                    # context 里面保存这次失败的爬虫
                    if each not in str(context[k]):
                        new_sended[k].remove(each)
                        nex_context['fixed_context'].append(each)

        # 发送全部消息
        if datetime.datetime.now().hour in ALL_SEND_TIME:
            nex_context = context
            nex_context.update({'fixed_context': []})
            for k, w in context.items():
                for each in context[k]:
                    new_sended[k].append(each['name'])
        else:
            for k, w in context.items():
                nex_context.update({k: []})
                for each in context[k]:
                    # 没发送过的
                    if each['name'] not in sended[k]:
                        nex_context[k].append(each)
                        # 添加到sended列表里面
                        new_sended[k].append(each['name'])

        # 写入文件
        for k, v in new_sended.items():
            if new_sended[k]:
                new_sended[k] = list(set(new_sended[k]))
        with open(self.sended_filename, 'w') as f:
            json.dump(new_sended, f)

        return nex_context

    def get_shot(self, callback=None):
        context = {}

        context.update(self.supervisorshot_ins.shot())
        context.update(self.retryshot_ins.shot())
        context.update(self.unknowshot_ins.shot())

        if callback:
            return callback(context)

    def run(self):
        ctx = self.get_shot(callback=self.just_send_new)

        content = make_report(ctx)
        if content:
            print content
            # send_mail(content)


if __name__ == '__main__':
    p = DeadShot(
        SENDED_LOGFILE,
        supervisor_shot_ctx=(
            {'log_path': LOG_PATH,
             'filter_dirname_list': LOG_FILTER_DIR,
             'filter_filename_list': LOG_FILTER_FILE}),
        unknowshot_shot_ctx=({'log_path': UNKNOWN_LOG_PATH}),
    )
    p.run()
