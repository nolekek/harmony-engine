# -*- coding: utf-8 -*-
"""Track WebAudio oscillators so stop() actually silences playback."""
import re
from pathlib import Path

path = Path(r"D:\aitraining\frontend\src\audio\synth.ts")
text = path.read_text(encoding="utf-8")

# 1. Add the registry field next to other private fields.
if "activeOscillators" not in text:
    text = text.replace(
        "  private playbackTimer: number | null = null;",
        "  private playbackTimer: number | null = null;\n"
        "  private activeOscillators: Set<OscillatorNode> = new Set();",
        1,
    )

# 2. Register every created oscillator right after creation.
pattern = re.compile(r"(const (\w+) = this\.ctx!?\.createOscillator\(\);)")
text = pattern.sub(lambda m: f"{m.group(1)}\n      this.activeOscillators.add({m.group(2)});", text)

# 3. stop() must kill sounding oscillators, not just the timer.
old_stop = """  public stop() {
    this.isPlaying = false;
    if (this.playbackTimer !== null) {
      clearTimeout(this.playbackTimer);
      this.playbackTimer = null;
    }
  }"""
new_stop = """  public stop() {
    this.isPlaying = false;
    if (this.playbackTimer !== null) {
      clearTimeout(this.playbackTimer);
      this.playbackTimer = null;
    }
    // Silence already-scheduled oscillators: clearing the timer alone leaves
    // the current chord ringing until its scheduled stop time.
    if (this.ctx) {
      const now = this.ctx.currentTime;
      this.activeOscillators.forEach((osc) => {
        try {
          osc.stop(now + 0.02);
        } catch {
          // already stopped
        }
      });
    }
    this.activeOscillators.clear();
  }"""
if old_stop not in text:
    raise SystemExit("stop() block not found — aborting patch")
text = text.replace(old_stop, new_stop, 1)

path.write_text(text, encoding="utf-8")
print("patched synth.ts")
