from aegisswarm.hybrid_objective_cli import build_parser


def test_hybrid_objective_cli_parses_quick_mode():
    args = build_parser().parse_args(["--quick", "--workers", "2", "--device", "cpu"])
    assert args.quick
    assert args.workers == 2
    assert args.device == "cpu"
