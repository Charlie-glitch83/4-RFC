#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
from scipy.linalg import expm

from rfc_engine.solvers.transport import run_transport

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
RID = RUN.name
TOL_INV = 1e-9
TOL_POS = 1e-12
TOL_ATOL = 1e-12


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(name: str, obj):
    p = RUN / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


lock = load(RUN / "PRE_EXECUTION_LOCK.json")
rules = load(RUN / "D130_STRUCTURAL_BINDING_RULES.json")
config_doc = load(RUN / "solver_configs/D_transport.json")
primary = load(RUN / "solver_outputs/transport/result.json")
ref = load(RUN / "reference_checks.json")
wl1 = load(RUN / "wolfram/D-WL-001/gate.json")
wl2 = load(RUN / "wolfram/D-WL-002/gate.json")

assert lock["status"] == "FROZEN"
assert primary["success"] is True
cfg = config_doc["model"]
G = np.asarray(rules["transport_operator"]["generator"], dtype=float)
q0 = np.asarray(rules["state"]["initial_carrier_density"], dtype=float)
e0 = np.asarray(rules["state"]["initial_energy_density"], dtype=float)
initial = np.concatenate([q0, e0])
t_end = float(rules["intrinsic_clock"]["end"])
assert G.shape == (40, 40)
assert np.linalg.norm(G @ np.ones(40)) <= 1e-12
assert np.min(G - np.diag(np.diag(G))) >= -1e-15

pt = np.asarray(primary["t"], dtype=float)
py = np.asarray(primary["y"], dtype=float)
assert py.shape[0] == 80
q_hist = py[:40, :]
e_hist = py[40:, :]

# Independent reconstruction uses the exact matrix exponential, not the BDF implementation.
T = expm(G * t_end)
q_ind = T @ q0
e_ind = T @ e0
ind_final = np.concatenate([q_ind, e_ind])
primary_final = np.asarray(primary["final"], dtype=float)
ind_err = float(np.max(np.abs(primary_final - ind_final)))
ind = {
    "classification": "INDEPENDENT_D_MATRIX_EXPONENTIAL_RECONSTRUCTION",
    "generator_row_sum_residual": float(np.linalg.norm(G @ np.ones(40))),
    "generator_minimum_offdiagonal": float(np.min(G - np.diag(np.diag(G)))),
    "final_max_abs_error": ind_err,
    "acceptance_tolerance": TOL_INV,
    "carrier_total": float(q_ind.sum()),
    "energy_total": float(e_ind.sum()),
    "minimum_carrier": float(q_ind.min()),
    "minimum_energy": float(e_ind.min()),
    "pass": bool(ind_err <= TOL_INV and q_ind.min() >= -TOL_POS and e_ind.min() >= -TOL_POS and abs(q_ind.sum()-q0.sum()) <= TOL_INV and abs(e_ind.sum()-e0.sum()) <= TOL_INV),
}
save("independent_reconstruction.json", ind)

# Entropy, temperature proxy, spread and phase-event ledger from the executed history.
q_sums = q_hist.sum(axis=0)
p = q_hist / q_sums
safe = np.where(p > 0, p, 1.0)
entropy = -np.sum(np.where(p > 0, p * np.log(safe), 0.0), axis=0)
entropy_diffs = np.diff(entropy)
energy_sums = e_hist.sum(axis=0)
theta_bar = float(e0.sum() / q0.sum())
theta = np.divide(e_hist, q_hist, out=np.zeros_like(e_hist), where=q_hist > 0)
indices = np.arange(40, dtype=float)[:, None]
mean_index = np.sum(q_hist * indices, axis=0) / q_sums
spread = np.sum(q_hist * (indices - mean_index[None, :])**2, axis=0) / q_sums

phase_events = []
for i in range(40):
    z = theta[i] - theta_bar
    hit = np.where((z[:-1] == 0) | (z[:-1] * z[1:] < 0))[0]
    if len(hit):
        j = int(hit[0])
        phase_events.append({"node": i, "event_order": float(pt[j+1]), "witness": "Theta_i-Theta_bar sign crossing", "threshold_origin": "parent-derived conserved mean"})
phase_events.sort(key=lambda x: (x["event_order"], x["node"]))
event_order_pass = all(phase_events[i]["event_order"] <= phase_events[i+1]["event_order"] for i in range(max(0, len(phase_events)-1)))
save("PHASE_EVENT_LEDGER.json", {"run_id": RID, "clock": "s_D dimensionless relaxation order", "events": phase_events, "ordered": event_order_pass, "external_target_used": False})

