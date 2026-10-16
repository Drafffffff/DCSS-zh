import subprocess,pathlib,shutil,time,os,json
home=pathlib.Path.home(); state=home/'.local/share/dcss-zh/0.34';base=pathlib.Path('/tmp/dcss-review-20261017-after');base.mkdir(exist_ok=True)
x=subprocess.Popen(['Xvfb',':96','-screen','0','3840x2160x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(2)
results=[]
try:
 for name,key in [('map',''),('monster','llgllllllx+v'),('weapon','llgic'),('stairs','xv'),('messages','llg\x10'),('shortbow','ia'),('combat-log','\x10')]:
  locale='C'
  tmp=base/name;tmp.mkdir(exist_ok=True)
  for folder in ('dat','docs'):
   if not (tmp/folder).exists():(tmp/folder).symlink_to(home/'Games/dcss-zh/game'/folder,target_is_directory=True)
  shutil.copytree(state/'saves',tmp/'saves',dirs_exist_ok=True)
  rc=(state/'init.txt').read_text().replace(str(state/'saves'),str(tmp/'saves')).replace(str(state/'morgue'),str(tmp/'morgue'))
  replay = ''
  if name == 'combat-log':
   replay = ''.join('crawl.mpr('+json.dumps(line)+'); ' for line in ['You hit the rat.', 'You bludgeon the rat!', 'You kill the rat!', 'You shoot an arrow.', 'The arrow hits the worm but does no damage.', 'You have reached level 5!', 'There is an open door here.', 'You see here a rat corpse.'])
  rc+='\nshow_more=false\n{\nlocal checked=false\nfunction ready()\nif not checked then checked=true; crawl.sendkeys('+json.dumps(('   '+key) if name == 'combat-log' else key).replace('\\u0010', '\\016')+'); '+replay+' end\nend\n}\n'
  (tmp/'init.txt').write_text(rc)
  env={**os.environ,'DISPLAY':':96','LC_ALL':locale,'DCSS_ZH_TRACE':str(tmp/'trace.jsonl'),'LANG':'zh_CN.UTF-8','LD_LIBRARY_PATH':str(home/'Games/dcss-zh/game/lib')}
  (tmp/'trace.jsonl').unlink(missing_ok=True)
  with (tmp/'run.log').open('w') as log:
   p=subprocess.Popen([str(home/'Games/dcss-zh/crawl-tiles'),'-dir',str(tmp),'-rc',str(tmp/'init.txt'),'-name',('ZhBow' if name == 'shortbow' else 'Awigithro'),*(['-species','Hu','-background','Hu'] if name == 'shortbow' else []),'-extra-opt-last','tile_skip_title=true'],cwd=str(home/'Games/dcss-zh/game'),env=env,stdout=log,stderr=log)
   time.sleep(8)
   assert p.poll() is None,(locale,(tmp/'run.log').read_text())
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','x11grab','-draw_mouse','0','-i',':96','-frames:v','1',str(base/(name+'.png'))],env=env,check=True)
   results.append({'locale':locale,'running_at_capture':p.poll() is None})
   p.terminate()
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:p.kill();p.wait()
finally:
 x.terminate();x.wait(timeout=10)
 (base/'results.json').write_text(json.dumps(results,indent=2))
