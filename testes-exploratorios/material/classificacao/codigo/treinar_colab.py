"""Treina a cabeca (regressao logistica) sobre features congeladas no Colab.

Entrada (ja descompactada em /content/ensino):
  recortes_ensino.csv, recortes_negativos.csv, recortes/*.png
Saida: /content/modelo/{config.json,cabeca.npz,cv_resultados.json,ensino_oof.csv}

Regras fixas desta etapa:
- validacao cruzada 5-fold agrupada por bloco (talhoes) / ponto (negativos);
- 8 transformacoes dihedral por imagem (treino e TTA);
- metricas de talhao apenas com recortes de CENTRO do grupo ensino;
- modelo escolhido por AUC OOF na imagem; limiar escolhido por acuracia
  balanceada no talhao (maioria das datas; empate = positivo).
"""
import json
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, "/content")
from modelo_util import (N_TTA, aplicar_cabeca, carregar_base, extrair_lista,
                         norma)

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

DADOS = "/content/ensino"
SAIDA = "/content/modelo"
CACHE = "/content/cache"
CS = [0.03, 0.1, 0.3, 1.0]
CONFIGS = [
    dict(tag="dinov2b448", base="vit_base_patch14_dinov2.lvd142m", size=448),
    dict(tag="convnextt448", base="convnext_tiny.fb_in22k_ft_in1k", size=448),
    dict(tag="dinov2b224", base="vit_base_patch14_dinov2.lvd142m", size=224),
]
T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


def carregar_dados():
    ens = pd.read_csv(os.path.join(DADOS, "recortes_ensino.csv"))
    neg = pd.read_csv(os.path.join(DADOS, "recortes_negativos.csv"))
    df = pd.concat([ens, neg], ignore_index=True)
    df["rotulo"] = df["rotulo"].astype(int)
    df["arquivo"] = df["arquivo"].astype(str)
    df["talhao"] = df["talhao"].astype(str)
    df["grupo_cv"] = np.where(df["grupo"] == "negativo_dificil",
                              "neg:" + df["talhao"], df["bloco"].astype(str))
    df["caminho"] = [os.path.join(DADOS, "recortes", a) for a in df["arquivo"]]
    falta = [p for p in df["caminho"] if not os.path.exists(p)]
    if falta:
        raise SystemExit(f"faltam {len(falta)} imagens; ex.: {falta[:3]}")
    return df


def extrair_tag(df, cfg):
    os.makedirs(CACHE, exist_ok=True)
    cache = os.path.join(CACHE, f"feat_{cfg['tag']}.npz")
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        if list(z["arquivos"]) == list(df["arquivo"]):
            log(f"{cfg['tag']}: cache carregado {z['X'].shape}")
            return z["X"]
    log(f"{cfg['tag']}: carregando {cfg['base']} @ {cfg['size']}")
    model = carregar_base(cfg["base"], cfg["size"])
    mean, std = norma(model)
    log(f"{cfg['tag']}: extraindo {len(df)} imagens x {N_TTA} visoes")
    X = extrair_lista(model, list(df["caminho"]), cfg["size"], mean, std,
                      batch=8, log=log)
    np.savez_compressed(cache, X=X, arquivos=np.array(df["arquivo"].values, dtype=object))
    log(f"{cfg['tag']}: features {X.shape} salvas")
    del model
    import torch
    torch.cuda.empty_cache()
    return X


