from __future__ import annotations

import argparse

from .optimizer_native_proof import (
    run_native_objective_confirmation,
    run_native_objective_development,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.optimizer_native_cli",
        description=(
            "Compare the current 60-token rule objective with a compact optimizer-native "
            "objective while holding search budget and Hungarian execution fixed."
        ),
    )
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument(
        "--source-dir",
        default="artifacts/optimizer_native_dev",
        help="frozen development directory used only with --confirm",
    )
    parser.add_argument("--force-train", action="store_true")
    return parser


def main():
    args = build_parser().parse_args()
    if args.quick and args.confirm:
        raise SystemExit("Choose either --quick or --confirm, not both.")
    if args.confirm and args.force_train:
        raise SystemExit("Confirmation never trains; --force-train is not allowed.")

    if args.confirm:
        run_native_objective_confirmation(
            source_dir=args.source_dir,
            out_dir=args.out_dir or "artifacts/optimizer_native_confirm",
            workers=args.workers,
        )
        return

    run_native_objective_development(
        out_dir=args.out_dir
        or ("artifacts/optimizer_native_quick" if args.quick else "artifacts/optimizer_native_dev"),
        workers=args.workers,
        quick=args.quick,
        force_train=args.force_train,
    )


if __name__ == "__main__":
    main()
