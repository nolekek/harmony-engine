# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.rules.doubling import get_triad_tones

key = Key("C", "Major")
grammar = HarmonicGrammar(key=key)

pitch = 68 # Ab4
print("get_triad_tones('D6', 0, 'MAJOR'):", get_triad_tones("D6", 0, "MAJOR"))
cands = grammar.get_compatible_functions(pitch, key=key, is_final=True)
print("Compatible functions for pitch 68 (is_final=True):", cands)
cands_nonfinal = grammar.get_compatible_functions(pitch, key=key, is_final=False)
print("Compatible functions for pitch 68 (is_final=False):", cands_nonfinal)
