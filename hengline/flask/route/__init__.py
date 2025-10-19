#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@FileName: __init__.py
@Description: Flask路由初始化模块
@Author: HengLine
@Time: 2025/08 - 2025/11
"""

# 导入路由初始化模块
from hengline.flask.route.index_route import app as index_route
from hengline.flask.route.file_route import app as file_route
from hengline.flask.route.video_route import app as video_route
from hengline.flask.route.ai_route import app as ai_route
from hengline.logger import info


def init_routes(app):
    """初始化所有API路由"""
    # 注册所有路由蓝图
    app.register_blueprint(index_route)
    app.register_blueprint(file_route)
    app.register_blueprint(video_route)
    app.register_blueprint(ai_route)

    info("所有API路由初始化完成")
