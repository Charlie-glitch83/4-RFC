#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
RID=RUN.name
B_RUN=ROOT/'modules/B/runs/B-110-20260811T140258Z'

def sha(p: Path)->str:
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def save(name,obj):
    p=RUN/name; p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); return p

def graph_laplacian(n, edges):
    L=np.zeros((n,n),dtype=float)
    for i,j,w in edges:
        i=int(i); j=int(j); w=float(w)
        L[i,i]+=w; L[j,j]+=w; L[i,j]-=w; L[j,i]-=w
    return L

b_cfg_path=B_RUN/'solver_configs/B_big_implosion.json'
b_res_path=B_RUN/'solver_outputs/big_implosion/result.json'
b_state_path=B_RUN/'FIRST_PHYSICAL_STATE.json'
b_handoff_path=B_RUN/'H_B_to_C.json'
b_manifest_path=B_RUN/'GENERATED_OUTPUT_MANIFEST.json'
for p in [b_cfg_path,b_res_path,b_state_path,b_handoff_path,b_manifest_path]:
    assert p.is_file(), p
b_cfg=load(b_cfg_path); b_res=load(b_res_path); b_state=load(b_state_path); b_handoff=load(b_handoff_path)
assert b_res['success'] is True
assert b_handoff['classification']=='EXACT_FIRST_PHYSICAL_HANDOFF'
assert b_state['classification']=='FIRST_PHYSICAL_RFC_STATE_MINIMAL_SPINE'

model=b_cfg['model']; n=int(model['node_count']); delta=float(model['delta'])
L=graph_laplacian(n, model['weighted_edges'])
K=L/(delta-1.0)
R=np.fliplr(np.eye(n))
comm=K@R-R@K
ones=np.ones(n)
zero_res=float(np.linalg.norm(K@ones))
vals=np.linalg.eigvalsh(K)
assert float(np.linalg.norm(K-K.T)) <= 1e-12
assert float(np.linalg.norm(comm)) <= 1e-12
assert float(np.min(vals)) >= -1e-12
assert zero_res <= 1e-12

# Anonymous microscopic constitution generated only from B's frozen pregeometry/compression law.
derivation={
 'run_id':RID,
 'classification':'C120_PARENT_DERIVED_MICROSCOPIC_CANDIDATE',
 'generation_mode':'GENERATION_SEALED',
 'parent':{
   'B_run_bundle_sha256':'c83bbcf212b2d7fc37f689013574e5b228f9bac7fb829e56c2c0f60ed84c228d',
   'B_solver_config':{'path':str(b_cfg_path.relative_to(ROOT)),'sha256':sha(b_cfg_path)},
   'B_solver_result':{'path':str(b_res_path.relative_to(ROOT)),'sha256':sha(b_res_path)},
   'B_first_physical_state':{'path':str(b_state_path.relative_to(ROOT)),'sha256':sha(b_state_path)},
   'H_B_to_C':{'path':str(b_handoff_path.relative_to(ROOT)),'sha256':sha(b_handoff_path)}
 },
 'candidate_law':{
   'name':'RFC_MICROSCOPIC_COMPRESSION_GENERATOR',
   'definition':'K_C = L_B/(delta_B-1) = Q_B^{-1}-I',
   'matrix':K.tolist(),
   'units':'dimensionless inherited event-generator scale',
   'dimensions':[n,n],
   'interpretation':'Anonymous microscopic excitation generator inherited from the executed Big Implosion operator; no Standard Model identity is assigned.'
 },
 'symmetry':{
   'name':'B_PATH_REFLECTION',
   'generator_matrix':R.tolist(),
   'commutator_norm':float(np.linalg.norm(comm)),
   'interpretation':'Exact reflection automorphism of the ordered B path pregeometry.'
 },
 'spectral_candidate':{
   'eigenvalues':vals.tolist(),
   'minimum_eigenvalue':float(np.min(vals)),
   'zero_mode_residual':zero_res,
   'positivity_class':'POSITIVE_SEMIDEFINITE',
   'excitation_identity':'ANONYMOUS_RFC_SPECTRAL_MODES'
 },
 'charge_and_conservation':{
   'owner':'RFC_TOTAL_CARRIER_CHARGE',
   'generator':'constant spectral mode',
   'total_parent_carrier':float(b_state['ledger']['total_manifested']),
   'nonzero_modes_charge':0.0,
   'statement':'Only the inherited total-carrier conserved charge is established; no electromagnetic or Standard Model charge label is admitted.'
 },
 'interaction_scope':{
   'quadratic_interaction':'x^T K_C x',
   'higher_nonlinear_interactions':'UNDETERMINED_AT_C120_PARENT_ONLY_SCOPE',
   'mass_mixing_interpretation':'Eigenvalues/eigenvectors are anonymous RFC spectral gap/mixing candidates, not measured masses or named particles.'
 },
 'clock_and_geometry':{
   'event_order_origin':0,
   'metric_geometry_assumed':False,
   'continuous_time_scale':None
 }
}
deriv_path=save('C120_MICROSCOPIC_DERIVATION.json',derivation)
deriv_sha=sha(deriv_path)

source={
 'run_id':RID,
 'exact_parents':[
   {'path':str(b_handoff_path.relative_to(ROOT)),'sha256':sha(b_handoff_path),'kind':'EXACT_PARENT_HANDOFF'},
   {'path':str(b_state_path.relative_to(ROOT)),'sha256':sha(b_state_path),'kind':'EXACT_PARENT_STATE'},
   {'path':str(b_cfg_path.relative_to(ROOT)),'sha256':sha(b_cfg_path),'kind':'EXACT_PARENT_CONFIG'},
   {'path':str(b_res_path.relative_to(ROOT)),'sha256':sha(b_res_path),'kind':'EXACT_PARENT_RESULT'}
 ],
 'admitted_sources':[],
 'imports':['hashlib','json','numpy'],
 'files':[str(p.relative_to(ROOT)) for p in [b_handoff_path,b_state_path,b_cfg_path,b_res_path,deriv_path]],
 'urls':[],
 'constants':[],
 'public_data_declaration':'NONE'
}
save('SOURCE_REGISTER.json',source)

