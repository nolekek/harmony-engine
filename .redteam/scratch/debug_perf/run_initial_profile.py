import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import time
import cProfile
import pstats
import io
from pathlib import Path
from src.harmony.pipeline import Harmonizer
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver import state_generator
from src.harmony.rules.engine import RuleEngine

melodies = {
    4: [64, 65, 62, 60],
    8: [64, 65, 64, 65, 64, 62, 62, 60],
    16: [64, 65, 64, 65, 64, 62, 62, 60] * 2,
    32: [64, 65, 64, 65, 64, 62, 62, 60] * 4,
    64: [64, 65, 64, 65, 64, 62, 62, 60] * 8,
}

stage_results = {}

for n, mel in melodies.items():
    times = {'generate_plans': 0.0, 'state_generator': 0.0, 'validate': 0.0, 'replanning': 0.0}
    orig_gp = HarmonicGrammar.generate_plans
    def timed_gp(*args, **kwargs):
        t0 = time.perf_counter()
        r = orig_gp(*args, **kwargs)
        times['generate_plans'] += (time.perf_counter() - t0)
        return r
    HarmonicGrammar.generate_plans = timed_gp

    orig_gcv = state_generator.generate_candidate_voicings
    def timed_gcv(*args, **kwargs):
        t0 = time.perf_counter()
        r = orig_gcv(*args, **kwargs)
        times['state_generator'] += (time.perf_counter() - t0)
        return r
    state_generator.generate_candidate_voicings = timed_gcv

    orig_val = RuleEngine.validate
    def timed_val(*args, **kwargs):
        t0 = time.perf_counter()
        r = orig_val(*args, **kwargs)
        times['validate'] += (time.perf_counter() - t0)
        return r
    RuleEngine.validate = timed_val

    orig_rep = Harmonizer._replan
    def timed_rep(*args, **kwargs):
        t0 = time.perf_counter()
        r = orig_rep(*args, **kwargs)
        times['replanning'] += (time.perf_counter() - t0)
        return r
    Harmonizer._replan = timed_rep

    h = Harmonizer()
    t_start = time.perf_counter()
    res = h.harmonize(mel, key='C Major')
    total_t = time.perf_counter() - t_start

    HarmonicGrammar.generate_plans = orig_gp
    state_generator.generate_candidate_voicings = orig_gcv
    RuleEngine.validate = orig_val
    Harmonizer._replan = orig_rep

    stage_results[n] = {
        'total_ms': total_t * 1000,
        'gp_ms': times['generate_plans'] * 1000,
        'sg_ms': times['state_generator'] * 1000,
        'val_ms': times['validate'] * 1000,
        'replan_ms': times['replanning'] * 1000,
        'success': res.is_success,
        'solutions': len(res.solutions) if res.solutions else 0,
    }
    print(f"N={n:2d} | Total: {total_t*1000:7.2f}ms | GP: {times['generate_plans']*1000:7.2f}ms | SG: {times['state_generator']*1000:7.2f}ms | VAL: {times['validate']*1000:7.2f}ms | REPLAN: {times['replanning']*1000:7.2f}ms | Success: {res.is_success}")

# cProfile on 8 and 32 notes
cprof_reports = {}
for n in [8, 32]:
    pr = cProfile.Profile()
    mel = melodies[n]
    h = Harmonizer()
    pr.enable()
    res = h.harmonize(mel, key='C Major')
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(15)
    cprof_reports[n] = s.getvalue()

profile_md = "# Initial Profiling Report (Baseline)\n\n"
profile_md += "## Stage Breakdown\n\n"
profile_md += "| Melody Length | Total (ms) | generate_plans (ms) | state_generator (ms) | validate (ms) | replanning (ms) | Success |\n"
profile_md += "|---|---|---|---|---|---|---|\n"
for n, data in stage_results.items():
    profile_md += f"| {n} notes | {data['total_ms']:.2f} | {data['gp_ms']:.2f} | {data['sg_ms']:.2f} | {data['val_ms']:.2f} | {data['replan_ms']:.2f} | {data['success']} ({data['solutions']} sol) |\n"

profile_md += "\n## cProfile Top-15 (Cumulative Time)\n\n"
for n in [8, 32]:
    profile_md += f"### 8-Note Melody (N={n})\n```\n{cprof_reports[n]}\n```\n\n"

out_path = Path('.redteam/scratch/debug_perf/PROFILE.md')
out_path.write_text(profile_md, encoding='utf-8')
print("Profile written to .redteam/scratch/debug_perf/PROFILE.md")
