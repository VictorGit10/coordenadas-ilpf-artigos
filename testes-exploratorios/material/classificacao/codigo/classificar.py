"""Classifica pontos (lon, lat) com o modelo treinado: probabilidade de renque.

Exemplos:
  python classificar.py --entrada pontos.csv --saida saida.csv
  python classificar.py --entrada pontos.csv --datas 3      # maioria de 3 datas
  python classificar.py --pontos="-51.7,-17.9;-48.7,-17.9"

O CSV de entrada precisa das colunas `lon` e `lat` (e opcionalmente `id`).
Cada ponto vira um recorte de 400 m (2 m/pixel) do CBERS-4A, estacao seca.
`--datas 1` (padrao) usa a cena mais recente que passa no QA; `--datas 3`
usa ate 3 anos diferentes e decide pela maioria (empate = positivo).
Requer torch + timm (roda no Colab ou em qualquer maquina com eles).
"""
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (BASE_DIR, os.getcwd(), "/content"):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)
from comum import SCRIPTS, qa_img
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
import cbers

from modelo_util import (aplicar_cabeca, carregar_base, carregar_cabeca,
                         carregar_config, extrair_pil, norma)

ANOS = [2024, 2025, 2026, 2023]
MEIO_M = 200
WORKERS = 4


def melhor_recorte(lon, lat, cenas):
    if not cenas:
        return None
    for f in sorted(cenas, key=cbers._preferencia, reverse=True)[:8]:
        try:
            res = cbers.recorte_centro(lon, lat, MEIO_M, cenas=[f])
        except Exception:
            continue
        if qa_img(res.get("img")):
            return res
    return None


def recortes_ponto(lon, lat, n_datas):
    """Ate n_datas recortes de anos diferentes."""
    out = []
    for ano in ANOS:
        if len(out) >= n_datas:
            break
        cenas = cbers.buscar_cenas(lon, lat, f"{ano}-05-01", f"{ano}-09-30")
        res = melhor_recorte(lon, lat, cenas)
        if res is not None:
            out.append(res)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", help="CSV com colunas lon, lat (e opcional id)")
    ap.add_argument("--saida", default=os.path.join(BASE_DIR, "classificacao.csv"))
    ap.add_argument("--datas", type=int, default=1, help="1..3 datas de anos diferentes")
    ap.add_argument("--limiar", type=float, default=None,
                    help="sobrescreve o limiar salvo no modelo")
    ap.add_argument("--modelo", default=os.path.join(BASE_DIR, "modelo"))
    ap.add_argument("--pontos", default="",
                    help='pares "lon,lat" separados por ";" (alem ou em vez do --entrada)')
    a = ap.parse_args()

    if a.entrada:
        df = pd.read_csv(a.entrada)
        if not {"lon", "lat"}.issubset(df.columns):
            raise SystemExit("CSV precisa de colunas lon e lat")
        df = df.reset_index(drop=True)
        if "id" not in df.columns:
            df["id"] = [f"p{i}" for i in range(len(df))]
    else:
        df = pd.DataFrame(columns=["id", "lon", "lat"])
    extra = []
    for i, s in enumerate([x.strip() for x in a.pontos.split(";") if x.strip()]):
        try:
            lon, lat = [float(x) for x in s.split(",")]
        except Exception:
            raise SystemExit(f"ponto invalido: {s}")
        extra.append(dict(id=f"p{i}", lon=lon, lat=lat))
    if extra:
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
    if df.empty:
        raise SystemExit("nenhum ponto")
    if "id" not in df.columns:
        df["id"] = [f"p{i}" for i in range(len(df))]

    cfg = carregar_config(a.modelo)
    cab = carregar_cabeca(a.modelo)
    limiar = float(a.limiar if a.limiar is not None else cfg["limiar"])
    print(f"{len(df)} pontos; modelo {cfg['tag']} @ {cfg['input_size']} px; "
          f"{a.datas} data(s); limiar {limiar}", flush=True)
    model = carregar_base(cfg["base_model"], cfg["input_size"])
    mean, std = norma(model)

    t0 = time.time()
    linhas = []
    # lotes para nao encher a memoria com centenas de recortes
    lote = 48
    for ini in range(0, len(df), lote):
        sub = df.iloc[ini:ini + lote]
        # 1) downloads em paralelo (no maximo 4)
        def baixar(r):
            return r.id, recortes_ponto(float(r.lon), float(r.lat), a.datas)

        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            res = list(ex.map(baixar, [r for _, r in sub.iterrows()]))
        imgs, mapa = [], []
        for pid, lista in res:
            for j, rr in enumerate(lista):
                imgs.append(rr["img"])
                mapa.append((pid, j, rr["data"]))
        probs = {}
        if imgs:
            feats = extrair_pil(model, imgs, cfg["input_size"], mean, std, batch=8)
            p = aplicar_cabeca(feats, cab)
            for (pid, j, data), pp in zip(mapa, p):
                probs.setdefault(pid, []).append((data, float(pp)))
        for _, r in sub.iterrows():
            lst = probs.get(r.id, [])
            n = len(lst)
            np_ = int(sum(1 for _, pp in lst if pp >= limiar))
            prob = float(np.mean([pp for _, pp in lst])) if lst else float("nan")
            decisao = int(2 * np_ >= n) if n else -1
            linhas.append(dict(id=r.id, lon=float(r.lon), lat=float(r.lat),
                               n_datas=n,
                               datas="|".join(d for d, _ in lst),
                               probs="|".join(f"{pp:.4f}" for _, pp in lst),
                               prob=prob,
                               prob_max=float(max([pp for _, pp in lst])) if lst else float("nan"),
                               decisao=decisao))
        print(f"  {min(ini + lote, len(df))}/{len(df)} pontos "
              f"({time.time() - t0:.0f}s)", flush=True)

    pd.DataFrame(linhas).to_csv(a.saida, index=False)
    print(f"salvo {a.saida} ({len(linhas)} linhas)")


if __name__ == "__main__":
    main()
