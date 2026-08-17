# AegisSwarm coding-agent instructions

Before making changes, read in this order:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/OPTIMIZER_NATIVE_OBJECTIVE.md`

The architecture is **not frozen**. The active branch is `agent/optimizer-native-objective` and the active protocol is `aegisswarm-optimizer-native-objective-v2`.

Optimizer-native V1 is rejected. Its full development campaign on `9000–9399` produced 35.9% survival versus 78.7% for the retrained rule-objective comparator, and inspection confirmed malformed zero-centred/no-op utility semantics plus severe generalization failure. Do not rerun/tune V1 and do not treat `9000–9399` as fresh.

V2 shares the rule-guided structural base utility and searches smooth state-reactive modifiers. Because V2 was designed after inspecting V1, it uses fresh evidence blocks:

- development: `11000–11399`
- reserved confirmation: `12000–12399`

The old `10000–10399` block remains untouched but belongs to the abandoned V1 plan; do not silently repurpose it.

Expected V2 output contains `optimizer-native-v2`, `native-v2-local`, and `optimizer_native_v2_*`. If output still says `native-local` or `optimizer_native_dev`, the checkout is stale.

Do not consume confirmation, change protocol semantics mid-run, or make broad superiority claims without following the handoff/status documents.
