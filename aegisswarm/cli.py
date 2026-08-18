from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .policies import BASELINE_POLICIES
from .optimization import HungarianPolicy
from .benchmark import evaluate_policies, format_summary
from .splits import SPLITS, TRAIN_SEEDS, VALIDATION_SEEDS, TEST_SEEDS
from .rl import train_q_learning, save_qtable, load_qtable
from .scoring import EvalConfig
from .axplorer_lite import train_axplorer_style, save_axplorer_result, load_best_genome
from .local_search import evolutionary_search
from .stress import STRESS_FAMILIES
from .scoring_v2 import EvalConfigV2, evaluate_genome_v2
from .search_v2 import train_policy_search_v2, save_policy_search_v2, load_best_genome_v2
from .strategy_v2 import decode_genome_v2


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
        print(f"{name:18s} survival={m.asset_survival_rate:.3f} containment={m.containment_rate:.3f} damage={m.cumulative_damage:.3f}")


def cmd_benchmark(args):
    seeds = SPLITS[args.split][:args.episodes]
    result = evaluate_policies(seeds, scenario_kwargs={"n_threats": args.threats, "n_defenders": args.defenders, "n_assets": args.assets, "n_sensors": args.sensors})
    print(format_summary(result))
    if args.out:
        _save_json(result, args.out)


def cmd_train_rl(args):
    q = train_q_learning(episodes=args.episodes, seed=args.seed, n_threats=args.threats, n_defenders=args.defenders)
    save_qtable(q, args.out)
    print(f"saved RL table: {args.out}")
    print(f"learned states: {len(q)}")


