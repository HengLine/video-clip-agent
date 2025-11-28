"""
@FileName: index_route.py
@Description: Flask index路由模块
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
from flask import Blueprint, render_template, jsonify

app = Blueprint('index_route', __name__)


# 首页路由
@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html',
                           title='视频工具智能体',
                           version='1.0.0',
                           features=['视频内容分析', '视频编辑', '质量验证'])


# API首页路由
@app.route('/api')
def api_index():
    """API首页"""
    return render_template('api_docs.html')


# 健康检查API
@app.route('/api/health', methods=['GET'])
def health_check():
    # 简化的健康检查，只返回服务状态
    return jsonify({
        'status': 'healthy',
        'message': 'Flask服务运行正常'
    })
