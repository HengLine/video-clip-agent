"""导出接口测试。"""


def test_start_render(client):
    resp = client.post("/api/v1/exports/render")
    assert resp.status_code == 200
    assert resp.json()["task_id"]


def test_get_render_status(client):
    resp = client.get("/api/v1/exports/export-1/status")
    assert resp.status_code == 200
    assert resp.json()["task_id"] == "export-1"


def test_download_video(client):
    resp = client.get("/api/v1/exports/export-1/download")
    assert resp.status_code == 200
    assert resp.json()["url"]
