#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import hashlib, json
from pathlib import Path
root=Path('.')
run=root/'modules/E/runs/E-140-20260811T175023Z'
reg=json.loads((run/'SOURCE_REGISTER.json').read_text(encoding='utf-8'))
rows=[]
for rec in reg['exact_parents'] + reg['admitted_sources']:
    p=root/rec['path']
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    expected=rec['sha256']
    rows.append((str(p), expected, actual, actual==expected))
for path, expected, actual, ok in rows:
    print(f'{"PASS" if ok else "FAIL"} {path} expected={expected} actual={actual}')
if not all(r[3] for r in rows):
    raise SystemExit('hash verification failed')
lock=json.loads((run/'PRE_EXECUTION_LOCK.json').read_text(encoding='utf-8'))
print('PRE_EXECUTION_LOCK_STATUS='+str(lock.get('status')))
print('FROZEN_UTC='+str(lock.get('frozen_utc')))
for rule in lock.get('stopping_rules',[]):
    print('STOPPING_RULE='+rule)
PY
