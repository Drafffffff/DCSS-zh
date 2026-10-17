#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
python3 tools/prepare_native_data.py
python3 tools/native_catalog.py compile
python3 tools/test_native_catalog.py
python3 tools/test_message_ids.py
python3 tools/audit_message_migration.py
python3 tools/test_native_text_grid.py
python3 tools/test_pretranslated_rendering.py
python3 tools/test_skill_menu_layout.py
python3 tools/test_hud_layout.py
python3 tools/test_translation_boundaries.py
python3 tools/test_detail_producers.py
python3 tools/test_curse_details.py
python3 tools/test_item_hints.py
python3 tools/test_font_split.py
mkdir -p output/macos verification/native
cd native/crawl-ref/source
make -j"${JOBS:-8}" FORCE_PKGCONFIG=y MACOSX_MIN_VERSION=26.0
cp crawl ../../../output/macos/crawl-console
make -j"${JOBS:-8}" TILES=y SOUND=y FORCE_PKGCONFIG=y MACOSX_MIN_VERSION=26.0
cp crawl ../../../output/macos/crawl-tiles
cd "$ROOT"
python3 tools/package_native.py macos
