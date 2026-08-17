---
name: aegisswarm-project-context
description: Canonical handoff for understanding, modifying, benchmarking, and advancing the AegisSwarm counter-swarm coordination research platform without invalidating experimental evidence.
last_updated: 2026-08-17
status: architecture-unfrozen
active_branch: agent/hybrid-objective-learning
active_protocol: aegisswarm-hybrid-objective-v1
primary_external_deadline: 2026-09-30T23:59:00+05:30
---

# AegisSwarm Project Skill / Canonical LLM Handoff

## 0. Read this first

AegisSwarm is an **active research project whose architecture is not frozen**.

Do not assume that the newest branch represents the final product architecture. The repository deliberately contains several generations of experiments because the project is trying to discover which combination of learned strategy generation, local/evolutionary search, optimization, explicit rules, and later adaptive learning produces the strongest defensive coordination system.

The correct mindset is:

> **Use frameworks together when they are complementary; make them compete only in controlled ablations so we can measure what each component contributes.**

The project is currently in a foundation/proof phase. The priority is to produce defensible technical evidence before making strong customer, investor, deployment, or superiority claims.

The immediate active hypothesis is:

> **Can AegisSwarm learn a better strategic objective for a constrained optimizer, and does a learned generative proposer add value beyond equally budgeted conventional search when both use the same optimizer?**

Do not run a reserved confirmation block merely because a development run completes. First interpret the development evidence, decide whether architecture and hyperparameters are frozen, record that decision, and only then spend the confirmation set.

---

# 1. Mission

AegisSwarm is a **simulation-first defensive counter-swarm coordination research platform**.

The system studies how an AI decision layer can coordinate limited sensing and defensive resources against a heterogeneous incoming swarm while protecting assets and preserving defensive capacity.

The system is not intended to design interceptor hardware or weapon mechanisms. The research contribution is the **coordination and decision layer**.

At a conceptual level, the eventual system should answer questions such as:

- what threats matter most right now;
- which resources should remain in reserve;
- what objective the allocation optimizer should prioritize;
- how assignments should change as the state evolves;
- how to trade containment, asset survival, resource use, and response delay;
- how to remain robust under uncertain sensing, decoys, fast threats, resource scarcity, and changing swarm composition.

Human supervision/manual override remains part of the intended operational concept.

---

# 2. Safety and scope boundary

Keep implementation **abstract, synthetic, defensive, and platform-independent**.

Allowed project scope:

- abstract threat classes;
- synthetic/dimensionless kinematics;
- probabilistic sensing;
- abstract resource capacities and ranges;
- assignment, scheduling, prioritization, reserve logic;
- simulation, optimization, search, RL, uncertainty, stress testing;
- decision-support and human-in-the-loop architecture.

Do not extend the repository into:

- weapon construction;
- payload/warhead design;
- real-world guidance-to-impact engineering;
- platform-specific terminal targeting logic;
- actionable hard-kill engineering details;
- instructions for causing physical harm.

If a future task requires higher-fidelity real-world integration, keep the research at the level of interfaces, abstract constraints, data schemas, and decision-support evaluation unless the project scope is explicitly and safely redefined.

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

Local search may remain valuable for offline improvement and proposal repair. RL may later be useful for adaptation to sequential non-stationarity. Explicit rules remain useful for safety, fallback behavior, and interpretable constraints.

Therefore, do not frame the ultimate product objective as "beat optimization" or "beat RL." Those comparisons are useful only as ablations.

---

# 4. What success eventually means

There are three progressively stronger success levels.

## Level A — simulator competence

AegisSwarm materially improves protected-asset survival, containment, leakage/penetration, damage, and resource efficiency relative to simple heuristics in the synthetic environment.

This is already substantially supported.

## Level B — architectural contribution

A full hybrid architecture outperforms reduced versions of itself under controlled ablations, for example:

```text
fixed objective + optimizer
searched objective + optimizer
learned objective + optimizer
learned objective + local refinement + optimizer
full system with adaptation
```

This is the current research target.

## Level C — defensible external evidence

Before deployment/customer/investor superiority claims, the system should additionally have:

