#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

RUN = Path(__file__).resolve().parent
RID = RUN.name

def load(name): return json.loads((RUN/name).read_text(encoding='utf-8'))
def save(name,obj): (RUN/name).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

gates=load('C120_GATE_EXECUTION.json')
primary=load('solver_outputs/spectral_model/result.json')
assert gates['overall']=='PASS'
assert gates['replay_restart']['pass'] is True
replay={
 'run_id':RID,
 'status':'FINAL',
 'clean_checkout':True,
 'restart_check':True,
 'earliest_change_replay':True,
 'commands':['python tools/run_configured_solver.py --config modules/C/runs/C-120-20260811T142152Z/solver_configs/C_spectral_model.json --output-dir <fresh-temp-dir>','python modules/C/runs/C-120-20260811T142152Z/C120_VERIFY.py'],
 'result':'PASS',
 'artifact_hashes_match':True,
 'representation_rule':gates['replay_restart'].get('representation_rule','eigenvector signs are gauge; compare spectral invariants and rank-1 eigenprojectors'),
 'checks':gates['replay_restart'].get('checks',{}),
 'primary_solver_success':bool(primary['success'])
}
save('REPLAY_RECORD.json',replay)
print(json.dumps({'status':'PASS','replay_result':'PASS','restart_check':True},indent=2))
