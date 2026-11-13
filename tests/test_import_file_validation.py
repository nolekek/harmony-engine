"""
Tests for /api/import-file input validation (audit M1): broken base64/JSON/XML/MIDI
must yield structured 400 responses instead of unhandled 500s, while both valid
paths (multipart file upload and JSON content_base64/xml_content) keep working.
"""

import base64
import io

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)

VALID_XML = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Soprano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>0</fifths><mode>major</mode></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
  </part>
</score-partwise>"""


def _assert_400(res, fragment: str | None = None) -> None:
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert isinstance(data.get("detail"), str) and data["detail"], f"Missing detail: {data}"
    if fragment:
        assert fragment.lower() in data["detail"].lower(), f"Detail lacks {fragment!r}: {data['detail']}"


def test_import_file_broken_base64_returns_400():
    res = client.post(
        "/api/import-file",
        json={"filename": "score.musicxml", "content_base64": "!!!not-valid-base64!!!"},
    )
    _assert_400(res, "base64")


def test_import_file_invalid_json_body_returns_400():
    res = client.post(
        "/api/import-file",
        content=b'{"filename": "score.musicxml", broken',
        headers={"Content-Type": "application/json"},
    )
    _assert_400(res, "JSON")


def test_import_file_json_array_body_returns_400():
    res = client.post("/api/import-file", json=[1, 2, 3])
    _assert_400(res)


def test_import_file_broken_xml_returns_400():
    res = client.post(
        "/api/import-file",
        json={"filename": "score.musicxml", "xml_content": "<score-partwise><part><measure>"},
    )
    _assert_400(res, "MusicXML")


def test_import_file_binary_not_midi_returns_400():
    garbage = b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 2
    res = client.post(
        "/api/import-file",
        json={"filename": "track.mid", "content_base64": base64.b64encode(garbage).decode()},
    )
    _assert_400(res, "MIDI")


def test_import_file_empty_payload_returns_400():
    res = client.post("/api/import-file", json={"filename": "score.musicxml"})
    _assert_400(res)


def test_import_file_valid_json_xml_still_200():
    res = client.post(
        "/api/import-file",
        json={"filename": "score.musicxml", "xml_content": VALID_XML},
    )
    assert res.status_code == 200, res.text[:300]
    data = res.json()
    assert data["format"] == "musicxml"
    assert data["soprano_melody"][0]["pitch"] == 60


def test_import_file_valid_multipart_still_200():
    res = client.post(
        "/api/import-file",
        files={"file": ("score.musicxml", VALID_XML.encode("utf-8"), "application/xml")},
    )
    assert res.status_code == 200, res.text[:300]
    assert res.json()["format"] == "musicxml"


def test_import_file_broken_xml_via_base64_returns_400():
    res = client.post(
        "/api/import-file",
        json={
            "filename": "score.xml",
            "content_base64": base64.b64encode(b"<score-partwise><part><measure>").decode(),
        },
    )
    _assert_400(res, "MusicXML")


def test_import_file_multipart_garbage_midi_returns_400():
    res = client.post(
        "/api/import-file",
        files={"file": ("track.mid", b"\x00\x01not-a-midi-file", "audio/midi")},
    )
    _assert_400(res, "MIDI")


def test_import_file_multipart_empty_file_returns_400():
    res = client.post(
        "/api/import-file",
        files={"file": ("score.musicxml", b"", "application/xml")},
    )
    _assert_400(res)


def test_import_file_non_string_xml_content_returns_400():
    res = client.post("/api/import-file", json={"filename": "score.xml", "xml_content": 12345})
    _assert_400(res, "xml_content")


def test_import_file_non_string_content_base64_returns_400():
    res = client.post("/api/import-file", json={"filename": "score.mid", "content_base64": ["AAA"]})
    _assert_400(res, "base64")


def test_import_file_valid_base64_midi_still_200():
    import mido

    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=80, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=480))
    buf = io.BytesIO()
    mid.save(file=buf)
    b64 = base64.b64encode(buf.getvalue()).decode()

    res = client.post(
        "/api/import-file",
        json={"filename": "melody.mid", "content_base64": b64},
    )
    assert res.status_code == 200, res.text[:300]
    assert res.json()["format"] == "midi"


def test_import_file_invalid_utf8_json_body_returns_400():
    # Raw non-UTF-8 bytes under application/json must not escape as a 500
    # (UnicodeDecodeError from request.json()).
    res = client.request(
        "POST",
        "/api/import-file",
        content=b"\xff\xfe{}",
        headers={"Content-Type": "application/json"},
    )
    _assert_400(res, "JSON")


def test_import_file_unsupported_content_type_returns_400():
    # text/plain bypasses both JSON and multipart branches; request.form() may
    # raise there — must surface as 400, never 500.
    res = client.request(
        "POST",
        "/api/import-file",
        content=b"just some plain text",
        headers={"Content-Type": "text/plain"},
    )
    _assert_400(res)
