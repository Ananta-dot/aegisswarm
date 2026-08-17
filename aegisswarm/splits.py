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

# Hybrid objective-learning development block. Here every searched candidate is
# executed through the optimizer during training.
HYBRID_OBJECTIVE_DEV_SEEDS = tuple(range(5000, 5400))

# Reserved confirmation for the optimizer-aware learned-objective architecture.
# Do not inspect until the architecture/hyperparameters are explicitly frozen.
HYBRID_OBJECTIVE_CONFIRM_SEEDS = tuple(range(8000, 8400))

SPLITS = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "test": TEST_SEEDS,
}
