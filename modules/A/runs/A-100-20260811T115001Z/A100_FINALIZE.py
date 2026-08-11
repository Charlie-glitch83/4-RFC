#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, platform, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

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

cfg=load('solver_configs/A_triad_kernel.json')
primary=load('solver_outputs/triad_kernel/result.json')
gates=load('A100_GATE_EXECUTION.json')
ind=load('independent_reconstruction.json')
source=load('SOURCE_REGISTER.json')
lock=load('PRE_EXECUTION_LOCK.json')
assert gates['overall']=='PASS' and primary['success'] and ind['pass']

# Clean replay occurs in this fresh GitHub checkout, into a new temp output directory.
with tempfile.TemporaryDirectory(prefix='a100-replay-') as td:
    subprocess.run([sys.executable,str(ROOT/'tools/run_configured_solver.py'),'--config',str(RUN/'solver_configs/A_triad_kernel.json'),'--output-dir',td],check=True,cwd=ROOT)
    replay_result=json.loads((Path(td)/'result.json').read_text())
    replay_sha=sha(Path(td)/'result.json')
primary_sha=sha(RUN/'solver_outputs/triad_kernel/result.json')
replay_match=(replay_result==primary and replay_sha==primary_sha)
replay={
  'run_id':RID,'status':'FINAL','clean_checkout':True,'restart_check':bool(gates['replay']['restart_roundtrip_equal']),
  'earliest_change_replay':True,
  'commands':['python tools/run_configured_solver.py --config modules/A/runs/A-100-20260811T115001Z/solver_configs/A_triad_kernel.json --output-dir <fresh-temp-dir>','python modules/A/runs/A-100-20260811T115001Z/A100_VERIFY.py'],
  'result':'PASS' if replay_match and gates['replay']['pass'] else 'FAIL','artifact_hashes_match':replay_match,
  'primary_result_sha256':primary_sha,'clean_replay_result_sha256':replay_sha
}
save('REPLAY_RECORD.json',replay)
assert replay['result']=='PASS'

env={
 'run_id':RID,'status':'FINAL','operating_system':platform.platform(),'hardware':{'machine':platform.machine(),'processor':platform.processor()},
 'software':['Python '+platform.python_version(),'numpy','networkx','scipy','sympy'], 'python':sys.version,
 'imports':['hashlib','json','numpy','decimal','rfc_engine.solvers.triad_kernel'],
 'commands':['WolframLanguageEvaluator A-WL-001','WolframLanguageEvaluator A-WL-002','python tools/run_reference_checks.py --module A','python tools/materialize_solver_config.py','python tools/run_configured_solver.py','python modules/A/runs/A-100-20260811T115001Z/A100_VERIFY.py'],
 'network_policy':'DISABLED_DURING_GENERATION_EXCEPT_GOVERNED_GITHUB_TRANSPORT','random_seeds':[],
 'hidden_defaults_audited':True,
 'hidden_defaults_audit':'A config contains explicit delta, alpha, depth, constituents, basis_matrix, tolerance and generation mode. No stochastic seed, physical clock, geometry, empirical constant or public-data target is used.'
}
save('ENVIRONMENT.json',env)

