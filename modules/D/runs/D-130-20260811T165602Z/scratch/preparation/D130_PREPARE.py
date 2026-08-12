#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
RID=RUN.name
C=ROOT/'modules/C/runs/C-120-20260811T142152Z'
B=ROOT/'modules/B/runs/B-110-20260811T140258Z'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def expr_for(row,names):
    terms=[]
    for c,name in zip(row,names):
        if abs(float(c))<1e-18: continue
        terms.append(f'({float(-c):.17g})*{name}')
    return ' + '.join(terms) if terms else '0.0'

expected={
 'H_C_to_D.json':'0f7fcbbe99ffd30ee5afaeb32f83c9fc8bb287d98ceb6850a0b31c551618945b',
 'MICROSCOPIC_STATE.json':'fc65192eb644621a8be4a19231200ee678dec91dd2ad587ad92d47acbfef9c5b',
 'C120_MICROSCOPIC_DERIVATION.json':'27280f0d4388d8e8cb3e9c35a0ffd0e8a42d4a419d070e43bc1118e9ae617c58',
 'solver_configs/C_spectral_model.json':'9543a388df43d188d12dfb76aa86f80c2e8ffe72d7a65193e4ed98d1fb61858d',
}
for rel,d in expected.items(): assert sha(C/rel)==d,(rel,sha(C/rel),d)
assert sha(B/'FIRST_PHYSICAL_STATE.json')=='f50c7e721c38dd9b63f2910f3a0ace399f1854e85cbdafaa9ce51649d40c073a'

handoff=load(C/'H_C_to_D.json')
micro=load(C/'MICROSCOPIC_STATE.json')
deriv=load(C/'C120_MICROSCOPIC_DERIVATION.json')
bstate=load(B/'FIRST_PHYSICAL_STATE.json')
assert handoff['generation_mode']=='GENERATION_SEALED'
assert handoff['preserved_obstructions']['standard_model_identity']=='NOT_ASSIGNED'
assert 'UNDETERMINED' in handoff['preserved_obstructions']['nonlinear_collision_or_interaction_operator']
K=np.asarray(deriv['candidate_law']['matrix'],dtype=float)
assert K.shape==(40,40)
assert np.linalg.norm(K-K.T)<=1e-12
assert np.linalg.norm(K@np.ones(40))<=1e-12
vals=np.linalg.eigvalsh(K)
positive=vals[vals>1e-12]
assert len(positive)==39 and vals.min()>=-1e-12
lam_min=float(positive.min()); lam_max=float(positive.max())

# Exact inherited positive carrier density on K_C's native pregeometry basis.
q=np.asarray(bstate['carrier_field']['values'],dtype=float)
assert q.shape==(40,) and q.min()>=0 and abs(q.sum()-1.0)<=1e-12

# Parent-derived nonnegative local quadratic energy density. Each edge's
# 1/2*w*(q_i-q_j)^2 is divided equally between its endpoints.
e=np.zeros(40,float)
edges=[]
for i in range(40):
    for j in range(i+1,40):
        w=float(-K[i,j])
        if w>1e-15:
            edge_energy=0.5*w*(q[i]-q[j])**2
            e[i]+=0.5*edge_energy; e[j]+=0.5*edge_energy
            edges.append([i,j,w])
energy_total=float(e.sum())
quadratic=float(0.5*q@K@q)
assert abs(energy_total-quadratic)<=1e-14 and e.min()>=0

# -K_C is the unique linear generator already encoded by C's frozen quadratic
# law. It has nonnegative off-diagonals, zero row sums and therefore defines a
# positivity-preserving conservative semigroup without inventing collision rates.
G=-K
assert np.min(G-np.diag(np.diag(G)))>=-1e-15
assert np.linalg.norm(G@np.ones(40))<=1e-12

qnames=[f'q{i:02d}' for i in range(40)]
enames=[f'e{i:02d}' for i in range(40)]
names=qnames+enames
rhs=[expr_for(K[i],qnames) for i in range(40)]+[expr_for(K[i],enames) for i in range(40)]
initial=q.tolist()+e.tolist()
# Natural intrinsic relaxation-order interval: one e-fold of the slowest
# nonzero parent mode; max step is one fastest-mode relaxation interval.
t_end=1.0/lam_min
max_step=1.0/lam_max
linv={
 'RFC_TOTAL_CARRIER_CHARGE':[1.0]*40+[0.0]*40,
 'RFC_TOTAL_QUADRATIC_ENERGY':[0.0]*40+[1.0]*40,
}

