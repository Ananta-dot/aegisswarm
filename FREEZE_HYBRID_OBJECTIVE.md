# Hybrid Objective Confirmation Gate

The reserved confirmation block `8000-8399` must not be evaluated while development is still active.

After development results are reviewed and the architecture/hyperparameters are explicitly frozen, edit:

```json
"architecture_frozen": true
```

in `artifacts/hybrid_objective_dev/protocol.json` before running confirmation.

This manual gate is intentional: confirmation is not part of the development loop.
