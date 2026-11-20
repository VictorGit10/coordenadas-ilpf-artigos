# Inspeção de imagem por IA: confere, não acha

**Frente:** leitura de fichas por modelos de linguagem com visão. **Data:** 12 e 13/11/2026.

## O que foi testado

Cinco configurações de modelo leram as mesmas 58 fichas de resposta conhecida: 18 com árvores e 40 sem. A ficha tinha três quadros: (A) imagem CBERS-4A de 2 m com o contorno amarelo da área, (B) detalhe de 500 m no centro e (C) série de NDVI do Sentinel-2 de julho de 2020 a outubro de 2025. O pedido era dizer se havia renques, com que espaçamento, o que havia entre eles, a classe e a confiança.

Depois, 50 fichas foram marcadas por uma pessoa sem ver a resposta da IA (a "régua"). Também foi comparado um formato novo de ficha (f1, com três datas de 400 m em imagens separadas) com a ficha antiga de uma data, em 58 pontos do grupo de ensino.

## Resultado

**Em resumo:** nenhum modelo inventou renque nas 40 fichas sem árvores; o melhor viu 9 das 18 com árvores; o Hydrogen alto foi o mais barato; na régua, 24 das 50 ficaram em "não dá para dizer". A IA confere, não acha.

- **Nenhum modelo inventou renque** nas 40 fichas sem árvores (0 falso em 40; 0 em 37 para o Gemini 3.8 alto, que leu 55 das 58).
- **O melhor viu 9 das 18** fichas com árvores: Gemini 3.8 Flash alto e Gemini 4 Hydrogen alto. O 3.8 médio e o Hydrogen xhigh viram 7; o DeepSeek v4.1 Flash, 6.
- Os renques vistos são sempre parte das **mesmas 9 fichas** (as mesmas que o resumo principal lista). Nenhum modelo viu as outras 9 com árvores. O limite é da ficha de uma data só, não do modelo.
- **Hydrogen alto foi o melhor custo-benefício:** cerca de 10 mil tokens por ficha, as 58 em 6,4 min, sem erro, e cerca de 0,04 ponto de cota por leitura, contra 0,14 do 3.8 alto na esteira. O xhigh viu menos e custou cerca de 4 vezes mais.
- **Na régua, 24 das 50 fichas ficaram em "não dá para dizer".** Das 13 que a IA aprovou com nota máxima, a marcação humana deu 11 "sim", 1 "sim com ressalva" e 1 "não sei"; nenhuma recebeu "não". Mas 5 fichas rejeitadas pela IA receberam "sim com ressalva", e uma ficha de uma data só não basta para quem não é inspetor.
- **O formato f1 acertou 13 dos 28 pontos com árvore e deu 1 falso em 30.** Nos 12 talhões com as duas fichas, o f1 viu 6 renques, contra 5 da ficha antiga; o Hydrogen via 8 desses 12 com a ficha antiga. O ganho do formato sozinho é pequeno. O f2 (f1 mais ampliações, referência e passo a passo) não entrou na comparação do resumo principal.

**Conclusão, coerente com o resumo principal:** a IA de imagem **confere, não acha**. Ela quase não dá falso positivo, mas deixa passar metade ou mais das áreas com árvores. O papel dela é conferir candidatos apontados por outra fonte (detector, classificador, artigo), não varrer a área.

## Como rodar

Os scripts foram escritos para a pasta de trabalho do experimento, não para esta pasta. O caminho da raiz é lido da variável `ILPF_RAIZ`; sem ela, vale o padrão de duas pastas acima do script. O projeto do Earth Engine é lido de `EE_PROJETO` e o padrão é `"SEU-PROJETO"`.

