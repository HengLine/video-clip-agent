"""pytest 全局夹具。

目录分类约定：
- tests/api/   —— 接口层测试（REST 端点）
- tests/unit/  —— 单元测试（领域层 / 应用层纯逻辑）
"""

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# src 布局：将 src 加入 sys.path，使未安装时可独立运行
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def client():
    """共享的 TestClient，触发 lifespan 启动（注册 Agent、编译图）。"""
    from penclip.app.application import app

    with TestClient(app) as c:
        yield c