def cv_config(X, y, groups, df):
    """Devolve oof (N,) e o C escolhido por AUC OOF."""
    gkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(gkf.split(np.arange(len(y)), y, groups))
    for k, (tr, va) in enumerate(folds):
        log(f"    fold {k}: treino {len(tr)} imgs ({int(y[tr].sum())} pos), "
            f"val {len(va)} imgs ({int(y[va].sum())} pos)")
        if len(np.unique(y[tr])) < 2:
            raise SystemExit(f"fold {k} sem as duas classes no treino")
    melhor = None
    for C in CS:
        oof = np.full(len(y), np.nan)
        for tr, va in folds:
            Xtr = X[tr].reshape(-1, X.shape[2])
            ytr = np.repeat(y[tr], N_TTA)
            sc = StandardScaler().fit(Xtr)
            clf = LogisticRegression(C=C, class_weight="balanced", max_iter=1500,
                                     solver="lbfgs")
            clf.fit(sc.transform(Xtr), ytr)
            Xva = X[va].reshape(-1, X.shape[2])
            p = clf.predict_proba(sc.transform(Xva))[:, 1]
            oof[va] = p.reshape(len(va), N_TTA).mean(1)
        auc_img = float(roc_auc_score(y, oof))
        auc_tal = auc_talhao(df, oof)
        log(f"    C={C:<5} AUC imagem={auc_img:.4f}  AUC talhao={auc_tal:.4f}")
        chave = (auc_tal if auc_tal == auc_tal else -1.0, auc_img)
        if melhor is None or chave > melhor[0]:
            melhor = (chave, C, auc_img, auc_tal, oof)
    return melhor


def avaliar_talhao(df, oof, limiar):
    """Regra do talhao: maioria das datas de CENTRO; empate = positivo."""
    m = (df["grupo"] == "ensino") & (df["tipo"] == "centro")
    sub = df[m].copy()
    sub["prob"] = oof[m.values]
    linhas = []
    for (tal, rot), g in sub.groupby(["talhao", "rotulo"]):
        n = len(g)
        positivas = int((g["prob"].values >= limiar).sum())
        decisao = int(2 * positivas >= n)
        linhas.append(dict(talhao=tal, rotulo=int(rot), n_datas=n,
                           n_positivas=positivas, prob_media=float(g["prob"].mean()),
                           prob_max=float(g["prob"].max()), decisao=decisao))
    t = pd.DataFrame(linhas)
    tp = int(((t.rotulo == 1) & (t.decisao == 1)).sum())
    fn = int(((t.rotulo == 1) & (t.decisao == 0)).sum())
    tn = int(((t.rotulo == 0) & (t.decisao == 0)).sum())
    fp = int(((t.rotulo == 0) & (t.decisao == 1)).sum())
    sens = tp / max(tp + fn, 1)
    spec = tn / max(tn + fp, 1)
    return dict(tp=tp, fn=fn, tn=tn, fp=fp, sens=float(sens), spec=float(spec),
                bal=float((sens + spec) / 2), n_pos=tp + fn, n_neg=tn + fp), t


def auc_talhao(df, oof):
    """AUC no nivel do talhao, usando a media das datas de centro."""
    m = (df["grupo"] == "ensino") & (df["tipo"] == "centro")
    sub = df[m].copy()
    sub["prob"] = oof[m.values]
    g = sub.groupby(["talhao", "rotulo"]).agg(prob=("prob", "mean")).reset_index()
    if g["rotulo"].nunique() < 2:
        return float("nan")
    return float(roc_auc_score(g["rotulo"], g["prob"]))


def escolher_limiar(df, oof):
    melhor = None
    curva = []
    for limiar in np.round(np.arange(0.02, 0.99, 0.01), 2):
        met, _ = avaliar_talhao(df, oof, float(limiar))
        curva.append(dict(limiar=float(limiar), **met))
        chave = (met["bal"], met["sens"], -abs(float(limiar) - 0.5))
        if melhor is None or chave > melhor[0]:
            melhor = (chave, float(limiar), met)
    return melhor[1], melhor[2], pd.DataFrame(curva)


