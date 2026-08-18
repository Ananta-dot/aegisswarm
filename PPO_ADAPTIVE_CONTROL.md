# AegisSwarm Hierarchical PPO Adaptive Control

Protocol: `aegisswarm-hierarchical-ppo-v1`

## Motivation

The full oracle-decomposition diagnostic showed that episode-level frozen-program selection is the wrong abstraction:

```text
single-tape oracle - fixed:   +0.1037 CI=[+0.0825,+0.12625]
expected oracle - fixed:      +0.0495 CI=[+0.0421875,+0.056875]
cross-tape oracle - fixed:    -0.0150 CI=[-0.024375,-0.0053125]
cross-tape choice agreement:   0.305
```

The raw oracle benefited strongly from realization-specific stochastic outcomes, while program identity did not generalize across independent tapes of the same structural world.

Earlier evidence-hardening also showed that deterministic valid interactions produced approximately `+19.8 pp` survival headroom while perfect sensing produced essentially none. Static reliability weighting, contingent backup, rolling horizon, repeated-tape training and t=0 strategy selection did not capture that headroom robustly.

The next justified question is therefore:

> Can an online learned controller improve outcomes by adapting to realized interaction failures, resource state and overload during the episode while preserving the incumbent constrained assignment layer?

## Architecture

PPO does **not** directly assign defenders to threats.

```text
observable / realized state
        -> PPO tactical mode
        -> frozen 60-token strategic program + tactical adjustment
        -> constrained one-step assignment
        -> Simulator V2 outcome
        -> next observable state
```

The frozen base program is program index `1` from `artifacts/optimizer_native_v2_dev`. It was already selected as the fixed comparator in the earlier selector protocol; V1 does not search over base programs.

## Action space

One discrete action is chosen every simulator step from six abstract tactical modes:

0. `incumbent` — unchanged `RuleGuidedHungarianPolicy`;
1. `urgency` — stronger urgency / fast-threat emphasis;
2. `conserve` — preserve last uses except for sufficiently urgent cases;
3. `reliability` — existing probability-weighted Hungarian ablation;
4. `backup` — existing contingent-backup assignment ablation;
5. `failure_recovery` — one-to-one Hungarian with reliability/urgency adjustment that reacts to recent realized failure pressure and current overload.

Every mode remains abstract, synthetic and platform-independent.

## Observation boundary

The PPO observation uses only information available at the current simulator step:

- detected active-threat summaries;
- detected type / speed / target-distance / time-to-target summaries;
- known defender reachability, capacity, range and remaining-use state;
- known sensor summaries;
- known asset value / observed damage state;
- current timestep;
- realized penetrations and resource use;
- cumulative realized interaction-failure rate;
- recent failure rates over 1, 3 and 5 steps;
- overload history;
- resource-exhaustion indicator;
- previous tactical mode.

It explicitly excludes:

- undetected threat type, position, velocity or target;
- scenario seed as a feature;
- future trajectories;
- future interaction outcomes;
- oracle choices or hindsight metrics.

Regression tests mutate an undetected threat's type, position, velocity and target and require the PPO observation to remain identical.

## Reward

V1 does not introduce a new optimization objective.

At each step, compute the established scalar episode score from the simulator's current metrics and return the scaled difference from the previous step:

```text
r_t = (score_t - score_{t-1}) / 10
```

PPO uses `gamma=1.0`, so the undiscounted shaped return telescopes exactly to:

```text
(final established score - common initial score) / 10
```

The existing score still contains asset survival, containment, damage, resource consumption and response delay terms.

## Fixed tactical comparator

To separate adaptive value from a merely better fixed mode, all six modes are evaluated on PPO **training/calibration** seeds only. The mode with highest mean established reward becomes the fixed tactical comparator before development evaluation.

Fresh development therefore compares:

1. incumbent mode 0;
2. training-selected best fixed tactical mode;
3. PPO online adaptive mode switching.

## Fresh seed blocks

```text
32000–32999  PPO training / calibration
33000–33399  PPO development evaluation
34000–34399  reserved PPO confirmation
```

Do not inspect `34000–34399` during development.

## Quick V1

```text
PPO training seeds:       32000–32999 sampled during training
static calibration:       32000–32099
PPO model seeds:          42101, 42102
training budget/model:    100,000 environment steps
fresh evaluation:         33000–33019
parallel envs:            min(--workers, 12)
```

Install optional RL dependencies once:

```bash
pip install -e '.[rl]'
```

Then run:

```bash
pytest -q
python -m aegisswarm.adaptive_rl_cli --workers 14
```

Do **not** run `--full` until the quick output is inspected.

## Full development — only after a promising quick result

```text
PPO model seeds:          42101–42105
training budget/model:    500,000 environment steps
static calibration:       32000–32399
fresh evaluation:         33000–33399
```

```bash
python -m aegisswarm.adaptive_rl_cli --full --workers 14
```

## Primary comparisons

The CLI reports:

```text
incumbent survival
training-selected static-best survival
PPO adaptive survival
static-best - incumbent + scenario-bootstrap CI
PPO - incumbent + hierarchical CI
PPO - static-best + hierarchical CI
per-training-seed PPO deltas
PPO tactical-mode usage counts
```

It also reports containment, penetrations, cumulative damage, resources consumed and response delay.

The PPO hierarchical interval resamples both independent PPO training runs and matched development scenarios.

## Decision gate

### PPO materially beats both comparators

Run full development. If the full result remains useful across independent training seeds, freeze the PPO architecture/hyperparameters before any confirmation.

### PPO beats incumbent but not static-best

The result is not evidence for online learning. Prefer the simpler fixed tactical mode and investigate that mode separately.

### PPO approximately ties

Do not immediately increase network size or training budget. First inspect mode collapse, reward learning curves and whether the observation contains sufficient realized-state information.

### PPO worsens

Close PPO V1. Do not claim RL generally failed; the result applies only to this hierarchical PPO formulation and budget.

## Claim boundary

This is a synthetic, abstract decision-support experiment. It does not establish superiority to RL generally, optimization generally, or any real-world defensive system.
