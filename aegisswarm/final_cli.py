from __future__ import annotations

import argparse

from .final_proof import run_final_proof
from .final_runtime_patch import install_budgeted_oracle_patch


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.final_cli",
        description=(
            "Run the frozen AegisSwarm proof protocol. Use --quick first; "
            "quick mode uses validation seeds and does not consume the final holdout."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="small integration check on validation seeds only",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="CPU worker processes used for simulator scoring",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "mps", "cuda"],
        default=None,
        help="transformer device; default is auto-detect",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="output directory (defaults to artifacts/final_proof[_quick])",
    )
    parser.add_argument(
        "--force-train",
        action="store_true",
        help="ignore completed per-seed training artifacts and retrain them",
    )
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = "artifacts/final_proof_quick" if args.quick else "artifacts/final_proof"

    # final_proof historically reused the same private worker name for two
    # different process-pool jobs. Install the unambiguous spawn-safe candidate
    # scorer before creating any pools.
    install_budgeted_oracle_patch()

    run_final_proof(
        out_dir=out_dir,
        workers=args.workers,
        device=args.device,
        quick=args.quick,
        force_train=args.force_train,
    )


if __name__ == "__main__":
    main()
