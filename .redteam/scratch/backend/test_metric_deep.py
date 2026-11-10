import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import TimeSignature, calculate_metric_structure

# 1. Test is_downbeat for different meters
for ts_str in ["4/4", "3/4", "2/4", "6/8", "3/8"]:
    ts = TimeSignature.parse(ts_str)
    print(f"\n--- Meter: {ts_str} (measure_duration_quarters={ts.measure_duration_quarters}) ---")
    step = 0.5 if "8" in ts_str else 0.5
    offsets = [i * step for i in range(int(ts.measure_duration_quarters / step))]
    for off in offsets:
        print(f"  Offset {off:.2f}q: is_downbeat = {ts.is_downbeat(off)}")

# 2. Test 3/4 with quarter notes: downbeat on beat 1 (offset 0), beat 2 (offset 1), beat 3 (offset 2)
# Does 3/4 mark beat 2 or 3 as downbeat?
ts34 = TimeSignature.parse("3/4")
print("\n3/4 downbeats:", [ts34.is_downbeat(0.0), ts34.is_downbeat(1.0), ts34.is_downbeat(2.0)])

# 3. Test 6/8 with 6 eighth notes:
# In 6/8, beat 1 (off 0) and beat 4 (off 1.5) are downbeats.
ts68 = TimeSignature.parse("6/8")
print("6/8 eighth offsets downbeats:", [(i*0.5, ts68.is_downbeat(i*0.5)) for i in range(6)])

# 4. Test 3/8 with 3 eighth notes:
ts38 = TimeSignature.parse("3/8")
print("3/8 eighth offsets downbeats:", [(i*0.5, ts38.is_downbeat(i*0.5)) for i in range(3)])

# 5. Test calculate_metric_structure with measure overflow (unaligned durations)
notes_overflow = [
    {"pitch": 60, "duration": "dotted_half"}, # 3.0q
    {"pitch": 62, "duration": "half"},        # 2.0q in 4/4 meter (total 5.0q in measure 1)
    {"pitch": 64, "duration": "quarter"},
]
info_overflow = calculate_metric_structure(notes_overflow, default_time_signature="4/4")
print("\nOverflow test in 4/4:")
for item in info_overflow:
    print(f"  Pitch {item['pitch']}, meas={item['measure']}, offset={item['offset_in_measure']}, dur={item['duration_quarters']}")
