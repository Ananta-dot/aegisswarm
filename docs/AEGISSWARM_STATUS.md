# AegisSwarm — Current Research Status

**Updated:** 2026-08-17
**Architecture:** NOT FROZEN. The current incumbent is a comparison anchor, not the final architecture.
**Current branch:** `agent/ppo-adaptive-control`
**External deadline recorded in canonical skill:** 2026-09-30 23:59 +05:30

For full historical context, read `docs/AEGISSWARM_SKILL.md`. For PPO details read `PPO_ADAPTIVE_CONTROL.md` and `PPO_FROZEN_EXTENSION.md`.

## Mission

AegisSwarm is a simulation-first research platform for adaptive defensive resource allocation under stochastic, partially observed threat interactions. The research target is a robust **decision/coordination architecture**, not a claim that one framework defeats all other frameworks.

The architecture is deliberately open. Structured rules, optimization, local/evolutionary search, Axplorer, reliability mechanisms, planning, RL/PPO, and hybrids are all candidate components. Use them together when complementary; compare them in controlled ablations when attribution matters.

## Current incumbent

```text
60-token state-reactive structured rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested alternative has robustly replaced this incumbent yet. This does **not** mean optimization/RL/evolutionary search are being rejected; they remain possible components of the final architecture.

## Major evidence so far

### Conventional baselines / early learning

Approximate development survival:

```text
random             0.320
closest            0.260
highest_risk       0.340
greedy_risk_cost    0.315
Hungarian           0.305
Q-learning          0.355
legacy local        0.745
legacy Axplorer     0.580
```

Structured rule search substantially improved on these baselines.

### Structured rule / Axplorer search

The structured 60-token representation became the strong comparator. Axplorer repeatedly showed positive point estimates but no robust enough advantage to justify replacing local/evolutionary search as the default proposer.

A representative development comparison:

```text
rule_local:       ~0.794
Axplorer V2:      ~0.810
```

The correct conclusion is not 'Axplorer is bad'; it is that its incremental benefit is not yet established under the completed protocols.

### Optimizer-aware objective search

The major architectural lesson is that strategies should be evaluated **through the optimizer they will actually use**. Swapping an optimizer underneath strategies trained for another executor did not help.

Hybrid objective development:

```text
fixed optimizer: 0.320
hybrid local:    0.805 CI=[0.7762,0.8310]
hybrid Axplorer: 0.810 CI=[0.7778,0.8410]
```

Thus optimizer-aware strategy search is important; Axplorer versus local/evolutionary search is still unresolved/tied.

### Reliability / backup

400-scenario development:

```text
incumbent:            0.809
reliability weighted: 0.810
contingent backup:    0.825
```

Backup has a useful point estimate but its CI still crosses zero. It is a candidate execution component, not a proven replacement.

### Rolling horizon

400-scenario V2 screen:

```text
one-step:    0.808
rolling V2:  0.801
delta:      -0.0065 CI=[-0.0325,+0.01825]
```

Rolling horizon is currently not justified as the primary executor and costs materially more runtime. Keep it available only for a new, specific hypothesis.

## Evidence hardening: where is the headroom?

400 development scenarios found:

```text
normal incumbent:            0.801
perfect sensing:             0.801
deterministic interactions:  0.999
interaction headroom:       +0.1980 CI=[+0.166,+0.23625]
```

This indicates that the largest identified simulator headroom is stochastic interaction reliability rather than simply missing sensing. Realized failures, resource depletion, overload, damage and penetrations become observable during an episode. That makes online adaptation a legitimate hypothesis.

## Oracle decomposition: episode-level program selection is closed

Five candidate programs across 400 stochastic worlds and 8 indexed tapes/world:

```text
program means:               [0.7522,0.8370,0.8192,0.8131,0.8214]
single-tape oracle - fixed:  +0.1037 CI=[+0.0825,+0.12625]
expected oracle - fixed:     +0.0495 CI=[+0.04219,+0.05688]
cross-tape oracle - fixed:   -0.0150 CI=[-0.02438,-0.00531]
choice agreement:             0.305
```

The raw best-of-five oracle is hindsight-driven. The best frozen program on one stochastic tape often does not remain best on another tape from the same structural world. Do not claim oracle performance is attainable.

The naive observable strategy selector also failed:

```text
fixed best: 0.828
selector:   0.811
oracle:     0.934
```

Therefore episode-level frozen-program selection is closed. This does **not** close online tactical adaptation.

## PPO V1

PPO was introduced as a hierarchical **online tactical controller**, not as a replacement for the structured program or constrained assignment optimizer.

Hierarchy:

```text
frozen strategic program
        |
        v
PPO chooses tactical mode
        |
        v
