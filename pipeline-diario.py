# -*- coding: utf-8 -*-
import json, re, sys, os, urllib.request, unicodedata, difflib
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# Fecha actual (Madrid) o la pasada por argumento
MADRID_TZ = timezone(timedelta(hours=1))
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.now(MADRID_TZ).strftime('%Y-%m-%d')
DDMM = FECHA[8:10] + '-' + FECHA[5:7]

print(f"Iniciando Pipeline para fecha: {FECHA}")

# Utilidades de nombres
STRIP = {"fc","cf","afc","sc","ac","as","cd","ca","club","clube","bk","sk","if","ff","fk","kv","krc","kvc","rsc","sv","ssv","vfb","vfl","tsg","bv","hnk","gnk","nk","uc","us","cfp","spa","calcio","spor","futbol","kulubu","deportivo","real","royal","sd","ud","ogc","rc","csc","cfr","cs","csm","sl","ks","asa","1899","1904","1893","1907","2018","1929","2004","1599","07","09","98","b","sp","rfc","bc"}
ALIAS = {"munich":"munchen","moskva":"moscow","az":"alkmaar","nec":"nijmegen","wolves":"wolverhampton","spurs":"tottenham"}

def norm(s):
    if not s: return set()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    out = set()
    for t in s.split():
        t = ALIAS.get(t, t)
        if t in STRIP: continue
        if t.isdigit() and len(t) <= 4: continue
        out.add(t)
    return out

def names_match(a, b):
    if not a or not b: return False
    if a == b: return True
    if a <= b or b <= a: return True
    def subset(x, y):
        for t in x:
            if t in y: continue
            if len(t) == 1 and any(u.startswith(t) for u in y): continue
            return False
        return True
    return subset(a, b) or subset(b, a)

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'})
    return urllib.request.urlopen(req, timeout=30).read()

# 1. Cargar datos de ValueStats
EXT = f'archivo-valuestats/{FECHA}/valuestats-extract.json'
if os.path.exists(EXT):
    d = json.load(open(EXT))
else:
    print(f"Aviso: {EXT} no existe, usando estructura vacía para refresco de cuotas.")
    d = {'players': [], 'teams': {}}

# 2. Descargar fixtures de ValueOdds
try:
    vf_data = json.loads(get(f'https://valueodds.net/api/v1/fixtures?date={FECHA}'))['data']
    print('Fixtures ValueOdds cargados:', len(vf_data))
except Exception as e:
    print('Error leyendo ValueOdds fixtures:', e)
    vf_data = []

fx_by_team = defaultdict(list)
for f in vf_data:
    for side in ('home_team', 'away_team'):
        fx_by_team[f[side]['name']].append(f)

def find_fx_names(equipo):
    if equipo in fx_by_team and len(fx_by_team[equipo]) == 1:
        f = fx_by_team[equipo][0]
        return [f['home_team']['name'], f['away_team']['name']]
    key = norm(equipo)
    hits = []
    for f in vf_data:
        for side in ('home_team', 'away_team'):
            if key and key <= norm(f[side]['name']):
                hits.append(f)
    if len(hits) == 1:
        return [hits[0]['home_team']['name'], hits[0]['away_team']['name']]
    return None

# 3. Procesar candidatos
jug = []
for c in d.get('players', []):
    fxn = find_fx_names(c.get('equipo', ''))
    if not fxn: continue
    jug.append({
        'comp': c.get('comp'), 'hora': c.get('hora'), 'nombre': c.get('nombre'), 'equipo': c.get('equipo'),
        'fixture': fxn, 'mercado': c.get('mercado'), 'l20pct': c.get('l20pct'), 'l20ab': c.get('l20ab'),
        'cond': c.get('cond', ''), 'condAb': c.get('condAb', ''),
        'condPct': c.get('condPct', '')
    })

# 4. Cuotas Winamax (PRELOADED_STATE)
wam_priced = {}
try:
    html = get('https://www.winamax.es/apuestas-deportivas/sports/1').decode('utf-8', 'ignore')
    i = html.find('var PRELOADED_STATE = ')
    if i != -1:
        wst, _ = json.JSONDecoder().raw_decode(html[i + len('var PRELOADED_STATE = '):].strip())
        print("Winamax conectado con éxito.")
except Exception as e:
    print('Winamax bypass omitido temporalmente:', e)

# 5. Guardar en radar-data.json
out_file = 'radar-data.json'
try:
    data = json.load(open(out_file)) if os.path.exists(out_file) else {'days': []}
except Exception:
    data = {'days': []}

day = next((x for x in data.get('days', []) if x.get('fecha') == FECHA), None)
if day is None:
    day = {'fecha': FECHA, 'candidatos': []}
    data.setdefault('days', []).append(day)
    data['days'] = data['days'][-3:] # Mantener últimos 3 días

data['updated_at'] = datetime.now(MADRID_TZ).isoformat(timespec='seconds')
json.dump(data, open(out_file, 'w'), ensure_ascii=False, indent=2)
print("radar-data.json actualizado correctamente.")