- multiple untouched scenario blocks;
- stronger optimization baseline(s), preferably rolling-horizon;
- stronger sequential learning baseline(s), e.g. PPO/MAPPO/MARL where appropriate;
- stochastic replications/common-random-number evaluation;
- objective-weight sensitivity;
- richer abstract swarm behaviors;
- tail-risk/CVaR evaluation;
- calibration against defensible public data/literature where possible;
- runtime/scaling measurements;
- versioned protocols and reproducible artifacts.

Do not collapse Level A or B evidence into Level C claims.

---

# 5. Current simulator and evaluation model

The current simulator is synthetic and normalized.

Core elements include:

- heterogeneous threat types: `DIRECT`, `FAST`, `DECOY`;
- protected assets;
- defenders/resources with range, finite capacity/uses, availability and assignment state;
- sensors with probabilistic distance-dependent detection;
- seeded scenario generation;
- abstract interaction success probability;
- penetration and abstract asset damage;
- repeated `sense -> assign -> resolve -> move -> penetrate` loop.

Typical default scenario:

- 30 threats;
- 8 defenders;
- 2 assets;
- 3 sensors;
- 20% decoys;
- 25% fast threats;
- maximum 150 steps.

Primary KPI:

- `asset_survival_rate`

Secondary metrics:

- `containment_rate`;
- `penetrations`;
- `cumulative_damage`;
- `defenders_consumed`;
- `mean_response_delay`;
- runtime as a separate systems metric.

Current scalar training loss:

```text
100 * (1 - survival)
+ 40 * (1 - containment)
+ 3 * damage
+ 0.15 * resources
+ 0.05 * response_delay
```

Fitness is `max(0, 200 - loss)`.

These weights are research design choices, not physical doctrine. They must eventually receive sensitivity analysis.

## Important simulator caveat

Policies currently run on the same scenario seed, but policy-dependent interaction calls can consume RNG in different sequences. This means the simulator is not yet using a perfect common-random-number/random-tape design for every stochastic event.

A future simulator version should consider indexed random tapes or stochastic replications per scenario. Do not silently change this during an active evidence protocol; doing so creates a new simulator version and invalidates direct comparability.

---

# 6. Baselines and what they actually represent

Current baseline families include:

- random assignment;
- closest threat;
- highest risk;
- greedy risk/cost;
- per-step Hungarian assignment;
- simple tabular Q-learning over a small strategy-template set;
- local/evolutionary search;
- Axplorer-style transformer proposal + local refinement.

Critical interpretation rules:

- The current Hungarian baseline is a **myopic per-step bipartite assignment optimizer**, not a rolling-horizon/MILP/MPC state-of-the-art optimizer.
- The current Q-learning baseline is a **small tabular/template RL baseline**, not PPO/MAPPO/MARL or a comprehensive state-of-the-art RL baseline.

Therefore never write:

- "AegisSwarm beats optimization";
- "AegisSwarm beats reinforcement learning";
- "transformers are superior to optimization/RL";

based only on the current baselines.

Acceptable language is narrower, e.g.:

- "The structured policy outperformed the current myopic Hungarian baseline in this simulator."
- "The current tabular Q-learning baseline was weaker than structured search."
- "The learned proposer did/did not add value over an equally budgeted local-search comparator under this protocol."

---

# 7. Strategy representation history

## 7.1 Legacy 8-gene representation

The original policy encoded eight global strategy weights such as urgency, defender distance, type priority, assignment stickiness, resource preservation, decoy penalty, and reserve threshold.

This search space was small and smooth enough that conventional local search was very competitive.

Important development result on the original 100-scenario evaluation:

| Method | Asset survival |
|---|---:|
| Q-learning | 35.5% |
| legacy Axplorer | 58.0% |
| legacy local search | 74.5% |

Interpretation: the original learned proposer did **not** justify itself. Local search was substantially better.

## 7.2 Structured 12-rule / 60-token programs

The project then moved to a larger ordered rule program. Each rule has five token fields conceptually corresponding to:

```text
enabled | condition | threshold | action | magnitude
```

Current abstract conditions include ideas such as urgency, defender distance, threat type, low resources, and accumulated asset damage.

Current abstract actions include priority changes, reserve/release-reserve behavior, stickiness, and decoy penalties.

