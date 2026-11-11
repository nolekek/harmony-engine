import sys
import io
import mido

sys.path.insert(0, r"D:\aitraining")

from backend.importers import (
    parse_musicxml_content,
    parse_midi_file,
    parse_text_melody,
    midi_to_note_name,
)

def test_text_melody_fuzz():
    print("=== Testing parse_text_melody ===")
    
    # Valid cases
    res1 = parse_text_melody("C4 E4 G4")
    print(f"C4 E4 G4 -> len {len(res1)}, pitches: {[r['pitch'] for r in res1]}")
    
    res2 = parse_text_melody("1 3 5 1")
    print(f"1 3 5 1 -> len {len(res2)}, pitches: {[r['pitch'] for r in res2]}")
    
    res3 = parse_text_melody("60, 64, 67")
    print(f"60, 64, 67 -> len {len(res3)}, pitches: {[r['pitch'] for r in res3]}")
    
    res4 = parse_text_melody("[3/4] C4:dotted_half D4:quarter E4:half")
    print(f"[3/4] C4:dotted_half -> len {len(res4)}, durs: {[r['duration'] for r in res4]}, ts: {res4[0]['time_signature']}")
    
    # Erroneous inputs
    test_cases = [
        "",
        "   ",
        "invalid notes only",
        "C4 invalid D4",
        "0", # degree 0
        "9", # degree 9
        "10", # neither degree nor midi (>=36)
        "999", # midi > 127
        "C-2", # negative octave
        "C##4", # double sharp
        "Cbb4", # double flat
        "C4:unknown_dur", # unknown duration
        "[0/0] C4", # divide by zero meter?
        "[-3/4] C4",
        "[abc/def] C4",
        "C4:0",
        "C4:-5",
    ]
    
    for tc in test_cases:
        try:
            r = parse_text_melody(tc)
            print(f"Input {tc!r} -> {len(r)} notes: {[x.get('pitch') for x in r]}")
        except Exception as e:
            print(f"Input {tc!r} -> EXCEPTION: {type(e).__name__}: {e}")

def test_midi_importer_fuzz():
    print("\n=== Testing parse_midi_file ===")
    # 1. Empty bytes
    try:
        r = parse_midi_file(b"")
        print("Empty bytes ->", r)
    except Exception as e:
        print(f"Empty bytes -> EXCEPTION: {type(e).__name__}: {e}")
        
    # 2. Corrupted bytes
    try:
        r = parse_midi_file(b"MThd\x00\x00\x00\x06\x00\x01\x00\x01\x01\xe0garbage")
        print("Corrupted bytes ->", r)
    except Exception as e:
        print(f"Corrupted bytes -> EXCEPTION: {type(e).__name__}: {e}")
        
    # 3. MIDI with different tempos
    for bpm in [40, 120, 240]:
        mid = mido.MidiFile(type=1, ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
        track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
        # Note on C4 (60) for 1 beat (480 ticks = quarter note)
        track.append(mido.Message("note_on", note=60, velocity=80, time=0))
        track.append(mido.Message("note_off", note=60, velocity=0, time=480))
        buf = io.BytesIO()
        mid.save(file=buf)
        res = parse_midi_file(buf.getvalue())
        print(f"BPM={bpm}: parsed {len(res['soprano_melody'])} notes, duration={res['durations']}")

def test_musicxml_importer_fuzz():
    print("\n=== Testing parse_musicxml_content ===")
    # 1. Empty string
    try:
        r = parse_musicxml_content("")
        print("Empty string ->", r)
    except Exception as e:
        print(f"Empty string -> EXCEPTION: {type(e).__name__}: {e}")
        
    # 2. Invalid XML
    try:
        r = parse_musicxml_content("<not valid xml")
        print("Invalid xml ->", r)
    except Exception as e:
        print(f"Invalid xml -> EXCEPTION: {type(e).__name__}: {e}")
        
    # 3. Minimal empty score
    try:
        r = parse_musicxml_content("<score-partwise><part-list><score-part id='P1'/></part-list><part id='P1'></part></score-partwise>")
        print("Empty score -> melody len:", len(r["soprano_melody"]), "voicings len:", len(r["satb_voicings"]))
    except Exception as e:
        print(f"Empty score -> EXCEPTION: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_text_melody_fuzz()
    test_midi_importer_fuzz()
    test_musicxml_importer_fuzz()
