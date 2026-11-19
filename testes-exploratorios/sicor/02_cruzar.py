"""Cruza as glebas de integração do SICOR com os 26 tiles da área piloto e com as amostras atuais.
Saídas em saida/: glebas_piloto.geojson, glebas_piloto.csv, resumo.json
"""
import csv, json, os, sys
from collections import Counter, defaultdict
import shapely
from shapely import wkt
from shapely.geometry import box, Point, mapping
from shapely.ops import unary_union, transform
from shapely.strtree import STRtree
import pyproj

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS, DOM, REPO = (os.path.join(RAIZ, d) for d in ("dados", "dominio", "repo"))
SAIDA = os.path.join(RAIZ, "saida")
os.makedirs(SAIDA, exist_ok=True)
csv.field_size_limit(1 << 30)

CLASSE = {"3": "ILP", "4": "SAF", "5": "ILPF", "6": "ILF", "7": "IPF"}
# nome da classe nas amostras do LAPIG -> classe equivalente no SICOR
EQUIV = {"ILP": "ILP", "ILPF": "ILPF", "ILF": "ILF", "IPF": "IPF", "Agrofloresta": "SAF"}

# ---------- tiles
stats = json.load(open(os.path.join(REPO, "assets_cnn_spatial_stats.json"), encoding="utf-8"))
tiles = [(t["tile"], box(t["bounds"][0][1], t["bounds"][0][0], t["bounds"][1][1], t["bounds"][1][0])) for t in stats["tiles"]]
uniao = unary_union([g for _, g in tiles])
bbox = box(stats["bounds"][0][1], stats["bounds"][0][0], stats["bounds"][1][1], stats["bounds"][1][0])
shapely.prepare(uniao)

# área em hectares: projeção equivalente de Albers do Brasil (IBGE)
albers = pyproj.CRS.from_proj4("+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs")
tr = pyproj.Transformer.from_crs("EPSG:4326", albers, always_xy=True).transform
ha = lambda g: transform(tr, g).area / 1e4

