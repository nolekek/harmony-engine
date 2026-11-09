"""
FastAPI REST router for Brigade Harmony Engine.
Exposes harmonization, student grading, file imports, exports, and key detection.
"""

from __future__ import annotations

import io
import time
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from src.harmony.core.types import Key, Chord, Voicing
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

router = APIRouter(prefix="/api")


class KeyRequest(BaseModel):
    tonic: str = "C"
    mode: str = "Major"


class MelodyNoteItem(BaseModel):
    pitch: int
    is_downbeat: bool = False
    duration: str = "half"
    name: str | None = None


class HarmonizeRequest(BaseModel):
    melody: list[MelodyNoteItem]
    key: KeyRequest = Field(default_factory=KeyRequest)
    allow_extended_ranges: bool = False
    allow_secondary_dominants: bool = True
    max_plans: int = 50


class VoicingItem(BaseModel):
    soprano: int
    alto: int
    tenor: int
    bass: int
    measure: int | None = None
    is_downbeat: bool = False


class GradeRequest(BaseModel):
    voicings: list[VoicingItem]
    key: KeyRequest = Field(default_factory=KeyRequest)
    chords: list[str] | None = None
    allow_extended_ranges: bool = False


class ParseTextRequest(BaseModel):
    text: str
    key: KeyRequest = Field(default_factory=KeyRequest)


class ExportMidiRequest(BaseModel):
    voicings: list[VoicingItem]
    bpm: int = 80


class ExportMusicXmlRequest(BaseModel):
    voicings: list[VoicingItem]
    chords: list[str] | None = None
    key: KeyRequest = Field(default_factory=KeyRequest)
    title: str = "Harmonization Exercise"


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
    return parse_text_melody(req.text, key_tonic=req.key.tonic, key_mode=req.key.mode)


