# AegisSwarm coding-agent instructions

Before making changes, read in this order:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/EVIDENCE_HARDENING.md`
5. `/ROLLING_HORIZON.md` for completed planner history

The architecture is **not frozen for external claims**. `AEGISSWARM_STATUS.md` is the latest-state overlay and supersedes older current-status wording when they differ.

Active branch/protocol:

```text
agent/evidence-hardening
aegisswarm-evidence-hardening-v1
```

Current incumbent:

```text
60-token state-reactive rules
+ optimizer-aware local/evolutionary search
+ one-step RuleGuidedHungarianPolicy
```

Do not reopen optimizer-native V3 or rolling-horizon V3 by default. Those tracks were closed by controlled development evidence.

The active phase introduces an opt-in `SimulatorV2` with policy-independent indexed random draws and a frozen-program headroom suite. Legacy `Simulator` remains untouched. Never silently mix simulator generations in one claim.

Evidence blocks:

- `17000–17399`: development
- `18000–18399`: reserved evidence/confirmation; do not inspect during development

Diagnostic perfect-sensing, deterministic-interaction, combined, and best-of-5 oracle results are **development headroom probes**, not deployable assumptions or mathematical upper bounds.

Do not change protocol semantics or make broad superiority claims without following the handoff documents.
