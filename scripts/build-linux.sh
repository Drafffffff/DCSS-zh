#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
python3 tools/native_catalog.py compile
python3 tools/test_native_catalog.py
mkdir -p output/linux
cd native/crawl-ref/source
make -j"${JOBS:-6}"
cp crawl ../../../output/linux/crawl-console
make -j"${JOBS:-6}" TILES=y SOUND=y
cp crawl ../../../output/linux/crawl-tiles
cd "$ROOT"
python3 tools/package_native.py linux
