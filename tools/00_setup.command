#!/bin/bash
# 雙擊執行 00_setup（macOS）。邏輯都在 tools/00_setup.py。
cd "$(dirname "$0")/.." || exit 1
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "找不到 uv。請先照網站「安裝環境」安裝 uv，然後關掉終端機重開。"
  read -r -p "按 Enter 關閉視窗"
  exit 1
fi
uv run --project policy python tools/00_setup.py "$@"
