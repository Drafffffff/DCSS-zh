#!/usr/bin/env python3
"""Exercise real target failure producers with world/name queries as seams."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog

def block(s,needle):
    p=s.index(needle);begin=s.rfind('\n',0,p)+1;brace=s.index('{',p);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[begin:end+1]
    raise AssertionError(needle)

def main():
    compile_catalog()
    source=(SRC/'target.cc').read_text()
    directn=(SRC/'directn.cc').read_text()
    consumer=block(directn,'void direction_chooser::print_target_description(')
    assert 'mpr(hitfunc->failure_message(), MSGCH_EXAMINE_FILTER)' in consumer
    assert 'why_not.c_str()' not in consumer
    assert not re.search(r'notify_fail\(\s*"[^"\n]+"',source), 'fixed reasons still reach legacy string path'
    fixture=json.loads((Path(__file__).parent/'fixtures/target-notifications-english.json').read_text())
    # Inspect the generated IDs actually bound by the real notify_fail calls.
    fixed=[]
    for ident in re.findall(r'notify_fail\(zh_message_arg\("reason", "([^"]+)"\)\)',source):
        fixed.append(ident)
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <iostream>
#include <string>
using namespace std;
enum {DESC_THE, PRONOUN_REFLEXIVE};
#define ASSERT(x) assert(x)
struct coord_def {int n=0;bool origin()const{return n==0;}};
struct actor {int type=1;bool stationary=false;string reflexive="itself";string pronoun(int)const{return reflexive;}bool is_stationary()const{return stationary;}};
struct monster:actor {string english="the orc",localized="甲";bool supported=true;};
struct monster_info {string english="the orc",localized="甲";bool supported=true;};
monster live;monster_info info;bool present=true,visible=true,explodes=false,harm=true,immune=true;
struct player {bool can_see(const actor&)const{return visible;}}you;
actor*actor_at(coord_def){return present?&live:nullptr;}
bool mons_is_hepliaklqana_ancestor(int n){return n==1;}
bool mons_is_tentacle_or_tentacle_segment(int n){return n==2;}
monster* monster_at(coord_def){return present?&live:nullptr;}
bool _unravelling_explodes_at(coord_def){return explodes;}
bool could_harm(const player*,const monster*){return harm;}
ZhArg zh_monster_arg(const string&key,const monster&mon){return {key,ZhArgType::Name,mon.english,mon.supported?mon.localized:mon.english,mon.supported};}
ZhArg zh_monster_info_arg(const string&key,const monster_info&mon){return {key,ZhArgType::Name,mon.english,mon.supported?mon.localized:mon.english,mon.supported};}
struct knowledge {const monster_info*monsterinfo()const{return present?&info:nullptr;}};
int terrain=1;
bool map_bounds(coord_def){return true;}
const char*feat_type_name(int n){return n==1?"rock wall":n==2?"stone wall":"unknown wall";}
string article_a(const char*s){return string("a ")+s;}
struct world {int grid(coord_def)const{return terrain;}knowledge map_knowledge(coord_def)const{return {};}}env;
struct targeter {
 string why_not;ZhArg display_failure;const actor*agent=nullptr;
 bool notify_fail(const ZhArg&);bool notify_fail(const string&);ZhMessage failure_message()const;
};
struct targeter_smite:targeter {bool base_valid=true;bool valid_aim(coord_def){return base_valid;}};
struct targeter_charge:targeter {bool valid_aim(coord_def);};
struct targeter_transference:targeter_smite {bool valid_aim(coord_def);};
struct targeter_unravelling:targeter_smite {bool valid_aim(coord_def);};
struct targeter_poisonous_vapours:targeter_smite {
 bool valid_aim(coord_def);bool affects_monster(const monster_info&)const{return !immune;}
};
bool land=true;ZhArg charge_reason;
coord_def get_electric_charge_landing_spot(const actor&,coord_def,string*canonical,ZhArg*reason){
 *canonical=charge_reason.canonical;*reason=charge_reason;coord_def c;c.n=land;return c;
}
'''
    for name in ['bool targeter::notify_fail(const ZhArg','bool targeter::notify_fail(const string','ZhMessage targeter::failure_message(','bool targeter_charge::valid_aim(','bool targeter_unravelling::valid_aim(','bool targeter_poisonous_vapours::valid_aim(','bool targeter_transference::valid_aim(','static ZhArg _wallmsg(']:
        code+=block(source,name)+'\n'
    code+='const char *fixed_ids[] = {'+','.join(json.dumps(x) for x in sorted(set(fixed)))+'};\n'
    code+='const char *fixed_english[] = {'+','.join(json.dumps(x) for x in fixture['fixed'])+'};\n'
    code+=r'''
int cases=0;
void check(targeter&t,const string&expected,bool supported){
 auto m=t.failure_message();assert(t.why_not==expected&&m.canonical==expected);
 assert((supported?m.localized!=expected:m.localized==expected));assert(m.display()==m.localized);++cases;
}
int main(int argc,char **argv){
 setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.target.notifications");
 targeter t;
 for(const char*en:fixed_english){bool found=false;for(const char*id:fixed_ids){
  auto r=zh_message_arg("reason",id);if(r.canonical==en){t.notify_fail(r);check(t,en,true);found=true;break;}}
  assert(found);
 }
 actor who;targeter_charge c;c.agent=&who;
 for(bool ok:{false,true})for(bool known:{false,true}){
  land=ok;charge_reason={"reason",ZhArgType::Text,"Charge blocked by terrain.",known?"乙":"Charge blocked by terrain.",known};
  assert(c.valid_aim({})==ok);if(!ok)check(c,charge_reason.canonical,known);
 }
 for(string name:{"the orc","Sigmund","the Wizard's ghost","the two-headed ogre","something","the +7 spectral blade"})
 for(bool known:{false,true})for(bool seen:{false,true})for(bool has:{false,true}){
  live.english=name;live.supported=known;info.english=name;info.supported=known;visible=seen;present=has;
  targeter_unravelling u;explodes=false;harm=true;
  bool expected=!(seen&&has);assert(u.valid_aim({})==expected);
  if(!expected)check(u,name+" has no magical effects to unravel.",known);
  explodes=true;harm=false;assert(u.valid_aim({})==expected);
  if(!expected)check(u,"You cannot do harm to "+name,known);
  targeter_poisonous_vapours p;immune=true;assert(p.valid_aim({})==!has);
  if(has)check(p,name+" cannot be affected by poisonous vapours.",known);
  immune=false;assert(p.valid_aim({}));
 }
 for(int feat:{1,2,99}){terrain=feat;t.notify_fail(_wallmsg({}));check(t,string("There is a ")+feat_type_name(feat)+" there.",feat!=99);}
 present=true;visible=true;live.type=1;
 for(string pronoun:{"itself","himself","herself","themselves"}){
  live.reflexive=pronoun;targeter_transference tr;assert(!tr.valid_aim({}));
  check(tr,"You can't transfer your ancestor with "+pronoun+".",true);
 }
 // An unsupported external child must replace prior localized state completely.
 t.notify_fail(zh_message_arg("reason","target.reason.out_of_range"));check(t,"Out of range.",true);
 assert(argc==2);setenv("DCSS_ZH_ID_MISSING",argv[1],1);
 t.notify_fail(string("A future external reason."));
 // Merely probing a candidate must not create a missing-translation report.
 assert(!ifstream(argv[1]).good());
 check(t,"A future external reason.",false);
 auto report=[&](){ifstream in(argv[1]);return string(istreambuf_iterator<char>(in),istreambuf_iterator<char>());};
 string expected_report="target.reason.external_unmigrated\tunsupported external producer\tA future external reason.\n";
 assert(report()==expected_report);++cases;
 t.notify_fail(string());assert(t.failure_message().canonical.empty()&&t.failure_message().localized.empty());++cases;
 assert(report()==expected_report);++cases;
 cout<<"PASS: "<<cases<<" real target notification producer cases, canonical names, branches and whole-message fallback\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'test.cc';path.write_text(code);exe=Path(tmp)/'test'
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(path),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),'-o',str(exe)],check=True)
        subprocess.run([str(exe),str(Path(tmp)/"missing.tsv")],check=True,timeout=30)
if __name__=='__main__':main()
