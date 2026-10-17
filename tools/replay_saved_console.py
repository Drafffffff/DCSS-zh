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
p.add_argument('--startup-timeout',type=float,default=30,help='Wait for real hints producer completion instead of a fixed loading delay')
p.add_argument('--require-complete',action='store_true',help='Fail on any missing ID or semantic name in the selected fixtures')
p.add_argument('--verify-only',action='store_true',help='Recheck saved capture evidence without opening a game or modifying a save copy')
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
from qa_restriction_scenes import RESTRICTION_SCENES, RESTRICTION_EXPECTED, RESTRICTION_FOLLOWUPS
cases.update(RESTRICTION_SCENES)
saved_report=json.loads((a.out/'results.json').read_text()) if a.verify_only else None
results=saved_report['scenes'] if a.verify_only else []
for scene in ([] if a.verify_only else a.scenes.split(',')):
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
            'if not sent then sent=true; '+rng_setup+'crawl.sendkeys('+json.dumps(cases[scene]).replace('\\u001b','\\027').replace('\\u0004','\\004')+'); end\nend\n}\n')
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
        reached_at=None; wall_followup_sent=False; wall_followup_due=None
        transcript=bytearray();end=time.monotonic()+(a.startup_timeout if scene.startswith(('hints-','speech-')) or scene in RESTRICTION_EXPECTED else 5)
        while time.monotonic()<end:
            if select.select([fd],[],[],.1)[0]:
                try:chunk=os.read(fd,65536)
                except OSError:break
                if not chunk:break
                transcript.extend(chunk)
                # Forced tutorial/religion more prompts require real child-PTY input.
                if b"--more--" in chunk: os.write(fd,b" ")
                if (scene in RESTRICTION_FOLLOWUPS and not wall_followup_sent
                        and RESTRICTION_FOLLOWUPS[scene]['trigger'].encode() in transcript):
                    wall_followup_sent=True
                    wall_followup_due=time.monotonic()+.5
            if wall_followup_due is not None and time.monotonic()>=wall_followup_due:
                os.write(fd,RESTRICTION_FOLLOWUPS[scene]['keys'].encode())
                wall_followup_due=None
            if scene in RESTRICTION_EXPECTED:
                trace=dst/'ids.tsv'
                if trace.exists() and all(identity+'\t' in trace.read_text() for identity in RESTRICTION_EXPECTED[scene]):
                    if reached_at is None: reached_at=time.monotonic()
                    if time.monotonic()-reached_at>=2: break
            if scene.startswith('hints-'):
                trace=dst/'boundaries.tsv'
                ids=dst/'ids.tsv'
                if (trace.exists() and 'detail.item.hints\tenter' in trace.read_text()
                        and ids.exists() and 'item.hints.' in ids.read_text()):
                    time.sleep(.3)
                    break
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
        for crash in (state/'morgue').glob('crash-*'):
            shutil.copy2(crash,dst/crash.name)
        text=transcript.decode('utf-8','replace')
        (dst/'transcript.txt').write_text(text)
        read=lambda file:(dst/file).read_text().splitlines() if (dst/file).exists() else []
        result={'scene':scene,'running_at_capture':running,'early_exit_status':None if running else status[1],'ids':read('ids.tsv'),
                'boundaries':read('boundaries.tsv'),'missing':read('missing.tsv'),'names':read('names.tsv'),'values':read('values.tsv'),
                'runtime_error':any(s in text for s in ('Legacy translation reached migrated boundary',
                    'Missing localization source:', 'ASSERT(', 'Lua error', 'terminate called', 'terminating due to', 'Invalid localization parameter', 'Invalid localization key', 'Lua 错误', 'unterminated <input>', '未终止的 <input>'))}
        results.append(result)
unchanged=saved_report['source_fixture_unchanged'] if a.verify_only else before==hashes()
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

