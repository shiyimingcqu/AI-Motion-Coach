import json
import time
import urllib.parse
import urllib.request

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


def req(method, path, body=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=90) as resp:
        return resp.status, json.loads(resp.read().decode())


_, sess = req(
    "POST",
    "/api/sessions",
    {
        "exercise": "squat",
        "duration_seconds": 30,
        "total_count": 3,
        "valid_count": 2,
        "error_count": 1,
        "average_score": 70,
        "issues": ["膝盖内扣"],
        "suggestions": [],
    },
)
sid = sess["session_id"]
summary = json.loads(sess["feedback_summary"])
print("created", sid, "pending=", summary.get("ai_advice_pending"))

for i in range(20):
    _, detail = req("GET", f"/api/sessions/{sid}")
    fb = json.loads(detail["feedback_summary"])
    advice = (fb.get("ai_advice") or "").strip()
    print(f"poll {i + 1}: advice_len={len(advice)} failed={fb.get('ai_advice_status')}")
    if advice or fb.get("ai_advice_status") == "failed":
        break
    time.sleep(2)

_, fb_res = req("GET", f"/api/feedback?session_id={sid}")
print("feedback items:", len(fb_res.get("items", [])))
