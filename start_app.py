#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName: start_flask.py
@Description: Flask服务器启动脚本，负责提供API接口
    功能：
        1. 检查Python环境是否安装
        2. 检查虚拟环境是否存在，不存在则创建
        3. 根据不同系统激活虚拟环境
        4. 安装项目依赖
        5. 启动Flask应用

    步骤严格按顺序执行，只有上一步成功才执行下一步
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import os
import subprocess
import sys

from app_env import AppBaseEnv
from hengline.logger import debug, info, error

# 获取当前脚本所在目录（项目根目录）
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = "."

# 设置编码为UTF-8以确保中文显示正常
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 全局变量 - 明确指定虚拟环境为当前目录下的venv
APP_FILE = os.path.join(PROJECT_ROOT, "hengline", "flask", "app_flask.py")  # 修复后的应用文件路径


class FlaskApp(AppBaseEnv):
    """Flask应用启动类"""

    def start_application(self):
        """启动应用的抽象方法"""
        info("=== 正在启动Flask应用.... ===")

        try:
            if not os.path.exists(APP_FILE):
                error(f"[错误] 应用文件 {APP_FILE} 不存在！")
                return False

            # 使用python -m方式运行Flask应用
            subprocess.run(["python", APP_FILE], check=True)

            return True
        except subprocess.CalledProcessError as e:
            error(f"[错误] Flask应用启动失败: {e}")
            return False
        except KeyboardInterrupt:
            debug("[信息] 应用已被用户中断。")
            return True
        except Exception as e:
            error(f"[错误] 发生未预期的错误: {e}")
            return False


if __name__ == "__main__":
    FlaskApp().main()
