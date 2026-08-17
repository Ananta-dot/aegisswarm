# AegisSwarm coding-agent instructions

Before making changes, read in this order:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/OPTIMIZER_NATIVE_OBJECTIVE.md`

The architecture is **not frozen**. The active branch is `agent/optimizer-native-objective` and the active protocol is `aegisswarm-optimizer-native-objective-v2`.

The first optimizer-native quick experiment (V1) was invalidated before full development because its zero-centred utility was not semantically comparable to the rule-guided policy and frequently preferred no-op assignments. Do not use that quick result as evidence against optimizer-native objectives generally.

V2 shares the rule-guided structural base utility and searches smooth state-reactive modifiers. Development is `9000–9399`; reserved confirmation `10000–10399` remains untouched and must not be consumed without an explicit freeze decision.

Do not change protocol semantics mid-run or make broad superiority claims without following the handoff/status documents.