rules={
 'run_id':RID,'module':'D','classification':'FROZEN_PARENT_DERIVED_LINEAR_TRANSPORT_RULES','generation_mode':'GENERATION_SEALED',
 'parent':{
  'C_run_bundle_sha256':'a194474515a4b7a274c41f7bc127ea4d09301c6af1b7e8d851ceb11c74930c1b',
  'H_C_to_D_sha256':expected['H_C_to_D.json'],'MICROSCOPIC_STATE_sha256':expected['MICROSCOPIC_STATE.json'],
  'C_derivation_sha256':expected['C120_MICROSCOPIC_DERIVATION.json'],'B_first_physical_state_sha256':'f50c7e721c38dd9b63f2910f3a0ace399f1854e85cbdafaa9ce51649d40c073a'
 },
 'transport_operator':{
  'definition':'G_D=-K_C','generator':G.tolist(),'offdiagonal_nonnegative':True,'row_sum_zero':True,
  'scope':'linear conservative transport only','nonlinear_collision_operator':'UNDETERMINED_AND_NOT_INSERTED'
 },
 'state':{
  'carrier_density_names':qnames,'energy_density_names':enames,'initial_carrier_density':q.tolist(),'initial_energy_density':e.tolist(),
  'energy_definition':'E_i = one-half share at node i of each incident edge energy (1/2) w_ij (q_i-q_j)^2',
  'total_charge':float(q.sum()),'total_energy':energy_total,'quadratic_energy_check':quadratic
 },
 'intrinsic_clock':{
  'variable':'s_D','kind':'DIMENSIONLESS_RELAXATION_ORDER','origin':0.0,'end':t_end,
  'derivation':'s_end=1/lambda_min_positive(K_C); no seconds or external clock scale assigned','continuous_empirical_time_scale':None
 },
 'thermal_observables':{
  'local_temperature_proxy':'Theta_i=e_i/q_i where q_i>0; dimensionless inherited energy-per-carrier ratio',
  'equilibrium_temperature_proxy':'Theta_bar=total_energy/total_charge',
  'entropy':'S=-sum_i p_i log p_i for p_i=q_i/sum(q)',
  'phase_event_witness':'signed crossing of Theta_i-Theta_bar; no fitted transition threshold',
  'pregeometry_spread':'charge-weighted variance of inherited path index; not metric expansion'
 },
 'solver_interval':{'t_span':[0.0,t_end],'max_step':max_step,'lambda_min_positive':lam_min,'lambda_max':lam_max},
 'invariants':linv,
 'preserved_obstructions':handoff['preserved_obstructions'],
 'claim_boundary':'Generated RFC linear nonequilibrium thermal/transport history on inherited pregeometry; nonlinear collisions, metric expansion, empirical temperature units, and primordial abundances remain unestablished.'
}
rules_path=RUN/'D130_STRUCTURAL_BINDING_RULES.json'; save(rules_path,rules); rules_sha=sha(rules_path)

sheet=load(RUN/'binding_sheets/D_transport.bindings.json')
values={
 'model.state_names':names,
 'model.parameters':{},
 'model.rhs_expressions':rhs,
 'model.initial_state':initial,
 'model.t_span':[0.0,t_end],
 'model.max_step':max_step,
 'model.linear_invariants':linv,
 'model.invariant_tolerance':1e-9,
 'model.positivity_tolerance':1e-12,
}
for rec in sheet['bindings']:
    path=rec['path']; assert path in values,path
    rec.update({'value':values[path],'origin_kind':'INTERNAL_DERIVATION','origin_path':f'modules/D/runs/{RID}/D130_STRUCTURAL_BINDING_RULES.json','origin_sha256':rules_sha,'module':'D','derivation_object':path.replace('model.','')})
    if path=='model.state_names': rec.update({'units':'labels','dimensions':'80','justification':'40 inherited carrier-density plus 40 derived local-energy-density states.'})
    elif path=='model.parameters': rec.update({'units':'none','dimensions':'0','justification':'No free or empirical rates: G_D=-K_C is encoded directly from the frozen C parent.'})
    elif path=='model.rhs_expressions': rec.update({'units':'state per intrinsic relaxation order','dimensions':'80','justification':'Exact linear transport dq/ds=-K_C q and de/ds=-K_C e.'})
    elif path=='model.initial_state': rec.update({'units':'inherited dimensionless carrier and quadratic-energy densities','dimensions':'80','justification':'Carrier density from exact B state admitted by C; local energy from the frozen C quadratic form.'})
    elif path=='model.t_span': rec.update({'units':'intrinsic relaxation order','dimensions':'2','justification':'One slowest nonzero parent-mode e-fold, derived from K_C spectrum.'})
    elif path=='model.max_step': rec.update({'units':'intrinsic relaxation order','dimensions':'1','justification':'One fastest parent-mode relaxation interval, derived from K_C spectrum.'})
    elif path=='model.linear_invariants': rec.update({'units':'dimensionless totals','dimensions':'2x80','justification':'Zero row sum of K_C separately conserves total carrier and total quadratic energy.'})
    elif path=='model.invariant_tolerance': rec.update({'units':'dimensionless','dimensions':'1','justification':'Uses the frozen transport template relative tolerance 1e-9; no looser scientific threshold introduced.'})
    elif path=='model.positivity_tolerance': rec.update({'units':'dimensionless','dimensions':'1','justification':'Uses the frozen transport template absolute tolerance 1e-12.'})
