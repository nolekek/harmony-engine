import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import json
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, parse_key
from src.harmony.rules.doubling import get_triad_tones

# 40+ melodies across C-dur, G-dur, F-dur, a-moll, d-moll, e-moll; 4/4 and 3/4; 4-10 notes
MELODIES = [
    # C major (4/4)
    {"name": "C-dur scale asc 8", "key": "C Major", "ts": "4/4", "notes": [60, 62, 64, 65, 67, 69, 71, 72]},
    {"name": "C-dur scale desc 8", "key": "C Major", "ts": "4/4", "notes": [72, 71, 69, 67, 65, 64, 62, 60]},
    {"name": "C-dur arpeggio 1", "key": "C Major", "ts": "4/4", "notes": [60, 64, 67, 72, 67, 64, 62, 60]},
    {"name": "C-dur motif 5 notes", "key": "C Major", "ts": "4/4", "notes": [64, 65, 67, 62, 60]},
    {"name": "C-dur chorale opening", "key": "C Major", "ts": "4/4", "notes": [67, 67, 69, 67, 65, 64, 62, 60]},
    {"name": "C-dur 4 notes short", "key": "C Major", "ts": "4/4", "notes": [64, 65, 62, 60]},
    {"name": "C-dur start on 5th", "key": "C Major", "ts": "4/4", "notes": [67, 65, 64, 65, 67, 62, 60]},
    {"name": "C-dur arch 7 notes", "key": "C Major", "ts": "4/4", "notes": [60, 62, 64, 67, 65, 62, 60]},
    {"name": "C-dur 9 notes motif", "key": "C Major", "ts": "4/4", "notes": [60, 62, 64, 65, 64, 62, 64, 62, 60]},
    {"name": "C-dur 10 notes phrase", "key": "C Major", "ts": "4/4", "notes": [67, 65, 64, 62, 60, 62, 64, 65, 62, 60]},

    # C major (3/4)
    {"name": "C-dur 3/4 motif 6", "key": "C Major", "ts": "3/4", "notes": [64, 67, 65, 64, 62, 60]},
    {"name": "C-dur 3/4 waltz-like 6", "key": "C Major", "ts": "3/4", "notes": [60, 64, 67, 69, 71, 72]},
    {"name": "C-dur 3/4 descending 6", "key": "C Major", "ts": "3/4", "notes": [67, 65, 64, 62, 64, 60]},

    # G major (4/4)
    {"name": "G-dur scale asc 8", "key": "G Major", "ts": "4/4", "notes": [67, 69, 71, 72, 74, 76, 78, 79]},
    {"name": "G-dur scale desc 8", "key": "G Major", "ts": "4/4", "notes": [79, 78, 76, 74, 72, 71, 69, 67]},
    {"name": "G-dur arpeggio 6", "key": "G Major", "ts": "4/4", "notes": [67, 71, 74, 71, 69, 67]},
    {"name": "G-dur motif 5 notes", "key": "G Major", "ts": "4/4", "notes": [71, 72, 74, 69, 67]},
    {"name": "G-dur hymn 7 notes", "key": "G Major", "ts": "4/4", "notes": [67, 69, 71, 72, 71, 69, 67]},
    {"name": "G-dur 4 notes short", "key": "G Major", "ts": "4/4", "notes": [71, 72, 69, 67]},

    # G major (3/4)
    {"name": "G-dur 3/4 melody 6", "key": "G Major", "ts": "3/4", "notes": [67, 71, 74, 72, 69, 67]},
    {"name": "G-dur 3/4 motif 9", "key": "G Major", "ts": "3/4", "notes": [74, 72, 71, 69, 71, 72, 71, 69, 67]},

    # F major (4/4)
    {"name": "F-dur scale asc 8", "key": "F Major", "ts": "4/4", "notes": [65, 67, 69, 70, 72, 74, 76, 77]},
    {"name": "F-dur scale desc 8", "key": "F Major", "ts": "4/4", "notes": [77, 76, 74, 72, 70, 69, 67, 65]},
    {"name": "F-dur arpeggio 6", "key": "F Major", "ts": "4/4", "notes": [65, 69, 72, 69, 67, 65]},
    {"name": "F-dur motif 5 notes", "key": "F Major", "ts": "4/4", "notes": [69, 70, 72, 67, 65]},
    {"name": "F-dur 4 notes short", "key": "F Major", "ts": "4/4", "notes": [69, 70, 67, 65]},
    {"name": "F-dur 7 notes arch", "key": "F Major", "ts": "4/4", "notes": [65, 69, 72, 74, 72, 67, 65]},

    # F major (3/4)
    {"name": "F-dur 3/4 motif 6", "key": "F Major", "ts": "3/4", "notes": [65, 69, 72, 70, 67, 65]},
    {"name": "F-dur 3/4 motif 9", "key": "F Major", "ts": "3/4", "notes": [72, 70, 69, 67, 69, 70, 69, 67, 65]},

    # A minor (4/4)
    {"name": "a-moll scale asc 8", "key": "A Minor", "ts": "4/4", "notes": [69, 71, 72, 74, 76, 77, 80, 81]},
    {"name": "a-moll scale desc 8", "key": "A Minor", "ts": "4/4", "notes": [81, 79, 77, 76, 74, 72, 71, 69]},
    {"name": "a-moll arpeggio 6", "key": "A Minor", "ts": "4/4", "notes": [69, 72, 76, 72, 71, 69]},
    {"name": "a-moll motif 5 notes", "key": "A Minor", "ts": "4/4", "notes": [72, 74, 76, 71, 69]},
    {"name": "a-moll 4 notes short", "key": "A Minor", "ts": "4/4", "notes": [72, 74, 71, 69]},
    {"name": "a-moll 7 notes phrase", "key": "A Minor", "ts": "4/4", "notes": [69, 72, 74, 76, 74, 71, 69]},

    # A minor (3/4)
    {"name": "a-moll 3/4 motif 6", "key": "A Minor", "ts": "3/4", "notes": [69, 72, 76, 74, 71, 69]},
    {"name": "a-moll 3/4 motif 9", "key": "A Minor", "ts": "3/4", "notes": [76, 74, 72, 71, 72, 74, 72, 71, 69]},

    # D minor (4/4)
    {"name": "d-moll scale asc 8", "key": "D Minor", "ts": "4/4", "notes": [62, 64, 65, 67, 69, 70, 73, 74]},
    {"name": "d-moll scale desc 8", "key": "D Minor", "ts": "4/4", "notes": [74, 72, 70, 69, 67, 65, 64, 62]},
    {"name": "d-moll arpeggio 6", "key": "D Minor", "ts": "4/4", "notes": [62, 65, 69, 65, 64, 62]},
    {"name": "d-moll motif 5 notes", "key": "D Minor", "ts": "4/4", "notes": [65, 67, 69, 64, 62]},
    {"name": "d-moll 4 notes short", "key": "D Minor", "ts": "4/4", "notes": [65, 67, 64, 62]},

    # D minor (3/4)
    {"name": "d-moll 3/4 motif 6", "key": "D Minor", "ts": "3/4", "notes": [62, 65, 69, 67, 64, 62]},

    # E minor (4/4)
    {"name": "e-moll scale asc 8", "key": "E Minor", "ts": "4/4", "notes": [64, 66, 67, 69, 71, 72, 75, 76]},
    {"name": "e-moll scale desc 8", "key": "E Minor", "ts": "4/4", "notes": [76, 74, 72, 71, 69, 67, 66, 64]},
    {"name": "e-moll arpeggio 6", "key": "E Minor", "ts": "4/4", "notes": [64, 67, 71, 67, 66, 64]},
    {"name": "e-moll motif 5 notes", "key": "E Minor", "ts": "4/4", "notes": [67, 69, 71, 66, 64]},
    {"name": "e-moll 4 notes short", "key": "E Minor", "ts": "4/4", "notes": [67, 69, 66, 64]},

    # E minor (3/4)
    {"name": "e-moll 3/4 motif 6", "key": "E Minor", "ts": "3/4", "notes": [64, 67, 71, 69, 66, 64]},
]

