"""Manda as fichas ao Gemini (agy) em lotes pequenos, vários em paralelo, e junta as respostas em leituras.json.
Uso: python 04_ler.py <rodada> [--grupos conhecida,sicor] [--modelo gemini-3.8-flash-medium] [--paralelo 5] [--lote 4]
Retomável: lote com resposta válida não é refeito.
"""
import json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEIT = os.path.join(RAIZ, "leitura")
AGY = shutil.which("agy")


def arg(nome, padrao):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


rodada = sys.argv[1]
grupos = arg("--grupos", "conhecida,sicor").split(",")
modelo = arg("--modelo", "gemini-3.8-flash-medium")
paralelo = int(arg("--paralelo", "5"))
tam = int(arg("--lote", "4"))
pasta = os.path.join(LEIT, rodada)
os.makedirs(pasta, exist_ok=True)
alvos = [a for a in json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8")) if a["grupo"] in grupos]
ids = [a["id"] for a in alvos if os.path.exists(os.path.join(RAIZ, "fichas", a["id"] + ".png"))]
lotes = [ids[i:i + tam] for i in range(0, len(ids), tam)]
print(f"{len(ids)} fichas em {len(lotes)} lotes; modelo {modelo}; {paralelo} em paralelo", flush=True)


def extrair(texto, esperados):
    i, j = texto.find("["), texto.rfind("]")
    if i < 0 or j < 0:
        return None
    try:
        lst = json.loads(texto[i:j + 1])
    except Exception:  # noqa
        return None
    por_id = {x.get("id"): x for x in lst if isinstance(x, dict)}
    return por_id if all(e in por_id for e in esperados) else None


def rodar(n_lote):
    n, lote = n_lote
    d = os.path.join(pasta, f"L{n:03d}")
    arq = os.path.join(d, "saida.json")
    if os.path.exists(arq):
        try:
            r = extrair(json.load(open(arq, encoding="utf-8")).get("response", ""), lote)
            if r:
                return n, r, 0, "já feito"
        except Exception:  # noqa
            pass
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(LEIT, "PEDIDO.md"), d)
    for fid in lote:
        shutil.copy(os.path.join(RAIZ, "fichas", fid + ".png"), d)
    pedido = ("Leia PEDIDO.md e siga as instruções. Fichas a ler, nesta ordem: " + ", ".join(f + ".png" for f in lote) +
              ". Abra cada imagem antes de responder.")
    for tent in range(2):
        t0 = time.time()
        try:
            p = subprocess.run([AGY, "-p", pedido, "--model", modelo, "--output-format", "json", "--print-timeout", "580s"],
                               cwd=d, stdin=subprocess.DEVNULL, capture_output=True, timeout=640)
            saida = p.stdout.decode("utf-8", "replace")
            open(arq, "w", encoding="utf-8").write(saida)
            dj = json.loads(saida)
            r = extrair(dj.get("response", ""), lote)
            if r:
                return n, r, time.time() - t0, f"ok ({dj.get('usage', {}).get('total_tokens')} tokens)"
            motivo = f"resposta sem todas as fichas (status {dj.get('status')})"
        except subprocess.TimeoutExpired:
            motivo = "tempo esgotado"
        except Exception as e:  # noqa
            motivo = f"{type(e).__name__}: {str(e)[:100]}"
        print(f"ERRO lote {n} tentativa {tent+1}: {motivo}", flush=True)
    return n, None, time.time() - t0, "FALHOU"


todas = {}
t0 = time.time()
with ThreadPoolExecutor(paralelo) as ex:
    feitos = 0
    for n, r, dt, st in ex.map(rodar, list(enumerate(lotes, 1))):
        feitos += 1
        if r:
            todas.update(r)
        print(f"lote {n}/{len(lotes)} {st} {dt:.0f}s | total {time.time()-t0:.0f}s", flush=True)
        json.dump(todas, open(os.path.join(pasta, "leituras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"FIM: {len(todas)} de {len(ids)} fichas lidas em {time.time()-t0:.0f}s", flush=True)
