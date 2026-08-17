from __future__ import annotations

import argparse

from .hybrid_ablation import run_hybrid_ablation


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.hybrid_cli",
        description=(
            "Compare fixed discovered strategies under greedy versus optimized "
            "execution on the separate hybrid development block."
        ),
    )
    parser.add_argument(
        "--source-dir",
        default="artifacts/axplorer_v2_dev",
        help="directory containing paired V2/local run artifacts",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="output directory (defaults to artifacts/hybrid_ablation[_quick])",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="use first 20 hybrid-development scenarios for integration checking",
    )
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = "artifacts/hybrid_ablation_quick" if args.quick else "artifacts/hybrid_ablation"

    run_hybrid_ablation(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=args.quick,
    )


if __name__ == "__main__":
    main()