save(RUN/'binding_sheets/D_transport.bindings.json',sheet)

source={
 'run_id':RID,
 'exact_parents':[
  {'path':'modules/C/runs/C-120-20260811T142152Z','sha256':'a194474515a4b7a274c41f7bc127ea4d09301c6af1b7e8d851ceb11c74930c1b','kind':'REGISTERED_RUN_BUNDLE'},
  {'path':'modules/C/runs/C-120-20260811T142152Z/H_C_to_D.json','sha256':expected['H_C_to_D.json'],'kind':'EXACT_PARENT_HANDOFF'},
  {'path':'modules/C/runs/C-120-20260811T142152Z/MICROSCOPIC_STATE.json','sha256':expected['MICROSCOPIC_STATE.json'],'kind':'EXACT_PARENT_STATE'},
  {'path':'modules/C/runs/C-120-20260811T142152Z/C120_MICROSCOPIC_DERIVATION.json','sha256':expected['C120_MICROSCOPIC_DERIVATION.json'],'kind':'EXACT_PARENT_DERIVATION'},
  {'path':'modules/B/runs/B-110-20260811T140258Z/FIRST_PHYSICAL_STATE.json','sha256':'f50c7e721c38dd9b63f2910f3a0ace399f1854e85cbdafaa9ce51649d40c073a','kind':'ANCESTRAL_STATE_EXPLICITLY_REFERENCED_BY_C_HANDOFF'}
 ],
 'admitted_sources':[],'imports':['hashlib','json','numpy'],'urls':[],
 'files':['recipes/D/WORK_ORDER.md','recipes/D/recipe.json','configured_runs/templates/D_transport.template.json',f'modules/D/runs/{RID}/D130_STRUCTURAL_BINDING_RULES.json'],
 'constants':[{'name':'transport.rtol','value':1e-9,'origin':'frozen D solver template','empirical':False},{'name':'transport.atol','value':1e-12,'origin':'frozen D solver template','empirical':False}],
 'public_data_declaration':'NONE'
}
save(RUN/'SOURCE_REGISTER.json',source)

