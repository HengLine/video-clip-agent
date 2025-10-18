import os
import sys
import uuid
from datetime import datetime
from hengline.logger import debug, info, error, warning

def upload_file(file, upload_dir, allowed_extensions=None):
    """
    上传文件到指定目录
    :param file: Flask上传的文件对象
    :param upload_dir: 目标上传目录
    :return: 上传后的文件路径
    """
    try:
        # 路径参数验证
        if not upload_dir or not isinstance(upload_dir, str):
            error("上传目录必须是有效的字符串")
            return None
        
        # 确保上传目录存在
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir, exist_ok=True)
                debug(f"创建上传目录: {upload_dir}")
            except Exception as e:
                error(f"创建上传目录失败: {str(e)}")
                return None
                
        if file:
            # 获取文件名，处理空文件名情况
            filename = file.filename if file.filename else f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 检查文件扩展名是否在允许的列表中
            if allowed_extensions:
                # 如果没有扩展名，直接返回None
                if '.' not in filename:
                    warning(f"文件没有扩展名: {filename}")
                    return None
                
                file_ext = filename.rsplit('.', 1)[1].lower()
                if file_ext not in allowed_extensions:
                    warning(f"文件扩展名 {file_ext} 不在允许的列表中: {allowed_extensions}")
                    return None
                    
            # 添加UUID以避免文件名冲突
            # unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            filepath = os.path.join(upload_dir, filename)
            
            # 保存文件
            file.save(filepath)
            debug(f"文件上传成功: {filepath}")
            return filepath
        else:
            debug("没有收到文件对象")
            return None
    except Exception as e:
        error(f"文件上传过程出错: {str(e)}")
        return None


def upload_files(files, upload_dir, allowed_extensions=None):
    """
    上传多个文件到指定目录
    :param files: Flask上传的文件对象列表
    :param upload_dir: 目标上传目录
    :return: 上传后的文件路径列表
    """
    uploaded_files = []
    for file in files:
        filepath = upload_file(file, upload_dir, allowed_extensions)
        if filepath:
            uploaded_files.append(filepath)
    return uploaded_files