from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .policies import BASELINE_POLICIES
from .optimization import HungarianPolicy


app = FastAPI(title="AegisSwarm Research Demo", version="0.2.0")


class SimRequest(BaseModel):
    seed: int = 7
    n_threats: int = 30
    n_defenders: int = 8
    n_assets: int = 2
    n_sensors: int = 3
    policy: str = "highest_risk"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AegisSwarm Research Demo</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }
    input, select, button { margin: 5px; padding: 8px; }
    pre { background: #f4f4f4; padding: 16px; overflow: auto; }
  </style>
</head>
<body>
<h1>AegisSwarm Research Demo</h1>
<p>Synthetic, normalized counter-swarm coordination simulator.</p>
<div>
Seed <input id="seed" type="number" value="7">
Threats <input id="threats" type="number" value="30">
Defenders <input id="defenders" type="number" value="8">
<button onclick="run()">Compare baselines</button>
</div>
<pre id="out">Ready.</pre>
<script>
async function run() {
  const body = {
    seed: Number(document.getElementById('seed').value),
    n_threats: Number(document.getElementById('threats').value),
    n_defenders: Number(document.getElementById('defenders').value),
    n_assets: 2,
    n_sensors: 3
  };
  const r = await fetch('/compare', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)
  });
  document.getElementById('out').textContent = JSON.stringify(await r.json(), null, 2);
}
</script>
</body>
</html>
"""


def build_policy(name):
    if name == "hungarian":
        return HungarianPolicy()
    if name in BASELINE_POLICIES:
        return BASELINE_POLICIES[name]()
    raise ValueError(f"Unknown policy: {name}")


@app.post("/simulate")
def simulate(req: SimRequest):
    gen = ScenarioGenerator()
    scenario = gen.generate(
        seed=req.seed,
        n_threats=req.n_threats,
        n_defenders=req.n_defenders,
        n_assets=req.n_assets,
        n_sensors=req.n_sensors,
    )
    policy = build_policy(req.policy)
    return Simulator.evaluate_policy(scenario, policy).as_dict()


@app.post("/compare")
def compare(req: SimRequest):
    gen = ScenarioGenerator()
    base = gen.generate(
        seed=req.seed,
        n_threats=req.n_threats,
        n_defenders=req.n_defenders,
        n_assets=req.n_assets,
        n_sensors=req.n_sensors,
    )
    names = list(BASELINE_POLICIES.keys()) + ["hungarian"]
    out = {}
    for name in names:
        out[name] = Simulator.evaluate_policy(
            gen.clone(base),
            build_policy(name),
        ).as_dict()
    return out