work=ROOT/'recipes/D/WORK_ORDER.md'; recipe=ROOT/'recipes/D/recipe.json'; template=RUN/'solver_templates/D_transport.template.json'; binding=RUN/'binding_sheets/D_transport.bindings.json'; sourcep=RUN/'SOURCE_REGISTER.json'
lock={
 'run_id':RID,'status':'FROZEN','frozen_utc':datetime.now(timezone.utc).isoformat(),
 'authority_hashes':[sha(work),sha(recipe)],
 'parent_hashes':['a194474515a4b7a274c41f7bc127ea4d09301c6af1b7e8d851ceb11c74930c1b',expected['H_C_to_D.json'],expected['MICROSCOPIC_STATE.json'],expected['C120_MICROSCOPIC_DERIVATION.json'],'f50c7e721c38dd9b63f2910f3a0ace399f1854e85cbdafaa9ce51649d40c073a'],
 'definition_hashes':[sha(template),rules_sha,sha(binding),sha(sourcep)],
 'candidate_classes':['RFC_CARRIER_DENSITY','RFC_LOCAL_QUADRATIC_ENERGY_DENSITY','LINEAR_PARENT_DERIVED_TRANSPORT_SEMIGROUP','DIMENSIONLESS_RELAXATION_ORDER','THERMAL_PROXY_FIELD','PHASE_CROSSING_WITNESS','ENTROPY_LEDGER'],
 'equations_and_laws':['G_D=-K_C','dq/ds=G_D q','de/ds=G_D e','sum_i q_i=constant','sum_i e_i=constant','Theta_i=e_i/q_i','S=-sum_i p_i log p_i','phase witness: sign crossing of Theta_i-Theta_bar'],
 'dimensions_units_frames_gauges_clocks':['All D amplitudes inherit C/B dimensionless normalization; no kelvin, seconds, metric length, or empirical scale is admitted.','s_D is an intrinsic dimensionless relaxation-order parameter with origin at the B event-order origin and scale derived only from K_C spectrum.','Pregeometry spread uses inherited path index and is not metric/cosmological expansion.'],
 'methods':['exact parent SHA-256 verification','D-WL-001','D-WL-002','D manufactured reference matrix','provenance-bound BDF transport execution','entropy/temperature/event postprocessing','stiffness and step convergence','transport/energy/charge ablations','restart/replay','internal numerical covariance','independent matrix-exponential reconstruction'],
 'tolerances':['BDF rtol 1e-9','BDF atol 1e-12','linear-invariant tolerance 1e-9','positivity tolerance 1e-12','no componentwise gate averaging'],
 'stopping_rules':['Stop on any unresolved __BIND_ token','Stop on any parent hash mismatch','Stop on negative carrier or energy density beyond 1e-12','Stop on carrier or energy drift above 1e-9','Stop if event ordering uses observed targets','Stop if nonlinear collision coefficients, empirical temperature/time scales, metric expansion, or primordial abundances are inserted','Stop on any mandatory gate failure'],
 'expected_invariants':['G_D has nonnegative off-diagonals and zero row sum','carrier and local-energy densities remain nonnegative','total carrier and total quadratic energy are conserved','entropy is nondecreasing within numerical tolerance','temperature proxy relaxes without fitted threshold','phase witnesses are derived crossings only','nonlinear collision obstruction remains explicit'],
 'tests':['D-WL-001 complete output','D-WL-002 complete output','Module D manufactured reference checks','primary 80-state BDF execution','max-step convergence','carrier/energy invariants','positivity','entropy production','phase-event ordering','zero-transport ablation','broken-conservation countermodel','restart/replay','internal covariance','independent matrix-exponential reconstruction'],
 'gates':['positive distributions','energy/charge conservation','event ordering','stiff-solver convergence','restart and independent reconstruction'],
 'falsifiers':['negative distribution beyond tolerance','carrier or energy drift beyond tolerance','entropy decrease beyond numerical tolerance','event witness depends on public/observed target','independent reconstruction mismatch','nonlinear/empirical input appears'],
 'claim_boundary':rules['claim_boundary'],
 'independent_verifier_design':'Reconstruct K_C directly from exact C parent, rebuild q and local quadratic e from admitted B ancestor, propagate both with exp(-K_C s) independently of the primary BDF solver, reproduce invariants/entropy/events and compare at frozen sample times.',
 'allowed_implementation_only_corrections':['Serialization, path, environment, solver-call, or equivalent implementation corrections only; no parent bytes, G_D law, initial-state derivation, intrinsic clock rule, tolerances, gates, falsifiers, or claim scope may change. Rerun full frozen matrix after correction.']
}
save(RUN/'PRE_EXECUTION_LOCK.json',lock)
(RUN/'RUN_PLAN.md').write_text(f'''# D-130 Run Plan\n\nRun: `{RID}`\n\nExecute the sole authorized Module D packet from exact frozen Module C parent bytes. The frozen transport law is `G_D=-K_C`, applied separately to inherited positive carrier density and parent-derived local quadratic-energy density so total carrier and total energy are exact linear invariants. The intrinsic clock is dimensionless relaxation order derived solely from the nonzero spectrum of `K_C`. Nonlinear collisions, metric expansion, empirical time/temperature scales, and primordial abundances are prohibited and remain unresolved.\n''',encoding='utf-8')
print(json.dumps({'status':'PASS','run_id':RID,'rules_sha256':rules_sha,'binding_sha256':sha(binding),'source_register_sha256':sha(sourcep),'pre_execution_lock_sha256':sha(RUN/'PRE_EXECUTION_LOCK.json'),'lambda_min_positive':lam_min,'lambda_max':lam_max,'t_end':t_end,'max_step':max_step,'initial_total_charge':float(q.sum()),'initial_total_energy':energy_total,'public_data':'NONE'},indent=2))
