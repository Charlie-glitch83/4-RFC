# K–L–M F0 Computational Certificate

## Scope

This certificate records execution of a constructed dimensionless reduced K–L–M recurrence derived from the frozen RFC constants and the declared causal order

```text
K(n) -> L(n) -> M(n) -> K(n+1)
```

It verifies recurrence orchestration, componentwise stopping, conservation, replay locality, restart, covariance propagation, independent reconstruction, and branch-classification machinery.

It is **not** a full nonlinear cosmological, hydrodynamic, stellar-evolution, isotope-network, metric/lightcone, or lensing execution. It does not constitute the required F1–F4 physical K–L–M parent and does not authorize Module N.

## Frozen inputs

The reduced map uses only the source-locked constants:

```text
delta = 4.6692
alpha = 0.0256831
nu = 0.00420784
epsilon = 0.000108071
lambda_normalized = 0.489442
w_QV = 0.984868
w_CIF = 0.005085
w_RFL = 0.010047
```

No public data or observed targets entered the recurrence.

## Protected state

The finite state contains:

```text
gas
stars
remnants
escaped
processed_fraction
dust_fraction
cooling
opacity
structure
metric
lensing
radiation
feedback
event_yield
```

Every protected component has its own stopping tolerance. No aggregate score overrides a failed component.

## Result

```text
classification: FIXED_POINT_F0
iterations: 17660
all mandatory F0 checks: PASS
final-state SHA-256:
a8bc1eb5902a063a026bdc216fd0611661b7cb7c9f3f52c647a5acbc98b01053
iteration-ledger SHA-256:
339884013a8cc4076bdb07c2b226ccafb83cad26ec3f44a25fe4e91b1f0b09bb
```

The final reduced state is recorded in `klm_f0_result.json`.

## Verified obligations

- mass conservation and positivity;
- bounded composition with dust as a subset of processed material;
- positive cooling and opacity;
- finite structure, metric, and lensing state;
- nonnegative radiation, feedback, and event-yield carriers;
- causal M-change replay through only affected K/L/M descendants;
- no mutation of Modules A–J;
- exact checkpoint/restart agreement;
- exact agreement with a separately written scalar implementation;
- positive-semidefinite propagated covariance;
- correct synthetic classification of fixed-point, period-two cycle, and divergent cases.

## Linearized classification

The full state contains two neutral conservation/accumulation directions. Therefore the certificate does not claim strict contraction of the entire coordinate state.

```text
full spectral radius: 0.9999999999999905
neutral modes: 2
quotient spectral radius: 0.9989537534312668
full state: nonexpansive
protected evolving quotient: locally contractive
```

## Replay result

A controlled perturbation to `M.processed_fraction` replayed only:

```text
M microphysics
-> K structure/metric/lensing
-> L gas/stars/feedback
-> M return
```

The local-replay and direct-forward results agreed exactly in the reduced system, and the upstream A–J mutation flag remained false.

## Claim boundary

This certificate establishes that the planned K–L–M recurrence and classification machinery is executable and internally consistent at F0 reduced scope.

It does **not** establish:

- an instantiated K^(0), L^(0), or M^(0) physical field state;
- F1 local resolved stellar/chemical replay;
- F2 zoom or F3 full-volume evolution;
- F4 independent full-physics reproduction;
- final metric, Weyl, lightcone, lensing-map, or full covariance closure;
- the physical `(K*,L*,M*)` parent required by Module N.

Module N therefore remains blocked pending the missing physical state and solver artifacts.