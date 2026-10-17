#!/usr/bin/env python3
"""Run on Bazzite: exercise real producers in disposable copies at native 4K.
No crawl.mpr injection. The source saves are hashed before/after, never opened.
"""
import hashlib,json,os,pathlib,shutil,subprocess,time
home=pathlib.Path.home(); source=home/'.local/share/dcss-zh/0.34'
save_source=pathlib.Path(os.environ.get('DCSS_QA_SAVES',str(source/'saves')))
base=pathlib.Path(os.environ.get('DCSS_QA_OUT','/tmp/dcss-message-migration-4k'));base.mkdir(exist_ok=True)
character=os.environ.get('DCSS_QA_NAME','Awigithro')
binary=pathlib.Path(os.environ.get('DCSS_QA_BINARY',str(home/'Games/dcss-zh/crawl-tiles')))
def hashes():
 return {str(p.relative_to(save_source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in save_source.rglob('*') if p.is_file()}
before=hashes();results=[]
cases=[('hud','l'),('hud-wizard','l&wiz\r '),('spell-detail','l&wiz\r!Magic Dart\ryIa'),('armour-detail','ia'),('shop-examine','l&wiz\r$1000\r&\\a>!a'),('shop-selected','l&wiz\r$1000\r&\\a>a'),('level-five','l&wiz\rl5\r'),('combat','l&wiz\rmrat\r'+ '\t'*12),('equipment','l&wiz\riTaWa.....'),('weapon-detail','ib'),('skills','m'),('skills-help','m?'),('skills-description','m?a'),('skills-enhanced','m_'),('skills-general-help','m??'),('shop-confirm','l&wiz\r$1000\r&\\a>a\r'),('shop-purchased','l&wiz\r$1000\r&\\a>a\ry'),('shop-list','l&wiz\r$1000\r&\\a>a$\x1b$'),('monster-detail','llgllllllx+v'),('manual-long','?k')]
# Independent hints-mode fixture; each scene gets its own disposable copy.
cases += [('hints-armour','ib'),('hints-wand','l&wiz\r%pre_id wand of flame\rgi\t\t\ta'),
          ('hints-missile','l&wiz\r%pre_id javelin\rgic'),
          ('hints-staff','l&wiz\r%pre_id staff of fire\rgic'),
          ('hints-scroll','l&wiz\r%pre_id scroll of identify\rxrva'),
          ('hints-potion','l&wiz\r%pre_id potion of curing\rxrva'),
          ('hints-book','l&wiz\r%pre_id book of Flames\rxrva'),
          ('hints-manual','l&wiz\r%pre_id manual of Axes\rxrva'),
          ('hints-misc','l&wiz\r%pre_id phial of floods\rxrva')]
from qa_restriction_scenes import RESTRICTION_SCENES, RESTRICTION_EXPECTED
cases += list(RESTRICTION_SCENES.items())
if os.environ.get('DCSS_QA_SCENES'):
 cases=[c for c in cases if c[0] in os.environ['DCSS_QA_SCENES'].split(',')]
x=subprocess.Popen(['Xvfb',':96','-screen','0','3840x2160x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(2)
# Keep the disposable X display's pointer outside the map: mouse aim must not
# replace the keyboard fixture's target with an unseen cell at screen centre.
subprocess.run(['xdotool','mousemove','3839','2159'],
               env={**os.environ,'DISPLAY':':96'},check=True)
try:
 for name,keys in cases:
  tmp=base/name
  if tmp.exists():shutil.rmtree(tmp)
  tmp.mkdir()
  for folder in ('dat','docs'):(tmp/folder).symlink_to(home/'Games/dcss-zh/game'/folder,target_is_directory=True)
  shutil.copytree(save_source,tmp/'saves')
  rc=(source/'init.txt').read_text().replace(str(source/'saves'),str(tmp/'saves')).replace(str(source/'morgue'),str(tmp/'morgue'))
  rc+='\nshow_more=false\n{\nlocal checked=false\nfunction ready()\nif not checked then checked=true; crawl.sendkeys('+json.dumps(keys).replace('\\u001b','\\027').replace('\\u0004','\\004')+'); end\nend\n}\n'
  (tmp/'init.txt').write_text(rc)
  env={**os.environ,'DISPLAY':':96','LC_ALL':'C','DCSS_LANG':'zh','DCSS_ZH_FORBID_LEGACY':'1','DCSS_ZH_STRICT_SOURCE':'1','DCSS_ZH_TRACE':str(tmp/'legacy.jsonl'),'DCSS_ZH_BOUNDARY_TRACE':str(tmp/'boundaries.tsv'),'DCSS_ZH_MESSAGE_VALUES':str(tmp/'values.tsv'),'DCSS_ZH_ID_TRACE':str(tmp/'ids.tsv'),'DCSS_ZH_ID_MISSING':str(tmp/'missing.tsv'),'DCSS_ZH_NAME_MISSING':str(tmp/'names.tsv'),'LD_LIBRARY_PATH':str(home/'Games/dcss-zh/game/lib')}
  with (tmp/'run.log').open('w') as log:
   p=subprocess.Popen([str(binary),'-dir',str(tmp),'-rc',str(tmp/'init.txt'),'-name',character,'-extra-opt-last','tile_skip_title=true'],cwd=home/'Games/dcss-zh/game',env=env,stdout=log,stderr=log)
   # Software rendering may take tens of seconds to finish loading at 4K.
   # Wait for a real producer trace, then let its frame settle; a live splash
   # screen is not evidence that the requested scenario was reached.
   started=time.monotonic()
   deadline=started+90
   trap_followup=0
   reached=False
   while p.poll() is None and time.monotonic()<deadline:
    wanted = ('detail.item.hints' if name.startswith('hints-') else
              'hud.' if name.startswith('hud') else
              'skill.menu' if name.startswith('skills') else
              'detail.spell' if name=='spell-detail' else
              'detail.item' if name in ('weapon-detail','armour-detail','shop-examine') else
              'detail.monster' if name=='monster-detail' else
              'shop.' if name.startswith('shop-') else '')
    trace=(tmp/'boundaries.tsv').read_text() if (tmp/'boundaries.tsv').exists() else ''
    ids=(tmp/'ids.tsv').read_text() if (tmp/'ids.tsv').exists() else ''
    ready=(all(identity+'\t' in ids for identity in RESTRICTION_EXPECTED[name])
           if name in RESTRICTION_EXPECTED else
           bool(wanted and wanted in trace or not wanted and ids))
    # Hints trap discovery opens a forced more screen and drops queued input
    # in local tiles. Advance only this disposable X display, then perform the
    # actual leave/re-enter movement. A traced expected confirmation is still
    # required below; this is input staging, not a synthetic UI message.
    if (name in ('terrain-alarm','terrain-zot') and trap_followup < 3
            and ids and time.monotonic()-started>=12 + 6*trap_followup and not ready):
     subprocess.run(['xdotool','key','space'],env=env,check=True)
     time.sleep(.5)
     subprocess.run(['xdotool','key','--delay','150','h','l','h'],env=env,check=True)
     trap_followup+=1
    if ready:
     reached=True
     # SDL may centre the pointer after window creation. Reapply keyboard aim
     # after loading; otherwise the mouse can choose an unseen cell instead.
     if name in ('external-passwall','external-inner-flame','external-simulacrum','external-crocodile'):
      subprocess.run(['xdotool','mousemove','3839','2159'],env=env,check=True)
      time.sleep(.5)
      keys=['r','period'] if name=='external-passwall' else ['r','h','period']
      subprocess.run(['xdotool','key']+keys,env=env,check=True)
     time.sleep(3)
     break
    time.sleep(.5)
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
   results.append({'scene':name,'keys':keys,'running_at_capture':running,'scene_reached':reached,'id_trace':read('ids.tsv').splitlines(),'boundaries':read('boundaries.tsv').splitlines(),'missing':read('missing.tsv').splitlines(),'values':read('values.tsv').splitlines(),'names':read('names.tsv').splitlines(),'legacy':read('legacy.jsonl').splitlines(),'lua_error':any(e in read('run.log') for e in ('Lua error','Legacy translation reached migrated boundary','Missing localization source:','terminate called', 'terminating due to', 'Invalid localization parameter', 'Invalid localization key', 'Lua 错误', 'unterminated <input>', '未终止的 <input>'))})
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
 'hints-armour':{'item.hints.armour.wear_remove'},
 'hints-wand':{'item.hints.wand.use','item.wand.damage','item.wand.noise'},
 'hints-scroll':{'item.hints.scroll.use'},
 'hints-potion':{'item.hints.potion.use'},
 'hints-book':{'item.hints.book.spellbook'},
 'hints-manual':{'item.hints.book.manual'},
 'hints-misc':{'item.hints.misc.evocation'},
 'hints-missile':{'item.hints.missile.throwable'},
 'hints-staff':{'item.hints.staff.school'},
 'hud':{'hud.experience.progress','hud.place.depth'},
 'hud-wizard':{'hud.experience.progress','hud.place.depth'},
 'skills':{'skill.menu.entry_name'},
 'skills-help':{'skill.menu.entry_name'},
 'skills-enhanced':{'skill.menu.default.aptitude'},
 'shop-confirm':{'shop.purchase.confirm'},
 'shop-list':{'shopping_list.title'},
 'shop-purchased':{'shop.purchase.confirm','shop.balance'},
 'shop-selected':{'shop.balance','shop_gold_after_purchase','shop.help.sort'},
 'level-five':{'level_reached'},
 'combat':{'log.combat.player_hit','log.combat.monster_hit','log.combat.player_miss'},
 'equipment':{'equip_start','equip_continue','equip_finish'},
 'spell-detail':{'spell.level'},
 'weapon-detail':{'item.weapon.base_stats','item.weapon.attack_delay_and_minimum'},
 'monster-detail':{'monster.hit_chance','target.hit_chance.verbose'},
}
expected.update(RESTRICTION_EXPECTED)
for result in results:
 assert result['scene_reached'] and result['running_at_capture'] and not result['lua_error'],result['scene']
 ids={line.split('\t')[0] for line in result['id_trace']}
 assert expected.get(result['scene'],set()) <= ids,(result['scene'],ids)
 if result['scene'].startswith('hints-') or result['scene'] in RESTRICTION_EXPECTED:
  assert not result['missing'],(result['scene'],result['missing'])
  assert not result['names'],(result['scene'],result['names'])
 if result['scene'].startswith('skills') or result['scene'] in ('combat','equipment','weapon-detail'):
  assert not result['missing'],(result['scene'],result['missing'])
for result in results:
 if result['scene']=='shop-purchased':
  assert any(line.startswith('shop.balance\t') and '838' in line for line in result['values']), 'Balance after purchase must be 838'
print(json.dumps({'original_saves_unchanged':unchanged,'scenes':len(results),'ids':len(set(line.split('\t')[0] for r in results for line in r['id_trace']))}))
