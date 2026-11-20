"""Monta uma ficha PNG por alvo: (A) contexto em 2 m com o contorno, (B) detalhe de 500 m, (C) série de NDVI do Sentinel-2.
Uso: python 02_fichas.py [series|fichas|tudo] [--so GRUPO]
"""
import json, math, os, sys, time, io
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape
import pyproj
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cbers

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FICHAS = os.path.join(RAIZ, "fichas")
os.makedirs(FICHAS, exist_ok=True)
ARQ_SERIES = os.path.join(RAIZ, "series.json")
PROJETO = os.environ.get("EE_PROJETO", "SEU-PROJETO")
INI, FIM = (2020, 7), (2025, 10)


def periodos():
    out = []
    a, m = INI
    while (a, m) <= FIM:
        out.append((f"{a}-{m:02d}-01", f"{a}-{m:02d}-16"))
        a2, m2 = (a, m + 1) if m < 12 else (a + 1, 1)
        out.append((f"{a}-{m:02d}-16", f"{a2}-{m2:02d}-01"))
        a, m = a2, m2
    return out


def fase_series(alvos):
    import ee
    ee.Initialize(project=PROJETO)
    series = json.load(open(ARQ_SERIES, encoding="utf-8")) if os.path.exists(ARQ_SERIES) else {}
    falta = [a for a in alvos if a["id"] not in series]
    if not falta:
        print("séries: nada a fazer")
        return
    print(f"séries: {len(falta)} alvos", flush=True)
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    csp = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    per = periodos()
    novo = {a["id"]: {} for a in falta}
    for lote_i in range(0, len(falta), 120):
        lote = falta[lote_i:lote_i + 120]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(a["geom"]), {"fid": a["id"]}) for a in lote])
        for p_i in range(0, len(per), 12):
            bloco = per[p_i:p_i + 12]

            def um(par):
                par = ee.List(par)
                ini, fim = ee.String(par.get(0)), ee.String(par.get(1))
                col = (s2.filterDate(ini, fim).filterBounds(fc).linkCollection(csp, ["cs_cdf"])
                       .map(lambda im: im.updateMask(im.select("cs_cdf").gte(0.6)).normalizedDifference(["B8", "B4"]).rename("ndvi")))
                img = ee.Image(ee.Algorithms.If(col.size().gt(0), col.median(), ee.Image.constant(0).rename("ndvi").selfMask()))
                r = img.reduceRegions(fc, ee.Reducer.mean(), 20)
                return r.map(lambda f: ee.Feature(None, {"fid": f.get("fid"), "t": ini, "v": f.get("mean")}))

            for tent in range(4):
                try:
                    res = ee.FeatureCollection(ee.List(bloco).map(um)).flatten().getInfo()
                    break
                except Exception as e:  # noqa
                    print("  EE falhou:", str(e)[:120], "tentativa", tent + 1, flush=True)
                    time.sleep(15 * (tent + 1))
            else:
                raise RuntimeError("EE não respondeu")
            for f in res["features"]:
                p = f["properties"]
                if p.get("v") is not None:
                    novo[p["fid"]][p["t"]] = round(p["v"], 3)
            print(f"  lote {lote_i//120+1}, períodos {p_i+1}-{p_i+len(bloco)} de {len(per)}", flush=True)
        series.update({a["id"]: novo[a["id"]] for a in lote})
        json.dump(series, open(ARQ_SERIES, "w", encoding="utf-8"))


def fonte(tam):
    for nome in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nome, tam)
        except Exception:  # noqa
            pass
    return ImageFont.load_default()


