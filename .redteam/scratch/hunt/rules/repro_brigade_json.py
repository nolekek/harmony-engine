"""
Reproduction script for docs/brigade_rules.json verification (Item 9):
1. Verifies that JSON catalog is dead weight: RuleEngine loads it, but get_rule_description
   and get_rule_severity are NEVER invoked by the validation pipeline or rule functions.
2. Incomplete catalog: only 22 rules in JSON, while code defines over 35 distinct rule IDs.
3. Musical defect in rule 154:
   "D43 обязан разрешаться в T6, так как септима в басу обязана сделать шаг вниз..."
   Musically absurd: the seventh is in an upper voice, the BASS of D43 is the fifth (scale degree II).
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.engine import RuleEngine

def run_tests():
    root = Path(__file__).resolve().parents[4]
    json_path = root / "docs" / "brigade_rules.json"

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    rules_in_json = data.get("rules", [])
    json_rule_ids = {r["id"] for r in rules_in_json}

    print(f"Total rules defined in brigade_rules.json: {len(json_rule_ids)}")

    re = RuleEngine()
    print(f"RuleEngine loaded rules_registry count: {len(re.rules_registry)}")

    # Check rule 154 (RESOLUTION_D43_TO_T6)
    d43_rule = re.rules_registry.get("RESOLUTION_D43_TO_T6", {})
    desc = d43_rule.get("description", "")
    print(f"\nRule RESOLUTION_D43_TO_T6 JSON description:\n  '{desc}'")
    if "септима в басу" in desc:
        print("  DEFECT CONFIRMED: Description falsely states that the seventh is in the bass for D43!")

    # Check missing rules in JSON catalog that exist in code:
    code_rules = [
        "CHORD_THIRD_MISSING", "CHORD_FIFTH_MISSING", "CHORD_ROOT_MISSING", "CHORD_SEVENTH_MISSING",
        "CADENCE_K64_INITIAL", "SYNTAX_NO_D_TO_K64", "SYNTAX_K64_MUST_RESOLVE_TO_D",
        "FALSE_RELATION_PERECHENIE", "SEVENTH_CHORD_INVERSION_INCOMPLETE",
        "SEVENTH_CHORD_DISTRIBUTION", "DOUBLING_VII6_LEADING_TONE",
        "DOUBLING_SECONDARY_DOMINANT", "RESOLUTION_VII7_SEVENTH_DOWN",
        "RESOLUTION_VII7_FIFTH_DOWN", "RESOLUTION_VII7_DOUBLED_THIRD",
        "RESOLUTION_SECONDARY_DOMINANT", "MELODIC_TWO_LEAPS_SAME_DIRECTION",
        "NCT_SUSPENSION_UNRESOLVED", "NCT_PASSING_ON_DOWNBEAT", "NCT_ILLEGAL_LEAP_NON_CHORD_TONE",
    ]
    missing_in_json = [r for r in code_rules if r not in json_rule_ids]
    print(f"\nRules implemented in Python code but MISSING from brigade_rules.json ({len(missing_in_json)} rules):")
    for m in missing_in_json:
        print(f"  - {m}")

if __name__ == "__main__":
    run_tests()
