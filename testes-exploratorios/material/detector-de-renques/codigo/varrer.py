"""Varre areas com o detector de renques e grava os candidatos georreferenciados.

Uso:
    python varrer.py --tile 22KGE_2
    python varrer.py --bbox OESTE SUL LESTE NORTE --nome teste
    python varrer.py --todos

Cada area e dividida em blocos quadrados de ``--bloco_m`` metros (5000 m por
padrao) com 300 m de sobreposicao.  Cada bloco e lido em paralelo com
``cbers.recorte_centro`` e processado por ``detector.detectar``; os contornos
sao convertidos de pixel para o CRS da cena e dai para EPSG:4326.

O resultado bruto de cada bloco fica em ``candidatos/_blocos/<nome>/<i>.json``,
o que torna a varredura retomavel.  As regioes dos blocos sao fundidas quando
se sobrepoem e o resultado final vai para ``candidatos/<nome>.geojson``.
"""

import argparse
import json
import math
import os
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from pyproj import Transformer
from shapely import get_parts, make_valid
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shapely_transform, unary_union
from shapely.strtree import STRtree

import cbers
import detector

# ------------------------------------------------------------------ parametros
SOBREPOSICAO_M = 300.0       # sobreposicao entre blocos vizinhos
AREA_MIN_HA = 1.0            # area minima de um candidato
PASTA_SAIDA = "candidatos"
PASTA_BLOCOS = os.path.join(PASTA_SAIDA, "_blocos")