@router.post("/harmonize")
def api_harmonize(req: HarmonizeRequest) -> dict[str, Any]:
    """
    Harmonizes a given soprano melody.
    Returns candidate pool (top-3 solutions) with Viterbi costs, colored MusicXML,
    and Sposobin functional analysis.
    """
    t_start = time.perf_counter()

    if not req.melody:
        raise HTTPException(status_code=400, detail="Мелодия не может быть пустой.")

    melody_dicts = [
        {"pitch": m.pitch, "is_downbeat": m.is_downbeat, "duration": m.duration}
        for m in req.melody
    ]
    parsed_key = Key(tonic=req.key.tonic, mode=req.key.mode)

    # 1. Synthesize candidate functional plans
    grammar = HarmonicGrammar(key=parsed_key)
    all_plans = grammar.generate_plans(melody=melody_dicts, key=parsed_key, max_plans=req.max_plans)

    # If secondary dominants are disallowed, filter them out
    if not req.allow_secondary_dominants:
        filtered_plans = []
        for plan in all_plans:
            fns = [c.function for c in plan]
            if not any(f.startswith("DD") for f in fns):
                filtered_plans.append(plan)
        plans_to_try = filtered_plans or all_plans
    else:
        plans_to_try = all_plans

    if not plans_to_try:
        return {
            "is_success": False,
            "candidates": [],
            "message": "Не удалось синтезировать функциональные планы для данной мелодии.",
            "latency_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }

    # 2. Solve candidate plans
    solver = ViterbiSolver()
    solutions: list[dict[str, Any]] = []

    for plan_idx, plan in enumerate(plans_to_try):
        res = solver.solve(
            melody=melody_dicts,
            chords=plan,
            key=parsed_key,
            allow_extended_ranges=req.allow_extended_ranges,
        )

        if res.is_success and res.voicings:
            chords_list = [c.function for c in plan]
            voicings_list = [
                {"soprano": v.s, "alto": v.a, "tenor": v.t, "bass": v.b}
                for v in res.voicings
            ]
            ascii_text = format_ascii_score(
                voicings=res.voicings,
                chords=plan,
                key=f"{parsed_key.tonic} {parsed_key.mode}",
            )
            colored_xml = build_colored_musicxml(
                voicings=res.voicings,
                chords=plan,
                key=parsed_key,
                title=f"Гармонизация в {parsed_key.tonic} {parsed_key.mode}",
            )

            # Generate descriptive summary for the candidate card
            progression_str = " → ".join(chords_list)
            cadence_type = "Полная каденция" if "K64" in chords_list else "Автентический оборот"
            if any("DD" in c for c in chords_list):
                cadence_type += " (с двойной доминантой DD)"

            solutions.append({
                "id": f"cand_{len(solutions) + 1}",
                "rank": len(solutions) + 1,
                "cost": round(res.total_cost, 2),
                "chords": chords_list,
                "progression_preview": progression_str,
                "description": cadence_type,
                "voicings": voicings_list,
                "musicxml": colored_xml,
                "ascii_score": ascii_text,
            })

            if len(solutions) >= 3:
                break

    # Sort solutions by ascending cost
    solutions.sort(key=lambda s: s["cost"])
    for idx, s in enumerate(solutions, start=1):
        s["rank"] = idx

    latency = round((time.perf_counter() - t_start) * 1000, 2)

    return {
        "is_success": len(solutions) > 0,
        "candidates": solutions,
        "best_candidate": solutions[0] if solutions else None,
        "message": f"Найдено {len(solutions)} математически оптимальных решений." if solutions else "Все кандидаты отклонены жесткими правилами голосоведения.",
        "latency_ms": latency,
    }


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

    report = grade_satb_solution(
        voicings=voicings,
        key=parsed_key,
        chords=req.chords,
        allow_extended_ranges=req.allow_extended_ranges,
    )

    colored_xml = build_colored_musicxml(
        voicings=voicings,
        chords=req.chords,
        key=parsed_key,
        title=f"Проверка голосоведения: {report.grade}",
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
    file: UploadFile | None = File(None),
    json_body: FileUploadJsonRequest | None = None,
) -> dict[str, Any]:
    """
    Imports MusicXML (.musicxml, .xml) or MIDI (.mid, .midi) file.
    Supports both multipart form-data and direct JSON with base64/text.
    """
    import base64

    filename = ""
    content = b""

    if file is not None:
        filename = file.filename or "upload"
        content = await file.read()
    elif json_body is not None:
        filename = json_body.filename
        if json_body.xml_content:
            content = json_body.xml_content.encode("utf-8")
        elif json_body.content_base64:
            content = base64.b64decode(json_body.content_base64)
    else:
        raise HTTPException(status_code=400, detail="Файл не передан.")

    if not content:
        raise HTTPException(status_code=400, detail="Файл пуст.")

    if filename.endswith((".xml", ".musicxml")):
        xml_text = content.decode("utf-8", errors="ignore")
        res = parse_musicxml_content(xml_text)
        return {
            "format": "musicxml",
            "filename": filename,
            "soprano_melody": res["soprano_melody"],
            "satb_voicings": res["satb_voicings"],
            "chords": res["chords"],
            "detected_key": res["detected_key"],
        }
    elif filename.endswith((".mid", ".midi")):
        res = parse_midi_file(content)
        # Auto detect key from soprano
        detected_key = detect_key_from_melody(res["soprano_melody"]) if res["soprano_melody"] else CANONICAL_KEYS[0]
        return {
            "format": "midi",
            "filename": filename,
            "soprano_melody": res["soprano_melody"],
            "satb_voicings": res["satb_voicings"],
            "chords": [],
            "detected_key": detected_key,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат файла. Поддерживаются .musicxml, .xml, .mid, .midi",
        )


@router.post("/export/midi")
def api_export_midi(req: ExportMidiRequest):
    """Exports SATB voicings to binary MIDI file download."""
    voicings = [
        Voicing(soprano=v.soprano, alto=v.alto, tenor=v.tenor, bass=v.bass)
        for v in req.voicings
    ]
    data = generate_midi_bytes(voicings, bpm=req.bpm)
    return Response(
        content=data,
        media_type="audio/midi",
        headers={"Content-Disposition": 'attachment; filename="harmonization.mid"'},
    )


@router.post("/export/musicxml")
def api_export_musicxml(req: ExportMusicXmlRequest):
    """Exports SATB voicings to MusicXML file download."""
    voicings = [
        Voicing(soprano=v.soprano, alto=v.alto, tenor=v.tenor, bass=v.bass)
        for v in req.voicings
    ]
    parsed_key = Key(tonic=req.key.tonic, mode=req.key.mode)
    xml_str = build_colored_musicxml(
        voicings=voicings,
        chords=req.chords,
        key=parsed_key,
        title=req.title,
    )
    return Response(
        content=xml_str,
        media_type="application/vnd.recordare.musicxml+xml",
        headers={"Content-Disposition": 'attachment; filename="harmonization.musicxml"'},
    )
