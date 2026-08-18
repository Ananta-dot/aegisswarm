from __future__ import annotations

import argparse

from .adaptive_rl import run_ppo_adaptive_screen


def main():
    parser = argparse.ArgumentParser(
        description="AegisSwarm hierarchical PPO online-adaptation screen"
    )
    parser.add_argument("--full", action="store_true", help="run full development protocol")
    parser.add_argument("--workers", type=int, default=8, help="parallel PPO vector environments")
    parser.add_argument(
        "--source-dir",
        default="artifacts/optimizer_native_v2_dev",
        help="directory containing the frozen five-program incumbent portfolio",
    )
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = (
            "artifacts/ppo_adaptive_dev"
            if args.full
            else "artifacts/ppo_adaptive_quick"
        )

    run_ppo_adaptive_screen(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=max(1, int(args.workers)),
        quick=not args.full,
    )


if __name__ == "__main__":
    main()