def cmd_train_axplorer(args):
    cfg = EvalConfig(seeds=TRAIN_SEEDS[:args.train_scenarios], n_threats=args.threats, n_defenders=args.defenders)
    best, history, model = train_axplorer_style(cfg, seed=args.seed, epochs=args.epochs, population=args.population, samples_per_epoch=args.samples_per_epoch, train_steps=args.train_steps, local_search_trials=args.local_search_trials, temperature=args.temperature)
    save_axplorer_result(best, history, args.out, model=model)
    print(f"saved Axplorer-style result: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_train_local(args):
    cfg = EvalConfig(seeds=TRAIN_SEEDS[:args.train_scenarios], n_threats=args.threats, n_defenders=args.defenders)
    best, history = evolutionary_search(cfg, seed=args.seed, population=args.population, generations=args.generations)
    _save_json({"best": best, "history": history}, args.out)
    print(f"saved local-search ablation: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_prove(args):
    seeds = TEST_SEEDS[:args.episodes]
    q = load_qtable(args.rl_table) if args.rl_table else None
    genome = load_best_genome(args.genome) if args.genome else None
    result = evaluate_policies(seeds, scenario_kwargs={"n_threats": args.threats, "n_defenders": args.defenders, "n_assets": args.assets, "n_sensors": args.sensors}, qtable=q, genome=genome)
    print(format_summary(result))
    if args.out:
        _save_json(result, args.out)


def cmd_stress(args):
    q = load_qtable(args.rl_table) if args.rl_table else None
    genome = load_best_genome(args.genome) if args.genome else None
    all_results = {}
    for i, (name, kwargs) in enumerate(STRESS_FAMILIES.items()):
        seeds = tuple(range(5000 + i * 1000, 5000 + i * 1000 + args.episodes))
        result = evaluate_policies(seeds, scenario_kwargs=kwargs, qtable=q, genome=genome)
        all_results[name] = result
        print(f"\n=== {name} ===")
        print(format_summary(result))
    if args.out:
        _save_json(all_results, args.out)


def cmd_all(args):
    Path("artifacts").mkdir(exist_ok=True)
    if args.quick:
        rl_episodes, ax_epochs, pop, samples, steps, train_scenarios, proof_episodes, local_trials = 80, 3, 32, 32, 50, 4, 20, 2
    else:
        rl_episodes, ax_epochs, pop, samples, steps, train_scenarios, proof_episodes, local_trials = 1500, 20, 256, 256, 500, 32, 500, 4
    q = train_q_learning(episodes=rl_episodes, seed=123)
    save_qtable(q, "artifacts/qtable.json")
    cfg = EvalConfig(seeds=TRAIN_SEEDS[:train_scenarios])
    best, history, model = train_axplorer_style(cfg, seed=123, epochs=ax_epochs, population=pop, samples_per_epoch=samples, train_steps=steps, local_search_trials=local_trials)
    save_axplorer_result(best, history, "artifacts/axplorer_best.json", model=model)
    genome = load_best_genome("artifacts/axplorer_best.json")
    result = evaluate_policies(TEST_SEEDS[:proof_episodes], qtable=q, genome=genome)
    print(format_summary(result))
    out = "artifacts/quick_proof.json" if args.quick else "artifacts/proof.json"
    _save_json(result, out)
    print(f"\nsaved: {out}")


def cmd_search_v2(args):
    if args.quick:
        epochs, population, samples, train_steps = 2, 16, 16, 10
        screen_n, train_n, validation_n = 4, 8, 8
        validation_candidates, local_trials, archive_size = 4, 2, 8
    else:
        epochs, population, samples, train_steps = args.epochs, args.population, args.samples_per_epoch, args.train_steps
        screen_n, train_n, validation_n = args.screen_scenarios, args.train_scenarios, args.validation_scenarios
        validation_candidates, local_trials, archive_size = args.validation_candidates, args.local_search_trials, args.archive_size

    common = dict(n_threats=args.threats, n_defenders=args.defenders, n_assets=args.assets, n_sensors=args.sensors)
    screen_cfg = EvalConfigV2(seeds=TRAIN_SEEDS[:screen_n], **common)
    train_cfg = EvalConfigV2(seeds=TRAIN_SEEDS[:train_n], **common)
    validation_cfg = EvalConfigV2(seeds=VALIDATION_SEEDS[:validation_n], **common)

    best, history, model, archive = train_policy_search_v2(
        screen_cfg,
        train_cfg,
        validation_cfg,
        seed=args.seed,
        epochs=epochs,
        population=population,
        samples_per_epoch=samples,
        train_steps=train_steps,
        promotion_fraction=args.promotion_fraction,
        validation_candidates=validation_candidates,
        local_search_trials=local_trials,
        archive_size=archive_size,
        temperature=args.temperature,
    )
    metadata = {
        "seed": args.seed,
        "screen_seeds": list(screen_cfg.seeds),
        "train_seeds": list(train_cfg.seeds),
        "validation_seeds": list(validation_cfg.seeds),
        "test_seeds_used_during_search": [],
        "quick": bool(args.quick),
    }
    save_policy_search_v2(best, history, archive, args.out, model=model, metadata=metadata)
    print(f"saved adaptive v2 search: {args.out}")
    print(json.dumps(best, indent=2))


def cmd_prove_v2(args):
    genome = load_best_genome_v2(args.genome)
    cfg = EvalConfigV2(seeds=TEST_SEEDS[:args.episodes], n_threats=args.threats, n_defenders=args.defenders, n_assets=args.assets, n_sensors=args.sensors)
    result = evaluate_genome_v2(genome, cfg)
    payload = {"genome": [int(x) for x in genome], "test_seeds": list(cfg.seeds), "metrics": result}
    print(json.dumps(payload, indent=2))
    if args.out:
        _save_json(payload, args.out)


def cmd_decode_v2(args):
    from dataclasses import asdict
    genome = load_best_genome_v2(args.genome)
    print(json.dumps({"genes": [int(x) for x in genome], "decoded": asdict(decode_genome_v2(genome))}, indent=2))


def cmd_serve(args):
    import uvicorn
    uvicorn.run("aegisswarm.service:app", host=args.host, port=args.port, reload=False)


def build_parser():
    p = argparse.ArgumentParser(prog="aegisswarm")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke")
    s.set_defaults(func=cmd_smoke)

    b = sub.add_parser("benchmark")
    b.add_argument("--episodes", type=int, default=100); b.add_argument("--split", choices=list(SPLITS), default="test")
    b.add_argument("--threats", type=int, default=30); b.add_argument("--defenders", type=int, default=8); b.add_argument("--assets", type=int, default=2); b.add_argument("--sensors", type=int, default=3); b.add_argument("--out", default=None)
    b.set_defaults(func=cmd_benchmark)

    r = sub.add_parser("train-rl")
    r.add_argument("--episodes", type=int, default=1000); r.add_argument("--seed", type=int, default=123); r.add_argument("--threats", type=int, default=30); r.add_argument("--defenders", type=int, default=8); r.add_argument("--out", default="artifacts/qtable.json")
    r.set_defaults(func=cmd_train_rl)

    a = sub.add_parser("train-axplorer")
    a.add_argument("--epochs", type=int, default=10); a.add_argument("--population", type=int, default=128); a.add_argument("--samples-per-epoch", type=int, default=128); a.add_argument("--train-steps", type=int, default=300); a.add_argument("--local-search-trials", type=int, default=4); a.add_argument("--train-scenarios", type=int, default=16); a.add_argument("--temperature", type=float, default=0.8); a.add_argument("--seed", type=int, default=123); a.add_argument("--threats", type=int, default=30); a.add_argument("--defenders", type=int, default=8); a.add_argument("--out", default="artifacts/axplorer_best.json")
    a.set_defaults(func=cmd_train_axplorer)

    l = sub.add_parser("train-local")
    l.add_argument("--generations", type=int, default=10); l.add_argument("--population", type=int, default=64); l.add_argument("--train-scenarios", type=int, default=16); l.add_argument("--seed", type=int, default=123); l.add_argument("--threats", type=int, default=30); l.add_argument("--defenders", type=int, default=8); l.add_argument("--out", default="artifacts/local_search.json")
    l.set_defaults(func=cmd_train_local)

    pr = sub.add_parser("prove")
    pr.add_argument("--episodes", type=int, default=100); pr.add_argument("--rl-table", default=None); pr.add_argument("--genome", default=None); pr.add_argument("--threats", type=int, default=30); pr.add_argument("--defenders", type=int, default=8); pr.add_argument("--assets", type=int, default=2); pr.add_argument("--sensors", type=int, default=3); pr.add_argument("--out", default=None)
    pr.set_defaults(func=cmd_prove)

    st = sub.add_parser("stress")
    st.add_argument("--episodes", type=int, default=100); st.add_argument("--rl-table", default=None); st.add_argument("--genome", default=None); st.add_argument("--out", default=None)
    st.set_defaults(func=cmd_stress)

    al = sub.add_parser("all")
    al.add_argument("--quick", action="store_true"); al.set_defaults(func=cmd_all)

    v2 = sub.add_parser("search-v2", help="search adaptive 20-gene policies with staged train/validation evaluation")
    v2.add_argument("--quick", action="store_true"); v2.add_argument("--epochs", type=int, default=20); v2.add_argument("--population", type=int, default=256); v2.add_argument("--samples-per-epoch", type=int, default=256); v2.add_argument("--train-steps", type=int, default=500); v2.add_argument("--screen-scenarios", type=int, default=16); v2.add_argument("--train-scenarios", type=int, default=64); v2.add_argument("--validation-scenarios", type=int, default=32); v2.add_argument("--validation-candidates", type=int, default=12); v2.add_argument("--promotion-fraction", type=float, default=0.50); v2.add_argument("--local-search-trials", type=int, default=4); v2.add_argument("--archive-size", type=int, default=32); v2.add_argument("--temperature", type=float, default=0.8); v2.add_argument("--seed", type=int, default=123); v2.add_argument("--threats", type=int, default=30); v2.add_argument("--defenders", type=int, default=8); v2.add_argument("--assets", type=int, default=2); v2.add_argument("--sensors", type=int, default=3); v2.add_argument("--out", default="artifacts/policy_v2.json")
    v2.set_defaults(func=cmd_search_v2)

    pv2 = sub.add_parser("prove-v2", help="evaluate the selected v2 champion on untouched test seeds")
    pv2.add_argument("--genome", default="artifacts/policy_v2.json"); pv2.add_argument("--episodes", type=int, default=500); pv2.add_argument("--threats", type=int, default=30); pv2.add_argument("--defenders", type=int, default=8); pv2.add_argument("--assets", type=int, default=2); pv2.add_argument("--sensors", type=int, default=3); pv2.add_argument("--out", default="artifacts/policy_v2_test.json")
    pv2.set_defaults(func=cmd_prove_v2)

    dv2 = sub.add_parser("decode-v2", help="show the learned adaptive policy parameters")
    dv2.add_argument("--genome", default="artifacts/policy_v2.json"); dv2.set_defaults(func=cmd_decode_v2)

    sv = sub.add_parser("serve")
    sv.add_argument("--host", default="127.0.0.1"); sv.add_argument("--port", type=int, default=8000); sv.set_defaults(func=cmd_serve)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
