#!/usr/bin/env python3
import ssl
import os

# 最激进的SSL禁用
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

# 导入lark
import lark_oapi as lark

# 测试连接
client = lark.Client.builder().app_id('cli_a93bbc2b02369bd6').app_secret('U3Njja1yPuc7Nqqz96Rl4bA74DUGpbl0').build()
handler = lark.EventDispatcherHandler.builder("", "").build()

print("启动WebSocket连接...")
cli = lark.ws.Client('cli_a93bbc2b02369bd6', 'U3Njja1yPuc7Nqqz96Rl4bA74DUGpbl0', event_handler=handler)
cli.start()
