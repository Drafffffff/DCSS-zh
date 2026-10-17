#!/usr/bin/env python3
"""PTY smoke test with isolated saves; checks Chinese and canonical English Lua history."""
import argparse,fcntl,json,os,pty,re,select,signal,struct,tempfile,termios,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('binary');p.add_argument('--data',required=True);p.add_argument('--out',required=True)
p.add_argument('--locale',default='en_US.UTF-8');p.add_argument('--extended',action='store_true');p.add_argument('--species',default='Mi');p.add_argument('--background',default='Be');a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
trace=out.resolve()/'trace.jsonl'
if a.extended: trace.unlink(missing_ok=True)
with tempfile.TemporaryDirectory(prefix='dcss-zh-smoke-') as td:
    state=Path(td);(state/'saves').mkdir();(state/'morgue').mkdir()
    (state/'dat').symlink_to(Path(a.data).resolve()/'dat',target_is_directory=True)
    docs=Path(a.data).resolve()/'docs'
    if not docs.exists(): docs=Path(a.data).resolve().parent/'docs'
    (state/'docs').symlink_to(docs,target_is_directory=True)
    rc=state/'init.txt';rc.write_text(f'''language = zh
save_dir = {state}/saves
morgue_dir = {state}/morgue
show_more = false
{{
local zh_checked = false
local zh_raw_seen = false
function c_message(text, channel)
  if string.find(text, "You feel better.", 1, true) then zh_raw_seen = true end
end
function ready()
  if zh_checked then return end
  zh_checked = true
  crawl.mpr("You feel better.")
  assert(zh_raw_seen, "canonical c_message hook failed")
  assert(string.find(crawl.messages(20), "You feel better.", 1, true), "canonical Lua history failed")
  for _, item in ipairs(items.inventory()) do
    local description = item.description
    assert(not string.find(description, "基础", 1, true), "canonical Lua item description failed")
  end
  crawl.mpr("ZH_CANONICAL_HISTORY_OK")
end
}}
''')
    pid,fd=pty.fork()
    if pid==0:
        os.chdir(a.data)
        env=dict(os.environ,TERM='xterm-256color',LANG=a.locale,LC_ALL=a.locale,DCSS_LANG='zh')
        if a.extended:
            env['DCSS_ZH_TRACE']=str(trace)
            env['DCSS_ZH_ID_TRACE']=str(out.resolve()/'ids.tsv')
            env['DCSS_ZH_ID_MISSING']=str(out.resolve()/'missing.tsv')
            env['DCSS_ZH_NAME_MISSING']=str(out.resolve()/'names.tsv')
        os.execve(a.binary,[a.binary,'-dir',str(state),'-rc',str(rc),'-name','ZhSmoke','-species',a.species,'-background',a.background,'-seed','1234'],env)
    fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',42,120,0,0))
    buf=bytearray()
    def read_for(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            r,_,_=select.select([fd],[],[],.1)
            if r:
                try: b=os.read(fd,65536)
                except OSError:return
                if not b:return
                buf.extend(b)
    read_for(12)
    frames=[{'keys':'startup','offset':len(buf)}]
    keys_to_send=[b'a',b'\r',b'\r']
    if a.extended:
        for key in (b'Tb', b'Wb', b'i', b'ia', b'm', b'm?', b'%', b'A', b'^', b'a', b'I', b'M', b'\\', b'X', b'?', b'??'):
            keys_to_send += [key,b'\x1b\x1b']
    keys_to_send += [b'?',b'\x1b',b'S',b'y']
    for keys in keys_to_send:
        try:os.write(fd,keys)
        except OSError:break
        read_for(1 if a.extended else 2)
        frames.append({'keys':keys.hex(),'offset':len(buf)})
    read_for(2)
    result=os.waitpid(pid,os.WNOHANG)
    saved=any((state/'saves').glob('*.cs'))
    if not result[0]:
        os.kill(pid,signal.SIGTERM);os.waitpid(pid,0)
    os.close(fd)
    text=buf.decode('utf-8','replace');(out/'console-raw.txt').write_text(text)
    (out/'frames.json').write_text(json.dumps(frames,indent=2)+'\n')
    clean=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b[()][A-Z0-9]|\x1b[=>]|\r','',text)
    (out/'console.txt').write_text(clean)
    report={'chinese_characters':len(re.findall('[\u3400-\u9fff]',clean)),'canonical_lua_history':'ZH_CANONICAL_HISTORY_OK' in clean,'saved':saved,'exit_success':bool(result[0] and os.waitstatus_to_exitcode(result[1])==0),'assertion_error':bool(re.search('canonical .*failed|ASSERT|Segmentation fault',clean))}
    (out/'smoke.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    assert report['chinese_characters']>20 and report['canonical_lua_history'] and report['saved'] and report['exit_success'] and not report['assertion_error']
