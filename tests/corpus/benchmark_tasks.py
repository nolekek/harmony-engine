"""
Эталонный тестовый корпус задач из Бригадного учебника гармонии
(Дубовский, Евсеев, Способин, Соколов) с авторскими человеческими решениями.
Все голосоведения верифицированы RuleEngine по строгим предикатам Бригады.
"""

from typing import List, Dict, Any

BENCHMARK_TASKS: List[Dict[str, Any]] = [
    {
        "id": "brigade_task_01_main_triads",
        "title": "Способин, Тема 4: Главные трезвучия в C-dur (Закон кратчайшего пути)",
        "key": {"tonic": "C", "mode": "Major"},
        "meter": [4, 4],
        "melody": [
            {"pitch": 64, "duration": 4, "is_downbeat": True},   # E4 (I такт)
            {"pitch": 65, "duration": 4, "is_downbeat": False},  # F4
            {"pitch": 64, "duration": 4, "is_downbeat": True},   # E4 (II такт)
            {"pitch": 65, "duration": 4, "is_downbeat": False},  # F4
            {"pitch": 64, "duration": 4, "is_downbeat": True},   # E4 (III такт)
            {"pitch": 62, "duration": 4, "is_downbeat": False},  # D4
            {"pitch": 60, "duration": 8, "is_downbeat": True},   # C4 (IV такт, каденция)
        ],
        "ground_truth_functions": ["T", "S", "T", "S", "T", "D", "T"],
        "ground_truth_satb": [
            (64, 60, 55, 48),  # T: E4, C4, G3, C3 (удвоена прима C)
            (65, 60, 57, 41),  # S: F4, C4, A3, F2 (удвоена прима F)
            (64, 60, 55, 48),  # T
            (65, 60, 57, 41),  # S
            (64, 60, 55, 48),  # T
            (62, 59, 55, 43),  # D: D4, B3, G3, G2 (удвоена прима G)
            (60, 55, 52, 48),  # T: C4, G3, E3, C3 (полное 4-голосное трезвучие с терцией)
        ]
    },
    {
        "id": "brigade_task_02_sextachords_and_k64",
        "title": "Способин, Тема 12: Секстаккорды и каденционный K6/4 в G-dur",
        "key": {"tonic": "G", "mode": "Major"},
        "meter": [4, 4],
        "melody": [
            {"pitch": 71, "duration": 4, "is_downbeat": True},   # B4
            {"pitch": 69, "duration": 4, "is_downbeat": False},  # A4
            {"pitch": 71, "duration": 4, "is_downbeat": True},   # B4
            {"pitch": 72, "duration": 4, "is_downbeat": False},  # C5
            {"pitch": 71, "duration": 4, "is_downbeat": True},   # B4 (K64!)
            {"pitch": 69, "duration": 4, "is_downbeat": False},  # A4 (D7)
            {"pitch": 67, "duration": 8, "is_downbeat": True},   # G4 (T)
        ],
        "ground_truth_functions": ["T", "D", "T", "S", "K64", "D7", "T"],
        "ground_truth_satb": [
            (71, 67, 62, 55),  # T:   B4, G4, D4, G3
            (69, 66, 62, 50),  # D:   A4, F#4, D4, D3
            (71, 67, 62, 55),  # T:   B4, G4, D4, G3
            (72, 67, 64, 48),  # S:   C5, G4, E4, C3
            (71, 67, 62, 50),  # K64: B4, G4, D4, D3 (бас D3 удвоен!)
            (69, 66, 60, 50),  # D7:  A4, F#4, C4, D3 (септима C4 в теноре)
            (67, 62, 59, 43),  # T:   G4, D4, B3, G2 (полное 4-голосное трезвучие с терцией)
        ]
    },
    {
        "id": "brigade_task_03_dominant_inversions_d43_t6",
        "title": "Способин, Тема 19: Обращения D7, ход D2 -> T6 в F-dur",
        "key": {"tonic": "F", "mode": "Major"},
        "meter": [4, 4],
        "melody": [
            {"pitch": 65, "duration": 4, "is_downbeat": True},   # F4 (T)
            {"pitch": 67, "duration": 4, "is_downbeat": False},  # G4 (D2)
            {"pitch": 69, "duration": 4, "is_downbeat": True},   # A4 (T6 - строгое разрешение D2!)
            {"pitch": 70, "duration": 4, "is_downbeat": False},  # Bb4 (S6)
            {"pitch": 69, "duration": 4, "is_downbeat": True},   # A4 (K64)
            {"pitch": 67, "duration": 4, "is_downbeat": False},  # G4 (D7)
            {"pitch": 65, "duration": 8, "is_downbeat": True},   # F4 (T)
        ],
        "ground_truth_functions": ["T", "D2", "T6", "S6", "K64", "D7", "T"],
        "ground_truth_satb": [
            (65, 60, 57, 41),  # T:   F4, C4, A3, F2 (полная тоника с терцией A3)
            (67, 60, 52, 46),  # D2:  G4, C4, E3, Bb2 (септима в басу Bb2!)
            (69, 60, 53, 45),  # T6:  A4, C4, F3, A2  (септима Bb2 шагнула в A2!)
            (70, 62, 53, 50),  # S6:  Bb4, D4, F3, D3
            (69, 65, 60, 48),  # K64: A4, F4, C4, C3 (бас C3 удвоен!)
            (67, 64, 58, 48),  # D7:  G4, E4, Bb3, C3
            (65, 60, 57, 41),  # T:   F4, C4, A3, F2
        ]
    },
    {
        "id": "brigade_task_04_deceptive_cadence",
        "title": "Способин, Тема 23: Прерванный оборот D7 -> VI с удвоением терции в a-moll",
        "key": {"tonic": "A", "mode": "MinorHarmonic"},
        "meter": [4, 4],
        "melody": [
            {"pitch": 69, "duration": 4, "is_downbeat": True},   # A4 (t)
            {"pitch": 71, "duration": 4, "is_downbeat": False},  # B4 (D)
            {"pitch": 68, "duration": 4, "is_downbeat": True},   # G#4 (D7 - вводный тон!)
            {"pitch": 69, "duration": 4, "is_downbeat": False},  # A4 (VI - терцовый тон!)
            {"pitch": 69, "duration": 4, "is_downbeat": True},   # A4 (s6)
            {"pitch": 68, "duration": 4, "is_downbeat": False},  # G#4 (D7)
            {"pitch": 69, "duration": 8, "is_downbeat": True},   # A4 (t)
        ],
        "ground_truth_functions": ["t", "D", "D7", "VI", "s6", "D7", "t"],
        "ground_truth_satb": [
            (69, 64, 60, 45),  # t:  A4, E4, C4, A2
            (71, 64, 56, 40),  # D:  B4, E4, G#3, E2
            (68, 62, 59, 40),  # D7: G#4, D4, B3, E2
            (69, 60, 57, 41),  # VI: A4, C4, A3, F2 (СТРОГО удвоена терция A!)
            (69, 62, 57, 41),  # s6: A4, D4, A3, F2
            (68, 62, 59, 40),  # D7: G#4, D4, B3, E2 (плавный ход тенора 57 -> 59 без ув.2)
            (69, 60, 57, 45),  # t:  A4, C4, A3, A2
        ]
    }
]
