"""Mantem em recortes_negativos.csv so os negativos que passaram no filtro
de sistema com arvore; apaga as imagens dos pontos descartados."""
import os

import pandas as pd

from comum import DADOS, RECORTES

sel = pd.read_csv(os.path.join(DADOS, "negativos_selecionados.csv"))
sel = set(sel["ficha"].astype(str))
p = os.path.join(DADOS, "recortes_negativos.csv")
d = pd.read_csv(p, dtype={"talhao": str})
keep = d[d["talhao"].isin(sel)].copy()
keep.to_csv(p, index=False, encoding="utf-8")
for a in set(d["arquivo"]) - set(keep["arquivo"]):
    fp = os.path.join(RECORTES, a)
    if os.path.exists(fp):
        os.remove(fp)
print(f"negativos: {d.talhao.nunique()} -> {keep.talhao.nunique()} pontos; "
      f"{len(d)} -> {len(keep)} recortes")
