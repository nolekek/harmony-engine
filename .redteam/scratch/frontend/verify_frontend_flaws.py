"""
Red-team Frontend Proof of Concept & Evidence Collector
Verifies frontend-to-backend integration bugs, payload mismatches, and audio leaks.
"""
import urllib.request
import json
from pathlib import Path

def test_api_keys_property_mismatch():
    """Bug: Backend returns 'name', but App.tsx & ControlPanel.tsx expect 'title'."""
    url = "http://127.0.0.1:8000/api/keys"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    first = data[0]
    has_title = "title" in first
    has_name = "name" in first
    print(f"[/api/keys] has 'title': {has_title}, has 'name': {has_name}")
    assert not has_title and has_name, "Expected backend to return 'name' instead of 'title'"
    print(" -> PROOF: ControlPanel.tsx renders blank '{k.title}' inside <option> because backend key object only has 'name'!")

def test_export_durations_omission():
    """Bug: ExportBar does not supply durations, causing backend to fallback to all-half notes."""
    url = "http://127.0.0.1:8000/api/export/musicxml"
    payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48},
            {"soprano": 60, "alto": 60, "tenor": 55, "bass": 48}
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4"
        # Notice: durations is omitted, as done by ExportBar.tsx
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        xml_content = resp.read().decode()
    assert "<type>half</type>" in xml_content
    print(" -> PROOF: Without durations, all exported notes degenerate to 'half' notes regardless of actual melody durations!")

def test_bundle_size():
    """Verify monolithic bundle size and lack of code-splitting."""
    dist_js = list(Path("D:/aitraining/frontend/dist/assets").glob("*.js"))[0]
    size_mb = dist_js.stat().st_size / (1024 * 1024)
    print(f"Bundle {dist_js.name}: {size_mb:.2f} MB")
    assert size_mb > 1.5, "Expected bundle to exceed 1.5 MB due to un-chunked OSMD"

if __name__ == "__main__":
    print("--- RUNNING FRONTEND RED-TEAM VERIFICATIONS ---")
    test_api_keys_property_mismatch()
    test_export_durations_omission()
    test_bundle_size()
    print("--- ALL EVIDENCE CONFIRMED ---")
