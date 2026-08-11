#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
RID=RUN.name

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

expected_h='c26421f00e724547f476a65fc8a2fc4f82dc9334'
hp=ROOT/'modules/D/runs/D-130-20260811T165602Z/H_D_to_E.json'
assert sha(hp)==expected_h,(sha(hp),expected_h)
hand=json.loads(hp.read_text(encoding='utf-8'))
assert hand['generation_mode']=='GENERATION_SEALED'
assert hand['preserved_obstructions']['primordial_abundances']=='OWNED_BY_MODULE_E'
manifest=json.loads((ROOT/'sources/SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
patterns=[re.compile(x,re.I) for x in [r'reaction',r'stoichi',r'rate law',r'rate coefficient',r'nucleosynth',r'BBN',r'Li7',r'Be7',r'deuter',r'helium']]
hits=[]
for rec in manifest['sources']:
    if rec.get('classification') not in {'CANONICAL_AUTHORITY','ADMITTED_SOURCE','CANDIDATE_ADDENDUM'}:
        continue
    p=ROOT/rec['frozen_path']
    if p.suffix.lower() not in {'.md','.txt','.json','.tex'} or not p.exists():
        continue
    text=p.read_text(encoding='utf-8',errors='ignore')
    for i,line in enumerate(text.splitlines(),1):
        if any(rx.search(line) for rx in patterns):
            hits.append({'source_label':rec['label'],'classification':rec['classification'],'path':rec['frozen_path'],'sha256':rec['sha256'],'line':i,'text':line[:500]})
audit={
  'run_id':RID,
  'classification':'PRE_EXECUTION_SOURCE_OWNERSHIP_AUDIT',
  'generation_mode':'GENERATION_SEALED',
  'exact_parent_handoff':{'path':str(hp.relative_to(ROOT)),'sha256':expected_h},
  'parent_obstructions':hand['preserved_obstructions'],
  'admitted_text_hits':hits,
  'required_objects':['source-owned species and reaction graph','rate laws and uncertainty without public abundance fitting','conservation/nullspace structure','freeze-out witnesses and isotope covariance'],
  'decision_rule':'Do not freeze E pre-execution lock unless admitted parent/source bytes specify a reaction graph/species and executable rate laws without observational targets or fitted abundance corrections.'
}
out=RUN/'E140_SOURCE_OWNERSHIP_AUDIT.json'
out.write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':'AUDIT_COMPLETE','run_id':RID,'exact_parent_sha256':expected_h,'admitted_text_hit_count':len(hits),'audit_path':str(out.relative_to(ROOT))},indent=2))
for h in hits[:160]: print(f"SOURCE_HIT {h['classification']} {h['path']}:{h['line']}: {h['text']}")
