# DeadShot

## 项目简介

本项目意在提供一个保险但不烦人的爬虫监控报警机制。通过监控supervisor或用户自定义的log等，从而达到及时通知用户失效爬虫的目的。

## 主要类与函数

#### DeadShot

Deadshot用与管理并执行所有的*shoter*以及*callback*。Deadshot实例化*shoter*并执行*shoter*的`shot()`方法获取所有*shoter*的*context*，最后将汇总的*context*作为参数依次调用*callback*。

*callback*相当于钩子函数，`self.callbacks`是一个由多个*callback*组成的钩子函数链。将所有*shoter*得到的*context*依次经过该函数链，从而达到特定的效果。



#### BaseShot及其子类

每一个*shoter*相当于一个监控项，例如一个*shoter*用于监控Supervisor的状态，另一个*shoter*用于监控RetryLog的数目。

每一个*shoter*必须重写`BaseShot`的`shot`方法，该方法通过读取文件，执行命令等过滤出需要报警的信息，返回一个字典，称其为*context*。*context*包含了用于报警邮件显示的各种信息。

一个SupervisorShoter的*context*如下：

```py
{"supervisor_result_context": [
    {
        "status": "STOPPED",
        "message": "Mar 17 09:59 AM",
        "name": "teddywalker_RL0079_2",
        "author": "lijiacong "
    },
    {
        "status": "STOPPED",
        "message": "Mar 17 09:02 PM",
        "name": "teddywalker_RL0105_3",
        "author": "PengYingZhi "
    },
    {
        "status": "STOPPED",
        "message": "Mar 20 09:28 AM",
        "name": "teddywalker_RL0120_1",
        "author": "wax8280 "
    }
]}
```



#### Callback

*callback*相当于钩子函数，其接受*shoter*处理完的*context*作为参数，进行必要的操作之后返回修改后的*context*

一个添加Server Name的*callback*如下：

```py
def add_server_name(ctx):
    ctx.update({'server_name': config['SERVER_NAME']})
    return ctx
```

运行前：

```py
{
    "unknown_result_context": [], 
    "retry_result_context": [], 
    "supervisor_result_context": [{
        "status": "STOPPED", 
        "message": "Mar 20 09:28 AM", 
        "name": "teddywalker_RL0120_1", 
        "author": "wax8280 "
    }]
}
```

运行后：

```py
{
    "unknown_result_context": [], 
    "retry_result_context": [], 
    "server_name": "spider6", 
    "supervisor_result_context": [{
        "status": "STOPPED", 
        "message": "Mar 20 09:28 AM", 
        "name": "teddywalker_RL0120_1", 
        "author": "wax8280 "
    }]
}
```



## 配置

### 配置文件

```
# slave与master分别表示从，主。
# slave会一直运行一个服务器在后台；master请求SLAVE_IP里所有的slave并进行整合与发送邮件
TYPE : 'master'

# master请求slave时失败的最大重试次数
MASTER_REQUSET_RETRY_TIME: 10

# slave的开放端口
SLAVE_PORT : 38383

# 用于master请求的slave主机ip列表
SLAVE_IP :
    'spider1': '120.25.222.158'
    'spider6': '120.25.122.61'
    'spdier7': '112.74.96.190'

# E-Mail模板文件的路径
E_MAIL_TEMPLATE_PATH : './deadshot/e_mail.html'

# Deadshot日志路径
DEADSHOT_LOG_PATH : './log/'

#　以下为Shoter设置
# ---------------- SupervisorShoter ----------------
# 不在次列表中的,都被视为异常状态
SUPERVISOR_NORMAL_STATUS :
    - 'RUNNING'

# 需要忽略的爬虫编号
SUPERVISOR_FILTERED_NAME :
    - 'teddywalker_RL_XM0001_1'

# 爬虫的supervisor log的路径。用于读取log用于判断爬虫是正常退出还是异常退出。
SPIDER_SUPERVISOR_LOG_PATH : ''
# ---------------- RetryShoter ----------------
# 爬虫retry日志的路径
RETRY_LOG_PATH : '/mnt/octopus/log'

# 需要过滤的文件夹与文件
RETRY_LOG_FILTER_DIR :
    - '_info$'
RETRY_LOG_FILTER_FILE :
    - '_info.log$'

# 查看日志的最后N行
RETRY_LAST_LINES : 500

# 当日志retry数达到RETRY_MAX_COUNT时发送警报
RETRY_MAX_COUNT: 500

# 最大通知超时时间
# 假设log里面最后一条retry log的时间为last_retry_log_time
# 当now - last_retry_log_time > RETRY_MAX_TIME　时发送警报
RETRY_MAX_TIME : 999999999

RETRY_PATTERN :
    'retry': '\[(.+?)\]\[(.+?)\] \[Retry\]'
    'process': '\[(.+?)\]\[(.+?)\] \[process\]'

# ---------------- UnknownShoter ------------------
# unkonwn log 的路径
UNKNOWN_LOG_PATH : '/mnt/octopus/log/_unknown'

# 最大通知超时时间　同上
UNKNOWN_MAX_TIME : 3600

UNKNOWN_PATTERN :
    'unknow': '\[(.+?)\]\[(.+?)\]'

# ----------------- SendEmail --------------------
PRIVATE_KEY : '1140923668'
TEMPLATE_NAME : 'spider'
EMAIL_API_URL : 'http://120.25.237.246:13150/api/5857cd86a542e930cc9c8dd5/emails'

# 以下为callback设置
# ----------------- add_author -------------------
SPIDER_SCRIPT_PATH : '/home/spider/teddywalker/teddywalker/spiders'
SPIDER_GIT_PATH : '/home/spider/teddywalker'

# ----------------- add_server_name --------------
SERVER_NAME : 'spider5'
```



### iptables防火墙配置

slave主机无验证系统，主要靠服务器防火墙建立白名单。

```py
// 请按顺序添加
sudo iptables -A INPUT -s 183.36.80.11 -p tcp --dport 38383 -j ACCEPT //添加master server为白名单
sudo iptables -A INPUT -p tcp --dport 38383 -j REJECT	//关闭38383端口
```



## 运行

### Slave

运行*deadshot*目录下的`start_slave_server.sh`即可，其使用Linux的`nohup`命令在后台运行服务。`nohup`为*flask*的输出，在*deadshot*里面的所有输出都记录在其，作辅助调试用。



### Master

添加定时任务

```
sudo crontab -u root -e
```

如，每小时执行一次

```
0 * * * * cd /home/spider/deadshot && /usr/bin/python ./deadshot.py
```