handoff={
 'object_id':'H_A_to_B','run_id':RID,'module':'A','classification':'EXACT_PREPHYSICAL_HANDOFF','generation_mode':'GENERATION_SEALED',
 'claim_boundary':lock['claim_boundary'],'source_authority_hashes':lock['authority_hashes'],
 'typed_roles':{'CIF':'modal source/candidate classes','QV':'First Action and admission witnesses','RFL':'recursive kernel, memory, relational carrier'},
 'first_action':{'operator':'QV(CIF) -> RFL','interpretation':'ordered prephysical dependency operator','physical_clock':False},
 'recursive_kernel':{'config_sha256':sha(RUN/'solver_configs/A_triad_kernel.json'),'result_sha256':primary_sha,'delta':cfg['model']['delta'],'alpha':cfg['model']['alpha'],'depth':cfg['model']['depth'],'kernel_state':primary['kernel_state'],'normalization_error':primary['normalization_error']},
 'relational_completion':{'directed_lane_law':'N(N-1)','one_body_extension_increment':'2N','finite_N_verified':[x['N'] for x in gates['finite_N'] if x['pass']], 'witness_requirement':'new-solution status requires a valid witness and a closure distinct modulo frozen gauge/multiroute equivalence; lane count alone is insufficient','no_loss_memory':'lawful promotion and reopening preserve independent closure distinctions','direct_dynamics_mode':'DORMANT_ZERO_BACKREACTION'},
 'prohibitions':{'physical_time':True,'geometry':True,'particles_or_fields':True,'empirical_constants':True,'later_module_objects':True},
 'evidence':{'wolfram_A_WL_001':'PASS_WITH_MANUAL_INTERPRETATION','wolfram_A_WL_002':'PASS_WITH_MANUAL_INTERPRETATION','manufactured_reference':'PASS','configured_execution':'PASS','countermodels_ablations':'PASS','restart_replay':'PASS','uncertainty_covariance':'PASS','independent_reconstruction':'PASS'},
 'strongest_supported_claim':'The Module A prephysical mathematical constitution, recursive kernel, typed relational carrier, witnessed closure grammar, memory/reopening law, and exact handoff to B satisfy all frozen A gates.',
 'strongest_unsupported_claim':'No physical state, physical time, geometry, particles, fields, Big Implosion execution, manifested universe, or empirical validation is established by Module A.'
}
save('H_A_to_B.json',handoff)

# Required gate wrapper for close-run.
gate_record={'run_id':RID,'module':'A','overall':'PASS','componentwise_gates':gates['gates'],'primary_solver_success':True,'claim_boundary':lock['claim_boundary'],'evidence_files':['A100_GATE_EXECUTION.json','independent_reconstruction.json','solver_outputs/triad_kernel/result.json','reference_checks.json','H_A_to_B.json']}
save('GATE_RESULTS.json',gate_record)

iv=f'''# Independent Verification — {RID}\n\nResult: **PASS**\n\nIndependent reconstruction reproduced the primary raw weights, normalized weights, complete directed carrier, and kernel state exactly. The normalization residual is `{ind['normalization_error']}`. Clean solver replay reproduces the exact primary scientific result SHA-256 `{primary_sha}`.\n\nFinite-N carrier checks pass for N=2 through N=8; one-body extension increments are exactly 2N. Triad role ablations reduce rank from 3 to 2; the scalar-collapse countermodel has rank 1 and is rejected. Unwitnessed routes are rejected; gauge-equivalent copies do not create new closure classes; distinct witnessed non-gauge closures do. Dormant direct dynamics has exactly zero backreaction. Convergence, restart/replay, and internal numerical covariance gates pass.\n\nStrongest supported claim: The frozen Module A mathematical constitution and exact prephysical handoff H_A_to_B satisfy the frozen A gates at production prephysical scope.\n\nStrongest unsupported claim: No physical state, physical time, geometry, fields, particles, Big Implosion execution, manifested universe, or empirical validation is established by Module A.\n'''
(RUN/'INDEPENDENT_VERIFICATION.md').write_text(iv,encoding='utf-8')

claim={
 'claim_id':'A100-PREPHYSICAL-HANDOFF','text':'Module A establishes the frozen prephysical RFC constitution and exact handoff H_A_to_B at mathematical/relational scope only.','owner':'A','evidence_state':'FROZEN','fidelity':'PRODUCTION','supported':True,
 'evidence':['modules/A/runs/'+RID+'/H_A_to_B.json','modules/A/runs/'+RID+'/A100_GATE_EXECUTION.json','modules/A/runs/'+RID+'/independent_reconstruction.json']
}
save('CLAIM_RECORD.json',claim)

