---
name: aegisswarm-project-context
description: Canonical handoff for understanding, modifying, benchmarking, and advancing the AegisSwarm counter-swarm coordination research platform without invalidating experimental evidence.
last_updated: 2026-08-17
status: architecture-unfrozen
active_branch: agent/optimizer-native-objective
active_protocol: aegisswarm-optimizer-native-objective-v2
primary_external_deadline: 2026-09-30T23:59:00+05:30
---

# AegisSwarm Project Skill / Canonical LLM Handoff

## 0. Read this first

AegisSwarm is an **active research project whose architecture is not frozen**.

Do not assume that the newest branch represents the final product architecture. The repository deliberately contains several generations of experiments because the project is trying to discover which combination of learned strategy generation, local/evolutionary search, optimization, explicit rules, and later adaptive learning produces the strongest defensive coordination system.

The correct mindset is:

> **Use frameworks together when they are complementary; make them compete only in controlled ablations so we can measure what each component contributes.**

The project is currently in a foundation/proof phase. The priority is to produce defensible technical evidence before making strong customer, investor, deployment, or superiority claims.

The current active hypothesis is:

> **Is the repeated ~80–81% development/formal plateau caused by the strategic representation supplied to the optimizer, or by the myopic one-step planning horizon?**

The active representation experiment compares the existing 60-token state-reactive rule objective with a smooth 14-parameter optimizer-native objective under the same local/evolutionary search budget and Hungarian executor.

Do not run a reserved confirmation block merely because a development run completes. First interpret the development evidence, decide whether architecture and hyperparameters are frozen, record that decision, and only then spend the confirmation set.

---

# 1. Mission

AegisSwarm is a **simulation-first defensive counter-swarm coordination research platform**.

The system studies how an AI decision layer can coordinate limited sensing and defensive resources against a heterogeneous incoming swarm while protecting assets and preserving defensive capacity.

The system is not intended to design interceptor hardware or weapon mechanisms. The research contribution is the **coordination and decision layer**.

Human supervision/manual override remains part of the intended operational concept.

---

# 2. Safety and scope boundary

Keep implementation **abstract, synthetic, defensive, and platform-independent**.

Allowed scope includes abstract threat classes, synthetic/dimensionless kinematics, probabilistic sensing, abstract resource capacities/ranges, assignment/scheduling/prioritization/reserve logic, simulation, optimization, search, RL, uncertainty, stress testing, and human-in-the-loop decision support.

Do not extend the repository into weapon construction, payload/warhead design, real-world guidance-to-impact engineering, platform-specific terminal targeting logic, actionable hard-kill engineering details, or instructions for causing physical harm.

---

# 3. End-state architecture hypothesis

The project should not become "a transformer that replaces every classical method."

The current long-term hypothesis is a **hybrid decision architecture**:

```text
sensor / track / asset / resource state
                |
                v
      situation / state representation
                |
                v
    learned or searched strategy layer
    - threat/risk priorities
    - reserve policy
    - objective weights
    - uncertainty/risk posture
    - strategic rules
                |
                v
       constrained optimizer
    - feasible assignment
    - scheduling / allocation
    - capacity / reserve constraints
                |
                v
        hard safety / rule layer
    - forbidden actions
    - fallback behavior
    - manual override constraints
                |
                v
             execution
                |
                v
              outcome
                |
                +----> later online adaptation / learning
```

The key conceptual split is:

> **Learning/search determines WHAT should be optimized. Optimization determines HOW to allocate resources subject to constraints.**

Local/evolutionary search is currently the default offline search engine because Axplorer has not demonstrated a robust incremental benefit under the completed protocols. Axplorer remains an optional proposer/ablation and may become useful again if a future representation becomes sufficiently high-dimensional/structured.

---

# 4. What success eventually means

## Level A — simulator competence

AegisSwarm materially improves protected-asset survival, containment, leakage/penetration, damage, and resource efficiency relative to simple heuristics in the synthetic environment.

## Level B — architectural contribution

A full hybrid architecture outperforms reduced variants under controlled ablations.

## Level C — defensible external evidence

Before deployment/customer/investor superiority claims, add stronger optimization and RL/MARL baselines, common-random-number/stochastic replication, richer uncertainty and scenario families, tail-risk/CVaR evaluation, objective-weight sensitivity, runtime/scaling, calibration to defensible public literature/data where possible, and versioned reproducible protocols.

---

# 5. Current simulator and evaluation model

The simulator is synthetic and normalized. Core elements include heterogeneous `DIRECT`, `FAST`, and `DECOY` threats; protected assets; finite-capacity defenders/resources; probabilistic sensors; seeded scenario generation; abstract interaction success; penetration/damage; and a repeated `sense -> assign -> resolve -> move -> penetrate` loop.

