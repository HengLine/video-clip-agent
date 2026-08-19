"""
@FileName: index_api.py
@Description: FastAPI 根路由 — 服务信息与健康检查
@Author: HiPeng
@Time: 2026/08/18
"""

from fastapi import APIRouter

router = APIRouter(tags=["NeoClip"])


@router.get("/")
def read_root():
    """
    根路径，提供 API 信息
    """
    return {
        "message": "NeoClip 视频混剪智能体服务",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@router.get("/health")
def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy"}
