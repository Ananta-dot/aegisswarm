# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** SELECTOR V1 FAILED; ORACLE DECOMPOSITION QUICK SHOWS NO STABLE SELECTION HEADROOM  
**Active branch:** `agent/oracle-decomposition`  
**Active protocol:** `aegisswarm-oracle-decomposition-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `ORACLE_DECOMPOSITION.md` for the active diagnostic, `STRATEGY_SELECTOR.md` for the closed selector experiment, `EVIDENCE_HARDENING.md` for Simulator V2 headroom evidence, and the reliability/stochastic/planning docs for prior closed experiments.

## Incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested proposer, compact representation, planner, reliability executor, repeated-tape training protocol, or t=0 observable selector has robustly replaced this incumbent.

## Completed selector V1 — FAILED

Full selector training used `27000–27399`; development evaluation used fresh `28000–28399`:

```text
fixed best program index:         1
fresh program survivals:          [0.7400, 0.8275, 0.81375, 0.81875, 0.8300]
fixed best survival:              0.8275
selector survival:                0.8113
oracle survival:                  0.9338
selector - fixed:                -0.0163 CI=[-0.0350,+0.0025]
selector - fixed reward:         -2.960 CI=[-5.3340,-0.6094]
oracle gap captured:             -0.153
selector/oracle agreement:        0.310
```

Decision:

- the t=0 observable ridge selector underperformed the training-selected fixed strategy;
- the scalar-reward CI is entirely negative;
- do **not** inspect `29000–29399` confirmation;
- do not tune ridge alpha/features/model complexity on this development block by default.

## Oracle decomposition quick — STRONG EVIDENCE AGAINST STABLE EPISODE-LEVEL SPECIALIZATION

Quick diagnostic used fresh structural worlds `30000–30019`, four independently keyed stochastic tapes per world, and the same five frozen incumbent programs.

```text
program mean survivals:          [0.7438, 0.8375, 0.8125, 0.7750, 0.8125]
single-tape fixed survival:      0.925
single-tape oracle survival:     0.975
single-tape oracle - fixed:     +0.0500 CI=[0.0000,+0.1250]
expected fixed survival:         0.8375
expected oracle survival:        0.9000
expected oracle - fixed:        +0.0625 CI=[+0.01875,+0.10625]
cross-tape fixed survival:       0.8375
cross-tape oracle survival:      0.8063
cross-tape oracle - fixed:      -0.0312 CI=[-0.0875,+0.03125]
cross-tape choice agreement:     0.450
tape-oracle modal fraction:      0.575
stable fraction of raw gap:     -0.625
```

Interpretation:

- same-tape hindsight remains optimistic;
- averaging several tapes and choosing/scoring on those same tapes still produces an optimistic `+6.25 pp` gap;
- the primary held-out-tape estimate is instead negative (`-3.12 pp`) and its CI spans zero;
- only `45%` of per-world best-program choices agree between tape halves;
- the typical tape-specific oracle choice is only modestly stable (`57.5%` modal fraction);
- this quick evidence strongly suggests that much of the earlier `~93–94%` best-of-five oracle is realization-specific stochastic luck rather than stable structural specialization that an episode-level selector could learn.

The negative stable-fraction statistic should not be interpreted literally as “negative headroom”; it means the held-out estimate reversed sign relative to the optimistic same-realization gap.

## Why the full decomposition is still authorized

Unlike a failed policy quick screen, this is an evidence diagnostic whose purpose is to decide whether strategy-selection headroom exists at all. Twenty worlds are too few to permanently close a research direction based on a held-out CI of `[-8.75,+3.125] pp`.

Therefore the exact protocol is frozen and the full **development diagnostic** is authorized:

```text
400 structural worlds: 30000–30399
8 independent indexed tapes/world
5 frozen programs
```

Run:

```bash
python -m aegisswarm.oracle_decomposition_cli --full --workers 14
```

Do not inspect the independent replication block `31000–31399`.

## Full-development decision gate

### Cross-tape gap remains near zero or negative

Close episode-level frozen-program selection as a performance path. Stop using raw `93–94%` oracle survival as a realistic target. The incumbent remains a single robust fixed rule program/executor, and the next performance work should target **online state adaptation / uncertainty-aware sequential control or broader benchmark regimes**, not another static selector.

### Cross-tape gap becomes materially positive and choices stabilize

There is genuine structural specialization hidden by the quick sample. Only then is a richer observable or later-state gating architecture justified.

### Same-tape/expected oracle remains large but cross-tape stays weak

Treat the gap as stochastic hindsight. Do not tune selector model families against it.

## Evidence ledger

Consumed/inspected blocks include:

- `2000–2099`: structured development-test
- `2100–2499`: V1 formal holdout
- `3000–3399`: Axplorer V2 development
- `4000–4399`: hybrid-executor development
- `5000–5399`: hybrid-objective development
- `9000–9399`: optimizer-native V1 development
- `11000–11399`: optimizer-native V2 development
- `13000–13399`: rolling-horizon V1 development
- `15000–15399`: rolling-horizon V2 development
- `17000–17399`: evidence-hardening/headroom development
- `19000–19399`: reliability-aware executor development
- `21000–21003`, `22000–22019`: stochastic-robust V1 quick
- `24000–24003`, `25000–25019`: stochastic-training V2 quick
- `27000–27399`, `28000–28399`: observable selector V1 full development
- `30000–30019`: oracle-decomposition quick structural worlds

Reserved blocks tied to abandoned/unfrozen protocols must not be repurposed, including `18000–18399`, `20000–20399`, `23000–23399`, `26000–26399`, and `29000–29399`. `31000–31399` is reserved independent oracle-decomposition replication and remains untouched.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- perfect-sensing headroom was essentially zero on `17000–17399`;
- deterministic valid interactions showed large diagnostic headroom (`+19.8 pp`);
- reliability weighting did not help, backup was only weakly positive, rolling horizon did not help, and repeated-tape training failed its clean quick gate;
- the t=0 observable ridge selector underperformed the training-selected fixed strategy on full development;
- the raw best-of-five oracle is a hindsight diagnostic and the quick cross-tape decomposition provides no evidence yet that its gap is stable across stochastic outcomes.

Not supported:

- raw oracle performance as deployable or predictably attainable;
- richer selector superiority;
- stable structural specialization before the full oracle-decomposition diagnostic;
- deterministic interaction success as attainable;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
