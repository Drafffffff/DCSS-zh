#!/bin/sh
# Build in the project's existing container, stage native binaries and runtime libraries.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
HOST=${DCSS_SSH_HOST:-bazzite}
REMOTE=Games/dcss-zh
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
python3 tools/test_consumable_producers.py
python3 tools/test_font_split.py
rsync -az --exclude='.git' --exclude='*.o' --exclude='*.tmp' --exclude='conftest*' --exclude='*.d' --exclude='*.a' --exclude='*.so' --exclude='*.dylib' --exclude='contrib/lua/src/lua' --exclude='contrib/lua/src/luac' --exclude='crawl' --exclude='.cflags' --exclude='.contrib-libs' --exclude='config.h' --exclude='compflag.h' --exclude='build.h' --exclude='contrib/install' --exclude='rltiles/.cflags' native/crawl-ref/ "$HOST:$REMOTE/source/"
ssh "$HOST" 'podman start dcss-zh-builder >/dev/null; podman exec -w /work/source/source dcss-zh-builder sh -c "make -j6 && cp crawl /work/crawl-console && make -j6 TILES=y SOUND=y && cp crawl /work/crawl-tiles"'
mkdir -p output/linux
rsync -az "$HOST:$REMOTE/crawl-console" "$HOST:$REMOTE/crawl-tiles" output/linux/
python3 tools/package_native.py linux
mkdir -p output/linux/dcss-zh/lib
rsync -az "$HOST:$REMOTE/runtime-lib/" output/linux/dcss-zh/lib/
rsync -az output/linux/dcss-zh/ "$HOST:$REMOTE/game/"