The structured representation was intended to give search a meaningful combinatorial language rather than a tiny vector of global weights.

---

# 8. Experiment ledger — what has actually happened

This section is the canonical historical record. If a future run supersedes these numbers, append a new entry rather than silently rewriting history.

## Experiment 0 — original heuristic/learning proof

100 held-out-like scenarios were used before the methodology was fully frozen.

Approximate key results:

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

Conclusion: structured/search-based policies looked promising, but the original Axplorer implementation was weaker than conventional local search.

## Experiment 1 — structured representation development ablation

On the 100-scenario development evaluation (seeds 2000–2099), after introducing the 12-rule/60-token program:

| Method | Survival | Containment | Penetrations | Damage |
|---|---:|---:|---:|---:|
| legacy local | 74.5% | 58.1% | 2.92 | 2.080 |
| legacy Axplorer | 58.0% | 48.2% | 4.12 | 2.883 |
| structured local | 80.5% | 61.9% | 2.28 | 1.599 |
| structured Axplorer V1 | 87.5% | 65.5% | 1.98 | 1.398 |

This looked excellent, but these scenarios had been inspected during architecture iteration. They were therefore reclassified as **development-test**, not final evidence.

Interpretation:

- structured representation clearly looked stronger than legacy representation;
- V1 Axplorer appeared better than structured local search on this development block;
- result was promising but not unbiased final evidence.

## Experiment 2 — formal V1 frozen holdout

Protocol included:

- 5 matched training/search seeds;
- identical 16-scenario training bundle;
- 1,800 unique candidate-policy evaluations per method/run;
- structured local vs structured Axplorer V1;
- 400 untouched scenarios, seeds 2100–2499;
- hierarchical bootstrap and paired sign-flip testing;
- stress families.

Final primary result:

```text
structured local survival:    0.800
structured Axplorer survival: 0.814
Axplorer - local:              +0.0132
95% hierarchical CI:          [-0.0365, +0.0665]
paired p-value:                0.160042
```

Conclusion:

> **V1 did not establish a statistically robust Axplorer advantage over structured local search.**

The correct interpretation is statistical parity with a small positive point estimate, not a transformer victory.

## Experiment 3 — Axplorer V2

V2 changed the learned proposer while keeping the simulator/objective/rule language/comparator concept stable.

V2 introduced:

- fitness/rank conditioning;
- score-weighted likelihood training;
- field-specific grammar heads;
- canonical program encoding;
- a multi-objective diversity archive.

Development block: seeds 3000–3399.

Full V2 development result:

```text
structured local survival:     0.794
Axplorer V2 survival:           0.810
V2 - local:                     +0.0168
95% hierarchical CI:           [-0.0350, +0.0773]
paired sign-flip p-value:       0.003700
```

Interpretation:

- V2 has a small positive point estimate (+1.68 pp);
- scenario-level paired differences appear fairly consistent under the sign-flip test;
- training-run uncertainty remains large enough that the hierarchical CI crosses zero;
- with only five independently trained policies, do **not** claim a robust effect size;
- **do not consume the V2 confirmation set yet** solely because p < 0.05 under one test.

The mismatch between sign-flip significance and the hierarchical CI should be cleaned up by aligning the primary estimand/test before publication-quality reporting.

## Experiment 4 — post-hoc hybrid executor ablation

Question: if we hold already-discovered strategies fixed and replace greedy execution with a Hungarian optimizer, does optimization add value?

Fresh hybrid development block: seeds 4000–4399.

Full 400-scenario results:

| Variant | Survival |
|---|---:|
| fixed optimizer only | 31.0% |
| local strategy + greedy | 80.0% |
| local strategy + optimizer | 79.5% |
| V2 strategy + greedy | 80.5% |
| V2 strategy + optimizer | 80.5% |

Key comparisons:

```text
optimizer effect on V2:         -0.0003
95% CI:                          [-0.01475, +0.016]
p-value:                         1.000000

V2 strategy effect w/ optimizer: +0.0100
95% CI:                          [-0.0525, +0.0823]
p-value:                         0.061047
```

Conclusion:

> **Naively swapping an optimizer underneath strategies trained for greedy execution did not help.**

