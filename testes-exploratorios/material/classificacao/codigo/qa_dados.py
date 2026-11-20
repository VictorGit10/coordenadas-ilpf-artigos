"""Conferencia dos recortes baixados: contagens, datas, tamanhos, arquivos."""
import glob
import os
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

from comum import BASE, DADOS, RECORTES, ler_csv

for csv_nome in ["recortes_ensino.csv", "recortes_negativos.csv", "recortes_medicao.csv"]:
    p = os.path.join(DADOS, csv_nome)
    if not os.path.exists(p):
        continue
    rows = ler_csv(p)
    print(f"\n== {csv_nome}: {len(rows)} linhas")
    if not rows:
        continue
    print("  grupos:", Counter(r["grupo"] for r in rows))
    print("  tipos:", Counter(r["tipo"] for r in rows))
    print("  rotulos:", Counter(r["rotulo"] for r in rows))
    print("  anos:", Counter(r["ano"] for r in rows))
    por_tal = defaultdict(set)
    for r in rows:
        por_tal[r["talhao"]].add(r["data"])
    print("  talhoes:", len(por_tal), "datas/talhao:",
          Counter(len(v) for v in por_tal.values()))
    faltam = [r["arquivo"] for r in rows
              if not os.path.exists(os.path.join(RECORTES, r["arquivo"]))]
    print("  arquivos faltando:", len(faltam))
    tamanhos = Counter()
    for r in rows[:]:
        fp = os.path.join(RECORTES, r["arquivo"])
        if not os.path.exists(fp):
            continue
        im = Image.open(fp)
        tamanhos[(im.size, im.mode)] += 1
    print("  tamanhos:", dict(tamanhos))

fs = glob.glob(os.path.join(RECORTES, "*.png"))
print(f"\ntotal de PNGs na pasta: {len(fs)}")
tam = sum(os.path.getsize(f) for f in fs) / 1e6
print(f"tamanho total: {tam:.1f} MB")
