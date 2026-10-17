#!/usr/bin/env python3
"""Exercise real typed delivery wrappers against the existing _mpr contract."""
import subprocess,tempfile
from pathlib import Path
from test_target_notifications import block
root=Path(__file__).resolve().parents[1]
source=(root/'native/crawl-ref/source/message.cc').read_text()
code=r'''
#include <cassert>
#include <string>
using namespace std;
using msg_channel_type=int;
struct ZhMessage {string canonical,localized;};
struct Delivery {string canonical,localized;int channel,param;bool nojoin,cap;} last;
void _mpr(string s,int ch=0,int param=0,bool nojoin=false,bool cap=true,const string&zh="") {last={s,zh,ch,param,nojoin,cap};}
'''
for signature in ('void mpr(const ZhMessage &','void mpr_nojoin(msg_channel_type channel, const ZhMessage &','void mpr_nocap(const ZhMessage &','void mpr_nojoin(msg_channel_type channel, string text)'):
 code+=block(source,signature)+'\n'
code+=r'''
int main(){
 for(const string&en:{string("a scroll labelled ABC"),string(1024,'x'),string("<red>lowercase +5</red>")})
 for(const string&zh:{string(""),string("<red>placeholder UTF-8 参数</red>")})
 for(int channel:{0,3,9})for(int param:{0,7,99}){
  ZhMessage m{en,zh};
  mpr(m,channel,param);assert(last.canonical==en&&last.localized==zh&&last.channel==channel&&last.param==param&&!last.nojoin&&last.cap);
  mpr_nocap(m,channel,param);assert(last.canonical==en&&last.localized==zh&&last.channel==channel&&last.param==param&&!last.nojoin&&!last.cap);
  mpr_nojoin(channel,m);auto typed=last;
  mpr_nojoin(channel,en);assert(last.canonical==typed.canonical&&last.channel==typed.channel&&last.param==typed.param&&last.nojoin==typed.nojoin&&last.cap==typed.cap&&typed.localized==zh);
 }
}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11',str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS: 162 real typed delivery calls preserve canonical, presentation, cap, nojoin, channel and parameter')