```bash
# leitura por DeepSeek, via opencode
export ILPF_RAIZ=/caminho/ilpf-exp
export EE_PROJETO=seu-projeto
python 14_ler_opencode.py rodada1 --grupos conhecida \
  --modelo ollama/deepseek-v4.1-flash:cloud#max --paralelo 4 --lote 4

# régua: gera a página e o gabarito a partir das leituras
python 16_regua.py /caminho/regua

# refazer as fichas (opcional; precisa de Earth Engine e da série de NDVI)
python 02_fichas.py fichas --so conhecida
```

Dependências: Python 3.10+, `Pillow`, `matplotlib`, `shapely`, `pyproj`, `numpy` e, para refazer fichas, `earthengine-api` autenticado. Para a leitura, o programa externo `opencode` no `PATH`; a régua só precisa de `Pillow`.

**Entradas que não estão publicadas e por quê:**

- `alvos.json`: contém as coordenadas e os identificadores das 58 amostras da equipe e das glebas do SICOR. É amostra da equipe; a regra 1 do briefing manda excluir.
- `fichas/`: cerca de 1 GB de PNGs, incluindo as 58 fichas conhecidas. Além do tamanho, são fichas de amostras da equipe.
- `series.json`: série de NDVI por ficha, derivada das amostras. Não publicada pelo mesmo motivo.
- `leitura/`: cerca de 2,1 GB de leituras brutas, lotes e respostas por ficha. O que importa está agregado nos dois CSV e no JSON desta pasta.
- `PEDIDO2.md` (prompt do DeepSeek) e `PEDIDO.md` (prompt do Gemini): publicados como `instrucoes-de-leitura-deepseek.md` e `instrucoes-de-leitura.md`. Para o script, copie o prompt desejado para `$ILPF_RAIZ/leitura/` com o nome que o `--pedido` espera.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `codigo/14_ler_opencode.py` | Manda as fichas ao DeepSeek pelo `opencode`, em lotes e em paralelo; junta as respostas em `leituras.json`. |
| `codigo/16_regua.py` | Monta a página HTML da régua (50 fichas embaralhadas) e o `regua_gabarito.json`. |
| `codigo/02_fichas.py` | Monta a ficha PNG de três quadros a partir de `alvos.json` e `series.json`. |
| `codigo/cbers.py` | Leitor dos recortes CBERS-4A do catálogo aberto do INPE (STAC). |
| `instrucoes-de-leitura.md` | Prompt usado nas leituras do Gemini. |
| `instrucoes-de-leitura-deepseek.md` | Prompt usado nas leituras do DeepSeek, com campos extras (contorno, idade das árvores). |
| `resultados/comparacao_leitores.csv` | As cinco configurações, fichas lidas, renques vistos, falsos, classe exata, ILP, tokens e tempo. |
| `resultados/regua_resumo.csv` | Cruzamento das leituras da IA com a marcação humana das 50 fichas. |
| `resultados/leituras_conhecidas_resumo.json` | Contagens e matriz de confusão das 58 fichas conhecidas (bloco `conhecidas` do `resultado_leitura.json`), sem identificadores. |

## Limites

- A base é pequena: 18 fichas com árvores e 40 sem. Um caso muda vários pontos percentuais.
- A ficha de uma data só é o limite principal: o mesmo lugar em 2023–2026 e a série temporal mudam a resposta.
- A classe (IPF, ILF, ILPF) é palpite do modelo; a classe final é trabalho de inspeção.
- ILP não é reconhecível numa imagem de uma data: os modelos acertaram 3 ou 4 de 14.
- O f2 não foi incluído na comparação publicada; o resumo principal registra que não há leituras dele para comparar.
- Nenhuma ficha desta frente foi publicada como exemplo: as 58 são de amostras da equipe. O exemplo de ficha do material é uma candidata do detector, em `../detector-de-renques/exemplo/`.

## Fonte

`DIARIO.md` (seções 2, 7, 78–98 e 136–212), `BALANCO.md` (Frente B), `ANALISE-DEEPSEEK-2026-11-13.md` e os arquivos de `testes-2026-11-12/`. As leituras brutas e os relatórios internos não estão neste repositório.
