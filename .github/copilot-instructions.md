# AegisSwarm coding-agent instructions

Read first:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/EVIDENCE_HARDENING.md`
5. `/RELIABILITY_AWARE.md`
6. `/ROLLING_HORIZON.md` for completed planner history

Current incumbent:

```text
60-token state-reactive rules
+ optimizer-aware local/evolutionary search
+ one-step RuleGuidedHungarianPolicy
```

Completed Simulator V2 headroom development found essentially zero perfect-sensing headroom but large deterministic-interaction diagnostic headroom (`+19.8` pp, CI entirely positive).

The reliability-aware executor screen is also complete:

```text
incumbent:             0.809
weighted:              0.810
contingent backup:     0.825
weighted-incumbent:   +0.0003 CI=[-0.0165,+0.01775]
backup-incumbent:     +0.0155 CI=[-0.00625,+0.03575625]
```

Do not treat backup as the incumbent and do not consume `20000–20399` confirmation. Weighting-only is a null result; backup is only a weak positive.

Next direction: stochastic-robust 60-token strategy training under Simulator V2 with multiple matched random tapes per structural scenario. The first version should retain the existing scalar fitness averaged over replications; do not introduce CVaR/risk weights yet. Compare incumbent-executor and backup-executor training under matched search budgets. Do not reopen Axplorer, optimizer-native V3, rolling-horizon V3, or sensing work by default.

Legacy `Simulator` and `SimulatorV2` are separate protocol generations. Never silently mix them in a claim.
