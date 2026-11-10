import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer

res = Harmonizer().harmonize([64, 65, 67, 64, 62, 60], key="C Major")
print(f"Success: {res.is_success}, Message: {res.message}")
