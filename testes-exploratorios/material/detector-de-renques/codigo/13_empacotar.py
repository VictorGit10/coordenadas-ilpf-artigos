"""Empacota as amostras com renques confirmadas: junta alvos (grupo 'listras'), primeira leitura e segunda leitura
rigorosa do Gemini, e grava GeoPackage, GeoJSON, CSV e as fichas na pasta de entrega."""
import csv, glob, json, os, shutil, sys
from collections import Counter
import geopandas as gpd
from shapely.geometry import shape

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "entrega")
os.makedirs(os.path.join(DEST, "fichas"), exist_ok=True)
alvos = {a["id"]: a for a in json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8")) if a["grupo"] == "listras"}
meta = json.load(open(os.path.join(RAIZ, "fichas_meta.json"), encoding="utf-8"))
prim, rigor = {}, {}
for arq in glob.glob(os.path.join(RAIZ, "leitura", "rodada5_listras", "leituras.json")) + [f for f in glob.glob(os.path.join(RAIZ, "leitura", "rodada6_*", "leituras.json")) if "rigor" not in f]:
    prim.update(json.load(open(arq, encoding="utf-8")))
for arq in glob.glob(os.path.join(RAIZ, "leitura", "rodada*rigor*", "leituras.json")):
    rigor.update(json.load(open(arq, encoding="utf-8")))


def classe(p, r):
    entre = (r or {}).get("entre_as_fileiras") or p.get("entre_os_renques") or ""
    lav = (r or {}).get("serie_tem_lavoura") == "sim" or p.get("serie_ciclos_de_lavoura") not in (None, "", "nenhum")
    if entre == "os dois" or (entre == "pasto" and lav):
        return "ILPF"
    if entre == "lavoura":
        return "ILF"
    if entre == "pasto":
        return "IPF"
    return p.get("classe") if p.get("classe") in ("IPF", "ILF", "ILPF") else "IPF"


linhas, geoms = [], []
cont = Counter()
for fid, a in alvos.items():
    p = prim.get(fid)
    if not p:
        cont["sem leitura"] += 1
        continue
    if p.get("renques_de_arvores") != "sim":
        cont["sem renque na 1a leitura"] += 1
        continue
    r = rigor.get(fid)
    nota = (r or {}).get("nota") or "sem 2a leitura"
    cont["nota " + nota] += 1
    if nota == "C":
        continue
    linhas.append({
        "id": fid, "tile": a.get("tile"), "classe_sugerida": classe(p, r), "nota": nota, "classe_1a_leitura": p.get("classe"),
        "confianca_1a_leitura": p.get("confianca"), "fileiras_contadas": (r or {}).get("fileiras_contadas"),
        "espacamento_m_gemini": (r or {}).get("espacamento_m") or p.get("espacamento_renques_m"), "espacamento_m_detector": a.get("espacamento_m"),
        "origem_das_arvores": (r or {}).get("origem_das_arvores"), "entre_as_fileiras": (r or {}).get("entre_as_fileiras") or p.get("entre_os_renques"),
        "serie_tem_lavoura": (r or {}).get("serie_tem_lavoura"), "arvores": p.get("arvores"),
        "onde_estao_os_renques": (r or {}).get("onde_estao_os_renques"), "contorno_cobre_os_renques": p.get("contorno_cobre_os_renques"),
        "area_ha": a.get("area_ha"), "lon": round(a["lon"], 6), "lat": round(a["lat"], 6),
        "data_imagem": (meta.get(fid) or {}).get("data_imagem"), "safra_referencia": "2024/2025",
        "amostra_atual_a_menos_de_300m": a.get("amostra_atual_a_menos_de_300m"),
        "origem": "detector de fileiras em CBERS-4A 2 m + duas leituras do Gemini 3.8 Flash High",
        "motivo_1a_leitura": p.get("motivo"), "duvida_2a_leitura": (r or {}).get("motivo_da_duvida"), "ficha": fid + ".png"})
    geoms.append(shape(a["geom"]))
    src = os.path.join(RAIZ, "fichas", fid + ".png")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(DEST, "fichas", fid + ".png"))
print("contagem:", dict(cont))
if linhas:
    gdf = gpd.GeoDataFrame(linhas, geometry=geoms, crs="EPSG:4326")
    gdf.to_file(os.path.join(DEST, "amostras_renques_candidatas.gpkg"), layer="poligonos", driver="GPKG")
    pts = gdf.copy()
    pts["geometry"] = gpd.points_from_xy(pts["lon"], pts["lat"])
    pts.to_file(os.path.join(DEST, "amostras_renques_candidatas.gpkg"), layer="pontos", driver="GPKG")
    gdf.to_file(os.path.join(DEST, "amostras_renques_candidatas.geojson"), driver="GeoJSON")
    with open(os.path.join(DEST, "amostras_renques_candidatas.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    print(len(linhas), "amostras empacotadas;", dict(Counter((l["nota"], l["classe_sugerida"]) for l in linhas)),
          "| novas (sem amostra atual perto):", sum(1 for l in linhas if not l["amostra_atual_a_menos_de_300m"]),
          "| hectares:", round(sum(l["area_ha"] for l in linhas)))
json.dump({"contagem": dict(cont), "empacotadas": len(linhas), "alvos_listras": len(alvos), "lidas": sum(1 for f in alvos if f in prim)},
          open(os.path.join(DEST, "resumo_entrega.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
