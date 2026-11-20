# Material dos testes exploratórios: índice e exemplo comentado

Este material reúne o que é leve e reaproveitável dos testes feitos entre 11 e 15 de novembro de 2026 para gerar amostras de ILPF por IA no Cerrado goiano. Ele acompanha o resumo principal em `../LEIA-ME.md`: os números daqui são os mesmos de lá, e nenhuma frente foi reescrita para parecer melhor do que foi.

O experimento testou caminhos para aumentar as amostras de sistemas integrados do mapa do LAPIG/Rede ILPF: 26 tiles, 4,52 milhões de hectares, safra 2024/2025. Quase tudo foi teste exploratório e não produziu amostra aproveitável. Nenhuma amostra foi confirmada por inspetor do laboratório e nada foi enviado à equipe.

## Índice

| Pasta | O que tem | Resultado em uma linha |
|---|---|---|
| [`inspecao-por-ia/`](inspecao-por-ia/LEIA-ME.md) | Cinco configurações de modelo lendo 58 fichas de resposta conhecida, a régua de 50 fichas e o teste de formato f1 | **Confere, não acha:** 0 falso em 40, no máximo 9 de 18 áreas com árvores vistas |
| [`semelhanca-alphaearth/`](semelhanca-alphaearth/LEIA-ME.md) | Busca de lugares parecidos com amostras de IPF e ILP nos embeddings anuais do AlphaEarth | **Descartado:** 1 renque em 50 candidatos de IPF e 0 em 50 de ILP |
| [`detector-de-renques/`](detector-de-renques/LEIA-ME.md) | Detector de textura periódica em CBERS-4A de 2 m, varredura dos 26 tiles, persistência e duas leituras por IA | **Candidatas, não confirmadas:** 39 áreas, 1.109 ha, 26 locais, 14 tiles |
| [`classificacao/`](classificacao/LEIA-ME.md) | Classificador DINOv2 com 856 recortes e teste de separação da TempCNN com 40 treinos | **Melhor resultado técnico:** 7 de 8 talhões com árvores nos tiles; sem amostra confirmada |
| [`curvas-evi2/`](curvas-evi2/LEIA-ME.md) | Reprodução do método de EVI2 da equipe e aplicação às 39 candidatas | **Método reproduzido:** diferença média de 3,7 × 10⁻⁸ em 21 registros |
| [`auditoria-mapa/`](auditoria-mapa/LEIA-ME.md) | Protocolo, sorteio de 100 pontos de IPF, 35 controles, 15 repetições e tela de inspeção | **Inconclusivo:** estrutura pronta, leitura por IA não feita |
| [`revisoes-de-plano/`](revisoes-de-plano/LEIA-ME.md) | Dois pedidos e quatro pareceres de modelos sobre o plano | **Plano corrigido:** Web Mercator, safra 2026/2027 e parada do treino |
| [`../sicor/`](../sicor/) | Os três scripts do SICOR e o `resumo.json`, já publicados antes deste material | **Descartado:** o código de integração não serviu como rótulo |

A frente dos **artigos** não está neste material: ela foi a única com acervo aproveitável e tem site próprio na raiz do repositório (`../../index.html`), com os dados completos em `../../dados-completos/`.

## O que não foi publicado e por quê

### Amostras da equipe do LAPIG

A regra 1 do briefing é explícita: nada de amostras da equipe. Ficaram de fora, por conter coordenadas, identificadores ou fichas de amostras da equipe:

- `samples_iCLS.csv`, `registros_ensino.gpkg`, `amostras_ilpf_inspecionadas_4326.gpkg` e `pontos_integrado_final_v2.gpkg`;
- `divisao_ensino_medicao.csv`, `pontos_fila_cega.csv`, `pontos_reserva_cega.csv` e o gabarito da auditoria (`auditoria_gabarito/`);
- a régua (`regua/`, `respostas_regua.json` e `regua_gabarito.json`) — o briefing a trata como material de amostra da equipe, embora o código mostre que as 50 fichas vieram de candidatas do detector (ver a dúvida no fim deste texto);
- `curvas-evi2/curvas_evi2_39.csv`, `curvas-evi2/cobertura_39.csv`, `validacao_20.csv`, `validacao_resumo.csv` e `conferencia_6.png`;
- `medicao_tabela.csv`, `medicao_probabilidades.csv`, `medicao_avaliacao.json` e o resultado do classificador por talhão da equipe;
- as fichas de exemplo de amostras da equipe e as 58 fichas conhecidas de `fichas/`;
- os recortes de 2 m centrados nos talhões da equipe (`classificador/recortes/`), os 1.360 recortes da auditoria e os PNGs do mapa da equipe.

Os scripts que leem esses arquivos foram publicados: eles não contêm os dados, só o código. Onde o resultado era agregado (contagens, métricas, matrizes), ele foi publicado sem identificadores.

### Imagens do Google

