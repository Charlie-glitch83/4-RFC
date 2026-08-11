#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
RID = RUN.name
B_RUN = ROOT / 'modules/B/runs/B-110-20260811T140258Z'
B_CFG = B_RUN / 'solver_configs/B_big_implosion.json'
B_STATE = B_RUN / 'FIRST_PHYSICAL_STATE.json'
EXPECTED_B_CFG_SHA = '16a3761a6562944e36506104594f8ee6b3ba2189e70396a2ae22b1afa67e6076'
EXPECTED_B_STATE_SHA = 'f50c7e721c38dd9b63f2910f3a0ace399f1854e85cbdafaa9ce51649d40c073a'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

if sha(B_CFG) != EXPECTED_B_CFG_SHA:
    raise SystemExit('exact B solver config hash mismatch')
if sha(B_STATE) != EXPECTED_B_STATE_SHA:
    raise SystemExit('exact B first physical state hash mismatch')

bcfg = json.loads(B_CFG.read_text(encoding='utf-8'))['model']
bstate = json.loads(B_STATE.read_text(encoding='utf-8'))
delta = float(bcfg['delta'])
n = int(bcfg['node_count'])
if n != 40:
    raise SystemExit('frozen B parent node count changed')

L = np.zeros((n, n), dtype=float)
for i, j, w in bcfg['weighted_edges']:
    i, j, w = int(i), int(j), float(w)
    L[i, i] += w
    L[j, j] += w
    L[i, j] -= w
    L[j, i] -= w
K = L / (delta - 1.0)
R = np.fliplr(np.eye(n))
if np.linalg.norm(K - K.T) > 1e-12:
    raise SystemExit('derived microscopic generator is not symmetric')
if np.linalg.norm(R.T @ K @ R - K) > 1e-12:
    raise SystemExit('derived path-reflection symmetry failed')

evals, evecs = np.linalg.eigh(K)
if float(np.min(evals)) < -1e-12:
    raise SystemExit('derived microscopic generator is not positive semidefinite')
carrier = np.asarray(bstate['carrier_field']['values'], dtype=float)
coeff = evecs.T @ carrier
power = np.square(coeff)
pop = power / float(np.sum(power))
ledger = np.ones(n)
mode_ledger = evecs.T @ ledger

law = {
    'run_id': RID,
    'classification': 'PARENT_DERIVED_MICROSCOPIC_QUADRATIC_LAW',
    'generation_mode': 'GENERATION_SEALED',
    'parent': {
        'B_solver_config': str(B_CFG.relative_to(ROOT)),
        'B_solver_config_sha256': EXPECTED_B_CFG_SHA,
        'B_first_physical_state': str(B_STATE.relative_to(ROOT)),
        'B_first_physical_state_sha256': EXPECTED_B_STATE_SHA,
    },
    'derivation': {
        'operator_identity': 'K_C = Q_B^{-1} - I = L_B/(delta_B-1)',
        'matrix': K.tolist(),
        'reflection_generator': R.tolist(),
        'quadratic_form': 'E_C(x)=1/2 x^T K_C x = [2(delta_B-1)]^-1 Sum_(i,j in B edges) (x_i-x_j)^2',
        'selection_rule': 'Use the unique generator algebraically implied by the frozen B compression operator; no fitted or remembered coefficient is admitted.',
    },
    'microscopic_interpretation': {
        'basis': 'anonymous RFC spectral excitation modes on B pregeometry',
        'eigenvalues': evals.tolist(),
        'eigenvectors': evecs.tolist(),
        'gap_units': 'dimensionless parent-derived spectral gap; not an empirical mass assignment',
        'charge_ownership': 'The exact total-carrier ledger belongs to the zero mode; modes orthogonal to the constant carrier have zero total-ledger charge.',
        'mode_total_ledger_components': mode_ledger.tolist(),
        'nonlinear_interactions': 'UNDETERMINED_AT_C120; no nonlinear coupling is imported or inferred by resemblance.',
        'named_standard_model_correspondence': None,
    },
    'prethermal_state': {
        'parent_carrier': carrier.tolist(),
        'spectral_coefficients': coeff.tolist(),
        'population_rule': 'p_r=|v_r^T x_B|^2 / Sum_s |v_s^T x_B|^2',
        'populations': pop.tolist(),
        'population_sum': float(np.sum(pop)),
    },
    'invariants': {
        'symmetric': True,
        'positive_semidefinite': True,
        'reflection_invariant': True,
        'minimum_eigenvalue': float(np.min(evals)),
        'zero_mode_residual': float(np.linalg.norm(K @ np.ones(n))),
    },
}
law_path = RUN / 'C120_MICROSCOPIC_DERIVATION.json'
save(law_path, law)
law_sha = sha(law_path)

sheet_path = RUN / 'binding_sheets/C_spectral_model.bindings.json'
sheet = json.loads(sheet_path.read_text(encoding='utf-8'))
for rec in sheet['bindings']:
    rec['origin_kind'] = 'INTERNAL_DERIVATION'
    rec['origin_path'] = str(law_path.relative_to(ROOT))
    rec['origin_sha256'] = law_sha
    rec['module'] = 'C'
    rec['units'] = 'dimensionless'
    if rec['path'] == 'model.matrix':
        rec['value'] = K.tolist()
        rec['derivation_object'] = 'derivation.matrix'
        rec['dimensions'] = '40x40'
        rec['justification'] = 'Unique quadratic microscopic generator recovered algebraically from the exact frozen B compression operator.'
    elif rec['path'] == 'model.symmetry_generators':
        rec['value'] = [R.tolist()]
        rec['derivation_object'] = 'derivation.reflection_generator'
        rec['dimensions'] = '1x40x40'
        rec['justification'] = 'Exact automorphism of the frozen B path pregeometry; no external symmetry label is imposed.'
    else:
        raise SystemExit(f'unexpected binding path {rec["path"]}')
save(sheet_path, sheet)
print(json.dumps({'status': 'PASS', 'derivation_sha256': law_sha, 'minimum_eigenvalue': float(np.min(evals)), 'population_sum': float(np.sum(pop))}, indent=2))
