# AegisSwarm coding-agent instructions

Read before changes:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/RELIABILITY_AWARE.md`
5. `/EVIDENCE_HARDENING.md`
6. `/ROLLING_HORIZON.md` for completed planner history

Architecture is not frozen for external claims. `AEGISSWARM_STATUS.md` is the current-state overlay.

Active branch/protocol:

```text
agent/reliability-aware-assignment
aegisswarm-reliability-aware-screen-v1
```

Incumbent entering this screen:

```text
60-token state-reactive rules
+ optimizer-aware local/evolutionary search
+ one-step RuleGuidedHungarianPolicy
```

Completed SimulatorV2 headroom development on `17000–17399` found:

```text
normal incumbent:           0.801
perfect sensing:            0.801
interaction deterministic:  0.999
best-of-5 oracle:            0.938
interaction headroom:      +0.1980 CI=[0.166,0.23625]
```

This motivates reliability-aware allocation. Deterministic success is only a diagnostic relaxation, not a deployable assumption.

The active screen compares frozen programs under:

- incumbent one-to-one Hungarian;
- reliability-weighted one-to-one Hungarian;
- reliability-aware contingent backup allocation with at most two defenders per threat.

Fresh blocks:

- `19000–19399`: development
- `20000–20399`: reserved confirmation; do not inspect

Do not repurpose `18000–18399`; it belongs to the completed evidence-hardening protocol.

Do not reopen optimizer-native or rolling-horizon V3 by default. Do not change simulator/scoring/protocol semantics mid-screen. Keep work abstract, synthetic, defensive, and decision-support oriented.
