TRAIN_SEEDS = tuple(range(0, 256))
VALIDATION_SEEDS = tuple(range(1000, 1100))

# Seeds 2000-2099 have already been inspected during architecture iteration.
# They are development-test seeds only and must not be treated as final evidence.
DEV_TEST_SEEDS = tuple(range(2000, 2100))
TEST_SEEDS = DEV_TEST_SEEDS  # backward-compatible name used by existing CLIs

# Frozen formal holdout. Do not use these seeds for tuning or architecture changes.
FINAL_HOLDOUT_SEEDS = tuple(range(2100, 2500))

SPLITS = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "test": TEST_SEEDS,
}
