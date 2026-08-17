from __future__ import annotations

import argparse

from .reliability_ablation import run_reliability_screen


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.reliability_cli",
        description=(
            "Screen reliability-aware abstract assignment against the frozen incumbent "
            "under SimulatorV2 indexed randomness."
        ),
    )
    parser.add_argument("--full", action="store_true", help="use all reliability-development scenarios")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--source-dir", default="artifacts/optimizer_native_v2_dev")
    parser.add_argument("--out-dir", default=None)
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = args.out_dir or (
        "artifacts/reliability_aware_dev"
        if args.full
        else "artifacts/reliability_aware_quick"
    )
    run_reliability_screen(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=not args.full,
    )


if __name__ == "__main__":
    main()
