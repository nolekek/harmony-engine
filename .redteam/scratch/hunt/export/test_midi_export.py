import sys
import io
import mido

sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing
from backend.exporters import generate_midi_bytes
from src.harmony.export.midi import export_to_midi

def inspect_midi(midi_bytes, label=""):
    print(f"\n=== Inspecting MIDI: {label} ===")
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))
    print(f"MIDI Type: {mid.type}")
    print(f"Ticks per beat: {mid.ticks_per_beat}")
    print(f"Number of tracks: {len(mid.tracks)}")
    
    assert mid.type == 1, f"Expected Type 1, got {mid.type}"
    assert len(mid.tracks) == 4, f"Expected 4 tracks, got {len(mid.tracks)}"
    
    track_names = ["Soprano", "Alto", "Tenor", "Bass"]
    
    for trk_idx, track in enumerate(mid.tracks):
        print(f"\n--- Track {trk_idx} ({track_names[trk_idx]}) ---")
        note_on_count = 0
        note_off_count = 0
        program_change = None
        has_tempo = False
        track_name = None
        current_time = 0
        
        events = []
        for msg in track:
            current_time += msg.time
            events.append((current_time, msg.time, msg))
            if msg.type == "track_name":
                track_name = msg.name
            elif msg.type == "set_tempo":
                has_tempo = True
                print(f"  Set Tempo: {msg.tempo} us/beat ({mido.tempo2bpm(msg.tempo):.1f} bpm)")
            elif msg.type == "program_change":
                program_change = (msg.channel, msg.program)
                print(f"  Program change: ch={msg.channel}, program={msg.program}")
            elif msg.type == "note_on" and msg.velocity > 0:
                note_on_count += 1
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                note_off_count += 1
                
        print(f"  Track name: {track_name}")
        print(f"  Total time ticks: {current_time}")
        print(f"  Note-ons: {note_on_count}, Note-offs: {note_off_count}")
        
        assert track_name == track_names[trk_idx], f"Expected track name {track_names[trk_idx]}, got {track_name}"
        assert program_change == (trk_idx, 52), f"Expected Program Change (ch={trk_idx}, prog=52), got {program_change}"
        assert note_on_count == note_off_count, f"Mismatch: {note_on_count} note-on vs {note_off_count} note-off"
        
        if trk_idx == 0:
            assert has_tempo, "Track 0 must have Set Tempo meta event"
            
    print("MIDI inspection passed for:", label)

if __name__ == "__main__":
    voicings = [
        Voicing(64, 60, 55, 48), # E4, C4, G3, C3
        Voicing(65, 60, 57, 45), # F4, C4, A3, A2
        Voicing(67, 60, 55, 48), # G4, C4, G3, C3
        Voicing(62, 59, 55, 43), # D4, B3, G3, G2
    ]
    
    # Test 1: Default 4/4 with half notes
    midi_bytes_default = generate_midi_bytes(voicings, bpm=80)
    inspect_midi(midi_bytes_default, "Default bpm=80, TS=4/4")
    
    # Test 2: Different durations & time signature
    midi_bytes_complex = generate_midi_bytes(
        voicings,
        bpm=120,
        durations=["quarter", "dotted_half", "half", "whole"],
        time_signature="3/4"
    )
    inspect_midi(midi_bytes_complex, "bpm=120, TS=3/4, variable durs")
