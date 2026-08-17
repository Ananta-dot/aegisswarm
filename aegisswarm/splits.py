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
V2_CONFIRM_SEEDS = tuple(range(6000, 6400))

# Hybrid executor development / reserved confirmation.
HYBRID_DEV_SEEDS = tuple(range(4000, 4400))
HYBRID_CONFIRM_SEEDS = tuple(range(7000, 7400))

# Hybrid objective-learning development / reserved confirmation.
HYBRID_OBJECTIVE_DEV_SEEDS = tuple(range(5000, 5400))
HYBRID_OBJECTIVE_CONFIRM_SEEDS = tuple(range(8000, 8400))

# Optimizer-native V1: development fully consumed; old confirmation untouched but
# belongs to the abandoned V1 evidence plan.
NATIVE_OBJECTIVE_DEV_SEEDS = tuple(range(9000, 9400))
NATIVE_OBJECTIVE_CONFIRM_SEEDS = tuple(range(10000, 10400))

# Optimizer-native V2: development fully consumed; confirmation remains untouched
# and must not be spent because V2 did not earn a freeze.
NATIVE_OBJECTIVE_V2_DEV_SEEDS = tuple(range(11000, 11400))
NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS = tuple(range(12000, 12400))

# Rolling-horizon planning development. This block may be inspected/tuned during
# planning architecture development and must never later be called untouched.
PLANNING_DEV_SEEDS = tuple(range(13000, 13400))

# Reserved confirmation for a future frozen rolling-horizon architecture. Do not
# inspect until the planning horizon, planner semantics, rule representation,
# training protocol and primary estimand are frozen.
PLANNING_CONFIRM_SEEDS = tuple(range(14000, 14400))

SPLITS = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "test": TEST_SEEDS,
}
