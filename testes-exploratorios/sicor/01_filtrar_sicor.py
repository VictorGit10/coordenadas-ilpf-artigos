"""Lê o SICOR (Banco Central) direto da internet, sem guardar os arquivos brutos,
e guarda só o que interessa:
  - dados/ops_integracao.csv   operações de crédito rural marcadas como integração
                               (ILP, SAF, ILPF, ILF, IPF) ou em subprograma de integração, Brasil todo
  - dados/glebas_integracao.csv polígonos (WKT) dessas operações
  - dados/resumo_ops.json      contagens por ano, UF e código, para conferência
Uso: python 01_filtrar_sicor.py [ops|glebas|tudo]
"""
import csv, gzip, io, json, os, re, sys, time, urllib.request
from collections import Counter, defaultdict

BASE = "https://www.bcb.gov.br/htms/sicor/DadosBrutos"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
DOM = os.path.join(RAIZ, "dominio")
os.makedirs(DADOS, exist_ok=True)
ANOS = list(range(2013, 2027))
COD_INTEGRACAO = {"3", "4", "5", "6", "7"}  # ILP, SAF, ILPF, ILF, IPF
csv.field_size_limit(1 << 30)


def subprogramas_integracao():
    cods = {}
    with open(os.path.join(DOM, "Subprogramas.csv"), encoding="latin-1") as f:
        for i, linha in enumerate(f):
            if i == 0:
                continue
            p = linha.rstrip("\n").split(";")
            if len(p) < 4:
                continue
            desc = p[1]
            if re.search(r"integra[çc][ãa]o|integ lav|agroflorest", desc, re.I):
                cods[(p[3].strip(), p[0].strip())] = desc  # (programa, subprograma)
    return cods


def abrir(url, tentativas=4):
    for t in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            r = urllib.request.urlopen(req, timeout=120)
            return io.TextIOWrapper(gzip.GzipFile(fileobj=r), encoding="latin-1", newline="")
        except Exception as e:  # noqa
            print(f"  falha ao abrir ({e}); tentativa {t+1}", flush=True)
            time.sleep(10 * (t + 1))
    raise RuntimeError("não abriu " + url)


def fase_ops():
    subs = subprogramas_integracao()
    print("subprogramas de integração:", subs, flush=True)
    resumo = {"por_ano": {}, "subprogramas": {f"{k[0]}/{k[1]}": v for k, v in subs.items()}}
    saida = os.path.join(DADOS, "ops_integracao.csv")
    cab_escrito = False
    with open(saida, "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo, delimiter=";")
        for ano in ANOS:
            t0 = time.time()
            url = f"{BASE}/SICOR_OPERACAO_BASICA_ESTADO_{ano}.gz"
            for tent in range(3):
                try:
                    f = abrir(url)
                    rd = csv.reader(f, delimiter=";")
                    cab = next(rd)
                    cab[0] = cab[0].lstrip("#")
                    ix = {c: i for i, c in enumerate(cab)}
                    iI, iUF, iP, iS = ix["CD_TIPO_INTGR_CONSOR"], ix["CD_ESTADO"], ix["CD_PROGRAMA"], ix["CD_SUBPROGRAMA"]
                    total = 0
                    cod_br = Counter()
                    cod_go = Counter()
                    sub_go = Counter()
                    linhas = []
                    for row in rd:
                        if len(row) <= iS:
                            continue
                        total += 1
                        cod = row[iI].strip()
                        uf = row[iUF]
                        cod_br[cod] += 1
                        chave_sub = (row[iP].strip(), row[iS].strip())
                        por_sub = chave_sub in subs
                        if uf == "GO":
                            cod_go[cod] += 1
                            if por_sub:
                                sub_go["/".join(chave_sub)] += 1
                        if cod in COD_INTEGRACAO or por_sub:
                            linhas.append([ano, "1" if por_sub else "0"] + row)
                    break
                except Exception as e:  # noqa
                    print(f"  {ano}: erro no meio ({e}); recomeçando o ano", flush=True)
                    time.sleep(20)
            else:
                raise RuntimeError(f"ano {ano} falhou 3 vezes")
            if not cab_escrito:
                w.writerow(["ANO_ARQUIVO", "SUBPROG_INTEGRACAO"] + cab)
                cab_escrito = True
                resumo["colunas"] = cab
            elif cab != resumo["colunas"]:
                # colunas mudaram entre anos: reordena para o primeiro cabeçalho
                pos = {c: i for i, c in enumerate(cab)}
                linhas = [l[:2] + [l[2 + pos[c]] if c in pos and 2 + pos[c] < len(l) else "" for c in resumo["colunas"]] for l in linhas]
            w.writerows(linhas)
            fo.flush()
            resumo["por_ano"][ano] = {"total_br": total, "cod_br": dict(cod_br), "cod_go": dict(cod_go),
                                      "sub_go": dict(sub_go), "guardadas": len(linhas)}
            print(f"{ano}: {total:,} operações; guardadas {len(linhas):,}; GO por código {dict(cod_go)}; {time.time()-t0:.0f}s", flush=True)
            json.dump(resumo, open(os.path.join(DADOS, "resumo_ops.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fase_glebas():
    chaves = set()
    with open(os.path.join(DADOS, "ops_integracao.csv"), encoding="utf-8") as f:
        rd = csv.reader(f, delimiter=";")
        cab = next(rd)
        iR, iN = cab.index("REF_BACEN"), cab.index("NU_ORDEM")
        for row in rd:
            chaves.add((row[iR], row[iN]))
    print(f"{len(chaves):,} operações de interesse", flush=True)
    saida = os.path.join(DADOS, "glebas_integracao.csv")
    resumo = {}
    with open(saida, "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo, delimiter=";")
        w.writerow(["ANO_ARQUIVO", "REF_BACEN", "NU_ORDEM", "NU_INDICE", "GT_GEOMETRIA"])
        for ano in ANOS:
            t0 = time.time()
            url = f"{BASE}/sicor_glebas_wkt_{ano}.gz"
            for tent in range(3):
                try:
                    f = abrir(url)
                    rd = csv.reader(f, delimiter=";")
                    next(rd)
                    total = 0
                    achadas = []
                    for row in rd:
                        if len(row) < 4:
                            continue
                        total += 1
                        if (row[0], row[1]) in chaves:
                            achadas.append([ano] + row[:4])
                    break
                except Exception as e:  # noqa
                    print(f"  {ano}: erro no meio ({e}); recomeçando o ano", flush=True)
                    time.sleep(20)
            else:
                raise RuntimeError(f"glebas {ano} falhou 3 vezes")
            w.writerows(achadas)
            fo.flush()
            resumo[ano] = {"glebas_total": total, "glebas_guardadas": len(achadas)}
            print(f"glebas {ano}: {total:,} no arquivo; guardadas {len(achadas):,}; {time.time()-t0:.0f}s", flush=True)
            json.dump(resumo, open(os.path.join(DADOS, "resumo_glebas.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if modo in ("ops", "tudo"):
        fase_ops()
    if modo in ("glebas", "tudo"):
        fase_glebas()
    print("FIM", flush=True)
