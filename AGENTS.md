# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `ORACLE_DECOMPOSITION.md` — active diagnostic.
4. `STRATEGY_SELECTOR.md` — closed selector protocol.
5. `STOCHASTIC_TRAINING_ABLATION.md` — closed repeated-tape V2.
6. `STOCHASTIC_ROBUST.md` — closed robust-training V1.
7. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
8. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
9. `ROLLING_HORIZON.md` — completed planner history.

## Non-negotiable rules

1. Never consume reserved confirmation/replication seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside a protocol.
4. Compare components by ablation, not ideology.
5. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
6. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
7. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
8. Keep handoff/status docs current after major experiments.
9. Do not run confirmation merely because a quick or development point estimate is positive.
10. Legacy `Simulator` and `SimulatorV2` are different protocol generations; label them explicitly.
11. Do not treat hindsight oracle performance as deployable or predictable without held-out stochastic evidence.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

No tested proposer, compact representation, planner, reliability executor, repeated-tape training scheme, or t=0 selector has robustly replaced it.

## Closed selector V1

Full development on `28000–28399`:

```text
fixed best survival:      0.8275
selector survival:        0.8113
selector-fixed:          -0.0163 CI=[-0.0350,+0.0025]
selector-fixed reward:   -2.960 CI=[-5.3340,-0.6094]
raw hindsight oracle:     0.9338
```

Do not inspect `29000–29399` and do not tune selector model families against this development block by default.

## Active phase — oracle decomposition V1

Branch: `agent/oracle-decomposition`  
Protocol: `aegisswarm-oracle-decomposition-v1`

No policy is trained or changed. The same five frozen programs are evaluated on repeated indexed stochastic tapes of the same structural worlds.

### Quick result — completed

Fresh `30000–30019`, four tapes/world:

```text
single-tape oracle-fixed:       +0.0500 CI=[0.0000,+0.1250]
expected oracle-fixed:          +0.0625 CI=[+0.01875,+0.10625]
cross-tape oracle-fixed:        -0.0312 CI=[-0.0875,+0.03125]
cross-tape choice agreement:     0.450
tape-oracle modal fraction:      0.575
stable fraction of raw gap:     -0.625
```

Interpretation: the apparent best-program advantage is strong when selection and scoring reuse the same stochastic outcomes, but does not generalize to held-out tapes in the quick sample. Best-program identity is unstable. This is evidence that the old ~93–94% raw oracle substantially mixes structural specialization with stochastic luck.

### Full development — authorized

Because only 20 worlds were used in quick and the cross-tape CI remains wide, run the exact frozen diagnostic on:

```text
30000–30399   400 structural worlds
8 independent indexed tapes/world
5 frozen programs
```

Run:

```bash
pytest -q
python -m aegisswarm.oracle_decomposition_cli --full --workers 14
```

Do not inspect `31000–31399`; that is reserved independent replication.

### Decision after full

- Cross-tape gap near zero/negative: close episode-level frozen-program selection and stop using raw oracle survival as a performance target.
- Cross-tape gap materially positive with stable choices: only then justify richer/later-state gating.
- Same-tape oracle large but cross-tape weak: classify the raw gap primarily as stochastic hindsight.

If selection closes, the next performance phase should target online state adaptation / uncertainty-aware sequential control or broader stress-regime benchmarking, not another static selector.