def main():
    os.makedirs(SAIDA, exist_ok=True)
    df = carregar_dados()
    y = df["rotulo"].values.astype(int)
    groups = df["grupo_cv"].values
    log(f"{len(df)} imagens, {y.sum()} positivas, {df.talhao[df.grupo=='ensino'].nunique()} talhoes de ensino")
    log(f"grupos de CV: {len(set(groups))}")

    resultados = {}
    oofs = {}
    for cfg in CONFIGS:
        try:
            X = extrair_tag(df, cfg)
        except Exception as e:
            log(f"{cfg['tag']}: FALHOU ({type(e).__name__}: {e})")
            resultados[cfg["tag"]] = dict(erro=str(e)[:300])
            continue
        log(f"{cfg['tag']}: CV 5-fold estratificado por bloco")
        chave, C, auc_img, auc_tal, oof = cv_config(X, y, groups, df)
        met, tab = avaliar_talhao(df, oof, 0.5)
        resultados[cfg["tag"]] = dict(base=cfg["base"], size=cfg["size"],
                                      C=C, auc_oof=auc_img, auc_talhao=auc_tal,
                                      bal_05=met["bal"], sens_05=met["sens"],
                                      spec_05=met["spec"])
        oofs[cfg["tag"]] = oof
        log(f"{cfg['tag']}: AUC imagem={auc_img:.4f} AUC talhao={auc_tal:.4f} "
            f"C={C}  bal@0.5={met['bal']:.3f} "
            f"(sens {met['sens']:.2f}, spec {met['spec']:.2f})")

    validos = {k: v for k, v in resultados.items() if "auc_oof" in v}
    if not validos:
        raise SystemExit("nenhum modelo treinou")
    tag = max(validos, key=lambda k: (validos[k]["auc_talhao"], validos[k]["auc_oof"]))
    cfg = next(c for c in CONFIGS if c["tag"] == tag)
    log(f"MELHOR: {tag} (AUC talhao {validos[tag]['auc_talhao']:.4f}, "
        f"AUC imagem {validos[tag]['auc_oof']:.4f})")

    oof = oofs[tag]
    limiar, met, curva = escolher_limiar(df, oof)
    log(f"limiar escolhido={limiar:.2f}  talhao bal={met['bal']:.3f} "
        f"sens={met['sens']:.3f} spec={met['spec']:.3f}")
    log(f"matriz OOF: TP={met['tp']} FN={met['fn']} TN={met['tn']} FP={met['fp']}")

    # refit em todo o ensino
    X = extrair_tag(df, cfg)
    Xtr = X.reshape(-1, X.shape[2])
    ytr = np.repeat(y, N_TTA)
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(C=validos[tag]["C"], class_weight="balanced",
                             max_iter=1500, solver="lbfgs")
    clf.fit(sc.transform(Xtr), ytr)

    np.savez(os.path.join(SAIDA, "cabeca.npz"),
             coef=clf.coef_.ravel().astype(np.float64),
             intercept=clf.intercept_.astype(np.float64),
             mean=sc.mean_.astype(np.float64),
             scale=sc.scale_.astype(np.float64))
    config = dict(base_model=cfg["base"], input_size=cfg["size"],
                  tag=tag, cabeca="regressao logistica L2", C=validos[tag]["C"],
                  tta=8, limiar=float(limiar),
                  regra_talhao="maioria das datas disponiveis; empate = positivo",
                  positivo="talhao com arvore/renque (rotulo do gpkg)",
                  n_imagens=int(len(df)), n_positivas=int(y.sum()),
                  n_talhoes_ensino=int(df.talhao[df.grupo == "ensino"].nunique()),
                  auc_oof=float(validos[tag]["auc_oof"]),
                  auc_talhao_oof=float(validos[tag]["auc_talhao"]),
                  oof_talhao={k: met[k] for k in ("tp", "tn", "fp", "fn", "sens", "spec", "bal")},
                  treinado_em=time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(os.path.join(SAIDA, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=1, default=float)

    with open(os.path.join(SAIDA, "cv_resultados.json"), "w", encoding="utf-8") as f:
        json.dump(dict(configs=resultados, escolhido=tag, limiar=limiar,
                       oof_talhao=met, curva_limiar=curva.to_dict("records")),
                  f, ensure_ascii=False, indent=1, default=float)
    out = df[["talhao", "grupo", "tipo", "bloco", "rotulo", "data", "arquivo"]].copy()
    out["prob_oof"] = oof
    out.to_csv(os.path.join(SAIDA, "ensino_oof.csv"), index=False)
    _, tab = avaliar_talhao(df, oof, limiar)
    tab.to_csv(os.path.join(SAIDA, "ensino_talhoes_oof.csv"), index=False)
    log("salvo modelo/cabeca.npz, config.json, cv_resultados.json")
    log("RESUMO " + json.dumps({k: v for k, v in config.items() if k != "oof_talhao"},
                               ensure_ascii=False))


if __name__ == "__main__":
    main()
