from aegisswarm.hybrid_objective_cli import build_parser


def test_confirmation_is_not_default():
    args = build_parser().parse_args([])
    assert not args.confirm
