import sys
sys.path.insert(0, r"D:\aitraining")
from backend.key_detector import CANONICAL_KEYS, detect_key_from_melody
from src.harmony.core.types import Key

# 1. Test default melody: E4 F4 G4 E4 D4 C4
default_melody = [64, 65, 67, 64, 62, 60]
det = detect_key_from_melody(default_melody)
print(f"Default melody detected as: {det['tonic']} {det['mode']} ({det['name']})")

# 2. Test accuracy on 24 keys: construct a simple tonic-triad/scale melody for each canonical key
# E.g. degree 1 -> 3 -> 5 -> 3 -> 2 -> 1
success_count = 0
failures = []

for k in CANONICAL_KEYS:
    k_obj = Key(tonic=k["tonic"], mode=k["mode"])
    scale = k_obj.scale_pcs
    tonic_pc = k_obj.tonic_pc
    is_min = "minor" in k["mode"].lower()
    
    # Simple melody: I -> III -> V -> IV -> II -> I
    deg1 = 60 + tonic_pc
    deg3 = deg1 + (3 if is_min else 4)
    deg5 = deg1 + 7
    deg4 = deg1 + 5
    deg2 = deg1 + 2
    # In harmonic minor, add raised 7th (VII#):
    if is_min:
        test_melody = [deg1, deg3, deg5, deg4, deg1 + 11, deg1]
    else:
        test_melody = [deg1, deg3, deg5, deg4, deg2, deg1]
        
    detected = detect_key_from_melody(test_melody)
    if detected["tonic"] == k["tonic"] and detected["mode"] == k["mode"]:
        success_count += 1
    else:
        failures.append((k["name"], f"{detected['tonic']} {detected['mode']} ({detected['name']})"))

print(f"24 Keys Accuracy: {success_count}/24")
if failures:
    print("Failures:")
    for expected, got in failures:
        print(f"  Expected {expected} -> Got {got}")

# 3. What if melody doesn't end on degree 1? Half cadence ending on degree 5 (dominant)?
half_cadence_c = [60, 62, 64, 65, 67] # C D E F G
det_half = detect_key_from_melody(half_cadence_c)
print(f"Half-cadence in C (C D E F G) detected as: {det_half['tonic']} {det_half['mode']}")

# 4. What about enharmonics? E.g., C# Major vs Db Major?
print(f"Is C# Major in CANONICAL_KEYS? {any(k['tonic'] == 'C#' and k['mode'] == 'Major' for k in CANONICAL_KEYS)}")
print(f"Is Db Major in CANONICAL_KEYS? {any(k['tonic'] == 'Db' and k['mode'] == 'Major' for k in CANONICAL_KEYS)}")
print(f"Is D# Minor in CANONICAL_KEYS? {any(k['tonic'] == 'D#' for k in CANONICAL_KEYS)}")
print(f"Is Eb Minor in CANONICAL_KEYS? {any(k['tonic'] == 'Eb' and 'minor' in k['mode'].lower() for k in CANONICAL_KEYS)}")
