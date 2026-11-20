# Auditoria do mapa e tela de inspeção: pronta, não lida

**Frente:** auditoria piloto do mapa da equipe e protótipo de tela de inspeção cega. **Data:** 12 e 13/11/2026.

## O que foi testado

A equipe publicou em 09/11/2026 a versão 1.0 do mapa da TempCNN para a área piloto (26 tiles do Cerrado goiano, 4,52 milhões de hectares, safra 2024/2025). A auditoria faz uma pergunta só:

> **Dos lugares que o mapa chama de IPF (pecuária com floresta), quantos têm de fato árvores plantadas em fileiras na safra 2024/2025?**

É uma **auditoria piloto**, com 100 pontos sorteados. Não é uma validação do mapa; diz se vale a pena a equipe olhar o assunto com os inspetores dela.

O desenho foi gravado antes de ver qualquer imagem: 100 pixels sorteados com chance igual entre os 2,37 milhões de pixels de IPF da imagem publicada, 15 controles com árvores e 20 sem árvores (talhões do grupo de ensino), 15 repetições escondidas e 30 pontos de reserva. A inspeção é cega: a fila só tem identificador e coordenada, e o gabarito fica à parte. O protocolo tem seis respostas (renque, plantio fechado, árvores espalhadas, vegetação nativa, sem árvores, não dá para dizer) e uma definição de renque com cinco critérios: fileiras paralelas, pelo menos 3, faixa aberta de 10 a 50 m, conjunto de 1,5 ha ou mais e ponto dentro do conjunto.

O desenho foi revisado por quatro IAs (Gemini 4 Hydrogen, DeepSeek v4.1, Kimi K3.1 Pro e Claude Fable 5.2) antes de qualquer imagem.

## Resultado

**Em resumo:** 100 pontos de IPF, 35 controles e 15 repetições prontos; 148 dos 150 pontos têm imagem de 2024 e 2025; a leitura por IA não foi feita. A frente é inconclusiva.

**A frente é inconclusiva: a estrutura está pronta, mas a leitura por IA não foi feita e não há resultado para contar.**

- Estão prontos: o protocolo, o sorteio, a fila cega de 150 pontos, os 30 de reserva, o gabarito fechado, 1.360 recortes de 2 m em 600 m e 1.500 m de lado (estação seca de 2023 a 2026, 172 MB) e a tela de inspeção testada. **148 dos 150 pontos têm imagem de 2024 e 2025**; dois têm só 2025.
- Falta: a leitura dos 150 pontos por IA, prevista para depois de 14/11, e a leitura de um inspetor da equipe. O gabarito estava fechado na última anotação.
- Os sinais que motivaram a auditoria são **preliminares e não devem ser lidos como conclusão**. O mapa atribui 394 mil ha (8,7% da área) a classes com árvores integradas: IPF 179 mil, ILPF 143 mil, Agrofloresta 60 mil e ILF 12 mil. Do "IPF" do mapa, **26%** cai onde o MapBiomas publicado não mostra uso agropecuário, 46% em pastagem, 13% em mosaico, 8% em agricultura e 7% em floresta plantada. Nas 39 áreas do detector, 32 têm pixel no mapa: em 14 a classe majoritária é Pastagem; 13 têm maioria de classes com árvore e 13 têm menos de 10% de árvore. Dos 100 pontos de IPF sorteados, 93 são de borda.
- A primeira conta, sem tratar a projeção Web Mercator das imagens, dava 33% do IPF fora do uso agropecuário e 30 das 39 áreas com pixel; a corrigida deu 26% e 32. O mapa dá a cada pixel a classe mais provável entre nove, sem classe de vegetação nativa, sem máscara e sem opção de rejeitar.

**Conclusão, coerente com o resumo principal:** a auditoria está pronta para rodar, mas não produziu número. O que existe são indícios sobre o mapa, não uma conclusão de que ele erra.

## Como rodar

O sorteio foi feito com semente fixa 20261112. A raiz é lida de `ILPF_RAIZ`; a pasta das imagens do mapa, de `ILPF_MAPA_DADOS`; a cópia do repositório da equipe, de `ILPF_SICOR_REPO`; a pasta das amostras, de `ILPF_AMOSTRAS`; a saída, de `ILPF_AUDITORIA`.

