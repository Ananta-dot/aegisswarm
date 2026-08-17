from __future__ import annotations

import argparse

from .hybrid_objective_proof import (
    run_hybrid_objective_confirmation,
    run_hybrid_objective_development,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.hybrid_objective_cli",
        description=(
            "Train strategies against the optimizer itself. Development uses a fresh "
            "seed block; confirmation only evaluates frozen artifacts."
        ),
    )
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument(
        "--source-dir",
        default="artifacts/hybrid_objective_dev",
        help="frozen development directory used only with --confirm",
    )
    parser.add_argument("--force-train", action="store_true")
    return parser


def main():
    args = build_parser().parse_args()
    if args.confirm and args.quick:
        raise SystemExit("Choose either --quick or --confirm, not both.")
    if args.confirm and args.force_train:
        raise SystemExit("--confirm never trains; --force-train is not allowed.")

    if args.confirm:
        out_dir = args.out_dir or "artifacts/hybrid_objective_confirm"
        run_hybrid_objective_confirmation(
            source_dir=args.source_dir,
            out_dir=out_dir,
            workers=args.workers,
        )
        return

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = (
            "artifacts/hybrid_objective_quick"
            if args.quick
            else "artifacts/hybrid_objective_dev"
        )
    run_hybrid_objective_development(
        out_dir=out_dir,
        workers=args.workers,
        device=args.device,
        quick=args.quick,
        force_train=args.force_train,
    )


if __name__ == "__main__":
    main()
