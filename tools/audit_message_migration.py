#!/usr/bin/env python3
"""Report real source bindings and remaining legacy producers; no CJK ratios."""
import json,re
from pathlib import Path
from compile_message_ids import ROOT,SRC,LOC,compile_catalog
from migrate_message_sources import calls
messages=compile_catalog();bindings={};remaining={};missing=[]
for path in sorted(SRC.glob('*.cc')):
 text=path.read_text()
 for identity in re.findall(r'\bzh_message\(\s*"([a-z0-9_.]+)"',text):
  bindings.setdefault(identity,[]).append(path.name)
  if identity not in messages:missing.append((path.name,identity))
 count=sum(1 for a,b,fn,args in calls(text) if not any('zh_message(' in arg for arg in args))
 if count:remaining[path.name]=count
assert not missing,missing
source_bindings={}
guarded_producers={}
raw_boundaries={}
legacy={}
for path in SRC.glob('*.cc'):
 text=path.read_text()
 for context in re.findall(r'\bzh_source\(\s*"([^"]+)"',text):
  source_bindings.setdefault(context,[]).append(path.name)
 guards=re.findall(r'ZhLegacyGuard\s+\w+\(\s*"([^"]+)"',text)
 if guards:guarded_producers[path.name]=sorted(set(guards))
 raw=len(re.findall(r'\b(?:parse_string_raw|parse_string_to_multiple_raw|set_text_pretranslated|set_title_pretranslated|set_more_pretranslated)\(',text))
 if raw:raw_boundaries[path.name]=raw
 count=len(re.findall(r'\bzh_translate\(',text))
 if count:legacy[path.name]=count
report={'defined_ids':len(messages),'direct_literal_bound_ids':len(bindings),'bindings':bindings,
 'remaining_legacy_mpr_calls_by_file':remaining,'remaining_legacy_render_hooks':legacy,
 'background_assertion_exclusions':{'output.cc':['draw_border','print_stats','redraw_screen'],'directn.cc':['UIDirectionChooserView::_render']},
 'source_literal_context_bindings':source_bindings,'guarded_producers':guarded_producers,'raw_display_boundaries':raw_boundaries,
 'scope_note':'Dynamic ID expressions and semantic word domains are additional bindings; no percentage claimed. Existing saved English history has no IDs.','general_word_fallback_removed': 'translate_terms(' not in (SRC/'zh-localization.cc').read_text()}
assert report['general_word_fallback_removed']
out=ROOT/'verification/native/message-migration';out.mkdir(parents=True,exist_ok=True);(out/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ('defined_ids','direct_literal_bound_ids','general_word_fallback_removed')}))
