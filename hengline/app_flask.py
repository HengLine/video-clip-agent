#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@FileName: app_flask.py
@Description: Flask应用入口
@Author: HengLine
@Time: 2025/08 - 2025/11
"""

# 然后导入其他标准库和第三方库
import datetime
import os
import signal
import sys
import threading
import time
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.routing import PathConverter
from werkzeug.utils import secure_filename

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义日志模块
from hengline.logger import debug, info
from hengline.agent.state import GraphState
from hengline.agent.graph import create_agent_graph
from hengline.utils.config_utils import get_flask_secret_key

# 初始化Flask应用
app = Flask(__name__, template_folder='flask/templates')
app.config['JSON_AS_ASCII'] = False  # 允许非ASCII字符
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)

# 配置文件上传
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# 创建必要的目录
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 从配置工具获取Flask配置
app.secret_key = get_flask_secret_key()

# 初始化智能体流程图
agent_graph = create_agent_graph()

# 辅助函数：检查文件类型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 路由定义
@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html', 
                           title='视频工具智能体',
                           version='1.0.0',
                           features=['视频内容分析', '视频编辑', '质量验证'])

# JSON API首页
@app.route('/api')
def api_index():
    """API首页"""
    return jsonify({
        'status': 'success',
        'message': '视频工具智能体服务正在运行',
        'version': '1.0.0',
        'features': ['视频内容分析', '视频编辑', '质量验证'],
        'api_endpoints': [
            '/api/process-video',
            '/api/video/<filename>',
            '/api/health'
        ]
    })

# 视频处理API
@app.route('/api/process-video', methods=['POST'])
def process_video():
    try:
        # 获取用户请求参数
        user_query = request.form.get('query', '')
        if not user_query:
            return jsonify({'status': 'error', 'message': '查询参数不能为空'}), 400
        
        # 检查是否有文件上传
        files = request.files.getlist('files[]')
        if not files or len(files) == 0:
            return jsonify({'status': 'error', 'message': '请上传至少一个视频文件'}), 400
        
        # 保存上传的文件
        video_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 添加UUID以避免文件名冲突
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                video_paths.append(filepath)
                debug(f"保存文件: {filepath}")
            else:
                debug(f"无效的文件类型: {file.filename}")
        
        if not video_paths:
            return jsonify({'status': 'error', 'message': '没有有效的视频文件'}), 400
        
        # 创建初始状态
        initial_state = GraphState(
            video_paths=video_paths,
            user_query=user_query,
            output_folder=app.config['OUTPUT_FOLDER']
        )
        
        # 执行智能体流程
        info(f"开始处理视频，查询: {user_query}")
        final_state = agent_graph.run(initial_state)
        
        # 根据处理结果返回响应
        if final_state.get('processing_status') == 'completed' and final_state.get('validation_passed'):
            final_video_path = final_state.get('final_video_path')
            if final_video_path:
                # 构建可访问的URL路径
                video_filename = os.path.basename(final_video_path)
                return jsonify({
                    'status': 'success',
                    'message': '视频处理成功',
                    'video_url': f'/api/video/{video_filename}',
                    'report': final_state.get('validation_report', {})
                })
            else:
                return jsonify({'status': 'error', 'message': '处理成功但未生成输出文件'}), 500
        else:
            error_msg = final_state.get('error', '处理失败')
            return jsonify({'status': 'error', 'message': error_msg}), 500
    
    except Exception as e:
        debug(f"处理请求出错: {str(e)}")
        return jsonify({'status': 'error', 'message': f'服务器内部错误: {str(e)}'}), 500

# 视频下载API
@app.route('/api/video/<filename>', methods=['GET'])
def serve_video(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

# 健康检查API
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'agents_loaded': len(agent_graph.agents) if 'agent_graph' in globals() else 0
    })


def handle_shutdown(signum, frame):
    """处理终止信号的回调函数"""
    info("接收到终止信号，正在异步关闭任务队列管理器...")


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
