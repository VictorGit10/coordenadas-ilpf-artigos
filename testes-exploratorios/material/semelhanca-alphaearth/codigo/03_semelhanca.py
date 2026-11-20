"""Busca por semelhança: parte de amostras conhecidas (sementes) e procura, nos 26 tiles, os lugares cujo
embedding de satélite (AlphaEarth, 10 m, ano 2024) mais se parece com elas. Acrescenta a alvos.json os grupos
'semelhanca' (os mais parecidos) e 'controle' (pontos sorteados ao acaso, para comparar).
"""
import json, math, os, random, sys, time
from collections import Counter, defaultdict
import ee

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SICOR = os.environ.get("ILPF_SICOR", os.path.join(RAIZ, "..", "ilpf-sicor"))
random.seed(7)
ee.Initialize(project=os.environ.get("EE_PROJETO", "SEU-PROJETO"))
N_SEM = {"IPF": 10, "ILP": 10}
N_CAND = {"IPF": 50, "ILP": 50}
N_CONTROLE = 30
ANOS_OK = ["2023/2024", "2024/2025"]


def dist_km(a, b):
    dx = (a[0] - b[0]) * 111.32 * math.cos(math.radians((a[1] + b[1]) / 2))
    dy = (a[1] - b[1]) * 110.574
    return math.hypot(dx, dy)


alvos = json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8"))
alvos = [a for a in alvos if a["grupo"] in ("conhecida", "sicor")]
usadas = {(a["lon"], a["lat"]) for a in alvos if a["grupo"] == "conhecida"}
am = json.load(open(os.path.join(SICOR, "repo", "assets_amostras_data.json"), encoding="utf-8"))
todos_locais = list({(a["lng"], a["lat"]) for a in am})
loc = defaultdict(list)
for a in am:
    if -52.34 <= a["lng"] <= -46.97 and -18.57 <= a["lat"] <= -12.66:
        loc[(a["lng"], a["lat"])].append(a)
sementes = []
for cl, n in N_SEM.items():
    cands = []
    for k, lst in loc.items():
        rec = [a for a in lst if a["ano"] in ANOS_OK]
        if not rec or k in usadas:
            continue
        ult = max(rec, key=lambda a: ANOS_OK.index(a["ano"]))
        # semente "limpa": a mesma classe em todos os anos recentes
        if ult["classe"] == cl and all(a["classe"] == cl for a in rec):
            cands.append({"lon": k[0], "lat": k[1], "classe": cl, "area": ult["area"]})
    random.shuffle(cands)
    sementes += cands[:n]
print("sementes:", Counter(s["classe"] for s in sementes))

emb = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").filterDate("2024-01-01", "2025-01-01").mosaic()
bandas = emb.bandNames().getInfo()
fc = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([s["lon"], s["lat"]]).buffer(min(100, max(20, math.sqrt(s["area"] * 1e4) / 4))), {"i": i})
    for i, s in enumerate(sementes)])
res = emb.reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()
for f in res["features"]:
    v = [f["properties"].get(b) for b in bandas]
    if any(x is None for x in v):
        continue
    n = math.sqrt(sum(x * x for x in v))
    sementes[f["properties"]["i"]]["vetor"] = [x / n for x in v]
sementes = [s for s in sementes if "vetor" in s]
print("sementes com embedding:", Counter(s["classe"] for s in sementes))

# semelhança entre as próprias sementes (referência do que é "parecido")
def cos(a, b):
    return sum(x * y for x, y in zip(a, b))
