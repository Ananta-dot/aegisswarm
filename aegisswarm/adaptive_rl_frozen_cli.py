from __future__ import annotations

import argparse

from .adaptive_rl_frozen import run_frozen_ppo_generalization


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate frozen quick PPO models on additional development scenarios"
    )
    parser.add_argument(
        "--source-dir",
        default="artifacts/optimizer_native_v2_dev",
        help="directory containing the frozen five-program incumbent portfolio",
    )
    parser.add_argument(
        "--model-dir",
        default="artifacts/ppo_adaptive_quick",
        help="directory containing ppo_seed_42101.zip and ppo_seed_42102.zip",
    )
    parser.add_argument(
        "--out-dir",
        default="artifacts/ppo_adaptive_frozen_eval",
    )
    args = parser.parse_args()

    run_frozen_ppo_generalization(
        source_dir=args.source_dir,
        model_dir=args.model_dir,
        out_dir=args.out_dir,
    )


if __name__ == "__main__":
    main()
