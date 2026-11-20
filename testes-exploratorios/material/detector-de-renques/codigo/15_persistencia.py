"""Teste de persistência: as fileiras que o detector achou na imagem de 2024/2025 também aparecem numa imagem antiga
(2020 a 2022) do mesmo lugar? Compara aprovadas (nota A), rejeitadas na 2a leitura (C) e rejeitadas na 1a leitura.
Não usa IA. Saída: persistencia.json e persistencia/<ID>_<periodo>.png (recortes dos casos com 2a leitura)."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pyproj
from PIL import Image, ImageDraw
from shapely.geometry import shape
from shapely.ops import transform as shp_transform

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ.get("ILPF_LISTRAS", os.path.join(RAIZ, "listras")))
import cbers  # noqa
from detector import detectar  # noqa

SAIDA = os.path.join(RAIZ, "persistencia")
os.makedirs(SAIDA, exist_ok=True)
PERIODOS = {"atual": ("2024-04-01", "2025-10-31"), "antiga": ("2023-03-01", "2023-12-31"), "nova": ("2026-02-01", "2026-10-31")}
alvos = {a["id"]: a for a in json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8")) if a["grupo"] == "listras"}
prim, rigor = {}, {}
for f in ["rodada5_listras", "rodada6_22KCE_2"]:
    prim.update(json.load(open(os.path.join(RAIZ, "leitura", f, "leituras.json"), encoding="utf-8")))
for f in ["rodada5b_rigor", "rodada5b_rigor2", "rodada6_rigor_22KCE_2"]:
    rigor.update(json.load(open(os.path.join(RAIZ, "leitura", f, "leituras.json"), encoding="utf-8")))


def veredito(fid):
    if fid in rigor:
        return "A" if rigor[fid].get("nota") == "A" else "C"
    return "sem renque (1a leitura)" if prim[fid].get("renques_de_arvores") != "sim" else "sim sem 2a leitura"


def medir(fid):
    a = alvos[fid]
    g = shape(a["geom"])
    res = {"id": fid, "veredito": veredito(fid), "area_ha": a.get("area_ha"), "esp_m": a.get("espacamento_m")}
    for nome, (ini, fim) in PERIODOS.items():
        try:
            cenas = cbers.buscar_cenas(a["lon"], a["lat"], ini, fim)
            minx, miny, maxx, maxy = g.bounds
            meio = int(min(1500, max(400, max(maxx - minx, maxy - miny) * 111000 / 2 + 150)))
            r = cbers.recorte_centro(a["lon"], a["lat"], meio, max_px=meio, cenas=cenas)
            if r.get("img") is None:
                res[nome] = {"erro": r.get("motivo")}
                continue
            img = r["img"]
            h, w = img.shape[:2]
            x0, y0, x1, y1 = r["limites"]
            tr = pyproj.Transformer.from_crs("EPSG:4326", r["crs"], always_xy=True).transform
            gp = shp_transform(tr, g)
            px = lambda x, y: ((x - x0) / (x1 - x0) * w, (y1 - y) / (y1 - y0) * h)
            m_alvo = Image.new("L", (w, h), 0)
            ImageDraw.Draw(m_alvo).polygon([px(x, y) for x, y in gp.exterior.coords], fill=1)
            m_alvo = np.array(m_alvo, bool)
            d = detectar(img, px_m=2 * meio / w)
            m_det = Image.new("L", (w, h), 0)
            dr = ImageDraw.Draw(m_det)
            for reg in d["regioes"]:
                if len(reg["contorno_px"]) >= 3:
                    dr.polygon([tuple(p) for p in reg["contorno_px"]], fill=1)
            m_det = np.array(m_det, bool)
            cob = float((m_alvo & m_det).sum() / max(m_alvo.sum(), 1))
            esp = [reg["espacamento_m"] for reg in d["regioes"]]
            res[nome] = {"data": r["data"], "cobertura": round(cob, 3), "regioes": len(d["regioes"]),
                         "score_max": round(float(d["score_max"]), 3), "espacamentos": [round(float(e), 1) for e in esp][:6]}
            if fid in rigor:
                im = Image.fromarray(img).convert("RGB")
                ImageDraw.Draw(im).line([px(x, y) for x, y in gp.exterior.coords], fill=(255, 230, 0), width=3)
                im.save(os.path.join(SAIDA, f"{fid}_{nome}_{r['data']}.png"))
        except Exception as e:  # noqa
            res[nome] = {"erro": f"{type(e).__name__}: {str(e)[:100]}"}
    print(fid, res["veredito"], res.get("antiga"), res.get("nova"), flush=True)
    return res


if __name__ == "__main__":
    ids = [f for f in alvos if f in prim]
    if "--so-rigor" in sys.argv:
        ids = [f for f in ids if f in rigor]
    with ThreadPoolExecutor(4) as ex:
        out = list(ex.map(medir, ids))
    json.dump(out, open(os.path.join(RAIZ, "persistencia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("FIM", len(out))