This does not imply optimization is useless. It implies the strategy and executor are coupled and should be trained jointly/in-loop.

The very large gap between the crude fixed optimizer and strategy-guided variants also suggests that objective quality is critical: an exact optimizer can still solve the wrong objective perfectly.

This result caused the current architectural pivot.

## Experiment 5 — hybrid objective learning (ACTIVE)

Active protocol: `aegisswarm-hybrid-objective-v1`.

Active branch: `agent/hybrid-objective-learning`.

Core change:

> **Every searched candidate strategy is now evaluated through the same rule-guided Hungarian optimizer during training.**

We are no longer training for greedy execution and swapping an optimizer in afterward.

Development comparison:

```text
fixed objective + optimizer
hybrid local-search objective + optimizer
hybrid Axplorer objective + optimizer
```

Fairness controls:

- 5 matched search seeds in full mode;
- 16 fixed training scenarios;
- 1,800 unique candidate evaluations per method/run;
- same optimizer for local and Axplorer candidates;
- same rule language;
- same simulator and scoring;
- fresh development scenarios.

Quick integration/development result (20 scenarios; **not evidence**):

```text
fixed_optimizer survival: 0.275
hybrid_local survival:     0.675   CI=[0.500, 0.800]
hybrid_axplorer survival:  0.725   CI=[0.525, 0.900]
Axplorer - local:           +0.0500 CI=[-0.125, +0.225]
paired p-value:             0.583321
```

Interpretation: the pipeline works and optimizer-aware search can find materially stronger objectives than the fixed optimizer even in the tiny run, but the Axplorer-vs-local difference is far too uncertain to interpret.

**Next action:** run the full 400-scenario development protocol on seeds 5000–5399. Do not run confirmation first.

---

# 9. Seed/evidence ledger — preserve this rigorously

| Seed block | Status | Meaning |
|---|---|---|
| 0–255 | training pool | candidate scoring/training; not evidence |
| 1000–1099 | validation | earlier validation/integration work |
| 2000–2099 | consumed development-test | repeatedly inspected during structured architecture work |
| 2100–2499 | consumed V1 final holdout | V1 formal confirmation; never call untouched again |
| 3000–3399 | consumed V2 development | may guide V2 architecture decisions |
| 4000–4399 | consumed hybrid-executor development | used to study executor swap |
| 5000–5399 | **ACTIVE hybrid-objective development** | may guide current architecture |
| 6000–6399 | reserved V2 confirmation | untouched; do not use unless V2 architecture is explicitly frozen |
| 7000–7399 | reserved hybrid-executor confirmation | untouched; likely obsolete unless that architecture is revived/frozen |
| 8000–8399 | **reserved hybrid-objective confirmation** | untouched; do not run until current architecture is frozen |

Rules:

1. Never tune after inspecting a confirmation block and still call it confirmation.
2. Never reuse a consumed block as "new" evidence.
3. When architecture changes materially, prefer a fresh development block and reserve a fresh confirmation block.
4. Record seed ranges in every report and protocol artifact.
5. If the simulator/scoring semantics change, treat old evidence as belonging to the old simulator version.

---

# 10. Statistics and evidence policy

Primary evaluation should account for both:

- scenario uncertainty;
- training/search-seed uncertainty.

Current formal tooling includes hierarchical bootstrap confidence intervals and paired sign-flip tests.

Do not announce significance from one p-value when the effect-size CI still materially crosses zero without explaining the estimand difference.

Preferred publication-grade approach:

1. define the primary estimand before confirmation;
2. use a hierarchical paired procedure that treats independently trained policies as a first-level source of variation and scenarios as a second level;
3. report point estimate, 95% CI, and a compatible hypothesis test;
4. report absolute survival difference in percentage points;
5. also report containment, penetration, damage, resources, response delay, and runtime;
6. report per-training-run effects, not just pooled averages;
7. consider more than five training seeds if run-to-run variance remains the dominant uncertainty.

A positive point estimate alone is not proof.

Preferred criterion before spending a fresh confirmation set:

