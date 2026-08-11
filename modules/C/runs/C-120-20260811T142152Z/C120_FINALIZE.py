#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
RID=RUN.name

def now(): return datetime.now(timezone.utc).isoformat()
def load(name): return json.loads((RUN/name).read_text(encoding='utf-8'))
def save(name,obj):
    p=RUN/name; p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); return p
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(rel):
    p=RUN/rel; return {'path':rel,'sha256':sha(p),'bytes':p.stat().st_size}

lock=load('PRE_EXECUTION_LOCK.json')
gates=load('C120_GATE_EXECUTION.json')
deriv=load('C120_MICROSCOPIC_DERIVATION.json')
primary=load('solver_outputs/spectral_model/result.json')
ind=load('independent_reconstruction.json')
unc=load('UNCERTAINTY_COVARIANCE.json')
replay=load('REPLAY_RECORD.json')
assert lock['status']=='FROZEN'
assert gates['overall']=='PASS' and primary['success'] and ind['pass'] and unc['pass'] and replay['result']=='PASS'

micro={
 'object_id':'C_MICROSCOPIC_STATE','run_id':RID,'module':'C','classification':'RFC_MICROSCOPIC_QUADRATIC_STATE_MINIMAL_SPINE','generation_mode':'GENERATION_SEALED',
 'parent':deriv['parent'],'candidate_law':deriv['candidate_law'],'symmetry':deriv['symmetry'],'spectral_candidate':deriv['spectral_candidate'],
 'charge_and_conservation':deriv['charge_and_conservation'],'interaction_scope':deriv['interaction_scope'],'clock_and_geometry':deriv['clock_and_geometry'],
 'prethermal_state':deriv['prethermal_state'],
 'verification':{'primary_solver_success':True,'all_frozen_gates':'PASS','independent_reconstruction':'PASS','restart_replay':'PASS','internal_covariance':'PASS'},
 'strongest_supported_claim':'The exact B first physical carrier determines a real symmetric positive-semidefinite microscopic quadratic generator, anonymous orthonormal RFC excitation modes, an exact path-reflection symmetry, total-carrier zero-mode charge ownership, and a normalized prethermal spectral population at MINIMAL_SPINE scope.',
 'strongest_unsupported_claim':'C-120 does not establish Standard Model identity, empirical mass units, measured couplings, completed nonlinear microscopic interactions, metric spacetime geometry, a thermal history, or empirical validation.'
}
save('MICROSCOPIC_STATE.json',micro)

checkpoint={'run_id':RID,'status':'FINAL','hash_algorithm':'sha256','state_schema':'RFC_MICROSCOPIC_QUADRATIC_STATE_MINIMAL_SPINE','restart_contract':'Restart from MICROSCOPIC_STATE.json plus the exact frozen B parent; reconstruct K_C, spectral basis, conserved zero mode and prethermal populations before Module D transport.','checkpoints':[{'path':'MICROSCOPIC_STATE.json','sha256':sha(RUN/'MICROSCOPIC_STATE.json')},{'path':'solver_configs/C_spectral_model.json','sha256':sha(RUN/'solver_configs/C_spectral_model.json')}]}
save('CHECKPOINT_RECORD.json',checkpoint)

env={'run_id':RID,'status':'FINAL','operating_system':platform.platform(),'hardware':{'machine':platform.machine(),'processor':platform.processor()},'software':['Python '+platform.python_version(),'numpy','scipy','sympy','networkx'],'python':sys.version,'imports':['hashlib','json','numpy','subprocess','tempfile'],'commands':['WolframLanguageEvaluator C-WL-001','WolframLanguageEvaluator C-WL-002','python tools/run_reference_checks.py --module C','python tools/materialize_solver_config.py','python tools/run_configured_solver.py','python modules/C/runs/'+RID+'/C120_VERIFY.py'],'network_policy':'DISABLED_DURING_GENERATION_EXCEPT_GOVERNED_GITHUB_TRANSPORT','random_seeds':[],'hidden_defaults_audited':True,'hidden_defaults_audit':'All C-120 scientific values descend from the exact B parent or frozen algebraic derivation. No measured mass, coupling, familiar particle label, public target, metric geometry or external clock scale is used.'}
save('ENVIRONMENT.json',env)

