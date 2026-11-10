import json
import urllib.request
import urllib.error

def post(url, data, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if isinstance(data, dict) else data,
        headers=h
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8"), e.headers

# 1. Test Key validation with garbage key
status, body, _ = post("http://127.0.0.1:8000/api/harmonize", {
    "melody": [{"pitch": 64}],
    "key": {"tonic": "Z#", "mode": "AlienMode"},
})
print("1. Garbage Key response status:", status)
print("   Response:", body.get("message") if isinstance(body, dict) else body)

# 2. Test max_plans <= 0
status, body, _ = post("http://127.0.0.1:8000/api/harmonize", {
    "melody": [{"pitch": 64, "duration": "half"}],
    "key": {"tonic": "C", "mode": "Major"},
    "max_plans": 0
})
print("2. max_plans=0 response status:", status)
print("   Response:", body.get("message") if isinstance(body, dict) else body)

# 3. Test negative max_plans
status, body, _ = post("http://127.0.0.1:8000/api/harmonize", {
    "melody": [{"pitch": 64, "duration": "half"}],
    "key": {"tonic": "C", "mode": "Major"},
    "max_plans": -10
})
print("3. max_plans=-10 response status:", status)
print("   Response:", body.get("message") if isinstance(body, dict) else body)

# 4. Test /api/grade with mismatch lengths (6 voicings, 2 chords)
status, body, _ = post("http://127.0.0.1:8000/api/grade", {
    "voicings": [
        {"soprano": 64, "alto": 60, "tenor": 48, "bass": 48},
        {"soprano": 65, "alto": 60, "tenor": 48, "bass": 45},
        {"soprano": 67, "alto": 59, "tenor": 55, "bass": 43},
    ],
    "chords": ["T"]
})
print("4. /api/grade chord/voicing mismatch status:", status)
if isinstance(body, dict) and "report" in body:
    print("   Grade:", body["report"]["grade"], "Total violations:", body["report"]["total_violations"])

# 5. Test CORS response headers with Origin
req = urllib.request.Request("http://127.0.0.1:8000/api/health", headers={"Origin": "http://evil.com"})
try:
    with urllib.request.urlopen(req) as resp:
        print("5. CORS headers:")
        print("   access-control-allow-origin:", resp.headers.get("access-control-allow-origin"))
        print("   access-control-allow-credentials:", resp.headers.get("access-control-allow-credentials"))
except Exception as e:
    print("5. CORS error:", e)
