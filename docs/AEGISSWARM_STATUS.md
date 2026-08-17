# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** OBSERVABILITY-SAFE STRATEGY SELECTOR ACTIVE; NOT FROZEN FOR EXTERNAL CLAIMS  
**Active branch:** `agent/strategy-selector`  
**Active protocol:** `aegisswarm-observable-strategy-selector-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `STRATEGY_SELECTOR.md` for the active protocol, `EVIDENCE_HARDENING.md` for Simulator V2 headroom evidence, and the stochastic/reliability/planning docs for closed experiments.

## Incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested proposer, compact representation, planner, reliability executor, or repeated-tape training protocol has robustly replaced this incumbent.

## Why strategy selection is now the active hypothesis

Simulator V2 headroom development on fresh `17000–17399` found:

```text
normal incumbent mean:          0.801
perfect sensing:                0.801
deterministic interactions:     0.999
best-of-5 frozen oracle:        0.938
frozen program survivals:       [0.7438, 0.8313, 0.8063, 0.8150, 0.8100]
```

The non-deployable oracle is therefore about `+10.7 pp` above the strongest individual frozen program on that block. This is evidence of scenario-specific strategy specialization, not evidence that a deployable selector already exists.

Other attempted routes did not capture the large headroom:

- reliability weighting: effectively null on `19000–19399`;
- contingent backup: only `+1.55 pp`, CI crossing zero;
- rolling-horizon V2: no useful gain and ~14x slower;
- stochastic-robust V1 quick: negative co-adaptation result;
- clean repeated-tape V2 quick: `-6.25 pp`, both paired runs negative.

Do not run the closed V1/V2 stochastic full campaigns and do not inspect their reserved confirmation blocks.

## Active experiment — observable strategy selector V1

Question:

> Can information available after the first sensing step but before the first assignment predict which of the five existing frozen 60-token strategies should be used for the episode?

### Frozen policy set

The same five incumbent programs from `artifacts/optimizer_native_v2_dev/runs` are used. They are not retrained or modified.

### Selector features

The selector snapshot is taken after `SimulatorV2.sense()` at `t=0` and before any assignment. Allowed features include:

- counts/types of **detected** active threats;
- detected-track speed, distance-to-target and time-to-target summaries;
- reachability counts from known defenders to detected real threats;
- known defender availability, remaining uses, capacity and range summaries;
- known sensor detection/range summaries;
- known asset value summary.

Explicitly forbidden from selector features:

- undetected threat position, type, velocity or target;
- scenario seed;
- future trajectory;
- realized interaction outcomes;
- oracle program choice or future episode metrics.

Regression tests verify that changing an undetected threat's state leaves the selector feature vector unchanged.

### Selector model

V1 uses an intentionally simple fixed model:

```text
one ridge reward regressor per frozen program
alpha = 1.0 (fixed, untuned)
```

Training targets are the established scalar episode reward for each program on selector-training scenarios. At evaluation time, the selector chooses the program with highest predicted reward and commits to it for the episode.

### Fair baseline

The primary baseline is **not the mean of five programs**. It is the best globally fixed frozen program selected by mean established scalar reward on the selector-training block.

Fresh development reports:

- best fixed survival;
- learned selector survival;
- non-deployable best-of-5 oracle survival;
- paired scenario bootstrap CI for selector minus fixed;
- selector minus fixed scalar reward;
- fraction of fresh oracle survival gap captured;
- selector/oracle choice frequencies and agreement (descriptive only).

## Fresh selector blocks

- `27000–27399`: selector training
- `28000–28399`: selector development evaluation
- `29000–29399`: reserved selector confirmation — **do not inspect**

Quick V1 uses:

```text
training:   27000–27099 (100 scenarios)
evaluation: 28000–28019 (20 scenarios)
```

The full 400/400 development run is authorized only if quick evidence is promising.

## Immediate runbook

```bash
git fetch origin
git checkout agent/strategy-selector
git pull origin agent/strategy-selector
pytest -q
python -m aegisswarm.strategy_selector_cli --workers 14
```

Do **not** use `--full` yet.

## Decision gate

### Selector materially beats fixed best

Run the full `27000–27399` training / `28000–28399` development protocol. If the full result remains useful, freeze the selector model/features before any confirmation.

### Selector approximately ties fixed best

The frozen-program oracle gap is largely not predictable from t=0 observable context using this simple static selector. Do not tune many classifier families immediately; first inspect whether oracle specialization is driven by later state or stochastic outcomes.

### Selector worsens

Close static t=0 strategy selection. The next scientifically justified options are later-state switching/contextual control or broader simulator/stress-regime generalization, not more frozen-program selector tuning by default.

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

Reserved blocks tied to abandoned/unfrozen protocols must not be silently repurposed, including `18000–18399`, `20000–20399`, `23000–23399`, and `26000–26399`.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- perfect-sensing headroom was essentially zero on `17000–17399`;
- deterministic valid interactions showed large diagnostic headroom (`+19.8 pp`);
- the five frozen strategies show substantial best-of-set scenario specialization;
- reliability weighting did not help, backup was only weakly positive, rolling horizon did not help, and repeated-tape training failed its clean quick gate.

Not supported:

- strategy-selector superiority before this active experiment runs;
- deterministic interaction success as attainable;
- oracle performance as deployable;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
