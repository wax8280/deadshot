# !/usr/bin/env python
# coding: utf-8
import codecs
import json
import urllib

from deadshot.lib.template import Templite
from deadshot.lib.deadshot_log import UsualLogging
from deadshot.config import config

EmailShotLogger = UsualLogging('Email')


def make_report(ctxs, error_message):
    """将汇总的context添加server_name并渲染E-Mail模板"""
    content = {
        'error_message': error_message,
        'unknown_result_context': [],
        'supervisor_result_context': [],
        'retry_result_cont  ext': [],
    }
    for ctx in ctxs:
        for k, v in ctx.items():
            if k != 'server_name':
                content.setdefault(k, [])
                for each_v in v:
                    each_v.update({'server_name': ctx['server_name']})
                    content[k].append(each_v)

    # 读取并渲染模板
    with codecs.open(config['E_MAIL_TEMPLATE_PATH'], 'r', 'utf-8') as f:
        lines = f.readlines()
    template_email_body = Templite(u"".join(lines))
    text = template_email_body.render(content)
    EmailShotLogger.info(message='text:' + text)
    return text


def send_mail(content):
    """发送邮件"""
    d = json.dumps({'spider': content})
    parmas = urllib.urlencode(
        {'private_key': config['PRIVATE_KEY'], 'template_name': config['TEMPLATE_NAME'], 'params': d})
    try:
        r = urllib.urlopen(config['EMAIL_API_URL'], parmas)
        print r.code
    except Exception as e:
        EmailShotLogger.waring(message='cant send email.err_info: ' + str(e))
