"""
Core domain model: Modulation and Tonality Relations.

Strictly implements the theory of tonality relations, modulation, and secondary dominants
from the Brigade harmony textbook (Дубовский, Евсеев, Способин, Соколов — «Учебник гармонии»,
главы 26-28, 29, 30, 31):
- First-Degree Related Keys (Тональности первой степени родства, гл. 29)
- Common Pivot Chords and Ranking (Общие посредствующие аккорды, гл. 30)
- Canonical Modulation Plan Builder (План модуляции: завязка -> посредствующий аккорд -> K64/D7 -> D7 -> T, гл. 30, 31)
- Secondary Dominants and Tonicization (Побочные доминанты и вводные септаккорды, гл. 26-28)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Sequence, Union

from .key import Key, Mode
from .pitch import PitchClass, ScaleDegree


@dataclass(frozen=True, slots=True)
class RelatedKeyInfo:
    """
    Metadata for a key related by the first degree of relationship (первая степень родства).

    Attributes:
        key: The related Key object.
        relation_name: Human-readable relation description (e.g. 'Dominant', 'Subdominant', 'Parallel minor').
        degree_in_source: Scale degree index (1..7) in the source key.
        is_subdominant_group: Whether this tonality belongs to the subdominant sphere (субдоминантовая группа/сфера).
        symbol: Classical harmonic degree symbol (e.g. 'V', 'VI', 'IV', 'II', 'III', 'iv', 'v', 'VII').
    """

    key: Key
    relation_name: str
    degree_in_source: int
    is_subdominant_group: bool
    symbol: str = ""

    @property
    def tonic(self) -> PitchClass:
        """Tonic pitch class of the related key."""
        return self.key.tonic

    @property
    def mode(self) -> Mode:
        """Mode of the related key."""
        return self.key.mode

    def __str__(self) -> str:
        tag = "[S-group]" if self.is_subdominant_group else "[D-group/Other]"
        sym = f" ({self.symbol})" if self.symbol else ""
        return f"{self.key.name}{sym}: {self.relation_name} {tag}"


@dataclass(frozen=True, slots=True)
class FirstDegreeRelations:
    """
    Container for the 6 first-degree related keys of a given source key (Бригадный учебник, гл. 29).

    Provides sequence protocol support and queries by relation, symbol, or harmonic group.
    """

    source_key: Key
    relations: tuple[RelatedKeyInfo, ...]

    def __post_init__(self) -> None:
        if len(self.relations) != 6:
            raise ValueError(
                f"FirstDegreeRelations must contain exactly 6 related keys, got {len(self.relations)}."
            )

    def __len__(self) -> int:
        return len(self.relations)

    def __iter__(self):
        return iter(self.relations)

    def __getitem__(self, index: Union[int, str]) -> RelatedKeyInfo:
        if isinstance(index, int):
            return self.relations[index]
        if isinstance(index, str):
            res = self.by_symbol(index) or self.by_relation_name(index)
            if res is not None:
                return res
            raise KeyError(f"No related key found for identifier '{index}'.")
        raise TypeError(f"Index must be int or str, got {type(index)}.")

    @property
    def keys(self) -> tuple[Key, ...]:
        """Tuple of the 6 related Key objects."""
        return tuple(r.key for r in self.relations)

    @property
    def subdominant_group(self) -> tuple[RelatedKeyInfo, ...]:
        """Related keys belonging to the subdominant sphere."""
        return tuple(r for r in self.relations if r.is_subdominant_group)

    @property
    def dominant_group(self) -> tuple[RelatedKeyInfo, ...]:
        """Related keys belonging to the dominant or tonic sphere."""
        return tuple(r for r in self.relations if not r.is_subdominant_group)

    def by_symbol(self, symbol: str) -> Optional[RelatedKeyInfo]:
        """Lookup related key by degree symbol ('V', 'VI', 'IV', 'II', 'III', 'iv', 'v', 'VII')."""
        sym_clean = symbol.strip()
        # 1. Exact case-sensitive match first (crucial to distinguish IV from iv, V from v)
        for r in self.relations:
            if r.symbol == sym_clean:
                return r
        # 2. Case-insensitive fallback
        for r in self.relations:
            if r.symbol.upper() == sym_clean.upper():
                return r
        return None

    def by_relation_name(self, name: str) -> Optional[RelatedKeyInfo]:
        """Lookup related key by relation name case-insensitively."""
        name_clean = name.strip().lower()
        for r in self.relations:
            if name_clean in r.relation_name.lower():
                return r
        return None

    def contains_key(self, target: Union[Key, str]) -> bool:
        """Check if target key is among the first-degree related keys."""
        tgt_key = Key.from_string(target) if isinstance(target, str) else target
        return any(
            r.key.tonic == tgt_key.tonic and r.key.mode == tgt_key.mode
            for r in self.relations
        )


def get_related_keys_first_degree(key: Union[Key, str]) -> FirstDegreeRelations:
    """
    Compute exactly 6 first-degree related keys according to Brigade Chapter 29.

    For a Major key (e.g. C Major):
    1. V  (Dominant): G Major
    2. VI (Submediant / Parallel minor): A MinorHarmonic
    3. IV (Subdominant): F Major
    4. II (Supertonic): D MinorHarmonic
    5. III (Mediant): E MinorHarmonic
    6. iv (Minor subdominant / гармоническая субдоминанта): F MinorHarmonic

    For a Minor key (e.g. A Minor):
    1. III (Parallel major): C Major
    2. iv  (Subdominant): D MinorHarmonic
    3. VI  (Submediant major): F Major
    4. v   (Natural minor dominant): E MinorNatural (or E MinorHarmonic)
    5. VII (Natural subtonic major): G Major
    6. V   (Harmonic major dominant): E Major
    """
    src_key = Key.from_string(key) if isinstance(key, str) else key

    if src_key.mode.is_major:
        # Major key first degree relations
        t = src_key.tonic.value
        # 1. V Dominant (Major)
        k_v = Key(tonic=PitchClass((t + 7) % 12), mode=Mode.MAJOR)
        # 2. VI Parallel minor / Submediant (MinorHarmonic)
        k_vi = Key(tonic=PitchClass((t + 9) % 12), mode=Mode.MINOR_HARMONIC)
        # 3. IV Subdominant (Major)
        k_iv = Key(tonic=PitchClass((t + 5) % 12), mode=Mode.MAJOR)
        # 4. II Supertonic (MinorHarmonic)
        k_ii = Key(tonic=PitchClass((t + 2) % 12), mode=Mode.MINOR_HARMONIC)
        # 5. III Mediant (MinorHarmonic)
        k_iii = Key(tonic=PitchClass((t + 4) % 12), mode=Mode.MINOR_HARMONIC)
        # 6. iv Minor subdominant / гармоническая субдоминанта (MinorHarmonic)
        k_sub_m = Key(tonic=PitchClass((t + 5) % 12), mode=Mode.MINOR_HARMONIC)

        relations = (
            RelatedKeyInfo(
                key=k_v,
                relation_name="Dominant",
                degree_in_source=5,
                is_subdominant_group=False,
                symbol="V",
            ),
            RelatedKeyInfo(
                key=k_vi,
                relation_name="Submediant / Parallel minor",
                degree_in_source=6,
                is_subdominant_group=True,
                symbol="VI",
            ),
            RelatedKeyInfo(
                key=k_iv,
                relation_name="Subdominant",
                degree_in_source=4,
                is_subdominant_group=True,
                symbol="IV",
            ),
            RelatedKeyInfo(
                key=k_ii,
                relation_name="Supertonic",
                degree_in_source=2,
                is_subdominant_group=True,
                symbol="II",
            ),
            RelatedKeyInfo(
                key=k_iii,
                relation_name="Mediant",
                degree_in_source=3,
                is_subdominant_group=False,
                symbol="III",
            ),
            RelatedKeyInfo(
                key=k_sub_m,
                relation_name="Minor subdominant",
                degree_in_source=4,
                is_subdominant_group=True,
                symbol="iv",
            ),
        )
    else:
        # Minor key first degree relations
        t = src_key.tonic.value
        # 1. III Parallel major (Major)
        k_iii = Key(tonic=PitchClass((t + 3) % 12), mode=Mode.MAJOR)
        # 2. iv Subdominant (MinorHarmonic)
        k_iv = Key(tonic=PitchClass((t + 5) % 12), mode=Mode.MINOR_HARMONIC)
        # 3. VI Submediant major (Major)
        k_vi = Key(tonic=PitchClass((t + 8) % 12), mode=Mode.MAJOR)
        # 4. v Natural minor dominant (MinorNatural)
        k_v_nat = Key(tonic=PitchClass((t + 7) % 12), mode=Mode.MINOR_NATURAL)
        # 5. VII Natural subtonic major (Major)
        k_vii_nat = Key(tonic=PitchClass((t + 10) % 12), mode=Mode.MAJOR)
        # 6. V Harmonic major dominant (Major)
        k_v_harm = Key(tonic=PitchClass((t + 7) % 12), mode=Mode.MAJOR)

        relations = (
            RelatedKeyInfo(
                key=k_iii,
                relation_name="Parallel major",
                degree_in_source=3,
                is_subdominant_group=False,
                symbol="III",
            ),
            RelatedKeyInfo(
                key=k_iv,
                relation_name="Subdominant",
                degree_in_source=4,
                is_subdominant_group=True,
                symbol="iv",
            ),
            RelatedKeyInfo(
                key=k_vi,
                relation_name="Submediant major",
                degree_in_source=6,
                is_subdominant_group=True,
                symbol="VI",
            ),
            RelatedKeyInfo(
                key=k_v_nat,
                relation_name="Natural minor dominant",
                degree_in_source=5,
                is_subdominant_group=False,
                symbol="v",
            ),
            RelatedKeyInfo(
                key=k_vii_nat,
                relation_name="Natural subtonic major",
                degree_in_source=7,
                is_subdominant_group=False,
                symbol="VII",
            ),
            RelatedKeyInfo(
                key=k_v_harm,
                relation_name="Harmonic major dominant",
                degree_in_source=5,
                is_subdominant_group=False,
                symbol="V",
            ),
        )

    return FirstDegreeRelations(source_key=src_key, relations=relations)


# -----------------------------------------------------------------------------
# Pivot Chords (Посредствующие аккорды, гл. 30)
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PivotChord:
    """
    Common diatonic/harmonic triad between two keys serving as pivot (посредствующий аккорд).

    Attributes:
        source_function: Function name in the source key (e.g. 'VI', 'T', 'S', 'II', 'III').
        target_function: Function name in the target key (e.g. 'II', 'IV', 'VI', 'T', 'D').
        pitch_classes: Exact 3 pitch classes of the triad (root, third, fifth).
        weight: Preference score (higher is better). Ch. 30 prioritizes subdominant functions in target.
        description: Harmonic explanation according to Brigade rules.
    """

    source_function: str
    target_function: str
    pitch_classes: tuple[PitchClass, PitchClass, PitchClass]
    weight: float
    description: str = ""

    @property
    def root(self) -> PitchClass:
        """Root pitch class of the triad."""
        return self.pitch_classes[0]

    @property
    def third(self) -> PitchClass:
        """Third pitch class of the triad."""
        return self.pitch_classes[1]

    @property
    def fifth(self) -> PitchClass:
        """Fifth pitch class of the triad."""
        return self.pitch_classes[2]

    @property
    def pitch_classes_set(self) -> frozenset[PitchClass]:
        """Frozenset of pitch classes for set comparisons."""
        return frozenset(self.pitch_classes)

    @property
    def is_subdominant_in_target(self) -> bool:
        """True if chord functions in the subdominant group (II, IV, VI, S) in target key."""
        clean = self.target_function.upper()
        return clean in ("II", "IV", "VI", "S", "II6", "S6")

    def __str__(self) -> str:
        pcs = "/".join(p.sharp_name for p in self.pitch_classes)
        return (
            f"PivotChord({self.source_function} -> {self.target_function}, "
            f"[{pcs}], weight={self.weight:.1f})"
        )


def _get_key_triads(key: Key) -> list[tuple[str, tuple[PitchClass, PitchClass, PitchClass]]]:
    """
    Generate all primary and secondary triads (both diatonic and harmonic) in a key.

    Returns a list of (function_symbol, (root, third, fifth)).
    """
    t = key.tonic.value
    triads: list[tuple[str, tuple[PitchClass, PitchClass, PitchClass]]] = []

    def make_triad(r: int, third_offset: int, fifth_offset: int) -> tuple[PitchClass, PitchClass, PitchClass]:
        return (
            PitchClass(r % 12),
            PitchClass((r + third_offset) % 12),
            PitchClass((r + fifth_offset) % 12),
        )

    if key.mode.is_major:
        # Natural major scale degrees
        deg1 = t
        deg2 = (t + 2) % 12
        deg3 = (t + 4) % 12
        deg4 = (t + 5) % 12
        deg5 = (t + 7) % 12
        deg6 = (t + 9) % 12
        deg7 = (t + 11) % 12

        triads.append(("T", make_triad(deg1, 4, 7)))      # I: major (C-E-G)
        triads.append(("II", make_triad(deg2, 3, 7)))     # II: minor (D-F-A)
        triads.append(("III", make_triad(deg3, 3, 7)))    # III: minor (E-G-B)
        triads.append(("IV", make_triad(deg4, 4, 7)))     # IV (S): major (F-A-C)
        triads.append(("V", make_triad(deg5, 4, 7)))      # V (D): major (G-B-D)
        triads.append(("VI", make_triad(deg6, 3, 7)))     # VI: minor (A-C-E)
        triads.append(("VII", make_triad(deg7, 3, 6)))    # VII: dim (B-D-F)

        # Harmonic major (гармонический мажор: bVI = t+8)
        b6 = (t + 8) % 12
        triads.append(("iv", make_triad(deg4, 3, 7)))     # Minor subdominant (F-Ab-C)
        triads.append(("bVI", make_triad(b6, 4, 7)))     # Major triad on bVI (Ab-C-Eb)
    else:
        # Minor key (harmonic and natural minor)
        deg1 = t
        deg2 = (t + 2) % 12
        deg3 = (t + 3) % 12
        deg4 = (t + 5) % 12
        deg5 = (t + 7) % 12
        deg6 = (t + 8) % 12
        deg7_nat = (t + 10) % 12
        deg7_harm = (t + 11) % 12

        triads.append(("t", make_triad(deg1, 3, 7)))          # i: minor (A-C-E)
        triads.append(("II", make_triad(deg2, 3, 6)))         # ii°: dim (B-D-F)
        triads.append(("III", make_triad(deg3, 4, 7)))        # III: major (C-E-G)
        triads.append(("iv", make_triad(deg4, 3, 7)))         # iv (s): minor (D-F-A)
        triads.append(("v", make_triad(deg5, 3, 7)))          # v (natural minor D): minor (E-G-B)
        triads.append(("V", make_triad(deg5, 4, 7)))          # V (harmonic major D): major (E-G#-B)
        triads.append(("VI", make_triad(deg6, 4, 7)))         # VI: major (F-A-C)
        triads.append(("VII", make_triad(deg7_nat, 4, 7)))    # VII (natural subtonic): major (G-B-D)
        triads.append(("vii°", make_triad(deg7_harm, 3, 6)))  # vii° (harmonic leading tone): dim (G#-B-D)

    return triads


def _calculate_pivot_weight(source_fn: str, target_fn: str, is_consonant: bool) -> float:
    """
    Score pivot chord according to Brigade Chapter 30 criteria:
    Best pivot chords are subdominant group in target key (II, IV, VI, II6),
    leading naturally into K64 or D7.
    """
    target_clean = target_fn.upper()
    source_clean = source_fn.upper()

    # 1. Target function score (dominant factor)
    if target_clean in ("II", "II6"):
        score = 100.0  # II is the strongest subdominant bridge to K64/D7
    elif target_clean in ("IV", "S", "IV6"):
        score = 90.0   # S is standard subdominant
    elif target_clean in ("VI", "VI6"):
        score = 80.0   # VI has strong subdominant color
    elif target_clean in ("T", "I"):
        score = 40.0   # Tonic pivot is sluggish ("вяло", Ch. 30)
    elif target_clean in ("III",):
        score = 30.0   # Weak mediant relationship
    elif target_clean in ("V", "D"):
        score = 15.0   # Dominant pivot cannot take K64 (D -> K64 forbidden)
    elif target_clean in ("VII", "VII°"):
        score = 10.0   # Diminished unstable triad
    else:
        score = 50.0

    # 2. Source function modifiers
    if source_clean in ("T", "I"):
        score += 10.0  # Natural departure directly from tonic
    elif source_clean in ("VI",):
        score += 10.0  # Deceptive or submediant branch
    elif source_clean in ("IV", "S"):
        score += 8.0
    elif source_clean in ("II",):
        score += 6.0
    elif source_clean in ("III",):
        score += 4.0
    elif source_clean in ("V", "D"):
        score -= 5.0
    elif source_clean in ("VII", "VII°"):
        score -= 15.0

    # 3. Consonance bonus
    if is_consonant:
        score += 5.0

    return score


def find_pivot_chords(
    source_key: Union[Key, str],
    target_key: Union[Key, str],
) -> list[PivotChord]:
    """
    Find all common triads between source and target keys, ranked by Brigade Chapter 30 preference.

    Returns:
        List of PivotChord objects sorted descending by weight (preferred pivot chords first).
    """
    src = Key.from_string(source_key) if isinstance(source_key, str) else source_key
    tgt = Key.from_string(target_key) if isinstance(target_key, str) else target_key

    src_triads = _get_key_triads(src)
    tgt_triads = _get_key_triads(tgt)

    pivots: list[PivotChord] = []
    seen: set[tuple[str, str, tuple[PitchClass, ...]]] = set()

    for s_fn, s_pcs in src_triads:
        s_set = frozenset(s_pcs)
        for t_fn, t_pcs in tgt_triads:
            t_set = frozenset(t_pcs)
            if s_set == t_set:
                # Same pitch class content!
                key_tuple = (s_fn, t_fn, s_pcs)
                if key_tuple in seen:
                    continue
                seen.add(key_tuple)

                # Check if major or minor triad (consonant) vs diminished
                # In 12-TET, root to fifth is 7 semitones for major/minor
                root_val = s_pcs[0].value
                fifth_val = s_pcs[2].value
                is_consonant = ((fifth_val - root_val) % 12) == 7

                weight = _calculate_pivot_weight(s_fn, t_fn, is_consonant)

                desc = (
                    f"Common triad [{s_pcs[0].sharp_name}-{s_pcs[1].sharp_name}-{s_pcs[2].sharp_name}]: "
                    f"{src.name} {s_fn} == {tgt.name} {t_fn}"
                )

                pivots.append(
                    PivotChord(
                        source_function=s_fn,
                        target_function=t_fn,
                        pitch_classes=s_pcs,
                        weight=weight,
                        description=desc,
                    )
                )

    # Sort descending by weight
    pivots.sort(key=lambda p: p.weight, reverse=True)
    return pivots


# -----------------------------------------------------------------------------
# Modulation Plan Builder (План модуляции, гл. 30, 31)
# -----------------------------------------------------------------------------


def build_modulation_plan(
    source_key: Union[Key, str],
    target_key: Union[Key, str],
    pivot_chord: Optional[PivotChord] = None,
    include_full_cadence: bool = False,
) -> list[tuple[Key, str]]:
    """
    Constructs a canonical Brigade modulation sequence:
    Source cadence/progression -> Pivot chord -> Target K64 (or target D7) -> Target D7 -> Target T.

    Args:
        source_key: Initial tonality.
        target_key: Destination tonality.
        pivot_chord: Explicit pivot chord to use; if None, optimal pivot chord is selected automatically.
        include_full_cadence: If True, uses full initial cadence (T-S-D-T); if False, starts directly with T.

    Returns:
        List of (Key, chord_symbol) tuples representing the progression.
    """
    src = Key.from_string(source_key) if isinstance(source_key, str) else source_key
    tgt = Key.from_string(target_key) if isinstance(target_key, str) else target_key

    if pivot_chord is None:
        candidates = find_pivot_chords(src, tgt)
        if not candidates:
            raise ValueError(
                f"No diatonic pivot chords found between {src.name} and {tgt.name}."
            )
        pivot_chord = candidates[0]

    plan: list[tuple[Key, str]] = []

    # 1. Source key exposure / cadence
    if include_full_cadence:
        plan.extend([
            (src, "T"),
            (src, "S" if src.mode.is_major else "s"),
            (src, "D"),
            (src, "T"),
        ])
    else:
        plan.append((src, "T"))

    # 2. Pivot chord
    # If the pivot chord in source key is already T and we just played T, avoid redundant T-T
    if pivot_chord.source_function.upper() not in ("T", "I") or include_full_cadence:
        if pivot_chord.source_function.upper() not in ("T", "I"):
            plan.append((src, pivot_chord.source_function))

    # Re-interpreted in target key
    plan.append((tgt, pivot_chord.target_function))

    # 3. Target modulating cadence
    # Brigade Ch. 30:
    # If pivot chord is dominant group in target key (V, D), K64 cannot follow (D -> K64 forbidden).
    # Otherwise (II, IV, VI, T, III), standard K64 is introduced on strong beat!
    target_fn_upper = pivot_chord.target_function.upper()
    if target_fn_upper in ("D", "V", "v"):
        # Straight into D7 -> T
        plan.append((tgt, "D7"))
        plan.append((tgt, "T"))
    else:
        plan.append((tgt, "K64"))
        plan.append((tgt, "D7"))
        plan.append((tgt, "T"))

    return plan


# -----------------------------------------------------------------------------
# Secondary Dominants and Tonicization (Побочные доминанты, гл. 26-28)
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SecondaryDominant:
    """
    Secondary dominant (побочная доминанта / DD) in classical functional harmony.

    Represents dominant triads, dominant seventh chords, and leading-tone seventh chords
    resolving to secondary diatonic scale degrees (Дубовский et al., гл. 26-28).

    Attributes:
        name: Common analytical symbol (e.g. 'DD', 'DD7', 'D7/II', 'D7/VI', 'VII7/V').
        key: Home tonality in which the secondary dominant operates.
        target_degree: Scale degree index in key being tonicized (e.g. 5, 2, 6, 4, 3).
        root: Root PitchClass of the secondary dominant.
        third: Third PitchClass (major third from root = leading tone to target tonic).
        fifth: Fifth PitchClass (perfect fifth from root).
        seventh: Seventh PitchClass if seventh chord, else None.
        is_seventh: Whether this chord contains a seventh factor.
        is_diminished_seventh: Whether this is a diminished leading-tone seventh chord (VII7/X).
    """

    name: str
    key: Key
    target_degree: int
    root: PitchClass
    third: PitchClass
    fifth: PitchClass
    seventh: Optional[PitchClass] = None
    is_seventh: bool = False
    is_diminished_seventh: bool = False

    def __post_init__(self) -> None:
        if self.seventh is not None and not self.is_seventh:
            object.__setattr__(self, "is_seventh", True)

    @property
    def pitch_classes(self) -> tuple[PitchClass, ...]:
        """Ordered tuple of pitch classes (root, third, fifth [, seventh])."""
        if self.is_seventh and self.seventh is not None:
            return (self.root, self.third, self.fifth, self.seventh)
        return (self.root, self.third, self.fifth)

    @property
    def pitch_classes_set(self) -> frozenset[PitchClass]:
        """Frozenset of pitch classes for set operations."""
        return frozenset(self.pitch_classes)

    @property
    def factors(self) -> dict[str, PitchClass]:
        """Mapping from factor names to PitchClasses."""
        res = {
            "root": self.root,
            "third": self.third,
            "fifth": self.fifth,
        }
        if self.is_seventh and self.seventh is not None:
            res["seventh"] = self.seventh
        return res

    @property
    def target_tonic(self) -> PitchClass:
        """The pitch class of the resolution target's tonic."""
        if self.key.mode.is_major:
            return self.key.pitch_class_for_degree(self.target_degree)
        # Minor key target degree
        if self.target_degree == 7:
            # Natural subtonic VII in minor
            return PitchClass((self.key.tonic.value + 10) % 12)
        return self.key.pitch_class_for_degree(self.target_degree)

    @classmethod
    def create(cls, key: Union[Key, str], symbol: str) -> SecondaryDominant:
        """
        Create a SecondaryDominant instance from a symbolic name in key.

        Supported notations:
        - 'DD': Double dominant triad (D to V degree)
        - 'DD7': Double dominant seventh chord (D7 to V degree)
        - 'VII7/V', 'DDVII7': Diminished leading-tone seventh to V degree
        - 'D/II', 'D7/II', 'D7/2': Secondary dominant to II degree
        - 'D/III', 'D7/III', 'D7/3': Secondary dominant to III degree
        - 'D/IV', 'D7/IV', 'D7/4': Secondary dominant to IV degree
        - 'D/V', 'D7/V': Synonym for DD / DD7
        - 'D/VI', 'D7/VI', 'D7/6': Secondary dominant to VI degree
        - 'D/VII', 'D7/VII', 'D7/7': Secondary dominant to VII natural degree (in minor)
        - 'VII7/II', 'VII7/IV', 'VII7/VI': Secondary leading-tone diminished 7th chords
        """
        k = Key.from_string(key) if isinstance(key, str) else key
        raw = symbol.strip()

        # 1. Double dominant special aliases
        if raw.upper() in ("DD", "D/V"):
            return cls.for_degree(k, target_degree=5, is_seventh=False, name="DD")
        if raw.upper() in ("DD7", "D7/V"):
            return cls.for_degree(k, target_degree=5, is_seventh=True, name="DD7")
        if raw.upper() in ("DDVII7", "VII7/V", "VII7_V"):
            return cls.for_degree(
                k, target_degree=5, is_seventh=True, is_leading_tone=True, name="VII7/V"
            )

        # 2. Match patterns like 'D7/II', 'D/IV', 'VII7/VI'
        m = re.match(r"^(D7|D|VII7)[/_]([0-9]+|[IViv]+)$", raw, re.IGNORECASE)
        if not m:
            raise ValueError(
                f"Unknown secondary dominant symbol '{symbol}'. Expected e.g. DD, DD7, D7/II, VII7/V."
            )

        chord_type, deg_str = m.groups()
        chord_type_upper = chord_type.upper()

        degree_map = {
            "1": 1, "I": 1,
            "2": 2, "II": 2,
            "3": 3, "III": 3,
            "4": 4, "IV": 4,
            "5": 5, "V": 5,
            "6": 6, "VI": 6,
            "7": 7, "VII": 7,
        }
        deg_clean = deg_str.upper()
        if deg_clean not in degree_map:
            raise ValueError(f"Invalid target degree in '{symbol}': '{deg_str}'.")

        target_degree = degree_map[deg_clean]
        is_seventh = "7" in chord_type_upper
        is_leading_tone = "VII" in chord_type_upper

        return cls.for_degree(
            k,
            target_degree=target_degree,
            is_seventh=is_seventh,
            is_leading_tone=is_leading_tone,
            name=raw,
        )

    @classmethod
    def for_degree(
        cls,
        key: Key,
        target_degree: int,
        is_seventh: bool = True,
        is_leading_tone: bool = False,
        name: Optional[str] = None,
    ) -> SecondaryDominant:
        """
        Build a secondary dominant or leading-tone chord tonicizing target_degree in key.
        """
        if not (1 <= target_degree <= 7):
            raise ValueError(f"Target degree must be 1..7, got {target_degree}.")

        # Find pitch class of target tonic
        if key.mode.is_major:
            if target_degree == 7:
                raise ValueError(
                    "Secondary dominant cannot tonicize VII degree in major (diminished triad)."
                )
            target_pc = key.pitch_class_for_degree(target_degree)
        else:
            if target_degree == 2:
                raise ValueError(
                    "Secondary dominant cannot tonicize II degree in minor (diminished triad)."
                )
            if target_degree == 7:
                # In minor, secondary dominant targets natural VII degree (subtonic)
                target_pc = PitchClass((key.tonic.value + 10) % 12)
            else:
                target_pc = key.pitch_class_for_degree(target_degree)

        t_val = target_pc.value

        if is_leading_tone:
            # Diminished seventh chord built on the leading tone to target (1 semitone below target)
            root = PitchClass((t_val + 11) % 12)
            third = PitchClass((root.value + 3) % 12)
            fifth = PitchClass((root.value + 6) % 12)
            seventh = PitchClass((root.value + 9) % 12) if is_seventh else None
            chord_name = name or (f"VII7/{target_degree}" if is_seventh else f"VII/{target_degree}")
            return cls(
                name=chord_name,
                key=key,
                target_degree=target_degree,
                root=root,
                third=third,
                fifth=fifth,
                seventh=seventh,
                is_seventh=is_seventh,
                is_diminished_seventh=True,
            )

        # Standard secondary dominant (major triad or dominant 7th, root is P5 above target)
        root = PitchClass((t_val + 7) % 12)
        third = PitchClass((root.value + 4) % 12)  # Leading tone to target!
        fifth = PitchClass((root.value + 7) % 12)
        seventh = PitchClass((root.value + 10) % 12) if is_seventh else None

        default_name = f"D7/{target_degree}" if is_seventh else f"D/{target_degree}"
        if target_degree == 5:
            default_name = "DD7" if is_seventh else "DD"

        chord_name = name or default_name

        return cls(
            name=chord_name,
            key=key,
            target_degree=target_degree,
            root=root,
            third=third,
            fifth=fifth,
            seventh=seventh,
            is_seventh=is_seventh,
            is_diminished_seventh=False,
        )

    def __str__(self) -> str:
        pcs = "/".join(p.sharp_name for p in self.pitch_classes)
        return f"SecondaryDominant({self.name} in {self.key.name}: [{pcs}])"


def get_secondary_dominants(key: Union[Key, str]) -> list[SecondaryDominant]:
    """
    Enumerate all canonical secondary dominants and leading-tone seventh chords in key.
    """
    k = Key.from_string(key) if isinstance(key, str) else key
    dominants: list[SecondaryDominant] = []

    if k.mode.is_major:
        # Eligible degrees in major: II, III, IV, V, VI
        degrees = [2, 3, 4, 5, 6]
    else:
        # Eligible degrees in minor: III, IV, V, VI, VII
        degrees = [3, 4, 5, 6, 7]

    for deg in degrees:
        # Dominant triad
        dominants.append(SecondaryDominant.for_degree(k, target_degree=deg, is_seventh=False))
        # Dominant seventh
        dominants.append(SecondaryDominant.for_degree(k, target_degree=deg, is_seventh=True))
        # Leading-tone seventh (VII7/deg)
        dominants.append(
            SecondaryDominant.for_degree(k, target_degree=deg, is_seventh=True, is_leading_tone=True)
        )

    return dominants
