#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, platform, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
RID=RUN.name

def now(): return datetime.now(timezone.utc).isoformat()
def load(name): return json.loads((RUN/name).read_text(encoding='utf-8'))
def save(name,obj):
    p=RUN/name; p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); return p
def sha(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def rec(rel):
    p=RUN/rel; return {'path':rel,'sha256':sha(p),'bytes':p.stat().st_size}

cfg=load('solver_configs/B_big_implosion.json')
primary=load('solver_outputs/big_implosion/result.json')
gates=load('B110_GATE_EXECUTION.json')
ind=load('independent_reconstruction.json')
source=load('SOURCE_REGISTER.json')
lock=load('PRE_EXECUTION_LOCK.json')
assert primary['success'] and gates['overall']=='PASS' and ind['pass'] and source['public_data_declaration']=='NONE'

# Clean replay in this fresh GitHub checkout.
with tempfile.TemporaryDirectory(prefix='b110-replay-') as td:
    subprocess.run([sys.executable,str(ROOT/'tools/run_configured_solver.py'),'--config',str(RUN/'solver_configs/B_big_implosion.json'),'--output-dir',td],check=True,cwd=ROOT)
    replay_result=json.loads((Path(td)/'result.json').read_text())
    replay_sha=sha(Path(td)/'result.json')
primary_sha=sha(RUN/'solver_outputs/big_implosion/result.json')
replay_match=(replay_result==primary and replay_sha==primary_sha)
replay={'run_id':RID,'status':'FINAL','clean_checkout':True,'restart_check':bool(gates['replay_restart']['restart_reopened_matches_parent']),'earliest_change_replay':True,'commands':['python tools/run_configured_solver.py --config modules/B/runs/B-110-20260811T140258Z/solver_configs/B_big_implosion.json --output-dir <fresh-temp-dir>','python modules/B/runs/B-110-20260811T140258Z/B110_VERIFY.py'],'result':'PASS' if replay_match and gates['replay_restart']['pass'] else 'FAIL','artifact_hashes_match':replay_match,'primary_result_sha256':primary_sha,'clean_replay_result_sha256':replay_sha}
save('REPLAY_RECORD.json',replay); assert replay['result']=='PASS'

manifested=np.asarray(primary['manifested_state'],dtype=float).reshape(-1)
L=np.asarray(primary['laplacian'],dtype=float)
edges=cfg['model']['weighted_edges']
edge_currents=[]
for i,j,w in edges:
    edge_currents.append([int(i),int(j),float(w)*(float(manifested[int(i)])-float(manifested[int(j)]))])
divergence=(L@manifested).tolist()
physical_state={
 'object_id':'B_FIRST_PHYSICAL_STATE','run_id':RID,'classification':'FIRST_PHYSICAL_RFC_STATE_MINIMAL_SPINE','generation_mode':'GENERATION_SEALED',
 'parent_handoff_sha256':'198816819e027409812de925efe42878f9898d628b8c7a137e92c2d52bc568a6',
 'event':{'type':'BIG_IMPLOSION','pre_event_physical_time':None,'intrinsic_event_order_origin':0,'continuous_time_scale':None,'statement':'Physical event ordering begins at this event; no physical clock exists on the A side.'},
 'pregeometry':{'type':'ORDERED_RECURSIVE_DEPTH_PATH_GRAPH','node_count':cfg['model']['node_count'],'weighted_edges':edges,'metric_geometry':False},
 'carrier_field':{'type':'CONSERVATION_BEARING_CARRIER_AMPLITUDE','values':manifested.tolist(),'units':'inherited dimensionless carrier amplitude','particles_or_microscopic_field_identity':False},
 'relational_edge_current':{'definition':'J_ij=w_ij*(carrier_i-carrier_j)','values':edge_currents,'divergence_Lx':divergence,'interpretation':'Relational current on pregeometry only; not an electromagnetic or later-module current.'},
 'ledger':{'total_parent':float(np.sum(np.asarray(primary['initial_state'],dtype=float))),'total_manifested':float(np.sum(manifested)),'total_relative_change':primary['total_relative_change'],'conserved_mode_error':primary['conserved_mode_error']},
 'compression':{'ratio':primary['compression_ratio'],'nontrivial_norm_before':primary['nontrivial_norm_before'],'nontrivial_norm_after':primary['nontrivial_norm_after'],'strict':primary['pass_flags']['strict_nontrivial_compression']},
 'memory_reopening':{'reopening_error':primary['reopening_error'],'reopened_state':primary['reopened_state'],'no_loss':primary['pass_flags']['reopening']},
 'sector_seeds':{'named_later_sectors':[],'total_carrier_ledger_only':True},
 'claim_boundary':lock['claim_boundary']
}
save('FIRST_PHYSICAL_STATE.json',physical_state)

checkpoint={'run_id':RID,'checkpoints':[{'checkpoint_id':'B_EVENT_0','event_order':0,'state_path':'FIRST_PHYSICAL_STATE.json','state_sha256':sha(RUN/'FIRST_PHYSICAL_STATE.json'),'parent_reopening_path':'solver_outputs/big_implosion/result.json','parent_reopening_sha256':primary_sha}],'restart_contract':'Reload frozen solver config and FIRST_PHYSICAL_STATE; reopening must recover the exact A initial carrier within 1e-11 and clean replay must reproduce the exact primary result SHA-256.','state_schema':'FIRST_PHYSICAL_RFC_STATE_MINIMAL_SPINE/v1','hash_algorithm':'sha256'}
save('CHECKPOINT_RECORD.json',checkpoint)

env={'run_id':RID,'status':'FINAL','operating_system':platform.platform(),'hardware':{'machine':platform.machine(),'processor':platform.processor()},'software':['Python '+platform.python_version(),'numpy','networkx','scipy','sympy'],'python':sys.version,'imports':['hashlib','json','numpy','rfc_engine.solvers.big_implosion'],'commands':['WolframLanguageEvaluator B-WL-001','WolframLanguageEvaluator B-WL-002','python tools/run_reference_checks.py --module B','python tools/materialize_solver_config.py','python tools/run_configured_solver.py','python modules/B/runs/B-110-20260811T140258Z/B110_VERIFY.py'],'network_policy':'DISABLED_DURING_GENERATION_EXCEPT_GOVERNED_GITHUB_TRANSPORT','random_seeds':[],'hidden_defaults_audited':True,'hidden_defaults_audit':'B config explicitly fixes delta, node_count, ordered-depth weighted edges, exact parent state, null pre-event clock, total-ledger projection, tolerance, strict compression margin, and generation mode. No stochastic seed, metric geometry, particle content, empirical constant, public target, or named later sector is used.'}
save('ENVIRONMENT.json',env)

handoff={'object_id':'H_B_to_C','run_id':RID,'module':'B','classification':'EXACT_FIRST_PHYSICAL_HANDOFF','generation_mode':'GENERATION_SEALED','claim_boundary':lock['claim_boundary'],'parent':{'A_run_bundle_sha256':'58a735dc94366ed57d592bc5535918a477976bf93efbe736dfb39325b19154d4','H_A_to_B_sha256':'198816819e027409812de925efe42878f9898d628b8c7a137e92c2d52bc568a6','A_parent_state_sha256':'f04f69ae94e9c4ce0105c835f0ba421377cc47df322d180b0b253cdcc8e5257b'},'event':physical_state['event'],'pregeometry':{'state_path':'FIRST_PHYSICAL_STATE.json','state_sha256':sha(RUN/'FIRST_PHYSICAL_STATE.json'),'node_count':cfg['model']['node_count'],'metric_geometry':False},'carrier':{'solver_config_sha256':sha(RUN/'solver_configs/B_big_implosion.json'),'solver_result_sha256':primary_sha,'compression_ratio':primary['compression_ratio'],'total_relative_change':primary['total_relative_change'],'reopening_error':primary['reopening_error']},'restart':{'checkpoint_path':'CHECKPOINT_RECORD.json','checkpoint_sha256':sha(RUN/'CHECKPOINT_RECORD.json'),'clean_replay_result_sha256':replay_sha},'sectors':{'named_later_sectors':[],'total_carrier_ledger_only':True},'evidence':{'wolfram_B_WL_001':'PASS_WITH_MANUAL_INTERPRETATION','wolfram_B_WL_002':'PASS_WITH_MANUAL_INTERPRETATION','manufactured_reference':'PASS','parent_bound_physical_execution':'PASS','multiple_graph_sizes':'PASS','ablations':'PASS','restart_replay':'PASS','uncertainty_covariance':'PASS','independent_reconstruction':'PASS'},'strongest_supported_claim':'Module B executes the frozen Big Implosion on the exact A parent and produces a restartable first physical RFC carrier state on explicitly typed pregeometry at MINIMAL_SPINE fidelity.','strongest_unsupported_claim':'Module B does not establish metric geometry, microscopic particles or identified fields, Standard Model content, later cosmological evolution, a completed manifested universe, or empirical validation.'}
save('H_B_to_C.json',handoff)

gate_record={'run_id':RID,'module':'B','overall':'PASS','componentwise_gates':gates['gates'],'primary_solver_success':True,'claim_boundary':lock['claim_boundary'],'evidence_files':['B110_GATE_EXECUTION.json','independent_reconstruction.json','solver_outputs/big_implosion/result.json','reference_checks.json','FIRST_PHYSICAL_STATE.json','H_B_to_C.json']}
save('GATE_RESULTS.json',gate_record)

iv=f'''# Independent Verification — {RID}\n\nResult: **PASS**\n\nAn independent reconstruction rebuilt the 40-node ordered-depth path Laplacian and Big Implosion operator directly from the frozen A parent. The manifested state and operator match the primary execution; reopening recovers the parent with maximum absolute error `{ind['reopened_parent_max_abs']}` and total-ledger change `{ind['total_ledger_change']}`.\n\nPrefix executions at N=8,16,24,32,40 all pass. The final first-four-node boundary difference is `{gates['convergence']['boundary_first4_differences'][-1]}`. The Q=I compression ablation and L=0 relational-coupling ablation both fail strict compression as predeclared. Clean replay reproduces the exact primary result SHA-256 `{primary_sha}`. Internal numerical covariance is positive semidefinite and its maximum residual is `{gates['uncertainty_covariance']['max_residual']}`.\n\nThe first physical state is an event-ordered conservation-bearing carrier on explicit pregeometry. No pre-event clock, metric geometry, particles, microscopic field identity, empirical constants, public targets, or later named sectors are introduced.\n\nStrongest supported claim: Module B produces a restartable first physical RFC state through the frozen Big Implosion on the exact A parent at MINIMAL_SPINE fidelity.\n\nStrongest unsupported claim: Metric geometry, microscopic particle/field constitution, later cosmological evolution, a completed manifested universe, and empirical validation remain unestablished.\n'''
(RUN/'INDEPENDENT_VERIFICATION.md').write_text(iv,encoding='utf-8')

claim={'claim_id':'B110-FIRST-PHYSICAL-STATE','text':'Module B executes the frozen Big Implosion on the exact Module A parent and establishes a restartable first physical RFC carrier state on typed pregeometry at MINIMAL_SPINE fidelity.','owner':'B','evidence_state':'FROZEN','fidelity':'MINIMAL_SPINE','supported':True,'evidence':['modules/B/runs/'+RID+'/FIRST_PHYSICAL_STATE.json','modules/B/runs/'+RID+'/H_B_to_C.json','modules/B/runs/'+RID+'/B110_GATE_EXECUTION.json','modules/B/runs/'+RID+'/independent_reconstruction.json']}
save('CLAIM_RECORD.json',claim)

closeout=f'''# Closeout\n\n- Run ID: `{RID}`\n- Work unit: `B-110`\n- Module: `B`\n- Result: `PASS`\n- Evidence state reached: `FROZEN`\n- Fidelity reached: `MINIMAL_SPINE`\n- Frozen artifact hashes: finalized in `GENERATED_OUTPUT_MANIFEST.json` and the registered run-bundle hash.\n- Verified GitHub commit SHA: `PENDING_EXTERNAL_VERIFICATION`\n\n## Scientific objects produced\n\n- `FIRST_PHYSICAL_STATE.json`: first event-ordered conservation-bearing RFC carrier state on typed pregeometry.\n- `H_B_to_C.json`: restartable exact physical handoff to Module C.\n- Big Implosion compression operator execution, total-carrier ledger, relational edge currents, event-order origin, and no-loss reopening memory.\n\n## Componentwise gate results\n\nAll frozen B gates in `GATE_RESULTS.json` and `B110_GATE_EXECUTION.json` are PASS.\n\n## Failures preserved and corrections made\n\nThe materializer initially rejected the noncanonical provenance label `FROZEN_PARENT`; it was corrected to the controlled vocabulary `EXACT_PARENT_ARTIFACT`. No parent byte, scientific value, derivation rule, equation, tolerance, expected outcome, gate, falsifier, or claim scope changed. Earlier stale A-transition workflows were transport noise only and did not mutate B science.\n\n## Independent reconstruction\n\nSee `INDEPENDENT_VERIFICATION.md` and `independent_reconstruction.json`; the independent path reconstructs the B Laplacian, operator, manifested state, conservation, and reopening from the frozen A parent.\n\n## Replay/restart/convergence evidence\n\nClean replay reproduces the exact primary result hash. The event-0 checkpoint is restartable; reopening recovers the exact A parent within the frozen tolerance. Prefix sizes N=8,16,24,32,40 pass and the boundary observable is converged by N=40.\n\n## Strongest supported claim\n\nModule B executes the sole frozen Big Implosion on the exact Module A parent and establishes a restartable first physical RFC carrier state on explicit pregeometry at `MINIMAL_SPINE` fidelity.\n\n## Strongest unsupported claim\n\nModule B does not establish metric geometry, microscopic particles or identified fields, Standard Model content, later cosmological evolution, a completed manifested universe, or empirical validation.\n\n## Remaining gaps\n\nMicroscopic field/particle/interaction/mass/mixing constitution from this exact first physical state remains wholly owned by Module C.\n\n## Exact next child\n\n`C-120`, only after this run is closed, Module B visits all required evidence states through `FROZEN`, the prescribed B commit is externally verified, and the controller advances B-110.\n'''
(RUN/'CLOSEOUT.md').write_text(closeout,encoding='utf-8')

outputs=[]
for rel in ['solver_configs/B_big_implosion.json','solver_outputs/big_implosion/result.json','solver_outputs/big_implosion/manifest.json','reference_checks.json','B110_GATE_EXECUTION.json','independent_reconstruction.json','FIRST_PHYSICAL_STATE.json','CHECKPOINT_RECORD.json','REPLAY_RECORD.json','ENVIRONMENT.json','H_B_to_C.json','GATE_RESULTS.json','INDEPENDENT_VERIFICATION.md','CLOSEOUT.md']:
    p=RUN/rel
    if p.exists(): outputs.append(rec(rel))
for rel in ['wolfram/B-WL-001/record.json','wolfram/B-WL-001/gate.json','wolfram/B-WL-002/record.json','wolfram/B-WL-002/gate.json']:
    p=RUN/rel
    if p.exists(): outputs.append(rec(rel))
h=hashlib.sha256()
for x in sorted(outputs,key=lambda x:x['path']):
    h.update(x['path'].encode()); h.update(b'\0'); h.update(x['sha256'].encode()); h.update(b'\n')
manifest={'run_id':RID,'status':'FINAL','finalized_utc':now(),'outputs':outputs,'tree_sha256':h.hexdigest(),'note':'Hash covers finalized generated scientific/evidence outputs listed here and excludes this manifest and mutable run-registration metadata.'}
save('GENERATED_OUTPUT_MANIFEST.json',manifest)
print(json.dumps({'status':'PASS','outputs':len(outputs),'replay_match':replay_match,'first_physical_state_sha256':sha(RUN/'FIRST_PHYSICAL_STATE.json'),'handoff_sha256':sha(RUN/'H_B_to_C.json'),'manifest_tree_sha256':manifest['tree_sha256']},indent=2))
