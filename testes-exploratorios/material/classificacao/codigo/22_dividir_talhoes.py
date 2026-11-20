"""Passo 1: divide os talhões da equipe em grupo de ensino e grupo de medição.
Talhão = geometria única (todos os anos do mesmo talhão vão juntos). Blocos de 0,1 grau (~11 km):
talhões do mesmo bloco ficam no mesmo grupo. Semente fixa. Saída: CSV (IDs, talhao, grupo) sem nomes."""
import glob, json, os, random
from collections import Counter
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENT = os.environ.get("ILPF_AMOSTRAS", os.path.join(RAIZ, "ilpf-amostras"))
g = gpd.read_file(ENT + r"\amostras_ilpf_inspecionadas_4326.gpkg")
SEMENTE, BLOCO, FRAC_MED = 20261112, 0.1, 0.30
ARVORE = {3, 5, 6, 7}

# limpeza
# ATENÇÃO: esta versão reproduz a divisão feita em 12/11/2026, que tratou 2026/2027 como safra
# impossível. Depois se verificou que 2026/2027 é uma safra válida; a divisão publicada não foi
# refeita. Mantido assim para reproduzir o resultado, não como regra recomendada.
g["cod"] = g["tipo_integ"].astype(str).str.strip()
ruins_ano = g["cropYear"].isin(["2026/2027", "2028/2029", "2029/2030"])
ruim_cod = g["cod"].isin(["0", ""])
g["descartado"] = ""
g.loc[ruins_ano, "descartado"] = "safra impossivel"
g.loc[ruim_cod, "descartado"] = "codigo 0"
g["cod"] = pd.to_numeric(g["cod"], errors="coerce")

# talhões por geometria
g["wkb"] = g.geometry.to_wkb()
ids_t = {w: i + 1 for i, w in enumerate(g.drop_duplicates("wkb").sort_values("IDs")["wkb"])}
g["talhao"] = g["wkb"].map(ids_t)
lim = g[g.descartado == ""]
t = lim.groupby("talhao").agg(cod=("cod", lambda s: Counter(s).most_common(1)[0][0]),
                              arvore=("cod", lambda s: bool(set(s) & ARVORE))).reset_index()
geo = g.drop_duplicates("talhao").set_index("talhao").geometry
t["geometry"] = t.talhao.map(geo)
t = gpd.GeoDataFrame(t, crs=4326)
pt = t.geometry.representative_point()
t["bloco"] = [f"{int(p.x // BLOCO)}_{int(p.y // BLOCO)}" for p in pt]

# dentro dos 26 tiles e marcado pelo detector
tiles = json.load(open(os.environ.get("ILPF_TILES", os.path.join(RAIZ, "varredura", "tiles.json"))))["tiles"]
caixas = gpd.GeoSeries([box(b[0][1], b[0][0], b[1][1], b[1][0]) for b in (x["bounds"] for x in tiles)], crs=4326)
t["nos_tiles"] = t.geometry.intersects(caixas.union_all())
cand = pd.concat([gpd.read_file(f) for f in glob.glob(os.environ.get("ILPF_CANDIDATOS", os.path.join(RAIZ, "varredura", "candidatos", "*.geojson")))
                  if "txt_" not in f]).to_crs(4326)
t["detector_marcou"] = t.geometry.intersects(cand.union_all())

# blocos obrigatórios no ensino
obrig = set(t[t.talhao.isin(g[g.IDs.isin([807, 438, 448])].talhao)].bloco)

# sorteio estratificado por bloco: tenta várias ordens e fica com a de proporções mais próximas
def custo(med):
    m = t[t.bloco.isin(med)]
    alvo_classes = t.cod.value_counts(normalize=True)
    c = abs(len(m) / len(t) - FRAC_MED)
    c += abs(m.cod.value_counts(normalize=True).reindex(alvo_classes.index, fill_value=0) - alvo_classes).sum() / 2
    arv_tiles = t[t.arvore & t.nos_tiles]
    c += abs(m.arvore.sum() / max(t.arvore.sum(), 1) - FRAC_MED) + abs((m.arvore & m.nos_tiles).sum() / len(arv_tiles) - 0.5)
    return c

rng = random.Random(SEMENTE)
blocos = sorted(set(t.bloco) - obrig)
melhor = None
for _ in range(5000):
    rng.shuffle(blocos)
    med, n = [], 0
    for b in blocos:
        if n >= FRAC_MED * len(t):
            break
        med.append(b); n += (t.bloco == b).sum()
    c = custo(med)
    if melhor is None or c < melhor[0]:
        melhor = (c, set(med))
t["grupo"] = ["medicao" if b in melhor[1] else "ensino" for b in t.bloco]

g["grupo"] = g.talhao.map(t.set_index("talhao").grupo)
g.loc[g.descartado != "", "grupo"] = "descartado"
saida = g[["IDs", "talhao", "cropYear", "cod", "grupo", "descartado"]].rename(columns={"cod": "tipo_integ"})
saida = saida.merge(t[["talhao", "bloco", "nos_tiles", "detector_marcou"]], on="talhao", how="left")
saida.sort_values("IDs").to_csv(ENT + r"\divisao_ensino_medicao.csv", index=False)
# cópia de trabalho sem nomes, para as outras IAs
t.drop(columns=[]).to_file(os.environ.get("ILPF_GPKG", os.path.join(RAIZ, "classificador", "talhoes_divididos.gpkg")), driver="GPKG")

print("talhoes", len(t), t.grupo.value_counts().to_dict())
print("registros", saida.grupo.value_counts().to_dict())
print(pd.crosstab(t.cod, t.grupo))
a = t[t.arvore & t.nos_tiles]
print("arvore nos tiles", len(a), "| marcados pelo detector", a.detector_marcou.sum())
print(pd.crosstab(a.grupo, a.detector_marcou))
print("obrigatorios", t[t.bloco.isin(obrig)].grupo.unique())
