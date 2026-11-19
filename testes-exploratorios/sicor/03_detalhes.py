import csv, json, os
from collections import Counter, defaultdict
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = json.load(open(os.path.join(RAIZ, "saida", "resumo.json"), encoding="utf-8"))
CL = {"3": "ILP", "4": "SAF", "5": "ILPF", "6": "ILF", "7": "IPF"}

print("== GOIÁS (estado inteiro), glebas por classe")
for cl, v in r["goias"].items():
    print(f"  {cl}: {v['glebas']} glebas, {v['operacoes']} operações, {v['locais_distintos']} locais, {v['area_distinta_ha']} ha, mediana {v['area_mediana_ha']} ha; produtos {v['produtos']}; safras {v['por_safra']}")

print("== PILOTO: total", r["piloto_glebas_total"], "glebas; sem amostra atual:", r["piloto_glebas_sem_amostra_atual"])
print("   por tile:", {k: v for k, v in r["piloto_por_tile"].items() if v})

print("== COBERTURA de gleba (operações com código de integração: total, com gleba)")
ag = defaultdict(lambda: [0, 0])
for k, (t, g) in r["cobertura"].items():
    esc, ano, cl = k.split("|")
    per = "2013-2018" if int(ano) <= 2018 else ("2019-2022" if int(ano) <= 2022 else "2023-2026")
    ag[(esc, per, cl)][0] += t
    ag[(esc, per, cl)][1] += g
for k in sorted(ag):
    print("  ", k, ag[k])

print("== AMOSTRAS:", {k: v for k, v in r["amostras"].items() if k != "exemplos"})
for e in r["amostras"]["exemplos"]:
    print("  ", e)

# concentração nacional
csv.field_size_limit(1 << 30)
ops = {}
with open(os.path.join(RAIZ, "dados", "ops_integracao.csv"), encoding="utf-8", newline="") as f:
    for o in csv.DictReader(f, delimiter=";"):
        ops[(o["REF_BACEN"], o["NU_ORDEM"])] = o
com = set()
ngl = Counter()
with open(os.path.join(RAIZ, "dados", "glebas_integracao.csv"), encoding="utf-8", newline="") as f:
    for g in csv.DictReader(f, delimiter=";"):
        k = (g["REF_BACEN"], g["NU_ORDEM"])
        com.add(k)
        ngl[k] += 1
uf = defaultdict(Counter)
ano = defaultdict(Counter)
banco = defaultdict(Counter)
for k in com:
    o = ops[k]
    cl = CL.get(o["CD_TIPO_INTGR_CONSOR"].strip(), "só subprograma")
    uf[cl][o["CD_ESTADO"]] += ngl[k]
    ano[cl][o["ANO_ARQUIVO"]] += ngl[k]
    banco[cl][o["CNPJ_IF"]] += ngl[k]
print("== BRASIL: glebas por classe, UF (10 maiores), ano e banco (3 maiores, só a parcela)")
for cl in uf:
    tot = sum(uf[cl].values())
    print(f"  {cl}: {tot} glebas")
    print("     UF:", uf[cl].most_common(10))
    print("     ano:", sorted(ano[cl].items()))
    print("     parcela dos 3 maiores bancos:", [round(100 * n / tot) for _, n in banco[cl].most_common(3)], "%")
