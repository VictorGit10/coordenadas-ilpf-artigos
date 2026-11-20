"""Junta a previsao de medicao com o gabarito do gpkg e resume os numeros."""
import json
import os

import geopandas as gpd
import pandas as pd

from comum import BASE, GPKG

CLASSES = {1: "Pastagem", 2: "Agricultura", 3: "ILPF", 4: "ILP",
           5: "IPF", 6: "SAF", 7: "ILF", 8: "Outros", 9: "Silvicultura"}


def main():
    res = pd.read_csv(os.path.join(BASE, "resultado", "medicao_talhoes.csv"))
    res["talhao"] = res["talhao"].astype(int)
    res = res.drop(columns=[c for c in ("cod", "bloco") if c in res.columns])
    g = gpd.read_file(GPKG)
    g["talhao"] = g["talhao"].astype(int)
    base = g[g.grupo == "medicao"][
        ["talhao", "cod", "arvore", "nos_tiles", "detector_marcou", "bloco"]].copy()
    tab = base.merge(res, on="talhao", how="left")
    tab["n_datas"] = tab["n_datas"].fillna(0).astype(int)
    tab["n_positivas"] = tab["n_positivas"].fillna(0).astype(int)
    tab["decisao"] = tab["decisao"].fillna(-1).astype(int)
    tab["pred"] = tab["decisao"] == 1
    tab["classe"] = tab["cod"].map(CLASSES)

    def bloco(mask):
        s = tab[mask]
        return dict(n=int(len(s)), positivos=int(s.pred.sum()),
                    talhoes=s.talhao.astype(int).tolist())

    out = {}
    out["arvore_nos_tiles"] = bloco(tab.arvore & tab.nos_tiles)
    out["arvore_todos"] = bloco(tab.arvore)
    out["sem_arvore"] = bloco(~tab.arvore)
    out["sem_arvore_por_classe"] = {
        CLASSES[int(k)]: dict(n=int(len(v)), falsos=int(v.pred.sum()),
                              talhoes=v.talhao.astype(int).tolist())
        for k, v in tab[~tab.arvore].groupby("cod")}
    out["sem_dados"] = tab[tab.n_datas == 0].talhao.astype(int).tolist()
    out["detector_marcou_8"] = int(
        tab[tab.arvore & tab.nos_tiles].detector_marcou.sum())
    out["detector_marcou_todos"] = int(tab[tab.arvore].detector_marcou.sum())

    print("8 com arvore e nos tiles:", out["arvore_nos_tiles"])
    print("todos com arvore:", out["arvore_todos"])
    print("sem arvore:", out["sem_arvore"])
    print("sem arvore por classe:", json.dumps(out["sem_arvore_por_classe"],
                                               ensure_ascii=False))
    print("sem dados:", out["sem_dados"])

    cols = ["talhao", "cod", "classe", "arvore", "nos_tiles", "n_datas",
            "n_positivas", "prob_media", "prob_max", "datas", "probs", "decisao"]
    tab[cols].sort_values("talhao").to_csv(
        os.path.join(BASE, "resultado", "medicao_tabela.csv"), index=False)
    with open(os.path.join(BASE, "resultado", "medicao_avaliacao.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # tabela markdown
    print("\n| talhao | cod | arvore | nos_tiles | datas | probs | decisao |")
    print("|---|---|---|---|---|---|---|")
    for _, r in tab.sort_values("talhao").iterrows():
        print(f"| {r.talhao} | {r.cod} {r.classe} | {int(bool(r.arvore))} | "
              f"{int(bool(r.nos_tiles))} | {r.n_datas} | {r.probs} | {r.decisao} |")


if __name__ == "__main__":
    main()
