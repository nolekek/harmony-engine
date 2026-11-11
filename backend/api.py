"""
FastAPI REST router for Brigade Harmony Engine.
Exposes harmonization, student grading, file imports, exports, and key detection.
"""

from __future__ import annotations

import io
import time
from typing import Annotated, Any, Self
from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator

from src.harmony.core.types import Key, Chord, Voicing, PITCH_CLASS_NAMES, VALID_DURATIONS
from src.harmony.pipeline import Harmonizer
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from backend.importers import (
    parse_musicxml_content,
    parse_midi_file,
    parse_text_melody,
    midi_to_note_name,
)
from backend.key_detector import CANONICAL_KEYS, detect_key_from_melody
from backend.exporters import build_colored_musicxml, generate_midi_bytes
from backend.grader import grade_satb_solution
from src.harmony.export.ascii import format_ascii_score

from starlette.concurrency import run_in_threadpool
from backend.service import HarmonizationService

router = APIRouter(prefix="/api")
harmonization_service = HarmonizationService()

VALID_TONICS = set(PITCH_CLASS_NAMES.keys())
VALID_MODES = {
    "major",
    "minor",
    "minorharmonic",
    "minornatural",
    "minor_harmonic",
    "minor_natural",
    "dur",
    "moll",
}


def _check_time_signature(value: str) -> str:
    """Validates a meter spelling; malformed meters are rejected with 422."""
    text = str(value).strip()
    parts = text.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Неверный размер: '{value}'. Ожидается формат '<доли>/<знаменатель>', напр. 4/4."
        )
    try:
        beats = int(parts[0])
        beat_type = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Неверный размер: '{value}'.") from exc
    if not (1 <= beats <= 32) or beat_type not in (1, 2, 4, 8, 16, 32):
        raise ValueError(
            f"Неверный размер: '{value}'. Допустимо: 1..32 долей, знаменатель из 1,2,4,8,16,32."
        )
    return f"{beats}/{beat_type}"


TimeSignatureStr = Annotated[str, AfterValidator(_check_time_signature)]


def _check_duration(value: str) -> str:
    """Validates a note duration spelling; unknown strings are rejected with 422."""
    text = str(value).strip().lower()
    if text in VALID_DURATIONS:
        return text
    try:
        float(text)
        return text
    except ValueError as exc:
        raise ValueError(
            f"Неизвестная длительность: '{value}'. Допустимые: {sorted(VALID_DURATIONS)}"
        ) from exc


VALID_CHORD_FUNCTIONS = {
    # Tonic
    "T", "T6", "T64", "T53", "T-6",
    "t", "t6", "t64", "t53", "t-6",
    # Subdominant
    "S", "S6", "S64", "S53", "S-6",
    "s", "s6", "s64", "s53", "s-6",
    # Dominant
    "D", "D6", "D7", "D65", "D43", "D2", "D53", "D-6", "D-7", "D-65", "D-43", "D-2",
    "D6/5", "D4/3",
    "d", "d6", "d7", "d65", "d43", "d2", "d53", "d-6", "d-7", "d-65", "d-43", "d-2",
    "d6/5", "d4/3",
    # Cadential 6/4
    "K64", "K6/4", "Cad64", "cad64", "CAD64", "k64",
    # II degree
    "II", "II6", "II7", "II65", "II43", "II2", "II53", "II-6", "II-7",
    "ii", "ii6", "ii7", "ii65", "ii43", "ii2", "ii53", "ii-6", "ii-7",
    # VI degree
    "VI", "VI6", "VI53", "VI-6",
    "vi", "vi6", "vi53", "vi-6",
    # III degree
    "III", "III6", "III53", "III-6",
    "iii", "iii6", "iii53", "iii-6",
    # VII degree
    "VII", "VII6", "VII7", "VII65", "VII43", "VII2", "VII53", "VII-6", "VII-7",
    "vii", "vii6", "vii7", "vii65", "vii43", "vii2", "vii53", "vii-6", "vii-7",
    # Double Dominant
    "DD", "DD7", "DD65", "DD43", "DD2", "DD6", "DD-7",
    "dd", "dd7", "dd65", "dd43", "dd2", "dd6", "dd-7",
    "D7V", "DV", "D7/V", "D/V", "d7v", "dv", "d7/v", "d/v",
    # Secondary dominants
    "D7II", "D/II", "D7/II", "D7VI", "D/VI", "D7/VI", "D7IV", "D/IV", "D7/IV",
    # Neapolitan chord (bII)
    "N", "N6", "N53", "N64", "N-6",
    "n", "n6", "n53", "n64", "n-6",
    "bII", "bII6", "bII53", "bII-6",
    "bii", "bii6", "bii53", "bii-6",
    # Chromatic submediant (bVI)
    "bVI", "bVI6", "bVI53", "bVI64", "bVI-6",
    "bvi", "bvi6", "bvi53", "bvi64", "bvi-6",
    "BVI", "BVI6", "BVI53", "BVI64", "BVI-6",
}


