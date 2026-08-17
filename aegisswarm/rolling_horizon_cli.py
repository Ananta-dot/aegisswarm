from __future__ import annotations

import argparse

from .rolling_horizon_ablation import run_planning_screen


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.rolling_horizon_cli",
        description=(
            "Screen rolling-horizon planner V2 against the same frozen 60-token "
            "rule strategies executed by one-step Hungarian assignment."
        ),
    )
    parser.add_argument("--full", action="store_true", help="use all planner-V2 development scenarios")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=4)
    parser.add_argument("--discount", type=float, default=0.90)
    parser.add_argument("--solver-time-limit", type=float, default=0.25)
    parser.add_argument("--source-dir", default="artifacts/optimizer_native_v2_dev")
    parser.add_argument("--out-dir", default=None)
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = args.out_dir or (
        "artifacts/rolling_horizon_v2_dev_screen"
        if args.full
        else "artifacts/rolling_horizon_v2_quick"
    )
    run_planning_screen(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=not args.full,
        horizon=args.horizon,
        discount=args.discount,
        time_limit=args.solver_time_limit,
    )


if __name__ == "__main__":
    main()