- architecture/hyperparameters frozen;
- development effect is operationally meaningful, not merely detectable;
- ideally the hierarchical 95% CI lower bound is above zero, or there is otherwise a strong pre-specified reason to confirm;
- no unresolved correctness bugs;
- quick/integration and full development artifacts are reproducible.

---

# 11. Current active architecture and files

The active branch is `agent/hybrid-objective-learning`.

Important files:

- `aegisswarm/models.py` — scenario entities;
- `aegisswarm/scenarios.py` — seeded synthetic scenario generation;
- `aegisswarm/simulator.py` — simulation loop;
- `aegisswarm/policies.py` — heuristic baselines;
- `aegisswarm/optimization.py` — current fixed Hungarian baseline;
- `aegisswarm/rule_program.py` — 12-rule/60-token strategy language;
- `aegisswarm/rule_search.py` — structured program evaluation/search utilities;
- `aegisswarm/axplorer_v2.py` — fitness-conditioned grammar-aware learned proposer;
- `aegisswarm/hybrid.py` — `RuleGuidedHungarianPolicy`; strategy-derived utility + exact assignment;
- `aegisswarm/hybrid_search.py` — hybrid program scoring;
- `aegisswarm/hybrid_ablation.py` / `hybrid_cli.py` — fixed-strategy executor ablation;
- `aegisswarm/hybrid_objective.py` — optimizer-aware local/Axplorer training;
- `aegisswarm/hybrid_objective_proof.py` — active protocol/evaluation/reporting;
- `aegisswarm/hybrid_objective_cli.py` — active experiment CLI;
- `aegisswarm/splits.py` — canonical seed/evidence blocks;
- `aegisswarm/final_proof.py` — V1 statistical/reporting utilities and legacy formal protocol;
- `tests/` — regression/integration tests.

Current draft PR:

- PR #2: `Train learned strategies through optimized execution`
- head: `agent/hybrid-objective-learning`
- base: `agent/hybrid-aegis`

The branch ancestry intentionally preserves the experiment progression. Do not blindly squash/merge old experimental branches without deciding how the final history should be represented.

---

# 12. Known implementation lessons / bugs already encountered

Do not rediscover these if avoidable.

## Multiprocessing worker-name shadowing

`final_proof.py` historically defined two helpers with the same `_evaluate_program_worker` name: one accepted `(tokens, config)`, another accepted one packed evaluation payload. Python kept the later definition, causing spawn/process-pool calls to fail with:

```text
TypeError: _evaluate_program_worker() takes 1 positional argument but 2 were given
```

Subsequent branches added explicit spawn-safe dispatch/worker handling and regression tests. When adding new process-pool code, use unambiguous top-level worker functions with picklable payloads.

## Diversity archive metric mismatch

Axplorer V2 initially ranked archive niches by `penetrations`, while the training evaluator cache omitted that metric, causing:

```text
KeyError: 'penetrations'
```

The evaluator was expanded to expose penetrations without changing the scalar fitness objective. Keep archive requirements and evaluator metric schemas synchronized.

## macOS / Apple Silicon

The primary development environment is Apple Silicon, with PyTorch MPS used for transformer training and CPU process pools used for simulator candidate scoring. Always exercise spawn multiprocessing in tests; fork-only assumptions are unsafe on macOS.

---

# 13. What the active hybrid-objective experiment is trying to learn

The previous hybrid ablation showed that an optimizer does not automatically improve a strategy that was trained for another executor.

The active architecture instead evaluates:

```text
candidate rule program
        |
        v
strategic pair utility + reserve intent
        |
        v
Hungarian assignment optimizer
        |
        v
simulated outcome
        |
        v
fitness returned to search
```

This turns the strategy learner into an **objective designer** for a constrained optimizer.

Mathematically, the conceptual form is:

```text
theta -> U_theta(state, defender, threat)
      -> argmax_x sum U_theta * x
      -> outcome -> fitness(theta)
```

where `theta` is the rule program and `x` is a feasible assignment.

This is a much stronger division of labor than asking a transformer to imitate combinatorial optimization.

---

# 14. Immediate runbook

## Current next command — full development

After quick mode passes, run:

```bash
python -m aegisswarm.hybrid_objective_cli \
  --workers 6 \
  --device mps
```

Expected development block:

