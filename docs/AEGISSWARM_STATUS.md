# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** SELECTOR V1 FAILED; ORACLE-DECOMPOSITION DIAGNOSTIC ACTIVE  
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

## Why the raw oracle must be decomposed

The raw best-of-5 oracle remains high (`0.9338`), but this does not necessarily mean ~10 pp of strategy headroom is predictable from scenario context.

`SimulatorV2` uses stateless indexed randomness. Interaction outcomes are keyed by event identity including `(timestep, defender_id, threat_id)`. Different frozen programs choose different assignments and therefore expose themselves to different stochastic interaction events/draws.

A same-realization hindsight oracle can consequently benefit from both:

1. genuine structural strategy specialization; and
2. stochastic luck specific to the action path chosen by each program.

The failed observable selector makes this distinction essential before any more selector complexity is introduced.

## Active diagnostic — oracle decomposition V1

Question:

> How much of the raw best-of-5 oracle gap persists when program choice must generalize across independent indexed stochastic tapes of the same structural scenario?

No policy is trained or modified.

Fresh blocks:

- `30000–30399`: oracle-decomposition development structural worlds
- `31000–31399`: reserved independent replication — do not inspect during development

Quick:

```text
20 structural worlds: 30000–30019
4 independent indexed tapes/world
5 frozen incumbent programs
```

Full development, only after quick inspection:

```text
400 structural worlds: 30000–30399
8 independent indexed tapes/world
```

### Reported oracle variants

1. **Single-tape hindsight oracle** — choose and score the best program on tape 0. Optimistic by construction.
2. **Expected-outcome oracle** — choose by mean reward over all tapes and score on those same tapes. Noise-reduced but still optimistic.
3. **Cross-tape oracle — primary diagnostic** — choose per-world best program on one tape half, score only on the held-out half, then reverse the halves and average.
4. **Cross-tape fixed comparator** — select one global fixed program on one half and score on the held-out half, symmetrically.

Primary statistic:

```text
cross-tape oracle survival - cross-tape fixed survival
```

Additional stability diagnostics:

- first-half vs second-half best-program agreement;
- modal fraction of tape-specific oracle choices within each structural world;
- fraction of the raw single-tape oracle gap retained cross-tape.

See `ORACLE_DECOMPOSITION.md` for exact semantics and interpretation boundaries.

## Immediate runbook

```bash
git fetch origin
git checkout agent/oracle-decomposition
git pull origin agent/oracle-decomposition
pytest -q
python -m aegisswarm.oracle_decomposition_cli --workers 14
```

Do **not** use `--full` until the quick result is inspected.

## Decision gate

### Cross-tape gap remains large and choices are stable

There is genuine structural policy specialization. A richer observable or later-state gating architecture becomes justified.

### Cross-tape gap collapses while raw oracle remains large

Most of the earlier oracle gap is stochastic hindsight. Stop using ~93–94% raw oracle survival as a realistic selector target and move toward robust/adaptive sequential control or broader benchmark evidence.

### Cross-tape oracle is worse than fixed

Per-scenario strategy identity is unstable across stochastic outcomes. Episode-level preselection is the wrong abstraction.

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

Reserved blocks tied to abandoned/unfrozen protocols must not be repurposed, including `18000–18399`, `20000–20399`, `23000–23399`, `26000–26399`, and `29000–29399`.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- perfect-sensing headroom was essentially zero on `17000–17399`;
- deterministic valid interactions showed large diagnostic headroom (`+19.8 pp`);
- reliability weighting did not help, backup was only weakly positive, rolling horizon did not help, and repeated-tape training failed its clean quick gate;
- the t=0 observable ridge selector underperformed the training-selected fixed strategy on full development;
- the raw best-of-5 oracle is a hindsight diagnostic whose predictable/stable component has not yet been established.

Not supported:

- raw oracle performance as deployable or predictably attainable;
- richer selector superiority before oracle decomposition;
- deterministic interaction success as attainable;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
