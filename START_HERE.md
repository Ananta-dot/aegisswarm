# START HERE

You only need this repository now. Ignore the earlier M1–M5 ZIPs.

## One-time setup

```bash
cd aegisswarm_full
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,serve]"
```

## Verify

```bash
pytest -q
python -m aegisswarm.cli smoke
```

## Run the entire pipeline quickly

```bash
python -m aegisswarm.cli all --quick
```

This validates:
- simulator
- heuristic baselines
- optimization baseline
- sequential RL baseline
- Axplorer-style transformer search
- held-out comparison

## Then run the serious experiment

```bash
bash scripts/run_full.sh
```

That creates the final experiment artifacts under `artifacts/`.

## Start the demo

```bash
python -m aegisswarm.cli serve --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Important workflow

Do not keep rebuilding/setup-ing stages individually.

From now on:
1. keep this repository as the single source of truth;
2. modify it in place;
3. use Git for checkpoints;
4. run `pytest -q` after changes;
5. use `all --quick` for integration checks;
6. use `scripts/run_full.sh` only for serious benchmark runs.
