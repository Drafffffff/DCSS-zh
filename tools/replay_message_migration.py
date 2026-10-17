#!/usr/bin/env python3
"""Run on Bazzite: exercise real producers in disposable copies at native 4K.
No crawl.mpr injection. The source saves are hashed before/after, never opened.
"""
import hashlib,json,os,pathlib,shutil,subprocess,time
home=pathlib.Path.home(); source=home/'.local/share/dcss-zh/0.34'
base=pathlib.Path('/tmp/dcss-message-migration-4k');base.mkdir(exist_ok=True)
def hashes():
 return {str(p.relative_to(source/'saves')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'saves').rglob('*') if p.is_file()}
before=hashes();results=[]
cases=[('shop-selected','l&wiz\r$1000\r&\\a>a'),('level-five','l&wiz\rl5\r'),('combat','l&wiz\rmrat\r'+ '\t'*12),('equipment','l&wiz\riTaWa.....'),('weapon-detail','ib'),('skills','m'),('monster-detail','llgllllllx+v'),('manual-long','?k')]
if os.environ.get('DCSS_QA_SCENES'):
 cases=[c for c in cases if c[0] in os.environ['DCSS_QA_SCENES'].split(',')]
x=subprocess.Popen(['Xvfb',':96','-screen','0','3840x2160x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(2)
try:
 for name,keys in cases:
  tmp=base/name
  if tmp.exists():shutil.rmtree(tmp)
  tmp.mkdir()
  for folder in ('dat','docs'):(tmp/folder).symlink_to(home/'Games/dcss-zh/game'/folder,target_is_directory=True)
  shutil.copytree(source/'saves',tmp/'saves')
  rc=(source/'init.txt').read_text().replace(str(source/'saves'),str(tmp/'saves')).replace(str(source/'morgue'),str(tmp/'morgue'))
  rc+='\nshow_more=false\n{\nlocal checked=false\nfunction ready()\nif not checked then checked=true; crawl.sendkeys('+json.dumps(keys)+'); end\nend\n}\n'
  (tmp/'init.txt').write_text(rc)
  env={**os.environ,'DISPLAY':':96','LC_ALL':'C','DCSS_LANG':'zh','DCSS_ZH_ID_TRACE':str(tmp/'ids.tsv'),'DCSS_ZH_ID_MISSING':str(tmp/'missing.tsv'),'DCSS_ZH_NAME_MISSING':str(tmp/'names.tsv'),'LD_LIBRARY_PATH':str(home/'Games/dcss-zh/game/lib')}
  with (tmp/'run.log').open('w') as log:
   p=subprocess.Popen([str(home/'Games/dcss-zh/crawl-tiles'),'-dir',str(tmp),'-rc',str(tmp/'init.txt'),'-name','Awigithro','-extra-opt-last','tile_skip_title=true'],cwd=home/'Games/dcss-zh/game',env=env,stdout=log,stderr=log)
   time.sleep(9)
   if name == 'level-five':
    for key in ('space', 's', 'space', 'space'):
     subprocess.run(['xdotool','key',key],env=env,check=True)
     time.sleep(.5)
   running=p.poll() is None
   if running:subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','x11grab','-draw_mouse','0','-i',':96','-frames:v','1',str(base/(name+'.png'))],env=env,check=True)
   if running and name == 'level-five':
    subprocess.run(['xdotool','key','ctrl+p'],env=env,check=True)
    time.sleep(.5)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','x11grab','-draw_mouse','0','-i',':96','-frames:v','1',str(base/'level-history.png')],env=env,check=True)
   read=lambda f:(tmp/f).read_text() if (tmp/f).exists() else ''
   results.append({'scene':name,'keys':keys,'running_at_capture':running,'id_trace':read('ids.tsv').splitlines(),'missing':read('missing.tsv').splitlines(),'names':read('names.tsv').splitlines(),'lua_error':'Lua error' in read('run.log')})
   if running:
    p.terminate()
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:p.kill();p.wait()
finally:
 x.terminate();x.wait(timeout=10)
 unchanged=before==hashes()
 (base/'results.json').write_text(json.dumps({'original_saves_unchanged':unchanged,'scenes':results},ensure_ascii=False,indent=2)+'\n')
 assert unchanged,'Original saves changed externally during test'
expected={
 'shop-selected':{'shop.balance','shop_gold_after_purchase','shop.help.sort'},
 'level-five':{'level_reached'},
 'combat':{'log.combat.player_hit','log.combat.monster_hit','log.combat.player_miss'},
 'equipment':{'equip_start','equip_continue','equip_finish'},
 'weapon-detail':{'item.weapon.base_stats','item.weapon.attack_delay_and_minimum'},
 'monster-detail':{'monster.hit_chance','target.hit_chance.verbose'},
}
for result in results:
 assert result['running_at_capture'] and not result['lua_error'],result['scene']
 ids={line.split('\t')[0] for line in result['id_trace']}
 assert expected.get(result['scene'],set()) <= ids,(result['scene'],ids)
 if result['scene'] in ('combat','equipment','weapon-detail'):
  assert not result['missing'],(result['scene'],result['missing'])
print(json.dumps({'original_saves_unchanged':unchanged,'scenes':len(results),'ids':len(set(line.split('\t')[0] for r in results for line in r['id_trace']))}))