DOMINANT_GROUP_ALL = {
    "D", "d", "D6", "d6", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2",
    "K64", "k64", "VII", "VII6", "VII7", "vii", "vii6", "vii7"
}
DOMINANT_STANDARD = {
    "K64", "k64", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2", "D6", "d6", "D", "d"
}

def analyze_melody(m_info, harmonizer):
    name = m_info["name"]
    k_str = m_info["key"]
    ts = m_info["ts"]
    notes = m_info["notes"]
    key = Key.parse(k_str)
    tonic_pc, mode = parse_key(key)
    is_minor = "MINOR" in str(mode).upper()
    tonic_tones = {tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12}
    dom_tones = {(tonic_pc + 7) % 12, (tonic_pc + 11) % 12, (tonic_pc + 2) % 12, (tonic_pc + 5) % 12}

    res = harmonizer.harmonize(melody=notes, key=k_str, time_signature=ts)
    if not res.is_success or not res.best_solution:
        return {
            "name": name,
            "key": k_str,
            "ts": ts,
            "notes": notes,
            "success": False,
            "chords": [],
            "defects": ["HARMONIZATION_FAILED: " + res.message]
        }

    chords = [c.function for c in res.best_solution.chords]
    defects = []
    n = len(notes)

    # 1. Final chord check
    final_note_pc = notes[-1] % 12
    final_chord = chords[-1]
    if final_note_pc in tonic_tones:
        # Must be T or t in root position
        if final_chord not in ("T", "t"):
            defects.append(f"ФИНАЛ: не T в основном виде ({final_chord}) при тонической ноте сопрано")
    else:
        # Half or deceptive cadence
        if final_chord in ("T6", "t6", "D6", "d6"):
            defects.append(f"ФИНАЛ: запрещенное обращение ({final_chord}) в финале каденции")
        elif final_chord not in ("D", "d", "D7", "d7", "VI", "vi"):
            defects.append(f"ФИНАЛ: ненормативный финал ({final_chord}) при нетонической ноте")

    # 2. Penultimate chord check
    if n >= 2:
        penult_chord = chords[-2]
        penult_note_pc = notes[-2] % 12
        if final_chord in ("T", "t", "T6", "t6"):
            # If penult note fits dominant, is it dominant group?
            if penult_note_pc in dom_tones:
                if penult_chord not in DOMINANT_STANDARD:
                    defects.append(f"ПРЕДПОСЛЕДНИЙ: не доминанта ({penult_chord}) перед T при возможности автентики")
            # Also check if K64 is immediately before T (K64 cannot go directly to T without D)
            if penult_chord in ("K64", "k64"):
                defects.append("ПРЕДПОСЛЕДНИЙ: K64 перед T без разрешения в D")

    # 3. Starting chord check
    start_note_pc = notes[0] % 12
    start_chord = chords[0]
    if start_note_pc in tonic_tones:
        if start_chord not in ("T", "t", "T6", "t6"):
            defects.append(f"СТАРТ: старт на {start_chord} при наличии тонических ступеней у сопрано")

    # 4. Chains of III6/VI and consecutive identical chords
    for i in range(n - 1):
        c1 = chords[i]
        c2 = chords[i + 1]
        if (c1 in ("III6", "iii6") and c2 in ("VI", "vi")) or (c1 in ("VI", "vi") and c2 in ("III6", "iii6")):
            defects.append(f"ЦЕПОЧКА III6/VI: позиция {i}->{i+1} ({c1} -> {c2})")
        if c1 in ("III6", "iii6") and c2 in ("III6", "iii6"):
            defects.append(f"ДВА III6 ПОДРЯД: позиция {i}->{i+1}")
        if c1 == c2 and notes[i] != notes[i + 1]:
            defects.append(f"ПОВТОР БЕЗ СМЕНЫ: {c1} -> {c2} на разных нотах сопрано (шаг {i}->{i+1})")

    # 5. K64 metric & resolution check
    metric_info = res.best_solution.metric_info
    for i, chord in enumerate(chords):
        if chord in ("K64", "k64"):
            is_db = metric_info[i]["is_downbeat"] if i < len(metric_info) else False
            if not is_db:
                defects.append(f"K64 НА СЛАБОЙ ДОЛЕ: шаг {i}")
            if i + 1 < len(chords):
                next_c = chords[i + 1]
                if next_c not in ("D", "d", "D7", "d7"):
                    defects.append(f"K64 РАЗРЕШЕНИЕ НЕ В D: шаг {i}->{i+1} ({chord} -> {next_c})")

    return {
        "name": name,
        "key": k_str,
        "ts": ts,
        "notes": notes,
        "success": True,
        "chords": chords,
        "defects": defects
    }