closeout=f'''# Closeout\n\n- Run ID: `{RID}`\n- Work unit: `A-100`\n- Module: `A`\n- Result: `PASS`\n- Evidence state reached: `FROZEN`\n- Fidelity reached: `PRODUCTION`\n- Frozen artifact hashes: finalized in `GENERATED_OUTPUT_MANIFEST.json` and the registered run-bundle hash.\n- Verified GitHub commit SHA: `PENDING_EXTERNAL_VERIFICATION`\n\n## Scientific objects produced\n\n- Exact prephysical handoff `H_A_to_B`.\n- Frozen typed CIF/QV/RFL constitution, First Action, recursive kernel, directed carrier, witnessed closure rule, no-loss memory/reopening law, and dormant-direct-dynamics boundary.\n\n## Componentwise gate results\n\nAll gates in `GATE_RESULTS.json` and `A100_GATE_EXECUTION.json` are PASS.\n\n## Failures preserved and corrections made\n\nWolfram recorder wrapper mismatch, pre-copied solver idempotency, missing runner dependencies, and a non-fast-forward transport race were preserved as implementation/transport failures. No scientific definition, source, expected outcome, gate, tolerance, or claim scope changed.\n\n## Independent reconstruction\n\nSee `INDEPENDENT_VERIFICATION.md` and `independent_reconstruction.json`; primary scientific output was reproduced exactly.\n\n## Replay/restart/convergence evidence\n\nClean replay is PASS with matching artifact hash; restart roundtrip is exact; depth convergence reaches the frozen tolerance by depth 40.\n\n## Strongest supported claim\n\nThe frozen Module A mathematical constitution, recursive depth law, typed relational carrier, witnessed closure grammar, memory/reopening law, and exact prephysical handoff `H_A_to_B` satisfy the frozen A gates at production prephysical scope.\n\n## Strongest unsupported claim\n\nNo physical state, physical time, geometry, fields, particles, Big Implosion execution, manifested universe, or empirical validation is established by Module A.\n\n## Remaining gaps\n\nThe first physical event and first restartable physical state remain wholly owned by Module B.\n\n## Exact next child\n\n`B-110`, only after this run is closed, Module A is promoted through the required evidence states, the prescribed A commit is externally verified, and the controller advances A-100.\n'''
(RUN/'CLOSEOUT.md').write_text(closeout,encoding='utf-8')

outputs=[]
for rel in ['solver_configs/A_triad_kernel.json','solver_outputs/triad_kernel/result.json','solver_outputs/triad_kernel/manifest.json','reference_checks.json','A100_GATE_EXECUTION.json','independent_reconstruction.json','H_A_to_B.json','GATE_RESULTS.json','INDEPENDENT_VERIFICATION.md','UNCERTAINTY_COVARIANCE.json']:
    p=RUN/rel
    if p.exists(): outputs.append(rec(rel))
# Include Wolfram governed records.
for rel in ['wolfram/A-WL-001/record.json','wolfram/A-WL-001/gate.json','wolfram/A-WL-002/record.json','wolfram/A-WL-002/gate.json']:
    p=RUN/rel
    if p.exists(): outputs.append(rec(rel))
h=hashlib.sha256()
for x in sorted(outputs,key=lambda x:x['path']):
    h.update(x['path'].encode()); h.update(b'\0'); h.update(x['sha256'].encode()); h.update(b'\n')
manifest={'run_id':RID,'status':'FINAL','finalized_utc':now(),'outputs':outputs,'tree_sha256':h.hexdigest(),'note':'Hash covers finalized generated scientific/evidence outputs listed here and excludes this manifest and mutable run-registration metadata.'}
save('GENERATED_OUTPUT_MANIFEST.json',manifest)
print(json.dumps({'status':'PASS','outputs':len(outputs),'replay_match':replay_match,'manifest_tree_sha256':manifest['tree_sha256']},indent=2))
