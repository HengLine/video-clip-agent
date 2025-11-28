#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@FileName: video_route.py
@Description: 视频相关API路由
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import json
import os

from flask import request, jsonify, send_from_directory, Blueprint

from config.config import get_allowed_extensions, get_upload_dir, get_output_dir
from hengline.logger import info, error
from utils.file_utils import upload_files
from hengline.agent.langgraph_orchestrator import agent_graph

app = Blueprint('video_route', __name__)

@app.route('/api/process-video', methods=['POST'])
def process_video_route():
    try:
        # 获取用户请求参数
        user_query = request.form.get('query', '')
        # 也尝试从其他可能的参数名获取
        if not user_query:
            user_query = request.form.get('user_query', '')
        if not user_query:
            return jsonify({'status': 'error', 'message': '查询参数不能为空'}), 400

        # 检查是否有文件上传
        files = request.files.getlist('files[]')
        # 也尝试从其他可能的参数名获取
        if not files or len(files) == 0:
            files = request.files.getlist('videos')
        if not files or len(files) == 0:
            return jsonify({'status': 'error', 'message': '请上传至少一个视频文件'}), 400

        # 保存上传的文件
        video_paths = upload_files(files, get_upload_dir(), get_allowed_extensions())

        if not video_paths:
            return jsonify({'status': 'error', 'message': '没有有效的视频文件'}), 400

        # 创建初始状态 - 使用LangGraphOrchestrator需要的格式
        initial_state = {
            'videos': video_paths,  # 符合GraphState定义的字段名
            'user_query': user_query,
            'config': {}  # 输出目录使用video_editor中的默认设置
        }

        # 检查是否有裁剪策略信息
        use_crop_strategy = request.form.get('use_crop_strategy', 'false')
        if use_crop_strategy.lower() == 'true':
            try:
                # 获取裁剪策略JSON字符串
                crop_strategy_str = request.form.get('crop_strategy', '{}')
                crop_strategy = json.loads(crop_strategy_str)
                # 将裁剪策略添加到初始状态
                initial_state['crop_strategy'] = crop_strategy
                info(f"接收到裁剪策略，包含{len(crop_strategy.get('segments', []))}个片段")
            except json.JSONDecodeError as e:
                error(f"裁剪策略JSON解析错误: {str(e)}")
                # 不中断处理，只是不使用裁剪策略

        # 执行智能体流程
        info(f"开始处理视频，查询: {user_query}")
        # 如果有其他处理选项，也添加到日志
        if request.form.get('priority'):
            info(f"处理优先级: {request.form.get('priority')}")
        if request.form.get('sort_by'):
            info(f"排序方式: {request.form.get('sort_by')}")
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
        error(f"处理请求出错: {str(e)}")
        return jsonify({'status': 'error', 'message': f'服务器内部错误: {str(e)}'}), 500


@app.route('/api/video/<filename>', methods=['GET'])
def serve_video_route(filename):
    """提供视频文件下载服务"""

    return send_from_directory(get_output_dir(), filename)
