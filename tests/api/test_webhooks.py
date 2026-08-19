"""Webhook 接口测试。"""


def test_register_webhook(client):
    resp = client.post("/api/v1/webhooks")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_delete_webhook(client):
    resp = client.delete("/api/v1/webhooks/hook-1")
    assert resp.status_code == 200
    assert resp.json()["webhook_id"] == "hook-1"
