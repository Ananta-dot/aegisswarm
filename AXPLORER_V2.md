# Axplorer V2

V1 formal holdout result:

- structured local survival: 0.800
- structured Axplorer V1 survival: 0.814
- difference: +0.0132
- 95% paired CI crossed zero
- paired p-value: 0.160042

V1 therefore established statistical parity, not a learned-search advantage.

## What changes in V2

Only the learned proposer changes. The simulator, rule language, scoring function,
training scenario bundle, structured local-search implementation, and oracle
budget remain fixed.

V2 adds:

1. **Fitness/rank conditioning**: each training program receives a quality level;
   generation is conditioned on the top-quality level.
2. **Score-weighted likelihood training**: higher-fitness programs contribute more
   to the model loss without discarding the archive tail.
3. **Grammar-aware decoding**: enabled, condition, threshold, action, and magnitude
   positions have separate output heads and valid category sets.
4. **Canonical encodings**: modulo/threshold aliases are removed before model
   training and generation.
5. **Diversity archive**: the model trains on global high-fitness programs plus
   specialists for survival, containment, penetration, damage, resource use, and
   response delay.

## Data hygiene

- V1 consumed final holdout: `2100-2499`.
- V2 development/evaluation: `3000-3399`.
- V2 reserved confirmation: `6000-6399`.

Do not use `6000-6399` during development.

## Step 1: integration check

```bash
pytest -q
python -m aegisswarm.v2_cli --quick --workers 4 --device mps
```

Quick mode uses only the V2 development block and a tiny search budget.

## Step 2: full V2 development experiment

```bash
python -m aegisswarm.v2_cli --workers 6 --device mps
```

This runs five paired search seeds. For every seed:

- structured local receives 1,800 unique candidate-program evaluations;
- Axplorer V2 receives 1,800 unique candidate-program evaluations;
- both score candidates on the same 16 training scenarios;
- both are evaluated on the same 400 V2 development scenarios.

Outputs:

```text
artifacts/axplorer_v2_dev/
  protocol.json
  results.json
  REPORT.md
  runs/
```

The primary decision statistic is the paired survival difference and its 95%
confidence interval.

## Gate before confirmation

Do **not** run confirmation simply because the point estimate is positive.
Freeze V2 only if the development result is materially convincing across the
five training runs and the paired interval supports an advantage worth testing.

Once frozen, confirmation is evaluation-only:

```bash
python -m aegisswarm.v2_cli --confirm --workers 6
```

The confirmation command loads the exact five development-trained local and V2
programs. It never trains or modifies them, then evaluates seeds `6000-6399`.

Outputs:

```text
artifacts/axplorer_v2_confirm/
  protocol.json
  results.json
  REPORT.md
```

After confirmation, those seeds are consumed and must not be reused as unseen
proof for a later architecture revision.
