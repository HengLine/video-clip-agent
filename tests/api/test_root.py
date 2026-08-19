"""根路由测试：服务信息与健康检查。"""


def test_root_info(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert "NeoClip" in body["message"]
    assert body["docs"] == "/docs"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
