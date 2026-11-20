# Plano revisado (12/11/2026, depois das três opiniões) — pedido de revisão

> **Nota de publicação.** Este é o pedido de revisão do plano revisado, de 12/11/2026. `CONTEXTO.md`, `DIARIO.md` e as demais pastas citadas não estão publicadas; o pedido original está em `PEDIDO.md` e as três opiniões estão nesta pasta.


Você é um revisor independente. Leia `CONTEXTO.md` (situação e pedido original), este arquivo, as três opiniões em `opinioes/` e o que precisar dos demais arquivos (o `DIARIO.md` desta pasta já traz, no fim, as correções da conta do mapa). **Não crie, altere nem apague arquivos; não leia fora desta pasta; não rode programas.** Responda em português, em texto, até cerca de 900 palavras, separando o que você conferiu nos arquivos do que é opinião.

## Restrições do pesquisador (não negociáveis por ora)
- Trabalho paralelo e individual: ele **não quer envolver a equipe** (nem criar campanha no TVI deles) antes de ter resultado bom. A inspeção humana disponível é a dele (um inspetor, não especialista em inspeção visual), numa tela própria no estilo do TVI.
- Quer um exemplo de uso de IA que seja inovador, útil e justificável; gosta da ideia de usar bastante IA e GPU do Colab, mas só se fizer sentido.
- Cotas: assinaturas com limite semanal; Colab com 599 unidades; ele não lê código.

## O que mudou depois das opiniões
- Conta do mapa corrigida para Web Mercator: 26% do "IPF" cai onde o MapBiomas publicado não mostra uso agropecuário; das 39 áreas, 32 têm pixel, 14 com Pastagem majoritária, 13 com ≥50% em classes com árvores, 13 com <10%.
- Conferido em `repo_05.py`: classe por argmax entre nove, sem máscara de vegetação nativa nem rejeição; há raster de confiança; três modos (pixel, segmento, grupos temporais).
- Aceito das opiniões: teste da TempCNN só depois de confirmação humana; classificador é ordenador, não juiz; rótulo atual é "árvore", não "renque"; artigos sem ampliar.

## Plano revisado
1. Definir por escrito o que é renque e o que conta como amostra boa (critérios de aceitação).
2. Conferências sem custo do mapa: dado original em vez do PNG, legenda do MapBiomas publicado, por que 7 das 39 áreas não têm pixel.
3. Tela própria de inspeção (estilo TVI): imagens de alta resolução de várias datas (Esri Wayback), série temporal, sem mostrar a resposta da IA.
4. O pesquisador inspeciona 100 a 150 pontos sorteados: as 39, pontos que o mapa chama de IPF/ILPF/Agrofloresta/ILF, e controles (mata nativa, silvicultura, pastagem).
5. Só então: classificador novo (mais negativos, definição de renque, talvez cabeça que use a grade de patches do DINOv2) e teste da TempCNN com e sem as amostras confirmadas, com separação por talhão e bloco.
6. Artigos: fechar as 5 a 7 regiões já achadas, sem ampliar.

## O que queremos de você
1. O plano revisado é o melhor uso do que existe, dadas as restrições? O que está errado, fora de ordem ou faltando?
2. As três opiniões têm algum erro, ou algum ponto bom que o plano ignorou?
3. Um inspetor só, não especialista, e que é o autor do trabalho: quanto isso enfraquece o resultado e como mitigar sem envolver a equipe?
4. O desenho da amostragem do passo 4 (quantos pontos, de quais estratos, como sortear) para que o número final "de cada 100 ha mapeados como IPF, tantos têm árvores plantadas" seja defensável. Seja concreto.
5. Qual é o menor resultado que já valeria mostrar à equipe, e qual a ordem para chegar nele gastando pouco?
6. Algo neste plano é "bobinho" ou, ao contrário, ambicioso demais para um pesquisador sozinho?
