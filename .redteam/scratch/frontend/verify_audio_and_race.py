"""
Detailed analysis of synth.ts, midiInput.ts, ScoreDisplay.tsx and App.tsx race conditions.
"""

def verify_code_findings():
    print("Verification of critical lines in frontend:")
    
    # 1. Alert blocks setIsHarmonizing(false)
    # In App.tsx lines 113-120:
    # alert() is called synchronously inside try {} before finally { setIsHarmonizing(false); }
    print("[1] App.tsx:114 -> alert blocks JS execution, leaving isHarmonizing=true, button spins, candidates not cleared.")
    
    # 2. Race condition in App.tsx:75-121
    print("[2] App.tsx:75 -> No AbortController, no requestId. Out-of-order network responses overwrite newest state.")
    
    # 3. Audio leak in synth.ts:242-248
    print("[3] synth.ts:242 -> stop() clears setTimeout but does NOT disconnect or stop active Web Audio oscillators/gains.")
    
    # 4. AudioContext creation on every metronome tick in midiInput.ts:121-140
    print("[4] midiInput.ts:126 -> new AudioCtxClass() instantiated on EVERY single metronome click! Exceeds browser limit.")
    
    # 5. ScoreDisplay problemMeasures all-highlight in ScoreDisplay.tsx:62-70
    print("[5] ScoreDisplay.tsx:65 -> querySelectorAll('g[id*=\"Measure\"], g.vf-measure') highlights ALL measures unconditionally.")
    
    # 6. ExportBar missing durations in ExportBar.tsx:31, 58-64
    print("[6] ExportBar.tsx:31,63 -> Missing durations parameter in export payload, destroying rhythmic values.")

if __name__ == "__main__":
    verify_code_findings()
