# !/usr/bin/env python
# coding: utf-8
import json
from deadshot.lib.deadshot_log import UsualLogging
from deadshot.lib.send_email import make_report, send_mail
import traceback
import requests
from deadshot.setting import *
from deadshot.shoters import RetryShot, SupervisorShot, UnknowShot

DeadShotLogger = UsualLogging('DeadShot')


def add_server_name(ctx):
    ctx.update({'server_name': SERVER_NAME})
    return ctx


class DeadShot(object):
    def __init__(self, **kwargs):
        """shot完之后回调self.callbacks，用于装饰"""

        # 实例化shoter
        self.retryshot_ins = RetryShot(**kwargs['supervisor_shot_ctx'])
        self.unknowshot_ins = UnknowShot(**kwargs['unknowshot_shot_ctx'])
        self.supervisorshot_ins = SupervisorShot()

        self.shoters = [
            self.retryshot_ins,
            self.unknowshot_ins,
            self.supervisorshot_ins
        ]

        # 每一个callback接受一个context字典,并返回一个context字典,用于装饰
        self.callbacks = [add_server_name]

    def get_shot(self):
        context = {}

        for shoter in self.shoters:
            context.update(shoter.shot())

        for callback in self.callbacks:
            context = callback(context)

        return context

    def run(self):
        return self.get_shot()


from flask import Flask

app = Flask(__name__)


@app.route('/')
def slave():
    p = DeadShot(
        supervisor_shot_ctx=(
            {'log_path': LOG_PATH,
             'filter_dirname_list': LOG_FILTER_DIR,
             'filter_filename_list': LOG_FILTER_FILE}),
        unknowshot_shot_ctx=({'log_path': UNKNOWN_LOG_PATH}),
    )
    result = p.run()
    return json.dumps(result)


def master():
    ctxs = []
    error_message = ''

    p = DeadShot(
        supervisor_shot_ctx=(
            {'log_path': LOG_PATH,
             'filter_dirname_list': LOG_FILTER_DIR,
             'filter_filename_list': LOG_FILTER_FILE}),
        unknowshot_shot_ctx=({'log_path': UNKNOWN_LOG_PATH}),
    )
    ctxs.append(p.run())

    for server_name, server_ip in SLAVE_IP.items():
        try_time = 0
        while try_time < RETRY_TIME:
            try:
                res = requests.get('http://' + server_ip + ':' + str(SLAVE_PORT))
            except Exception as e:
                traceback.print_exc()
                try_time += 1
                if try_time == RETRY_TIME:
                    error_message += "Reach the maximum retry.Server name:{}.\nErrInfo:{}\n".format(server_name, e)
                continue

            if res.status_code == 200:
                ctxs.append(json.loads(res.content))
                break

    content = make_report(ctxs, error_message)
    print content
    send_mail(content)


if __name__ == '__main__':
    if TYPE == 'slave':
        app.run(host='0.0.0.0', port=SLAVE_PORT)
    elif TYPE == 'master':
        master()
