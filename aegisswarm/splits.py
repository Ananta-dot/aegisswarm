TRAIN_SEEDS = tuple(range(0, 256))
VALIDATION_SEEDS = tuple(range(1000, 1100))

# Seeds 2000-2099 have already been inspected during architecture iteration.
DEV_TEST_SEEDS = tuple(range(2000, 2100))
TEST_SEEDS = DEV_TEST_SEEDS

FINAL_HOLDOUT_SEEDS = tuple(range(2100, 2500))
V2_DEV_SEEDS = tuple(range(3000, 3400))
V2_CONFIRM_SEEDS = tuple(range(6000, 6400))
HYBRID_DEV_SEEDS = tuple(range(4000, 4400))
HYBRID_CONFIRM_SEEDS = tuple(range(7000, 7400))
HYBRID_OBJECTIVE_DEV_SEEDS = tuple(range(5000, 5400))
HYBRID_OBJECTIVE_CONFIRM_SEEDS = tuple(range(8000, 8400))
NATIVE_OBJECTIVE_DEV_SEEDS = tuple(range(9000, 9400))
NATIVE_OBJECTIVE_CONFIRM_SEEDS = tuple(range(10000, 10400))
NATIVE_OBJECTIVE_V2_DEV_SEEDS = tuple(range(11000, 11400))
NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS = tuple(range(12000, 12400))
PLANNING_DEV_SEEDS = tuple(range(13000, 13400))
PLANNING_CONFIRM_SEEDS = tuple(range(14000, 14400))
PLANNING_V2_DEV_SEEDS = tuple(range(15000, 15400))
PLANNING_V2_CONFIRM_SEEDS = tuple(range(16000, 16400))
EVIDENCE_DEV_SEEDS = tuple(range(17000, 17400))
EVIDENCE_CONFIRM_SEEDS = tuple(range(18000, 18400))
RELIABILITY_DEV_SEEDS = tuple(range(19000, 19400))
RELIABILITY_CONFIRM_SEEDS = tuple(range(20000, 20400))

# Stochastic-robust V1. Quick inspection consumed training worlds 21000-21003
# and evaluation scenarios 22000-22019. The V1 architecture is closed after
# the quick screen; do not silently reuse the remainder of these blocks as
# unseen evidence for a changed protocol.
ROBUST_TRAIN_WORLD_SEEDS = tuple(range(21000, 21032))
ROBUST_DEV_SEEDS = tuple(range(22000, 22400))
ROBUST_CONFIRM_SEEDS = tuple(range(23000, 23400))

# Stochastic-training ablation V2. This cleanly isolates repeated random-tape
# training from single-tape SimulatorV2 training while holding the executor,
# representation, search family, structural worlds, search seeds and candidate
# budget fixed.
STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS = tuple(range(24000, 24032))
STOCHASTIC_ABLATION_DEV_SEEDS = tuple(range(25000, 25400))
STOCHASTIC_ABLATION_CONFIRM_SEEDS = tuple(range(26000, 26400))

SPLITS = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "test": TEST_SEEDS,
}
