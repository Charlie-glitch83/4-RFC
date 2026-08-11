# Independent Verification — REC-040

## Inputs reconstructed

- Exact 2-RFC Module L commit `b0f21d023f64ce9c70fd4755dfdbb7357b9f7a10` and its science, proof, and verification objects.
- Exact 2-RFC K-L-M F0 commit `3dff7f9626759500b708f2fd905df01509ca8c9e` and its certificate, configuration, archived executors, and result.
- Existing 4-RFC canonical source manifest for P29, P30, revised N-body proof, and revised N-body metadata.

## Methods independent from primary execution

Module L was checked by a separate finite reconstruction of representative mass conservation, pair momentum exchange, matter-radiation exchange, stoichiometric conservation, star-birth mass ledger, the analytic `n=1` Lane-Emden identity, positive-semidefinite covariance, and a contractive toy K-L-M map. These representative checks passed. This does not reproduce a full physical baryonic universe.

The two exact archived F0 Python executors were independently rerun in a fresh Python/NumPy environment. Both reached `FIXED_POINT_F0` at 17660 iterations with zero restart residual and zero local causal-replay residual. The replayed final-state serialization reproduced the archived final-state SHA-256 `a8bc1eb5902a063a026bdc216fd0611661b7cb7c9f3f52c647a5acbc98b01053`.

## Results

- Exact candidate commits and paths: PASS.
- Module L representative finite reconstruction: PASS at declared representative scope.
- F0 final state and qualitative classification: reproduced.
- F0 restart and causal replay: reproduced with residual 0.
- F0 local linearization: spectral radius `0.9999999999999905`, two neutral modes, quotient radius `0.9989537534312668`.
- Public-data generation influence: none detected or used.
- Old PASS/state promotion: none.

## Disagreements

The archived F0 result records iteration-ledger SHA-256 `339884013a8cc4076bdb07c2b226ccafb83cad26ec3f44a25fe4e91b1f0b09bb`. Replaying the exact archived `klm_f0_execution.py` produced `b43da955f4d6a5e4ad06ce59a63a9ac63fa648e1c07e44036df2c41b415c7079`; replaying the exact archived `klm_f0_reduced.py` produced `f4beefb5eb6d44d983c35e721ad2f6b69ef916151193bc6270ed239e3c499111`. The mismatch is preserved as a reproducibility defect and prevents F0 from being promoted beyond comparison/regression use.

## Verdict

**PASS for REC-040 recovery classification.** The gate passes because discrepancies are preserved and the affected objects are not promoted. Module L is retained only as `REPLAY_REQUIRED` formal/representative material until an exact 4-RFC K parent is physically executed. F0 is `COMPARISON_ONLY`. No recovered 2-RFC object becomes a new physical parent, and no old completion label is inherited.
