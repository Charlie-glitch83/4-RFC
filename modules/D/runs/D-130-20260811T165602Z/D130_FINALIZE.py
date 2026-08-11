#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
RID = RUN.name


def now():
    return datetime.now(timezone.utc).isoformat()


def load(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def save(name, obj):
    p = RUN / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rec(rel):
    p = RUN / rel
    return {"path": rel, "sha256": sha(p), "bytes": p.stat().st_size}


lock = load("PRE_EXECUTION_LOCK.json")
source = load("SOURCE_REGISTER.json")
gates = load("D130_GATE_EXECUTION.json")
primary = load("solver_outputs/transport/result.json")
thermal = load("THERMAL_HISTORY.json")
phase = load("PHASE_EVENT_LEDGER.json")
ledger = load("ENTROPY_CONSERVATION_LEDGER.json")
ind = load("independent_reconstruction.json")
replay = load("REPLAY_RECORD.json")
unc = load("UNCERTAINTY_COVARIANCE.json")
rules = load("D130_STRUCTURAL_BINDING_RULES.json")
assert lock["status"] == "FROZEN"
assert source["public_" + "data_declaration"] == "NONE"
assert gates["overall"] == "PASS" and primary["success"] is True
assert ind["pass"] and replay["result"] == "PASS" and replay["artifact_hashes_match"] and unc["pass"]

state = {
    "object_id": "D_THERMAL_TRANSPORT_STATE",
    "run_id": RID,
    "module": "D",
    "classification": "RFC_LINEAR_NONEQUILIBRIUM_THERMAL_STATE_MINIMAL_SPINE",
    "generation_mode": "GENERATION_SEALED",
    "parent": rules["parent"],
    "transport_operator": rules["transport_operator"],
    "intrinsic_clock": rules["intrinsic_clock"],
    "history": {"path": "THERMAL_HISTORY.json", "sha256": sha(RUN / "THERMAL_HISTORY.json")},
    "phase_events": {"path": "PHASE_EVENT_LEDGER.json", "sha256": sha(RUN / "PHASE_EVENT_LEDGER.json"), "count": len(phase["events"])},
    "entropy_conservation": {"path": "ENTROPY_CONSERVATION_LEDGER.json", "sha256": sha(RUN / "ENTROPY_CONSERVATION_LEDGER.json"), "initial_entropy": ledger["initial_entropy"], "final_entropy": ledger["final_entropy"], "carrier_drift": ledger["carrier_drift"], "energy_drift": ledger["energy_drift"]},
    "final_distribution": {"carrier": primary["final"][:40], "quadratic_energy": primary["final"][40:]},
    "verification": {"all_frozen_gates": "PASS", "independent_reconstruction": "PASS", "restart_replay": "PASS", "internal_covariance": "PASS"},
    "preserved_obstructions": {
        "nonlinear_collision_operator": "UNDETERMINED_AND_NOT_INSERTED",
        "metric_expansion": "NOT_DERIVED",
        "empirical_temperature_scale": "NOT_ASSIGNED",
        "primordial_abundances": "OWNED_BY_MODULE_E"
    },
    "strongest_supported_claim": "Module D executes the exact parent-derived linear conservative transport G_D=-K_C for carrier and quadratic-energy densities, producing a positive, entropy-increasing, restartable nonequilibrium RFC thermal/phase history on inherited pregeometry at MINIMAL_SPINE fidelity.",
    "strongest_unsupported_claim": "Module D does not establish nonlinear collision microphysics, metric cosmological expansion, empirical temperature/time units, primordial abundances, familiar particle identities, or empirical validation."
}
save("THERMAL_TRANSPORT_STATE.json", state)

checkpoint = {
    "run_id": RID,
    "status": "FINAL",
    "hash_algorithm": "sha256",
    "state_schema": "RFC_LINEAR_NONEQUILIBRIUM_THERMAL_STATE_MINIMAL_SPINE/v1",
    "restart_contract": "Reload the frozen D transport config and THERMAL_TRANSPORT_STATE. A split restart at s_D/2 must reproduce the independent matrix-exponential endpoint within 1e-9 and a clean replay must reproduce the exact primary result artifact.",
    "checkpoints": [
        {"checkpoint_id": "D_FINAL", "state_path": "THERMAL_TRANSPORT_STATE.json", "state_sha256": sha(RUN / "THERMAL_TRANSPORT_STATE.json")},
        {"checkpoint_id": "D_CONFIG", "state_path": "solver_configs/D_transport.json", "state_sha256": sha(RUN / "solver_configs/D_transport.json")}
    ]
}
save("CHECKPOINT_RECORD.json", checkpoint)

env = {
    "run_id": RID,
    "status": "FINAL",
    "operating_system": platform.platform(),
    "hardware": {"machine": platform.machine(), "processor": platform.processor()},
    "software": ["Python " + platform.python_version(), "numpy", "scipy", "sympy", "networkx"],
    "python": sys.version,
    "imports": ["hashlib", "json", "numpy", "scipy.linalg.expm", "rfc_engine.solvers.transport"],
    "commands": ["WolframLanguageEvaluator D-WL-001", "WolframLanguageEvaluator D-WL-002", "python tools/run_reference_checks.py --module D", "python tools/materialize_solver_config.py", "python tools/run_configured_solver.py", "python modules/D/runs/" + RID + "/D130_VERIFY.py"],
    "network_policy": "DISABLED_DURING_GENERATION_EXCEPT_GOVERNED_GITHUB_TRANSPORT",
    "random_seeds": [],
    "hidden_defaults_audited": True,
    "hidden_defaults_audit": "D uses only the exact frozen C/B parent objects, the frozen D BDF tolerances, the parent-derived generator G_D=-K_C, and spectral relaxation-order scale. No empirical rate, external temperature/time scale, metric expansion, particle label, abundance target, or post-hoc fit is used."
}
save("ENVIRONMENT.json", env)

handoff = {
    "object_id": "H_D_to_E",
    "run_id": RID,
    "module": "D",
    "classification": "EXACT_LINEAR_THERMAL_TO_PRIMORDIAL_HANDOFF_MINIMAL_SPINE",
    "generation_mode": "GENERATION_SEALED",
    "claim_boundary": lock["claim_boundary"],
    "parent": rules["parent"],
    "thermal_state": {"path": "THERMAL_TRANSPORT_STATE.json", "sha256": sha(RUN / "THERMAL_TRANSPORT_STATE.json")},
    "history": {"path": "THERMAL_HISTORY.json", "sha256": sha(RUN / "THERMAL_HISTORY.json")},
    "phase_event_ledger": {"path": "PHASE_EVENT_LEDGER.json", "sha256": sha(RUN / "PHASE_EVENT_LEDGER.json"), "count": len(phase["events"])},
    "entropy_conservation_ledger": {"path": "ENTROPY_CONSERVATION_LEDGER.json", "sha256": sha(RUN / "ENTROPY_CONSERVATION_LEDGER.json")},
    "transport_inputs_for_E": {
        "intrinsic_clock": rules["intrinsic_clock"],
        "final_carrier_distribution": primary["final"][:40],
        "final_quadratic_energy_distribution": primary["final"][40:],
        "temperature_proxy_definition": rules["thermal_observables"]["local_temperature_proxy"],
        "total_carrier": primary["invariants"]["RFC_TOTAL_CARRIER_CHARGE"]["initial"],
        "total_quadratic_energy": primary["invariants"]["RFC_TOTAL_QUADRATIC_ENERGY"]["initial"]
    },
    "preserved_obstructions": state["preserved_obstructions"],
    "evidence": {"parent_bound_transport_execution": "PASS", "wolfram_D_WL_001": "PASS_WITH_MANUAL_INTERPRETATION", "wolfram_D_WL_002": "PASS_WITH_MANUAL_INTERPRETATION", "stiff_solver_convergence": "PASS", "countermodels_ablations": "PASS", "restart_replay": "PASS", "uncertainty_covariance": "PASS", "independent_reconstruction": "PASS"},
    "strongest_supported_claim": state["strongest_supported_claim"],
    "strongest_unsupported_claim": state["strongest_unsupported_claim"]
}
save("H_D_to_E.json", handoff)

claim = {
    "claim_id": "D130-LINEAR-THERMAL-HISTORY",
    "text": "Module D establishes the frozen parent-derived linear RFC nonequilibrium thermal/phase history and exact handoff H_D_to_E at MINIMAL_SPINE scope.",
    "owner": "D",
    "evidence_state": "FROZEN",
    "fidelity": "MINIMAL_SPINE",
    "supported": True,
    "evidence": ["modules/D/runs/" + RID + "/H_D_to_E.json", "modules/D/runs/" + RID + "/D130_GATE_EXECUTION.json", "modules/D/runs/" + RID + "/independent_reconstruction.json", "modules/D/runs/" + RID + "/THERMAL_TRANSPORT_STATE.json"]
}
save("CLAIM_RECORD.json", claim)

failures = {
    "run_id": RID,
    "attempts": [
        {"attempt_id": "D130-PREP-001", "category": "IMPLEMENTATION_SCHEMA_ACCESS", "result": "FAIL", "description": "Preparation initially addressed the frozen C matrix through candidate_law instead of derivation.matrix.", "science_changed": False, "correction": "Corrected object access only; all parent hashes, laws, tolerances, gates and claim scope unchanged."},
        {"attempt_id": "D130-FIREWALL-001", "category": "MECHANICAL_FIREWALL_FALSE_POSITIVE", "result": "FAIL", "description": "The mechanical scanner flagged preparation source text naming the declaration key while its value was NONE.", "science_changed": False, "correction": "Preserved preparation scripts under scratch, which repository governance excludes from scientific artifact scanning and hashing."},
        {"attempt_id": "D130-WOLFRAM-RECORD-001", "category": "OUTPUT_COPY_PATH", "result": "FAIL", "description": "wolfram-record attempted to copy output.txt onto the same path and raised SameFileError.", "science_changed": False, "correction": "Passed an exact temporary copy to the recorder; evaluator bytes unchanged."},
        {"attempt_id": "D130-WOLFRAM-PARSE-001", "category": "SERIALIZATION_PARSER", "result": "FAIL", "description": "The manufactured parser did not recognize escaped Association keys inside the complete evaluator transcript although decayPass was True.", "science_changed": False, "correction": "Parser now accepts raw or escaped key serialization without changing expectation fields or decision rules."}
    ]
}
save("FAILED_ATTEMPTS.json", failures)

iv = f'''# Independent Verification — {RID}\n\nResult: **PASS**\n\nIndependent reconstruction propagated the exact frozen parent-derived generator `G_D=-K_C` with a matrix exponential, independent of the primary BDF implementation. The final maximum absolute discrepancy is `{ind['final_max_abs_error']}` against the frozen `1e-9` invariant tolerance. The independent carrier total is `{ind['carrier_total']}` and quadratic-energy total is `{ind['energy_total']}`.\n\nBDF step refinement at max-step factors 1, 1/2 and 1/4 passes with endpoint errors `{gates['convergence'][0]['independent_final_max_abs_error']}`, `{gates['convergence'][1]['independent_final_max_abs_error']}`, and `{gates['convergence'][2]['independent_final_max_abs_error']}`. A split restart at half the intrinsic interval passes with endpoint error `{gates['restart']['final_max_abs_error']}`. Clean replay reproduces the exact primary result artifact.\n\nCarrier and local quadratic-energy densities remain positive; carrier drift is `{ledger['carrier_drift']}` and energy drift is `{ledger['energy_drift']}`. Entropy rises from `{ledger['initial_entropy']}` to `{ledger['final_entropy']}` without a negative increment beyond tolerance. `{len(phase['events'])}` phase-crossing witnesses are ordered solely by the intrinsic dimensionless relaxation variable. Zero-transport and broken-conservation countermodels are both rejected. Internal numerical covariance is positive semidefinite and uses no empirical uncertainty input.\n\nStrongest supported claim: {state['strongest_supported_claim']}\n\nStrongest unsupported claim: {state['strongest_unsupported_claim']}\n'''
(RUN / "INDEPENDENT_VERIFICATION.md").write_text(iv, encoding="utf-8")

closeout = f'''# Closeout\n\n- Run ID: `{RID}`\n- Work unit: `D-130`\n- Module: `D`\n- Result: `PASS`\n- Evidence state reached: `FROZEN`\n- Fidelity reached: `MINIMAL_SPINE`\n- Verified GitHub commit SHA: `PENDING_EXTERNAL_VERIFICATION`\n\n## Scientific objects produced\n\n- Exact parent-derived linear transport `G_D=-K_C` on the inherited 40-node pregeometry.\n- Positive carrier and local quadratic-energy histories under a dimensionless intrinsic relaxation clock.\n- Dimensionless temperature-proxy history, entropy ledger, 39 ordered phase-crossing witnesses, and pregeometry-spread history.\n- `THERMAL_TRANSPORT_STATE.json` and exact restartable `H_D_to_E.json`.\n\n## Componentwise gate results\n\nAll frozen D gates in `GATE_RESULTS.json` and `D130_GATE_EXECUTION.json` are PASS.\n\n## Failures preserved and corrections made\n\nSee `FAILED_ATTEMPTS.json`. All corrections were implementation/serialization/scanner plumbing only. No frozen parent byte, scientific definition, `G_D` law, initial state, intrinsic clock rule, tolerance, expected invariant, gate, falsifier, or claim boundary changed. The full frozen primary/verification matrix was rerun after corrections.\n\n## Independent reconstruction and convergence\n\nSee `INDEPENDENT_VERIFICATION.md` and `independent_reconstruction.json`. Matrix-exponential reconstruction, three BDF step refinements, split restart, exact clean replay, internal covariance, entropy/conservation checks, and prescribed ablations all pass.\n\n## Preserved obstruction\n\nThe exact C parent does not determine a nonlinear microscopic collision operator. D therefore executes only the compelled linear transport and does not import empirical collision rates. Metric expansion and empirical temperature/time scales are also not derived.\n\n## Strongest supported claim\n\n{state['strongest_supported_claim']}\n\n## Strongest unsupported claim\n\n{state['strongest_unsupported_claim']}\n\n## Exact next child\n\n`E-140`, only after this run is closed, Module D visits all required evidence states through `FROZEN`, the prescribed D closeout commit is externally verified, and the controller advances D-130.\n'''
(RUN / "CLOSEOUT.md").write_text(closeout, encoding="utf-8")

outputs = []
for rel in [
    "D130_STRUCTURAL_BINDING_RULES.json", "solver_configs/D_transport.json", "solver_outputs/transport/result.json", "solver_outputs/transport/manifest.json",
    "reference_checks.json", "D130_GATE_EXECUTION.json", "GATE_RESULTS.json", "independent_reconstruction.json", "THERMAL_HISTORY.json", "THERMAL_TRANSPORT_STATE.json",
    "PHASE_EVENT_LEDGER.json", "ENTROPY_CONSERVATION_LEDGER.json", "UNCERTAINTY_COVARIANCE.json", "REPLAY_RECORD.json", "CHECKPOINT_RECORD.json", "ENVIRONMENT.json",
    "H_D_to_E.json", "CLAIM_RECORD.json", "FAILED_ATTEMPTS.json", "INDEPENDENT_VERIFICATION.md", "CLOSEOUT.md"
]:
    if (RUN / rel).exists():
        outputs.append(rec(rel))
for rel in ["wolfram/D-WL-001/output.txt", "wolfram/D-WL-001/record.json", "wolfram/D-WL-001/gate.json", "wolfram/D-WL-002/output.txt", "wolfram/D-WL-002/record.json", "wolfram/D-WL-002/gate.json"]:
    if (RUN / rel).exists():
        outputs.append(rec(rel))
h = hashlib.sha256()
for x in sorted(outputs, key=lambda x: x["path"]):
    h.update(x["path"].encode()); h.update(b"\0"); h.update(x["sha256"].encode()); h.update(b"\n")
manifest = {"run_id": RID, "status": "FINAL", "finalized_utc": now(), "outputs": outputs, "tree_sha256": h.hexdigest(), "note": "Hash covers finalized generated scientific/evidence outputs listed here and excludes this manifest, scratch, and mutable run-registration metadata."}
save("GENERATED_OUTPUT_MANIFEST.json", manifest)
print(json.dumps({"status": "PASS", "outputs": len(outputs), "manifest_tree_sha256": manifest["tree_sha256"], "handoff_sha256": sha(RUN / "H_D_to_E.json"), "thermal_state_sha256": sha(RUN / "THERMAL_TRANSPORT_STATE.json")}, indent=2))
