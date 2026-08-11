# Independent Verification — D-130-20260811T165602Z

Result: **PASS**

Independent reconstruction propagated the exact frozen parent-derived generator `G_D=-K_C` with a matrix exponential, independent of the primary BDF implementation. The final maximum absolute discrepancy is `1.1796119636642288e-14` against the frozen `1e-9` invariant tolerance. The independent carrier total is `0.999999999999942` and quadratic-energy total is `0.02949580130352957`.

BDF step refinement at max-step factors 1, 1/2 and 1/4 passes with endpoint errors `1.1796119636642288e-14`, `2.5951463200613034e-15`, and `2.8102520310824275e-15`. A split restart at half the intrinsic interval passes with endpoint error `2.924398223580482e-11`. Clean replay reproduces the exact primary result artifact.

Carrier and local quadratic-energy densities remain positive; carrier drift is `6.661338147750939e-16` and energy drift is `2.42861286636753e-17`. Entropy rises from `0.9008810516855332` to `3.546531515944081` without a negative increment beyond tolerance. `39` phase-crossing witnesses are ordered solely by the intrinsic dimensionless relaxation variable. Zero-transport and broken-conservation countermodels are both rejected. Internal numerical covariance is positive semidefinite and uses no empirical uncertainty input.

Strongest supported claim: Module D executes the exact parent-derived linear conservative transport G_D=-K_C for carrier and quadratic-energy densities, producing a positive, entropy-increasing, restartable nonequilibrium RFC thermal/phase history on inherited pregeometry at MINIMAL_SPINE fidelity.

Strongest unsupported claim: Module D does not establish nonlinear collision microphysics, metric cosmological expansion, empirical temperature/time units, primordial abundances, familiar particle identities, or empirical validation.