```bash
export ILPF_RAIZ=/caminho/ilpf-exp
export ILPF_MAPA_DADOS=/caminho/mapa_equipe/dados
export ILPF_SICOR_REPO=/caminho/ilpf-sicor/repo
export ILPF_AMOSTRAS=/caminho/ilpf-amostras

python 01_sortear.py
```

O script lê os PNGs do mapa, os manifestos de 30 m e 75 m, `divisao_ensino_medicao.csv`, `amostras_ilpf_inspecionadas_4326.gpkg` e `amostras_renques_candidatas.gpkg`. Grava `gabarito_NAO_ABRIR.csv`, `pontos_fila_cega.csv` e `pontos_reserva_cega.csv` na pasta de auditoria.

Dependências: Python 3.10+, `numpy`, `pandas`, `geopandas`, `Pillow` e `shapely`. A tela é HTML estático e não precisa de servidor.

**Entradas que não estão publicadas e por quê:**

- `pontos_fila_cega.csv`, `pontos_reserva_cega.csv` e `gabarito_NAO_ABRIR.csv`: a regra 1 do briefing exclui a fila cega e o gabarito, porque os pontos vêm do mapa e dos talhões da equipe. O desenho está em `resultados/desenho_auditoria.json`, sem coordenadas.
- `amostras_ilpf_inspecionadas_4326.gpkg` e `divisao_ensino_medicao.csv`: amostras da equipe, com nomes e identificadores. Não publicados.
- `recortes/`: 1.360 JPEGs de 2 m, 172 MB. São imagens de pontos do mapa e de talhões da equipe; a regra 1 e a regra 3 mandam excluir. Além disso, o tamanho passa do limite.
- `mapa_equipe/dados`: os PNGs do mapa publicado, 33 MB, e as estatísticas por classe. Não são amostras, mas são o objeto auditado; não foram republicados para não duplicar o repositório da equipe.
- O código da tela (`baixar_recortes.py`, `analisar_recortes.py`, `verificar_recortes.py`, `inspecao.html`, `tvi.html`, `tvi.css`, `tvi.js`, `dados.js`): não está neste material. O que existe aqui é o protocolo e o registro do que foi construído e conferido.
- `pontos_integrado_final_v2.gpkg`: tem nomes de pessoas e não vai para nenhuma IA, conforme a regra do próprio protocolo.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `PROTOCOLO.md` | A pergunta, a definição de renque, as seis respostas, o sorteio e a regra de contagem, gravados antes de ver imagem. |
| `RELATORIO-tela.md` | O que a tela de inspeção simples entrega, como os recortes foram feitos, cobertura, conferências e limitações. |
| `TELA-TVI.md` | Manual do protótipo de tela com a aparência do TVI (não é o TVI oficial). |
| `codigo/01_sortear.py` | Sorteio dos 100 pixels de IPF, dos 35 controles, das 15 repetições e dos 30 reservas, com semente fixa. |
| `resultados/desenho_auditoria.json` | Área do mapa por classe, contagens do sorteio, quebra do MapBiomas nos 100, borda, cobertura e tamanho das imagens. Sem coordenadas. |

## Limites

- **100 pontos dão um intervalo largo:** se 30 forem renque, o intervalo vai de cerca de 21 a 40.
- A auditoria olha só a classe IPF e só "tem ou não tem fileiras de árvores". Não diz nada sobre ILP, que não se vê numa imagem de uma data.
- A leitura por IA deixa passar renques: nas calibrações, os modelos viram 9 de 18 áreas com árvores e não inventaram nenhuma em 40. A IA tende a contar renques **de menos**; os 35 controles medem quanto.
- O ponto é um pixel de 30 m, e 93 dos 100 estão em borda. Um renque pode estar ao lado do ponto e não nele; a regra conta só o que está no ponto.
- A fonte é a imagem de visualização do mapa (PNG de 30 m), não o dado original da equipe.
- O "transparente" do MapBiomas publicado foi lido como "fora de uso agropecuário" sem conferir a legenda.
- Não há exemplo de imagem nesta frente: os recortes são de pontos do mapa e de talhões da equipe, e a regra 1 e a regra 3 do briefing mandam excluir.

## Fonte

`auditoria-mapa/LEIA-ME.md`, `auditoria-mapa/PROTOCOLO.md`, `auditoria-mapa/RELATORIO-tela.md`, `tela-tvi/LEIA-ME.md`, `DIARIO.md` (seções 225–246 e 261), `BALANCO.md` (Frente C). Os relatórios internos completos não estão neste repositório.
