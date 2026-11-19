#!/usr/bin/env python3
"""Gera a exportação completa das coordenadas dos artigos (níveis A, B e C).

Este script foi escrito para o ambiente do pipeline. Ele lê arquivos de
../../dados e ../../site/referencia.js, que não estão incluídos neste
repositório público; por isso, aqui ele serve como registro de como os quatro
arquivos de dados foram gerados, e não roda só com o que está publicado.

Grava, nesta pasta, coordenadas-todas.csv, locais-sem-coordenada.csv,
documentos.csv e croquis.geojson. Usa só a biblioteca padrão do Python.

Uso:
    python gerar.py
"""

import csv
import json
import os
import re
from collections import Counter, defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DADOS = os.path.join(RAIZ, "dados")
SITE = os.path.join(RAIZ, "site")

# ---------------------------------------------------------------------------
# leitura


def ler_json(nome, padrao=None):
    caminho = os.path.join(DADOS, nome)
    if not os.path.exists(caminho):
        if padrao is not None:
            return padrao
        raise FileNotFoundError(caminho)
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def ler_csv(nome):
    caminho = os.path.join(DADOS, nome)
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def escrever_csv(nome, campos, linhas):
    caminho = os.path.join(AQUI, nome)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


# ---------------------------------------------------------------------------
# limpeza de texto e de nomes de pessoas


def limpa_texto(t):
    """Remove controles do PDF, normaliza espaços e preserva quebras de linha."""
    if t is None:
        return ""

    def visivel(c):
        return c in "\n\t" or (ord(c) >= 32 and not (0x7F <= ord(c) <= 0x9F))

    t = str(t).replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\u00a0", " ").replace("\u202f", " ")
    t = "".join(c if visivel(c) else " " for c in t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    return t.strip()


def uma_linha(t):
    return re.sub(r"\s+", " ", limpa_texto(t)).strip()


# Nome próprio: uma palavra com maiúscula seguida de outras, aceitando as
# partículas de, da, do, dos, das e e.  Serve para achar nomes de pessoas em
# expressões como "propriedade do Sr. Fulano de Tal".
NOME = (
    r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’.\-]*"
    r"(?:\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’.\-]*)*"
)
# Para "propriedade de Fulano", exige ao menos duas palavras: assim
# "propriedade da Embrapa" e "propriedade da Universidade" não são mexidas.
NOME2 = (
    r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’.\-]*"
    r"(?:\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’.\-]*)+"
)
INSTITUICAO = (
    r"(?:Embrapa|Universidade|Instituto|Empresa|Fundação|Centro|Estação|"
    r"Fazenda|Sítio|Chácara|Assentamento|Cooperativa|Prefeitura|Governo|"
    r"Ministério|Incaper|Emater|Epamig|Iapar|UFRGS|UF|IF)\b"
)
# Começos de nome de fazenda, sítio, lugar ou instituição.  Serve para não
# tratar "Sítio Boa Esperança (propriedade rural)" como nome de pessoa.
NAO_NOME_INICIO = (
    r"(?:Fazenda|Sítio|Sitio|Chácara|Chacara|Estância|Estancia|Rancho|Haras|"
    r"Retiro|Assentamento|Comunidade|Colônia|Colonia|Bairro|Distrito|"
    r"Município|Municipio|Propriedade|Área|Area)\b"
)
# Palavras que aparecem entre parênteses depois de um nome de fazenda e que
# não são nome de pessoa: unidades, empresas, siglas e topônimos.  A regra do
# parêntese só vale para o campo `fazenda`, para exatamente duas palavras e
# quando nenhuma das duas está nesta lista.
NAO_NOME_PAR = {
    "farm", "agroflorestas", "agropecuária", "agropecuaria", "grupo",
    "cabanha", "fazenda", "sítio", "sitio", "chácara", "chacara", "estância",
    "estancia", "rancho", "haras", "assentamento", "associação", "associacao",
    "escola", "universidade",
    "instituto", "centro", "cooperativa", "fundação", "fundacao", "empresa",
    "comissão", "comissao", "projeto", "programa", "núcleo", "nucleo",
    "laboratório", "laboratorio", "departamento", "campus", "câmpus", "polo",
    "distrito", "município", "municipio", "estado", "rio", "serra", "vale",
    "mato", "minas", "são", "sao", "santa", "santo", "nossa", "nova", "novo",
    "campo", "belo", "bela", "alta", "alto", "ponta", "passo", "porto",
    "três", "tres", "dois", "duas", "grande", "lagoa", "lago", "costa",
    "morro", "monte", "barra", "ilha", "praia", "boa", "bom", "balão",
    "balao", "uep", "urt", "iftm", "embrapa", "iapar", "ceplac", "ufra",
    "mst", "pf",
}
NOME_PAR2 = re.compile(
    r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-zà-ÿ][\wÀ-ÿ'’.\-]*"
    r"\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-zà-ÿ][\wÀ-ÿ'’.\-]*$"
)


