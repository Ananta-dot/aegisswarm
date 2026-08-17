TRAIN_SEEDS = tuple(range(0, 256))
VALIDATION_SEEDS = tuple(range(1000, 1100))

# Seeds 2000-2099 have already been inspected during architecture iteration.
# They are development-test seeds only and must not be treated as final evidence.
DEV_TEST_SEEDS = tuple(range(2000, 2100))
TEST_SEEDS = DEV_TEST_SEEDS  # backward-compatible name used by existing CLIs

# Frozen V1 formal holdout. This block has now been consumed by the V1 proof and
# must never be reused as unseen evidence for algorithm changes.
FINAL_HOLDOUT_SEEDS = tuple(range(2100, 2500))

# Axplorer V2 architecture-development block.
V2_DEV_SEEDS = tuple(range(3000, 3400))

# Reserved V2 confirmation block. Do not inspect until V2 is frozen.
V2_CONFIRM_SEEDS = tuple(range(6000, 6400))

# Hybrid execution-ablation development block.
HYBRID_DEV_SEEDS = tuple(range(4000, 4400))

# Reserved hybrid execution confirmation block.
HYBRID_CONFIRM_SEEDS = tuple(range(7000, 7400))

# Hybrid objective-learning development block. This block has been consumed by
# the optimizer-aware rule-objective development experiment.
HYBRID_OBJECTIVE_DEV_SEEDS = tuple(range(5000, 5400))

# Reserved confirmation for the hybrid rule-objective architecture. Keep
# untouched unless that exact architecture is deliberately revived and frozen.
HYBRID_OBJECTIVE_CONFIRM_SEEDS = tuple(range(8000, 8400))

# Optimizer-native V1 representation development. This block is fully consumed:
# V1 quick and then a full 5-run campaign were inspected before the malformed
# zero-centred utility was replaced. Never describe this block as unseen again.
NATIVE_OBJECTIVE_DEV_SEEDS = tuple(range(9000, 9400))

# Previously reserved for the invalidated V1 representation. It remains
# untouched, but do not silently repurpose it as V2 confirmation because the V2
# architecture was designed after inspecting the V1 development result.
NATIVE_OBJECTIVE_CONFIRM_SEEDS = tuple(range(10000, 10400))

# Fresh optimizer-native V2 development block. V2 shares the rule-guided
# structural base utility and searches smooth state-reactive modifiers.
NATIVE_OBJECTIVE_V2_DEV_SEEDS = tuple(range(11000, 11400))

# Reserved confirmation for optimizer-native V2. Keep untouched until the V2
# representation, hyperparameters, primary estimand and code are explicitly frozen.
NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS = tuple(range(12000, 12400))

SPLITS = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "test": TEST_SEEDS,
}
