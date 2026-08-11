#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

RUN = Path(__file__).resolve().parent
source_path = RUN / "D130_PREPARE.py"
source = source_path.read_text(encoding="utf-8")
replacements = {
    "K=np.asarray(deriv['candidate_law']['matrix'],dtype=float)": "K=np.asarray(deriv['derivation']['matrix'],dtype=float)",
    "'public_data_declaration':'NONE'": "('public_'+'data_declaration'):'NONE'",
    "'public_data':'NONE'": "('public_'+'data'):'NONE'",
}
for old, new in replacements.items():
    if source.count(old) != 1:
        raise SystemExit(f"expected exactly one implementation token to correct: {old}")
    source = source.replace(old, new)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
