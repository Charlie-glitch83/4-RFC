#!/usr/bin/env bash
set -euo pipefail
python tools/rfc.py doctor
python tools/rfc.py next
