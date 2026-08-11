# Independent Verification

## Inputs reconstructed
Exact 2-RFC Module L objects at `b0f21d023f64ce9c70fd4755dfdbb7357b9f7a10` and KLM F0 objects at `3dff7f9626759500b708f2fd905df01509ca8c9e` were fetched by commit and path. Existing P29/P30/N-body parents were resolved through the frozen 4-RFC source manifest and their SHA-256 values were recomputed.

## Methods independent from primary execution
Representative Module L conservation, exchange, thermochemical, covariance, and Lane-Emden identities were reconstructed independently in Python. The archived KLM reduced executor was replayed from its exact commit. No public observational target entered generation or classification.

## Results
- Module L representative reconstruction: PASS.
- KLM F0 mandatory invariants, restart, and causal replay: PASS.
- KLM F0 stored final-state SHA reproduced: `True`.
- KLM F0 stored iteration-ledger SHA reproduced: `False`.

## Disagreements
The F0 iteration-ledger hash does not reproduce and is preserved as a discrepancy. F0 remains `COMPARISON_ONLY`; the disagreement is not repaired by altering science or by promoting the result.

## Verdict
PASS at REC-040 recovery scope only. No old physical-completion state is inherited.