- 5 matched search seeds;
- 16 training scenarios;
- 1,800 unique candidate evaluations per method/run;
- 400 evaluation scenarios, seeds 5000–5399.

Output should include:

```text
=== HYBRID OBJECTIVE LEARNING ===
fixed_optimizer survival: ...
hybrid_local survival:    ...
hybrid_axplorer survival: ...
difference (A-L):         ...
paired p-value:           ...
```

Artifacts default to:

```text
artifacts/hybrid_objective_dev/
```

## Do not run yet

```bash
python -m aegisswarm.hybrid_objective_cli --confirm ...
```

Confirmation seeds 8000–8399 must remain untouched until an explicit architecture-freeze decision.

---

# 15. Decision tree after active full development

## Case A — hybrid Axplorer clearly and meaningfully beats hybrid local

Example desirable pattern:

- positive effect of several percentage points;
- hierarchical CI substantially above zero;
- effect visible across training seeds;
- no severe resource/runtime tradeoff;
- no correctness concerns.

Then:

1. freeze architecture and hyperparameters;
2. record commit SHA/protocol ID;
3. run `8000–8399` confirmation exactly once;
4. do not tune on the confirmation result;
5. if confirmed, move to stronger external baselines and robustness work.

## Case B — hybrid Axplorer and hybrid local are tied

Do **not** burn confirmation.

Use 5000–5399 as development evidence to diagnose:

- model collapse/diversity;
- insufficient training-seed count;
- rule-language bottlenecks;
- objective parameterization;
- whether local refinement is doing nearly all useful work;
- whether transformer compute is justified by marginal gain.

A future architecture change should get a new protocol ID and, if material, a new development/confirmation block.

## Case C — hybrid local clearly wins

Treat that as useful evidence. Do not preserve Axplorer for branding reasons.

Possible conclusions:

- learned generative proposal is not buying enough search efficiency;
- local/evolutionary search may be the correct offline strategy learner;
- use ML elsewhere (state representation, uncertainty prediction, behavior forecasting, adaptation) rather than forcing it into strategy generation.

The end goal is the best system, not proving a favored algorithm.

---

# 16. Next architecture stages after hybrid-objective learning

Do not implement all of these at once. Advance one hypothesis at a time with ablations.

## Stage 1 — stronger optimizer

The current Hungarian solver is myopic. A likely next step is a short rolling-horizon optimizer / MPC-style planner that anticipates future state/resource scarcity.

Goal: test whether strategic learning adds more value when paired with an optimizer capable of temporal planning.

## Stage 2 — richer strategic parameterization

The current rule language may be expanded or replaced by a more optimizer-native objective representation, e.g. abstract weights for:

- threat urgency;
- asset value/risk;
- fast/direct threat premiums;
- decoy discount;
- distance cost;
- resource scarcity;
- reserve policy;
- assignment persistence;
- uncertainty/risk aversion;
- tail-risk penalty.

Keep it abstract and defensive.

## Stage 3 — stronger sequential learning baseline

Add stronger RL/MARL only when the environment supports a meaningful sequential-learning question. Potential families include PPO/MAPPO-style baselines, but the experiment must be compute/budget conscious and correctly specified.

Do not add RL merely to claim it was beaten.

## Stage 4 — uncertainty and partial observation

Improve sensing uncertainty, track confidence, degraded sensors, and state estimation. Evaluate robustness to observation noise and distribution shift.

## Stage 5 — simulator v2 / random tapes

Introduce event-indexed random tapes or repeated stochastic replications so policy comparisons get cleaner common-random-number coupling.

This should be a new simulator/protocol version, not a silent patch to an active final experiment.

## Stage 6 — richer abstract swarm behavior

Potential behavior families:

- direct attack;
- clustered waves;
- split/multi-axis approach;
- decoy screening;
- retargeting;
- stochastic maneuver;
- changing composition;
- sensor degradation;
- resource-poor scenarios.

Keep these abstract, not operationally prescriptive.

## Stage 7 — tail-risk and mission-level metrics

Add metrics such as:

- protected-value survival;
- leakage fraction;
- resource per contained threat;
- worst-decile performance;
- CVaR / tail damage;
- robustness across scenario families;
- runtime/scaling.

