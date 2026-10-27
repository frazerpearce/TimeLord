"""Offline standard-library search. Writes a candidate config; never changes a delivery.

Usage: python3 optimize.py --output /tmp/compact-candidate.json
The selected config is checked in; normal builds do not repeat this search.
"""
import argparse,copy,lzma,json,random,re,time
from pathlib import Path
import compact
ROOT=Path(__file__).resolve().parent

def stream(source,config):
    compact.CONFIG=config
    document=('<body><script>'+compact.minify(source)+'</script>').encode()
    return document,lzma.compress(document,format=lzma.FORMAT_RAW,filters=config['lzma_filters'])

def search(source,original):
    begin=time.time();rng=random.Random(712);best=copy.deepcopy(original)
    best_size=len(stream(source,best)[1]);trials=0
    shader=source[source.index('precision highp float;'):source.index('}`.replace')]
    used=set(re.findall(r'\b[A-Za-z_]\w*\b',shader))
    glsl=[x for x in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' if x not in used]
    js=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    # Randomized identifier allocation, then deterministic local improvements.
    for i in range(12000):
        candidate=copy.deepcopy(best);rng.shuffle(glsl);rng.shuffle(js)
        candidate['glsl_identifiers']=dict(zip(original['glsl_identifiers'],glsl))
        candidate['js_identifiers']=dict(zip(original['js_identifiers'],js))
        n=len(stream(source,candidate)[1]);trials+=1
        if n<best_size:best,best_size=candidate,n
    for group,aliases in [('glsl_identifiers',glsl),('js_identifiers',js)]:
        for _ in range(4):
            improved=False
            for name in best[group]:
                for alias in aliases:
                    candidate=copy.deepcopy(best);mapping=candidate[group];previous=mapping[name]
                    other=next((k for k,v in mapping.items() if v==alias),None)
                    mapping[name]=alias
                    if other:mapping[other]=previous
                    n=len(stream(source,candidate)[1]);trials+=1
                    if n<best_size:best,best_size=candidate,n;improved=True
            if not improved:break
    document,_=stream(source,best)
    for lc in range(5):
        for lp in range(3):
            if lc+lp>4:continue
            for pb in range(5):
                for mf in [lzma.MF_HC3,lzma.MF_HC4,lzma.MF_BT2,lzma.MF_BT3,lzma.MF_BT4]:
                    for nice in [8,16,32,64,128,273]:
                        for depth in [0,16,64,256]:
                            f={**best['lzma_filters'][0],'lc':lc,'lp':lp,'pb':pb,'mf':mf,'nice_len':nice,'depth':depth}
                            n=len(lzma.compress(document,format=lzma.FORMAT_RAW,filters=[f]));trials+=1
                            if n<best_size:best['lzma_filters']=[f];best_size=n
    print(json.dumps(dict(best_stream_bytes=best_size,candidates=trials,elapsed_seconds=round(time.time()-begin,3)),indent=2))
    return best

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    config=search((ROOT/'src/planet.js').read_text(),compact.CONFIG)
    # Encoding-only options stay together; decoder needs id/dict_size/lc/lp/pb only.
    config.pop('lzma_filter',None)
    args.output.write_text(json.dumps(config,indent=2)+'\n')
