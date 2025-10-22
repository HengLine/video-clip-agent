#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@FileName: app_flask.py
@Description: Flask应用入口
@Author: HengLine
@Time: 2025/08 - 2025/11
"""

# 然后导入其他标准库和第三方库
import os
import signal
import sys
import time

from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入自定义日志模块
from hengline.logger import debug, info
from config.config import get_flask_secret_key, get_settings_config, get_model_dir

# 初始化Flask应用
# 使用绝对路径来确保模板正确加载
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.config['JSON_AS_ASCII'] = False  # 允许非ASCII字符
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)

# 从配置模块导入辅助方法
from config.config import get_upload_dir, get_output_dir, get_temp_dir, get_allowed_extensions

# 使用配置模块中的辅助方法获取各种目录的绝对路径
UPLOAD_FOLDER = get_upload_dir()
OUTPUT_FOLDER = get_output_dir()
MODEL_DIR = get_model_dir()
ALLOWED_EXTENSIONS = get_allowed_extensions()

# 日志记录目录配置，帮助调试
debug(f"上传目录配置为: {UPLOAD_FOLDER}")
debug(f"输出目录配置为: {OUTPUT_FOLDER}")
debug(f"模型目录配置为: {MODEL_DIR}")
debug(f"允许的文件扩展名: {ALLOWED_EXTENSIONS}")

# 从配置工具获取Flask配置
app.secret_key = get_flask_secret_key()

# 初始化智能体编排器并存储到应用配置中
from hengline.agent.langgraph_orchestrator import LangGraphOrchestrator
agent_graph = LangGraphOrchestrator()
app.config['agent_graph'] = agent_graph
info(f"成功加载基于langgraph的智能体编排器，可用智能体: {', '.join(agent_graph.get_available_agents())}")

# 导入路由初始化模块
from hengline.flask.route import init_routes

# 初始化所有路由
init_routes(app)


def handle_shutdown(signum, frame):
    """处理终止信号的回调函数"""

    info("服务正在关闭，请稍等片刻......")

    # 等待一段时间让异步关闭有时间完成
    time.sleep(1)

    # 在信号处理上下文中，我们不应该尝试通过request.environ获取shutdown函数
    # 因为此时没有活跃的HTTP请求上下文，直接退出程序
    sys.exit(0)


def run_flask_app():
    """\在独立函数中运行Flask应用，便于信号处理"""
    try:
        # 直接使用Flask内置服务器启动应用（不使用SocketIO）
        info("使用Flask内置服务器启动应用...")
        app.run(
            debug=True,
            host='0.0.0.0',
            port=8000,
            use_reloader=False
        )
    except KeyboardInterrupt:
        info("Flask应用被用户中断")
        handle_shutdown(None, None)


if __name__ == '__main__':
    # 注册信号处理函数
    if sys.platform != 'win32':  # Linux/Mac系统
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
        info("已设置Linux/Mac平台信号处理器")
    else:  # Windows系统的信号处理
        # 对于Windows平台，采用更简单直接的方式处理SIGINT信号
        # 完全避免使用可能导致问题的SetConsoleCtrlHandler
        def windows_sigint_handler(signum, frame):
            debug("Windows平台接收到中断信号，准备关闭应用...")
            # 立即调用shutdown函数
            handle_shutdown(signum, frame)
            # handle_shutdown会调用sys.exit()，这里不需要再抛出异常


        # 设置信号处理器
        signal.signal(signal.SIGINT, windows_sigint_handler)
        debug("已设置Windows平台信号处理器")

    # 在主进程中运行Flask应用，确保信号可以正确捕获
    try:
        run_flask_app()
    except KeyboardInterrupt:
        info("主进程捕获到KeyboardInterrupt异常")
        # 确保所有资源都被正确释放
        sys.exit(0)
