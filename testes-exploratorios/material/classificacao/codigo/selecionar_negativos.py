"""Seleciona negativos dificeis (urbano/construcao e terraco de curva de nivel)
a partir das leituras de fichas ja rejeitadas, com as regras do PEDIDO:
- so fichas em que a leitura disse que NAO ha renques;
- motivo/cobertura citando area urbana/construcao/galpao OU terraco/curva de nivel;
- descarta qualquer ponto a menos de 5 km de QUALQUER talhao de medicao;
- descarta pontos dentro (ou a menos de 300 m) de talhao positivo de ensino;
- descarta leitura conflitante (mesmo id lido como positivo em outra rodada).
"""
import glob
import json
import os
from collections import defaultdict

import geopandas as gpd
import pandas as pd
import pyproj
import shapely
import shapely.ops
from shapely.geometry import Point

from comum import BASE

ALVOS = os.environ.get("ILPF_ALVOS", os.path.join(os.path.dirname(BASE), "alvos.json"))
LEITURA = os.environ.get("ILPF_LEITURA", os.path.join(os.path.dirname(BASE), "leitura"))

KW_URB = ["urbana", "urban", "cidade", "telhado", "constru", "galp", "sede"]
KW_TER = ["terraco", "terraço", "curva de nivel", "curva de nível",
          "curvas de nível", "curvas de nivel"]
# se a propria ficha ou o cadastro indicam sistema com arvore, nao serve de
# negativo dificil (evita ensinar o modelo a rejeitar plantio de arvores)
KW_ARVORE = ["ilpf", "ilf", "ipf", "saf", "silvicultura", "silv",
             "floresta plantada", "eucalipto", "seringueira", "cafe", "café",
             "lavoura perene", "lavoura permanente", "citros", "laranja",
             "pomar"]


def tem_arvore_cadastro(a, vs):
    txt = " ".join(str(a.get(k, "")) for k in
                   ("classe_sicor", "classe_verdadeira", "semente_classe")).lower()
    if any(k in txt for k in KW_ARVORE):
        return True
    for v in vs:
        txt = " ".join(str(v.get(k, "")) for k in
                       ("classe", "segunda_opcao", "motivo",
                        "cobertura_dominante")).lower()
        if any(k in txt for k in KW_ARVORE):
            return True
    return False


def categoria(v):
    t = ((v.get("motivo") or "") + " " + (v.get("cobertura_dominante") or "")).lower()
    if any(k in t for k in KW_URB):
        return "urbano"
    if any(k in t for k in KW_TER):
        return "terraco"
    return None


def dist_min_m(lon, lat, geoms):
    """Distancia minima (m) do ponto a um conjunto de poligonos, via aeqd local."""
    crs = pyproj.CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m +no_defs")
    tr = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    px, py = tr.transform(lon, lat)
    p = Point(px, py)
    melhor = float("inf")
    for g in geoms:
        if g.is_empty:
            continue
        gg = shapely.ops.transform(tr.transform, g)
        d = p.distance(gg)
        if d < melhor:
            melhor = d
            if melhor <= 0:
                break
    return melhor


def main():
    alvos = json.load(open(ALVOS, encoding="latin-1"))
    by = {x["id"]: x for x in alvos if "id" in x}
    leituras = defaultdict(list)
    for p in glob.glob(os.path.join(LEITURA, "*", "leituras.json")):
        d = json.load(open(p, encoding="utf-8"))
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict):
                    leituras[k].append(v)
    print(f"fichas lidas: {len(leituras)}")

    cand = []
    for fid, vs in leituras.items():
        # conflito entre rodadas -> fora
        if len({v.get("renques_de_arvores") for v in vs}) > 1:
            continue
        if any(v.get("renques_de_arvores") == "sim" for v in vs):
            continue
        cats = [categoria(v) for v in vs]
        cats = [c for c in cats if c]
        if not cats:
            continue
        if fid not in by:
            continue
        if tem_arvore_cadastro(by[fid], vs):
            continue
        a = by[fid]
        cand.append(dict(ficha=fid, categoria=cats[0],
                         lon=float(a["lon"]), lat=float(a["lat"]),
                         motivo=(vs[0].get("motivo") or "")[:200]))
    cand = pd.DataFrame(cand).drop_duplicates("ficha")
    print("candidatos por categoria:", cand.categoria.value_counts().to_dict())

    tal = gpd.read_file(os.path.join(BASE, "talhoes_divididos.gpkg"))
    tal["area_ha"] = tal.to_crs(6933).area / 1e4
    med = tal[tal.grupo == "medicao"]
    pos_ens = tal[(tal.grupo == "ensino") & (tal.arvore)]
    # poligonos num CRS metrico local por candidato; fazemos em blocos por lat/lon
    # usando aeqd centrado no candidato
    med_geoms = list(med.geometry)
    pos_geoms = list(pos_ens.geometry)

    linhas = []
    for i, r in cand.iterrows():
        dmed = dist_min_m(r.lon, r.lat, med_geoms)
        if dmed < 5000.0:
            continue
        dpos = dist_min_m(r.lon, r.lat, pos_geoms)
        if dpos < 300.0:
            continue
        linhas.append(dict(r, dist_medicao_m=round(dmed, 1), dist_pos_ensino_m=round(dpos, 1)))
    out = pd.DataFrame(linhas)
    print("apos filtro de 5 km:", len(out), out.categoria.value_counts().to_dict())
    print("distancias medicao (m):", out.dist_medicao_m.describe().to_dict())
    os.makedirs(os.path.join(BASE, "dados"), exist_ok=True)
    out.to_csv(os.path.join(BASE, "dados", "negativos_selecionados.csv"),
               index=False, encoding="utf-8")
    print("salvo dados/negativos_selecionados.csv")


if __name__ == "__main__":
    main()
