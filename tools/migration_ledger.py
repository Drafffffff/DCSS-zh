#!/usr/bin/env python3
"""Inventory translation boundaries without treating candidates/counts as coverage.
This scans lexical calls, not a C++ AST. The reviewed module ledger determines
scope; each call retains its exact source anchor for verification.
"""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'native/crawl-ref/source'
OUT=ROOT/'analysis/message-migration'
APIS={'zh_message','zh_source','zh_translate','zh_word','zh_word_arg',
      'zh_glossary_name','zh_place_arg','zh_monster_type_arg','origin_display_desc','zh_item_arg','zh_monster_arg','zh_monster_info_arg',
      'mpr','mprf','cprintf','CPRINTF','make_stringf','vmake_stringf','getLongDescription','getQuoteString',
      'parse_string','parse_string_raw','parse_string_to_multiple',
      'parse_string_to_multiple_raw','set_title','set_title_pretranslated',
      'set_more','set_more_pretranslated','add_text','set_text',
      'set_text_pretranslated','ZhTranslationPause','ZhLegacyPause',
      'ZhLegacyGuard','ZhLegacyBackground'}
TOKENS=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\bZh(?:TranslationPause|LegacyPause|LegacyGuard|LegacyBackground)\s+\w+\s*\(|\b[A-Za-z_]\w*\s*\(',re.S)
RULES=[('protocol',{'zh-message','zh-localization','database'}),
 ('rendering',{'format','menu','precision-menu','scroller','ui','cio','libgui','libunix','tilesdl'}),
 ('names',{'zh-display-name','item-name','mon-info','mon-util'}),
 ('details',{'describe','describe-spells'}),('skills',{'skill-menu','skills','lookup-help','tilereg-skl'}),
 ('shop',{'shopping'}),('hud',{'output','tilereg-tab','tilereg-grid','tilereg-msg','tilereg-doll'}),
 ('combat',{'attack','melee-attack','ranged-attack','fight','mon-attack','player-hurt'}),
 ('equipment-items',{'delay','player-equip','item-use','item-prop','invent','item-name','items'}),
 ('targeting',{'target','directn','quiver'}),
 ('religion',{'religion','god-abil','god-passive','god-wrath','god-pr','decks'}),
 ('character',{'player','mutation','ability','status','species','jobs','transform'}),
 ('world',{'terrain','travel','traps','stairs','feature','dungeon','map','view','viewchar'}),
 ('help',{'command','hints','tutorial'})]
def module(path):
 for name,stems in RULES:
  if path.stem in stems:return name
 if path.stem.startswith(('spl-','spell-')):return 'spells'
 if path.stem.startswith('mon-'):return 'monsters'
 if path.stem.startswith('tilereg-'):return 'rendering'
 return 'other-review-required'
def scan(path):
 text=path.read_text();rows=[]
 for match in TOKENS.finditer(text):
  token=match.group()
  if token.startswith(('//','/*','"',"'")):continue
  api=token.split('(')[0].strip().split()[0]
  if api not in APIS:continue
  # Anchor is a single source line, not an invented stable message ID.
  line=text.count('\n',0,match.start())+1
  start=text.rfind('\n',0,match.start())+1
  end=text.find('\n',match.end());end=len(text) if end<0 else end
  anchor=text[start:end].strip()
  rows.append({'file':path.name,'line':line,'api':api,'anchor':anchor,
   'module':module(path),'classification':
    'legacy-hook' if api=='zh_translate' else
    'canonical-read-scope' if api=='ZhTranslationPause' else
    'raw-render-scope' if api=='ZhLegacyPause' else
    'typed-producer' if api in ('zh_message','zh_source') else
    'semantic-name' if api in ('zh_item_arg','zh_monster_arg','zh_monster_info_arg','zh_glossary_name','zh_word','zh_word_arg') else
    'boundary-assertion' if api in ('ZhLegacyGuard','ZhLegacyBackground') else
    'callsite-review-required'})
 return rows

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 manifest=json.loads((OUT/'modules.json').read_text())
 rows=[row for path in sorted(SRC.glob('*.cc')) for row in scan(path)]
 report={'schema':1,'method':'lexical callsite inventory; not a translation coverage metric',
  'native_head':json.loads((ROOT/'localization/upstream.json').read_text())['localized_commit'],
  'files':{str(p.relative_to(SRC)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*.cc')) if any(r['file']==p.name for r in rows)},
  'modules':manifest['modules'],'callsites':rows}
 encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
 destination=OUT/'callsites.json'
 if args.check:
  assert destination.read_text()==encoded,'Migration ledger is stale; regenerate after source changes'
 else:destination.write_text(encoded)
 lines=['# 迁移账本','', '本文由 modules.json 与真实源码调用清单生成。调用点是审查候选，不等于玩家可见文案或翻译完成率。','',
 '| 模块 | 当前边界 | 下一步 / 验收 |','|---|---|---|']
 for entry in manifest['modules']:
  lines.append('| '+entry['name']+' | '+entry['state']+' | '+entry['acceptance']+' |')
 if manifest.get('workflow'):
  flow=manifest['workflow']
  lines+=['','## 按项目结构推进的路线','',flow['unit']+'。',flow['completion']+'。',flow['evidence']+'。','']
  for n,item in enumerate(flow['order'],1):lines.append(f'{n}. {item}')
 if manifest.get('work_packages'):
  lines+=['','## 可验收工作包','']
  for package in manifest['work_packages']:
   assert package['state'] in ('queued','in-progress','verified'),package['id']
   for name in package['sources']:assert (SRC/name).is_file(),(package['id'],name)
   if package['state']=='verified':
    assert package.get('report') and (ROOT/package['report']).is_file(),package['id']
    for test in package['tests']:assert (ROOT/test).is_file(),(package['id'],test)
    text='\n'.join((SRC/name).read_text() for name in package['sources'])
    for producer in package['producers']:assert producer in text,(package['id'],producer)
   lines += [f"### {package['id']} — {package['state']}",'',
    '所属模块：'+package['module']+'。',
    '文件：'+ '、'.join('`'+name+'`' for name in package['sources'])+'。',
    '生产函数：'+'、'.join('`'+name+'`' for name in package['producers'])+'。',
    '显示/业务消费者：'+'、'.join('`'+name+'`' for name in package['consumers'])+'。',
    '验证：'+'、'.join('`'+name+'`' for name in package['tests'])+'。']
   if package.get('canonical_compatibility'):lines.append('兼容规则：'+package['canonical_compatibility']+'。')
   if package.get('report'):lines.append('验收记录：['+package['report']+'](../../'+package['report']+')。')
   lines+=['剩余：'+'；'.join(package['remaining'])+'。','']
 lines+=['','## 公共旧入口','']
 for row in rows:
  if row['classification']=='legacy-hook':lines.append(f"- `{row['file']}:{row['line']}` — `{row['anchor']}`")
 lines+=['','## 边界声明','',
 '规范英文读取使用 ZhTranslationPause；只阻止旧匹配的原样渲染使用 ZhLegacyPause。两种职责不可互换。',
 '模块完成需覆盖主入口、选择、详情、帮助、悬停、成功/失败反馈及渲染出口；同文件有新接口不代表整个文件完成。',
 '旧存档没有消息 ID 的历史兼容单列，不能据此保留新实时消息的旧匹配。',
 '所有新增/修改游戏译文由 Luna 批量审校，主 agent 负责代码。Mac 为主调试平台；Linux 在里程碑验收。','']
 summary='\n'.join(lines)
 if args.check:assert (OUT/'LEDGER.md').read_text()==summary,'Module ledger is stale'
 else:(OUT/'LEDGER.md').write_text(summary)
 print(json.dumps({'callsites_for_review':len(rows),'legacy_hooks':sum(r['classification']=='legacy-hook' for r in rows),'module_groups':len(manifest['modules'])}))
if __name__=='__main__':main()
