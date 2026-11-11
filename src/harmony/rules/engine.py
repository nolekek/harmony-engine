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


def check_syntax_rules(
    prev_chord: Any | None,
    curr_chord: Any | None,
    is_downbeat: bool = False,
    phrase_boundary: bool = False,
) -> list[RuleViolation]:
    """
    Core Brigade syntax rules for harmonic functional progressions:
    - K64 cannot appear as initial chord of piece
    - K64 must be placed on a strong/downbeat
    - D -> S prohibition: strictly forbidden inside phrases, permitted only at phrase boundaries
    - Dominant cannot regress to K64
    - K64 must resolve to Dominant (D or D7)
    """
    violations: list[RuleViolation] = []
    curr_sym = parse_chord_symbol(curr_chord) if curr_chord is not None else ""
    prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""

    # K64 is strictly forbidden as initial chord of a progression
    if curr_sym == "K64" and (prev_chord is None or prev_sym == ""):
        violations.append(
            RuleViolation(
                rule_id="CADENCE_K64_INITIAL",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    "K64 is forbidden as the initial chord of a piece; "
                    "it must appear only in a cadential progression"
                ),
            )
        )

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

    # Functional regression prohibition: D -> S (forbidden inside phrase, allowed on phrase boundary)
    if (prev_sym in DOMINANT_GROUP or prev_sym.startswith("DD")) and curr_sym in SUBDOMINANT_GROUP:
        if not phrase_boundary:
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
            "contrary_bass_bonus": 0.0,
            "direct_bass_penalty": 3.0,
            "bass_leap_penalty": 2.0,
        }
        if weights:
            self.weights.update(weights)
        self.style_scorer = style_scorer

        self._load_catalog(rules_catalog_path)

    def get_rule_description(self, rule_id: str) -> str | None:
        """Returns the human-readable description of a rule from the catalog if loaded."""
        rule = self.rules_registry.get(rule_id)
        if rule and isinstance(rule, dict) and "description" in rule:
            return rule["description"]
        return None

    def get_rule_severity(self, rule_id: str) -> str | None:
        """Returns the severity of a rule from the catalog if loaded."""
        rule = self.rules_registry.get(rule_id)
        if rule and isinstance(rule, dict) and "severity" in rule:
            return rule["severity"]
        return None

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
        phrase_boundary: bool = False,
    ) -> list[RuleViolation]:
        """
        Validates macro harmonic syntax using the unified check_syntax_rules predicate.
        """
        return check_syntax_rules(
            prev_chord=prev_chord,
            curr_chord=curr_chord,
            is_downbeat=is_downbeat,
            phrase_boundary=phrase_boundary,
        )

    _OPENING_PENALTY: dict[str, float] = {
        "T": 0.0, "t": 0.0,
        "T6": 1.0, "t6": 1.0,
        "VI": 2.0, "vi": 2.0,
        "S": 3.0, "S6": 3.0, "s": 3.0, "s6": 3.0,
        "II": 3.0, "II6": 3.0,
        "III": 4.0, "III6": 4.0,
        "D": 5.0, "D6": 5.0, "D7": 5.0,
    }

    def compute_initial_cost(
        self,
        voicing: Any,
        chord: Any = None,
        key: Any = None,
    ) -> float:
        """
        Computes heuristic cost for the starting state (step 0).
        Penalizes extreme vocal registers, wide spacing gaps, and adjacent unisons,
        and prefers a tonic opening (T > T6 > VI...). Guarantees step 0 cost >= 0.0.
        """
        satb = to_satb(voicing)
        cost = 1.0

        # Functional opening preference: classical exercises open on the tonic,
        # not on a mediant/submediant wandering chord.
        if chord is not None:
            sym = parse_chord_symbol(chord)
            cost += self._OPENING_PENALTY.get(sym, 6.0)

        # Distance from center of comfortable vocal tessitura:
        # S ~ 69 (A4), A ~ 62 (D4), T ~ 55 (G3), B ~ 47 (B2)
        cost += abs(satb[0] - 69) * 0.05
        cost += abs(satb[1] - 62) * 0.05
        cost += abs(satb[2] - 55) * 0.05
        cost += abs(satb[3] - 47) * 0.05

        # Penalize adjacent voice unisons (S==A, A==T, T==B)
        if satb[0] == satb[1]:
            cost += 4.0
        if satb[1] == satb[2]:
            cost += 3.0
        if satb[2] == satb[3]:
            cost += 4.0

        # Penalize upper voice spacing gaps > 8 semitones
        gap_sa = satb[0] - satb[1]
        gap_at = satb[1] - satb[2]
        gap_tb = satb[2] - satb[3]
        if gap_sa > 8:
            cost += (gap_sa - 8) * 0.25
        if gap_at > 8:
            cost += (gap_at - 8) * 0.25
        if gap_tb > 16:
            cost += (gap_tb - 16) * 0.15

        return round(cost, 2)

    def compute_soft_cost(
        self,
        prev_voicing: Any,
        curr_voicing: Any,
    ) -> float:
        """
        Computes non-negative heuristic transition cost (REPORT #53):
        - Movement cost of middle voices (Alto + Tenor)
        - Direct motion penalty between Soprano and Bass
        - Smooth bass line preference
        Guarantees cost >= 0.0.
        """
        prev_satb = to_satb(prev_voicing)
        curr_satb = to_satb(curr_voicing)

        cost = 0.0

        # Law of shortest path: |dA| + |dT|
        da = abs(curr_satb[1] - prev_satb[1])
        dt = abs(curr_satb[2] - prev_satb[2])
        movement_cost = (da + dt) * self.weights.get("shortest_path", 1.0)
        cost += movement_cost

        # Bass vs Soprano relative motion: non-negative scheme
        ds = curr_satb[0] - prev_satb[0]
        db = curr_satb[3] - prev_satb[3]
        if ds != 0 and db != 0:
            if ds * db > 0:
                cost += self.weights.get("direct_bass_penalty", 3.0)
            elif ds * db < 0:
                # Contrary motion is rewarded by applying 0 penalty
                pass

        # Smooth bass line: penalty for leaps wider than a fifth (> 7 semitones)
        abs_db = abs(db)
        if abs_db > 7:
            cost += self.weights.get("bass_leap_penalty", 2.0) * ((abs_db - 7) / 2.0)

        # Neuro-symbolic style prior scorer (if provided)
        if self.style_scorer is not None:
            cost += self.style_scorer.score_transition(prev_satb, curr_satb)

        return max(0.0, cost)

    _DOMINANT_FAMILY = {
        "D", "d", "D6", "d6", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2",
        "K64", "k64",
    }

    def compute_functional_cost(
        self,
        prev_chord: Any | None,
        curr_chord: Any | None,
        is_final_chord: bool = False,
    ) -> float:
        """Non-negative harmonic-quality cost.

        Cadences must be prepared by a dominant (authentic cadence); wandering
        mediant/submediant chords outside a deceptive resolution are penalized.
        """
        if prev_chord is None or curr_chord is None:
            return 0.0
        prev_sym = parse_chord_symbol(prev_chord)
        curr_sym = parse_chord_symbol(curr_chord)
        cost = 0.0

        if is_final_chord:
            if curr_sym in ("T", "t", "T6", "t6"):
                if prev_sym in self._DOMINANT_FAMILY:
                    cost += 0.0
                elif prev_sym in ("VI", "vi"):
                    cost += 1.5  # deceptive cadence as the final is weak
                else:
                    cost += 4.0  # plagal / unprepared final tonic
            elif curr_sym in ("D", "d", "D7", "d7"):
                cost += 0.5  # half cadence is legitimate but less conclusive
            return cost

        if curr_sym in ("III", "iii", "III6", "iii6"):
            cost += 2.5
        if curr_sym in ("VI", "vi") and prev_sym not in self._DOMINANT_FAMILY:
            cost += 2.0
        if prev_sym in self._DOMINANT_FAMILY and curr_sym in ("VI", "vi"):
            cost += 0.5
        return cost

    def validate(
        self,
        prev_voicing: Any | None,
        curr_voicing: Any,
        prev_chord: Any | None = None,
        curr_chord: Any | None = None,
        key: Any = None,
        is_downbeat: bool = False,
        is_final_chord: bool = False,
        phrase_boundary: bool = False,
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
                is_final_chord=is_final_chord,
            )
        )

        # 2. Macro syntax checks (metric placement & regression)
        violations.extend(
            self.check_syntax(
                prev_chord,
                curr_chord,
                is_downbeat=is_downbeat,
                phrase_boundary=phrase_boundary,
            )
        )

        # 3. Transition checks (if previous voicing is present)
        soft_cost = 0.0
        if prev_voicing is not None:
            violations.extend(
                validate_voice_leading(
                    prev_voicing,
                    curr_voicing,
                    key=key,
                    prev_chord=prev_chord,
                    curr_chord=curr_chord,
                )
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
            soft_cost += self.compute_functional_cost(
                prev_chord, curr_chord, is_final_chord=is_final_chord
            )
        else:
            soft_cost = self.compute_initial_cost(curr_voicing, chord=curr_chord, key=key)

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
            cost=max(0.0, soft_cost),
        )

    def validate_voicing(
        self,
        voicing: Any,
        chord: Any | None = None,
        key: Any = None,
        is_downbeat: bool = False,
        is_final_chord: bool = False,
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
            is_final_chord=is_final_chord,
        )