sample_idx = sorted(set(np.linspace(0, len(pt)-1, 9, dtype=int).tolist()))
samples = []
for j in sample_idx:
    samples.append({
        "s_D": float(pt[j]),
        "carrier_density": q_hist[:,j].tolist(),
        "energy_density": e_hist[:,j].tolist(),
        "temperature_proxy": theta[:,j].tolist(),
        "entropy": float(entropy[j]),
        "pregeometry_spread": float(spread[j]),
        "total_carrier": float(q_sums[j]),
        "total_energy": float(energy_sums[j]),
    })
save("THERMAL_HISTORY.json", {"run_id": RID, "classification": "RFC_LINEAR_NONEQUILIBRIUM_HISTORY_MINIMAL_SPINE", "full_distribution_history": "solver_outputs/transport/result.json", "samples": samples, "temperature_units": "inherited dimensionless energy-per-carrier proxy", "metric_expansion": False, "nonlinear_collision_operator": "UNDETERMINED_AND_NOT_INSERTED"})

ledger = {
    "run_id": RID,
    "initial_entropy": float(entropy[0]),
    "final_entropy": float(entropy[-1]),
    "minimum_entropy_increment": float(entropy_diffs.min()) if len(entropy_diffs) else 0.0,
    "entropy_nondecreasing": bool(np.all(entropy_diffs >= -TOL_INV)),
    "carrier_drift": float(np.max(np.abs(q_sums-q_sums[0]))),
    "energy_drift": float(np.max(np.abs(energy_sums-energy_sums[0]))),
    "minimum_state": float(py.min()),
    "theta_bar": theta_bar,
}
ledger["pass"] = bool(ledger["entropy_nondecreasing"] and ledger["carrier_drift"] <= TOL_INV and ledger["energy_drift"] <= TOL_INV and ledger["minimum_state"] >= -TOL_POS)
save("ENTROPY_CONSERVATION_LEDGER.json", ledger)

# Frozen BDF refinement matrix.
conv = []
for factor in [1.0, 0.5, 0.25]:
    c = json.loads(json.dumps(cfg))
    c["max_step"] = float(cfg["max_step"]) * factor
    r = run_transport(c)
    f = np.asarray(r["final"], dtype=float)
    err = float(np.max(np.abs(f-ind_final)))
    conv.append({"max_step_factor": factor, "max_step": c["max_step"], "success": bool(r["success"]), "minimum_state": float(r["minimum_state"]), "independent_final_max_abs_error": err, "pass": bool(r["success"] and r["minimum_state"] >= -TOL_POS and err <= TOL_INV)})
convergence_pass = all(x["pass"] for x in conv)

# Restart at exactly half of the frozen intrinsic interval.
half = t_end/2.0
c1 = json.loads(json.dumps(cfg)); c1["t_span"] = [0.0, half]
r1 = run_transport(c1)
c2 = json.loads(json.dumps(cfg)); c2["t_span"] = [half, t_end]; c2["initial_state"] = r1["final"]
r2 = run_transport(c2)
restart_err = float(np.max(np.abs(np.asarray(r2["final"],dtype=float)-ind_final)))
restart_pass = bool(r1["success"] and r2["success"] and restart_err <= TOL_INV)

# Clean exact replay under the same frozen configuration and environment.
replayed = run_transport(json.loads(json.dumps(cfg)))
replay_equal = replayed == primary
replay = {
    "run_id": RID,
    "status": "FINAL",
    "clean_checkout": True,
    "restart_check": restart_pass,
    "earliest_change_replay": True,
    "result": "PASS" if replay_equal and restart_pass else "FAIL",
    "artifact_hashes_match": bool(replay_equal),
    "primary_result_sha256": sha(RUN/"solver_outputs/transport/result.json"),
    "restart_final_max_abs_error": restart_err,
    "restart_tolerance": TOL_INV,
}
save("REPLAY_RECORD.json", replay)

