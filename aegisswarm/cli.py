from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .policies import BASELINE_POLICIES
from .optimization import HungarianPolicy
from .benchmark import evaluate_policies, format_summary
from .splits import SPLITS, TRAIN_SEEDS, TEST_SEEDS
from .rl import train_q_learning, save_qtable, load_qtable
from .scoring import EvalConfig
from .axplorer_lite import train_axplorer_style, save_axplorer_result, load_best_genome
from .local_search import evolutionary_search
from .stress import STRESS_FAMILIES


def _save_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def cmd_smoke(_args):
    gen = ScenarioGenerator(max_steps=80)
    base = gen.generate(seed=7, n_threats=18, n_defenders=6)
    policies = {name: cls() for name, cls in BASELINE_POLICIES.items()}
    policies["hungarian"] = HungarianPolicy()

    print("AegisSwarm smoke test")
    for name, policy in policies.items():
        m = Simulator.evaluate_policy(gen.clone(base), policy)
        print(
            f"{name:18s} survival={m.asset_survival_rate:.3f} "
            f"containment={m.containment_rate:.3f} damage={m.cumulative_damage:.3f}"
        )


def cmd_benchmark(args):
    seeds = SPLITS[args.split][:args.episodes]
    result = evaluate_policies(
        seeds,
        scenario_kwargs={
            "n_threats": args.threats,
            "n_defenders": args.defenders,
            "n_assets": args.assets,
            "n_sensors": args.sensors,
        },
    )
    print(format_summary(result))
    if args.out:
        _save_json(result, args.out)


def cmd_train_rl(args):
    q = train_q_learning(
        episodes=args.episodes,
        seed=args.seed,
        n_threats=args.threats,
        n_defenders=args.defenders,
    )
    save_qtable(q, args.out)
    print(f"saved RL table: {args.out}")
    print(f"learned states: {len(q)}")