def limpa_parentese(m):
    """Troca "(Nome Sobrenome)" por "(nome omitido)" quando parece pessoa."""
    conteudo = m.group(1).strip()
    if not NOME_PAR2.match(conteudo):
        return m.group(0)
    palavras = conteudo.split()
    if any(p.lower() in NAO_NOME_PAR for p in palavras):
        return m.group(0)
    return "([nome omitido])"


def limpa_nome(t, campo=None):
    """Tira nomes de proprietários, como o site já faz. Não mexe em topônimos."""
    if not t:
        return ""
    t = limpa_texto(t)
    # "(propriedade de Fulano...)" inteiro
    t = re.sub(
        r"\s*\((?:[^()]*?(?i:propriedade|propriet[aá]ri[oa]s?)\s+d[eoa]s?\s+[^()]*)\)",
        "",
        t,
    )
    # Sr., Sra., Senhor, Senhora
    t = re.sub(
        r"((?i:\b(?:Sr\.?|Sra\.?|Senhor|Senhora)))\s+" + NOME,
        r"\1 [nome omitido]",
        t,
    )
    # família Fulano (mas não "Escola Família Agrícola", que é nome de escola)
    t = re.sub(
        r"((?i:\bfam[íi]lia))\s+(?:de\s+)?"
        r"(?!Agrícola\b|Rural\b|Agricultora\b|Produtora\b|Camponesa\b|Trabalhadora\b)"
        + NOME,
        r"\1 [nome omitido]",
        t,
    )
    # agricultor Fulano, produtor Fulano, cafeicultor Fulano...
    t = re.sub(
        r"((?i:\b(?:agricultor|agricultora|produtor|produtora|cafeicultor|"
        r"cafeicultora|pecuarista|propriet[áa]rio|propriet[áa]ria)))\s+" + NOME,
        r"\1 [nome omitido]",
        t,
    )
    # propriedade de Fulano de Tal, no singular ou no plural
    t = re.sub(
        r"((?i:\bpropriedade[s]?)\s+(?:de|do|da)\s+)(?!" + INSTITUICAO + r")" + NOME2,
        r"\1[nome omitido]",
        t,
    )
    # "Fazenda X, de Fulano de Tal" (nome de pessoa depois da vírgula)
    t = re.sub(
        r"(,\s*de\s+)(?!" + INSTITUICAO + r")" + NOME2,
        r"\1[nome omitido]",
        t,
    )
    # Nome próprio no começo, seguido de "(propriedade particular)".
    # Só pega quando o campo não começa com um nome de fazenda, sítio ou
    # instituição ("Sítio Boa Esperança (propriedade rural)" fica como está).
    t = re.sub(
        r"^(?!" + NAO_NOME_INICIO + r")" + NOME2
        + r"(?=\s*\((?:propriedade|propriet[áa]ri[oa]|produtor|produtora|"
        r"agricultor|agricultora))",
        "[nome omitido]",
        t,
    )
    # Nome de pessoa entre parênteses depois do nome da fazenda, sem a palavra
    # "propriedade" antes.  Só no campo `fazenda` e só quando o parêntese tem
    # exatamente duas palavras que não são unidade, empresa, sigla ou lugar.
    if campo == "fazenda":
        t = re.sub(r"\(([^()]*)\)", limpa_parentese, t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# traduções de códigos e formatos


REF_SIMPLES = {
    "parcela": "parcela",
    "area_experimental": "área experimental",
    "fazenda_sede": "fazenda ou sede",
    "municipio": "município",
    "nao_diz": "não diz",
    "": "não diz",
}


def texto_ref(ref):
    if ref == "fazenda_sede":
        return "a coordenada é da fazenda ou da sede, não de uma parcela ou área experimental"
    if ref == "municipio":
        return "a coordenada é do município, não do local estudado"
    if ref in ("nao_diz", "", None):
        return "o texto não diz a que a coordenada se refere"
    if ref == "parcela":
        return "a coordenada é de uma parcela"
    if ref == "area_experimental":
        return "a coordenada é da área experimental"
    return "a coordenada se refere a " + str(ref)


def texto_precisao(p):
    if p is None or str(p).strip() == "":
        return "precisão não informada"
    s = str(p).strip().replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return "precisão não informada"
    if abs(v - 1850) < 0.6:
        return "precisão só em minutos (~1,8 km)"
    if abs(v - 11100) < 6:
        return "precisão de 0,1° (~11 km)"
    if abs(v - 1110) < 0.6:
        return "precisão de 0,01° (~1,1 km)"
    if abs(v - 185) < 0.6:
        return "precisão de 0,1 minuto (~185 m)"
    if abs(v - 18.5) < 0.6:
        return "precisão de 0,01 minuto (~18 m)"
    if v <= 0:
        return "precisão de menos de 1 m"
    if v <= 100:
        return "precisão de ~%d m" % round(v)
    if v >= 1000:
        return ("precisão de %.1f km" % (v / 1000)).replace(".", ",")
    return "precisão de %d m, acima do limite de 100 m" % round(v)


def texto_km(km):
    v = float(str(km).replace(",", "."))
    return ("%.1f" % v).replace(".", ",")


def texto_metros(km):
    v = float(str(km).replace(",", "."))
    m = round(v * 1000)
    if m < 1000:
        return "%d m" % m
    return texto_km(km) + " km"


def formata_classe(nome):
    nome = nome.strip()
    nome = nome.replace("Vegetacao", "Vegetação")
    return nome


def formata_classes(s):
    partes = []
    for bloco in (s or "").split(" | "):
        bloco = bloco.strip()
        if not bloco:
            continue
        m = re.match(r"(.+?)\(([^)]*)\)$", bloco)
        if not m:
            partes.append(formata_classe(bloco))
            continue
        nome, papel = m.group(1).strip(), m.group(2).strip()
        papel = {"comparacao": "comparação", "estudado": "estudado"}.get(papel, papel)
        partes.append("%s (%s)" % (formata_classe(nome), papel) if papel else formata_classe(nome))
    # O mesmo sistema pode ter sido listado mais de uma vez pela IA.
    vistos = []
    for p in partes:
        if p not in vistos:
            vistos.append(p)
    return " | ".join(vistos)


def formata_periodo(anos):
    partes = []
    for bloco in (anos or "").split(" | "):
        bloco = bloco.strip()
        if not bloco:
            continue
        m = re.match(r"impl\s+(.*?)\s*/\s*aval\s+(.*)$", bloco)
        if not m:
            partes.append(bloco)
            continue
        impl, aval = m.group(1).strip(), m.group(2).strip()
        seg = []
        if impl and impl != "-":
            seg.append("implantação " + impl)
        if aval and aval != "-":
            seg.append("avaliação " + aval)
        if seg:
            partes.append("; ".join(seg))
    vistos = []
    for p in partes:
        if p not in vistos:
            vistos.append(p)
    return " | ".join(vistos)


def doi_limpo(s):
    s = (s or "").strip()
    s = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^doi:\s*", "", s, flags=re.I)
    return s.strip()


# ---------------------------------------------------------------------------
# motivo da classificação, em português


def traduz_motivo(raw, nivel, precisao, sem_latlon=False):
    s = (raw or "").strip()
    itens = []  # (ordem, texto)

    def add(ordem, texto):
        if texto and texto not in [t for _, t in itens]:
            itens.append((ordem, texto))

    def take(padrao, funcao, ordem, flags=0):
        nonlocal s
        for m in re.finditer(padrao, s, flags):
            add(ordem, funcao(m))
        s = re.sub(padrao, "", s, flags=flags)

    # O aviso do PDF tem ponto e vírgula dentro; por isso vem primeiro.
    take(
        r"o PDF perdeu o sinal de minuto \(aparece como 0\); leitura reconstruida",
        lambda m: "o PDF perdeu o sinal de minuto (aparece como 0); leitura reconstruída",
        90,
    )
    take(
        r"trecho nao existe no texto",
        lambda m: "o trecho citado não foi encontrado no texto",
        5,
    )
    take(
        r"coordenada impossivel no texto \(minuto ou segundo acima de 60\)",
        lambda m: "coordenada impossível no texto (minuto ou segundo acima de 60)",
        5,
    )
    take(
        r"numero nao bate com o trecho",
        lambda m: "o número não confere com o texto",
        5,
    )
    if sem_latlon:
        # "fora do Brasil" aqui costuma ser só efeito de a conversão ter
        # falhado; o motivo útil é a falta de latitude/longitude.
        s = re.sub(r"fora do Brasil", "", s)
    else:
        take(r"fora do Brasil", lambda m: "cai fora do Brasil", 10)
    take(
        r"precisao \? m",
        lambda m: "não foi possível medir a precisão",
        20,
    )
    take(r"precisao ([\d.,]+) m", lambda m: texto_precisao(m.group(1)), 20)
    take(r"refere-se a\s*([a-z_]*)\s*", lambda m: texto_ref(m.group(1)), 30)
    take(
        r"sem ano no texto",
        lambda m: "o texto não informa ano de implantação nem de avaliação",
        40,
    )
    take(
        r"cai em area construida \(([\d.]+)% num raio de 100 m\)",
        lambda m: "cai em área construída (%s%% num raio de 100 m)" % m.group(1),
        50,
    )
    take(
        r"a ([\d.,]+) km da sede de ([^:]+): provavelmente e a coordenada da cidade",
        lambda m: "cai na cidade: a %s da sede municipal de %s"
        % (texto_metros(m.group(1)), m.group(2).strip()),
        60,
    )
    take(
        r"a ([\d.,]+) km da sede de ([^:]+): conferir se nao e a coordenada da cidade",
        lambda m: "a %s km da sede de %s — conferir se não é a coordenada da cidade"
        % (texto_km(m.group(1)), m.group(2).strip()),
        61,
    )

    resto = re.sub(r"[\s;]+", " ", s).strip()
    if resto:
        add(99, "outro motivo registrado no script: " + resto)

    itens.sort(key=lambda x: (x[0], x[1]))
    textos = [t for _, t in itens]

    if nivel == "A":
        base = "parcela/área experimental; %s; classe e ano no texto" % texto_precisao(precisao)
        avisos = [t for o, t in itens if o in (61, 90)]
        return "; ".join([base] + avisos)

    if nivel == "B":
        # A precisão boa costuma ser o pano de fundo do B; entra no fim.
        tem_precisao = bool(re.search(r"precisao", raw or ""))
        if not tem_precisao:
            textos.append(texto_precisao(precisao))
        if not textos:
            textos.append("coordenada com boa precisão, mas não é de parcela/área experimental ou falta ano no texto")
        return "; ".join(textos)

    # nível C
    if sem_latlon:
        textos.append("não foi possível converter a coordenada em latitude/longitude")
    if not textos:
        textos.append("não entrou em A/B/C por motivo não registrado")
    return "; ".join(textos)


# ---------------------------------------------------------------------------
# dados


linhas = ler_csv("coordenadas.csv")
X = ler_json("extracao.json")
CHK = ler_json("checagens.json", {})
CONF = ler_json("confirmacao_imagem.json", {})
RESUMO = ler_json("resumo.json", {})
FILA = ler_json("fila.json", [])
SESSOES = ler_json("sessoes.json", [])
CAND = ler_json("candidatos.json", {})
CAND_NOVO = ler_json("candidatos_novo.json", {})

META = {}
for d in FILA:
    if isinstance(d, dict) and d.get("id"):
        META.setdefault(d["id"], d)


def meta_doc(id_doc, linha=None):
    m = META.get(id_doc, {})
    linha = linha or {}
    titulo = m.get("titulo") or linha.get("titulo") or ""
    ano = m.get("ano")
    if ano in (None, ""):
        ano = linha.get("ano_pub", "")
    doi = doi_limpo(m.get("doi") or linha.get("doi") or "")
    link = m.get("pdf") or m.get("pagina") or linha.get("link") or ""
    return {
        "titulo": uma_linha(titulo),
        "ano": ano,
        "doi": doi,
        "link": limpa_texto(link),
    }


def chave_conf(linha):
    if not linha.get("lat") or not linha.get("lon"):
        return None
    try:
        return "%s|%.6f|%.6f" % (
            linha["id"],
            float(linha["lat"]),
            float(linha["lon"]),
        )
    except ValueError:
        return None


def conf_texto(linha):
    if linha["nivel"] not in ("A", "B"):
        return ""
    k = chave_conf(linha)
    if not k or k not in CONF:
        return "não conferida"
    c = CONF[k]
    status = {"sim": "sim", "incerto": "incerto", "nao": "não"}.get(
        c.get("status", ""), c.get("status", "")
    )
    nota = uma_linha(c.get("nota", ""))
    return status + (" — " + nota if nota else "")


# ---------------------------------------------------------------------------
# coordenadas-todas.csv


CAMPOS_COORD = [
    "nivel",
    "motivo_classificacao",
    "id_ponto",
    "id_documento",
    "titulo",
    "ano_publicacao",
    "doi",
    "link",
    "pagina",
    "figura_ou_mapa",
    "coordenada_literal",
    "trecho_localizacao",
    "lat",
    "lon",
    "precisao_m",
    "a_que_se_refere",
    "local",
    "fazenda",
    "municipio",
    "uf",
    "classes",
    "periodo",
    "conferencia_imagem",
]

cont_ab = defaultdict(int)
cont_c = defaultdict(int)
saida_coord = []
for r in linhas:
    nivel = r.get("nivel", "")
    if nivel not in ("A", "B", "C"):
        continue
    id_doc = r["id"]
    if nivel in ("A", "B"):
        cont_ab[id_doc] += 1
        id_ponto = "%s-%d" % (id_doc, cont_ab[id_doc])
    else:
        cont_c[id_doc] += 1
        id_ponto = "%s-C%d" % (id_doc, cont_c[id_doc])

    md = meta_doc(id_doc, r)
    sem_latlon = not (r.get("lat") and r.get("lon"))
    saida_coord.append(
        {
            "nivel": nivel,
            "motivo_classificacao": traduz_motivo(
                r.get("motivo", ""), nivel, r.get("precisao_m", ""), sem_latlon
            ),
            "id_ponto": id_ponto,
            "id_documento": id_doc,
            "titulo": md["titulo"],
            "ano_publicacao": md["ano"],
            "doi": md["doi"],
            "link": md["link"],
            "pagina": limpa_texto(r.get("pagina", "")),
            "figura_ou_mapa": uma_linha(r.get("mapa", "")),
            "coordenada_literal": limpa_texto(r.get("texto_literal", "")),
            "trecho_localizacao": uma_linha(limpa_nome(r.get("trecho_localizacao", ""))),
            "lat": r.get("lat", ""),
            "lon": r.get("lon", ""),
            "precisao_m": r.get("precisao_m", ""),
            "a_que_se_refere": REF_SIMPLES.get(r.get("refere", ""), r.get("refere", "")),
            "local": uma_linha(limpa_nome(r.get("local", ""))),
            "fazenda": uma_linha(limpa_nome(r.get("fazenda", ""), "fazenda")),
            "municipio": uma_linha(r.get("municipio", "")),
            "uf": uma_linha(r.get("uf", "")),
            "classes": formata_classes(r.get("classes", "")),
            "periodo": formata_periodo(r.get("anos", "")),
            "conferencia_imagem": conf_texto(r),
        }
    )

# A precisão das 15 linhas do W2531023108 (minutos decimais com três casas) e
# das duas linhas de minutos inteiros abaixo foi calculada errado pelo
# pipeline.  Elas continuam C nesta exportação, mas o motivo recebe a ressalva
# para não repetir o número errado sem explicação.
NOTA_PRECISAO = " (precisão calculada incorretamente pelo pipeline; ver LEIA-ME)"
for d in saida_coord:
    if d["id_documento"] == "W2531023108" or d["id_ponto"] in (
        "W2625001271-C1",
        "W2887145174-C1",
    ):
        d["motivo_classificacao"] += NOTA_PRECISAO

ORDEM_NIVEL = {"A": 0, "B": 1, "C": 2}


def chave_ponto(d):
    sufixo = d["id_ponto"].rsplit("-", 1)[-1]
    if sufixo.startswith("C"):
        return (1, int(sufixo[1:]))
    return (0, int(sufixo))


saida_coord.sort(
    key=lambda d: (
        ORDEM_NIVEL.get(d["nivel"], 9),
        d["id_documento"],
        chave_ponto(d),
    )
)
escrever_csv("coordenadas-todas.csv", CAMPOS_COORD, saida_coord)

# ---------------------------------------------------------------------------
# locais-sem-coordenada.csv


CAMPOS_DESC = [
    "nivel",
    "motivo_descarte",
    "id_local",
    "id_documento",
    "titulo",
    "ano_publicacao",
    "doi",
    "link",
    "local",
    "fazenda",
    "municipio",
    "uf",
    "classes",
    "periodo",
    "figura_ou_mapa",
    "trecho_localizacao",
]

cont_sem = defaultdict(int)
saida_desc = []
for r in linhas:
    if r.get("nivel") != "sem coordenada":
        continue
    id_doc = r["id"]
    cont_sem[id_doc] += 1
    md = meta_doc(id_doc, r)
    saida_desc.append(
        {
            "nivel": "sem coordenada",
            "motivo_descarte": (
                "o texto não dá coordenada deste local: o artigo descreve o local, "
                "mas não informa latitude e longitude"
            ),
            "id_local": "%s-S%d" % (id_doc, cont_sem[id_doc]),
            "id_documento": id_doc,
            "titulo": md["titulo"],
            "ano_publicacao": md["ano"],
            "doi": md["doi"],
            "link": md["link"],
            "local": uma_linha(limpa_nome(r.get("local", ""))),
            "fazenda": uma_linha(limpa_nome(r.get("fazenda", ""), "fazenda")),
            "municipio": uma_linha(r.get("municipio", "")),
            "uf": uma_linha(r.get("uf", "")),
            "classes": formata_classes(r.get("classes", "")),
            "periodo": formata_periodo(r.get("anos", "")),
            "figura_ou_mapa": uma_linha(r.get("mapa", "")),
            "trecho_localizacao": uma_linha(limpa_nome(r.get("trecho_localizacao", ""))),
        }
    )

escrever_csv("locais-sem-coordenada.csv", CAMPOS_DESC, saida_desc)

# ---------------------------------------------------------------------------
# documentos.csv


CAMPOS_DOC = [
    "id_documento",
    "titulo",
    "ano_publicacao",
    "doi",
    "link",
    "estudo_de_campo",
    "n_locais",
    "n_coordenadas",
    "n_A",
    "n_B",
    "n_C",
    "situacao",
]

contagem = defaultdict(Counter)
for r in linhas:
    if r.get("nivel") in ("A", "B", "C"):
        contagem[r["id"]][r["nivel"]] += 1

ORDEM_SITUACAO = {
    "com coordenada A/B": 0,
    "só coordenada C": 1,
    "local sem coordenada": 2,
    "não é estudo de campo": 3,
}

saida_doc = []
for id_doc, v in X.items():
    c = contagem[id_doc]
    n_ab = c["A"] + c["B"]
    if not v.get("estudo_de_campo"):
        situacao = "não é estudo de campo"
    elif n_ab > 0:
        situacao = "com coordenada A/B"
    elif c["C"] > 0:
        situacao = "só coordenada C"
    else:
        situacao = "local sem coordenada"
    md = meta_doc(id_doc)
    saida_doc.append(
        {
            "id_documento": id_doc,
            "titulo": md["titulo"],
            "ano_publicacao": md["ano"],
            "doi": md["doi"],
            "link": md["link"],
            "estudo_de_campo": "sim" if v.get("estudo_de_campo") else "não",
            "n_locais": len(v.get("locais") or []),
            "n_coordenadas": c["A"] + c["B"] + c["C"],
            "n_A": c["A"],
            "n_B": c["B"],
            "n_C": c["C"],
            "situacao": situacao,
        }
    )

saida_doc.sort(
    key=lambda d: (
        ORDEM_SITUACAO.get(d["situacao"], 9),
        d["id_documento"],
    )
)
escrever_csv("documentos.csv", CAMPOS_DOC, saida_doc)

# ---------------------------------------------------------------------------
# croquis.geojson


def gera_croquis():
    caminho = os.path.join(SITE, "referencia.js")
    if not os.path.exists(caminho):
        return {"type": "FeatureCollection", "name": "croquis", "features": []}
    with open(caminho, encoding="utf-8") as f:
        texto = f.read()
    m = re.search(r"window\.REF\s*=\s*(\[.*\])\s*;?\s*$", texto, re.S)
    if not m:
        raise ValueError("não entendi o formato de site/referencia.js")
    areas = json.loads(m.group(1))
    feats = []
    for a in areas:
        poligono = a.get("poligono") or []
        if len(poligono) < 3:
            continue
        anel = []
        for par in poligono:
            if not isinstance(par, (list, tuple)) or len(par) < 2:
                continue
            lat, lon = float(par[0]), float(par[1])
            anel.append([lon, lat])
        if len(anel) < 3:
            continue
        if anel[0] != anel[-1]:
            anel.append(anel[0])

        props = {}
        for chave in (
            "nome",
            "classe",
            "municipio",
            "uf",
            "area_artigo",
            "area_desenho",
            "figura",
            "titulo",
            "autores",
            "ano",
            "revista",
            "doi",
            "historia",
        ):
            if a.get(chave) not in (None, ""):
                props[chave] = a[chave]
        props["id_area"] = a.get("id", "")
        props["id_documento"] = a.get("openalex", "")

        descricao = []
        if a.get("nome"):
            descricao.append(a["nome"])
        if a.get("classe"):
            descricao.append("classe " + str(a["classe"]))
        if a.get("municipio"):
            descricao.append(
                "%s/%s" % (a["municipio"], a.get("uf", ""))
                if a.get("uf")
                else a["municipio"]
            )
        if a.get("figura"):
            descricao.append("desenhado a partir de " + str(a["figura"]))
        if a.get("area_artigo") is not None:
            descricao.append(
                "área no artigo %s ha" % str(a["area_artigo"]).replace(".", ",")
            )
        if a.get("area_desenho") is not None:
            descricao.append(
                "área do desenho %s ha" % str(a["area_desenho"]).replace(".", ",")
            )
        props["descricao"] = "; ".join(descricao) + "."

        feats.append(
            {
                "type": "Feature",
                "id": a.get("id", ""),
                "properties": props,
                "geometry": {"type": "Polygon", "coordinates": [anel]},
            }
        )
    return {"type": "FeatureCollection", "name": "croquis", "features": feats}


croquis = gera_croquis()
with open(os.path.join(AQUI, "croquis.geojson"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(croquis, f, ensure_ascii=False, indent=1)
    f.write("\n")

# ---------------------------------------------------------------------------
# conferência e resumo


por_nivel = Counter(r["nivel"] for r in saida_coord)
print("Arquivos gravados em %s" % AQUI)
print("coordenadas-todas.csv: %d linhas (A=%d, B=%d, C=%d)"
      % (len(saida_coord), por_nivel["A"], por_nivel["B"], por_nivel["C"]))
print("locais-sem-coordenada.csv: %d linhas (locais sem coordenada)" % len(saida_desc))
print("documentos.csv: %d linhas" % len(saida_doc))
print("croquis.geojson: %d polígonos" % len(croquis["features"]))

print("Documentos por situação:")
for k in ("com coordenada A/B", "só coordenada C", "local sem coordenada", "não é estudo de campo"):
    print("  %-24s %d" % (k + ":", sum(1 for d in saida_doc if d["situacao"] == k)))

print("Conferência na imagem (pontos A/B):")
status = Counter()
for r in saida_coord:
    if r["nivel"] in ("A", "B"):
        s = r["conferencia_imagem"].split(" — ")[0]
        status[s] += 1
for k in ("sim", "incerto", "não", "não conferida"):
    print("  %-15s %d" % (k + ":", status[k]))
print("  total A/B:      %d" % sum(status.values()))

# Conferências com o resumo oficial.
esperado = {"A": 125, "B": 105, "C": 228}
if dict(por_nivel) != esperado:
    print("ATENÇÃO: níveis não batem com o resumo:", dict(por_nivel), esperado)
else:
    print("Níveis batem com dados/resumo.json: 125 A, 105 B, 228 C.")

print("Total de locais em extracao.json: %d" % sum(len(v.get("locais") or []) for v in X.values()))
print("Sessões em sessoes.json: %d; pool de candidatos: %s"
      % (len(SESSOES), CAND.get("total_pool", "?")))
print("checagens.json: %d pontos únicos; confirmacao_imagem.json: %d chaves"
      % (len(CHK), len(CONF)))
if RESUMO:
    print("resumo.json: documentos=%s, campo=%s, coordenadas=%s"
          % (RESUMO.get("documentos"), RESUMO.get("estudo_de_campo"),
             RESUMO.get("coordenadas_por_nivel")))