# ---------- domínios
emp = {}
with open(os.path.join(DOM, "Empreendimento.csv"), encoding="latin-1", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    cab = [c.lstrip("#") for c in next(rd)]
    for r in rd:
        if len(r) >= 7:
            emp[r[0]] = dict(zip(cab, r))

# ---------- operações
ops = {}
with open(os.path.join(DADOS, "ops_integracao.csv"), encoding="utf-8", newline="") as f:
    rd = csv.DictReader(f, delimiter=";")
    for r in rd:
        ops[(r["REF_BACEN"], r["NU_ORDEM"])] = r
print(f"{len(ops):,} operações de integração no Brasil")

def safra(dt):  # dd/mm/aaaa -> ano agrícola (jul-jun)
    try:
        d, m, a = dt.split("/")
        a, m = int(a), int(m)
        return f"{a}/{a+1}" if m >= 7 else f"{a-1}/{a}"
    except Exception:
        return ""

# ---------- glebas
feicoes = []
ops_com_gleba = set()
invalidas = 0
with open(os.path.join(DADOS, "glebas_integracao.csv"), encoding="utf-8", newline="") as f:
    rd = csv.DictReader(f, delimiter=";")
    for r in rd:
        k = (r["REF_BACEN"], r["NU_ORDEM"])
        ops_com_gleba.add(k)
        o = ops[k]
        try:
            g = shapely.force_2d(wkt.loads(r["GT_GEOMETRIA"]))
            if not g.is_valid:
                g = shapely.make_valid(g)
            if g.is_empty or g.area == 0:
                invalidas += 1
                continue
        except Exception:
            invalidas += 1
            continue
        c = g.representative_point()
        no_bbox = bbox.contains(c)
        no_piloto = no_bbox and uniao.contains(c)
        e = emp.get(o["CD_EMPREENDIMENTO"], {})
        feicoes.append({
            "ref": k[0], "ordem": k[1], "indice": r["NU_INDICE"], "geom": g,
            "uf": o["CD_ESTADO"], "cod": o["CD_TIPO_INTGR_CONSOR"].strip(),
            "classe": CLASSE.get(o["CD_TIPO_INTGR_CONSOR"].strip(), "sem código (só subprograma)"),
            "subprog_integracao": o["SUBPROG_INTEGRACAO"], "emissao": o["DT_EMISSAO"], "vencimento": o["DT_VENCIMENTO"],
            "safra": safra(o["DT_EMISSAO"]), "finalidade": e.get("FINALIDADE", ""), "atividade": e.get("ATIVIDADE", ""),
            "modalidade": e.get("MODALIDADE", ""), "produto": e.get("PRODUTO", ""),
            "area_informada": o.get("VL_AREA_INFORMADA", ""), "no_bbox": no_bbox, "no_piloto": no_piloto,
        })
print(f"{len(feicoes):,} glebas válidas; {invalidas} inválidas; {len(ops_com_gleba):,} operações com gleba")

res = {"brasil": {}, "goias": {}, "piloto": {}}

# ---------- cobertura: quantas operações de integração têm gleba, por ano e UF=GO
cob = defaultdict(lambda: [0, 0])
for k, o in ops.items():
    cod = o["CD_TIPO_INTGR_CONSOR"].strip()
    if cod not in CLASSE:
        continue
    a = o["ANO_ARQUIVO"]
    for esc in ("BR",) + (("GO",) if o["CD_ESTADO"] == "GO" else ()):
        cob[(esc, a, CLASSE[cod])][0] += 1
        cob[(esc, a, CLASSE[cod])][1] += k in ops_com_gleba
res["cobertura"] = {f"{e}|{a}|{c}": v for (e, a, c), v in sorted(cob.items())}

def resumir(fs):
    out = {}
    por_classe = defaultdict(list)
    for x in fs:
        por_classe[x["classe"]].append(x)
    for cl, lst in por_classe.items():
        areas = sorted(ha(x["geom"]) for x in lst)
        n = len(areas)
        # locais distintos: funde glebas que se sobrepõem (mesmo talhão financiado mais de uma vez)
        un = unary_union([x["geom"].buffer(0) for x in lst])
        partes = list(un.geoms) if hasattr(un, "geoms") else [un]
        out[cl] = {
            "glebas": n, "operacoes": len({(x["ref"], x["ordem"]) for x in lst}),
            "locais_distintos": len(partes), "area_distinta_ha": round(ha(un)),
            "area_mediana_ha": round(areas[n // 2], 1), "area_p10_ha": round(areas[n // 10], 1), "area_p90_ha": round(areas[(n * 9) // 10], 1),
            "por_safra": dict(sorted(Counter(x["safra"] for x in lst).items())),
            "produtos": dict(Counter(x["produto"] for x in lst).most_common(8)),
            "finalidade": dict(Counter(x["finalidade"] for x in lst).most_common(4)),
        }
    return out

res["brasil"] = {cl: len(v) for cl, v in Counter(x["classe"] for x in feicoes).items()} if False else dict(Counter(x["classe"] for x in feicoes))
go = [x for x in feicoes if x["uf"] == "GO"]
pil = [x for x in feicoes if x["no_piloto"]]
res["goias"] = resumir(go)
res["piloto"] = resumir(pil)
res["piloto_por_tile"] = {}
for nome, g in tiles:
    shapely.prepare(g)
    res["piloto_por_tile"][nome] = dict(Counter(x["classe"] for x in pil if g.contains(x["geom"].representative_point())))

# ---------- comparação com as amostras atuais (centroides)
am = json.load(open(os.path.join(REPO, "assets_amostras_data.json"), encoding="utf-8"))
locais = {}
for a in am:
    locais.setdefault((a["lng"], a["lat"]), []).append(a)
arv = STRtree([x["geom"] for x in feicoes])
conf = Counter()
locais_no_piloto = 0
locais_reencontrados = 0
exemplos = []
for (lng, lat), lst in locais.items():
    p = Point(lng, lat)
    if not uniao.contains(p):
        continue
    locais_no_piloto += 1
    classes_amostra = sorted({a["classe"] for a in lst})
    idx = [i for i in arv.query(p) if feicoes[i]["geom"].contains(p)]
    classes_sicor = sorted({feicoes[i]["classe"] for i in idx})
    integ = any(c in EQUIV for c in classes_amostra)
    conf[("amostra de integração" if integ else "amostra de outra classe", "dentro de gleba de integração" if idx else "fora")] += 1
    if idx:
        locais_reencontrados += 1
        exemplos.append({"lng": lng, "lat": lat, "amostra": classes_amostra, "anos_amostra": sorted({a["ano"] for a in lst}),
                         "sicor": classes_sicor, "safras_sicor": sorted({feicoes[i]["safra"] for i in idx})})
res["amostras"] = {"locais_no_piloto": locais_no_piloto, "locais_dentro_de_gleba": locais_reencontrados,
                   "cruzamento": {f"{a} | {b}": n for (a, b), n in conf.items()}, "exemplos": exemplos[:60]}

# glebas do piloto que NÃO contêm nenhuma amostra atual = candidatas novas
pts = [Point(k) for k in locais]
arv_p = STRtree(pts)
novas = 0
for x in pil:
    tem = any(x["geom"].contains(pts[i]) for i in arv_p.query(x["geom"]))
    x["tem_amostra"] = tem
    novas += not tem
res["piloto_glebas_sem_amostra_atual"] = novas
res["piloto_glebas_total"] = len(pil)

# ---------- saídas
def props(x):
    p = {k: v for k, v in x.items() if k != "geom"}
    p["area_ha"] = round(ha(x["geom"]), 2)
    c = x["geom"].representative_point()
    p["lng"], p["lat"] = round(c.x, 6), round(c.y, 6)
    return p

for nome, fs in (("glebas_piloto", pil), ("glebas_goias", go)):
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": props(x), "geometry": mapping(x["geom"])} for x in fs]}
    json.dump(fc, open(os.path.join(SAIDA, nome + ".geojson"), "w", encoding="utf-8"), ensure_ascii=False)
    with open(os.path.join(SAIDA, nome + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
        if fs:
            w = csv.DictWriter(f, fieldnames=list(props(fs[0]).keys()), delimiter=";", extrasaction="ignore")
            w.writeheader()
            for x in fs:
                w.writerow(props(x))
json.dump(res, open(os.path.join(SAIDA, "resumo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("brasil", "piloto", "amostras", "piloto_glebas_sem_amostra_atual", "piloto_glebas_total")}, ensure_ascii=False, indent=1)[:6000])
