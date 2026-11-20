"""Empacota os recortes para envio ao Colab (somente os arquivos usados)."""
import argparse
import os
import zipfile

from comum import BASE, DADOS, RECORTES, ler_csv


def empacotar(nome_zip, csvs, csv_dir=DADOS):
    destino = os.path.join(BASE, nome_zip)
    linhas = []
    for c in csvs:
        linhas += ler_csv(os.path.join(csv_dir, c))
    faltam = [r["arquivo"] for r in linhas
              if not os.path.exists(os.path.join(RECORTES, r["arquivo"]))]
    if faltam:
        raise SystemExit(f"{len(faltam)} imagens faltando; ex.: {faltam[:5]}")
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_STORED) as z:
        for c in csvs:
            z.write(os.path.join(csv_dir, c), arcname=os.path.basename(c))
        vistos = set()
        for r in linhas:
            a = r["arquivo"]
            if a in vistos:
                continue
            vistos.add(a)
            z.write(os.path.join(RECORTES, a), arcname=os.path.join("recortes", a))
    print(f"{nome_zip}: {len(linhas)} linhas, {len(vistos)} imagens, "
          f"{os.path.getsize(destino)/1e6:.1f} MB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("conjunto", choices=["ensino", "medicao", "todos"])
    a = ap.parse_args()
    if a.conjunto in ("ensino", "todos"):
        empacotar("dados_ensino.zip", ["recortes_ensino.csv", "recortes_negativos.csv"])
    if a.conjunto in ("medicao", "todos"):
        empacotar("dados_medicao.zip", ["recortes_medicao.csv"])
