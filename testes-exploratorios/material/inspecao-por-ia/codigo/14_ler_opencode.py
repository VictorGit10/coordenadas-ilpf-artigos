"""Mesma leitura de fichas do 04_ler.py, mas pelo opencode (DeepSeek no Ollama Cloud), para comparar com o Gemini.
Uso: python 14_ler_opencode.py <rodada> --grupos conhecida [--ids F1,F2] [--pedido PEDIDO2.md] [--paralelo 4] [--lote 4]
"""
import json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEIT = os.path.join(RAIZ, "leitura")
OC = shutil.which("opencode")
arg = lambda n, p: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else p
rodada = sys.argv[1]
grupos = arg("--grupos", "conhecida").split(",")
modelo = arg("--modelo", "ollama/deepseek-v4.1-flash:cloud#max")
paralelo, tam, arq_pedido = int(arg("--paralelo", "4")), int(arg("--lote", "4")), arg("--pedido", "PEDIDO2.md")
so_ids = [x for x in arg("--ids", "").split(",") if x]
pasta = os.path.join(LEIT, rodada)
os.makedirs(pasta, exist_ok=True)
alvos = [a for a in json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8")) if a["grupo"] in grupos]
if so_ids:
    alvos = [a for a in alvos if a["id"] in so_ids]
ids = [a["id"] for a in alvos if os.path.exists(os.path.join(RAIZ, "fichas", a["id"] + ".png"))]
lotes = [ids[i:i + tam] for i in range(0, len(ids), tam)]
print(f"{len(ids)} fichas em {len(lotes)} lotes; modelo {modelo}; {paralelo} em paralelo", flush=True)


def texto(bruto):
    t, tok, ferr = "", 0, 0
    for linha in bruto.splitlines():
        try:
            ev = json.loads(linha)
        except Exception:  # noqa
            continue
        if ev.get("type") == "text":
            t += ev.get("part", {}).get("text", "")
        if ev.get("type") == "tool_use":
            ferr += 1
        tk = (ev.get("part") or {}).get("tokens") or {}
        tok += (tk.get("input") or 0) + (tk.get("output") or 0) + (tk.get("reasoning") or 0)
    return t, tok, ferr


def extrair(bruto, esperados):
    t, tok, ferr = texto(bruto)
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j < 0:
        return None, tok, ferr
    try:
        lst = json.loads(t[i:j + 1])
    except Exception:  # noqa
        return None, tok, ferr
    por = {x.get("id"): x for x in lst if isinstance(x, dict)}
    return (por if all(e in por for e in esperados) else None), tok, ferr


def rodar(n_lote):
    n, lote = n_lote
    d = os.path.join(pasta, f"L{n:03d}")
    arq = os.path.join(d, "saida.jsonl")
    if os.path.exists(arq):
        r, tok, ferr = extrair(open(arq, encoding="utf-8", errors="replace").read(), lote)
        if r:
            return n, r, 0, "já feito"
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(LEIT, arq_pedido), os.path.join(d, "PEDIDO.md"))
    for fid in lote:
        shutil.copy(os.path.join(RAIZ, "fichas", fid + ".png"), d)
    pedido = (f"Leia {os.path.join(d, 'PEDIDO.md')} e siga as instruções. As fichas estão na pasta {d}. Fichas a ler, nesta ordem: " + ", ".join(f + ".png" for f in lote) +
              ". Abra cada imagem com a ferramenta de leitura de arquivos e olhe a imagem antes de responder. Não escreva nem altere arquivos.")
    motivo = ""
    for tent in range(2):
        t0 = time.time()
        try:
            p = subprocess.run([OC, "run", "--standalone", "--format", "json", "-m", modelo, pedido], cwd=d, stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=900)
            bruto = p.stdout.decode("utf-8", "replace")
            open(arq, "w", encoding="utf-8").write(bruto)
            r, tok, ferr = extrair(bruto, lote)
            if r:
                return n, r, time.time() - t0, f"ok ({tok} tokens, {ferr} ferramentas)"
            motivo = "resposta incompleta"
        except subprocess.TimeoutExpired:
            motivo = "tempo esgotado"
        except Exception as e:  # noqa
            motivo = f"{type(e).__name__}: {str(e)[:100]}"
        print(f"ERRO lote {n} tentativa {tent+1}: {motivo}", flush=True)
    return n, None, time.time() - t0, "FALHOU"


todas = {}
t0 = time.time()
with ThreadPoolExecutor(paralelo) as ex:
    for n, r, dt, st in ex.map(rodar, list(enumerate(lotes, 1))):
        if r:
            todas.update(r)
        print(f"lote {n}/{len(lotes)} {st} {dt:.0f}s | total {time.time()-t0:.0f}s", flush=True)
        json.dump(todas, open(os.path.join(pasta, "leituras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"FIM: {len(todas)} de {len(ids)} fichas lidas em {time.time()-t0:.0f}s", flush=True)
