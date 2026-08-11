# K–L–M Physical Input Gap

## Current evidence state

```text
K/L/M constitutive laws: FORMALIZED
Representative module checks: VERIFIED
K–L–M F0 reduced recurrence: PHYSICALLY EXECUTED AT REDUCED SYNTHETIC SCOPE
F1–F4 physical K–L–M recurrence: NOT EXECUTED
Certified (K*,L*,M*) parent: ABSENT
Module N physical execution: BLOCKED
```

## Missing exact inputs

The repository and project library do not contain instantiated, source-locked physical packets for:

- `K^(0)` nonlinear particle/field/metric state;
- `L^(0)` gas, stellar, compact-object, radiation, and feedback state;
- `M^(0)` isotope, chemical, dust, cooling, opacity, and event-yield state;
- time-resolved K/L/M return fields and changed-domain markers;
- field-, object-, event-, route-, and branch-level covariance;
- metric, Weyl, lightcone, ray/Jacobi, lens-plane, map, spectrum, and correlation states;
- solver executables or reproducible F1–F4 configurations capable of evolving those packets;
- full replay ledger and independent full-chain reconstruction.

The existing files define laws, interfaces, schemas, representative identities, and synthetic checks. They are not substitutes for these physical states.

## Required next execution ladder

1. Instantiate the frozen Module J realization consumed by K.
2. Execute K at the required nonlinear fidelity to create `K^(0)`.
3. Execute L on the exact K parent to create `L^(0)` and the baryonic return.
4. Replay K to create the current-composition baryonic state.
5. Execute M on the exact stellar/event trajectories to create `M^(0)`.
6. Return composition, dust, cooling, opacity, radioactive, and stress-energy fields to K/L.
7. Replay only the earliest causally changed K/L/M interval.
8. Iterate componentwise until fixed point, cycle, attractor, lawful branch family, or explicit nonconvergence is established.
9. Regenerate metric, lightcones, optical routes, maps, spectra, correlations, and covariance.
10. Independently reproduce the full chain and seal the physical K–L–M certificate.

## Nonnegotiable boundary

No synthetic reduced state, analytic toy model, representative finite check, or stable abundance vector may be renamed as the physical `(K*,L*,M*)` universe. Public data may not generate missing inputs, choose a branch, or tune replay.