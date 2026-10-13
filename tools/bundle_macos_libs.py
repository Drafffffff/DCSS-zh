#!/usr/bin/env python3
"""Vendor Mach-O Homebrew dependencies; rewrite to relative loader paths and sign."""
import argparse, subprocess, shutil, json, hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('app',type=Path);args=p.parse_args()
res=args.app/'Contents/Resources';lib=res/'lib';lib.mkdir(exist_ok=True)
licenses=res/'third-party-licenses';licenses.mkdir(exist_ok=True)
def run(*args): return subprocess.check_output(args,text=True)
def deps(path): return [line.strip().split(' (',1)[0] for line in run('otool','-L',str(path)).splitlines()[1:]]
queue=[res/'crawl-tiles',res/'crawl-console'];seen=set();origins={}
# SDL2-compat loads SDL3 at runtime rather than through a Mach-O load command.
sdl3=Path('/opt/homebrew/opt/sdl3/lib/libSDL3.0.dylib')
if sdl3.exists():
 dest=lib/sdl3.name;shutil.copy2(sdl3,dest);dest.chmod(0o755)
 origins[dest]=sdl3;queue.append(dest)
 alias=lib/'libSDL3.dylib'
 if alias.exists() or alias.is_symlink(): alias.unlink()
 alias.symlink_to(sdl3.name)
while queue:
 path=queue.pop(0)
 if path in seen: continue
 seen.add(path)
 for dep in deps(path):
  if dep.startswith('/opt/homebrew/'):
   src=Path(dep)
  elif dep.startswith(('@rpath/', '@loader_path/')) and path in origins:
   source=origins[path]
   tail=dep.split('/',1)[1]
   candidates=[source.parent/tail,source.resolve().parent/tail,Path('/opt/homebrew/lib')/Path(tail).name]
   src=next((p for p in candidates if p.exists()),None)
   if src is None: raise RuntimeError(f'Cannot resolve {dep} from {source}')
  else:
   continue
  if src.name=='libSDL2-2.0.0.dylib': src=Path('/opt/homebrew/opt/sdl2/lib/libSDL2-2.0.0.dylib')
  dest=lib/src.name
  if dest not in origins:
   shutil.copy2(src,dest);dest.chmod(0o755);origins[dest]=src;queue.append(dest)
  subprocess.run(['install_name_tool','-change',dep,('@loader_path/' if path.parent==lib else '@loader_path/lib/')+dest.name,str(path)],check=True,capture_output=True)
 if path.parent==lib:
  subprocess.run(['install_name_tool','-id','@loader_path/'+path.name,str(path)],check=True,capture_output=True)
records=[]
for dest,src in origins.items():
 prefix=src.resolve().parent.parent
 target=licenses/prefix.parent.name;target.mkdir(exist_ok=True)
 for pat in ('*LICENSE*','*COPYING*','*NOTICE*','share/licenses/**/*','share/doc/**/*COPYING*','share/doc/**/*LICENSE*'):
  for f in prefix.glob(pat):
   if f.is_file():
    out=target/f.relative_to(prefix);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out)
 records.append({'library':dest.name,'formula':prefix.parent.name,'version':prefix.name,'source_path':str(src),'bundled_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
for path in seen:
 remaining=[d for d in deps(path) if d.startswith(('/opt/homebrew/','@rpath/')) or (d.startswith('@loader_path/') and not (path.parent/d.split('/',1)[1]).exists())]
 if remaining: raise RuntimeError((str(path),remaining))
 subprocess.run(['codesign','--force','--sign','-',str(path)],check=True,capture_output=True)
# Record formula/version rather than private build paths.
for r in records: del r['source_path']
(res/'bundled-libraries.json').write_text(json.dumps(records,indent=2)+'\n')
print(f'Bundled {len(origins)} libraries; no external Homebrew load commands remain.')
