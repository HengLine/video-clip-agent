import os
import sys
import uuid
from hengline.logger import debug, info, error

def upload_file(file, upload_dir, allowed_extensions=None):
    """
    上传文件到指定目录
    :param file: Flask上传的文件对象
    :param upload_dir: 目标上传目录
    :return: 上传后的文件路径
    """
    if file:
        filename = file.filename if file.filename else datetime.now().strftime("%Y%m%d_%H%M%S")
        # 检查文件扩展名是否在允许的列表中
        if allowed_extensions and '.' in filename and filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            debug(f"文件扩展名 {filename.rsplit('.', 1)[1].lower()} 不在允许的列表中: {allowed_extensions}")
            return None
        # 添加UUID以避免文件名冲突
        # unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return filepath
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