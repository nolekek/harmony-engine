"""
Central Brigade Rule Engine for four-part voice leading and texture validation.
Executes hard-gate rule checks and computes soft heuristic costs for dynamic programming.
"""

from typing import Any, Mapping
import json
from pathlib import Path

from src.harmony.core.types import (
    RuleViolation,
    ValidationResult,
    to_satb,
    parse_key,
    parse_chord_symbol,
)
from src.harmony.rules.spacing import validate_spacing
from src.harmony.rules.voice_leading import validate_voice_leading
from src.harmony.rules.doubling import check_doubling
from src.harmony.rules.resolutions import validate_resolutions
from src.harmony.rules.chromatic import validate_chromatic_rules

DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
SUBDOMINANT_GROUP = {"S", "S6", "S64", "s", "s6", "s64", "II", "II6", "II65"}


class RuleEngine:
    """
    Central validation engine implementing Brigade Textbook (Способин et al.) rules.
    """

    def __init__(
        self,
        rules_catalog_path: str | Path | None = None,
        allow_extended_ranges: bool = False,
        weights: Mapping[str, float] | None = None,
        style_scorer: Any | None = None,
    ):
        self.allow_extended_ranges = allow_extended_ranges
        self.rules_registry: dict[str, dict[str, Any]] = {}
        self.weights: dict[str, float] = {
            "shortest_path": 1.0,
            "contrary_bass_bonus": -5.0,
            "direct_bass_penalty": 2.0,
            "bass_leap_penalty": 2.0,
        }
        if weights:
            self.weights.update(weights)
        self.style_scorer = style_scorer

        self._load_catalog(rules_catalog_path)

    def _load_catalog(self, path: str | Path | None) -> None:
        catalog_path = None
        if path:
            p = Path(path)
            if p.exists():
                catalog_path = p
        else:
            default_p = Path(__file__).resolve().parents[3] / "docs" / "brigade_rules.json"
            if default_p.exists():
                catalog_path = default_p

        if catalog_path and catalog_path.exists():
            try:
                data = json.loads(catalog_path.read_text(encoding="utf-8"))
                for r in data.get("rules", []):
                    rid = r.get("id")
                    if rid:
                        self.rules_registry[rid] = r
            except Exception:
                pass

    def check_syntax(
        self,
        prev_chord: Any | None,
        curr_chord: Any | None,
        is_downbeat: bool = False,
    ) -> list[RuleViolation]:
        """
        Validates macro harmonic syntax:
        - K64 metric placement (must be on downbeat)
        - Dominant -> Subdominant prohibition (no D -> S regression)
        """
        violations: list[RuleViolation] = []
        curr_sym = parse_chord_symbol(curr_chord) if curr_chord is not None else ""
        prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""

        # K64 must be on a downbeat
        if curr_sym == "K64" and not is_downbeat:
            violations.append(
                RuleViolation(
                    rule_id="CADENCE_K64_STRONG_BEAT",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        "K64 must appear on a downbeat (strong or relatively strong beat) "
                        "before resolving to D or D7"
                    ),
                )
            )

        # Functional regression prohibition: D -> S
        if prev_sym in DOMINANT_GROUP and curr_sym in SUBDOMINANT_GROUP:
            violations.append(
                RuleViolation(
                    rule_id="SYNTAX_NO_D_TO_S",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Forbidden functional regression from dominant group ({prev_sym}) "
                        f"to subdominant group ({curr_sym})"
                    ),
                )
            )

        # Dominant cannot move to K64 (D -> K64 regression)
        if prev_sym in DOMINANT_GROUP and curr_sym == "K64":
            violations.append(
                RuleViolation(
                    rule_id="SYNTAX_NO_D_TO_K64",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=f"Forbidden regression from dominant ({prev_sym}) to K64",
                )
            )

        # K64 must resolve to dominant (D or D7)
        if prev_sym == "K64" and curr_sym not in ("D", "D7"):
            violations.append(
                RuleViolation(
                    rule_id="SYNTAX_K64_MUST_RESOLVE_TO_D",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=f"K64 must resolve to D or D7, got {curr_sym}",
                )
            )

        return violations

    def compute_soft_cost(
        self,
        prev_voicing: Any,
        curr_voicing: Any,
    ) -> float:
        """
        Computes heuristic transition cost:
        - Movement cost of middle voices (Alto + Tenor)
        - Contrary motion bonus between Soprano and Bass
        - Smooth bass line preference
        """
        prev_satb = to_satb(prev_voicing)
        curr_satb = to_satb(curr_voicing)

        cost = 0.0

        # Law of shortest path: |dA| + |dT|
        da = abs(curr_satb[1] - prev_satb[1])
        dt = abs(curr_satb[2] - prev_satb[2])
        movement_cost = (da + dt) * self.weights["shortest_path"]
        cost += movement_cost

        # Bass vs Soprano relative motion
        ds = curr_satb[0] - prev_satb[0]
        db = curr_satb[3] - prev_satb[3]
        if ds != 0 and db != 0:
            if ds * db < 0:
                # Contrary motion bonus
                cost += self.weights["contrary_bass_bonus"]
            elif ds * db > 0:
                # Direct motion penalty
                cost += self.weights["direct_bass_penalty"]

        # Smooth bass line: penalty for leaps wider than a fifth (> 7 semitones)
        abs_db = abs(db)
        if abs_db > 7:
            cost += self.weights["bass_leap_penalty"] * ((abs_db - 7) / 2.0)

        # Neuro-symbolic style prior scorer (if provided)
        if self.style_scorer is not None:
            cost += self.style_scorer.score_transition(prev_satb, curr_satb)

        return cost

    def validate(
        self,
        prev_voicing: Any | None,
        curr_voicing: Any,
        prev_chord: Any | None = None,
        curr_chord: Any | None = None,
        key: Any = None,
        is_downbeat: bool = False,
    ) -> ValidationResult:
        """
        Validates transition from prev_voicing to curr_voicing or evaluates
        a single starting vertical slice if prev_voicing is None.
        """
        violations: list[RuleViolation] = []

        # 1. Static checks on current vertical slice
        violations.extend(
            validate_spacing(curr_voicing, allow_extended=self.allow_extended_ranges)
        )
        violations.extend(
            check_doubling(
                curr_voicing,
                curr_chord,
                key=key,
                prev_chord=prev_chord,
            )
        )

        # 2. Macro syntax checks (metric placement & regression)
        violations.extend(
            self.check_syntax(prev_chord, curr_chord, is_downbeat=is_downbeat)
        )

        # 3. Transition checks (if previous voicing is present)
        soft_cost = 0.0
        if prev_voicing is not None:
            violations.extend(
                validate_voice_leading(prev_voicing, curr_voicing, key=key)
            )
            violations.extend(
                validate_resolutions(
                    prev_voicing,
                    curr_voicing,
                    prev_chord,
                    curr_chord,
                    key=key,
                )
            )
            violations.extend(
                validate_chromatic_rules(prev_voicing, curr_voicing, key=key)
            )
            soft_cost = self.compute_soft_cost(prev_voicing, curr_voicing)

        # 4. Determine validity and final cost
        has_hard = any(v.is_hard for v in violations)
        if has_hard:
            return ValidationResult(
                is_valid=False,
                violations=violations,
                cost=float("inf"),
            )

        return ValidationResult(
            is_valid=True,
            violations=violations,
            cost=soft_cost,
        )

    def validate_voicing(
        self,
        voicing: Any,
        chord: Any | None = None,
        key: Any = None,
        is_downbeat: bool = False,
    ) -> ValidationResult:
        """
        Convenience method to validate a single isolated vertical slice.
        """
        return self.validate(
            prev_voicing=None,
            curr_voicing=voicing,
            prev_chord=None,
            curr_chord=chord,
            key=key,
            is_downbeat=is_downbeat,
        )
