"""Mede o grupo `medicao` UMA vez com o modelo ja congelado em /content/modelo.

Entrada: /content/medicao/{recortes_medicao.csv,recortes/*.png}
Saida:   /content/resultado/{medicao_probabilidades.csv,medicao_talhoes.csv,medicao_resumo.json}

O CSV de medicao NAO tem rotulo/arvore: o script nao consegue (nem deve) usar
os rotulos na previsao. A juncao com o gabarito e feita depois, no PC.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/content")
from modelo_util import (N_TTA, aplicar_cabeca, carregar_base, carregar_cabeca,
                         carregar_config, extrair_lista, norma)

DADOS = "/content/medicao"
MODELO = "/content/modelo"
SAIDA = "/content/resultado"


def main():
    os.makedirs(SAIDA, exist_ok=True)
    cfg = carregar_config(MODELO)
    cab = carregar_cabeca(MODELO)
    df = pd.read_csv(os.path.join(DADOS, "recortes_medicao.csv"))
    df["arquivo"] = df["arquivo"].astype(str)
    df["caminho"] = [os.path.join(DADOS, "recortes", a) for a in df["arquivo"]]
    falta = [p for p in df["caminho"] if not os.path.exists(p)]
    if falta:
        raise SystemExit(f"faltam {len(falta)} imagens: {falta[:3]}")
    print(f"{len(df)} recortes de medicao; modelo {cfg['tag']} "
          f"(limiar {cfg['limiar']})", flush=True)

    model = carregar_base(cfg["base_model"], cfg["input_size"])
    mean, std = norma(model)
    X = extrair_lista(model, list(df["caminho"]), cfg["input_size"], mean, std,
                      batch=8, log=lambda m: print(m, flush=True))
    df["prob"] = aplicar_cabeca(X, cab)
    df.to_csv(os.path.join(SAIDA, "medicao_probabilidades.csv"), index=False)

    limiar = float(cfg["limiar"])
    linhas = []
    for tal, g in df.groupby("talhao"):
        n = len(g)
        positivas = int((g["prob"].values >= limiar).sum())
        linhas.append(dict(
            talhao=tal, cod=g["cod"].iloc[0], bloco=g["bloco"].iloc[0],
            n_datas=n, n_positivas=positivas,
            prob_media=float(g["prob"].mean()), prob_min=float(g["prob"].min()),
            prob_max=float(g["prob"].max()),
            datas="|".join(g["data"].astype(str)),
            probs="|".join(f"{p:.4f}" for p in g["prob"]),
            decisao=int(2 * positivas >= n)))
    tab = pd.DataFrame(linhas)
    tab.to_csv(os.path.join(SAIDA, "medicao_talhoes.csv"), index=False)
    resumo = dict(n_talhoes=int(len(tab)), n_recortes=int(len(df)),
                  n_datas_por_talhao=tab.n_datas.value_counts().to_dict(),
                  n_positivos=int(tab.decisao.sum()),
                  por_classe={str(k): dict(n=int(v["n"]), positivos=int(v["pos"]))
                              for k, v in tab.groupby("cod")
                              .agg(n=("talhao", "size"), pos=("decisao", "sum"))
                              .iterrows()},
                  limiar=limiar, modelo=cfg["tag"])
    with open(os.path.join(SAIDA, "medicao_resumo.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=1)
    print(json.dumps(resumo, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