def cmd_train_axplorer(args):
    train_seeds = TRAIN_SEEDS[:args.train_scenarios]
    cfg = EvalConfig(
        seeds=train_seeds,
        n_threats=args.threats,
        n_defenders=args.defenders,
    )
    best, history, model = train_axplorer_style(
        cfg,
        seed=args.seed,
        epochs=args.epochs,
        population=args.population,
        samples_per_epoch=args.samples_per_epoch,
        train_steps=args.train_steps,
        local_search_trials=args.local_search_trials,
        temperature=args.temperature,
    )
    save_axplorer_result(best, history, args.out, model=model)
    print(f"saved Axplorer-style result: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_train_local(args):
    cfg = EvalConfig(
        seeds=TRAIN_SEEDS[:args.train_scenarios],
        n_threats=args.threats,
        n_defenders=args.defenders,
    )
    best, history = evolutionary_search(
        cfg,
        seed=args.seed,
        population=args.population,
        generations=args.generations,
    )
    _save_json({"best": best, "history": history}, args.out)
    print(f"saved local-search ablation: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_prove(args):
    seeds = TEST_SEEDS[:args.episodes]
    q = load_qtable(args.rl_table) if args.rl_table else None
    genome = load_best_genome(args.genome) if args.genome else None

    result = evaluate_policies(
        seeds,
        scenario_kwargs={
            "n_threats": args.threats,
            "n_defenders": args.defenders,
            "n_assets": args.assets,
            "n_sensors": args.sensors,
        },
        qtable=q,
        genome=genome,
    )
    print(format_summary(result))
    if args.out:
        _save_json(result, args.out)


def cmd_stress(args):
    q = load_qtable(args.rl_table) if args.rl_table else None
    genome = load_best_genome(args.genome) if args.genome else None
    all_results = {}

    for i, (name, kwargs) in enumerate(STRESS_FAMILIES.items()):
        seeds = tuple(range(5000 + i * 1000, 5000 + i * 1000 + args.episodes))
        result = evaluate_policies(
            seeds,
            scenario_kwargs=kwargs,
            qtable=q,
            genome=genome,
        )
        all_results[name] = result
        print(f"\n=== {name} ===")
        print(format_summary(result))

    if args.out:
        _save_json(all_results, args.out)


def cmd_all(args):
    Path("artifacts").mkdir(exist_ok=True)

    if args.quick:
        rl_episodes = 80
        ax_epochs = 3
        pop = 32
        samples = 32
        steps = 50
        train_scenarios = 4
        proof_episodes = 20
        local_trials = 2
    else:
        rl_episodes = 1500
        ax_epochs = 20
        pop = 256
        samples = 256
        steps = 500
        train_scenarios = 32
        proof_episodes = 500
        local_trials = 4

    q = train_q_learning(episodes=rl_episodes, seed=123)
    save_qtable(q, "artifacts/qtable.json")

    cfg = EvalConfig(seeds=TRAIN_SEEDS[:train_scenarios])
    best, history, model = train_axplorer_style(
        cfg,
        seed=123,
        epochs=ax_epochs,
        population=pop,
        samples_per_epoch=samples,
        train_steps=steps,
        local_search_trials=local_trials,
    )
    save_axplorer_result(best, history, "artifacts/axplorer_best.json", model=model)

    genome = load_best_genome("artifacts/axplorer_best.json")
    result = evaluate_policies(
        TEST_SEEDS[:proof_episodes],
        qtable=q,
        genome=genome,
    )
    print(format_summary(result))
    out = "artifacts/quick_proof.json" if args.quick else "artifacts/proof.json"
    _save_json(result, out)
    print(f"\nsaved: {out}")


def cmd_serve(args):
    import uvicorn
    uvicorn.run("aegisswarm.service:app", host=args.host, port=args.port, reload=False)


def build_parser():
    p = argparse.ArgumentParser(prog="aegisswarm")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke")
    s.set_defaults(func=cmd_smoke)

    b = sub.add_parser("benchmark")
    b.add_argument("--episodes", type=int, default=100)
    b.add_argument("--split", choices=list(SPLITS), default="test")
    b.add_argument("--threats", type=int, default=30)
    b.add_argument("--defenders", type=int, default=8)
    b.add_argument("--assets", type=int, default=2)
    b.add_argument("--sensors", type=int, default=3)
    b.add_argument("--out", default=None)
    b.set_defaults(func=cmd_benchmark)

    r = sub.add_parser("train-rl")
    r.add_argument("--episodes", type=int, default=1000)
    r.add_argument("--seed", type=int, default=123)
    r.add_argument("--threats", type=int, default=30)
    r.add_argument("--defenders", type=int, default=8)
    r.add_argument("--out", default="artifacts/qtable.json")
    r.set_defaults(func=cmd_train_rl)

    a = sub.add_parser("train-axplorer")
    a.add_argument("--epochs", type=int, default=10)
    a.add_argument("--population", type=int, default=128)
    a.add_argument("--samples-per-epoch", type=int, default=128)
    a.add_argument("--train-steps", type=int, default=300)
    a.add_argument("--local-search-trials", type=int, default=4)
    a.add_argument("--train-scenarios", type=int, default=16)
    a.add_argument("--temperature", type=float, default=0.8)
    a.add_argument("--seed", type=int, default=123)
    a.add_argument("--threats", type=int, default=30)
    a.add_argument("--defenders", type=int, default=8)
    a.add_argument("--out", default="artifacts/axplorer_best.json")
    a.set_defaults(func=cmd_train_axplorer)

    l = sub.add_parser("train-local")
    l.add_argument("--generations", type=int, default=10)
    l.add_argument("--population", type=int, default=64)
    l.add_argument("--train-scenarios", type=int, default=16)
    l.add_argument("--seed", type=int, default=123)
    l.add_argument("--threats", type=int, default=30)
    l.add_argument("--defenders", type=int, default=8)
    l.add_argument("--out", default="artifacts/local_search.json")
    l.set_defaults(func=cmd_train_local)

    pr = sub.add_parser("prove")
    pr.add_argument("--episodes", type=int, default=100)
    pr.add_argument("--rl-table", default=None)
    pr.add_argument("--genome", default=None)
    pr.add_argument("--threats", type=int, default=30)
    pr.add_argument("--defenders", type=int, default=8)
    pr.add_argument("--assets", type=int, default=2)
    pr.add_argument("--sensors", type=int, default=3)
    pr.add_argument("--out", default=None)
    pr.set_defaults(func=cmd_prove)

    st = sub.add_parser("stress")
    st.add_argument("--episodes", type=int, default=100)
    st.add_argument("--rl-table", default=None)
    st.add_argument("--genome", default=None)
    st.add_argument("--out", default=None)
    st.set_defaults(func=cmd_stress)

    al = sub.add_parser("all")
    al.add_argument("--quick", action="store_true")
    al.set_defaults(func=cmd_all)

    sv = sub.add_parser("serve")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.set_defaults(func=cmd_serve)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
