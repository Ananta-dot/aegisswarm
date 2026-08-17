from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import evaluate_policies, format_summary
from .splits import TRAIN_SEEDS, TEST_SEEDS
from .scoring import EvalConfig
from .rule_search import evolutionary_rule_search, save_rule_result, load_best_program
from .rule_axplorer import train_rule_axplorer, save_rule_axplorer_result
from .axplorer_lite import load_best_genome
from .rl import load_qtable


def _save_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def cmd_train_local(args):
    cfg = EvalConfig(
        seeds=TRAIN_SEEDS[:args.train_scenarios],
        n_threats=args.threats,
        n_defenders=args.defenders,
    )
    best, history = evolutionary_rule_search(
        cfg,
        seed=args.seed,
        population=args.population,
        generations=args.generations,
        local_trials=args.local_search_trials,
    )
    save_rule_result(best, history, args.out)
    print(f"saved structured local-search result: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_train_axplorer(args):
    cfg = EvalConfig(
        seeds=TRAIN_SEEDS[:args.train_scenarios],
        n_threats=args.threats,
        n_defenders=args.defenders,
    )
    best, history, model = train_rule_axplorer(
        cfg,
        seed=args.seed,
        epochs=args.epochs,
        population=args.population,
        samples_per_epoch=args.samples_per_epoch,
        train_steps=args.train_steps,
        local_search_trials=args.local_search_trials,
        temperature=args.temperature,
    )
    save_rule_axplorer_result(best, history, args.out, model=model)
    print(f"saved structured Axplorer result: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_prove(args):
    q = load_qtable(args.rl_table) if args.rl_table else None
    legacy_local = load_best_genome(args.legacy_local) if args.legacy_local else None
    legacy_axplorer = load_best_genome(args.legacy_axplorer) if args.legacy_axplorer else None
    rule_local = load_best_program(args.rule_local) if args.rule_local else None
    rule_axplorer = load_best_program(args.rule_axplorer) if args.rule_axplorer else None

    result = evaluate_policies(
        TEST_SEEDS[:args.episodes],
        scenario_kwargs={
            "n_threats": args.threats,
            "n_defenders": args.defenders,
            "n_assets": args.assets,
            "n_sensors": args.sensors,
        },
        qtable=q,
        local_genome=legacy_local,
        axplorer_genome=legacy_axplorer,
        rule_local_program=rule_local,
        rule_axplorer_program=rule_axplorer,
    )
    print(format_summary(result))
    if args.out:
        _save_json(result, args.out)
        print(f"saved: {args.out}")


def build_parser():
    p = argparse.ArgumentParser(prog="python -m aegisswarm.rule_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("train-local")
    l.add_argument("--generations", type=int, default=12)
    l.add_argument("--population", type=int, default=96)
    l.add_argument("--train-scenarios", type=int, default=16)
    l.add_argument("--local-search-trials", type=int, default=6)
    l.add_argument("--seed", type=int, default=123)
    l.add_argument("--threats", type=int, default=30)
    l.add_argument("--defenders", type=int, default=8)
    l.add_argument("--out", default="artifacts/rule_local.json")
    l.set_defaults(func=cmd_train_local)

    a = sub.add_parser("train-axplorer")
    a.add_argument("--epochs", type=int, default=12)
    a.add_argument("--population", type=int, default=128)
    a.add_argument("--samples-per-epoch", type=int, default=128)
    a.add_argument("--train-steps", type=int, default=300)
    a.add_argument("--local-search-trials", type=int, default=4)
    a.add_argument("--train-scenarios", type=int, default=16)
    a.add_argument("--temperature", type=float, default=0.9)
    a.add_argument("--seed", type=int, default=123)
    a.add_argument("--threats", type=int, default=30)
    a.add_argument("--defenders", type=int, default=8)
    a.add_argument("--out", default="artifacts/rule_axplorer.json")
    a.set_defaults(func=cmd_train_axplorer)

    pr = sub.add_parser("prove")
    pr.add_argument("--episodes", type=int, default=100)
    pr.add_argument("--rl-table", default=None)
    pr.add_argument("--legacy-local", default=None)
    pr.add_argument("--legacy-axplorer", default=None)
    pr.add_argument("--rule-local", default=None)
    pr.add_argument("--rule-axplorer", default=None)
    pr.add_argument("--threats", type=int, default=30)
    pr.add_argument("--defenders", type=int, default=8)
    pr.add_argument("--assets", type=int, default=2)
    pr.add_argument("--sensors", type=int, default=3)
    pr.add_argument("--out", default="artifacts/rule_ablation.json")
    pr.set_defaults(func=cmd_prove)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
