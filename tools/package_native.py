#!/usr/bin/env python3
"""Stage native builds with independent saves and explicit fonts; no system installation."""
import argparse, os, plistlib, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('platform',choices=['macos','linux']);p.add_argument('--dest',type=Path);a=p.parse_args()
stage=ROOT/'output'/a.platform
stage.mkdir(parents=True,exist_ok=True)
def data(dest):
    for folder in ('dat',): shutil.copytree(ROOT/'native/crawl-ref/source'/folder,dest/folder,dirs_exist_ok=True)
    shutil.copytree(ROOT/'native/crawl-ref/docs',dest/'docs',dirs_exist_ok=True)
    (dest/'fonts').mkdir(exist_ok=True)
    for filename in ('NotoSansSC-Regular.ttf', 'DCSSPixelSC-Regular.ttf'):
        shutil.copy2(ROOT/'fonts'/filename,dest/'fonts'/filename)
    shutil.copytree(ROOT/'fonts/fusion-pixel-licenses',dest/'fonts/fusion-pixel-licenses',dirs_exist_ok=True)
    if (ROOT/'fonts/OFL.txt').exists(): shutil.copy2(ROOT/'fonts/OFL.txt',dest/'fonts/OFL.txt')
    for name in ('LICENSE','CREDITS.txt'):
        src=ROOT/'native/crawl-ref'/name
        if not src.exists(): src=ROOT/'native'/name
        shutil.copy2(src,dest/name)
def executable(path,text): path.write_text(text);path.chmod(0o755)
if a.platform=='macos':
    dest=(a.dest or Path.home()/'Applications')/'DCSS 中文版.app'
    res=dest/'Contents/Resources';mac=dest/'Contents/MacOS'
    res.mkdir(parents=True,exist_ok=True);mac.mkdir(parents=True,exist_ok=True);data(res)
    icon=ROOT/'native/crawl-ref/source/dat/tiles/stone_soup_icon.icns'
    if icon.exists(): shutil.copy2(icon,res/'Crawl.icns')
    for mode in ('tiles','console'): shutil.copy2(stage/f'crawl-{mode}',res/f'crawl-{mode}')
    plist={'CFBundleName':'DCSS 中文版','CFBundleDisplayName':'DCSS 中文版','CFBundleIdentifier':'local.dcss.zh.stable','CFBundleExecutable':'dcss-zh','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.34.1','NSHighResolutionCapable':True,'CFBundleIconFile':'Crawl.icns'}
    with (dest/'Contents/Info.plist').open('wb') as f: plistlib.dump(plist,f)
    executable(mac/'dcss-zh','''#!/bin/sh
set -eu
RES=$(CDPATH= cd -- "$(dirname -- "$0")/../Resources" && pwd)
STATE="$HOME/Library/Application Support/DCSS-zh/0.34"
MODE=${DCSS_MODE:-tiles}
mkdir -p "$STATE/saves" "$STATE/morgue"
if [ ! -f "$STATE/init.txt" ]; then
cat > "$STATE/init.txt" <<EOF
language = zh
save_dir = $STATE/saves
morgue_dir = $STATE/morgue
tile_full_screen = false
tile_font_crt_size = 24
tile_font_stat_size = 24
tile_font_msg_size = 24
tile_font_tip_size = 24
tile_font_lbl_size = 24
tile_font_crt_file = $RES/fonts/DCSSPixelSC-Regular.ttf
tile_font_msg_file = $RES/fonts/DCSSPixelSC-Regular.ttf
tile_font_stat_file = $RES/fonts/DCSSPixelSC-Regular.ttf
tile_font_tip_file = $RES/fonts/DCSSPixelSC-Regular.ttf
tile_font_lbl_file = $RES/fonts/DCSSPixelSC-Regular.ttf
EOF
fi
export DCSS_LANG=${DCSS_LANG:-zh}
cd "$RES"
exec "$RES/crawl-$MODE" -dir "$STATE" -rc "$STATE/init.txt" -extra-opt-last "language=$DCSS_LANG" "$@"
''')
    executable(dest.parent/'DCSS 中文版终端.command','''#!/bin/sh
export DCSS_MODE=console
exec "$(dirname "$0")/DCSS 中文版.app/Contents/MacOS/dcss-zh" "$@"
''')
    print(dest)
else:
    dest=a.dest or stage/'dcss-zh';dest.mkdir(parents=True,exist_ok=True);data(dest)
    for mode in ('tiles','console'): shutil.copy2(stage/f'crawl-{mode}',dest/f'crawl-{mode}')
    executable(dest/'dcss-zh','''#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
STATE="${XDG_DATA_HOME:-$HOME/.local/share}/dcss-zh/0.34"
MODE=${DCSS_MODE:-tiles}
mkdir -p "$STATE/saves" "$STATE/morgue"
if [ ! -f "$STATE/init.txt" ]; then
cat > "$STATE/init.txt" <<EOF
language = zh
save_dir = $STATE/saves
morgue_dir = $STATE/morgue
tile_full_screen = false
tile_font_crt_size = 24
tile_font_stat_size = 24
tile_font_msg_size = 24
tile_font_tip_size = 24
tile_font_lbl_size = 24
tile_font_crt_file = $BASE/fonts/DCSSPixelSC-Regular.ttf
tile_font_msg_file = $BASE/fonts/DCSSPixelSC-Regular.ttf
tile_font_stat_file = $BASE/fonts/DCSSPixelSC-Regular.ttf
tile_font_tip_file = $BASE/fonts/DCSSPixelSC-Regular.ttf
tile_font_lbl_file = $BASE/fonts/DCSSPixelSC-Regular.ttf
EOF
fi
export DCSS_LANG=${DCSS_LANG:-zh}
export LD_LIBRARY_PATH="$BASE/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$BASE"
exec "$BASE/crawl-$MODE" -dir "$STATE" -rc "$STATE/init.txt" -extra-opt-last "language=$DCSS_LANG" "$@"
''')
    opts = {line.split('=',1)[0].strip():line.split('=',1)[1].strip() for line in ((ROOT/'config/bazzite-4k.rc') if (ROOT/'config/bazzite-4k.rc').exists() else (ROOT/'config/4k.rc.in')).read_text().splitlines() if '=' in line}
    opts = {key: (f'$BASE/fonts/{Path(value).name}' if key.endswith('_file') else value) for key,value in opts.items()}
    extra = ' '.join(f'-extra-opt-last "{key}={value}"' for key,value in opts.items())
    executable(dest/'dcss-zh-4k', '#!/bin/sh\nset -eu\nBASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "$BASE/dcss-zh" ' + extra + ' "$@"\n')
    executable(dest/'dcss-zh-console','''#!/bin/sh
export DCSS_MODE=console
exec "$(dirname "$0")/dcss-zh" "$@"
''')
    print(dest)
