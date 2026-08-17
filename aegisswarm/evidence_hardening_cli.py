from __future__ import annotations

import argparse
from collections import Counter

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
    result = run_evidence_hardening(
        source_dir=args.source_dir,
        out_dir=out_dir,
        workers=args.workers,
        quick=not args.full,
    )

    summaries = result["summaries"]
    normal_survival = summaries["incumbent_v2_normal"]["asset_survival_rate"]
    oracle_survival = summaries["best_of_5_oracle_v2"]["asset_survival_rate"]
    headroom = result["headroom"]
    choices = Counter(int(x) for x in result.get("best_of_5_oracle_choices", []))
    diagnostics = result.get("normal_v2_diagnostics_mean", {})

    print("\n--- DEVELOPMENT DIAGNOSTICS ---", flush=True)
    print(
        "normal per-program survival:      "
        f"{[round(float(x), 4) for x in normal_survival.get('training_run_means', [])]}",
        flush=True,
    )
    print(
        "best-of-5 oracle gap:             "
        f"{float(oracle_survival['mean']) - float(normal_survival['mean']):+.4f}",
        flush=True,
    )
    print(
        "oracle choice counts:             "
        f"{dict(sorted(choices.items()))}",
        flush=True,
    )

    for key, label in (
        ("perfect_sensing", "sensing headroom CI"),
        ("deterministic_interactions", "interaction headroom CI"),
        ("combined_relaxation", "combined headroom CI"),
    ):
        stats = headroom[key]["asset_survival_rate"]
        print(
            f"{label + ':':32s} "
            f"{stats['relaxed_minus_normal']:+.4f} CI={stats['ci95']}",
            flush=True,
        )

    interesting = (
        "detection_opportunities",
        "detections",
        "real_interaction_attempts",
        "real_interaction_failures",
        "decoy_resource_uses",
        "penetrations_undetected",
        "penetrations_no_in_range_defender",
        "penetrations_in_range_no_resource",
        "penetrations_with_reachable_resource",
        "overload_steps",
        "resource_uses_remaining",
        "resource_exhausted",
    )
    compact = {
        key: round(float(diagnostics[key]), 4)
        for key in interesting
        if key in diagnostics
    }
    print(f"normal diagnostic means:         {compact}", flush=True)


if __name__ == "__main__":
    main()
