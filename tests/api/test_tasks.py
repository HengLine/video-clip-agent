"""任务接口测试：提交 / 状态 / 结果 / 取消。"""

import time


def test_submit_task(client):
    resp = client.post("/api/v1/tasks", json={"user_input": "剪掉开头3秒"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"]
    assert body["session_id"]
    assert body["status"] == "pending"


def test_submit_task_requires_input(client):
    resp = client.post("/api/v1/tasks", json={})
    assert resp.status_code == 422


def test_nonexistent_task_404(client):
    assert client.get("/api/v1/tasks/does-not-exist").status_code == 404
    assert client.get("/api/v1/tasks/does-not-exist/result").status_code == 404
    assert client.delete("/api/v1/tasks/does-not-exist").status_code == 404


def test_task_completes(client):
    resp = client.post("/api/v1/tasks", json={"user_input": "剪掉开头3秒"})
    task_id = resp.json()["task_id"]

    result = None
    for _ in range(50):  # 最多等待约 5s
        r = client.get(f"/api/v1/tasks/{task_id}/result")
        assert r.status_code == 200
        result = r.json()
        if result.get("status") in ("success", "failed"):
            break
        time.sleep(0.1)

    assert result is not None
    assert result["task_id"] == task_id
    assert result["status"] == "success"

    status = client.get(f"/api/v1/tasks/{task_id}")
    assert status.status_code == 200
    assert status.json()["task_id"] == task_id