ref = {}
for cl in N_SEM:
    vs = [s["vetor"] for s in sementes if s["classe"] == cl]
    outros = [s["vetor"] for s in sementes if s["classe"] != cl]
    dentro = sorted(max(cos(v, w) for j, w in enumerate(vs) if j != i) for i, v in enumerate(vs))
    fora = sorted(max(cos(v, w) for w in outros) for v in vs)
    ref[cl] = {"mesma_classe_mediana": round(dentro[len(dentro) // 2], 3), "outra_classe_mediana": round(fora[len(fora) // 2], 3)}
print("referência (vizinho mais parecido):", ref)

# imagem de semelhança: para cada classe, o máximo do produto interno com as sementes
sims = []
for cl in N_SEM:
    ims = [emb.multiply(ee.Image.constant(s["vetor"])).reduce(ee.Reducer.sum()) for s in sementes if s["classe"] == cl]
    sims.append(ee.ImageCollection(ims).max().rename("sim_" + cl))
sim = ee.Image.cat(sims)

stats = json.load(open(os.path.join(SICOR, "repo", "assets_cnn_spatial_stats.json"), encoding="utf-8"))
pontos = []
for t in stats["tiles"]:
    (s_, w_), (n_, e_) = t["bounds"]
    reg = ee.Geometry.Rectangle([w_, s_, e_, n_], None, False)
    for tent in range(4):
        try:
            r = sim.sample(region=reg, scale=30, numPixels=4000, seed=11, geometries=True, tileScale=4).getInfo()
            break
        except Exception as e:  # noqa
            print("  EE falhou:", str(e)[:100], flush=True)
            time.sleep(20)
    else:
        continue
    for f in r["features"]:
        x, y = f["geometry"]["coordinates"]
        p = {"lon": x, "lat": y, "tile": t["tile"]}
        p.update({k: v for k, v in f["properties"].items()})
        pontos.append(p)
    print(f"  {t['tile']}: {len(r['features'])} pontos", flush=True)
print(len(pontos), "pontos amostrados")
json.dump({"sementes": [{k: v for k, v in s.items() if k != "vetor"} for s in sementes], "referencia": ref,
           "distribuicao": {cl: [round(sorted(p["sim_" + cl] for p in pontos)[int(q * (len(pontos) - 1))], 3) for q in (0.5, 0.9, 0.99, 0.999, 1.0)] for cl in N_SEM}},
          open(os.path.join(RAIZ, "semelhanca_resumo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

escolhidos = []
def longe(p, km_amostra=1.0, km_entre=1.5):
    c = (p["lon"], p["lat"])
    if any(abs(c[0] - l[0]) < 0.02 and abs(c[1] - l[1]) < 0.02 and dist_km(c, l) < km_amostra for l in todos_locais):
        return False
    return all(dist_km(c, (e["lon"], e["lat"])) >= km_entre for e in escolhidos)

for cl, n in N_CAND.items():
    k = 0
    for p in sorted(pontos, key=lambda p: -p["sim_" + cl]):
        if k >= n:
            break
        if longe(p):
            escolhidos.append(dict(p, grupo="semelhanca", semente_classe=cl))
            k += 1
resto = pontos[:]
random.shuffle(resto)
k = 0
for p in resto:
    if k >= N_CONTROLE:
        break
    if longe(p):
        escolhidos.append(dict(p, grupo="controle", semente_classe=""))
        k += 1

def quadrado(lon, lat, lado_m=300):
    dy = lado_m / 2 / 110574.0
    dx = lado_m / 2 / (111320.0 * math.cos(math.radians(lat)))
    return {"type": "Polygon", "coordinates": [[[lon - dx, lat - dy], [lon + dx, lat - dy], [lon + dx, lat + dy], [lon - dx, lat + dy], [lon - dx, lat - dy]]]}

random.shuffle(escolhidos)
base = len(alvos)
for i, p in enumerate(escolhidos, 1):
    alvos.append({"id": f"F{base+i:03d}", "grupo": p["grupo"], "semente_classe": p["semente_classe"], "tile": p["tile"],
                  "sim_IPF": round(p["sim_IPF"], 4), "sim_ILP": round(p["sim_ILP"], 4), "area_ha": 9.0,
                  "lon": p["lon"], "lat": p["lat"], "geom": quadrado(p["lon"], p["lat"]), "contorno": "quadrado de 300 m"})
json.dump(alvos, open(os.path.join(RAIZ, "alvos.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(alvos), "alvos:", Counter(a["grupo"] for a in alvos))
for cl in N_CAND:
    v = sorted(a["sim_" + cl] for a in alvos if a.get("semente_classe") == cl)
    print(cl, "semelhança dos escolhidos: min", v[0], "mediana", v[len(v) // 2], "max", v[-1])
