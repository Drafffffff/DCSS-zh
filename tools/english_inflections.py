"""English name inflections, mirroring stable 0.34 english.cc:pluralise.

Chinese noun translations are invariant here. The catalog's original Pi
translations supply all wording; these aliases only recognise engine output.
"""
def pluralise(name, monster=False):
    for q in (' of ',' labelled ',' from '):
        if q in name and not (monster and name.endswith(('zombie','draugr','simulacrum'))):
            a,b=name.split(q,1);return pluralise(a)+q+b
    for close,opening in ((')',' ('),(']',' [')):
        if name.endswith(close) and opening in name:
            i=name.rfind(opening);return pluralise(name[:i])+name[i:]
    s=name.lower()
    if s.endswith('us'):return name+'es' if s.endswith(('lotus','status')) else name[:-2]+'i'
    if s.endswith(('larva','antenna','hypha','noma','amoeba')):return name+'e'
    if s.endswith('ex'):return name[:-2]+'ices'
    if s.endswith(('mosquito','ss')):return name+'es'
    if s.endswith('cyclops'):return name[:-1]+'es'
    if s=='catoblepas':return 'catoblepae'
    if s=='stratum':return 'strata'
    if s.endswith('s'):return name
    if s.endswith('y'):return name+'s' if len(s)==1 or s[-2] in 'aeiou' else name[:-1]+'ies'
    if s.endswith(('fe','staff')):return name[:-2]+'ves'
    if s.endswith('f') and not s.endswith('ff'):return name[:-1]+'ves'
    if s.endswith('mage') and not s.endswith('damage'):return name[:-1]+'i'
    if s in ('gold','oni') or s.endswith(('fish','folk','spawn','tengu','sheep','swine','efreet','jiangshi','raiju','meliai','kemwar')):return name
    if s.endswith(('ch','sh','x','chon')):return name+'es'
    if s.endswith(('simulacrum','plasmodium','eidolon')):return name[:-2]+'a'
    if s.endswith('djinni'):return name[:-1]
    if s=='foot':return 'feet'
    if s in ('ophan','cherub','seraph'):return name+'im'
    if s.endswith('arachi'):return name+'m'
    if s=='ushabti':return name+'u'
    if "'s ghost" in s:return 'ghosts called '+name[:s.index("'s ghost")]
    return name+'s'
