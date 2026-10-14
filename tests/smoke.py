import json
import os
import time
import urllib.request

base = os.getenv("BASE_URL", "http://127.0.0.1:8080")
for attempt in range(60):
    try:
        with urllib.request.urlopen(base + "/health", timeout=1) as response:
            assert json.load(response)["status"] == "ok"
        break
    except Exception:
        if attempt == 59:
            raise
        time.sleep(0.5)
with urllib.request.urlopen(base + "/api/info", timeout=3) as response:
    info = json.load(response)
    assert info["version"] == os.getenv("EXPECT_VERSION", "ci-test")
    assert info["framework"] == "FastAPI"
with urllib.request.urlopen(base, timeout=3) as response:
    assert "생각이 문장이 되는 곳" in response.read().decode()
request = urllib.request.Request(base + "/api/echo", data=json.dumps({"message": "파도"}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(request, timeout=3) as response:
    assert json.load(response) == {"message": "파도", "length": 2}
print("Container HTTP smoke checks passed")
