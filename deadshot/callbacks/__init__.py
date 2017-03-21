# !/usr/bin/env python
# coding: utf-8
from deadshot.config import config


def add_server_name(ctx):
    ctx.update({'server_name': config['SERVER_NAME']})
    return ctx