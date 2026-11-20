# Pedido de análise crítica independente

> **Nota de publicação.** Este é o pedido original de 12/11/2026. Os arquivos internos citados (`DIARIO.md`, `ANALISE-CAMINHOS.md`, `RELATORIO-classificador.md`, `RELATORIO-curvas.md`, `LEIA-ME-artigos.md` e `codigo-publico-equipe/`) não estão publicados; o essencial está no `../LEIA-ME.md` desta frente e no resumo principal.


Você é um revisor externo. Leia este arquivo e os outros desta pasta e dê uma opinião crítica e franca. Responda em português, em texto, na própria resposta. **Não crie, altere nem apague arquivos. Não leia nada fora desta pasta. Não rode treinos nem baixe dados.**

## Situação
Um laboratório (LAPIG/UFG) mapeia sistemas integrados de produção (ILP, IPF, ILF, ILPF, SAF) numa área piloto de 26 tiles no Cerrado goiano (4,52 Mha, safra 2024/2025) com uma TempCNN que classifica a curva anual de EVI2 (13 medianas mensais do Sentinel-2) em 9 classes. Em paralelo, e por conta própria, um pesquisador do laboratório experimenta usar IA para gerar amostras e quer que o resultado seja um bom exemplo de uso de IA: inovador, útil, justificável. Ele só mostrará à equipe se houver contribuição concreta.

## Arquivos desta pasta
- `DIARIO.md`: história completa e números (a última seção é a olhada no mapa da equipe).
- `ANALISE-CAMINHOS.md`: análise de caminhos feita antes da olhada no mapa.
- `RELATORIO-classificador.md`: classificador de imagem de 2 m (DINOv2 congelado + regressão logística).
- `RELATORIO-curvas.md`: reprodução do método de EVI2 da equipe.
- `LEIA-ME-artigos.md`: coleta de locais a partir de artigos e teses.
- `codigo-publico-equipe/`: scripts públicos da TempCNN da equipe (`repo_03.py` pré-treino, `repo_04.py` ajuste fino, `repo_05.py` classificação) e a página de metodologia.
- `cruzar.py`, `nas39.py`: as duas contas rápidas feitas sobre o mapa publicado.

## Resumo do que se sabe
1. Base da equipe: 242 talhões (polígonos) × safras = 1.267 registros, quase todos em Goiás (93 talhões dentro dos tiles), mais 212 pontos × 4 anos em outros 8 estados. Por classe (talhões): ILP 112, IPF 36, ILPF 4, ILF 4, SAF 0.
2. Coleta: crédito rural (SICOR) descartado (0 de 74 glebas do piloto batiam); semelhança por embeddings descartada (1 em 100); artigos renderam 5 regiões aprovadas, todas fora dos tiles, com a classe escrita no texto.
3. Leitura de imagem por modelos de linguagem (Gemini, DeepSeek): 0 falsos "tem renque" em 40; veem só 9 de 18 áreas com árvores; não acertam a classe; ILP não é reconhecível.
4. Esteira (detector de fileiras feito à mão + persistência entre anos + duas leituras): 39 áreas candidatas (33 IPF, 6 ILF por palpite da IA), 1.109 ha, não confirmadas pela equipe.
5. Classificador de recortes de 2 m: treinado em 164 talhões (28 com árvores), medido uma vez em 77 separados por blocos espaciais: 7 de 8 talhões com árvores dentro dos tiles (8 de 13 no total), 6 falsos em 61.
6. Mapa publicado da equipe (v1.0, 09/11/2026): classes com árvores integradas somam 394 mil ha (8,7% da área); ILP 24,3%. O mapa não tem classe de vegetação nativa. Cruzando com o MapBiomas 2025 publicado pela própria equipe, um terço do "IPF" cai onde o MapBiomas não mostra uso agropecuário. Nas 30 das nossas 39 áreas que têm mapa, a classe majoritária é Pastagem em 15 e alguma classe com árvores em cerca de 10. Contas preliminares, com as ressalvas do diário.
7. O script público da equipe separa treino e teste por linha (o mesmo talhão em safras diferentes cai dos dois lados) e usa o teste para a parada antecipada. Os pesos e a configuração da TempCNN não estão públicos.

## Plano em discussão (três caminhos ligados)
1. **Auditar o mapa da equipe**: conferir legendas e alinhamento, sortear pontos que o mapa chama de IPF/ILPF/SAF/ILF, passar o classificador de imagem de 2 m, e uma pessoa confere uma parte sorteada numa tela própria (estilo TVI, com imagens históricas de alta resolução do Esri Wayback). Resultado: "de cada 100 ha mapeados como IPF, tantos têm árvores plantadas", e indicação de que amostras faltam (talvez vegetação nativa como classe negativa).
2. **Classificador mais robusto**: mais negativos (mata nativa, mata ciliar, silvicultura, pomar, via MapBiomas), mais positivos confirmados, mais casos de medição.
3. **Artigos**: achar pelo nome (SIGEF/INCRA, OpenStreetMap, busca manual) as fazendas citadas sem coordenada, para amostras de ILPF e SAF com classe escrita por pesquisador. Trabalho manual do pesquisador com o DeepSeek.
Em todos, uma parte sorteada é conferida por humano para quebrar o círculo "IA escolhe, IA confirma".

## O que queremos de você
1. O raciocínio se sustenta? Onde há erro de lógica, de estatística ou conclusão maior que a evidência? Seja específico (cite o arquivo).
2. A leitura do mapa da equipe (item 6) é sólida? Que explicações alternativas existem e como conferir antes de afirmar algo?
3. O plano dos três caminhos é o melhor uso do que já existe? O que você cortaria, mudaria de ordem ou acrescentaria?
4. Há um caminho mais inovador e ainda justificável que não estamos vendo (por exemplo, com mais uso de GPU no Colab ou de modelos de visão)? Diga custo e risco.
5. Como garantir, de forma defensável, que uma amostra gerada com ajuda de IA é boa o bastante para treinar ou validar o modelo?
6. Qual seria, na sua opinião, o resultado final mais convincente para mostrar à equipe?

Limite: até cerca de 900 palavras. Aponte o que é fato conferido por você nos arquivos e o que é opinião.
