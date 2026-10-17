#!/usr/bin/env python3
"""Exercise source-generated menus on disposable copies of an existing save.

No original character is opened. Input is sent only to the new child PTY. The
source fixture is hashed before/after; strict migration guards remain enabled.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import tempfile
import termios
import time

p=argparse.ArgumentParser()
p.add_argument('--binary',required=True,type=Path)
p.add_argument('--data',required=True,type=Path)
p.add_argument('--saves',required=True,type=Path)
p.add_argument('--name',default='Awigithro')
p.add_argument('--out',required=True,type=Path)
p.add_argument('--scenes',default='weapon-detail,skills,skills-help,monster-detail,shop-selected')
p.add_argument('--require-complete',action='store_true',help='Fail on any missing ID or semantic name in the selected fixtures')
a=p.parse_args()
a.binary=a.binary.resolve();a.data=a.data.resolve();a.saves=a.saves.resolve();a.out=a.out.resolve()
a.out.mkdir(parents=True,exist_ok=True)
def hashes():
    return {str(f.relative_to(a.saves)):hashlib.sha256(f.read_bytes()).hexdigest()
            for f in a.saves.rglob('*') if f.is_file()}
before=hashes()
assert (a.saves/(a.name+'.cs')).exists(), 'Source fixture missing'
cases={'skill-lookup':'?/k','skill-lookup-detail':'?/ka','hud':'l','hud-wizard':'l&wiz\r ', 'spell-detail':'l&wiz\r!Magic Dart\ryIa','armour-detail':'ia','shop-examine':'l&wiz\r$1000\r&\\a>!a','weapon-detail':'ib','skills':'m','skills-help':'m?',
       'monster-detail':'llgllllllx+v','shop-selected':'l&wiz\r$1000\r&\\a>a',
       'shop-confirm':'l&wiz\r$1000\r&\\a>a\r',
       'shop-purchased':'l&wiz\r$1000\r&\\a>a\ry',
       'shop-list':'l&wiz\r$1000\r&\\a>a$\x1b$',
       'skills-description':'m?a','skills-enhanced':'m_','skills-general-help':'m??'}
# These scenes use the separately created hints-mode fixture, never a normal
# player's save with a forced game-type override.
cases.update({'hints-weapon':'ia','hints-armour':'ib',
 'hints-weapon-unwielded':'l&wiz\r%pre_id whip\rxrva',
 'hints-wand':'l&wiz\r%pre_id wand of flame\rxrva',
 'hints-missile':'l&wiz\r%pre_id javelin\rgic',
 'hints-jewellery':'l&wiz\r%pre_id ring of protection\rxrva',
 'hints-scroll':'l&wiz\r%pre_id scroll of identify\rxrva',
 'hints-potion':'l&wiz\r%pre_id potion of curing\rxrva',
 'hints-staff':'l&wiz\r%pre_id staff of fire\rgic',
 'hints-book':'l&wiz\r%pre_id book of Flames\rxrva',
 'hints-manual':'l&wiz\r%pre_id manual of Axes\rxrva',
 'hints-misc':'l&wiz\r%pre_id phial of floods\rxrva'})
# Cover every current ordinary staff identity and missile classifier through
# actual item generation (quantity fixed rather than trusting RNG stacks).
for label in ('air','alchemy','cold','conjuration','necromancy','earth','fire'):
    cases['hints-staff-'+label]='l&wiz\r%pre_id staff of '+label+'\rgic'
for label in ('dart','javelin','stone','large rock','throwing net','boomerang'):
    for qty in (1,3):
        cases['hints-missile-'+label.replace(' ','-')+'-'+str(qty)]='l&wiz\r%pre_id '+label+' q:'+str(qty)+'\rgic'
# Every current talisman subtype, each on a fresh disposable save copy.
item_source=(Path(__file__).resolve().parents[1]/'native/crawl-ref/source/item-prop.cc').read_text()
talisman_names=dict(re.findall(r'case TALISMAN_([A-Z_]+):\s*return "([^"]+)";',item_source))
for kind,name in talisman_names.items():
    cases['talisman-'+kind.lower()]='l&wiz\r%level:1 pre_id '+name+'\rgid'
results=[]
for scene in a.scenes.split(','):
    with tempfile.TemporaryDirectory(prefix='dcss-copy-'+scene+'-') as folder:
        import shutil
        state=Path(folder)
        shutil.copytree(a.saves,state/'saves')
        (state/'morgue').mkdir()
        (state/'dat').symlink_to(a.data/'dat',target_is_directory=True)
        docs=a.data/'docs'
        if not docs.exists():docs=a.data.parent/'docs'
        (state/'docs').symlink_to(docs,target_is_directory=True)
        dst=a.out/scene;dst.mkdir(exist_ok=True)
        for f in ('ids.tsv','missing.tsv','names.tsv','legacy.jsonl','values.tsv','boundaries.tsv'):
            (dst/f).unlink(missing_ok=True)
        rc=state/'init.txt'
        # Advance only the disposable fixture's RNG to avoid this save's
        # deterministic first low-tier talisman roll becoming a randart.
        rng_setup='for i=1,8 do crawl.random2(100) end; ' if scene.startswith('talisman-') else ''
        rc.write_text('language=zh\nshow_more=false\nsave_dir='+str(state/'saves')+
            '\nmorgue_dir='+str(state/'morgue')+'\n{\nlocal sent=false\nfunction ready()\n'+
            'if not sent then sent=true; '+rng_setup+'crawl.sendkeys('+json.dumps(cases[scene]).replace('\\u001b','\\027')+'); end\nend\n}\n')
        pid,fd=pty.fork()
        if pid==0:
            os.chdir(a.data)
            env={**os.environ,'TERM':'xterm-256color','LC_ALL':'C','DCSS_LANG':'zh',
                 'DCSS_ZH_STRICT_SOURCE':'1','DCSS_ZH_FORBID_LEGACY':'1',
                 'DCSS_ZH_BOUNDARY_TRACE':str((dst/'boundaries.tsv').resolve()),
                 'DCSS_ZH_MESSAGE_VALUES':str((dst/'values.tsv').resolve()),
                 'DCSS_ZH_ID_TRACE':str((dst/'ids.tsv').resolve()),
                 'DCSS_ZH_ID_MISSING':str((dst/'missing.tsv').resolve()),
                 'DCSS_ZH_NAME_MISSING':str((dst/'names.tsv').resolve()),
                 'DCSS_ZH_TRACE':str((dst/'legacy.jsonl').resolve())}
            os.execve(str(a.binary),[str(a.binary),'-dir',str(state),'-rc',str(rc),'-name',a.name],env)
        fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',52,140,0,0))
        transcript=bytearray();end=time.monotonic()+5
        while time.monotonic()<end:
            if select.select([fd],[],[],.1)[0]:
                try:chunk=os.read(fd,65536)
                except OSError:break
                if not chunk:break
                transcript.extend(chunk)
        status=os.waitpid(pid,os.WNOHANG)
        running=status==(0,0)
        if running:
            os.kill(pid,signal.SIGTERM)
            deadline=time.monotonic()+3
            while os.waitpid(pid,os.WNOHANG)==(0,0):
                if time.monotonic()>=deadline:
                    os.kill(pid,signal.SIGKILL);os.waitpid(pid,0);break
                time.sleep(.05)
        os.close(fd)
        text=transcript.decode('utf-8','replace')
        (dst/'transcript.txt').write_text(text)
        read=lambda file:(dst/file).read_text().splitlines() if (dst/file).exists() else []
        result={'scene':scene,'running_at_capture':running,'ids':read('ids.tsv'),
                'boundaries':read('boundaries.tsv'),'missing':read('missing.tsv'),'names':read('names.tsv'),'values':read('values.tsv'),
                'runtime_error':any(s in text for s in ('Legacy translation reached migrated boundary',
                    'Missing localization source:', 'ASSERT(', 'Lua error', 'terminate called', 'terminating due to', 'Invalid localization parameter', 'Invalid localization key', 'Lua 错误'))}
        results.append(result)
unchanged=before==hashes()
report={'source_fixture_unchanged':unchanged,'scenes':results}
(a.out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert unchanged, 'Source fixture changed'
assert all(r['running_at_capture'] and not r['runtime_error'] for r in results),[(r['scene'],r['missing']) for r in results if r['runtime_error'] or not r['running_at_capture']]
if a.require_complete:
    assert all(not r['missing'] and not r['names'] for r in results),[(r['scene'],r['missing'],r['names']) for r in results if r['missing'] or r['names']]
expected={
 'hints-weapon':{'item.hints.weapon.melee.wielded'},
 'hints-armour':{'item.hints.armour.wear_remove'},
 'hints-weapon-unwielded':{'item.hints.weapon.unwielded'},
 'hints-wand':{'item.hints.wand.use'},
 'hints-missile':{'item.hints.missile.throwable'},
 'hints-jewellery':{'item.hints.jewellery.wear_remove'},
 'hints-scroll':{'item.hints.scroll.use'},
 'hints-potion':{'item.hints.potion.use'},
 'hints-staff':{'item.hints.staff.school'},
 'hints-book':{'item.hints.book.spellbook'},
 'hints-manual':{'item.hints.book.manual'},
 'hints-misc':{'item.hints.misc.evocation'},
 'skill-lookup':{'skill.lookup.prompt'},
 'skill-lookup-detail':{'skill.lookup.prompt'},
 'hud':{'hud.experience.progress','hud.place.depth'},
 'hud-wizard':{'hud.experience.progress','hud.place.depth'},
    'skills':{'skill.menu.entry_name'},
    'skills-help':{'skill.menu.entry_name'},
    'skills-enhanced':{'skill.menu.default.aptitude'},
    'shop-selected':{'shop.balance','shop_gold_after_purchase','shop.help.sort'},
    'shop-confirm':{'shop.purchase.confirm'},
    'shop-list':{'shopping_list.title'},
    'shop-purchased':{'shop.purchase.confirm','shop.balance'},
    'spell-detail':{'spell.level'},
    'armour-detail':{'item.armour.base_rating'},
    'weapon-detail':{'item.weapon.base_stats','item.weapon.attack_delay_and_minimum'},
    'monster-detail':{'monster.hit_chance'},
}

for result in results:
    if result['scene'].startswith('hints-'):
        assert 'detail.item.hints\tenter' in result['boundaries'], (result['scene'], 'hint producer not reached')
    if result['scene'].startswith('talisman-') and result['scene']!='talisman-protean':
        assert 'detail.form\tenter' in result['boundaries'], (result['scene'], 'form producer not reached')
    ids={line.split('\t')[0] for line in result['ids']}
    if result['scene'].startswith('hints-staff-'):
        assert 'item.hints.staff.school' in ids,result['scene']
    if result['scene'].startswith('hints-missile-'):
        assert 'item.hints.missile.throwable' in ids,result['scene']
    assert expected.get(result['scene'],set()) <= ids,(result['scene'],ids)
    if result['scene'].startswith(('skills','skill-lookup')):
        assert not result['missing'],(result['scene'],result['missing'])
    if result['scene']=='shop-purchased':
        assert any(line.startswith('shop.balance\t') and '838' in line
                   for line in result['values']), 'Purchase did not update the balance to 838'

print(json.dumps({'source_fixture_unchanged':unchanged,'scenes':len(results)}))
