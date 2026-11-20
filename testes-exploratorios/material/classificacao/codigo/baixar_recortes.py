"""Monta os recortes de 400 m (2 m/pixel) do CBERS-4A para o classificador.

Uso:
  python baixar_recortes.py ensino      # centros + deslocados do grupo ensino
  python baixar_recortes.py negativos   # negativos dificeis (urbano/terraco)
  python baixar_recortes.py medicao     # centros do grupo medicao (so no fim)

Regras fixas (decididas antes de olhar qualquer resultado):
- 400 m de lado (meio_m=200), centrado no ponto representativo do talhao;
- ate 3 datas da estacao seca (1/mai a 30/set) de anos DIFERENTES, tentando
  2024, 2025, 2026 e 2023, nessa ordem;
- dentro de cada ano, tenta as cenas mais recentes primeiro (cbers._preferencia)
  e aceita a primeira que passa no QA;
- no maximo 4 downloads simultaneos.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import shapely.ops
from PIL import Image
from shapely.geometry import Point

from comum import (BASE, COLS, DADOS, RECORTES, SCRIPTS, abrir_csv,
                   escrever_linhas, garantir_pastas, ler_csv, nome_arquivo,
                   qa_img)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
import cbers

ANOS = [2024, 2025, 2026, 2023]
N_DATAS = 3
MEIO_M = 200
WORKERS = 4

_t0 = time.time()


def log(msg):
    print(f"[{time.time() - _t0:7.1f}s] {msg}", flush=True)


def cenas_ano(lon, lat, ano):
    return cbers.buscar_cenas(lon, lat, f"{ano}-05-01", f"{ano}-09-30")


def melhor_recorte(lon, lat, cenas):
    """Tenta as cenas em ordem de preferencia e devolve a primeira com QA ok."""
    if not cenas:
        return None
    ordem = sorted(cenas, key=cbers._preferencia, reverse=True)[:8]
    for f in ordem:
        try:
            res = cbers.recorte_centro(lon, lat, MEIO_M, cenas=[f])
        except Exception:
            continue
        if qa_img(res.get("img")):
            return res
    return None


def salvar(img, nome):
    caminho = os.path.join(RECORTES, nome)
    Image.fromarray(img[..., :3]).save(caminho, optimize=True)
    return caminho


def baixar_ponto(lon, lat, anos, n_datas, tipo, talhao, idx="", categoria=""):
    """Baixa ate n_datas de anos diferentes. Devolve (linhas, falhas)."""
    linhas, falhas = [], []
    for ano in anos:
        if len(linhas) >= n_datas:
            break
        cenas = cenas_ano(lon, lat, ano)
        res = melhor_recorte(lon, lat, cenas)
        if res is None:
            falhas.append(f"{ano}:sem cena boa({len(cenas)})")
            continue
        data = res["data"]
        nome = nome_arquivo(talhao, tipo, idx, data, categoria)
        salvar(res["img"], nome)
        linhas.append(dict(talhao=talhao, data=data, arquivo=nome,
                           cena=res["id"],
                           href=next((f["assets"]["tci"]["href"] for f in cenas
                                      if f["id"] == res["id"]), ""),
                           lon=lon, lat=lat, ano=data[:4]))
    return linhas, falhas


def baixar_scene_fixa(lon, lat, row):
    """Baixa um recorte usando a cena ja escolhida para o centro do talhao."""
    fake = dict(id=row["cena"], assets={"tci": {"href": row["href"]}},
                properties={"datetime": row["data"] + "T00:00:00Z"})
    try:
        res = cbers.recorte_centro(lon, lat, MEIO_M, cenas=[fake])
    except Exception:
        return None
    return res if qa_img(res.get("img")) else None


# ------------------------------------------------------------------ ensino
def etapa_ensino():
    tal = gpd.read_file(os.path.join(BASE, "talhoes_divididos.gpkg"))
    tal = tal[tal.grupo == "ensino"].copy()
    tal["area_ha"] = tal.to_crs(6933).area / 1e4
    csv_path = os.path.join(DADOS, "recortes_ensino.csv")
    existentes = ler_csv(csv_path)
    ja = {(r["talhao"], r["tipo"], r["idx"]) for r in existentes}
    log(f"ensino: {len(tal)} talhoes, {len(existentes)} linhas ja existentes")

    f, w, _ = abrir_csv(csv_path)
    trava_rows = []

    def tarefa(r):
        centro = r.geometry.representative_point()
        if (str(r.talhao), "centro", "") in ja:
            return
        linhas, falhas = baixar_ponto(centro.x, centro.y, ANOS, N_DATAS,
                                      "centro", int(r.talhao))
        for ln in linhas:
            ln.update(grupo="ensino", rotulo=int(r.arvore), cod=int(r.cod),
                      bloco=r.bloco, tipo="centro", idx="", categoria="")
        with open(os.path.join(DADOS, "log_baixada.txt"), "a", encoding="utf-8") as lf:
            if falhas:
                lf.write(f"centro {r.talhao}: {'; '.join(falhas)}\n")
        return linhas

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(tarefa, r): r.talhao for _, r in tal.iterrows()}
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                linhas = fu.result()
            except Exception as e:
                log(f"erro talhao {futs[fu]}: {e}")
                continue
            if linhas:
                escrever_linhas(w, linhas)
            if i % 20 == 0 or i == len(futs):
                log(f"centros: {i}/{len(futs)}")
    f.close()

    # ---------------- deslocados dentro de talhoes grandes (so ensino)
    existentes = ler_csv(csv_path)
    centros = {}
    for r in existentes:
        if r["tipo"] != "centro":
            continue
        centros.setdefault(r["talhao"], []).append(r)
    ja = {(r["talhao"], r["tipo"], r["idx"]) for r in existentes}
    alvos = tal[(tal.area_ha >= 100.0) & tal.talhao.astype(str).isin(centros)]
    log(f"deslocados: {len(alvos)} talhoes >=100 ha com centro")
    f, w, _ = abrir_csv(csv_path)

    def pontos_deslocados(row):
        """Pontos a >=150 m da borda, em grade de 300 m, no maximo 2, os mais
        afastados do centro. Projecao azimutal local (metros reais)."""
        centro = row.geometry.representative_point()
        crs = pyproj.CRS.from_proj4(
            f"+proj=aeqd +lat_0={centro.y} +lon_0={centro.x} +datum=WGS84 +units=m +no_defs")
        tr = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        inv = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        g = shapely.ops.transform(tr.transform, row.geometry)
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda x: x.area)
        try:
            dentro = g.buffer(-150.0)
        except Exception:
            return []
        if dentro.is_empty:
            return []
        c = g.centroid
        x0, y0, x1, y1 = dentro.bounds
        cand = []
        step = 300.0
        y = y0 + step / 2
        while y < y1:
            x = x0 + step / 2
            while x < x1:
                p = Point(x, y)
                if dentro.contains(p):
                    cand.append((p.distance(c), x, y))
                x += step
            y += step
        cand.sort(reverse=True)
        out = []
        for _, x, y in cand:
            ok = True
            for _, xx, yy in out:
                if ((x - xx) ** 2 + (y - yy) ** 2) ** 0.5 < 300.0:
                    ok = False
                    break
            if ok:
                out.append((0, x, y))
            if len(out) == 2:
                break
        return [inv.transform(x, y) for _, x, y in out]

    tarefas = []
    for _, r in alvos.iterrows():
        pts = pontos_deslocados(r)
        for k, (x, y) in enumerate(pts, 1):
            if (str(r.talhao), "deslocado", str(k)) in ja:
                continue
            lon, lat = x, y
            tarefas.append((r, k, lon, lat))

    def tarefa2(r, k, lon, lat):
        linhas = []
        for row in centros[str(r.talhao)]:
            res = baixar_scene_fixa(lon, lat, row)
            if res is None:
                continue
            nome = nome_arquivo(int(r.talhao), "deslocado", str(k), res["data"])
            salvar(res["img"], nome)
            linhas.append(dict(talhao=int(r.talhao), grupo="ensino",
                               rotulo=int(r.arvore), data=res["data"],
                               arquivo=nome, cena=row["cena"], href=row["href"],
                               lon=lon, lat=lat, cod=int(r.cod), bloco=r.bloco,
                               tipo="deslocado", idx=str(k), categoria="",
                               ano=res["data"][:4]))
        return linhas

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(tarefa2, *t) for t in tarefas]
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                linhas = fu.result()
            except Exception as e:
                log(f"erro deslocado: {e}")
                continue
            if linhas:
                escrever_linhas(w, linhas)
            if i % 20 == 0 or i == len(futs):
                log(f"deslocados: {i}/{len(futs)}")
    f.close()
    log(f"ensino pronto: {len(ler_csv(csv_path))} linhas")


# --------------------------------------------------------------- negativos
def etapa_negativos():
    src = os.path.join(DADOS, "negativos_selecionados.csv")
    df = pd.read_csv(src)
    log(f"negativos: {len(df)} pontos")
    csv_path = os.path.join(DADOS, "recortes_negativos.csv")
    existentes = ler_csv(csv_path)
    ja = {r["talhao"] for r in existentes}
    f, w, _ = abrir_csv(csv_path)

    def tarefa(r):
        nome_id = r.ficha
        if nome_id in ja:
            return []
        linhas, falhas = baixar_ponto(float(r.lon), float(r.lat), ANOS, 2,
                                      "negativo", nome_id, categoria=r.categoria)
        for ln in linhas:
            ln.update(grupo="negativo_dificil", rotulo=0, cod="", bloco="",
                      tipo="negativo", idx="", categoria=r.categoria)
        with open(os.path.join(DADOS, "log_baixada.txt"), "a", encoding="utf-8") as lf:
            if falhas:
                lf.write(f"neg {nome_id}: {'; '.join(falhas)}\n")
        return linhas

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(tarefa, r) for _, r in df.iterrows()]
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                linhas = fu.result()
            except Exception as e:
                log(f"erro negativo: {e}")
                continue
            if linhas:
                escrever_linhas(w, linhas)
            if i % 25 == 0 or i == len(futs):
                log(f"negativos: {i}/{len(futs)}")
    f.close()
    log(f"negativos prontos: {len(ler_csv(csv_path))} linhas")


# ----------------------------------------------------------------- medicao
def etapa_medicao():
    tal = gpd.read_file(os.path.join(BASE, "talhoes_divididos.gpkg"))
    tal = tal[tal.grupo == "medicao"].copy()
    csv_path = os.path.join(DADOS, "recortes_medicao.csv")
    existentes = ler_csv(csv_path)
    ja = {r["talhao"] for r in existentes}
    f, w, _ = abrir_csv(csv_path)
    log(f"medicao: {len(tal)} talhoes, {len(existentes)} linhas ja existentes")

    def tarefa(r):
        if str(r.talhao) in ja:
            return []
        centro = r.geometry.representative_point()
        linhas, falhas = baixar_ponto(centro.x, centro.y, ANOS, N_DATAS,
                                      "centro", int(r.talhao))
        for ln in linhas:
            # sem rotulo/arvore no CSV de medicao, para nao vazar nada no treino
            ln.update(grupo="medicao", cod=int(r.cod), bloco=r.bloco,
                      tipo="centro", idx="", categoria="", rotulo="")
        with open(os.path.join(DADOS, "log_baixada.txt"), "a", encoding="utf-8") as lf:
            if falhas:
                lf.write(f"medicao {r.talhao}: {'; '.join(falhas)}\n")
        return linhas

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(tarefa, r): r.talhao for _, r in tal.iterrows()}
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                linhas = fu.result()
            except Exception as e:
                log(f"erro medicao {futs[fu]}: {e}")
                continue
            if linhas:
                escrever_linhas(w, linhas)
            if i % 20 == 0 or i == len(futs):
                log(f"medicao: {i}/{len(futs)}")
    f.close()
    log(f"medicao pronta: {len(ler_csv(csv_path))} linhas")


if __name__ == "__main__":
    garantir_pastas()
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["ensino", "negativos", "medicao"])
    a = ap.parse_args()
    if a.etapa == "ensino":
        etapa_ensino()
    elif a.etapa == "negativos":
        etapa_negativos()
    else:
        etapa_medicao()