expected.update(RESTRICTION_EXPECTED)
for result in results:
    if result['scene'].startswith(('external-','channel-')):
        # ID tracing also observes speculative target probes. Require each
        # intended complete reviewed sentence in the actual child terminal.
        catalogue=json.loads((Path(__file__).resolve().parents[1]/'localization/migration/luna-external-target-reasons-messages.json').read_text())
        reviewed={m['id']:m for m in catalogue['messages']}
        terminal=(a.out/result['scene']/'transcript.txt').read_text()
        terminal=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',terminal)
        terminal=re.sub(r'\x1b[()][A-Za-z0-9]','',terminal)
        visible=[]
        for ident in sorted(RESTRICTION_EXPECTED[result['scene']]):
            message=reviewed[ident]
            assert not message['params'],(result['scene'], 'visible oracle needs parameter binding',ident)
            sentence=re.sub(r'<[^>]+>','',message['zh']).replace('%','.')
            assert sentence in terminal,(result['scene'],'intended complete message not visible',ident,sentence)
            visible.append(ident)
        result['visible_message_ids']=visible
    if result['scene'].startswith(('prompt-', 'terrain-', 'monster-', 'encounter-', 'shout-', 'speech-', 'item-', 'sol61-')):
        # A traced speculative probe is not proof of a displayed message.
        # Compare bound complete templates with the real terminal, ignoring
        # terminal cursor-based padding and style escapes only.
        terminal=(a.out/result['scene']/'transcript.txt').read_text()
        terminal=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',terminal)
        terminal=re.sub(r'\x1b[()][A-Za-z0-9]','',terminal)
        # DB traces record the fixed template before [[reference]] expansion.
        # Expand only documented internal keys using reviewed raw templates;
        # compare the complete resulting paragraph, never omit child prose.
        def expand_references(text):
            if '[[' not in text: return text
            root=Path(__file__).resolve().parents[1]
            rows={}
            for section in (root/'native/crawl-ref/source/dat/descript/monstatus.txt').read_text().split('%%%%'):
                section='\n'.join(line for line in section.splitlines() if not line.startswith('#')).strip()
                if section:
                    key,body=section.split('\n',1); rows[key]=body.strip()
            translated={m['en']:m['zh'] for path in (root/'localization/migration').glob('luna-*-messages.json')
                        for m in json.loads(path.read_text())['messages']
                        if m.get('source_context') in ('detail.monster.status_text','detail.monster.status_reference')}
            def expand(body,depth=0):
                assert depth<32,'Cyclic DB reference in visible oracle'
                return re.sub(r'\[\[([^]\n]+)\]\]',lambda match:expand(translated[rows[match[1]]],depth+1),body)
            return expand(text)
        normalize=lambda text:re.sub(r'\s+','',re.sub(r'<[^>]+>','',text))
        visible=normalize(terminal)
        checked=[]
        visible_expected=set(expected[result['scene']])
        if result['scene']=='encounter-first-console':
            parents={line.split('\t')[0] for line in result['ids']} & {'hint.encounter.first.console','hint.encounter.first.console_list'}
            assert len(parents)==1, 'First encounter parent was not generated'
            visible_expected.update(parents)
        for identity in sorted(visible_expected):
            rendered=[line.split('\t',2)[2] for line in result['values']
                      if line.startswith(identity+'\t')]
            # Tutorial channel inserts a structural '_' prefix between source
            # paragraphs. Check every complete authored line/paragraph rather
            # than pretending those renderer prefixes are part of the message.
            def complete_visible(text):
                paragraphs=re.split(r'\\n|\n',text)
                paragraphs=[re.sub(r'^(?:SOUND|TALK|VISUAL|PLAIN|SPELL|ENCHANT|WARN):','',p) for p in paragraphs]
                return all(normalize(re.sub(r'\\([rt])',' ',paragraph)) in visible
                           for paragraph in paragraphs if normalize(paragraph))
            assert any(complete_visible(expand_references(t)) for t in rendered),(result['scene'],'bound message not visible',identity)
            checked.append(identity)
        result['visible_message_ids']=checked
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

(a.out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_fixture_unchanged':unchanged,'scenes':len(results)}))