---

# 17. External deadline and submission context

## iDEX Open Challenge — primary external deadline

**Verified from the official iDEX website on 2026-08-17:**

- Open Challenge page currently indicates the challenge is open;
- deadline: **30 September 2026, 11:59 PM**;
- grant support: **up to ₹1.5 crore**;
- eligible applicant categories include recognized startups, Indian MSMEs/companies, and individual innovators; research/academic institutions may use the individual-innovator route according to the official FAQ.

Official sources to re-check before relying on this section:

- `https://www.idex.gov.in/disc-category/18`
- `https://idex.gov.in/faq`

**Never trust this deadline indefinitely. Re-verify the official page when doing submission work.**

The Open Challenge is particularly relevant because it permits innovators to propose their own defence/aerospace problem/solution rather than requiring a currently listed problem statement.

## Recommended internal working gates toward 30 September 2026

These are project management targets, not official deadlines. Adjust if experiments invalidate the architecture.

### By ~24 August

- finish hybrid-objective full development;
- make explicit freeze / no-freeze decision;
- if no-freeze, choose exactly one next architecture hypothesis rather than proliferating models.

### By ~31 August

- have one strongest reproducible architecture candidate;
- complete core ablations;
- resolve the primary statistical estimand/reporting mismatch;
- decide whether an untouched confirmation run is justified.

### By ~7 September

- complete the strongest available confirmation/evidence package if architecture is frozen;
- compile stress results and failure modes;
- identify stronger baseline gaps that must be disclosed or filled.

### By ~14 September

- freeze the technical story for the iDEX application;
- prepare system architecture, novelty, validation methodology, TRL/prototype status, milestones, funding use, risks, and integration concept;
- avoid inventing deployment readiness that the simulator does not establish.

### By ~21 September

- draft complete iDEX technical/financial proposal package;
- perform evidence and claim audit;
- ensure every performance claim maps to a reproducible artifact/protocol.

### By ~27 September

- final review and submission buffer;
- re-check official portal requirements/deadline;
- avoid waiting until 30 September for first upload/submission attempt.

### 30 September 2026, 11:59 PM

- current official iDEX Open Challenge deadline as verified 2026-08-17.

---

# 18. iDEX positioning — only after evidence

Potential eventual positioning:

> AegisSwarm is a simulation-first AI decision-support and coordination layer for heterogeneous counter-swarm defence, combining learned strategic objective design with constrained resource optimization and explicit safety/override logic.

Do not position it as a deployable autonomous weapon system.

What an iDEX evidence package should eventually contain:

- clearly defined operational coordination problem;
- architecture diagram;
- simulator/prototype demonstration;
- algorithmic novelty;
- fair baselines;
- held-out evidence with uncertainty;
- stress/failure analysis;
- runtime/scalability;
- human-supervision/override concept;
- data/integration interfaces at an abstract level;
- development milestones and requested funding;
- honest limitations and validation plan.

The strongest pitch is not "we used a transformer." It is:

> **We built a disciplined hybrid decision architecture and can quantitatively show what each layer contributes under controlled disruption/stress scenarios.**

---

# 19. Claims policy

## Claims currently supported inside the synthetic simulator

Reasonable:

- structured rule policies were substantially stronger than the original 8-gene representation in development experiments;
- structured search policies materially outperform the current simple heuristic, tabular-Q, and myopic fixed-objective baselines in this synthetic environment;
- V1 Axplorer did not robustly beat structured local search on the untouched V1 holdout;
- V2 produced a small positive development effect but with material training-run uncertainty;
- merely swapping a Hungarian executor underneath strategies trained for greedy execution did not improve performance;
- this motivated optimizer-aware strategy learning.

## Claims not currently supported

Do not say:

- "AegisSwarm is proven superior to state-of-the-art counter-swarm systems";
- "AegisSwarm beats reinforcement learning";
- "AegisSwarm beats optimization";
- "Axplorer is statistically proven superior" based on current V1/V2 evidence;
- "ready for deployment";
- "validated on real military data";
- "87.5% final performance" — that number came from a development evaluation;
- any real-world effectiveness percentage inferred from synthetic survival rates.

---