handoff={'object_id':'H_C_to_D','run_id':RID,'module':'C','classification':'EXACT_MICROSCOPIC_TO_THERMAL_HANDOFF_MINIMAL_SPINE','generation_mode':'GENERATION_SEALED','claim_boundary':lock['claim_boundary'],'parent':deriv['parent'],'microscopic_state':{'path':'MICROSCOPIC_STATE.json','sha256':sha(RUN/'MICROSCOPIC_STATE.json')},'transport_inputs':{'anonymous_mode_generator':deriv['candidate_law']['matrix'],'prethermal_populations':deriv['prethermal_state']['populations'],'total_carrier_charge_owner':'constant zero mode','event_order_origin':0,'continuous_time_scale':None,'metric_geometry':False},'resolved':{'quadratic_generator':True,'reflection_symmetry':True,'positive_semidefinite_spectrum':True,'total_carrier_charge':True,'prethermal_population':True},'preserved_obstructions':{'nonlinear_collision_or_interaction_operator':'UNDETERMINED_AT_C120; Module D must derive any transport/collision operator from admitted C state without importing empirical couplings.','standard_model_identity':'NOT_ASSIGNED','empirical_mass_scale':'NOT_ASSIGNED'},'evidence':{'parent_bound_spectral_execution':'PASS','wolfram_C_WL_001':'PASS_WITH_MANUAL_INTERPRETATION','wolfram_C_WL_002':'PASS_WITH_MANUAL_INTERPRETATION','countermodels_ablations':'PASS','restart_replay':'PASS','uncertainty_covariance':'PASS','independent_reconstruction':'PASS'},'strongest_supported_claim':micro['strongest_supported_claim'],'strongest_unsupported_claim':micro['strongest_unsupported_claim']}
save('H_C_to_D.json',handoff)

gate_record={'run_id':RID,'module':'C','overall':'PASS','componentwise_gates':gates['gates'],'primary_solver_success':True,'claim_boundary':lock['claim_boundary'],'evidence_files':['C120_GATE_EXECUTION.json','independent_reconstruction.json','solver_outputs/spectral_model/result.json','reference_checks.json','MICROSCOPIC_STATE.json','H_C_to_D.json']}
save('GATE_RESULTS.json',gate_record)

iv=f'''# Independent Verification — {RID}\n\nResult: **PASS**\n\nIndependent reconstruction rebuilt the microscopic generator directly from the exact frozen Module B path and compression scale. Matrix and reflection-generator matches are exact within the frozen tolerance. The minimum eigenvalue is `{ind['minimum_eigenvalue']}`; zero-mode residual is `{ind['zero_mode_residual']}`; orthogonality error is `{ind['orthogonality_error']}`; reconstruction error is `{ind['reconstruction_error']}`.\n\nAll prefix resolutions N=8,16,24,32,40 pass symmetry, positivity, reflection and zero-mode checks. Symmetry, negative-spectrum, parent-operator and charge-owner countermodels are rejected. Clean replay passes under the frozen representation rule that eigenvector signs are gauge and rank-1 eigenprojectors are compared. Internal numerical covariance is positive semidefinite and uses no public or empirical uncertainty.\n\nStrongest supported claim: {micro['strongest_supported_claim']}\n\nStrongest unsupported claim: {micro['strongest_unsupported_claim']}\n'''
(RUN/'INDEPENDENT_VERIFICATION.md').write_text(iv,encoding='utf-8')

