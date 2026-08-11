"""
@FileName: __init__.py
@Description: NeoClip - 智能视频混剪服务
@Author: HiPeng
@Time: 2026/3/6 22:34
"""

"""
使用方式：

1. Python 智能体调用（Function Call）：
    from neoclip import PenshotFunction
    agent = PenshotFunction()
    result = agent.breakdown_script("剧本内容")

2. REST API 调用：
    POST /api/v1/storyboard
"""
from neoclip import __version__
from neoclip.api.function_calls import PenshotFunction, PenshotResult
from neoclip.api.function_calls import create_penshot_agent

__author__ = "HiPeng"

__all__ = [
    "PenshotFunction",
    "PenshotResult",
    "create_penshot_agent",
]
