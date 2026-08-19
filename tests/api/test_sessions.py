"""会话接口测试。"""


def test_create_session(client):
    resp = client.post("/api/v1/sessions")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_get_session(client):
    resp = client.get("/api/v1/sessions/sess-1")
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "sess-1"


def test_delete_session(client):
    resp = client.delete("/api/v1/sessions/sess-1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
