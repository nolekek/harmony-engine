"""
Regression test for audit M3: src/harmony/pipeline.py must NOT monkey-patch
engine.validate_voice_leading at import time (the runtime compat guard was
removed — the native function already accepts prev_chord/curr_chord).
Pattern follows test_no_monkey_patch_in_doubling (P1 wave).
"""

import inspect

from src.harmony import pipeline as pipeline_mod
from src.harmony.rules import engine as engine_mod
from src.harmony.rules import voice_leading as voice_leading_mod


def test_no_monkey_patch_guard_in_pipeline():
    assert not hasattr(pipeline_mod, "_orig_vvl"), (
        "pipeline.py must not keep the runtime compat guard (_orig_vvl)"
    )
    assert not hasattr(pipeline_mod, "_compat_validate_voice_leading"), (
        "pipeline.py must not define the _compat_validate_voice_leading wrapper"
    )


def test_validate_voice_leading_is_native():
    assert voice_leading_mod.validate_voice_leading.__module__ == "src.harmony.rules.voice_leading", (
        "voice_leading.validate_voice_leading must be native, not a patched wrapper"
    )
    assert engine_mod.validate_voice_leading is voice_leading_mod.validate_voice_leading, (
        "engine must reference the native function object, not a pipeline-injected wrapper"
    )


def test_native_signature_accepts_chord_context():
    params = inspect.signature(voice_leading_mod.validate_voice_leading).parameters
    assert "prev_chord" in params, "guard removal precondition: native signature must accept prev_chord"
    assert "curr_chord" in params
