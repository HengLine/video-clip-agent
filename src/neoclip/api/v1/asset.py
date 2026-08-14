"""Asset API endpoints — video upload, metadata, analysis."""

from fastapi import APIRouter

router = APIRouter(prefix="/asset", tags=["asset"])


@router.post("/upload")
async def upload_asset():
    return {"status": "ok", "message": "Asset uploaded (stub)"}


@router.get("/{asset_id}")
async def get_asset(asset_id: str):
    return {"asset_id": asset_id, "status": "uploaded"}


@router.get("/{asset_id}/metadata")
async def get_asset_metadata(asset_id: str):
    return {"asset_id": asset_id, "duration": 0, "resolution": "1920x1080"}


@router.post("/{asset_id}/analyze")
async def analyze_asset(asset_id: str):
    return {"asset_id": asset_id, "status": "analyzing"}
