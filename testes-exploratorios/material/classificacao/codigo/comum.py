"""Utilitarios comuns do classificador de renques (caminhos, QA, CSV)."""
import csv
import os
import sys
import threading

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.environ.get("ILPF_SCRIPTS", BASE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

GPKG = os.path.join(BASE, "talhoes_divididos.gpkg")
RECORTES = os.path.join(BASE, "recortes")
DADOS = os.path.join(BASE, "dados")
MODELO = os.path.join(BASE, "modelo")

COLS = ["talhao", "grupo", "rotulo", "data", "arquivo", "cena", "href",
        "lon", "lat", "cod", "bloco", "tipo", "idx", "categoria", "ano"]

_trava = threading.Lock()


def garantir_pastas():
    for p in (RECORTES, DADOS, MODELO):
        os.makedirs(p, exist_ok=True)


def qa_img(img):
    """Controle de qualidade minimo de um recorte ja realcado."""
    if img is None:
        return False
    if img.ndim != 3 or img.shape[2] < 3:
        return False
    if img.shape[0] < 120 or img.shape[1] < 120:
        return False
    if img.dtype != np.uint8:
        return False
    preto = float((img[..., :3].sum(axis=2) == 0).mean())
    if preto > 0.05:
        return False
    branco = float((img[..., :3].min(axis=2) > 235).mean())
    if branco > 0.30:
        return False
    if float(img[..., :3].std()) < 4.0:
        return False
    return True


def abrir_csv(caminho):
    """Abre CSV em modo append e devolve (arquivo, writer, ja_existe)."""
    novo = not os.path.exists(caminho) or os.path.getsize(caminho) == 0
    f = open(caminho, "a", newline="", encoding="utf-8", buffering=1)
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    if novo:
        w.writeheader()
    return f, w, novo


def escrever_linhas(writer, linhas):
    if not linhas:
        return
    with _trava:
        for ln in linhas:
            writer.writerow({k: ln.get(k, "") for k in COLS})


def ler_csv(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def nome_arquivo(talhao, tipo, idx, data, categoria=""):
    if tipo == "negativo":
        base = f"n{talhao}_{categoria}_{data}"
    else:
        suf = f"_{tipo}" if tipo == "centro" else f"_{tipo}{idx}"
        base = f"t{talhao:03d}{suf}_{data}"
    return base + ".png"
