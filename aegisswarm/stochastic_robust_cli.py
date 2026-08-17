from __future__ import annotations

import argparse

from .stochastic_robust import run_stochastic_robust_training


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.stochastic_robust_cli",
        description=(
            "Train 60-token strategies across repeated matched SimulatorV2 random tapes "
            "and cross-evaluate incumbent vs contingent-backup execution."
        ),
    )
    parser.add_argument("--full", action="store_true", help="run the full robust-training development protocol")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--source-dir", default="artifacts/optimizer_native_v2_dev")
    parser.add_argument("--out-dir", default=None)
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = args.out_dir or (
        "artifacts/stochastic_robust_dev"
        if args.full
        else "artifacts/stochastic_robust_quick"
    )
    run_stochastic_robust_training(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=not args.full,
    )


if __name__ == "__main__":
    main()
