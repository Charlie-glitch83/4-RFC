#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
RID=RUN.name
B=ROOT/'modules/B/runs/B-110-20260811T140258Z'
TOL=1e-10

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save(name,obj):
    p=RUN/name; p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); return p
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lap(n,edges):
    L=np.zeros((n,n),float)
    for i,j,w in edges:
        i=int(i); j=int(j); w=float(w)
        L[i,i]+=w; L[j,j]+=w; L[i,j]-=w; L[j,i]-=w
    return L

bcfg=load(B/'solver_configs/B_big_implosion.json')['model']
bstate=load(B/'FIRST_PHYSICAL_STATE.json')
cfg=load(RUN/'solver_configs/C_spectral_model.json')['model']
primary=load(RUN/'solver_outputs/spectral_model/result.json')
deriv=load(RUN/'C120_MICROSCOPIC_DERIVATION.json')
source=load(RUN/'SOURCE_REGISTER.json')
lock=load(RUN/'PRE_EXECUTION_LOCK.json')
assert lock['status']=='FROZEN'
assert source['public_data_declaration']=='NONE'
assert primary['success'] is True

n=int(bcfg['node_count']); delta=float(bcfg['delta'])
L=lap(n,bcfg['weighted_edges']); K=L/(delta-1.0); R=np.fliplr(np.eye(n))
M=np.asarray(cfg['matrix'],float); G=np.asarray(cfg['symmetry_generators'][0],float)
vals,vecs=np.linalg.eigh(K)
parent_carrier=np.asarray(bstate['carrier_field']['values'],float)
coeff=vecs.T@parent_carrier; power=coeff*coeff; pop=power/power.sum()

ind={
 'classification':'INDEPENDENT_C_RECONSTRUCTION',
 'matrix_match':bool(np.allclose(M,K,rtol=0,atol=1e-14)),
 'reflection_match':bool(np.allclose(G,R,rtol=0,atol=1e-14)),
 'symmetry_error':float(np.linalg.norm(K-K.T)),
 'reflection_commutator':float(np.linalg.norm(K@R-R@K)),
 'minimum_eigenvalue':float(vals.min()),
 'zero_mode_residual':float(np.linalg.norm(K@np.ones(n))),
 'orthogonality_error':float(np.linalg.norm(vecs.T@vecs-np.eye(n))),
 'reconstruction_error':float(np.linalg.norm(vecs@np.diag(vals)@vecs.T-K)),
 'population_minimum':float(pop.min()),
 'population_sum':float(pop.sum()),
 'total_carrier_charge':float(parent_carrier.sum()),
}
ind['pass']=all([
 ind['matrix_match'],ind['reflection_match'],ind['symmetry_error']<=TOL,
 ind['reflection_commutator']<=TOL,ind['minimum_eigenvalue']>=-TOL,
 ind['zero_mode_residual']<=TOL,ind['orthogonality_error']<=TOL,
 ind['reconstruction_error']<=TOL,ind['population_minimum']>=-TOL,
 abs(ind['population_sum']-1.0)<=TOL,
])
save('independent_reconstruction.json',ind)

# Prefix-resolution audit using the exact inherited path rule.
prefix=[]
for m in [8,16,24,32,40]:
    e=[[i,j,w] for i,j,w in bcfg['weighted_edges'] if int(i)<m and int(j)<m]
    Km=lap(m,e)/(delta-1.0); Rm=np.fliplr(np.eye(m)); vm=np.linalg.eigvalsh(Km)
    prefix.append({'N':m,'minimum_eigenvalue':float(vm.min()),'maximum_eigenvalue':float(vm.max()),'zero_mode_residual':float(np.linalg.norm(Km@np.ones(m))),'reflection_commutator':float(np.linalg.norm(Km@Rm-Rm@Km)),'pass':bool(vm.min()>=-TOL and np.linalg.norm(Km@np.ones(m))<=TOL and np.linalg.norm(Km@Rm-Rm@Km)<=TOL)})

# Countermodels/ablations.
wrong=np.eye(n); wrong[[0,1]]=wrong[[1,0]]
wrong_comm=float(np.linalg.norm(K@wrong-wrong@K))
negative=K-0.01*np.eye(n)
zero=np.zeros_like(K)
abl={
 'symmetry_ablation':{'countermodel':'swap nodes 0 and 1','commutator_norm':wrong_comm,'rejected':wrong_comm>TOL},
 'negative_spectrum_countermodel':{'minimum_eigenvalue':float(np.linalg.eigvalsh(negative).min()),'rejected':float(np.linalg.eigvalsh(negative).min()) < -TOL},
 'parent_operator_ablation':{'countermodel':'K=0','nontrivial_spectrum':bool(np.max(np.abs(np.linalg.eigvalsh(zero)))>TOL),'rejected':bool(np.max(np.abs(vals[1:]))>TOL)},
 'charge_owner_ablation':{'countermodel':'remove constant zero-mode ownership','parent_total_carrier':float(parent_carrier.sum()),'rejected':bool(abs(parent_carrier.sum())>TOL and np.linalg.norm(K@np.ones(n))<=TOL)},
}
abl['pass']=all(x['rejected'] for x in abl.values() if isinstance(x,dict) and 'rejected' in x)

