#!/bin/bash
# 사용: r3_run.sh <스크립트이름.py> [인자...]  (refs 스크립트를 uv 격리 파이썬으로 실행)
S=/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs
cd /tmp || exit 1
script="$1"; shift
exec uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I "$S/$script" "$@"
