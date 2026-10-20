# 사양 글 검사(13:33·13:35·8.2): 광장·받침·기초 절개가 '있는 것처럼' 쓴 문장이 남았는지 센다. 0건이면 종료 코드 0
# 제거 기록 문장(같은 문장 안에 0·없·철회·폐기·짓지 않·금지·빼·지운·대신 등)과 철회·폐기 목록 열쇠 아래는 센다에서 뺀다
import json, re, sys
PATS = ['조경 광장', '광장 판석', '광장 포장', '판석 광장', '광장 문', '광장 가장자리', '첫 집 줄', '기초 절개', '받침 앞', '콜로세움 받침', '예약 원', '건물 ∪ 광장', 'hero_plaza']
ALLOW_KEYS = ('withdrawn', 'invalidated_from_previous', 'not_built', 'removed', 'plaza_d5_withdrawn', 'forbidden', 'print_rules', 'legacy', 'composition_1249', 'd4_')
MARK = re.compile(r"(\b0\b|0이다|0\(|0mm|0개|0회|없|철회|폐기|짓지 않|금지|빼|지운|지웠|대신|않는다)")
s = json.load(open(sys.argv[1], encoding='utf-8'))
hits = []
def sentences(t):
    return re.split(r"(?<=[.。])\s+|(?<=다)\.\s*|\s·\s|; ", t)
def walk(o, path):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + '[%d]' % i)
    elif isinstance(o, str):
        if any(a in path for a in ALLOW_KEYS):
            return
        for sen in sentences(o):
            for p in PATS:
                if p in sen and not MARK.search(sen):
                    hits.append((p, path, sen[:150]))
walk(s, '')
for h in hits:
    print(h[0], '|', h[1], '|', h[2])
print('hits', len(hits))
sys.exit(1 if hits else 0)