constrained assignment executor
```

Six tactical modes:

```text
0 incumbent
1 urgency
2 conserve
3 reliability
4 backup
5 failure_recovery
```

PPO does not directly choose defender-threat assignments.

Observations use detected/current state and realized history only. Hidden undetected state, future outcomes, scenario seed and oracle information are forbidden.

Reward remains the established project score increment:

```text
r_t = (established_score_t - established_score_{t-1}) / 10
```

### PPO quick

Two independent models, seeds `42101/42102`, 100k steps/model:

```text
incumbent:    0.800
static best:  0.800
PPO:          0.800
```

The models nevertheless learned different tactical mixtures, so the tie did not imply behavioral collapse.

### Frozen PPO generalization — COMPLETE

Exact saved models evaluated on 100 additional untouched development scenarios:

```text
survival incumbent/static/PPO:  0.820 / 0.855 / 0.840
reward incumbent/static/PPO:    157.255 / 161.168 / 159.510
```

PPO versus incumbent:

```text
survival: +0.0200 CI=[-0.01,+0.06]
reward:   +2.255  CI=[-1.329,+6.929]
```

PPO versus static backup:

```text
survival: -0.0150 CI=[-0.055,+0.02]
reward:   -1.658 CI=[-6.267,+2.236]
```

Per PPO seed versus incumbent:

```text
survival: [+0.01,+0.03]
reward:   [+0.991,+3.518]
```

Correct interpretation:

> PPO V1 has a positive but statistically inconclusive generalization signal over the incumbent on both survival and established reward. It has not beaten the strongest static backup strategy.

Secondary metrics:

```text
                    incumbent     PPO       static backup
containment          0.6514       0.6529    0.6502
damage               1.5610       1.4909    1.4044
penetrations         2.280        2.205     2.090
overload steps       55.24        53.72     54.34
resource exhaustion  0.45         0.51      0.51
```

PPO appears to change failure management rather than simply improving interaction reliability. It also consumes resources more aggressively than the incumbent.

## Next hypothesis: PPO V2

Do **not** simply spend a large PPO V1 training budget.

The next hypothesis is **resource/reliability-aware hierarchical PPO V2**. Keep the base structured program and constrained assignment layer frozen for the first test, but expose richer observable information:

```text
current resource availability
resource exhaustion risk
recent interaction failures/successes
overload state/history
threat pressure
available defender capacity
estimated time-to-impact
current tactical mode
```

The hypothesis is that PPO V1 lacks enough explicit resource/reliability state to make good tactical decisions.

Compare:

```text
same frozen strategic program
        |
        +-- incumbent executor
        +-- strongest static executor
        +-- PPO V2 adaptive executor
```

Keep the established reward. Do not invent an objective merely to make PPO win.

If PPO V2 produces a consistent, operationally meaningful improvement over both incumbent and static backup, keep RL as an architectural component and define a fresh longer-training protocol. If it ties or loses, change the learning abstraction or close this six-mode PPO hypothesis; do not merely increase timesteps.

## Evidence boundaries

PPO blocks:

```text
32000–32999  training / calibration
33000–33019  PPO V1 quick — inspected
33020–33119  frozen PPO generalization — inspected
33120–33399  remaining PPO development
34000–34399  reserved confirmation — DO NOT INSPECT
```

The broader project also has reserved confirmation blocks documented in `docs/AEGISSWARM_SKILL.md`. Never tune on confirmation data.

## Claim discipline

Supported:

- structured rule search is the current incumbent;
- stochastic interaction failure is the dominant identified simulator headroom;
- episode-level frozen-program selection does not generalize across stochastic tapes;
- rolling horizon, reliability variants, selectors and Axplorer have not yet robustly replaced the incumbent;
- PPO V1 shows a positive but statistically inconclusive signal over the incumbent;
- static backup remains stronger than PPO V1 on the current 100-scenario extension.

Not supported:

- 'AegisSwarm beats RL.'
- 'AegisSwarm beats optimization.'
- 'AegisSwarm beats evolutionary search.'
- 'AegisSwarm beats heuristics.'
- 'PPO does not work.'
- treating oracle performance as attainable;
- treating deterministic interaction diagnostics as attainable;
- real-world effectiveness/deployment claims from this simulator.

## Agent runbook

When asked what to do next:

1. Read this file and `docs/AEGISSWARM_SKILL.md`.
2. Inspect the active branch/protocol and recent experiment documents.
3. Identify the current incumbent and the current open hypothesis.
4. Do not assume architecture freeze.
5. Prefer controlled ablations over indiscriminate extra training.
6. Protect reserved confirmation seeds.
7. Compare against the incumbent and strongest relevant alternative.
8. Report point estimates, CIs, per-run effects and runtime/resource costs.
9. Explicitly close failed hypotheses so they are not repeated.
10. Update this status after material experiments.

For every new experiment record: hypothesis, frozen components, changed components, train/eval/confirmation seeds, primary metric, reward definition, statistical test, runtime/resource cost, and decision gate.

The goal is not the largest development number. The goal is a reproducible architecture whose improvements survive controlled stochastic evaluation.
