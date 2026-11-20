"""Recorte de imagem CBERS-4A WPM (2 m, cor verdadeira) do catálogo aberto do INPE, sem baixar a cena inteira."""
import time
import numpy as np
import requests
import rasterio
from rasterio.windows import from_bounds
import pyproj

STAC = "https://data.inpe.br/bdc/stac/v1/search"
COLECAO = "CB4A-WPM-PCA-FUSED-1"
_env = rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF",
                    GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2", VSI_CACHE="TRUE")
_env.__enter__()
_cache_cenas = {}


def buscar_cenas(lon, lat, ini="2024-04-01", fim="2025-10-31", limite=40):
    chave = (round(lon, 1), round(lat, 1), ini, fim)
    d = 0.02
    corpo = {"collections": [COLECAO], "bbox": [lon - d, lat - d, lon + d, lat + d],
             "datetime": f"{ini}T00:00:00Z/{fim}T23:59:59Z", "limit": limite}
    for t in range(4):
        try:
            r = requests.post(STAC, json=corpo, timeout=60)
            r.raise_for_status()
            return r.json().get("features", [])
        except Exception:  # noqa
            time.sleep(3 * (t + 1))
    return []


def _preferencia(f):
    """Prefere a estação seca (maio a setembro: menos nuvem) e, dentro dela, a mais recente."""
    d = f["properties"].get("datetime", "")[:10]
    mes = int(d[5:7]) if d else 1
    return (1 if 5 <= mes <= 9 else 0, d)


def _realce(img):
    """Realce de contraste por canal (percentis 1 e 99), para tirar o tom avermelhado da cena bruta."""
    out = np.empty_like(img)
    for c in range(img.shape[2]):
        v = img[..., c].astype(np.float32)
        validos = v[v > 0]
        if validos.size < 50:
            out[..., c] = img[..., c]
            continue
        lo, hi = np.percentile(validos, [1, 99])
        out[..., c] = np.clip((v - lo) / max(hi - lo, 1) * 255, 0, 255).astype(np.uint8)
    return out


def recorte_centro(lon, lat, meio_m, max_px=740, cenas=None, id_cena=None):
    """Quadrado de lado 2*meio_m metros centrado em (lon, lat).
    Devolve dict(img, data, id, crs, limites) ou dict(img=None, motivo=...)."""
    cenas = cenas if cenas is not None else buscar_cenas(lon, lat)
    if not cenas:
        return {"img": None, "motivo": "sem cena"}
    ordem = sorted(cenas, key=_preferencia, reverse=True)
    if id_cena:
        ordem = [f for f in ordem if f["id"] == id_cena] + [f for f in ordem if f["id"] != id_cena]
    motivo = "sem cena válida"
    for f in ordem[:8]:
        try:
            with rasterio.open("/vsicurl/" + f["assets"]["tci"]["href"]) as ds:
                x, y = pyproj.Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True).transform(lon, lat)
                lim = (x - meio_m, y - meio_m, x + meio_m, y + meio_m)
                w = from_bounds(*lim, transform=ds.transform)
                larg, alt = int(round(w.width)), int(round(w.height))
                if larg < 20 or alt < 20:
                    continue
                esc = min(1.0, max_px / max(larg, alt))
                forma = (min(3, ds.count), max(1, int(alt * esc)), max(1, int(larg * esc)))
                arr = ds.read(indexes=list(range(1, forma[0] + 1)), window=w, out_shape=forma, boundless=True, fill_value=0)
                crs = ds.crs.to_string()
            img = np.transpose(arr, (1, 2, 0))
            if img.dtype != np.uint8:
                img = np.clip(img / (img.max() or 1) * 255, 0, 255).astype(np.uint8)
            if (img.sum(axis=2) == 0).mean() > 0.10:
                motivo = "recorte na borda da cena"
                continue
            if (img.min(axis=2) > 235).mean() > 0.30:
                motivo = "nuvem"
                continue
            return {"img": _realce(img), "data": f["properties"]["datetime"][:10], "id": f["id"], "crs": crs, "limites": lim}
        except Exception as e:  # noqa
            motivo = f"erro {type(e).__name__}: {str(e)[:80]}"
    return {"img": None, "motivo": motivo}
