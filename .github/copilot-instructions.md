# AegisSwarm coding-agent instructions

Read first:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/STOCHASTIC_ROBUST.md`
5. `/EVIDENCE_HARDENING.md`
6. `/RELIABILITY_AWARE.md`
7. `/ROLLING_HORIZON.md`

Current incumbent:

```text
60-token state-reactive rules
+ optimizer-aware local/evolutionary search
+ one-step RuleGuidedHungarianPolicy
```

Completed Simulator V2 headroom development found essentially zero perfect-sensing headroom but large deterministic-interaction diagnostic headroom (`+19.8` pp, CI entirely positive).

The completed reliability-aware executor screen found:

```text
incumbent:             0.809
weighted:              0.810
contingent backup:     0.825
weighted-incumbent:   +0.0003 CI=[-0.0165,+0.01775]
backup-incumbent:     +0.0155 CI=[-0.00625,+0.03575625]
```

Do not treat backup as the incumbent and do not consume `20000–20399` confirmation.

Active branch/protocol:

```text
agent/stochastic-robust-training
aegisswarm-stochastic-robust-training-v1
```

V1 trains the same 60-token representation with conventional local/evolutionary search over multiple matched Simulator V2 random tapes per structural scenario. It keeps the established scalar fitness and compares training through incumbent vs contingent-backup execution under matched budgets. Do not add CVaR/risk weights, Axplorer, new rule tokens, a planning horizon, or sensing changes during V1.

Fresh blocks:

- `21000–21031`: training structural worlds;
- `22000–22399`: development evaluation;
- `23000–23399`: reserved confirmation — do not inspect.

Run quick first. Do not run full until quick output is inspected.

Legacy `Simulator` and `SimulatorV2` are separate protocol generations. Never silently mix them in a claim.
