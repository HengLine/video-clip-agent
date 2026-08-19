"""素材接口测试。"""


def test_upload_asset(client):
    resp = client.post("/api/v1/assets")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_get_asset(client):
    resp = client.get("/api/v1/assets/asset-1")
    assert resp.status_code == 200
    assert resp.json()["asset_id"] == "asset-1"


def test_get_asset_metadata(client):
    resp = client.get("/api/v1/assets/asset-1/metadata")
    assert resp.status_code == 200
    assert resp.json()["resolution"] == "1920x1080"


def test_analyze_asset(client):
    resp = client.post("/api/v1/assets/asset-1/analyze")
    assert resp.status_code == 200
    assert resp.json()["status"] == "analyzing"
