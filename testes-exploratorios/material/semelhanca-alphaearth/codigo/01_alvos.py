"""Monta a lista de alvos das fichas (alvos.json), com identificadores embaralhados para a leitura às cegas.
Grupos: 'conhecida' (amostra do LAPIG, classe sabida) e 'sicor' (gleba de integração na área piloto).
Os grupos 'semelhanca' e 'controle' são acrescentados depois por 03_semelhanca.py.
"""
import json, math, os, random
from collections import defaultdict, Counter
from shapely.geometry import shape, box, mapping

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SICOR = os.environ.get("ILPF_SICOR", os.path.join(RAIZ, "..", "ilpf-sicor"))
random.seed(20261111)
BBOX = (-52.33827, -18.56234, -46.97821, -12.66328)
ORDEM_ANO = ["2022/2023", "2023/2024", "2024/2025"]
COTA = {"ILP": 14, "IPF": 14, "ILPF": 8, "ILF": 6, "Pastagem": 12, "Agricultura": 10, "Outros": 4}


def quadrado(lon, lat, lado_m):
    dy = lado_m / 2 / 110574.0
    dx = lado_m / 2 / (111320.0 * math.cos(math.radians(lat)))
    return box(lon - dx, lat - dy, lon + dx, lat + dy)


# ---- amostras conhecidas
am = json.load(open(os.path.join(SICOR, "repo", "assets_amostras_data.json"), encoding="utf-8"))
loc = defaultdict(list)
for a in am:
    if BBOX[0] <= a["lng"] <= BBOX[2] and BBOX[1] <= a["lat"] <= BBOX[3]:
        loc[(a["lng"], a["lat"])].append(a)
cand = defaultdict(list)
for (lng, lat), lst in loc.items():
    recentes = [a for a in lst if a["ano"] in ORDEM_ANO]
    if not recentes:
        continue
    ult = max(recentes, key=lambda a: ORDEM_ANO.index(a["ano"]))
    if ult["ano"] == "2022/2023":
        continue  # queremos classe válida em 2023/2024 ou 2024/2025, perto da data da imagem
    classes_3anos = sorted({a["classe"] for a in recentes})
    cand[ult["classe"]].append({"lng": lng, "lat": lat, "classe": ult["classe"], "ano": ult["ano"],
                                "area_ha": ult["area"], "classes_recentes": classes_3anos})
print("locais com classe recente, por classe:", {k: len(v) for k, v in cand.items()})
alvos = []
for cl, n in COTA.items():
    lst = cand.get(cl, [])
    random.shuffle(lst)
    for a in lst[:n]:
        lado = min(1500.0, max(120.0, math.sqrt(max(a["area_ha"], 0.5) * 1e4)))
        g = quadrado(a["lng"], a["lat"], lado)
        alvos.append({"grupo": "conhecida", "classe_verdadeira": cl, "ano_amostra": a["ano"], "classes_recentes": a["classes_recentes"],
                      "area_ha": a["area_ha"], "lon": a["lng"], "lat": a["lat"], "geom": mapping(g), "contorno": "quadrado aproximado"})

# ---- glebas do SICOR na área piloto (sem repetir o mesmo talhão)
fc = json.load(open(os.path.join(SICOR, "saida", "glebas_piloto.geojson"), encoding="utf-8"))
mantidas = []
for f in fc["features"]:
    g = shape(f["geometry"]).buffer(0)
    rep = False
    for g2, _ in mantidas:
        if g.intersects(g2) and g.intersection(g2).area > 0.5 * min(g.area, g2.area):
            rep = True
            break
    if not rep:
        mantidas.append((g, f["properties"]))
for g, p in mantidas:
    c = g.representative_point()
    alvos.append({"grupo": "sicor", "classe_sicor": p["classe"], "safra_sicor": p["safra"], "produto_sicor": p["produto"],
                  "area_ha": p["area_ha"], "lon": c.x, "lat": c.y, "geom": mapping(g), "contorno": "gleba financiada"})

random.shuffle(alvos)
for i, a in enumerate(alvos, 1):
    a["id"] = f"F{i:03d}"
json.dump(alvos, open(os.path.join(RAIZ, "alvos.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(alvos), "alvos:", Counter(a["grupo"] for a in alvos))
print("conhecidas por classe:", Counter(a["classe_verdadeira"] for a in alvos if a["grupo"] == "conhecida"))
print("sicor por classe:", Counter(a["classe_sicor"] for a in alvos if a["grupo"] == "sicor"))
