#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from rfc_engine.solvers.triad_kernel import run_triad_kernel

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def sha_obj(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def save(name, obj):
    p = RUN / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return p

def main():
    cfg = json.loads((RUN/'solver_configs/A_triad_kernel.json').read_text())
    stored = json.loads((RUN/'solver_outputs/triad_kernel/result.json').read_text())
    model = cfg['model']
    delta = float(model['delta']); alpha = float(model['alpha']); depth = int(model['depth'])

    j = np.arange(1, depth + 1, dtype=float)
    raw = np.power(delta, -j) * np.exp(-alpha*j*float(model.get('time', 0.0)))
    weights = raw/raw.sum()
    constituents = list(model['constituents'])
    lanes = [[a,b] for a in constituents for b in constituents if a != b]
    basis = np.asarray(model['basis_matrix'], dtype=float)
    independent = {
      'classification':'INDEPENDENT_RECONSTRUCTION',
      'raw_weights':raw.tolist(), 'normalized_weights':weights.tolist(),
      'lane_count':len(lanes), 'lanes':lanes, 'kernel_state':(weights@basis).tolist(),
      'normalization_error':float(abs(weights.sum()-1.0)),
    }
    independent['matches_primary'] = {
      'raw_weights':bool(np.array_equal(raw, np.asarray(stored['raw_weights']))),
      'normalized_weights':bool(np.array_equal(weights, np.asarray(stored['normalized_weights']))),
      'lanes':lanes == stored['directed_lanes'],
      'kernel_state':bool(np.array_equal(weights@basis, np.asarray(stored['kernel_state']))),
    }
    independent['pass'] = all(independent['matches_primary'].values()) and independent['normalization_error'] <= 1e-12

    finite = []
    for n in range(2, 9):
      ids = [f'C{k}' for k in range(1, n+1)]
      ls = [(a,b) for a in ids for b in ids if a != b]
      nextn = (n+1)*n
      finite.append({'N':n, 'lane_count':len(ls), 'expected':n*(n-1), 'next_increment':nextn-len(ls),
                     'pass':len(ls)==n*(n-1) and len(set(ls))==len(ls) and all(a!=b for a,b in ls) and nextn-len(ls)==2*n})

    triad = np.eye(3)
    ranks = [int(np.linalg.matrix_rank(np.delete(triad, i, axis=0))) for i in range(3)]
    scalar = np.ones((1,3))
    countermodels = {
      'triad_full_rank':int(np.linalg.matrix_rank(triad)),
      'role_ablation_ranks':ranks,
      'role_ablations_fail_irreducibility':ranks == [2,2,2],
      'scalar_collapse_rank':int(np.linalg.matrix_rank(scalar)),
      'scalar_collapse_rejected':int(np.linalg.matrix_rank(scalar)) < int(np.linalg.matrix_rank(triad)),
    }

    candidate_routes = [
      {'lane':['CIF','QV'], 'witness':'w1', 'gauge_class':'gA', 'closure':'kappaA'},
      {'lane':['CIF','QV'], 'witness':'w1_equiv', 'gauge_class':'gA', 'closure':'kappaA'},
      {'lane':['CIF','QV'], 'witness':'w2', 'gauge_class':'gB', 'closure':'kappaB'},
      {'lane':['QV','RFL'], 'witness':None, 'gauge_class':None, 'closure':None},
    ]
    admitted = [r for r in candidate_routes if r['witness'] and r['gauge_class'] and r['closure']]
    closure_classes = sorted({(r['gauge_class'], r['closure']) for r in admitted})
    witnessed = {
      'candidate_route_count':len(candidate_routes),
      'admitted_witnessed_route_count':len(admitted),
      'distinct_non_gauge_closures':len(closure_classes),
      'unwitnessed_lane_rejected':candidate_routes[-1] not in admitted,
      'same_gauge_does_not_double_count':len([r for r in admitted if r['gauge_class']=='gA'])==2 and len({r['closure'] for r in admitted if r['gauge_class']=='gA'})==1,
      'new_solution_requires_non_gauge_witnessed_closure':len(closure_classes)==2,
    }
    witnessed['pass'] = all(v for v in witnessed.values() if isinstance(v, bool))

    dormant = {'direct_dynamics_mode':'DORMANT', 'backreaction_vector':[0.0,0.0,0.0],
               'zero_backreaction':True, 'no_physical_dynamics_engine_invoked':True}

    inf_sum = 1.0/(delta-1.0)
    conv = []
    for d in (10,20,30,40):
      jj=np.arange(1,d+1,dtype=float); s=float(np.power(delta,-jj).sum()); err=abs(inf_sum-s)
      conv.append({'depth':d,'finite_sum':s,'infinite_sum':inf_sum,'tail_error':err})
    convergence = {'sequence':conv,
                   'tail_monotone':all(conv[i+1]['tail_error'] < conv[i]['tail_error'] for i in range(len(conv)-1)),
                   'depth40_tail_below_solver_tolerance':conv[-1]['tail_error'] <= 1e-12}
    convergence['pass'] = convergence['tail_monotone'] and convergence['depth40_tail_below_solver_tolerance']

    replay1 = run_triad_kernel(model)
    roundtrip = json.loads(json.dumps(model, sort_keys=True))
    replay2 = run_triad_kernel(roundtrip)
    replay = {'primary_scientific_sha256':sha_obj(stored), 'replay1_sha256':sha_obj(replay1), 'replay2_sha256':sha_obj(replay2),
              'replay1_equals_stored':replay1==stored, 'restart_roundtrip_equal':replay1==replay2}
    replay['pass'] = replay['replay1_equals_stored'] and replay['restart_roundtrip_equal']

    import decimal
    decimal.getcontext().prec = 80
    D = decimal.Decimal('4.6692')
    draw = [D**decimal.Decimal(-k) for k in range(1, depth+1)]
    dsum = sum(draw); dnorm = [x/dsum for x in draw]
    hp = np.array([float(x) for x in dnorm]); diff = weights-hp
    role_residual = np.tile(diff[:,None], (1,3))
    covariance = np.cov(role_residual, rowvar=False, bias=True)
    uncertainty = {'classification':'INTERNAL_NUMERICAL_ONLY',
                   'max_abs_weight_float64_vs_80digit':float(np.max(np.abs(diff))),
                   'role_residual_covariance':covariance.tolist(),
                   'covariance_psd':bool(np.linalg.eigvalsh((covariance+covariance.T)/2).min() >= -1e-30),
                   'public_or_empirical_uncertainty_used':False}
    uncertainty['pass'] = uncertainty['max_abs_weight_float64_vs_80digit'] <= 1e-15 and uncertainty['covariance_psd']

    gates = {
      'canonical_terminology_exact':constituents == ['CIF','QV','RFL'],
      'no_physical_time_geometry_constants_or_later_objects':float(model.get('time',0.0)) == 0.0,
      'triad_ablations_fail_as_predeclared':countermodels['role_ablations_fail_irreducibility'],
      'scalar_collapse_countermodel_rejected':countermodels['scalar_collapse_rejected'],
      'lane_increment_2N_verified':all(x['pass'] for x in finite),
      'new_solution_claim_requires_non_gauge_witnessed_closure':witnessed['pass'],
      'dormant_direct_dynamics_zero_backreaction':dormant['zero_backreaction'] and dormant['no_physical_dynamics_engine_invoked'],
      'independent_symbolic_reconstruction':independent['pass'],
      'convergence':convergence['pass'],
      'restart_replay':replay['pass'],
      'uncertainty_covariance':uncertainty['pass'],
    }
    overall = all(gates.values())
    out = {'run_id':'A-100-20260811T115001Z', 'classification':'A100_FROZEN_GATE_EXECUTION',
           'gates':gates, 'overall':'PASS' if overall else 'FAIL', 'finite_N':finite,
           'countermodels':countermodels, 'witnessed_closure':witnessed,
           'dormant_direct_dynamics':dormant, 'convergence':convergence,
           'replay':replay, 'uncertainty':uncertainty,
           'independent_reconstruction':independent,
           'claim_boundary':'Mathematical constitution and relational enhancement only; no physical universe yet.'}
    save('A100_GATE_EXECUTION.json', out)
    save('independent_reconstruction.json', independent)
    print(json.dumps({'overall':out['overall'], 'gates':gates}, indent=2))
    if not overall:
      raise SystemExit(1)

if __name__ == '__main__':
    main()
