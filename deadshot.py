# !/usr/bin/env python
# coding: utf-8
import json
from deadshot.lib.deadshot_log import UsualLogging
from deadshot.lib.email import make_report, send_mail
import traceback
import requests
import deadshot.config
from deadshot.shoters import RetryShot, SupervisorShot, UnknowShot
from deadshot.callbacks import *
from flask import Flask

DeadShotLogger = UsualLogging('DeadShot')


class DeadShot(object):
    """
    实例化shoter并执行shoter的run()方法获取context，最后将context作为参数依次调用callback。
    callback相当于钩子函数，self.callbacks是一个由多个callback组成的钩子函数链。
    """

    def __init__(self, conf):
        """shot完之后回调self.callbacks，用于装饰"""

        # 实例化shoter
        self.retryshot_ins = RetryShot(conf)
        self.unknowshot_ins = UnknowShot(conf)
        self.supervisorshot_ins = SupervisorShot(conf)

        self.shoters = [
            self.retryshot_ins,
            self.unknowshot_ins,
            self.supervisorshot_ins
        ]

        # 每一个callback接受一个context字典,并返回一个context字典,用于装饰
        self.callbacks = [add_author, add_server_name]

    def get_shot(self):
        context = {}

        for shoter in self.shoters:
            context.update(shoter.shot())

        for callback in self.callbacks:
            context = callback(context)

        return context

    def run(self):
        return self.get_shot()


app = Flask(__name__)


@app.route('/')
def slave():
    reload(deadshot.config)
    p = DeadShot(deadshot.config.config)
    result = p.run()
    return json.dumps(result)


def master():
    ctxs = []
    error_message = ''

    p = DeadShot(deadshot.config.config)
    ctxs.append(p.run())

    for server_name, server_ip in deadshot.config.config['SLAVE_IP'].items():
        try_time = 0
        while try_time < deadshot.config.config['MASTER_REQUSET_RETRY_TIME']:
            try:
                res = requests.get('http://' + server_ip + ':' + str(deadshot.config.config['SLAVE_PORT']))
            except Exception as e:
                traceback.print_exc()
                try_time += 1
                if try_time == deadshot.config.config['MASTER_REQUSET_RETRY_TIME']:
                    error_message += "Reach the maximum retry.Server name:{}.\nErrInfo:{}\n".format(server_name, e)
                continue

            if res.status_code == 200:
                ctxs.append(json.loads(res.content))
                break

    content = make_report(ctxs, error_message)
    send_mail(content)
    print content.encode('utf-8')


if __name__ == '__main__':
    if deadshot.config.config['TYPE'] == 'slave':
        app.run(host='0.0.0.0', port=deadshot.config.config['SLAVE_PORT'])
    elif deadshot.config.config['TYPE'] == 'master':
        master()
