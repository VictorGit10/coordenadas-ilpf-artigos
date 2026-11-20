# -*- coding: utf-8 -*-
"""Confere o resultados.csv contra as divisoes recalculadas e imprime o resumo
que alimenta o RELATORIO.md. Nao apaga nada e nao escreve fora desta pasta."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import separacao_rodar as R

BASE = Path(__file__).resolve().parent


def main():
    X, y, meta = R.carregar_dados(BASE)
    df = pd.read_csv(BASE / "resultados.csv")
    problemas = []

    if df.duplicated(["caso", "semente"]).any():
        problemas.append("ha (caso, semente) duplicado")
    for caso in "ABCD":
        s = sorted(df.loc[df.caso == caso, "semente"].tolist())
        if s != R.SEMENTES_PADRAO:
            problemas.append(f"caso {caso}: sementes {s}")

    linhas_verif = []
    for _, r in df.iterrows():
        caso, seed = r["caso"], int(r["semente"])
        div = R.dividir(caso, y, meta, seed)
        partes = {k: len(div[k]) for k in ("pre", "treino", "val", "teste")}
        soma = sum(partes.values())
        if soma != len(y):
            problemas.append(f"{caso} {seed}: soma {soma}")
        for campo, chave in [("n_linhas_pretreino", "pre"),
                             ("n_linhas_treino", "treino"),
                             ("n_linhas_validacao", "val"),
                             ("n_linhas_teste", "teste")]:
            if int(r[campo]) != partes[chave]:
                problemas.append(f"{caso} {seed}: {campo} {r[campo]} != {partes[chave]}")

        lugares = meta["grupo_id"].to_numpy()
        blocos = meta["bloco"].to_numpy()
        cj = {k: set(lugares[div[k]]) for k in ("pre", "treino", "val", "teste")}
        cb = {k: set(blocos[div[k]]) for k in ("pre", "treino", "val", "teste")}
        inter_g = sum(len(cj[a] & cj[b]) for i, a in enumerate(cj) for b in list(cj)[i + 1:])
        inter_b = sum(len(cb[a] & cb[b]) for i, a in enumerate(cb) for b in list(cb)[i + 1:])
        if caso in ("C", "D") and inter_g:
            problemas.append(f"{caso} {seed}: grupos compartilhados ({inter_g})")
        if caso == "D" and inter_b:
            problemas.append(f"D {seed}: blocos compartilhados ({inter_b})")
        if int(r["teste_lugares_no_treino"]) != len(cj["teste"] & cj["treino"]):
            problemas.append(f"{caso} {seed}: teste_lugares_no_treino diverge")
        if int(r["teste_lugares_no_pretreino"]) != len(cj["teste"] & cj["pre"]):
            problemas.append(f"{caso} {seed}: teste_lugares_no_pretreino diverge")

        linhas_verif.append({
            "caso": caso, "semente": seed, "soma": soma,
            "n_pretreino": partes["pre"], "n_treino": partes["treino"],
            "n_val": partes["val"], "n_teste": partes["teste"],
            "intersecao_grupos_entre_lados": inter_g,
            "intersecao_blocos_entre_lados": inter_b,
        })

    pd.DataFrame(linhas_verif).to_csv(BASE / "verificacao.csv", index=False)

    if problemas:
        print("PROBLEMAS:")
        for p in problemas:
            print(" -", p)
        return 1

    print(f"OK: {len(df)} rodadas, {df.caso.nunique()} casos x {df.semente.nunique()} sementes; "
          f"soma=1607 em todas; C/D sem grupo compartilhado; D sem bloco compartilhado.")
    print()
    pd.set_option("display.width", 160)
    resumo = df.groupby("caso")[["acuracia", "f1_macro", "f1_macro_presentes", "tempo_s"]].agg(["mean", "std"])
    print(resumo.round(4).to_string())
    print()
    print("Linhas por lado (min-max):")
    for caso in "ABCD":
        d = df[df.caso == caso]
        print(f"  {caso}: pre {d.n_linhas_pretreino.min()}-{d.n_linhas_pretreino.max()}, "
              f"treino {d.n_linhas_treino.min()}-{d.n_linhas_treino.max()}, "
              f"val {d.n_linhas_validacao.min()}-{d.n_linhas_validacao.max()}, "
              f"teste {d.n_linhas_teste.min()}-{d.n_linhas_teste.max()}, "
              f"lugares teste {d.n_lugares_teste.min()}-{d.n_lugares_teste.max()}")
    print()
    print("Classes ausentes do teste (contagem de sementes):")
    for caso in "ABCD":
        aus = df[df.caso == caso]["classes_ausentes_teste"].fillna("")
        cont = {}
        for valor in aus:
            for nome in [x for x in str(valor).split(";") if x]:
                cont[nome] = cont.get(nome, 0) + 1
        print(f"  {caso}: {cont if cont else 'nenhuma'}")
    print()
    print("F1 por classe (media +- desvio), com suporte medio no teste:")
    for caso in "ABCD":
        d = df[df.caso == caso]
        texto = []
        for c in R.CLASSES:
            texto.append(f"{c}:{d[f'f1_classe_{c}'].mean():.3f}+-{d[f'f1_classe_{c}'].std():.3f}"
                         f"(n~{d[f'suporte_classe_{c}'].mean():.1f})")
        print(f"  {caso}: " + " ".join(texto))
    print()
    print("Diferenca pareada por semente:")
    for metrica in ["acuracia", "f1_macro", "f1_macro_presentes"]:
        for outro in "BCD":
            a = df[df.caso == "A"].set_index("semente")[metrica]
            b = df[df.caso == outro].set_index("semente")[metrica]
            dif = (a - b).dropna()
            n = len(dif)
            media = dif.mean()
            erro = dif.std(ddof=1) / np.sqrt(n)
            t = 2.262  # t(0.975, 9)
            print(f"  A-{outro} {metrica}: media {media:+.4f} IC95 [{media - t * erro:+.4f}, "
                  f"{media + t * erro:+.4f}] (n={n})")
    print()
    print(f"Tempo total de treino: {df.tempo_s.sum() / 60:.1f} min; "
          f"media por rodada {df.tempo_s.mean():.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