Typical default scenario: 30 threats, 8 defenders, 2 assets, 3 sensors, 20% decoys, 25% fast threats, maximum 150 steps.

Primary KPI: `asset_survival_rate`.

Secondary metrics: containment, penetrations, cumulative damage, defenders consumed, response delay, and runtime.

Current scalar loss:

```text
100 * (1 - survival)
+ 40 * (1 - containment)
+ 3 * damage
+ 0.15 * resources
+ 0.05 * response_delay
```

Fitness is `max(0, 200 - loss)`.

Important caveat: policies share scenario seeds but stochastic interaction RNG is not yet indexed by event/policy-independent random tapes. A future simulator version should improve common-random-number coupling; do not silently change this during an active evidence protocol.

---

# 6. Baselines and interpretation

Current baselines include random, closest, highest-risk, greedy risk/cost, per-step Hungarian assignment, simple tabular Q-learning, local/evolutionary search, and Axplorer-style generative proposal + local refinement.

The current Hungarian baseline is a **myopic per-step bipartite assignment optimizer**, not a rolling-horizon/MILP/MPC state-of-the-art optimizer.

The current Q-learning baseline is a **small tabular/template RL baseline**, not PPO/MAPPO/MARL.

Never generalize current results into "AegisSwarm beats optimization" or "AegisSwarm beats RL."

---

# 7. Representation history

## 7.1 Legacy 8-gene strategy

Original development result: Q-learning 35.5%, legacy Axplorer 58.0%, legacy local search 74.5%. Conclusion: original learned proposer did not justify itself.

## 7.2 Structured 12-rule / 60-token programs

Each rule contains `enabled | condition | threshold | action | magnitude`. Conditions include urgency, distance, threat type, low resources, and high damage. Actions include priority changes, reserve/release reserve, stickiness, and decoy penalties.

This representation produced the first strong structured policies and remains the current strong comparator.

---

# 8. Experiment ledger

## Experiment 0 — original heuristic/learning proof

Approximate 100-scenario development results:

| Method | Survival |
|---|---:|
| random | 32.0% |
| closest | 26.0% |
| highest risk | 34.0% |
| greedy risk/cost | 31.5% |
| Hungarian | 30.5% |
| tabular Q-learning | 35.5% |
| legacy local | 74.5% |
| legacy Axplorer | 58.0% |

## Experiment 1 — structured representation development

Seeds 2000–2099, inspected during architecture iteration:

| Method | Survival |
|---|---:|
| legacy local | 74.5% |
| legacy Axplorer | 58.0% |
| structured local | 80.5% |
| structured Axplorer V1 | 87.5% |

Promising development evidence only; not final.

## Experiment 2 — V1 formal frozen holdout

5 matched search runs, 1,800 unique candidate evaluations/run, 400 untouched scenarios 2100–2499:

```text
structured local survival:    0.800
structured Axplorer survival: 0.814
Axplorer - local:              +0.0132
95% hierarchical CI:          [-0.0365, +0.0665]
paired p-value:                0.160042
```

Conclusion: **no statistically robust Axplorer advantage**.

## Experiment 3 — Axplorer V2 development

Seeds 3000–3399:

```text
structured local:      0.794
Axplorer V2:            0.810
V2 - local:            +0.0168
hierarchical CI:       [-0.0350, +0.0773]
sign-flip p-value:      0.003700
```

Small positive point estimate, but training-run uncertainty remains material. Do not claim robust superiority.

## Experiment 4 — fixed-strategy hybrid executor ablation

Seeds 4000–4399:

| Variant | Survival |
|---|---:|
| fixed optimizer only | 31.0% |
| local + greedy | 80.0% |
| local + optimizer | 79.5% |
| V2 + greedy | 80.5% |
| V2 + optimizer | 80.5% |

Conclusion: **swapping an optimizer under strategies trained for greedy execution did not help**. Strategy/executor must be trained jointly/in-loop.

## Experiment 5 — hybrid objective learning

Seeds 5000–5399. Every candidate strategy was evaluated through the optimizer during search.

```text
fixed_optimizer: 0.320
hybrid_local:     0.805 CI=[0.77624375, 0.83100625]
hybrid_axplorer:  0.810 CI=[0.77775, 0.841]
Axplorer - local: +0.0055 CI=[-0.0235, +0.0320]
p-value:          0.507075
```

Conclusions:

- optimizer-aware objective search is highly valuable relative to the current fixed hand-written objective in this synthetic simulator;
- Axplorer is statistically tied with optimizer-aware local/evolutionary search;
- **NO FREEZE, NO CONFIRMATION**;
- proposer choice is deprioritized;
- repeated ~80–81% results suggest a representation/planning ceiling.

