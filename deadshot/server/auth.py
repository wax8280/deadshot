# !/usr/bin/env python
# coding: utf-8

import hmac
import os

def client_authenticate(connection, secret_key):
    '''
    接受服务器发送的32byte加密字符串，用secret_key加密后发回服务器
    secret_key 是客户端与服务器都知道
    '''
    message = connection.recv(32)
    hash = hmac.new(secret_key, message)
    digest = hash.digest()
    connection.send(digest)

def server_authenticate(connection, secret_key):
    '''
    随机生成32byte字符串，以secret_key加密后发送给客户端
    '''
    message = os.urandom(32)
    connection.send(message)
    hash = hmac.new(secret_key, message)
    digest = hash.digest()
    response = connection.recv(len(digest))
    return hmac.compare_digest(digest,response)
