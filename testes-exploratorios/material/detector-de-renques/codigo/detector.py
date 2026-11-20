"""Detector de renques de arvores (sistemas de integracao) em imagem CBERS-4A 2 m.

Como funciona
--------------
Um renque e uma faixa escura (copa de arvore) de 4 a 15 m de largura, repetida
a cada 10-60 m, com direcao bem definida, separada por faixas claras de pasto
ou lavoura.  O detector procura exatamente essa assinatura:

1. converte para cinza e remove a variacao de iluminacao (passa-alta);
2. em cada janela deslizante estima a direcao dominante do gradiente com o
   tensor de estrutura - essa e a normal dos renques;
3. projeta a janela nessa direcao (perfil 1D), tira a tendencia do perfil e
   mede o espectro 1D: pico estreito entre 10 e 60 m, amplitude (contraste
   copa x pasto), fracao de variancia explicada pela senoide e proeminencia
   do pico sobre o fundo espectral;
4. aplica um filtro de coerencia espacial: so sobrevive janela que tenha
   vizinhas com a mesma direcao e o mesmo espacamento (pasto com arvores
   soltas e ruido nao formam conjunto);
5. limiariza o mapa, fecha buracos, mantem regioes de no minimo 1 ha e
   funde regioes vizinhas de mesma orientacao e espacamento.

Pixels (0,0,0) sao "sem dado": sao preenchidos por inpainting e nao entram na
analise.
"""

import os
import sys

import cv2
import numpy as np

# ---------------------------------------------------------------- parametros
PERIODO_MIN_M = 10.0     # menor espacamento aceito (m)
PERIODO_MAX_M = 60.0     # maior espacamento aceito (m)
CICLOS_MIN = 4.6         # ciclos minimos dentro da janela para aceitar o periodo
R2_MIN = 0.28            # variancia minima explicada pela senoide
PROM_MIN = 1.35          # proeminencia minima do pico espectral
AREA_MIN_HA = 1.0        # area minima de uma regiao candidata
TH_SCORE = 4.6           # limiar do mapa de score (niveis de cinza)
JANELAS = (64, 128)      # tamanhos de janela em px (para px_m = 2 m)

_CACHE = {}


def _hann(n):
    k = ("h", n)
    if k not in _CACHE:
        _CACHE[k] = np.hanning(n).astype(np.float32)
    return _CACHE[k]


def _hpmat(n, sig):
    """Matriz (n x n) do passa-alta  p - gaussiana(p), com borda replicada."""
    key = ("hp", n, round(sig, 3))
    if key in _CACHE:
        return _CACHE[key]
    s = np.arange(-4 * n, 5 * n - 1)
    G = np.zeros((n, n), np.float32)
    idx = np.clip(s, 0, n - 1)
    for i in range(n):
        w = np.exp(-0.5 * ((i - s) / sig) ** 2)
        w /= w.sum()
        G[i] = np.bincount(idx, weights=w, minlength=n)[:n]
    H = (np.eye(n, dtype=np.float32) - G).astype(np.float32)
    _CACHE[key] = H
    return H


def _base_trig(n, f):
    k = ("t", n, f)
    if k not in _CACHE:
        ph = 2.0 * np.pi * f * np.arange(n) / n
        _CACHE[k] = (np.cos(ph).astype(np.float32), np.sin(ph).astype(np.float32))
    return _CACHE[k]


