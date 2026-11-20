# Semelhança por embedding (AlphaEarth): negativo

**Frente:** busca de lugares parecidos com amostras conhecidas nos embeddings anuais do AlphaEarth. **Data:** 11 e 12/11/2026.

## O que foi testado

O AlphaEarth representa cada lugar por um vetor numérico anual, construído a partir de imagens de satélite. A ideia era procurar, nesses vetores, lugares parecidos com as amostras conhecidas de IPF e de ILP, sem depender de imagem de 2 m nem de leitura por IA.

O desenho foi: 10 sementes de IPF e 10 de ILP, tiradas das amostras da equipe com a mesma classe em 2023/2024 e 2024/2025; uma imagem de semelhança por classe (produto interno máximo com as sementes) no embedding anual de 2024, amostrada a 30 m; 50 candidatos por classe, escolhidos entre os mais parecidos e com pelo menos 1 km de qualquer amostra conhecida e 1,5 km entre si; e 30 pontos de controle sorteados ao acaso, para comparar.

## Resultado

**Em resumo:** 1 renque em 50 candidatos de IPF e 0 em 50 de ILP; o controle de 30 pontos deu 1 ILP; a frente foi descartada.

- **IPF:** 1 dos 50 candidatos tinha renque.
- **ILP:** 0 dos 50 candidatos tinha renque.
- **Controle:** 30 pontos ao acaso renderam 1 lido como integração (uma ILP), então o 1 em 50 não é sinal forte.
- A maioria dos 50 candidatos de IPF era **pasto com árvores nativas espalhadas**, não renque. É o que explica o negativo: o embedding aproxima o pasto arborizado da amostra de IPF, mas a imagem de 2 m não mostra fileiras.
- A separação entre classes era fraca já na referência: a semelhança mediana com a própria classe era 0,962 para IPF e 0,939 para ILP, contra 0,934 e 0,921 com a outra classe. As distribuições se sobrepõem.

**Conclusão, coerente com o resumo principal:** a frente foi **descartada**. O resultado não justificava o custo de continuar.

## Como rodar

Os scripts foram escritos para a pasta de trabalho do experimento. A raiz é lida de `ILPF_RAIZ`; a pasta do SICOR, de `ILPF_SICOR`; o projeto do Earth Engine, de `EE_PROJETO` (padrão `"SEU-PROJETO"`).

```bash
export ILPF_RAIZ=/caminho/ilpf-exp
export ILPF_SICOR=/caminho/ilpf-sicor
export EE_PROJETO=seu-projeto

python 01_alvos.py          # monta alvos.json com as amostras e as glebas do SICOR
python 03_semelhanca.py     # calcula os embeddings e escolhe 50 + 50 candidatos e 30 controles
python 02_fichas.py fichas --so semelhanca
python 04_ler.py rodada_semelhanca --grupos semelhanca,controle
```

Dependências: Python 3.10+, `earthengine-api` autenticado, `numpy`, `geopandas`, `shapely`, `Pillow` e `matplotlib`. A leitura por imagem precisa do programa `agy` no `PATH` (Gemini) e do prompt `instrucoes-de-leitura.md`.

**Entradas que não estão publicadas e por quê:**

- `assets_amostras_data.json`: coordenadas, classe, ano e área das amostras da equipe. É amostra da equipe; a regra 1 do briefing manda excluir.
- `glebas_piloto.geojson` e `glebas_goias.geojson`: dado público do SICOR, mas com 81 e 338 polígonos e 111 KB / 469 KB. Não são amostras da equipe; ficaram de fora porque a pasta `../../sicor/` publica os scripts e o `resumo.json`, mas não os geojsons. O `01_alvos.py` os lê.
- `assets_cnn_spatial_stats.json`: estatísticas do mapa da equipe (limites dos tiles e contagem por classe). Vem do repositório público da equipe, mas não é resultado desta frente.
- `alvos.json`: contém as sementes (coordenadas das amostras da equipe) e os 130 candidatos/controles. Não publicado por causa das sementes.
- `fichas/` e `leitura/`: cerca de 1 GB de fichas e 2,1 GB de leituras brutas. Além do tamanho, as fichas de exemplo desta frente são de amostras da equipe.
- `semelhanca_resumo.json`: tem as coordenadas das 20 sementes. O que não é coordenada foi copiado para `resultados/semelhanca_resultado.json`.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `codigo/01_alvos.py` | Monta `alvos.json` com as amostras conhecidas e as glebas do SICOR, com identificadores embaralhados. |
| `codigo/03_semelhanca.py` | Calcula os embeddings do AlphaEarth, a imagem de semelhança, os 50 + 50 candidatos e os 30 controles. |
| `codigo/02_fichas.py` | Monta as fichas PNG dos candidatos e controles. |
| `codigo/04_ler.py` | Manda as fichas ao Gemini em lotes e junta as respostas. |
| `codigo/cbers.py` | Leitor dos recortes CBERS-4A do catálogo aberto do INPE. |
| `instrucoes-de-leitura.md` | Prompt usado na leitura das fichas. |
| `resultados/semelhanca_resultado.json` | Referência, distribuição, contagem dos 100 candidatos e dos 30 controles. Sem coordenadas. |

## Limites

- O embedding anual de 10 m não separa pasto arborizado de IPF com renque; a confusão é conceitual, não só de limiar.
- As sementes são poucas (10 por classe) e vêm das amostras da equipe.
- O controle de 30 pontos é pequeno; 1 acerto pode ser acaso.
- O resultado negativo não diz que o AlphaEarth é inútil para outros alvos; diz que, para renque de ILPF nesta área, ele não substitui a imagem de 2 m.
- Nenhuma ficha desta frente foi publicada: as fichas-exemplo disponíveis são de amostras da equipe.

## Fonte

`DIARIO.md` (seção 3), `BALANCO.md` (Frente A), `03_semelhanca.py`, `resultado_leitura.json` e `semelhanca_resumo.json`. Os relatórios internos completos não estão neste repositório.