def select_top_candidates(solutions: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]:
    """
    Stably selects the top-k candidate solutions with the lowest total cost.
    Updates the 1-based rank on each selected candidate.
    """
    sorted_solutions = sorted(solutions, key=lambda s: s.get("cost", 0.0))[:k]
    for idx, s in enumerate(sorted_solutions, start=1):
        s["rank"] = idx
    return sorted_solutions


class KeyRequest(BaseModel):
    tonic: str = "C"
    mode: str = "Major"

    @field_validator("tonic")
    @classmethod
    def validate_tonic(cls, v: str) -> str:
        if not isinstance(v, str) or v.strip().upper() not in VALID_TONICS:
            raise ValueError(f"Неизвестная тоника: '{v}'. Допустимые: {sorted(VALID_TONICS)}")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if not isinstance(v, str) or v.strip().lower() not in VALID_MODES:
            raise ValueError(f"Неизвестный лад: '{v}'. Допустимые: Major, Minor, MinorHarmonic, MinorNatural")
        return v


class MelodyNoteItem(BaseModel):
    pitch: int = Field(..., ge=0, le=127)
    is_downbeat: bool | None = None
    duration: str = "half"
    name: str | None = None

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        return _check_duration(v)


class HarmonizeRequest(BaseModel):
    melody: list[MelodyNoteItem] = Field(..., min_length=1, max_length=128)
    key: KeyRequest = Field(default_factory=KeyRequest)
    time_signature: TimeSignatureStr = "4/4"
    allow_extended_ranges: bool = False
    allow_secondary_dominants: bool = True
    max_plans: int = Field(default=50, ge=1, le=100)


class VoicingItem(BaseModel):
    soprano: int
    alto: int
    tenor: int
    bass: int
    measure: int | None = None
    is_downbeat: bool = False
    duration: str | None = None

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str | None) -> str | None:
        return None if v is None else _check_duration(v)


