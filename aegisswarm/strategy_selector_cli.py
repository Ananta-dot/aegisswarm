from __future__ import annotations

import argparse

from .strategy_selector import run_strategy_selector


def main():
    parser = argparse.ArgumentParser(
        description="AegisSwarm observability-safe frozen-strategy selector screen"
    )
    parser.add_argument("--full", action="store_true", help="run full development")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument(
        "--source-dir",
        default="artifacts/optimizer_native_v2_dev",
        help="directory containing the five frozen incumbent rule-program runs",
    )
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    quick = not args.full
    out_dir = args.out_dir or (
        "artifacts/strategy_selector_quick"
        if quick
        else "artifacts/strategy_selector_dev"
    )

    print(
        f"AegisSwarm observable strategy selector | "
        f"mode={'quick' if quick else 'development'} workers={args.workers}",
        flush=True,
    )
    run_strategy_selector(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=quick,
    )


if __name__ == "__main__":
    main()
