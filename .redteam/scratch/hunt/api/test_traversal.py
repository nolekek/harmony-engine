import httpx

xml = "<score-partwise><part-list><score-part id='P1'><part-name>M</part-name></score-part></part-list><part id='P1'><measure number='1'><note><pitch><step>C</step><octave>4</octave></pitch></note></measure></part></score-partwise>"
r = httpx.post(
    "http://127.0.0.1:8000/api/import-file",
    json={"filename": "../../secret.xml", "xml_content": xml}
)
print("status:", r.status_code)
print("resp filename:", r.json().get("filename"))
print("keys in resp:", list(r.json().keys()))
