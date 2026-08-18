# AegisSwarm Frozen PPO Generalization Extension

Protocol: `aegisswarm-hierarchical-ppo-v1-frozen-extension`

## Why this extension exists

The first hierarchical PPO quick screen used two independently trained models (`42101`, `42102`), 100,000 environment steps/model and fresh evaluation scenarios `33000–33019`.

Observed quick result:

```text
incumbent survival:          0.800
static-best survival:        0.800
PPO adaptive survival:       0.800
PPO - incumbent:            +0.0000 CI=[-0.075,+0.075]
PPO per-run survival delta:  [0.0,0.0]
```

The two PPO models nevertheless used materially different tactical-mode mixtures, so the 20-scenario survival tie does not establish that the learned controllers are behaviorally identical. Secondary metrics also differed slightly.

Before spending substantially more compute on longer PPO training, V1 performs a frozen-model generalization extension.

## Frozen design

Nothing is retrained or tuned.

- same frozen base program index `1`;
- exact saved quick PPO models `ppo_seed_42101.zip` and `ppo_seed_42102.zip`;
- same six tactical modes;
- same observation boundary;
- same reward;
- same deterministic evaluation action selection;
- same training-selected static comparator.

Only the evaluation sample is enlarged.

## Fresh extension scenarios

```text
33020–33119  100 additional PPO-development scenarios
```

These are disjoint from the quick evaluation scenarios `33000–33019`.

The rest of `33000–33399` remains development evidence. `34000–34399` remains reserved confirmation and must not be inspected.

## Added reporting

The extension reports:

- survival for incumbent / training-selected static mode / PPO;
- established row-wise scalar reward for all three;
- hierarchical PPO survival and reward deltas across the two training seeds;
- per-training-run survival and reward deltas;
- interaction attempts and failures;
- aggregate interaction-failure rate;
- resource-exhaustion rate;
- overload steps and remaining resources;
- PPO tactical-mode proportions.

The established reward is exactly the existing project score computed per completed episode. No new objective is introduced.

## Run

After the original quick PPO models exist locally:

```bash
pytest -q
python -m aegisswarm.adaptive_rl_frozen_cli
```

No PPO training occurs in this command.

## Decision gate

### Frozen PPO improves both survival/reward or shows a consistent positive reward signal

PPO online adaptation remains a credible architecture. Do not automatically run the old `--full`; define a fresh longer-training V2 evaluation protocol so model-budget changes are not justified and scored on the same inspected evidence.

### Frozen PPO remains essentially tied with incumbent

Close hierarchical PPO V1 at this tactical-mode resolution. More timesteps alone are not justified.

### Frozen PPO is worse

Close V1. If RL is revisited, change the learning abstraction rather than merely increasing the PPO training budget.