def main():
    harmonizer = Harmonizer()
    results = []
    print(f"Запуск аудита для {len(MELODIES)} мелодий...")
    for idx, m in enumerate(MELODIES, 1):
        res = analyze_melody(m, harmonizer)
        results.append(res)
        status = "OK" if not res["defects"] else f"ДЕФЕКТЫ ({len(res['defects'])})"
        print(f"[{idx:02d}/{len(MELODIES)}] {m['name']}: {status}")

    out_dir = Path(".redteam/scratch/debug_musicality")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "REPORT.md"

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    clean = sum(1 for r in results if not r["defects"])
    defect_count = sum(len(r["defects"]) for r in results)

    lines = [
        "# Отчет аудита музыкального канона (40+ мелодий)",
        "",
        f"- **Всего мелодий:** {total}",
        f"- **Успешно сгармонизовано:** {successful}/{total}",
        f"- **Без дефектов:** {clean}/{total}",
        f"- **Всего обнаружено нарушений:** {defect_count}",
        "",
        "## Таблица: мелодия → аккорды → дефекты",
        "",
        "| # | Мелодия | Тональность | Размер | Аккорды | Дефекты |",
        "|---|---|---|---|---|---|",
    ]

    for idx, r in enumerate(results, 1):
        chords_str = " -> ".join(r["chords"]) if r["chords"] else "—"
        def_str = "<br>".join(r["defects"]) if r["defects"] else "Нет (чисто)"
        lines.append(f"| {idx} | {r['name']} | {r['key']} | {r['ts']} | {chords_str} | {def_str} |")

    lines.append("")
    lines.append("## Сводка нарушений по категориям")
    category_counts = {}
    for r in results:
        for d in r["defects"]:
            cat = d.split(":")[0]
            category_counts[cat] = category_counts.get(cat, 0) + 1

    for cat, cnt in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- **{cat}**: {cnt}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Отчет записан в {report_path}")

if __name__ == "__main__":
    main()
