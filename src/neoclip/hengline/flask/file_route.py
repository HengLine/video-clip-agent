"""
@FileName: file_route.py
@Description: Flask file上传路由模块
@Author: HengLine
@Time: 2025/08 - 2025/11
"""

import os
import uuid

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config.config import get_allowed_extensions, get_upload_dir
from utils.file_utils import upload_file

from hengline.logger import debug, error

app = Blueprint('file_route', __name__)


# 通用文件上传API
@app.route('/api/upload', methods=['POST'])
def upload_file_route():
    """通用文件上传接口"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有文件被上传'}), 400

        file = request.files['file']

        # 如果用户没有选择文件，浏览器也会发送一个空的文件
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400

        # 检查文件类型
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in get_allowed_extensions():
            filepath = upload_file(file, get_upload_dir(), get_allowed_extensions())
            debug(f"保存文件: {filepath}")

            # 返回文件信息
            # 从filepath中提取文件名
            file_name = os.path.basename(filepath)
            return jsonify({
                'status': 'success',
                'message': '文件上传成功',
                'filename': file_name,
                'original_filename': file.filename,
                'filepath': filepath
            })
        else:
            allowed_extensions_str = ', '.join(get_allowed_extensions())
            return jsonify({'status': 'error', 'message': f'不支持的文件类型，请上传以下格式: {allowed_extensions_str}'}), 400

    except Exception as e:
        error(f"文件上传出错: {str(e)}")
        return jsonify({'status': 'error', 'message': f'服务器内部错误: {str(e)}'}), 500