Nenhuma imagem do Google foi publicada. As duas fichas de exemplo são CBERS-4A de 2 m (INPE, coleção aberta) com a série de NDVI do Sentinel-2. O site dos artigos usa imagens de satélite de terceiros para conferência, mas isso está fora deste material e não foi copiado para cá.

### Fichas e leituras brutas, por tamanho

- **Fichas:** 555 PNGs, **0,96 GB** (cerca de 1 GB), em `fichas/`. Inclui as 58 fichas conhecidas e as fichas dos candidatos. Fora do material pelo tamanho e, no caso das 58, pela regra 1.
- **Leituras brutas:** 2.402 arquivos, **2,06 GB** (cerca de 2,1 GB), em `leitura/`. São lotes, respostas por ficha, saídas de modelo e imagens de apoio. O que importa está agregado nos CSV e JSONs de cada frente.
- **Fichas-IA:** 2.963 arquivos, **610 MB**, em `fichas-ia/` (formatos f1/f2 do teste de ficha). Não publicadas pelo tamanho e por serem derivadas de talhões da equipe.
- **Recortes da auditoria:** 1.360 JPEGs, **172 MB**, em `auditoria/tela/recortes/`. Não publicados pela regra 1 e pelo tamanho.

### Pesos do DINOv2

O classificador usa o **DINOv2 base `vit_base_patch14_dinov2.lvd142m`**, com pesos públicos obtidos pelo `timm`, entrada de 448 × 448 px e 8 transformações dihedral. O nome exato está em `classificacao/resultados/config.json` e em `classificacao/codigo/modelo_util.py`. Os pesos do backbone **não foram copiados**: são um download público e grande, e qualquer pessoa os obtém com `timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True)`.

A cabeça logística treinada (`cabeca.npz`, 37 KB) também não foi publicada. Ela não tem coordenadas nem identificadores, mas foi ajustada nos 856 recortes das amostras da equipe; por cautela, ficou de fora. O `config.json` e o código permitem reconstruir a arquitetura, o limiar e a regra de decisão, mas não os pesos da cabeça.

### Logs, rascunhos e guias

Não foram publicados os rascunhos para a equipe, o guia de trabalho interno, os `log_*.txt`, os `*.jsonl` de sessão, os pedidos internos de trabalho e os arquivos de credencial. Também não há e-mails, tokens ou nomes de pessoas que não sejam autores publicados.

### Caminhos e projeto do Earth Engine

Todos os caminhos absolutos do Windows foram trocados por variáveis no topo dos scripts: `ILPF_RAIZ`, `ILPF_SICOR`, `ILPF_AMOSTRAS`, `ILPF_MAPA_DADOS`, `ILPF_AUDITORIA`, `ILPF_TILES`, `ILPF_GPKG`, `ILPF_SCRIPTS`, `ILPF_ALVOS`, `ILPF_LEITURA` e `EE_PROJETO`. O identificador do projeto do Earth Engine foi trocado por `"SEU-PROJETO"`. A lógica dos programas não mudou; só os caminhos e o projeto.

## Exemplo comentado: da candidata F0284 à curva EVI2

Este é o percurso completo de **uma** candidata do detector, do candidato bruto à curva de EVI2. Ela é uma **candidata**, não uma amostra confirmada. O objetivo é mostrar como as peças se encaixam e o que cada uma prova — e o que não prova.

### 1. O candidato

A varredura do detector no tile `22KGE_2` marcou uma região de **8,95 ha**, centrada em **-48,510647, -18.283210**, na imagem CBERS-4A de **17/08/2025**. O detector mediu **25,6 m** de espaçamento entre as fileiras. A região entrou no grupo `listras` e ganhou a ficha `F0284.png`.

O polígono e a linha da tabela estão em [`detector-de-renques/resultados/amostras_renques_candidatas.csv`](detector-de-renques/resultados/amostras_renques_candidatas.csv) e no `.geojson` ao lado. A coordenada é de uma candidata nossa; a regra 2 do briefing permite publicá-la.

### 2. A ficha

A ficha está em [`detector-de-renques/exemplo/F0284.png`](detector-de-renques/exemplo/F0284.png). Ela tem três quadros:

- **A, contexto:** imagem CBERS-4A de 2 m, quadro de 1.300 m de lado, norte para cima. O contorno amarelo é a área avaliada; o quadrado ciano mostra onde fica o detalhe B.
- **B, detalhe:** quadro de 500 m de lado no centro da área, na resolução original de 2 m. É onde se veem as fileiras.
- **C, série:** NDVI do Sentinel-2 a cada 15 dias, de julho de 2020 a outubro de 2025, média dentro do contorno. As faixas azuis são a estação chuvosa (outubro a março).

Na ficha, o detalhe B mostra **fileiras escuras paralelas de árvores adultas**, acompanhando a curva de nível, com pasto claro entre elas. O contorno amarelo pega parte do conjunto; há fileiras logo fora dele. É exatamente o tipo de alvo que o detector foi escrito para achar.