## Experiment 6 — optimizer-native objective representation (ACTIVE)

### V1 quick — invalidated before full development

The first 10-parameter native representation used a zero-centred utility and omitted important state-reactive information. Quick mode on the first 20 development scenarios produced:

```text
fixed_optimizer:   0.350
rule_objective:    0.688 CI=[0.400, 0.925]
native_v1:         0.300 CI=[0.175, 0.425]
native - rule:    -0.3875 CI=[-0.650, -0.075]
p-value:            0.000100
```

This was a **diagnostic integration/development result, not evidence against optimizer-native objectives generally**. V1 was stopped before the full 5×1,800 campaign.

Diagnosis:

- unlike the rule-guided policy, V1 had no guaranteed positive structural base utility;
- many candidates could prefer no-op assignments simply because utilities remained non-positive;
- V1 discarded state-reactive target-damage and reserve/release interactions.

### V2 — current active protocol

Protocol: `aegisswarm-optimizer-native-objective-v2`.

V2 shares the rule-guided policy's structural base:

```text
2 * abstract threat-type prior
+ inverse target-asset distance term
+ inverse defender/threat distance term
```

It then searches 14 smooth state modifiers covering urgency, asset value, threat-class modifiers, defender/threat closeness, defender capacity, resource scarcity, reserve threshold, release-urgency threshold, persistence, speed, target damage, and urgency×scarcity.

Primary comparison:

```text
fixed objective + optimizer
60-token searched rule objective + optimizer
14-parameter optimizer-native V2 objective + optimizer
```

Both searched representations start from stochastic candidates and use the same local/evolutionary search family, matched seeds, and candidate budget.

Development: 9000–9399. The first 20 seeds have already been inspected by V1 quick, so this block is development-only.

Reserved confirmation: 10000–10399, still untouched and code-gated.

V2 writes to fresh `artifacts/optimizer_native_v2_*` paths so malformed V1 quick artifacts cannot be resumed.

---

# 9. Seed/evidence ledger

| Seed block | Status | Meaning |
|---|---|---|
| 0–255 | training pool | candidate scoring/training |
| 1000–1099 | validation | earlier integration/model selection |
| 2000–2099 | consumed development-test | structured architecture work |
| 2100–2499 | consumed V1 final holdout | V1 formal confirmation |
| 3000–3399 | consumed V2 development | proposer development |
| 4000–4399 | consumed hybrid-executor development | executor swap |
| 5000–5399 | consumed hybrid-objective development | optimizer-aware strategy search |
| 6000–6399 | reserved V2 confirmation | untouched |
| 7000–7399 | reserved executor-swap confirmation | untouched/likely obsolete |
| 8000–8399 | reserved hybrid-objective confirmation | untouched; do not use |
| 9000–9399 | active optimizer-native development | development-only; first 20 inspected by V1 quick |
| 10000–10399 | reserved optimizer-native confirmation | untouched; do not use until freeze |

Never reuse consumed blocks as new evidence. Never tune on confirmation and still call it confirmation.

---

# 10. Statistics/evidence policy

Account for scenario uncertainty and training/search-run uncertainty. Current tools include hierarchical bootstrap CIs and paired sign-flip tests. Do not announce significance from one p-value when the effect-size CI still materially crosses zero without explaining estimand differences.

Before confirmation, define the primary estimand/test, report point estimate + compatible 95% CI, report per-training-run effects, and preferably require an operationally meaningful effect rather than merely a positive point estimate.

---

# 11. Current active files

Important files include:

- `aegisswarm/simulator.py`, `scenarios.py`, `models.py` — environment;
- `aegisswarm/rule_program.py` — strong 60-token state-reactive representation;
- `aegisswarm/hybrid.py` — rule-guided Hungarian executor;
- `aegisswarm/hybrid_objective.py` — optimizer-aware rule search;
- `aegisswarm/optimizer_native.py` — optimizer-native V2 representation/search;
- `aegisswarm/optimizer_native_proof.py` — active V2 protocol/evaluation;
- `aegisswarm/optimizer_native_cli.py` — active CLI;
- `aegisswarm/splits.py` — seed/evidence ledger;
- `docs/AEGISSWARM_STATUS.md` — current-state overlay.

Current branch: `agent/optimizer-native-objective`.

Current draft PR: PR #3, `Test optimizer-native strategic objective representation`.

---

# 12. Known implementation lessons

## Multiprocessing worker shadowing

Avoid duplicate top-level worker names/signatures; macOS spawn exposed this earlier.

## Diversity archive metric mismatch

Keep evaluator metric schemas synchronized with archive ranking requirements.

## Native V1 zero-centred utility

When comparing strategic representations, preserve equivalent structural semantics. V1 accidentally made the new representation learn basic positive assignment utility that the rule comparator received for free. V2 fixes this by sharing the same structural base utility and changing only the strategic modifiers.

