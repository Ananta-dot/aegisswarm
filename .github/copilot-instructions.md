# AegisSwarm coding-agent instructions

Before making changes, read in this order:

1. `/AGENTS.md`
2. `/docs/AEGISSWARM_SKILL.md`
3. `/docs/AEGISSWARM_STATUS.md`
4. `/ROLLING_HORIZON.md`

The architecture is **not frozen**. `AEGISSWARM_STATUS.md` is the latest-state overlay and supersedes older current-status wording when they differ.

Current planning state: rolling-horizon V1 completed a 400-scenario development screen with a -3.0 pp survival point estimate and substantially higher runtime. Code inspection found a receding-horizon action-deferral pathology. Planner V2 makes one targeted correction and must be evaluated on fresh development seeds `15000–15399` before any planner-aware retraining is considered.

Do not consume `16000–16399` confirmation, do not repurpose older reserved blocks, and do not launch planner-aware 1,800-candidate training merely because a quick screen looks positive.

Do not change protocol semantics or make broad superiority claims without following the handoff documents.
