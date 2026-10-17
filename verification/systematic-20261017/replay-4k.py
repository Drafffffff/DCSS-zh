import subprocess,pathlib,shutil,time,os,json,re
home=pathlib.Path.home(); state=home/'.local/share/dcss-zh/0.34';base=pathlib.Path('/tmp/dcss-systematic-20261017-after');base.mkdir(exist_ok=True)
x=subprocess.Popen(['Xvfb',':96','-screen','0','3840x2160x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(2)
results=[]
try:
 for name,key in [('shop-menu','l&wiz\r\\a>'),('combat-log',''),('equipment-log',''),('shop-log',''),('manual-mutations','?k'),('quickstart','?^'),('tiles-help','?t'),('monster','llgllllllx+v'),('weapon','llgic')]:
  locale='C'
  tmp=base/name;tmp.mkdir(exist_ok=True)
  for folder in ('dat','docs'):
   if not (tmp/folder).exists():(tmp/folder).symlink_to(home/'Games/dcss-zh/game'/folder,target_is_directory=True)
  shutil.copytree(state/'saves',tmp/'saves',dirs_exist_ok=True)
  rc=(state/'init.txt').read_text().replace(str(state/'saves'),str(tmp/'saves')).replace(str(state/'morgue'),str(tmp/'morgue'))
  replay = ''
  messages = {
   'combat-log': ['You encounter a rat.', 'The rat bites you.', 'The wyvern is nearby!', 'The arrow barely misses the worm.', 'Snorg blocks the arrow with his shield... and reflects it back!', "The rat's fire resistance burns away.", 'You have reached level 5!', 'Found three staircases leading out of the dungeon.', 'There is an open door, spattered with blood here.', 'Really walk onto that pressure plate?'],
   'equipment-log': ['You continue putting on your amulet of faith.']*5 + ['You finish putting on your amulet of faith.', 'You continue putting on your amulet of reflection.', 'You finish putting on your amulet of reflection.'],
   'shop-log': ["Welcome to Utarac's General Store! What would you like to do?", "There is an entrance to Utarac's General Store here.", '<yellow>You have 260 gold pieces. After the purchase, you will have 134 gold pieces.</yellow>', '<yellow>You have 1 gold piece and a voucher.<lightred> You are short 53 gold pieces for the purchase.</lightred></yellow>', 'You now have 260 gold pieces (gained 220).', "Thank you for shopping at Utarac's General Store!"]
  }
  if name in messages:
   replay = ''.join('crawl.mpr('+json.dumps(line)+'); ' for line in messages[name])
  rc+='\nshow_more=false\n{\nlocal checked=false\nfunction ready()\nif not checked then checked=true; crawl.sendkeys('+json.dumps('' if name in messages else key).replace(r'\u0010', r'\016')+'); '+replay+' end\nend\n}\n'
  (tmp/'init.txt').write_text(rc)
  env={**os.environ,'DISPLAY':':96','LC_ALL':locale,'DCSS_ZH_TRACE':str(tmp/'trace.jsonl'),'LANG':'zh_CN.UTF-8','LD_LIBRARY_PATH':str(home/'Games/dcss-zh/game/lib')}
  (tmp/'trace.jsonl').unlink(missing_ok=True)
  with (tmp/'run.log').open('w') as log:
   p=subprocess.Popen([str(home/'Games/dcss-zh/crawl-tiles'),'-dir',str(tmp),'-rc',str(tmp/'init.txt'),'-name',('ZhBow' if name == 'shortbow' else 'Awigithro'),*(['-species','Hu','-background','Hu'] if name == 'shortbow' else []),'-extra-opt-last','tile_skip_title=true'],cwd=str(home/'Games/dcss-zh/game'),env=env,stdout=log,stderr=log)
   time.sleep(8)
   if name in messages:
    subprocess.run(['xdotool','key','space'],env=env,check=True)
    time.sleep(.5)
    subprocess.run(['xdotool','key','ctrl+p'],env=env,check=True)
    time.sleep(1)
   assert p.poll() is None,(locale,(tmp/'run.log').read_text())
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','x11grab','-draw_mouse','0','-i',':96','-frames:v','1',str(base/(name+'.png'))],env=env,check=True)
   trace=(tmp/'trace.jsonl').read_text()
   sources=[re.sub(r'<[^>]*>','',json.loads(line)['en']) for line in trace.splitlines()]
   assert 'Lua error' not in trace and 'canonical' not in (tmp/'run.log').read_text()
   if name in messages:
    for message in messages[name]:
     assert any(re.sub(r'<[^>]*>','',message) in source for source in sources), (name, message)
   results.append({'name':name,'locale':locale,'running_at_capture':p.poll() is None,'injected_sources_verified':len(messages.get(name,[]))})
   p.terminate()
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:p.kill();p.wait()
finally:
 x.terminate();x.wait(timeout=10)
 (base/'results.json').write_text(json.dumps(results,indent=2))
