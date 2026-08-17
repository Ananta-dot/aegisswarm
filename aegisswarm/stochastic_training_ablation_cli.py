from __future__ import annotations

import argparse

from .stochastic_training_ablation import run_stochastic_training_ablation


def main():
    parser = argparse.ArgumentParser(
        description="Run the matched SimulatorV2 single-tape vs repeated-tape training ablation."
    )
    parser.add_argument("--full", action="store_true", help="Run full development instead of quick screen.")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--source-dir", default="artifacts/optimizer_native_v2_dev")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    quick = not args.full
    out = args.out or (
        "artifacts/stochastic_training_ablation_quick"
        if quick
        else "artifacts/stochastic_training_ablation_dev"
    )
    run_stochastic_training_ablation(
        source_dir=args.source_dir,
        out_dir=out,
        workers=args.workers,
        quick=quick,
    )


if __name__ == "__main__":
    main()
