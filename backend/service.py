"""
Service layer for Brigade Classical Harmony harmonization requests.
Encapsulates plan generation, DD filtering, Viterbi optimization, candidate selection,
scoring, MusicXML/ASCII formatting, and structured error reporting.
"""

from __future__ import annotations

import copy
import logging
import time
from typing import Any

from src.harmony.core.types import Key, Chord, TimeSignature
from src.harmony.core.metric import MetricGrid
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.rules.engine import RuleEngine
from src.harmony.pipeline import Harmonizer
from src.harmony.export.ascii import format_ascii_score
from backend.exporters import build_colored_musicxml

logger = logging.getLogger(__name__)

# Request-level cache for idempotent repeated requests
_SERVICE_REQUEST_CACHE: dict[tuple, dict[str, Any]] = {}


def clear_service_cache() -> None:
    """Flushes the service-level request cache."""
    _SERVICE_REQUEST_CACHE.clear()


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
        self.harmonizer = Harmonizer(rule_engine=self.rule_engine, solver=self.solver)

    def _replanning_candidates(
        self,
        parsed_key: Key,
        melody_raw: list[dict[str, Any]],
        time_sig: TimeSignature,
        durations_list: list[str],
        max_plans: int,
        allow_extended_ranges: bool,
    ) -> list[dict[str, Any]]:
        """Bounded-replanning fallback.

        The fast path walks pre-generated plans one by one; the core engine owns
        macro/micro replanning and can synthesize plans itself when the grammar
        produced none (chromatic NCT lines, minor-key S6 dead ends, ...).

        Note: the raw melody is forwarded unchanged (is_downbeat=None when the
        client omitted the flag) so the core can decide metric placement itself.
        """
        try:
            fallback = self.harmonizer.harmonize(
                melody=melody_raw,
                key=parsed_key,
                time_signature=str(time_sig),
                max_plans=max_plans,
                allow_extended_ranges=allow_extended_ranges,
                allow_replanning=True,
            )
        except TypeError:
            return []
        if fallback is None or not fallback.is_success:
            return []

        candidates: list[dict[str, Any]] = []
        for sol in fallback.solutions:
            chords_list = [c.function for c in sol.chords]
            voicings_list = [
                {"soprano": v.s, "alto": v.a, "tenor": v.t, "bass": v.b}
                for v in sol.voicings
            ]
            ascii_text = format_ascii_score(
                voicings=sol.voicings,
                chords=sol.chords,
                key=f"{parsed_key.tonic} {parsed_key.mode}",
            )
            colored_xml = build_colored_musicxml(
                voicings=sol.voicings,
                chords=sol.chords,
                key=parsed_key,
                title="",
                durations=durations_list,
                time_signature=str(time_sig),
            )
            candidates.append({
                "id": f"cand_{len(candidates) + 1}",
                "rank": len(candidates) + 1,
                "cost": round(sol.cost, 2),
                "chords": chords_list,
                "progression_preview": " → ".join(chords_list),
                "description": (
                    "Полная каденция (replanning)"
                    if "K64" in chords_list
                    else "Автентический оборот (replanning)"
                ),
                "time_signature": str(time_sig),
                "durations": durations_list,
                "voicings": voicings_list,
                "musicxml": colored_xml,
                "ascii_score": ascii_text,
            })
        return candidates

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

        # Request-level cache lookup for identical parameters
        cache_key = (
            tuple((item["pitch"], item["duration"], item["is_downbeat"]) for item in melody_dicts),
            parsed_key.tonic,
            parsed_key.mode,
            str(time_sig),
            allow_extended_ranges,
            allow_secondary_dominants,
            max_plans,
        )
        if cache_key in _SERVICE_REQUEST_CACHE:
            cached_resp = copy.deepcopy(_SERVICE_REQUEST_CACHE[cache_key])
            cached_resp["latency_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
            logger.info("Harmonization returned from request cache in %.2f ms", cached_resp["latency_ms"])
            return cached_resp

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
            # The grammar may legitimately produce no plans (e.g. a chromatic NCT
            # line with an awkward cadence); the replanning engine can still
            # synthesize a functional plan from scratch.
            if allow_secondary_dominants:
                replanned = self._replanning_candidates(
                    parsed_key=parsed_key,
                    melody_raw=norm_melody_input,
                    time_sig=time_sig,
                    durations_list=durations_list,
                    max_plans=max_plans,
                    allow_extended_ranges=allow_extended_ranges,
                )
                if replanned:
                    replanned = select_top_candidates(replanned, k=3)
                    for idx, s in enumerate(replanned, start=1):
                        s["id"] = f"cand_{idx}"
                    latency = round((time.perf_counter() - t_start) * 1000, 2)
                    logger.info(
                        "Harmonization rescued by replanning in %.2f ms: %d candidates",
                        latency,
                        len(replanned),
                    )
                    return {
                        "is_success": True,
                        "candidates": replanned,
                        "best_candidate": replanned[0],
                        "message": f"Найдено {len(replanned)} математически оптимальных решений.",
                        "latency_ms": latency,
                        "error": None,
                    }
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

        best_cost_seen = float("inf")
        stagnant_count = 0
        early_stop_threshold = 15 if len(norm_melody_input) >= 16 else 0
        timeout_sec = float(data.get("timeout_sec", 4.0))

        for plan_idx, plan in enumerate(plans_to_try):
            if time.perf_counter() - t_start > timeout_sec:
                logger.warning(
                    "Harmonization plan evaluation reached timeout limit (%.2fs) after %d/%d plans",
                    timeout_sec,
                    plan_idx,
                    len(plans_to_try),
                )
                break

            res = self.solver.solve(
                melody=melody_dicts,
                chords=plan,
                key=parsed_key,
                allow_extended_ranges=allow_extended_ranges,
            )

            if res.is_success and res.voicings:
                if res.total_cost < best_cost_seen - 1e-4:
                    best_cost_seen = res.total_cost
                    stagnant_count = 0
                else:
                    stagnant_count += 1

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
                    title="",
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
                if len(solutions) >= 3:
                    stagnant_count += 1

            if early_stop_threshold > 0 and len(solutions) >= 3 and stagnant_count >= early_stop_threshold:
                logger.info(
                    "Early stopping triggered at plan %d/%d (best cost: %.2f)",
                    plan_idx + 1,
                    len(plans_to_try),
                    best_cost_seen,
                )
                break

        # 2b. Bounded replanning fallback: the fast path above walks plans one by
        # one; the core engine owns macro/micro replanning for melodies whose
        # plans are all micro-infeasible (e.g. minor-key scales with S6 dead ends).
        if not solutions and allow_secondary_dominants:
            solutions.extend(
                self._replanning_candidates(
                    parsed_key=parsed_key,
                    melody_raw=norm_melody_input,
                    time_sig=time_sig,
                    durations_list=durations_list,
                    max_plans=max_plans,
                    allow_extended_ranges=allow_extended_ranges,
                )
            )

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

        final_response = {
            "is_success": True,
            "candidates": solutions,
            "best_candidate": solutions[0],
            "message": f"Найдено {len(solutions)} математически оптимальных решений.",
            "latency_ms": latency,
            "error": None,
        }
        _SERVICE_REQUEST_CACHE[cache_key] = copy.deepcopy(final_response)
        return final_response