claim={'claim_id':'C120-MICROSCOPIC-HANDOFF','text':'Module C establishes the frozen parent-derived anonymous RFC microscopic quadratic constitution and exact handoff H_C_to_D at MINIMAL_SPINE scope.','owner':'C','evidence_state':'FROZEN','fidelity':'MINIMAL_SPINE','supported':True,'evidence':['modules/C/runs/'+RID+'/H_C_to_D.json','modules/C/runs/'+RID+'/C120_GATE_EXECUTION.json','modules/C/runs/'+RID+'/independent_reconstruction.json','modules/C/runs/'+RID+'/MICROSCOPIC_STATE.json']}
save('CLAIM_RECORD.json',claim)

closeout=f'''# Closeout\n\n- Run ID: `{RID}`\n- Work unit: `C-120`\n- Module: `C`\n- Result: `PASS`\n- Evidence state reached: `FROZEN`\n- Fidelity reached: `MINIMAL_SPINE`\n- Verified GitHub commit SHA: `PENDING_EXTERNAL_VERIFICATION`\n\n## Scientific objects produced\n\n- Parent-derived microscopic generator `K_C = Q_B^(-1)-I = L_B/(delta_B-1)`.\n- Anonymous orthonormal RFC spectral excitation modes and dimensionless spectral gaps.\n- Exact B-path reflection symmetry.\n- Total-carrier conserved charge owned by the constant zero mode.\n- Normalized prethermal spectral population.\n- Restartable `MICROSCOPIC_STATE.json` and `H_C_to_D.json`.\n\n## Componentwise gate results\n\nAll gates in `GATE_RESULTS.json` and `C120_GATE_EXECUTION.json` are PASS.\n\n## Failures preserved and corrections made\n\nThe pre-execution firewall false positive and the initial replay representation-comparison failure are preserved in C120 failure-review records. Corrections changed no parents, science definitions, values, tolerances, gates or claim scope; the full frozen matrix was rerun.\n\n## Preserved obstruction\n\nThe exact B parent does not determine nonlinear microscopic interaction/collision coefficients at C-120. No familiar particle identity or empirical coupling was imported. This obstruction is carried explicitly into `H_C_to_D`; Module D owns any derived transport/collision law.\n\n## Strongest supported claim\n\n{micro['strongest_supported_claim']}\n\n## Strongest unsupported claim\n\n{micro['strongest_unsupported_claim']}\n\n## Exact next child\n\n`D-130`, only after this run is closed, Module C is promoted through all required evidence states, the prescribed C closeout commit is externally verified, and the controller advances C-120.\n'''
(RUN/'CLOSEOUT.md').write_text(closeout,encoding='utf-8')

outputs=[]
for rel in ['C120_MICROSCOPIC_DERIVATION.json','solver_configs/C_spectral_model.json','solver_outputs/spectral_model/result.json','solver_outputs/spectral_model/manifest.json','reference_checks.json','C120_GATE_EXECUTION.json','independent_reconstruction.json','UNCERTAINTY_COVARIANCE.json','MICROSCOPIC_STATE.json','CHECKPOINT_RECORD.json','REPLAY_RECORD.json','H_C_to_D.json','GATE_RESULTS.json','INDEPENDENT_VERIFICATION.md']:
    if (RUN/rel).exists(): outputs.append(rec(rel))
for rel in ['wolfram/C-WL-001/record.json','wolfram/C-WL-001/gate.json','wolfram/C-WL-002/record.json','wolfram/C-WL-002/gate.json']:
    if (RUN/rel).exists(): outputs.append(rec(rel))
h=hashlib.sha256()
for x in sorted(outputs,key=lambda x:x['path']): h.update(x['path'].encode()+b'\0'+x['sha256'].encode()+b'\n')
manifest={'run_id':RID,'status':'FINAL','finalized_utc':now(),'outputs':outputs,'tree_sha256':h.hexdigest(),'note':'Hash covers finalized generated scientific/evidence outputs listed here and excludes this manifest and mutable run-registration metadata.'}
save('GENERATED_OUTPUT_MANIFEST.json',manifest)
print(json.dumps({'status':'PASS','outputs':len(outputs),'manifest_tree_sha256':manifest['tree_sha256'],'handoff_sha256':sha(RUN/'H_C_to_D.json')},indent=2))