---

# 13. Current decision tree

## If optimizer-native V2 clearly beats the 60-token rule representation

Inspect secondary metrics and run stability. If the effect is operationally meaningful and robust, freeze architecture/hyperparameters before using 10000–10399 confirmation.

## If V2 ties the rule representation near the existing plateau

Stop representation tuning. Move to a new protocol testing a short rolling-horizon/MPC-style abstract planner. Keep the stronger/simpler representation fixed.

## If V2 remains materially worse

Keep the 60-token rule representation and move to planning. Do not keep expanding the vector merely to force a win.

---

# 14. Immediate runbook

```bash
git checkout agent/optimizer-native-objective
git pull origin agent/optimizer-native-objective
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

If V2 quick no longer shows pathological native under-assignment, run:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do not run `--confirm` automatically.

---

# 15. Next architecture stage if representation does not break the plateau

Test a short rolling-horizon planner rather than one-step Hungarian matching. The goal is to model temporal consequences such as future resource scarcity, assignment congestion, reserve value, and delayed effects. This should be a new protocol because execution semantics change.

After that, consider stronger sequential learning baselines, uncertainty/partial-observation improvements, simulator random tapes/stochastic replications, richer abstract scenario families, and tail-risk/CVaR metrics.

---

# 16. External deadline / iDEX

Current tracked external target: iDEX Open Challenge deadline **30 September 2026, 11:59 PM**, last verified on the official site on 2026-08-17. Re-verify before submission work.

Internal working intent: reach one strongest reproducible architecture and core ablations by late August/early September, then freeze the technical story and build the evidence/submission package. Do not invent deployment readiness or real-world performance from the synthetic simulator.

---

# 17. Claims policy

Supported inside the synthetic environment:

- structured/search-based strategy is substantially stronger than early simple baselines;
- V1 Axplorer did not robustly beat structured local search on its untouched holdout;
- V2 Axplorer produced only a small uncertain development increment;
- swapping an optimizer under greedily trained strategies did not help;
- searching the objective with the optimizer in-loop is substantially stronger than the current fixed hand-written objective;
- Axplorer and optimizer-aware local/evolutionary search are statistically tied under the completed hybrid-objective protocol.

Not supported:

- Axplorer superiority;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- state-of-the-art counter-swarm superiority;
- real-world effectiveness percentages;
- deployment readiness.

---

# 18. Development philosophy

1. Performance first, narrative second.
2. One hypothesis at a time.
3. Keep strong comparators.
4. Exploit complementarity between learning/search and optimization.
5. Measure marginal contribution by ablation.
6. Protect holdouts.
7. Preserve negative results.
8. Prefer reproducibility to one-off numbers.
9. Record architecture changes caused by inspected development results.
10. The final system can be hybrid even if no learned component individually beats every classical framework.

---

# 19. Workflow for any LLM

Before modifying code:

1. Read this file.
2. Read `docs/AEGISSWARM_STATUS.md` for the latest overlay.
3. Read `AGENTS.md`.
4. Inspect `aegisswarm/splits.py` before evaluation.
5. Identify whether the task is bug fixing, development, confirmation, architecture design, or submission work.
6. If a result is pasted, classify it as training, quick/integration, development, or untouched confirmation before interpreting it.
7. Never consume confirmation without explicit freeze status.
8. Update the handoff/status documents when a major experiment or architectural decision occurs.

---

# 20. Project separation

AegisSwarm is separate from Ripple (airline disruption recovery) and separate from MISR/rectangle-integrality-gap research. Do not mix their deadlines, data, or claims unless explicitly asked.

---

# 21. Current status in one paragraph

As of **2026-08-17**, AegisSwarm has a functioning synthetic counter-swarm simulator, heuristic/optimization/RL baselines, a strong 60-token state-reactive strategy language, local/evolutionary search, two generations of an Axplorer-style proposer, formal held-out statistics, hybrid optimizer execution, and optimizer-aware strategy search. The strongest full-development result currently shows optimizer-aware local search at 80.5% survival and Axplorer at 81.0%, statistically tied, while the fixed hand-written optimizer objective is far weaker. This shifted attention from proposer choice to representation/planning. The first compact optimizer-native representation failed badly in quick mode because its zero-centred utility was not semantically comparable to the rule policy; it was invalidated before full development. The active protocol is now **optimizer-native V2**, which shares the rule-guided structural base utility and searches 14 smooth state modifiers. Development remains on `9000–9399`; confirmation `10000–10399` is untouched and must remain so until an explicit freeze decision. If V2 does not materially beat the 60-token representation, the next architecture should target the myopic one-step planning horizon rather than another proposer/representation iteration.
