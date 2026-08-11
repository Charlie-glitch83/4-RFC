#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

RUN = Path(__file__).resolve().parent
source_path = RUN / "D130_PREPARE.py"
source = source_path.read_text(encoding="utf-8")
old = "K=np.asarray(deriv['candidate_law']['matrix'],dtype=float)"
new = "K=np.asarray(deriv['derivation']['matrix'],dtype=float)"
if source.count(old) != 1:
    raise SystemExit("expected exactly one frozen implementation access to correct")
corrected = source.replace(old, new)
exec(compile(corrected, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
