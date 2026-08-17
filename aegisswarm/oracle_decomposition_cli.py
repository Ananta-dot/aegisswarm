from __future__ import annotations

import argparse

from .oracle_decomposition import run_oracle_decomposition


def main():
    parser = argparse.ArgumentParser(
        description="Decompose AegisSwarm hindsight-oracle headroom across indexed stochastic tapes."
    )
    parser.add_argument("--source-dir", default="artifacts/optimizer_native_v2_dev")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    out_dir = (
        "artifacts/oracle_decomposition_dev"
        if args.full
        else "artifacts/oracle_decomposition_quick"
    )
    run_oracle_decomposition(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=not args.full,
    )


if __name__ == "__main__":
    main()
