# !/usr/bin/env python
# coding: utf-8
import json
from deadshot.lib.deadshot_log import UsualLogging
from deadshot.lib.send_email import make_report
from deadshot.setting import *
from deadshot.shoters import RetryShot, SupervisorShot, UnknowShot

DeadShotLogger = UsualLogging('DeadShot')


def add_server_name(ctx):
    return ctx.update({'server_name': SERVER_NAME})


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


if __name__ == '__main__':
    if TYPE == 'slave':
        app.run(host='0.0.0.0', port=38383)
    else:
        pass
