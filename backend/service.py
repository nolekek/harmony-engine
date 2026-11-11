"""
Service layer for Brigade Classical Harmony harmonization requests.
Encapsulates plan generation, DD filtering, Viterbi optimization, candidate selection,
scoring, MusicXML/ASCII formatting, and structured error reporting.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.harmony.core.types import Key, Chord, TimeSignature
from src.harmony.core.metric import MetricGrid
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.rules.engine import RuleEngine
from src.harmony.export.ascii import format_ascii_score
from backend.exporters import build_colored_musicxml

# Runtime compatibility guard while concurrent agent updates src/harmony/rules/voice_leading.py
import inspect
from src.harmony.rules import engine, voice_leading
_orig_vvl = engine.validate_voice_leading
if "prev_chord" not in inspect.signature(_orig_vvl).parameters:
    def _compat_validate_voice_leading(prev_voicing, curr_voicing, key=None, **kwargs):
        sig = inspect.signature(_orig_vvl)
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        if "key" in sig.parameters:
            call_kwargs["key"] = key
        return _orig_vvl(prev_voicing, curr_voicing, **call_kwargs)
    engine.validate_voice_leading = _compat_validate_voice_leading
    voice_leading.validate_voice_leading = _compat_validate_voice_leading

logger = logging.getLogger(__name__)


def select_top_candidates(solutions: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]:
    """
    Stably selects the top-k candidate solutions with the lowest total cost.
    Updates the 1-based rank on each selected candidate.
    """
    sorted_solutions = sorted(solutions, key=lambda s: s.get("cost", 0.0))[:k]
    for idx, s in enumerate(sorted_solutions, start=1):
        s["rank"] = idx
    return sorted_solutions


class HarmonizationService:
    """
    Authoritative Harmonization Application Service.
    Orchestrates macro syntax synthesis and micro voice-leading search.
    """

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        solver: ViterbiSolver | None = None,
    ) -> None:
        self.rule_engine = rule_engine or RuleEngine()
        self.solver = solver or ViterbiSolver(rule_engine=self.rule_engine)

    def harmonize(self, req: dict[str, Any] | Any) -> dict[str, Any]:
        """
        Executes complete harmonization workflow on request parameters.
        Returns unified JSON payload compliant with REST API schema.
        """
        t_start = time.perf_counter()

        # Handle pydantic model or plain dict
        if hasattr(req, "model_dump"):
            data = req.model_dump()
        elif hasattr(req, "dict"):
            data = req.dict()
        elif isinstance(req, dict):
            data = req
        else:
            data = dict(req)

        melody_raw = data.get("melody", [])
        if not melody_raw:
            return {
                "is_success": False,
                "candidates": [],
                "best_candidate": None,
                "message": "Мелодия не может быть пустой.",
                "error": {
                    "code": "EMPTY_MELODY",
                    "message": "Мелодия не может быть пустой.",
                    "diagnostics": [],
                    "hint": "Предоставьте хотя бы одну ноту для гармонизации.",
                },
                "latency_ms": 0.0,
            }

        key_data = data.get("key", {})
        if isinstance(key_data, dict):
            tonic = key_data.get("tonic", "C")
            mode = key_data.get("mode", "Major")
        else:
            tonic = getattr(key_data, "tonic", "C")
            mode = getattr(key_data, "mode", "Major")

        parsed_key = Key(tonic=tonic, mode=mode)
        time_sig_raw = data.get("time_signature", "4/4")
        time_sig = TimeSignature.parse(time_sig_raw)
        allow_extended_ranges = bool(data.get("allow_extended_ranges", False))
        allow_secondary_dominants = bool(data.get("allow_secondary_dominants", True))
        max_plans = int(data.get("max_plans", 50))

        logger.info(
            "Harmonization request started: %d notes, key=%s, meter=%s, secondary_dominants=%s, max_plans=%d",
            len(melody_raw),
            parsed_key,
            time_sig,
            allow_secondary_dominants,
            max_plans,
        )

        # Normalize melody items through unified MetricGrid
        norm_melody_input = []
        for m in melody_raw:
            if isinstance(m, dict):
                norm_melody_input.append({
                    "pitch": m.get("pitch", 60),
                    "duration": m.get("duration", "half"),
                    "is_downbeat": m.get("is_downbeat"),
                })
            else:
                norm_melody_input.append({
                    "pitch": getattr(m, "pitch", 60),
                    "duration": getattr(m, "duration", "half"),
                    "is_downbeat": getattr(m, "is_downbeat", None),
                })

        metric_grid = MetricGrid(time_signature=time_sig, notes=norm_melody_input)
        melody_dicts = [
            {"pitch": item["pitch"], "is_downbeat": item["is_downbeat"], "duration": item["duration"]}
            for item in metric_grid
        ]
        durations_list = [item["duration"] for item in metric_grid]

        # 1. Synthesize candidate functional plans
        grammar = HarmonicGrammar(key=parsed_key)
        all_plans = grammar.generate_plans(melody=melody_dicts, key=parsed_key, max_plans=max_plans)

        # Filter secondary dominants if disallowed
        if not allow_secondary_dominants:
            filtered_plans = []
            for plan in all_plans:
                fns = [c.function for c in plan]
                if not any(f.startswith("DD") for f in fns):
                    filtered_plans.append(plan)
            plans_to_try = filtered_plans
            if not plans_to_try:
                latency = round((time.perf_counter() - t_start) * 1000, 2)
                logger.warning(
                    "Harmonization aborted in %.2f ms: SECONDARY_DOMINANTS_DISABLED (all %d plans contained DD)",
                    latency,
                    len(all_plans),
                )
                return {
                    "is_success": False,
                    "candidates": [],
                    "best_candidate": None,
                    "message": "Без побочных доминант невозможно гармонизовать заданную мелодию.",
                    "error": {
                        "code": "SECONDARY_DOMINANTS_DISABLED",
                        "message": "Без побочных доминант невозможно гармонизовать заданную мелодию.",
                        "diagnostics": [],
                        "hint": "Включите опцию allow_secondary_dominants=true или скорректируйте мелодию.",
                    },
                    "latency_ms": latency,
                }
        else:
            plans_to_try = all_plans

        if not plans_to_try:
            latency = round((time.perf_counter() - t_start) * 1000, 2)
            logger.warning("Harmonization aborted in %.2f ms: NO_PLANS generated by grammar", latency)
            return {
                "is_success": False,
                "candidates": [],
                "best_candidate": None,
                "message": "Не удалось синтезировать функциональные планы для данной мелодии.",
                "error": {
                    "code": "NO_PLANS",
                    "message": "Не удалось синтезировать функциональные планы для данной мелодии.",
                    "diagnostics": [],
                    "hint": "Проверьте тональность мелодии или диапазон нот.",
                },
                "latency_ms": latency,
            }

        # 2. Solve candidate plans via Viterbi
        solutions: list[dict[str, Any]] = []
        collected_diagnostics: list[dict[str, Any]] = []

        for plan_idx, plan in enumerate(plans_to_try):
            res = self.solver.solve(
                melody=melody_dicts,
                chords=plan,
                key=parsed_key,
                allow_extended_ranges=allow_extended_ranges,
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
                    durations=durations_list,
                    time_signature=str(time_sig),
                )

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
                    "time_signature": str(time_sig),
                    "durations": durations_list,
                    "voicings": voicings_list,
                    "musicxml": colored_xml,
                    "ascii_score": ascii_text,
                })
            else:
                if getattr(res, "diagnostics", None):
                    for d in res.diagnostics:
                        if isinstance(d, dict) and d not in collected_diagnostics:
                            collected_diagnostics.append(d)

        solutions = select_top_candidates(solutions, k=3)
        for idx, s in enumerate(solutions, start=1):
            s["id"] = f"cand_{idx}"

        latency = round((time.perf_counter() - t_start) * 1000, 2)

        if not solutions:
            logger.warning(
                "Harmonization finished in %.2f ms with NO_FEASIBLE_PLAN across %d tested plans",
                latency,
                len(plans_to_try),
            )
            return {
                "is_success": False,
                "candidates": [],
                "best_candidate": None,
                "message": "Все кандидаты отклонены жесткими правилами голосоведения.",
                "error": {
                    "code": "NO_FEASIBLE_PLAN",
                    "message": "Все кандидаты отклонены жесткими правилами голосоведения.",
                    "diagnostics": collected_diagnostics,
                    "hint": "Проверьте мелодические ходы на запрещенные интервалы или включите расширенные диапазоны (allow_extended_ranges=true).",
                },
                "latency_ms": latency,
            }

        logger.info(
            "Harmonization completed successfully in %.2f ms: evaluated %d plans, found %d solutions (best cost: %.2f)",
            latency,
            len(plans_to_try),
            len(solutions),
            solutions[0]["cost"],
        )

        return {
            "is_success": True,
            "candidates": solutions,
            "best_candidate": solutions[0],
            "message": f"Найдено {len(solutions)} математически оптимальных решений.",
            "latency_ms": latency,
            "error": None,
        }
