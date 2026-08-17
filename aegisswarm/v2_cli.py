from __future__ import annotations

import argparse

from .v2_proof import run_v2_confirmation, run_v2_development
from .worker_compat import install_final_proof_worker_compat


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.v2_cli",
        description=(
            "Run the Axplorer V2 development protocol. Development uses seeds "
            "3000-3399; confirmation seeds 6000-6399 are only available through "
            "the explicit --confirm mode after V2 is frozen."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="small end-to-end integration check on the V2 development block",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="evaluate frozen V2 development policies on reserved confirmation seeds; never trains",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--device",
        choices=["cpu", "mps", "cuda"],
        default=None,
        help="transformer device for development training",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="override output directory",
    )
    parser.add_argument(
        "--source-dir",
        default="artifacts/axplorer_v2_dev",
        help="frozen development directory used only with --confirm",
    )
    parser.add_argument(
        "--force-train",
        action="store_true",
        help="retrain completed development runs; invalid with --confirm",
    )
    return parser


def main():
    # V1 final_proof historically reused `_evaluate_program_worker` for two
    # different process-pool signatures. V2 installs a spawn-safe dispatcher
    # before any training or evaluation starts so both call paths work on macOS.
    install_final_proof_worker_compat()

    args = build_parser().parse_args()
    if args.confirm and args.quick:
        raise SystemExit("Choose either --quick or --confirm, not both.")
    if args.confirm and args.force_train:
        raise SystemExit("--confirm never trains; --force-train is not allowed.")

    if args.confirm:
        out_dir = args.out_dir or "artifacts/axplorer_v2_confirm"
        run_v2_confirmation(
            source_dir=args.source_dir,
            out_dir=out_dir,
            workers=args.workers,
        )
        return

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = "artifacts/axplorer_v2_quick" if args.quick else "artifacts/axplorer_v2_dev"

    run_v2_development(
        out_dir=out_dir,
        workers=args.workers,
        device=args.device,
        quick=args.quick,
        force_train=args.force_train,
    )


if __name__ == "__main__":
    main()