# ------------------------------------------------------------------ utilidades
def _cinza(img_rgb):
    """Cinza float32; pixels sem dado sao preenchidos por inpainting."""
    rgb = np.asarray(img_rgb)
    if rgb.ndim == 2:
        gray = rgb.astype(np.float32)
        valid = np.ones(gray.shape, bool)
    else:
        gray = cv2.cvtColor(rgb[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32)
        valid = rgb[..., :3].any(axis=2)
    if not valid.all():
        if valid.mean() < 0.02:
            return None, valid
        gray = cv2.inpaint(gray, (~valid).astype(np.uint8), 5, cv2.INPAINT_TELEA)
    return gray, valid


def _perfil(patch, ang, W):
    """Projeta o patch na direcao `ang` (media ao longo da direcao normal)."""
    M = cv2.getRotationMatrix2D((W / 2.0 - 0.5, W / 2.0 - 0.5), ang, 1.0)
    r = cv2.warpAffine(patch, M, (W, W), flags=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_REPLICATE)
    return r.mean(axis=0)


def _feats(p, Tmin, Tmax, sig):
    """Features espectrais de um perfil 1D."""
    n = len(p)
    pd = _hpmat(n, sig) @ p.astype(np.float32)
    pd = pd - pd.mean()
    var = float(pd.var()) + 1e-9
    k0 = max(int(np.ceil(n / Tmax)), 3)
    k1 = min(int(np.floor(n / Tmin)), n // 2 - 2)
    if k1 <= k0:
        return None
    spec = np.abs(np.fft.rfft(pd * _hann(n))) / n
    ks = spec[k0:k1 + 1]
    k = k0 + int(np.argmax(ks))
    c, s = _base_trig(n, k)
    a = 2.0 / n * float(np.dot(pd, c))
    b = 2.0 / n * float(np.dot(pd, s))
    amp = float(np.hypot(a, b))
    r2 = (a * a + b * b) / 2.0 / var
    nb = 0.25 * float(spec[k - 2] + spec[k - 1] + spec[k + 1] + spec[k + 2])
    prom = float(spec[k] / (nb + 1e-9))
    return dict(amp=amp, r2=r2, prom=prom, T=float(n) / k, k=k)


def _score(d):
    """Score bruto (unidade ~ niveis de cinza); 0 quando nao ha padrao."""
    if d is None:
        return 0.0
    f_prom = np.clip((d["prom"] - PROM_MIN) / 1.5, 0.0, 1.0)
    f_r2 = np.clip((d["r2"] - R2_MIN) / 0.50, 0.0, 1.0)
    return float(d["amp"] * np.sqrt(max(d["r2"], 0.0)) * f_prom
                 * (0.45 + 0.55 * f_r2))


def _score01(raw):
    return float(1.0 - np.exp(-max(raw, 0.0) / 10.0))


# ------------------------------------------------------------------- varredura
def _varredura(gray, px_m, W, step):
    """Varre janelas W x W e devolve (deteccoes, passo, W)."""
    H, Wi = gray.shape
    if H < W or Wi < W:
        return None
    Tmin = max(PERIODO_MIN_M / px_m, 3.0)
    Tmax = min(PERIODO_MAX_M / px_m, W / CICLOS_MIN)
    if Tmax <= Tmin * 1.3:
        return None
    sig_prof = 0.14 * W

    a = gray - cv2.GaussianBlur(gray, (0, 0), 0.20 * W)
    gx = cv2.Sobel(a, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(a, cv2.CV_32F, 0, 1, ksize=3)
    S = 2 * (W // 16) + 1
    Jxx = cv2.boxFilter(gx * gx, -1, (S, S), normalize=True)
    Jyy = cv2.boxFilter(gy * gy, -1, (S, S), normalize=True)
    Jxy = cv2.boxFilter(gx * gy, -1, (S, S), normalize=True)

    ny = (H - W) // step + 1
    nx = (Wi - W) // step + 1
    grid = np.zeros((ny, nx), np.float32)
    gT = np.zeros((ny, nx), np.float32)
    gA = np.zeros((ny, nx), np.float32)
    half = W / 2.0
    dets = []
    for iy, y in enumerate(range(0, H - W + 1, step)):
        for ix, x in enumerate(range(0, Wi - W + 1, step)):
            jxx = float(Jxx[y:y + W, x:x + W].sum())
            jyy = float(Jyy[y:y + W, x:x + W].sum())
            jxy = float(Jxy[y:y + W, x:x + W].sum())
            if jxx + jyy <= 1e-6:
                continue
            th = 0.5 * np.degrees(np.arctan2(2.0 * jxy, jxx - jyy))
            d = _feats(_perfil(a[y:y + W, x:x + W], th, W), Tmin, Tmax, sig_prof)
            sc = _score(d)
            if sc <= 0.0:
                continue
            grid[iy, ix] = sc
            gT[iy, ix] = d["T"]
            gA[iy, ix] = th % 180.0
            dets.append([sc, d["T"], th % 180.0, x + half, y + half, W])

    # coerencia espacial: media geometrica entre a janela e a vizinhanca
    # compativel (mesma direcao, mesmo espacamento).  Pico isolado -> 0.
    if dets:
        acc = np.zeros_like(grid)
        wsum = np.zeros_like(grid)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                s = np.roll(np.roll(grid, dy, 0), dx, 1)
                t = np.roll(np.roll(gT, dy, 0), dx, 1)
                a2 = np.roll(np.roll(gA, dy, 0), dx, 1)
                dang = np.abs(((a2 - gA + 90.0) % 180.0) - 90.0)
                dt = np.abs(t - gT) / np.maximum(gT, 1e-6)
                w = np.exp(-(dang / 14.0) ** 2) * np.exp(-(dt / 0.30) ** 2) * (s > 0)
                acc += s * w
                wsum += w
        viz = np.where(wsum > 0.6, acc / np.maximum(wsum, 1e-6), 0.0)
        grid = np.sqrt(np.maximum(grid, 0.0) * np.maximum(viz, 0.0))
        for d in dets:
            iy = int(round((d[4] - half) / step))
            ix = int(round((d[3] - half) / step))
            d[0] = float(grid[iy, ix])
    return dets, step, W


def _mapa(scan, shape):
    """Mapa de score na escala do pixel (maximo das janelas que cobrem o pixel)."""
    H, W = shape
    dets, step, Wb = scan
    if not dets:
        return np.zeros((H, W), np.float32)
    acc = np.zeros((H, W), np.float32)
    for sc, T, ang, cx, cy, w in dets:
        ix = int(round((cx - Wb / 2.0) / step))
        iy = int(round((cy - Wb / 2.0) / step))
        x0 = min(max(ix * step, 0), W - Wb)
        y0 = min(max(iy * step, 0), H - Wb)
        np.maximum(acc[y0:y0 + Wb, x0:x0 + Wb], sc, out=acc[y0:y0 + Wb, x0:x0 + Wb])
    return acc


# ------------------------------------------------------------------- regioes
def _ang_media(angs, pesos):
    a = np.radians(np.asarray(angs, float) * 2.0)
    w = np.asarray(pesos, float)
    s = float((np.sin(a) * w).sum())
    c = float((np.cos(a) * w).sum())
    return float(np.degrees(0.5 * np.arctan2(s, c)) % 180.0)


def _contorno(mask, x0, y0):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL,
                             cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return []
    c = max(cs, key=cv2.contourArea)
    per = cv2.arcLength(c, True)
    eps = 0.008 * per
    p = cv2.approxPolyDP(c, eps, True)
    while len(p) > 40:
        eps *= 1.35
        p = cv2.approxPolyDP(c, eps, True)
    return [(int(px + x0), int(py + y0)) for px, py in p.reshape(-1, 2)]


def _regioes(scans, gray_shape, px_m, step):
    """Limiariza o mapa, fecha buracos e vetoriza regioes >= 1 ha."""
    H, W = gray_shape
    smap = np.zeros(gray_shape, np.float32)
    for sc_ in scans:
        smap = np.maximum(smap, _mapa(sc_, gray_shape))
    if smap.max() < TH_SCORE:
        return []
    mask = (smap >= TH_SCORE).astype(np.uint8)
    core = (smap >= TH_SCORE * 1.18).astype(np.uint8)
    k = max(5, int(round(1.6 * step)) | 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    area_min = AREA_MIN_HA * 1e4 / (px_m * px_m)
    n, lab, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=8)
    todos = [d for sc_ in scans for d in sc_[0]]
    regs = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < area_min:
            continue
        sub = (lab == i)
        csub = sub[y:y + bh, x:x + bw]
        if float(core[y:y + bh, x:x + bw][csub].sum()) < area_min:
            continue
        smv = smap[y:y + bh, x:x + bw][csub]
        score = float(np.percentile(smv, 80))
        if score < TH_SCORE:
            continue
        vals, angs, Ts, wts = [], [], [], []
        for sc, T, ang, cx, cy, w in todos:
            ix, iy = int(cx), int(cy)
            if 0 <= iy < H and 0 <= ix < W and sub[iy, ix] and sc >= 0.7 * score:
                vals.append(sc)
                angs.append(ang)
                Ts.append(T)
                wts.append(sc)
        if len(vals) < 2:
            continue
        vals = np.asarray(vals)
        wts = np.asarray(wts)
        topo = vals >= np.percentile(vals, 60)
        T = float(np.average(np.asarray(Ts)[topo], weights=wts[topo]))
        ori = _ang_media(np.asarray(angs)[topo], wts[topo])
        cont = _contorno(csub, x, y)
        regs.append(dict(bbox_px=(int(x), int(y), int(x + bw), int(y + bh)),
                         area_ha=float(area) * px_m * px_m / 1e4,
                         score=_score01(score),
                         espacamento_m=T * px_m,
                         orientacao_graus=(-(ori + 90.0)) % 180.0,
                         contorno_px=cont,
                         _raw=score, _ori_img=ori, _T=T,
                         _cx=float(cents[i][0]), _cy=float(cents[i][1])))
    return regs


def _fundir(regs, px_m, dist_px=90.0):
    """Funde regioes vizinhas de mesma orientacao e espacamento parecido."""
    if len(regs) < 2:
        return regs
    pai = list(range(len(regs)))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    for i in range(len(regs)):
        for j in range(i + 1, len(regs)):
            a, b = regs[i], regs[j]
            dx = a["_cx"] - b["_cx"]
            dy = a["_cy"] - b["_cy"]
            ra = 0.5 * ((a["bbox_px"][2] - a["bbox_px"][0]) +
                        (a["bbox_px"][3] - a["bbox_px"][1]))
            rb = 0.5 * ((b["bbox_px"][2] - b["bbox_px"][0]) +
                        (b["bbox_px"][3] - b["bbox_px"][1]))
            if np.hypot(dx, dy) > dist_px + 0.5 * (ra + rb):
                continue
            da = abs(((a["_ori_img"] - b["_ori_img"] + 90) % 180) - 90)
            if da > 15.0:
                continue
            if max(a["_T"], b["_T"]) / max(min(a["_T"], b["_T"]), 1e-6) > 1.35:
                continue
            r1, r2 = raiz(i), raiz(j)
            if r1 != r2:
                pai[r2] = r1
    grupos = {}
    for i in range(len(regs)):
        grupos.setdefault(raiz(i), []).append(i)
    out = []
    for idxs in grupos.values():
        if len(idxs) == 1:
            out.append(regs[idxs[0]])
            continue
        g = [regs[i] for i in idxs]
        w = np.array([x["_raw"] for x in g], float)
        pts = np.array([p for x in g for p in x["contorno_px"]], np.int32)
        hull = cv2.convexHull(pts.reshape(-1, 1, 2))
        per = cv2.arcLength(hull, True)
        eps = 0.01 * per
        hp = cv2.approxPolyDP(hull, eps, True)
        while len(hp) > 40:
            eps *= 1.35
            hp = cv2.approxPolyDP(hull, eps, True)
        T = float(np.average([x["_T"] for x in g], weights=w))
        ori = _ang_media([x["_ori_img"] for x in g], w)
        raws = float(np.average([x["_raw"] for x in g], weights=w))
        x0 = min(x["bbox_px"][0] for x in g)
        y0 = min(x["bbox_px"][1] for x in g)
        x1 = max(x["bbox_px"][2] for x in g)
        y1 = max(x["bbox_px"][3] for x in g)
        out.append(dict(bbox_px=(int(x0), int(y0), int(x1), int(y1)),
                        area_ha=float(sum(x["area_ha"] for x in g)),
                        score=_score01(raws),
                        espacamento_m=T * px_m,
                        orientacao_graus=(-(ori + 90.0)) % 180.0,
                        contorno_px=[(int(px), int(py)) for px, py in hp.reshape(-1, 2)],
                        _raw=raws, _ori_img=ori, _T=T,
                        _cx=float(np.average([x["_cx"] for x in g], weights=w)),
                        _cy=float(np.average([x["_cy"] for x in g], weights=w))))
    return out


# ---------------------------------------------------------------------- API
def detectar(img_rgb, px_m=2.0):
    """Detecta regioes candidatas a renques de arvores.

    img_rgb : numpy uint8 HxWx3 (RGB).  Pixels (0,0,0) sao "sem dado".
    px_m    : tamanho do pixel em metros.

    Devolve dict com:
      'regioes'   : lista de dicts com 'bbox_px', 'area_ha', 'score',
                    'espacamento_m', 'orientacao_graus' e 'contorno_px'
      'score_max' : maior score entre as regioes (0 se nada foi achado)
    """
    gray, _ = _cinza(img_rgb)
    if gray is None:
        return dict(regioes=[], score_max=0.0)
    H, W = gray.shape
    escala = 2.0 / float(px_m)
    step = max(12, min(50, int(round(min(H, W) / 55.0))))
    scans = []
    for Wb in JANELAS:
        Ww = int(round(Wb * escala))
        Ww = min(max(Ww, 40), 192)
        if H < Ww or W < Ww:
            continue
        st = max(8, min(step, int(round(0.75 * Ww))))
        r = _varredura(gray, px_m, Ww, st)
        if r is not None and r[0]:
            scans.append(r)
    if not scans:
        return dict(regioes=[], score_max=0.0)

    regs = _regioes(scans, gray.shape, px_m, step)
    regs = _fundir(regs, px_m, dist_px=60.0 * escala)
    regs.sort(key=lambda r: -r["_raw"])
    for r in regs:
        for k in ("_raw", "_ori_img", "_T", "_cx", "_cy"):
            r.pop(k, None)
    smax = float(max((r["score"] for r in regs), default=0.0))
    return dict(regioes=regs, score_max=smax)


# ---------------------------------------------------------------------- CLI
def _tabela(pasta, salvar=False):
    nomes = sorted(f for f in os.listdir(pasta) if f.lower().endswith(".png"))
    linhas = []
    pos = neg = npos = nneg = 0
    outdir = os.path.join(pasta, "..", "saida")
    if salvar:
        os.makedirs(outdir, exist_ok=True)
    for nome in nomes:
        bgr = cv2.imread(os.path.join(pasta, nome), cv2.IMREAD_COLOR)
        if bgr is None:
            continue
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        res = detectar(rgb, 2.0)
        regs = res["regioes"]
        area = sum(r["area_ha"] for r in regs)
        esp = regs[0]["espacamento_m"] if regs else 0.0
        linhas.append((nome, res["score_max"], len(regs), area, esp))
        base = nome.lower()
        if base.startswith("pos"):
            npos += 1
            pos += 1 if regs else 0
        elif base.startswith("neg"):
            nneg += 1
            neg += 1 if regs else 0
        if salvar:
            out = bgr.copy()
            for r in regs:
                if len(r["contorno_px"]) >= 3:
                    c = np.array(r["contorno_px"], np.int32).reshape(-1, 1, 2)
                    cv2.polylines(out, [c], True, (0, 0, 255), 2)
            cv2.imwrite(os.path.join(outdir, nome), out)

    w = max([len(x[0]) for x in linhas] + [10])
    print(f"{'arquivo':<{w}}  {'score_max':>9}  {'regioes':>7}  {'area_ha':>8}  {'esp_m':>7}")
    print("-" * (w + 40))
    for nome, sm, nr, area, esp in linhas:
        print(f"{nome:<{w}}  {sm:9.3f}  {nr:7d}  {area:8.2f}  {esp:7.1f}")
    print("-" * (w + 40))
    print(f"pos detectados: {pos}/{npos}    neg marcados por engano: {neg}/{nneg}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    pasta = args[0] if args else "exemplos"
    _tabela(pasta, salvar="--salvar" in sys.argv)