# Bind the prebuilt spectral audit only to the frozen internal derivation object.
sheet_path=RUN/'binding_sheets/C_spectral_model.bindings.json'
sheet=load(sheet_path)
for rec in sheet['bindings']:
    rec.update({'origin_kind':'INTERNAL_DERIVATION','origin_path':str(deriv_path.relative_to(ROOT)),'origin_sha256':deriv_sha,'module':'C','units':'dimensionless','justification':'Frozen parent-derived C-120 microscopic candidate; no public or measured input.'})
    if rec['path']=='model.matrix':
        rec['value']=derivation['candidate_law']['matrix']; rec['derivation_object']='candidate_law.matrix'; rec['dimensions']=f'{n}x{n}'
    elif rec['path']=='model.symmetry_generators':
        rec['value']=[derivation['symmetry']['generator_matrix']]; rec['derivation_object']='symmetry.generator_matrix'; rec['dimensions']=f'1x{n}x{n}'
    else: raise AssertionError(rec['path'])
sheet_path.write_text(json.dumps(sheet,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

lock={
 'run_id':RID,'status':'FROZEN','frozen_utc':datetime.now(timezone.utc).isoformat(),
 'authority_hashes':[sha(ROOT/'recipes/C/WORK_ORDER.md'),sha(ROOT/'recipes/C/recipe.json'),sha(ROOT/'configured_runs/templates/C_spectral_model.template.json'),sha(ROOT/'rfc_engine/solvers/spectral_model.py')],
 'parent_hashes':[sha(b_handoff_path),sha(b_state_path),sha(b_cfg_path),sha(b_res_path)],
 'definition_hashes':[deriv_sha,sha(sheet_path)],
 'candidate_classes':['ANONYMOUS_RFC_SPECTRAL_MODE','RFC_TOTAL_CARRIER_CHARGE','B_PATH_REFLECTION_SYMMETRY','QUADRATIC_MICROSCOPIC_INTERACTION'],
 'equations_and_laws':['K_C=L_B/(delta_B-1)=Q_B^{-1}-I','K_C v_a=lambda_a v_a','[K_C,R_B]=0','Q_total=<1,x> conserved','quadratic candidate action x^T K_C x'],
 'dimensions_units_frames_gauges_clocks':['K_C dimensionless inherited event-generator scale','carrier amplitudes inherit B dimensionless carrier amplitude','no metric geometry assumed','no continuous physical time scale introduced','event order origin inherited from B as 0'],
 'methods':['exact B parent hash admission','Wolfram C-WL-001','Wolfram C-WL-002','manufactured Module C reference matrix','parent-derived spectral_model execution','spectral ablations','restart/replay','internal numerical covariance','independent reconstruction'],
 'tolerances':['spectral_model tolerance 1e-10','parent/symmetry/positivity checks 1e-10 unless exact hash comparison','no aggregate gate may override a component failure'],
 'stopping_rules':['stop on unresolved __BIND token','stop on parent hash mismatch','stop on negative spectrum below tolerance','stop on symmetry closure failure','stop if conservation ownership is undefined','stop if any Standard Model name, measured mass, measured coupling, or empirical constant is inserted'],
 'expected_invariants':['K_C symmetric positive semidefinite','constant mode conserved','B path reflection commutes with K_C','spectral reconstruction closes','all identities remain anonymous RFC microscopic modes','total carrier charge remains owned by the constant mode'],
 'tests':['C-WL-001','C-WL-002','Module C manufactured reference checks','spectral_model parent-bound execution','reflection symmetry ablation','positivity ablation','charge-owner ablation','restart/replay','internal numerical covariance','independent reconstruction'],
 'gates':['units and dimensions','symmetry/constraint closure','positivity/unitarity or declared alternative','no Standard Model label without derivation or correspondence theorem','independent symbolic and numerical checks'],
 'falsifiers':['K_C is nonsymmetric','K_C has an eigenvalue below -1e-10','[K_C,R_B] exceeds 1e-10','constant mode is not conserved','spectral reconstruction fails','a measured/familiar particle identity is required to make the candidate pass'],
 'claim_boundary':'RFC microscopic spectral constitution at executed parent-derived scope; anonymous fields/excitations and conserved carrier charge only. Empirical identity remains for Module P; higher nonlinear microscopic interactions remain unresolved unless derived in C.',
 'independent_verifier_design':'Rebuild L_B directly from the frozen B edge list and delta, reconstruct K_C without trusting C primary outputs, independently diagonalize it, verify PSD/reflection/zero-mode ownership, and compare the primary spectral audit and replay.',
 'allowed_implementation_only_corrections':['serialization, path handling, dependency, recorder-wrapper, or equivalent implementation corrections that do not alter parents, K_C definition, symmetry generator, tolerances, gates, falsifiers, or claim boundary; rerun full frozen matrix after correction']
}
save('PRE_EXECUTION_LOCK.json',lock)
print(json.dumps({'status':'FROZEN','run_id':RID,'derivation_sha256':deriv_sha,'matrix_shape':[n,n],'min_eigenvalue':float(np.min(vals)),'reflection_commutator_norm':float(np.linalg.norm(comm)),'zero_mode_residual':zero_res},indent=2))
