from __future__ import annotations

import argparse

from .evidence_hardening import run_evidence_hardening


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m aegisswarm.evidence_hardening_cli",
        description=(
            "Evaluate the incumbent architecture under Simulator V2 indexed randomness "
            "and development-only sensing/interaction/headroom diagnostics."
        ),
    )
    parser.add_argument("--full", action="store_true", help="use all evidence-development scenarios")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--source-dir", default="artifacts/optimizer_native_v2_dev")
    parser.add_argument("--out-dir", default=None)
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = args.out_dir or (
        "artifacts/evidence_hardening_dev"
        if args.full
        else "artifacts/evidence_hardening_quick"
    )
    run_evidence_hardening(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=not args.full,
    )


if __name__ == "__main__":
    main()
