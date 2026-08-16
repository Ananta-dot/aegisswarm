# Optional upstream Axplorer integration

The core AegisSwarm repository does not require external Axplorer.

This folder exists only if we later want to run the exact upstream
`AxiomMath/axplorer` training loop.

The strategy representation used by AegisSwarm is deliberately compatible with
Axplorer's environment pattern:

- fixed `DataPoint.data`
- `calc_score()`
- `calc_features()`
- `local_search()`
- tokenizer `encode()/decode_batch()`

For the first research campaign, use the self-contained `train-axplorer` command.
Only move to the upstream adapter after the simulator/scoring contract is frozen.