_DIR = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------- utilidades
def _utm_crs(lon, lat):
    """EPSG da zona UTM que contem o ponto."""
    zona = int((lon + 180.0) // 6.0) + 1
    zona = min(max(zona, 1), 60)
    return "EPSG:%d" % ((32600 if lat >= 0 else 32700) + zona)


def _caixa_metros(oeste, sul, leste, norte):
    """BBox geografica -> (minx, miny, maxx, maxy, crs) na projecao local.

    A borda do retangulo em graus e amostrada ponto a ponto; a bbox dos pontos
    projetados contem o retangulo inteiro (as bordas projetadas sao curvas).
    """
    lon_c = 0.5 * (oeste + leste)
    lat_c = 0.5 * (sul + norte)
    crs = _utm_crs(lon_c, lat_c)
    fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    n = 41
    los = np.linspace(oeste, leste, n)
    las = np.linspace(sul, norte, n)
    lons = np.concatenate([los, los, np.full(n, oeste), np.full(n, leste)])
    lats = np.concatenate([np.full(n, sul), np.full(n, norte), las, las])
    xs, ys = fwd.transform(lons, lats)
    return float(np.min(xs)), float(np.min(ys)), float(np.max(xs)), float(np.max(ys)), crs


def _blocos(oeste, sul, leste, norte, bloco_m):
    """Lista de blocos (centro em graus) cobrindo a area."""
    minx, miny, maxx, maxy, crs = _caixa_metros(oeste, sul, leste, norte)
    inv = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    passo = max(bloco_m - SOBREPOSICAO_M, 1.0)
    largura = maxx - minx
    altura = maxy - miny
    nx = max(1, int(math.ceil((largura - bloco_m) / passo)) + 1) if largura > bloco_m else 1
    ny = max(1, int(math.ceil((altura - bloco_m) / passo)) + 1) if altura > bloco_m else 1

    # Com um bloco so, centraliza na area; senao comeca no canto sudoeste.
    if nx == 1:
        x_base = 0.5 * (minx + maxx) - 0.5 * bloco_m
    else:
        x_base = minx
    if ny == 1:
        y_base = 0.5 * (miny + maxy) - 0.5 * bloco_m
    else:
        y_base = miny

    jobs = []
    k = 0
    for j in range(ny):
        for i in range(nx):
            xc = x_base + i * passo + 0.5 * bloco_m
            yc = y_base + j * passo + 0.5 * bloco_m
            lon, lat = inv.transform(xc, yc)
            jobs.append(dict(i=k, lon=float(lon), lat=float(lat),
                             meio_m=0.5 * bloco_m, bloco_m=float(bloco_m)))
            k += 1
    return jobs


def _caminho_bloco(nome, i):
    return os.path.join(PASTA_BLOCOS, nome, "%d.json" % i)


def _ler_cache(caminho, job):
    """Le o resultado de um bloco, se existir e corresponder a este bloco."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("status") not in ("ok", "sem_imagem"):
            return None
        if abs(float(d.get("lon", 1e9)) - job["lon"]) > 1e-7:
            return None
        if abs(float(d.get("lat", 1e9)) - job["lat"]) > 1e-7:
            return None
        if abs(float(d.get("meio_m", -1e9)) - job["meio_m"]) > 0.01:
            return None
        return d
    except (OSError, ValueError, TypeError):
        return None


def _gravar_json(caminho, obj):
    """Grava JSON de forma atomica (tmp + replace)."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, caminho)


# --------------------------------------------------------------- bloco (filho)
def _processar_bloco(job):
    """Le a imagem, roda o detector e devolve as regioes em lon/lat.

    Roda no processo filho.  Uma excecao faz o bloco ser tentado uma segunda vez.
    """
    lon = job["lon"]
    lat = job["lat"]
    meio = job["meio_m"]
    motivo = "erro desconhecido"
    for tentativa in range(2):
        try:
            r = cbers.recorte_centro(lon, lat, meio, max_px=int(round(meio)))
            if r.get("img") is None:
                motivo = str(r.get("motivo", "sem imagem"))
                # "erro ..." veio de uma excecao dentro do cbers: tenta de novo.
                if motivo.startswith("erro") and tentativa == 0:
                    time.sleep(2.0)
                    continue
                # Erro de leitura nao e cacheado: a proxima rodada tenta de novo.
                estado = "erro" if motivo.startswith("erro") else "sem_imagem"
                return dict(i=job["i"], status=estado, motivo=motivo,
                            lon=lon, lat=lat, meio_m=meio)

            img = r["img"]
            minx, miny, maxx, maxy = (float(v) for v in r["limites"])
            H, W = img.shape[0], img.shape[1]
            dx = (maxx - minx) / float(W)
            dy = (maxy - miny) / float(H)
            px_m = 0.5 * (dx + dy)

            res = detector.detectar(img, px_m=px_m)
            tr = Transformer.from_crs(r["crs"], "EPSG:4326", always_xy=True)

            regioes = []
            for reg in res.get("regioes", []):
                pts = reg.get("contorno_px") or []
                if len(pts) < 3:
                    continue
                # Pixel -> CRS da cena.  O centro do pixel (x, y) fica em
                # (x + 0.5, y + 0.5); a linha 0 e o norte (maxy).
                xs = [minx + (float(x) + 0.5) * dx for x, y in pts]
                ys = [maxy - (float(y) + 0.5) * dy for x, y in pts]
                lons, lats = tr.transform(xs, ys)
                anel = [[float(a), float(b)] for a, b in zip(lons, lats)]
                if anel[0] != anel[-1]:
                    anel.append(anel[0])
                regioes.append(dict(
                    anel=anel,
                    area_ha=float(reg["area_ha"]),
                    score=float(reg["score"]),
                    espacamento_m=float(reg["espacamento_m"]),
                    orientacao_graus=float(reg["orientacao_graus"]),
                ))

            return dict(i=job["i"], status="ok", motivo="",
                        lon=lon, lat=lat, meio_m=meio,
                        data_imagem=str(r.get("data", "")),
                        cena=str(r.get("id", "")),
                        crs=str(r.get("crs", "")),
                        px_m=float(px_m), regioes=regioes)
        except Exception as e:  # noqa: BLE001 - o bloco nao pode derrubar a varredura
            motivo = "%s: %s" % (type(e).__name__, str(e)[:160])
            if tentativa == 0:
                time.sleep(2.0)
                traceback.print_exc()
    return dict(i=job["i"], status="erro", motivo=motivo,
                lon=lon, lat=lat, meio_m=meio)


# -------------------------------------------------------------------- geometria
_TRANSFORMADORES = {}


def _area_m2(geom, lon, lat):
    """Area de um poligono lon/lat em m2, numa projecao UTM local."""
    crs = _utm_crs(lon, lat)
    tr = _TRANSFORMADORES.get(crs)
    if tr is None:
        tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        _TRANSFORMADORES[crs] = tr
    return abs(float(shapely_transform(tr.transform, geom).area))


def _limpar_geometria(g):
    """Devolve Polygon/MultiPolygon valido (ou vazio) a partir de uma uniao."""
    if g is None or g.is_empty:
        return Polygon()
    if not g.is_valid:
        try:
            g = make_valid(g)
        except Exception:  # noqa: BLE001
            g = g.buffer(0)
    if g.geom_type == "GeometryCollection":
        partes = [p for p in get_parts(g)
                  if p.geom_type in ("Polygon", "MultiPolygon") and not p.is_empty]
        if not partes:
            return Polygon()
        g = unary_union(partes)
    if g.geom_type not in ("Polygon", "MultiPolygon"):
        return Polygon()
    return g


def _media_angular(angs, pesos):
    """Media circular de angulos em graus modulo 180."""
    a = np.radians(np.asarray(angs, dtype=float) * 2.0)
    w = np.asarray(pesos, dtype=float)
    s = float((np.sin(a) * w).sum())
    c = float((np.cos(a) * w).sum())
    if s == 0.0 and c == 0.0:
        return float(np.asarray(angs, dtype=float).mean() % 180.0)
    return float(np.degrees(0.5 * np.arctan2(s, c)) % 180.0)


def _juntar(resultados):
    """Junta as regioes de todos os blocos, fundindo as que se sobrepoem."""
    regs = []
    for i in sorted(resultados):
        d = resultados[i]
        if d.get("status") != "ok":
            continue
        for r in d.get("regioes", []):
            anel = r.get("anel") or []
            if len(anel) < 4:
                continue
            try:
                p = Polygon(anel)
            except Exception:  # noqa: BLE001
                continue
            if p.is_empty:
                continue
            if not p.is_valid:
                p = p.buffer(0)
                if p.geom_type == "MultiPolygon":
                    # Mantem a maior parte; o detector devolve manchas simples.
                    p = max(p.geoms, key=lambda x: x.area)
            if p.is_empty or p.geom_type != "Polygon":
                continue
            regs.append(dict(poly=p, area_ha=float(r["area_ha"]),
                             score=float(r["score"]),
                             espacamento_m=float(r["espacamento_m"]),
                             orientacao_graus=float(r["orientacao_graus"]),
                             data_imagem=d.get("data_imagem", ""),
                             cena=d.get("cena", "")))

    n = len(regs)
    if n == 0:
        return []

    # Sobreposicao entre regioes de blocos vizinhos.  O limiar em m2 evita
    # fundir poligonos que apenas se tocam por uma linha/ruido numerico.
    geoms = [r["poly"] for r in regs]
    arvore = STRtree(geoms)
    pai = list(range(n))

    def raiz(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a

    for i, g in enumerate(geoms):
        for j in arvore.query(g):
            j = int(j)
            if j <= i:
                continue
            h = geoms[j]
            if not g.intersects(h):
                continue
            inter = g.intersection(h)
            if inter.is_empty or inter.area <= 0.0:
                continue
            cy = float(inter.centroid.y)
            m2 = float(inter.area) * (111320.0 * math.cos(math.radians(cy))) * 110574.0
            if m2 < 1.0:
                continue
            ra, rb = raiz(i), raiz(j)
            if ra != rb:
                pai[rb] = ra

    grupos = {}
    for i in range(n):
        grupos.setdefault(raiz(i), []).append(i)

    saida = []
    for idxs in grupos.values():
        if len(idxs) == 1:
            g = geoms[idxs[0]]
        else:
            g = unary_union([geoms[i] for i in idxs])
        g = _limpar_geometria(g)
        if g.is_empty:
            continue

        membros = [regs[i] for i in idxs]
        lon_c, lat_c = float(g.centroid.x), float(g.centroid.y)
        area_ha = _area_m2(g, lon_c, lat_c) / 1e4
        if area_ha < AREA_MIN_HA:
            continue

        areas = np.array([max(r["area_ha"], 0.0) for r in membros], dtype=float)
        if areas.sum() <= 0.0:
            areas = np.ones(len(membros), dtype=float)
        esp = float(np.average([r["espacamento_m"] for r in membros], weights=areas))
        ori = _media_angular([r["orientacao_graus"] for r in membros], areas)
        melhor = max(membros, key=lambda r: (r["score"], r["area_ha"]))

        # Ponto garantidamente dentro do poligono.
        pt = g.representative_point()
        saida.append(dict(
            geom=g, area_ha=float(area_ha),
            score=float(max(r["score"] for r in membros)),
            espacamento_m=esp,
            orientacao_graus=ori,
            data_imagem=melhor["data_imagem"],
            cena=melhor["cena"],
            lon=float(pt.x), lat=float(pt.y),
        ))

    saida.sort(key=lambda r: (-r["score"], -r["area_ha"]))
    return saida


# ---------------------------------------------------------------------- area
def _carregar_tiles():
    caminho = os.path.join(_DIR, "tiles.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _nome_seguro(nome):
    return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in nome)


def varrer_area(nome, oeste, sul, leste, norte, processos, bloco_m):
    """Varre uma area, grava o GeoJSON e imprime o resumo."""
    t0 = time.time()
    nome = _nome_seguro(nome)
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    jobs = _blocos(oeste, sul, leste, norte, bloco_m)
    total = len(jobs)

    resultados = {}
    pendentes = []
    for job in jobs:
        d = _ler_cache(_caminho_bloco(nome, job["i"]), job)
        if d is None:
            pendentes.append(job)
        else:
            resultados[d["i"]] = d

    print("[%s] %d blocos (%.1f x %.1f km): %d em cache, %d a fazer"
          % (nome, total, (leste - oeste) * 111.32 * math.cos(math.radians(0.5 * (sul + norte))),
             (norte - sul) * 110.57, len(resultados), len(pendentes)), flush=True)

    feitos = len(resultados)
    if pendentes:
        with ProcessPoolExecutor(max_workers=max(1, int(processos))) as ex:
            futuros = {ex.submit(_processar_bloco, job): job for job in pendentes}
            for fut in as_completed(futuros):
                job = futuros[fut]
                try:
                    d = fut.result()
                except Exception as e:  # noqa: BLE001
                    d = dict(i=job["i"], status="erro",
                             motivo="%s: %s" % (type(e).__name__, str(e)[:160]),
                             lon=job["lon"], lat=job["lat"], meio_m=job["meio_m"])
                resultados[d["i"]] = d
                # So guarda o que nao precisa ser refeito numa proxima rodada.
                if d["status"] in ("ok", "sem_imagem"):
                    _gravar_json(_caminho_bloco(nome, job["i"]), d)
                feitos += 1
                if feitos % 10 == 0 or feitos == total:
                    print("[%s] %d/%d blocos (%.1f s)"
                          % (nome, feitos, total, time.time() - t0), flush=True)
    elif total:
        print("[%s] %d/%d blocos (todos em cache)" % (nome, total, total), flush=True)

    # Blocos sem imagem / com erro: contados e listados.
    sem = [resultados[i] for i in sorted(resultados) if resultados[i].get("status") != "ok"]
    for d in sem:
        print("  SEM IMAGEM bloco %d (%.5f, %.5f): %s"
              % (d["i"], d["lon"], d["lat"], d.get("motivo", "")), flush=True)

    regioes = _juntar(resultados)

    features = []
    for k, r in enumerate(regioes, start=1):
        features.append(dict(
            type="Feature",
            geometry=mapping(r["geom"]),
            properties=dict(
                id="%s_%04d" % (nome, k),
                tile=nome,
                area_ha=round(r["area_ha"], 3),
                score=round(r["score"], 4),
                espacamento_m=round(r["espacamento_m"], 2),
                orientacao_graus=round(r["orientacao_graus"], 2),
                data_imagem=r["data_imagem"],
                cena=r["cena"],
                lon=r["lon"],
                lat=r["lat"],
            ),
        ))

    fc = dict(type="FeatureCollection",
              name=nome,
              crs=dict(type="name", properties=dict(
                  name="urn:ogc:def:crs:OGC:1.3:CRS84")),
              features=features)
    _gravar_json(os.path.join(PASTA_SAIDA, nome + ".geojson"), fc)

    area_total = sum(r["area_ha"] for r in regioes)
    segundos = time.time() - t0
    print("FIM %s: %d blocos, %d sem imagem, %d regiões, %.1f hectares, %.1f segundos"
          % (nome, total, len(sem), len(regioes), area_total, segundos), flush=True)
    return dict(nome=nome, total=total, sem=len(sem), regioes=len(regioes),
                area_ha=area_total, segundos=segundos)


# ----------------------------------------------------------------------- CLI
def main(argv=None):
    p = argparse.ArgumentParser(
        description="Varre tiles com o detector de renques e grava candidatos.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tile", help="nome do tile em tiles.json (ex.: 22KGE_2)")
    g.add_argument("--bbox", nargs=4, type=float,
                   metavar=("OESTE", "SUL", "LESTE", "NORTE"),
                   help="retangulo em graus: OESTE SUL LESTE NORTE")
    g.add_argument("--todos", action="store_true", help="varre os 26 tiles")
    p.add_argument("--nome", help="nome de saida (para --bbox)")
    p.add_argument("--processos", type=int, default=4, help="processos (padrao 4)")
    p.add_argument("--bloco_m", type=float, default=5000.0,
                   help="lado do bloco em metros (padrao 5000)")
    args = p.parse_args(argv)

    if args.bloco_m <= SOBREPOSICAO_M:
        p.error("--bloco_m precisa ser maior que %.0f m" % SOBREPOSICAO_M)

    areas = []
    if args.todos:
        for t in _carregar_tiles()["tiles"]:
            (lat_s, lon_o), (lat_n, lon_l) = t["bounds"]
            areas.append((t["tile"], lon_o, lat_s, lon_l, lat_n))
    elif args.tile:
        alvo = None
        for t in _carregar_tiles()["tiles"]:
            if t["tile"] == args.tile:
                alvo = t
                break
        if alvo is None:
            p.error("tile %r nao encontrado em tiles.json" % args.tile)
        (lat_s, lon_o), (lat_n, lon_l) = alvo["bounds"]
        areas.append((args.nome or alvo["tile"], lon_o, lat_s, lon_l, lat_n))
    else:
        oeste, sul, leste, norte = args.bbox
        if not (oeste < leste and sul < norte):
            p.error("--bbox invalido: use OESTE < LESTE e SUL < NORTE")
        nome = args.nome or ("bbox_%.3f_%.3f_%.3f_%.3f" % (oeste, sul, leste, norte))
        areas.append((nome, oeste, sul, leste, norte))

    t0 = time.time()
    resumos = []
    for nome, oeste, sul, leste, norte in areas:
        try:
            resumos.append(varrer_area(nome, oeste, sul, leste, norte,
                                       args.processos, args.bloco_m))
        except Exception:  # noqa: BLE001 - em --todos, segue para o proximo tile
            print("ERRO ao varrer %s:" % nome, flush=True)
            traceback.print_exc()

    if args.todos:
        ok = sum(1 for r in resumos if r)
        print("TOTAL: %d/%d tiles, %d regioes, %.1f hectares, %.1f s"
              % (ok, len(areas), sum(r["regioes"] for r in resumos),
                 sum(r["area_ha"] for r in resumos), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
