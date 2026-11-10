"""
Student Homework Grader ("Консерваторский инспектор").
Validates student SATB solutions using RuleEngine and generates precise,
pedagogical Russian diagnostic reports with measure numbers and note names.
"""

from __future__ import annotations

from typing import Any, Sequence
from dataclasses import dataclass, asdict

from src.harmony.core.types import Key, Voicing, Chord, to_satb, parse_key
from src.harmony.rules.engine import RuleEngine
from backend.importers import midi_to_note_name

VOICE_NAMES_RU = ("сопрано", "альт", "тенор", "бас")
VOICE_NAMES_EN = ("Soprano", "Alto", "Tenor", "Bass")


@dataclass
class GraderViolation:
    measure: int
    chord_index: int
    rule_id: str
    severity: str  # "hard_gate" | "soft_penalty"
    message_ru: str
    voices: list[str]
    notes: list[str]


@dataclass
class GraderReport:
    is_valid: bool
    total_violations: int
    hard_violations_count: int
    soft_violations_count: int
    violations: list[dict[str, Any]]
    problem_measures: list[int]
    summary_verdict: str
    grade: str  # "5 (Отлично)", "4 (Хорошо)", "3 (Удовлетворительно)", "2 (Не зачтено)"


def _format_rule_message(
    rule_id: str,
    desc: str,
    measure: int,
    chord_idx: int,
    v_prev: Any | None,
    v_curr: Any,
    voices_tuple: tuple[int, ...] | None,
) -> tuple[str, list[str], list[str]]:
    """Generates precise Russian critique with exact note names and voice names."""
    curr_satb = to_satb(v_curr)
    prev_satb = to_satb(v_prev) if v_prev is not None else None

    involved_voices: list[str] = []
    involved_notes: list[str] = []

    if voices_tuple:
        involved_voices = [VOICE_NAMES_RU[v] for v in voices_tuple]
        if prev_satb:
            for v in voices_tuple:
                p_name = midi_to_note_name(prev_satb[v])
                c_name = midi_to_note_name(curr_satb[v])
                involved_notes.append(f"{VOICE_NAMES_RU[v]}: {p_name} -> {c_name}")
        else:
            for v in voices_tuple:
                c_name = midi_to_note_name(curr_satb[v])
                involved_notes.append(f"{VOICE_NAMES_RU[v]}: {c_name}")

    # Specific formatting per rule
    if rule_id == "PARALLEL_FIFTHS":
        if voices_tuple and len(voices_tuple) == 2 and prev_satb:
            v1, v2 = voices_tuple
            p1, p2 = midi_to_note_name(prev_satb[v1]), midi_to_note_name(prev_satb[v2])
            c1, c2 = midi_to_note_name(curr_satb[v1]), midi_to_note_name(curr_satb[v2])
            return (
                f"Такт {measure}: Параллельные квинты между {VOICE_NAMES_RU[v1]} и {VOICE_NAMES_RU[v2]} "
                f"({p1}-{p2} → {c1}-{c2})",
                involved_voices,
                involved_notes,
            )
        return (f"Такт {measure}: Параллельные квинты в голосоведении", involved_voices, involved_notes)

    if rule_id == "PARALLEL_OCTAVES":
        if voices_tuple and len(voices_tuple) == 2 and prev_satb:
            v1, v2 = voices_tuple
            p1, p2 = midi_to_note_name(prev_satb[v1]), midi_to_note_name(prev_satb[v2])
            c1, c2 = midi_to_note_name(curr_satb[v1]), midi_to_note_name(curr_satb[v2])
            return (
                f"Такт {measure}: Параллельные октавы между {VOICE_NAMES_RU[v1]} и {VOICE_NAMES_RU[v2]} "
                f"({p1}-{p2} → {c1}-{c2})",
                involved_voices,
                involved_notes,
            )
        return (f"Такт {measure}: Параллельные октавы в голосоведении", involved_voices, involved_notes)

    if rule_id == "CONTRARY_OCTAVES":
        return (f"Такт {measure}: Противоположные октавы между голосами", involved_voices, involved_notes)

    if rule_id == "CONTRARY_FIFTHS":
        return (f"Такт {measure}: Противоположные квинты между голосами", involved_voices, involved_notes)

    if rule_id == "HIDDEN_FIFTHS_OCTAVES":
        return (
            f"Такт {measure}: Скрытые квинты/октавы в крайних голосах (сопрано и бас идут в прямом движении без поступенного шага)",
            ["сопрано", "бас"],
            involved_notes,
        )

    if rule_id == "VOICE_CROSSING":
        return (f"Такт {measure}: Перекрещивание голосов (нарушен высотный порядок SATB)", involved_voices, involved_notes)

    if rule_id == "VOICE_RANGE_BOUNDS":
        return (f"Такт {measure}: Выход голоса за пределы допустимого вокального диапазона хора", involved_voices, involved_notes)

    if rule_id == "UPPER_VOICE_SPACING_LIMIT":
        return (f"Такт {measure}: Разрыв фактуры: расстояние между верхними голосами превышает чистую октаву", involved_voices, involved_notes)

    if rule_id == "BASS_TENOR_SPACING_LIMIT":
        return (f"Такт {measure}: Расстояние между тенором и басом превышает две октавы", ["тенор", "бас"], involved_notes)

    if rule_id == "VOICE_OVERLAPPING":
        return (f"Такт {measure}: Перекрывание голосов: голос идет выше/ниже предыдущей ноты соседнего голоса", involved_voices, involved_notes)

    if rule_id == "DIRECT_UNISON":
        return (f"Такт {measure}: Взятие или оставление унисона прямым движением голосов воспрещается", involved_voices, involved_notes)

    if rule_id == "VOICE_UNISON":
        if voices_tuple and len(voices_tuple) == 2:
            v1, v2 = voices_tuple
            return (
                f"Такт {measure}: Недопустимый унисон между соседними голосами ({VOICE_NAMES_RU[v1]} и {VOICE_NAMES_RU[v2]})",
                involved_voices,
                involved_notes,
            )
        return (f"Такт {measure}: Недопустимый унисон между соседними голосами", involved_voices, involved_notes)

    if rule_id == "CHORD_THIRD_MISSING":
        return (f"Такт {measure}: В аккорде отсутствует обязательный терцовый тон", involved_voices, involved_notes)

    if rule_id == "CHORD_FIFTH_MISSING":
        return (f"Такт {measure}: В аккорде отсутствует обязательный квинтовый тон", involved_voices, involved_notes)

    if rule_id == "CADENCE_K64_INITIAL":
        return (f"Такт {measure}: Кадансовый квартсекстаккорд K64 запрещен в качестве начального аккорда", involved_voices, involved_notes)

    if rule_id == "MELODIC_AUGMENTED_INTERVAL":
        return (f"Такт {measure}: Запрещенный мелодический ход на увеличенный интервал (ув.2 / ув.4)", involved_voices, involved_notes)

    if rule_id == "MELODIC_SEVENTH_LEAP":
        return (f"Такт {measure}: Запрещенный мелодический скачок на септиму", involved_voices, involved_notes)

    if rule_id == "DOUBLING_MAIN_TRIAD_ROOT":
        if desc and "root not doubled" in desc.lower():
            return (f"Такт {measure}: Недопустимое удвоение в главном трезвучии (прима не удвоена)", involved_voices, involved_notes)
        return (f"Такт {measure}: Недопустимое удвоение в главном трезвучии (удвоена терция вместо примы)", involved_voices, involved_notes)

    if rule_id == "DOUBLING_SEXTACCORD":
        return (f"Такт {measure}: Недопустимое удвоение в секстаккорде (удваивается прима или квинта)", involved_voices, involved_notes)

    if rule_id == "DOUBLING_D6_LEADING_TONE":
        return (f"Такт {measure}: В секстаккорде D6 удвоение вводного тона категорически запрещено", involved_voices, involved_notes)

    if rule_id == "DOUBLING_K64_BASS_ONLY":
        return (f"Такт {measure}: Удвоена терция в квартсекстаккорде K64 (в K64 удваивается строго бас/квинта)", involved_voices, involved_notes)

    if rule_id == "DOUBLING_DECEPTIVE_VI_THIRD":
        return (f"Такт {measure}: В трезвучии VI ступени при прерванном обороте (D -> VI) обязана удваиваться терция", involved_voices, involved_notes)

    if rule_id == "DOUBLING_SECONDARY_DOMINANT":
        return (f"Такт {measure}: В побочной доминанте запрещено удваивать альтерированный вводный тон", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_SEVENTH_DOWN":
        return (f"Такт {measure}: Септима септаккорда брошена без обязательного разрешения на ступень вниз", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_LEADING_TONE_UP":
        return (f"Такт {measure}: Вводный тон (VII ступень) в крайнем голосе брошен вниз без разрешения в тонику", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_D43_TO_T6":
        return (f"Такт {measure}: Терцквартаккорд D43 обязан разрешаться в T6", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_D2_TO_T6":
        return (f"Такт {measure}: Секундаккорд D2 обязан разрешаться в T6", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_VII7_SEVENTH_DOWN":
        return (f"Такт {measure}: Септима вводного септаккорда VII7 обязана разрешаться на ступень вниз", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_VII7_FIFTH_DOWN":
        return (f"Такт {measure}: Квинта вводного септаккорда VII7 обязана разрешаться вниз в терцию тоники", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_VII7_LEADING_TONE_UP":
        return (f"Такт {measure}: Вводный тон септаккорда VII7 обязан разрешаться вверх в тонику", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_DD_TARGET":
        return (f"Такт {measure}: Двойная доминанта обязана разрешаться в K64, D или D7", involved_voices, involved_notes)

    if rule_id == "RESOLUTION_SECONDARY_DOMINANT":
        return (f"Такт {measure}: Альтерированный вводный тон побочной доминанты обязан разрешаться на полутон вверх", involved_voices, involved_notes)

    if rule_id == "FALSE_RELATION_PERECHENIE":
        return (f"Такт {measure}: Перечение: хроматический полутон между разными голосами без плавного хода", involved_voices, involved_notes)

    if rule_id == "CADENCE_K64_STRONG_BEAT":
        return (f"Такт {measure}: Каденционный K64 обязан стоять на сильной доле относительно последующей доминанты", involved_voices, involved_notes)

    if rule_id == "SYNTAX_NO_D_TO_S":
        return (f"Такт {measure}: Запрещенный функциональный откат из доминанты в субдоминанту (D -> S)", involved_voices, involved_notes)

    if rule_id == "SYNTAX_NO_D_TO_K64":
        return (f"Такт {measure}: Запрещенный переход из доминанты в кадансовый квартсекстаккорд (D -> K64)", involved_voices, involved_notes)

    if rule_id == "SYNTAX_K64_MUST_RESOLVE_TO_D":
        return (f"Такт {measure}: Кадансовый квартсекстаккорд обязан разрешаться в доминанту (D или D7)", involved_voices, involved_notes)

    # Fallback to description
    return (f"Такт {measure}: {desc or rule_id}", involved_voices, involved_notes)


def grade_satb_solution(
    voicings: Sequence[Any],
    key: Any = "C Major",
    chords: Sequence[Any] | None = None,
    allow_extended_ranges: bool = False,
    time_signature: Any = "4/4",
    durations: Sequence[Any] | None = None,
) -> GraderReport:
    """
    Grades an entire 4-part SATB progression using the Brigade RuleEngine.
    Returns structured diagnostic feedback with problem measures, severity,
    and a final pedagogical grade according to the Moscow Conservatory standards.
    Supports variable meters (3/4, 2/4, 6/8, 4/4) and dotted durations.
    """
    if not voicings:
        return GraderReport(
            is_valid=False,
            total_violations=1,
            hard_violations_count=1,
            soft_violations_count=0,
            violations=[{
                "measure": 1,
                "chord_index": 1,
                "rule_id": "EMPTY_SCORE",
                "severity": "hard_gate",
                "message_ru": "Партитура пуста: отсутствуют аккорды для проверки.",
                "voices": [],
                "notes": [],
            }],
            problem_measures=[1],
            summary_verdict="Партитура пуста.",
            grade="2 (Не зачтено)",
        )

    from src.harmony.core.types import calculate_metric_structure, to_satb
    parsed_key = key if isinstance(key, Key) else Key(tonic=parse_key(key)[0], mode=parse_key(key)[1])
    engine = RuleEngine(allow_extended_ranges=allow_extended_ranges)

    # Calculate metric structure and exact measure indices
    melody_items = []
    for i, v in enumerate(voicings):
        dur = durations[i] if durations and i < len(durations) else "half"
        melody_items.append({"pitch": to_satb(v)[0], "duration": dur})
    metric_info = calculate_metric_structure(melody_items, default_time_signature=time_signature)

    violations_list: list[GraderViolation] = []
    problem_measures_set: set[int] = set()

    chord_list = list(chords) if chords else []
    seen_violations: set[tuple[int, int, str, tuple[str, ...]]] = set()

    def _record_violation(viol: Any, measure_num: int, chord_idx: int, v_prev: Any | None, v_curr: Any) -> None:
        msg_ru, voices, notes = _format_rule_message(
            rule_id=viol.rule_id,
            desc=viol.description,
            measure=measure_num,
            chord_idx=chord_idx,
            v_prev=v_prev,
            v_curr=v_curr,
            voices_tuple=viol.voices,
        )
        dedup_key = (measure_num, chord_idx, viol.rule_id, tuple(voices))
        if dedup_key in seen_violations:
            return
        seen_violations.add(dedup_key)

        violations_list.append(GraderViolation(
            measure=measure_num,
            chord_index=chord_idx,
            rule_id=viol.rule_id,
            severity=viol.severity,
            message_ru=msg_ru,
            voices=voices,
            notes=notes,
        ))
        if viol.is_hard:
            problem_measures_set.add(measure_num)

    # 1. Validate the initial vertical slice (chord 0)
    m0 = metric_info[0]["measure"]
    db0 = metric_info[0]["is_downbeat"]
    c0 = chord_list[0] if chord_list else None
    is_single = (len(voicings) == 1)
    res_first = engine.validate_voicing(
        voicing=voicings[0],
        chord=c0,
        key=parsed_key,
        is_downbeat=db0,
        is_final_chord=is_single,
    )
    for viol in res_first.violations:
        _record_violation(viol, m0, 1, None, voicings[0])

    # 2. Validate all transitions and subsequent slices (chords 1..N-1)
    # Note: engine.validate() evaluates both slice i (spacing, doubling with prev_chord context,
    # and metric syntax) as well as transition i-1 -> i (voice leading, resolutions, chromatic).
    for i in range(1, len(voicings)):
        measure_num = metric_info[i]["measure"]
        is_downbeat = metric_info[i]["is_downbeat"]
        prev_v = voicings[i - 1]
        curr_v = voicings[i]
        prev_chord = chord_list[i - 1] if (i - 1) < len(chord_list) else None
        curr_chord = chord_list[i] if i < len(chord_list) else None
        is_final = (i == len(voicings) - 1)

        res_trans = engine.validate(
            prev_voicing=prev_v,
            curr_voicing=curr_v,
            prev_chord=prev_chord,
            curr_chord=curr_chord,
            key=parsed_key,
            is_downbeat=is_downbeat,
            is_final_chord=is_final,
        )

        for viol in res_trans.violations:
            # Skip non-rule heuristic costs
            if not getattr(viol, "rule_id", None):
                continue
            _record_violation(viol, measure_num, i + 1, prev_v, curr_v)

    hard_count = sum(1 for v in violations_list if v.severity == "hard_gate")
    soft_count = sum(1 for v in violations_list if v.severity != "hard_gate")
    is_clean = (hard_count == 0)

    # Determine grade
    if is_clean:
        grade = "5 (Отлично / Без замечаний)"
        verdict = "Безупречное голосоведение! Все каноны Бригадного учебника строго соблюдены."
    elif hard_count == 1:
        grade = "3 (Удовлетворительно)"
        verdict = f"Обнаружена 1 грубая ошибка правил голосоведения в такте {list(problem_measures_set)[0]}."
    elif hard_count == 2:
        grade = "2 (Не зачтено)"
        verdict = f"Обнаружено {hard_count} грубых нарушений правил Способина. Требуется исправление."
    else:
        grade = "2 (Не зачтено / Полный разнос)"
        verdict = f"Грубейшие нарушения ({hard_count} ошибок)! Параллелизмы или запрещенные удвоения ломают фактуру."

    return GraderReport(
        is_valid=is_clean,
        total_violations=len(violations_list),
        hard_violations_count=hard_count,
        soft_violations_count=soft_count,
        violations=[asdict(v) for v in violations_list],
        problem_measures=sorted(list(problem_measures_set)),
        summary_verdict=verdict,
        grade=grade,
    )
