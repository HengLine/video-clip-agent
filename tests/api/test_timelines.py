"""时间线接口测试。"""


def test_create_timeline(client):
    resp = client.post("/api/v1/timelines")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_get_timeline(client):
    resp = client.get("/api/v1/timelines/tl-1")
    assert resp.status_code == 200
    assert resp.json()["timeline_id"] == "tl-1"


def test_update_slot(client):
    resp = client.put("/api/v1/timelines/tl-1/slots/slot-1")
    assert resp.status_code == 200
    assert resp.json()["slot_id"] == "slot-1"