### 3. A leitura da IA

A primeira leitura (Gemini 3.8 Flash, esforço alto) respondeu:

- `renques_de_arvores`: **sim**;
- `classe`: **IPF**;
- `confianca`: **0,9**;
- `espacamento_renques_m`: **40**;
- `fracao_da_area_com_renques`: **0,75**;
- `contorno_cobre_os_renques`: **em parte**;
- `arvores`: **adultas**;
- `motivo`: *"Renques paralelos de árvores adultas em curva de nível sobre relevo ondulado com pasto entre eles e série de NDVI típica de pastagem perene."*

### 4. A nota da segunda leitura

A segunda leitura, cética, deu **nota A** (nítido), com **6 fileiras contadas** e **30 m** de espaçamento; confirmou pasto entre as fileiras, série sem lavoura e renques parte dentro e parte fora do contorno. Não houve dúvida registrada. A nota A é o que colocou a F0284 entre as 39 aprovadas; não é confirmação de campo.

### 5. A curva de EVI2

A curva de 13 meses da safra 2024/2025 está em [`curvas-evi2/resultados/evi2_F0284.csv`](curvas-evi2/resultados/evi2_F0284.csv). Os valores são:

| Mês | Out | Nov | Dez | Jan | Fev | Mar | Abr | Mai | Jun | Jul | Ago | Set | Out+1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EVI2 | 0,160 | 0,376 | 0,352 | 0,368 | 0,370 | 0,239 | 0,224 | 0,253 | 0,196 | 0,163 | 0,144 | 0,145 | 0,276 |

Não houve mês interpolado nesta candidata. A curva sobe de outubro a fevereiro, cai em março e fica baixa na seca; é uma curva sazonal de pasto, não o patamar alto e estável que se esperaria de um dossel fechado. Na maior parte do ano ela fica abaixo da mediana de IPF e próxima da mediana de Pastagem; em novembro e no fim da seca, supera a Pastagem. Isso é coerente com **pasto com árvores em fileiras**, mas **não prova** a classe: a curva é descritiva e a classe é palpite da IA. O que mostra o renque é a imagem de 2 m, não a curva.

O gráfico com as 39 curvas está em [`curvas-evi2/exemplo/evi2_candidatas.png`](curvas-evi2/exemplo/evi2_candidatas.png). A F0284 é uma das linhas azuis finas; o gráfico não destaca uma curva individual.

### 6. O que este exemplo prova — e o que não prova

**Prova:** que o detector achou uma região com fileiras visíveis; que a ficha mostra as fileiras em 2 m; que a leitura da IA viu o que está na ficha; que a segunda leitura deu nota A; e que a curva de EVI2 pode ser calculada para a candidata com o método da equipe.

**Não prova:** que a área seja IPF de verdade, que o produtor a declare como integração, que o polígono seja o talhão inteiro ou que a candidata sirva como amostra de treino. Falta a inspeção de um inspetor do laboratório, e é isso que separa "candidata" de "amostra".

## Convenções deste material

- Todos os caminhos são relativos a esta pasta ou à raiz do experimento. Os scripts aceitam as variáveis de ambiente listadas acima; sem elas, valem os padrões da pasta de trabalho original.
- Os CSV usam vírgula ou ponto e vírgula, conforme o arquivo; o separador está indicado no LEIA-ME de cada frente. Todos os textos estão em UTF-8.
- As datas são as do experimento (novembro de 2026). "Safra 2024/2025" quer dizer outubro de 2024 a outubro de 2025.
- "Renque" é a fileira de árvores plantadas com pasto ou lavoura entre as fileiras; "candidata" é uma região que passou pelos filtros e pela leitura da IA, mas não foi confirmada por pessoa; "amostra" é o que passou pela inspeção.
- O material não substitui o resumo principal (`../LEIA-ME.md`) nem os dados completos do site dos artigos. Ele é o material leve dos testes, para outro pesquisador entender e reaproveitar o que foi feito.
- O material inteiro tem cerca de **4,4 MB**, sem nenhum arquivo acima de 5 MB.

## Uma dúvida registrada

O briefing diz que a régua (`regua/`) usa fichas de amostras da equipe e manda excluí-la. O código `16_regua.py`, porém, monta a régua com o grupo `listras` de `alvos.json` — as 100 regiões já lidas do detector, que são candidatas nossas, não amostras da equipe. Excluí a régua e o `respostas_regua.json` de qualquer forma, para seguir a regra 1, mas registro a divergência: se a régua for mesmo de candidatas, ela poderia ser publicada sem as coordenadas, e o número de 50 fichas marcadas por pessoa ficaria verificável.

## Fonte

`../LEIA-ME.md` (resumo principal), `DIARIO.md`, `BALANCO.md`, `PROXIMA-ETAPA.md` e os relatórios de cada frente. Os números deste material são os do resumo principal; onde o relatório interno divergiu, o resumo principal prevaleceu.
