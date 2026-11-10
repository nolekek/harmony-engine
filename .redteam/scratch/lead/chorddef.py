import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.chord import ChordFunction, ChordDefinition, Inversion
from src.harmony.core.types import Key, Voicing, parse_chord_symbol
from src.harmony.rules.doubling import check_doubling
c=ChordDefinition(function=ChordFunction.T, inversion=Inversion.ROOT, key=Key('C','Major'))
v=Voicing(64,64,60,48)
print('symbol:', parse_chord_symbol(c))
print('violations:', check_doubling(v, c, key=Key('C','Major')))