class GradeRequest(BaseModel):
    voicings: list[VoicingItem] = Field(..., min_length=1)
    chords: list[str] = Field(..., min_length=1)
    key: KeyRequest = Field(default_factory=KeyRequest)
    time_signature: TimeSignatureStr = "4/4"
    durations: list[str] | None = None
    allow_extended_ranges: bool = False

    @field_validator("durations")
    @classmethod
    def validate_durations(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else [_check_duration(item) for item in v]

    @field_validator("chords")
    @classmethod
    def validate_chords(cls, chords: list[str]) -> list[str]:
        for c in chords:
            if not isinstance(c, str) or c.strip() not in VALID_CHORD_FUNCTIONS:
                raise ValueError(f"Неизвестная функция аккорда: '{c}'")
        return chords

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        if len(self.voicings) != len(self.chords):
            raise ValueError(
                f"Несоответствие длины: voicings ({len(self.voicings)}) и chords ({len(self.chords)}) должны совпадать."
            )
        return self


class ParseTextRequest(BaseModel):
    text: str
    key: KeyRequest = Field(default_factory=KeyRequest)
    time_signature: TimeSignatureStr = "4/4"


class ExportMidiRequest(BaseModel):
    voicings: list[VoicingItem]
    bpm: int = 80
    time_signature: TimeSignatureStr = "4/4"
    durations: list[str] | None = None

    @field_validator("durations")
    @classmethod
    def validate_durations(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else [_check_duration(item) for item in v]


class ExportMusicXmlRequest(BaseModel):
    voicings: list[VoicingItem]
    chords: list[str] | None = None
    key: KeyRequest = Field(default_factory=KeyRequest)
    title: str = "Harmonization Exercise"
    time_signature: TimeSignatureStr = "4/4"
    durations: list[str] | None = None

    @field_validator("durations")
    @classmethod
    def validate_durations(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else [_check_duration(item) for item in v]


@router.get("/keys")
def get_canonical_keys() -> list[dict[str, Any]]:
    """Returns 24 canonical keys (12 major, 12 harmonic minor)."""
    return CANONICAL_KEYS


@router.post("/detect-key")
def api_detect_key(melody: list[MelodyNoteItem]) -> dict[str, Any]:
    """Auto-detects the most probable key from a soprano melody."""
    if not melody:
        return CANONICAL_KEYS[0]
    return detect_key_from_melody([{"pitch": m.pitch} for m in melody])


@router.post("/parse-text")
def api_parse_text(req: ParseTextRequest) -> list[dict[str, Any]]:
    """Parses text notation (note names, MIDI numbers, or scale degrees)."""
    return parse_text_melody(
        req.text,
        key_tonic=req.key.tonic,
        key_mode=req.key.mode,
        time_signature=req.time_signature,
    )


@router.post("/harmonize")
async def api_harmonize(req: HarmonizeRequest) -> dict[str, Any]:
    """
    Harmonizes a given soprano melody.
    Returns candidate pool (top-3 solutions) with Viterbi costs, colored MusicXML,
    and Sposobin functional analysis.
    """
    if not req.melody:
        raise HTTPException(status_code=400, detail="Мелодия не может быть пустой.")
    return await run_in_threadpool(harmonization_service.harmonize, req)


@router.post("/grade")
def api_grade(req: GradeRequest) -> dict[str, Any]:
    """
    Grades student SATB solution using RuleEngine.
    Returns comprehensive diagnostic report and highlighted score.
    """
    voicings = [
        Voicing(soprano=v.soprano, alto=v.alto, tenor=v.tenor, bass=v.bass)
        for v in req.voicings
    ]
    parsed_key = Key(tonic=req.key.tonic, mode=req.key.mode)

    durs = req.durations or ([v.duration or "half" for v in req.voicings] if any(v.duration for v in req.voicings) else None)
    report = grade_satb_solution(
        voicings=voicings,
        key=parsed_key,
        chords=req.chords,
        allow_extended_ranges=req.allow_extended_ranges,
        time_signature=req.time_signature,
        durations=durs,
    )

    colored_xml = build_colored_musicxml(
        voicings=voicings,
        chords=req.chords,
        key=parsed_key,
        title=f"Проверка голосоведения: {report.grade}",
        durations=durs,
        time_signature=req.time_signature,
    )
    ascii_score = format_ascii_score(
        voicings=voicings,
        chords=req.chords,
        key=f"{parsed_key.tonic} {parsed_key.mode}",
    )

    return {
        "report": report,
        "musicxml": colored_xml,
        "ascii_score": ascii_score,
    }


class FileUploadJsonRequest(BaseModel):
    filename: str
    content_base64: str | None = None
    xml_content: str | None = None


@router.post("/import-file")
async def api_import_file(
    request: Request,
    file: UploadFile | None = None,
    json_body: FileUploadJsonRequest | None = None,
) -> dict[str, Any]:
    """
    Imports MusicXML (.musicxml, .xml) or MIDI (.mid, .midi) file.
    Supports both multipart form-data and direct JSON with base64/text.
    """
    import base64

    filename = ""
    content = b""

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        filename = body.get("filename", "upload")
        if body.get("xml_content"):
            content = body["xml_content"].encode("utf-8")
        elif body.get("content_base64"):
            content = base64.b64decode(body["content_base64"])
    else:
        # Multipart form upload
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file is not None and hasattr(uploaded_file, "read"):
            filename = getattr(uploaded_file, "filename", "upload") or "upload"
            content = await uploaded_file.read()
        elif file is not None:
            filename = file.filename or "upload"
            content = await file.read()
        elif json_body is not None:
            filename = json_body.filename
            if json_body.xml_content:
                content = json_body.xml_content.encode("utf-8")
            elif json_body.content_base64:
                content = base64.b64decode(json_body.content_base64)

    if not filename or not content:
        raise HTTPException(status_code=400, detail="Файл не передан.")

    if filename.endswith((".xml", ".musicxml")):
        xml_text = content.decode("utf-8", errors="ignore")
        res = parse_musicxml_content(xml_text)
        ts_info = res.get("time_signature") or {}
        ts_str = f"{ts_info.get('beats', 4)}/{ts_info.get('beat_type', 4)}"
        durations = [note.get("duration", "half") for note in res["soprano_melody"]]
        return {
            "format": "musicxml",
            "filename": filename,
            "soprano_melody": res["soprano_melody"],
            "satb_voicings": res["satb_voicings"],
            "chords": res["chords"],
            "key": res["detected_key"],
            "detected_key": res["detected_key"],
            "time_signature": ts_str,
            "durations": durations,
        }
    elif filename.endswith((".mid", ".midi")):
        res = parse_midi_file(content)
        # Auto detect key from soprano
        detected_key = detect_key_from_melody(res["soprano_melody"]) if res["soprano_melody"] else CANONICAL_KEYS[0]
        durations = [note.get("duration", "half") for note in res["soprano_melody"]]
        return {
            "format": "midi",
            "filename": filename,
            "soprano_melody": res["soprano_melody"],
            "satb_voicings": res["satb_voicings"],
            "chords": [],
            "key": detected_key,
            "detected_key": detected_key,
            "time_signature": str(res.get("time_signature", "4/4")),
            "durations": durations,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат файла. Поддерживаются .musicxml, .xml, .mid, .midi",
        )


@router.post("/export/midi")
def api_export_midi(req: ExportMidiRequest):
    """Exports SATB voicings to binary MIDI file download."""
    if not req.voicings:
        raise HTTPException(status_code=400, detail="Нет аккордов для экспорта.")
    voicings = [
        Voicing(soprano=v.soprano, alto=v.alto, tenor=v.tenor, bass=v.bass)
        for v in req.voicings
    ]
    durs = req.durations or ([v.duration or "half" for v in req.voicings] if any(v.duration for v in req.voicings) else None)
    data = generate_midi_bytes(
        voicings,
        bpm=req.bpm,
        durations=durs,
        time_signature=req.time_signature,
    )
    return Response(
        content=data,
        media_type="audio/midi",
        headers={"Content-Disposition": 'attachment; filename="harmonization.mid"'},
    )


@router.post("/export/musicxml")
def api_export_musicxml(req: ExportMusicXmlRequest):
    """Exports SATB voicings to MusicXML file download."""
    if not req.voicings:
        raise HTTPException(status_code=400, detail="Нет аккордов для экспорта.")
    if req.chords:
        for chord_symbol in req.chords:
            if str(chord_symbol).strip() not in VALID_CHORD_FUNCTIONS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Неизвестная функция аккорда: '{chord_symbol}'",
                )
    voicings = [
        Voicing(soprano=v.soprano, alto=v.alto, tenor=v.tenor, bass=v.bass)
        for v in req.voicings
    ]
    parsed_key = Key(tonic=req.key.tonic, mode=req.key.mode)
    durs = req.durations or ([v.duration or "half" for v in req.voicings] if any(v.duration for v in req.voicings) else None)
    xml_str = build_colored_musicxml(
        voicings=voicings,
        chords=req.chords,
        key=parsed_key,
        title=req.title,
        durations=durs,
        time_signature=req.time_signature,
    )
    return Response(
        content=xml_str,
        media_type="application/vnd.recordare.musicxml+xml",
        headers={"Content-Disposition": 'attachment; filename="harmonization.musicxml"'},
    )