def grafico(serie, larg=1500, alt=340):
    fig, ax = plt.subplots(figsize=(larg / 100, alt / 100), dpi=100)
    import datetime as dt
    xs = [dt.date.fromisoformat(k) + dt.timedelta(days=7) for k in sorted(serie)]
    ys = [serie[k] for k in sorted(serie)]
    for ano in range(INI[0], FIM[0] + 1):
        ax.axvspan(dt.date(ano, 10, 1), dt.date(ano + 1, 4, 1), color="#cfe3f5", alpha=0.6, lw=0)
        ax.axvline(dt.date(ano + 1, 1, 1), color="#888", lw=0.6)
    ax.plot(xs, ys, "-o", color="#1a6b1a", ms=3, lw=1.3)
    ax.set_ylim(0, 1)
    ax.set_xlim(dt.date(INI[0], INI[1], 1), dt.date(FIM[0], FIM[1], 28))
    ax.set_ylabel("NDVI")
    ax.grid(axis="y", color="#ddd", lw=0.6)
    ax.set_title("C. Série de NDVI (Sentinel-2, a cada 15 dias), média dentro do contorno amarelo. Faixas azuis = estação chuvosa (out–mar).", fontsize=10, loc="left")
    import matplotlib.dates as md
    ax.xaxis.set_major_locator(md.MonthLocator(bymonth=(1, 7)))
    ax.xaxis.set_major_formatter(md.DateFormatter("%b/%y"))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def uma_ficha(a, serie):
    destino = os.path.join(FICHAS, a["id"] + ".png")
    if os.path.exists(destino):
        return a["id"], "já existe", None
    g = shape(a["geom"])
    minx, miny, maxx, maxy = g.bounds
    lat0 = (miny + maxy) / 2
    larg_m = (maxx - minx) * 111320 * math.cos(math.radians(lat0))
    alt_m = (maxy - miny) * 110574
    meio = min(2600.0, max(650.0, 0.7 * max(larg_m, alt_m)))
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    cenas = cbers.buscar_cenas(cx, cy)
    A = cbers.recorte_centro(cx, cy, meio, 740, cenas)
    if A["img"] is None:
        return a["id"], "sem imagem: " + A["motivo"], None
    B = cbers.recorte_centro(a["lon"], a["lat"], 250, 250, cenas, id_cena=A["id"])
    S = 740
    tela = Image.new("RGB", (1500, 60 + S + 20 + 340), "white")
    d = ImageDraw.Draw(tela)
    imA = Image.fromarray(A["img"]).resize((S, S), Image.LANCZOS)
    tr = pyproj.Transformer.from_crs("EPSG:4326", A["crs"], always_xy=True).transform
    x0, y0, x1, y1 = A["limites"]
    dA = ImageDraw.Draw(imA)
    polis = list(g.geoms) if hasattr(g, "geoms") else [g]
    for p in polis:
        if p.geom_type != "Polygon":
            continue
        pts = [((tr(x, y)[0] - x0) / (x1 - x0) * S, (y1 - tr(x, y)[1]) / (y1 - y0) * S) for x, y in p.exterior.coords]
        dA.line(pts, fill=(255, 235, 0), width=3)
    # marca do quadro B dentro de A
    bx, by = tr(a["lon"], a["lat"])
    q = [((bx - 250 - x0) / (x1 - x0) * S, (y1 - (by + 250)) / (y1 - y0) * S), ((bx + 250 - x0) / (x1 - x0) * S, (y1 - (by - 250)) / (y1 - y0) * S)]
    dA.rectangle(q, outline=(0, 255, 255), width=1)
    tela.paste(imA, (0, 60))
    if B["img"] is not None:
        tela.paste(Image.fromarray(B["img"]).resize((S, S), Image.LANCZOS), (760, 60))
    else:
        d.text((780, 400), "detalhe indisponível", fill="black", font=fonte(22))
    f1, f2 = fonte(24), fonte(17)
    d.text((8, 4), f"Ficha {a['id']}", fill="black", font=f1)
    d.text((170, 8), f"Imagem CBERS-4A, 2 m, de {A['data']}. Norte para cima.", fill="black", font=f2)
    d.text((8, 36), f"A. Contexto: quadro de {2*meio:.0f} m de lado. Amarelo = área avaliada. Ciano = quadro B.", fill="black", font=f2)
    d.text((768, 36), "B. Detalhe: quadro de 500 m de lado no centro da área (cada pixel original = 2 m).", fill="black", font=f2)
    if serie:
        tela.paste(grafico(serie), (0, 60 + S + 20))
    else:
        d.text((20, 60 + S + 150), "série de NDVI indisponível", fill="black", font=f1)
    tela.save(destino, optimize=True)
    return a["id"], "ok", {"data_imagem": A["data"], "cena": A["id"], "lado_contexto_m": round(2 * meio)}


def fase_fichas(alvos):
    series = json.load(open(ARQ_SERIES, encoding="utf-8")) if os.path.exists(ARQ_SERIES) else {}
    arq_meta = os.path.join(RAIZ, "fichas_meta.json")
    meta = json.load(open(arq_meta, encoding="utf-8")) if os.path.exists(arq_meta) else {}
    t0 = time.time()
    with ThreadPoolExecutor(6) as ex:
        for i, (fid, st, m) in enumerate(ex.map(lambda a: uma_ficha(a, series.get(a["id"], {})), alvos), 1):
            if m:
                meta[fid] = m
            elif st != "já existe":
                meta[fid] = {"falha": st}
                print("  ", fid, st, flush=True)
            if i % 20 == 0:
                print(f"  {i}/{len(alvos)} fichas, {time.time()-t0:.0f}s", flush=True)
    json.dump(meta, open(arq_meta, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ok = sum(1 for a in alvos if os.path.exists(os.path.join(FICHAS, a["id"] + ".png")))
    print(f"fichas prontas: {ok} de {len(alvos)}")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    alvos = json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8"))
    if "--so" in sys.argv:
        alvos = [a for a in alvos if a["grupo"] == sys.argv[sys.argv.index("--so") + 1]]
    if "--n" in sys.argv:
        alvos = alvos[: int(sys.argv[sys.argv.index("--n") + 1])]
    if modo in ("series", "tudo"):
        fase_series(alvos)
    if modo in ("fichas", "tudo"):
        fase_fichas(alvos)
