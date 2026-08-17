# Observable Strategy Selector V1

Protocol: `aegisswarm-observable-strategy-selector-v1`

## Motivation

The five frozen 60-token strategies exhibit material scenario specialization under Simulator V2. On development seeds `17000–17399`, the non-deployable best-of-5 oracle reached `0.938` survival while the strongest individual frozen program reached about `0.831`.

The selector experiment asks whether any useful fraction of that gap is predictable from information actually observable before the first action.

## Frozen policy set

Use the five incumbent programs loaded from:

```text
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44001.json
...
rule_objective_seed_44005.json
```

No rule tokens, executor semantics, simulator interaction model or scoring weights are changed.

## Observation boundary

The selector acts after the first `SimulatorV2.sense()` call and before the first assignment at `t=0`.

Allowed:

- active **detected** threat counts and detected types;
- detected-track speed, target-distance and time-to-target summaries;
- defender reachability to detected real threats;
- known defender remaining uses/capacity/range;
- known sensor quality/range;
- known asset value.

Forbidden:

- any undetected threat state;
- scenario seed;
- future motion;
- future detection state;
- realized interaction randomness;
- penetration/damage outcomes;
- oracle choices.

`tests/test_strategy_selector.py` contains a leakage regression: changing an undetected threat's position, velocity, type and target must not change the feature vector.

## Model

V1 is deliberately simple:

```text
features -> standardization -> five ridge reward regressors
ridge alpha = 1.0, fixed and untuned
```

For every selector-training scenario, all five frozen programs are evaluated under Simulator V2. Their established scalar episode rewards become the five regression targets.

At evaluation time:

```text
first observable snapshot
    -> predict reward for each frozen program
    -> choose argmax
    -> commit to that frozen program for the episode
```

No switching occurs in V1.

## Baseline and oracle

Primary baseline:

> the single frozen program with the highest mean established scalar reward on selector-training scenarios.

This is stronger and fairer than comparing the selector to the mean of the five programs.

Development-only oracle:

> best frozen program in hindsight for each evaluation scenario.

The oracle is non-deployable and is reported only to quantify remaining selection headroom.

## Fresh evidence blocks

```text
27000–27399   selector training
28000–28399   selector development
29000–29399   reserved selector confirmation
```

Do not inspect `29000–29399` during development.

## Quick protocol

```text
training scenarios:    27000–27099   (100)
evaluation scenarios:  28000–28019   (20)
programs:               5 frozen programs
model:                  ridge reward selector, alpha=1.0
```

Run:

```bash
git checkout agent/strategy-selector
git pull origin agent/strategy-selector
pytest -q
python -m aegisswarm.strategy_selector_cli --workers 14
```

Do not run `--full` until quick output is inspected.

## Quick output

The CLI reports:

```text
fixed best program index
fresh five-program survival rates
fixed best survival
selector survival
oracle survival
selector - fixed survival + paired scenario bootstrap CI
selector - fixed established reward + CI
fraction of oracle survival gap captured
selector choice counts
oracle choice counts
selector/oracle choice agreement
```

## Decision gate

### Promising

If selector-minus-fixed is meaningfully positive and not driven by one pathological choice pattern, run full training `27000–27399` and full development `28000–28399`.

### Tied

If the selector ties the best fixed program, do not immediately tune many classifier families. First test whether oracle specialization becomes predictable only after later observations or whether it is predominantly stochastic-outcome hindsight.

### Worse

Close static t=0 selection. Later-state adaptive switching or broader stress/regime evaluation becomes more justified than further static selector tuning.

## Claim boundary

A positive V1 development result would support only:

> observable context can improve selection among this fixed set of five synthetic-simulator strategies relative to a globally fixed frozen strategy.

It would not establish real-world effectiveness, general strategy-selection superiority, or oracle attainability.