# 20. Development philosophy

When deciding what to do next, follow these rules:

1. **Performance first, narrative second.** Do not optimize customer/investor positioning before technical evidence.
2. **One hypothesis at a time.** Avoid changing representation, optimizer, simulator, score, and model simultaneously.
3. **Keep a strong comparator.** Local/evolutionary search is not the enemy; if it is best, use it.
4. **Exploit complementarity.** If optimization solves a subproblem exactly, use it rather than asking a transformer to relearn it.
5. **Measure marginal contribution.** Every major component should survive an ablation.
6. **Protect holdouts.** Fresh evidence is scarce; do not casually spend it.
7. **Do not hide negative results.** V1 parity and no-gain hybrid executor swap are valuable architecture evidence.
8. **Prefer reproducibility over impressive one-off numbers.** Multiple training seeds and fixed protocols matter.
9. **Record architecture changes caused by inspected development results.** This preserves scientific honesty.
10. **The final system can be hybrid even if no individual learned component beats every classical baseline.**

---

# 21. Suggested workflow for any LLM picking up the repository

Before modifying code:

1. Read this file.
2. Read root `AGENTS.md`.
3. Inspect `aegisswarm/splits.py` before touching any evaluation command.
4. Identify the active branch and protocol.
5. Inspect the most recent `artifacts/*/REPORT.md` if available locally.
6. Determine whether the user is asking for:
   - bug fixing;
   - development experimentation;
   - confirmation/final evidence;
   - architecture design;
   - submission/positioning.
7. If confirmation is requested, verify architecture-freeze status first.
8. If a result is pasted, classify it as training, quick/integration, development, or untouched confirmation before interpreting it.
9. Preserve existing evidence; do not rewrite seed status to make results look stronger.
10. Update this handoff when a major experiment completes or the active hypothesis changes.

When modifying code:

- prefer full, coherent implementation over scattered patches;
- add regression tests for bugs that reached the user;
- keep multiprocessing spawn-safe on macOS;
- retain resumable artifacts for expensive search runs;
- make protocol settings explicit in generated JSON/report files;
- never silently change fitness/scenario semantics inside a running formal protocol.

---

# 22. Repository / branch chronology

Major research branches currently include:

- `agent/structured-rule-program` — structured 12-rule programs, V1 formal proof machinery;
- `agent/axplorer-v2` — fitness-conditioned/grammar-aware Axplorer V2;
- `agent/hybrid-aegis` — fixed discovered strategy + optimized execution ablation;
- `agent/hybrid-objective-learning` — **current active branch**, optimizer-aware strategy search.

Current draft PR:

- PR #2, `Train learned strategies through optimized execution`.

The architecture remains explicitly **unfrozen**.

---

# 23. Project separation

Do not conflate AegisSwarm with other projects that may exist in the same user's work history.

In particular:

- **Ripple** is a separate airline disruption-recovery/optimization project.
- MISR / rectangle-integrality-gap work is separate combinatorial-optimization research.

AegisSwarm's current external submission target is iDEX/Open Challenge; aviation/OpenSky deadlines belong to Ripple/aviation research unless explicitly connected by the user.

---

# 24. Current status in one paragraph

As of **2026-08-17**, AegisSwarm has a functioning synthetic counter-swarm simulator, heuristic/optimization/RL baselines, a structured 12-rule policy language, local/evolutionary search, two generations of an Axplorer-style learned proposer, formal held-out statistics, stress testing, and hybrid optimizer execution. The strongest rigorous lesson so far is not that one framework universally wins: structured strategy search is strong, V1 Axplorer was statistically indistinguishable from local search on its untouched holdout, V2 showed only a small uncertain development gain, and simply swapping an optimizer under greedily trained strategies did not help. The project has therefore pivoted to **optimizer-aware objective learning**, where every candidate strategy is scored through the optimizer during training. A tiny quick run succeeded but is not evidence. The next meaningful result is the full 5-run, 1,800-evaluation-per-method development campaign on seeds **5000–5399**. Architecture is **not frozen**, and confirmation seeds **8000–8399 must remain untouched** until a deliberate freeze decision. The primary external target currently tracked is the iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, verified on the official site on 2026-08-17.