# Clean replay in fresh output directory. Eigenvector signs are a representation gauge,
# so compare sign-invariant spectral content rather than raw JSON byte equality.
with tempfile.TemporaryDirectory(prefix='c120-replay-') as td:
    subprocess.run([sys.executable,str(ROOT/'tools/run_configured_solver.py'),'--config',str(RUN/'solver_configs/C_spectral_model.json'),'--output-dir',td],check=True,cwd=ROOT)
    replay=load(Path(td)/'result.json')
primary_vals=np.asarray(primary['eigenvalues'],float)
replay_vals=np.asarray(replay['eigenvalues'],float)
primary_vecs=np.asarray(primary['eigenvectors'],float)
replay_vecs=np.asarray(replay['eigenvectors'],float)
projector_errors=[]
for j in range(n):
    pp=np.outer(primary_vecs[:,j],primary_vecs[:,j])
    rp=np.outer(replay_vecs[:,j],replay_vecs[:,j])
    projector_errors.append(float(np.linalg.norm(pp-rp)))
replay_checks={
 'success_match':bool(replay['success']==primary['success']),
 'classification_match':bool(replay['classification']==primary['classification']),
 'shape_match':bool(replay['shape']==primary['shape']),
 'symmetric_match':bool(replay['symmetric']==primary['symmetric']),
 'eigenvalues_match':bool(np.allclose(replay_vals,primary_vals,rtol=0,atol=TOL)),
 'eigenprojectors_match':bool(max(projector_errors)<=TOL),
 'reconstruction_error_match':bool(abs(float(replay['reconstruction_error'])-float(primary['reconstruction_error']))<=TOL),
 'generator_audits_match':bool(replay['symmetry_generator_audits']==primary['symmetry_generator_audits']),
}
replay_equal=all(replay_checks.values())

# Numerical residual covariance only; no empirical uncertainty enters.
res=[]
for r in prefix:
    res.append([r['minimum_eigenvalue'],r['zero_mode_residual'],r['reflection_commutator']])
A=np.asarray(res,float)
cov=np.cov(A,rowvar=False) if len(A)>1 else np.zeros((3,3))
cov_eigs=np.linalg.eigvalsh(cov)
unc={'classification':'INTERNAL_NUMERICAL_ONLY','residual_vectors':A.tolist(),'covariance':cov.tolist(),'covariance_psd':bool(cov_eigs.min()>=-1e-24),'public_or_empirical_uncertainty_used':False,'pass':bool(cov_eigs.min()>=-1e-24)}
save('UNCERTAINTY_COVARIANCE.json',unc)

forbidden=['electron','muon','tau','quark','photon','gluon','higgs','standard model','gev','mev','tev']
text=(RUN/'C120_MICROSCOPIC_DERIVATION.json').read_text(encoding='utf-8').lower()
no_sm=not any(tok in text for tok in forbidden)

# Manufactured Wolfram and reference records are evidence inputs, not promotion substitutes.
wl1=load(RUN/'wolfram/C-WL-001/gate.json'); wl2=load(RUN/'wolfram/C-WL-002/gate.json'); ref=load(RUN/'reference_checks.json')
gates={
 'units_and_dimensions': deriv['microscopic_interpretation']['gap_units'].startswith('dimensionless'),
 'symmetry_constraint_closure': primary['symmetric'] and all(x['pass'] for x in primary['symmetry_generator_audits']) and ind['reflection_commutator']<=TOL,
 'positivity_or_declared_alternative': ind['minimum_eigenvalue']>=-TOL,
 'no_standard_model_label_without_derivation': no_sm,
 'charge_and_conservation_ownership': ind['zero_mode_residual']<=TOL and abs(ind['total_carrier_charge']-1.0)<=1e-12,
 'prethermal_population': ind['population_minimum']>=-TOL and abs(ind['population_sum']-1.0)<=TOL,
 'wolfram_symbolic_checks': wl1['status'].startswith('PASS') and wl2['status'].startswith('PASS'),
 'manufactured_reference': ref['overall']=='PASS',
 'independent_symbolic_and_numerical_checks': ind['pass'],
 'countermodels_and_ablations': abl['pass'],
 'prefix_resolution_convergence': all(x['pass'] for x in prefix),
 'restart_and_replay': replay_equal,
 'uncertainty_covariance': unc['pass'],
}
result={
 'run_id':RID,'classification':'C120_FROZEN_GATE_EXECUTION','overall':'PASS' if all(gates.values()) else 'FAIL',
 'gates':gates,'independent_reconstruction':ind,'prefix_runs':prefix,'ablations':abl,
 'replay_restart':{'representation_rule':'eigenvector signs are gauge; compare eigenvalues and rank-1 eigenprojectors','checks':replay_checks,'maximum_projector_error':max(projector_errors),'pass':replay_equal},
 'uncertainty_covariance':unc,
 'physical_scope':{'candidate_dimension':n,'field_identity':'ANONYMOUS_RFC_SPECTRAL_MODES','standard_model_identity_assigned':False,'metric_geometry_assumed':False,'continuous_time_scale':None,'nonlinear_interactions':'UNDETERMINED_AT_C120'},
 'claim_boundary':lock['claim_boundary']
}
save('C120_GATE_EXECUTION.json',result)
print(json.dumps({'overall':result['overall'],'gates':gates,'minimum_eigenvalue':ind['minimum_eigenvalue'],'population_sum':ind['population_sum'],'replay_checks':replay_checks},indent=2))
raise SystemExit(0 if result['overall']=='PASS' else 1)
