import json
import sqlite3
import urllib.parse
import urllib.request
import uuid

BASE = "http://127.0.0.1:8000"

data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
login_req = urllib.request.Request(
    BASE + "/api/auth/login",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
login = json.loads(urllib.request.urlopen(login_req).read().decode())
token = login["access_token"]

sid = "test-orphan-" + uuid.uuid4().hex[:8]
fb = json.dumps({"ai_advice_pending": True, "issues": ["下蹲深度不足"]}, ensure_ascii=False)
conn = sqlite3.connect("pose_evaluation.db")
conn.execute(
    """
    INSERT INTO sessions (
        session_id, user_id, exercise, duration_seconds, total_count,
        valid_count, error_count, average_score, feedback_summary, created_at
    ) VALUES (?, NULL, 'squat', 60, 5, 4, 1, 80, ?, datetime('now'))
    """,
    (sid, fb),
)
conn.commit()
conn.close()

req = urllib.request.Request(
    BASE + f"/api/sessions/{sid}",
    headers={"Authorization": "Bearer " + token},
)
resp = urllib.request.urlopen(req)
body = json.loads(resp.read().decode())
print("GET session orphan:", resp.status, "user_id=", body.get("user_id"), "has_fb=", bool(body.get("feedback_summary")))

req2 = urllib.request.Request(
    BASE + f"/api/feedback?session_id={sid}",
    headers={"Authorization": "Bearer " + token},
)
fb_res = json.loads(urllib.request.urlopen(req2).read().decode())
print("GET feedback items:", len(fb_res.get("items", [])))