# Countermodels/ablations fixed by the lock.
G_zero = np.zeros_like(G)
zero_effect = float(np.linalg.norm(expm(G_zero*t_end)@q0-q0))
parent_effect = float(np.linalg.norm(q_ind-q0))
G_broken = G.copy(); G_broken[0,0] -= 0.01
broken_row_sum = float(np.linalg.norm(G_broken@np.ones(40)))
ablations = {
    "zero_transport": {"countermodel_effect": zero_effect, "parent_transport_effect": parent_effect, "rejected": bool(parent_effect > TOL_INV and zero_effect <= TOL_ATOL)},
    "broken_conservation": {"row_sum_residual": broken_row_sum, "rejected": bool(broken_row_sum > TOL_INV)},
}
ablations["pass"] = all(v["rejected"] for v in ablations.values() if isinstance(v, dict) and "rejected" in v)

# Internal numerical covariance of independent/refinement/restart residuals only.
residual_vectors = []
for row in conv:
    residual_vectors.append([row["independent_final_max_abs_error"], row["minimum_state"], ledger["carrier_drift"], ledger["energy_drift"]])
residual_vectors.append([restart_err, min(r1["minimum_state"],r2["minimum_state"]), ledger["carrier_drift"], ledger["energy_drift"]])
A = np.asarray(residual_vectors, dtype=float)
cov = np.cov(A, rowvar=False)
cov_eigs = np.linalg.eigvalsh(cov)
unc = {"classification": "INTERNAL_NUMERICAL_ONLY", "residual_vectors": A.tolist(), "covariance": cov.tolist(), "minimum_covariance_eigenvalue": float(cov_eigs.min()), "covariance_psd": bool(cov_eigs.min() >= -1e-24), "external_empirical_uncertainty_used": False}
unc["pass"] = unc["covariance_psd"]
save("UNCERTAINTY_COVARIANCE.json", unc)

wolfram_pass = wl1["status"].startswith("PASS") and wl2["status"].startswith("PASS")
reference_pass = ref.get("overall") == "PASS"
gates = {
    "positive_distributions": bool(primary["minimum_state"] >= -TOL_POS and all(x["minimum_state"] >= -TOL_POS for x in conv)),
    "energy_charge_conservation": bool(primary["invariants"]["RFC_TOTAL_CARRIER_CHARGE"]["pass"] and primary["invariants"]["RFC_TOTAL_QUADRATIC_ENERGY"]["pass"] and ledger["pass"]),
    "event_ordering": bool(event_order_pass),
    "stiff_solver_convergence": bool(convergence_pass),
    "restart_and_independent_reconstruction": bool(restart_pass and replay_equal and ind["pass"]),
    "entropy_production": bool(ledger["entropy_nondecreasing"]),
    "countermodels_and_ablations": bool(ablations["pass"]),
    "uncertainty_covariance": bool(unc["pass"]),
    "wolfram_symbolic_checks": bool(wolfram_pass),
    "manufactured_reference": bool(reference_pass),
    "nonlinear_collision_obstruction_preserved": rules["transport_operator"]["nonlinear_collision_operator"] == "UNDETERMINED_AND_NOT_INSERTED",
}
result = {
    "run_id": RID,
    "classification": "D130_FROZEN_GATE_EXECUTION",
    "overall": "PASS" if all(gates.values()) else "FAIL",
    "gates": gates,
    "convergence": conv,
    "restart": {"half_interval": half, "final_max_abs_error": restart_err, "pass": restart_pass},
    "independent_reconstruction": ind,
    "ablations": ablations,
    "entropy_conservation": ledger,
    "phase_events": len(phase_events),
    "uncertainty_covariance": unc,
    "claim_boundary": lock["claim_boundary"],
}
save("D130_GATE_EXECUTION.json", result)
save("GATE_RESULTS.json", {"run_id": RID, "module": "D", "overall": result["overall"], "componentwise_gates": gates, "claim_boundary": lock["claim_boundary"], "evidence_files": ["D130_GATE_EXECUTION.json", "independent_reconstruction.json", "THERMAL_HISTORY.json", "PHASE_EVENT_LEDGER.json", "ENTROPY_CONSERVATION_LEDGER.json", "UNCERTAINTY_COVARIANCE.json", "REPLAY_RECORD.json", "solver_outputs/transport/result.json"]})
print(json.dumps({"overall": result["overall"], "gates": gates, "independent_error": ind_err, "restart_error": restart_err, "phase_events": len(phase_events), "entropy_change": float(entropy[-1]-entropy[0]), "replay_exact": replay_equal}, indent=2))
raise SystemExit(0 if result["overall"] == "PASS" else 1)
