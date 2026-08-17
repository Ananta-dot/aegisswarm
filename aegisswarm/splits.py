TRAIN_SEEDS = tuple(range(0, 256))
VALIDATION_SEEDS = tuple(range(1000, 1100))

# Seeds 2000-2099 have already been inspected during architecture iteration.
# They are development-test seeds only and must not be treated as final evidence.
DEV_TEST_SEEDS = tuple(range(2000, 2100))
TEST_SEEDS = DEV_TEST_SEEDS  # backward-compatible name used by existing CLIs

# Frozen V1 formal holdout. This block has now been consumed by the V1 proof and
# must never be reused as unseen evidence for algorithm changes.
FINAL_HOLDOUT_SEEDS = tuple(range(2100, 2500))

# Axplorer V2 architecture-development block. It is intentionally separate from
# every V1 evaluation block. Results here may guide V2 development.
V2_DEV_SEEDS = tuple(range(3000, 3400))

# Hybrid-architecture development block. This is separate from V2 development so
# executor/optimizer changes can be diagnosed without reusing the V2 dev set.
HYBRID_DEV_SEEDS = tuple(range(4000, 4400))

# Reserved V2 confirmation block. Do not inspect or evaluate these seeds until
# the V2 architecture and hyperparameters have been frozen after development.
V2_CONFIRM_SEEDS = tuple(range(6000, 6400))

# Reserved confirmation block for the eventual hybrid architecture. Do not use
# this block during hybrid architecture or hyperparameter development.
HYBRID_CONFIRM_SEEDS = tuple(range(7000, 7400))

SPLITS = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "test": TEST_SEEDS,
}
