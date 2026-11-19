# Testes exploratórios de amostras de ILPF por IA: resumo

Entre 11 e 15 de novembro de 2026, o experimento testou caminhos para gerar amostras de sistemas integrados de produção para o mapa do LAPIG/Rede ILPF: 26 tiles do Cerrado goiano, 4,52 milhões de hectares, safra 2024/2025. Quase tudo foi teste exploratório e não produziu amostra aproveitável. Nenhuma amostra de ILPF foi confirmada por inspetor do laboratório e nada foi enviado à equipe. A única frente com resultado real para amostras foi a extração de coordenadas de artigos: um acervo público com 588 documentos lidos e 458 coordenadas classificadas; dos 230 pontos A/B, 43 foram confirmados na imagem, 139 ficaram incertos e 48 não conferem. Esses 43 são coordenadas confirmadas na imagem, não amostras de campo.

Os sistemas citados no texto são ILP (lavoura com pecuária), IPF (pecuária com floresta), ILF (lavoura com floresta), ILPF (os três) e SAF (agrofloresta). "Tile" é cada quadrado de imagem que cobre a área piloto. "Renque" é a fileira de árvores plantadas, com pasto ou lavoura entre uma fileira e outra; é a marca visível de IPF, ILF e ILPF em imagem de 2 m.

| Frente | O que testamos | O que deu | Conclusão |
|---|---|---|---|
| **SICOR (crédito rural)** | Microdados de 2013 a 2026 do Banco Central; código de integração e subprogramas; polígonos das glebas financiadas | 48.561 glebas no Brasil, 81 na área piloto e 338 em Goiás; 74 fichas lidas pelo Gemini, nenhuma batia com o código declarado | **Descartado** |
| **Inspeção de imagem por IA** | Gemini 3.8 Flash (esforço médio e alto), Gemini 4 Hydrogen (alto e xhigh) e DeepSeek v4.1 Flash lendo 58 fichas com imagem CBERS-4A de 2 m e série de NDVI do Sentinel-2 | No máximo 9 das 18 fichas com árvores foram vistas; 0 falso em 40 no conjunto (0 em 37 para o 3.8 alto, que leu 55 das 58 fichas); o Hydrogen alto gastou cerca de 10 mil tokens por ficha e leu as 58 em 6,4 min; na régua de 50 fichas, 24 ficaram em "não dá para dizer" | **Resultado:** a IA confere, não acha |
| **Semelhança por embedding (AlphaEarth)** | Busca de lugares parecidos com amostras de IPF e de ILP nos embeddings anuais | 1 renque em 50 candidatos de IPF; 0 em 50 de ILP | **Descartado** |
| **Detector de fileiras (varredura)** | Detector de textura periódica em CBERS-4A de 2 m; 26 tiles; filtros de espaçamento maior ou igual a 12 m e área maior ou igual a 1,5 ha; persistência em 2023 ou 2026; duas leituras por IA | Cerca de 970 regiões candidatas (26.755 ha); 249 fichas lidas; 45 "sim" + 1 "incerto" = 46 relidas; 39 aprovadas (38 A, 1 B), 1.109 ha, 26 locais em 14 tiles; 7 rejeitadas, que não entraram no pacote; marcou 2 dos 17 talhões com árvores já conhecidos | **Resultado parcial:** candidatas, não confirmadas |
| **Classificação (classificador, EVI2 e TempCNN)** | Classificador DINOv2 com 856 recortes de 2 m; reprodução das curvas de EVI2 da equipe; 40 treinos da TempCNN com quatro formas de separar os dados | 7 de 8 talhões com árvores nos tiles (o detector: 0 de 8); 6 falsos em 61; curvas com diferença média de 3,7 × 10⁻⁸ e maior diferença de 9,5 × 10⁻⁶; 58,2% na receita reimplementada e 52,2% com validação separada | **Resultado técnico**, sem amostra confirmada |
| **Auditoria do mapa / tela TVI** | 100 pixels que o mapa chama de IPF, 35 controles e 15 repetições; protocolo cego; tela de inspeção; 1.360 recortes de 2 m | 148 dos 150 pontos têm imagem de 2024 e 2025; a leitura por IA não foi feita; não há resultado registrado | **Inconclusivo** |
| **Artigos** | Busca no OpenAlex; extração da coordenada com trecho literal; conferência por programa e por imagem; site público | 588 documentos com texto lido; 458 coordenadas (125 A, 105 B, 228 C); dos 230 pontos A/B, 43 confirmados na imagem, 139 incertos e 48 que não conferem | **Resultado:** a única frente com acervo aproveitável |

A, B e C são níveis de confiança da coordenada, não classes de uso do solo. A definição está na seção dos artigos.

Fonte: DIARIO.md; BALANCO.md; PROXIMA-ETAPA.md; medicao-3-detector-de-renques/resumo_entrega.json; medicao-4-classificador/RELATORIO.md; auditoria-mapa/LEIA-ME.md; RESULTADO.md.

**Nota sobre as fontes.** Os relatórios internos citados como "Fonte" no fim de cada seção (`DIARIO.md`, `BALANCO.md`, `PROXIMA-ETAPA.md`, os relatórios do detector, do classificador, das curvas EVI2, da auditoria, do teste de separação e da rota dos artigos, entre outros) não estão neste repositório. O que está publicado é este resumo, a exportação de `dados-completos/` e os três scripts do SICOR em `sicor/`, com o `sicor/resumo.json`. Os números deste resumo vêm desses relatórios internos e não podem ser refeitos só com o que está aqui.

## SICOR: o código de integração não serviu como rótulo

**De onde vieram os dados.** O SICOR é a base de crédito rural do Banco Central. O experimento baixou os microdados de operações e de glebas de 2013 a 2026, direto do site do Banco Central. A base tem duas partes que importam aqui: uma linha por operação de crédito, com o código de integração, o programa, o subprograma, a finalidade e o produto; e uma linha por gleba, com o polígono em WKT. O código de integração usado foi o campo `CD_TIPO_INTGR_CONSOR`, com cinco valores: 3 ILP, 4 SAF, 5 ILPF, 6 ILF e 7 IPF.

**Como filtramos.** O trabalho ficou em três scripts, copiados em `testes-exploratorios/sicor/`.

- **`01_filtrar_sicor.py`** lê os arquivos anuais do Banco Central sem guardar o bruto. Guarda só as operações com um dos cinco códigos de integração ou com subprograma cuja descrição casa com "integração", "integ lav" ou "agroflorest". Também guarda as glebas dessas operações. Os quatro subprogramas encontrados foram: Crédito Investimento em Sistemas Agroflorestais (Pronaf Floresta), ABC+ Integração, Integração Lavoura-Pecuária-Floresta (encerrado) e RenovAgro Integração. O script grava `ops_integracao.csv`, `glebas_integracao.csv` e um resumo por ano, UF e código.
- **`02_cruzar.py`** lê os 26 tiles do repositório público da equipe, a tabela de empreendimentos, as operações e as glebas. Corrige geometrias inválidas, calcula área em hectares numa projeção equivalente e resume por classe: número de glebas, operações, locais distintos, área distinta, mediana e percentis de área, safras, produtos e finalidade. Depois cruza as glebas com os centroides das amostras atuais do LAPIG e com os tiles. Grava `glebas_piloto.geojson`, `glebas_piloto.csv`, `glebas_goias.geojson`, `glebas_goias.csv` e `resumo.json`.
- **`03_detalhes.py`** não baixa nem cruza nada. Lê o `resumo.json` e os CSV de operações e glebas gerados pelo script 01 e imprime, para conferência, o detalhamento de Goiás por classe, o total do piloto, a cobertura de gleba por período, o cruzamento com as amostras e a concentração nacional por UF, ano e banco.

Os três calculam a raiz a partir do caminho do próprio arquivo, com `__file__`. Não há caminho absoluto do Windows neles; por isso a cópia em `testes-exploratorios/sicor/` mantém a lógica sem alteração. Eles não rodam só com o que está no repositório: o `01_filtrar_sicor.py` precisa da pasta `dominio/` (tabelas do Banco Central) e grava em `dados/`; o `02_cruzar.py` precisa de `dados/`, `dominio/` e `repo/` (tiles e amostras da equipe); o `03_detalhes.py` lê o `saida/resumo.json` produzido pelo 02 e os CSV de `dados/`. Nenhuma dessas pastas está publicada. O `resumo.json` desta pasta é uma cópia do resultado do 02, para consulta.

**Quanto havia.** No Brasil, o filtro guardou 71.764 operações de interesse. Dessas, 28.988 tinham gleba; o restante ficou sem polígono. Depois de descartar 252 geometrias inválidas ou vazias, sobraram 48.561 glebas válidas, assim distribuídas:

| Classe no SICOR | Glebas no Brasil |
|---|---:|
| ILP | 10.710 |
| ILPF | 14.114 |
| Sem código (só subprograma) | 21.396 |
| SAF | 1.985 |
| ILF | 227 |
| IPF | 129 |
| **Total** | **48.561** |

Em Goiás, o recorte por UF ficou com 338 glebas: 226 sem código, 54 ILPF, 33 ILP e 25 SAF. Não há ILF nem IPF nesse recorte. Na área piloto, isto é, nas glebas cujo ponto representativo cai dentro da união dos 26 tiles, ficaram 81 glebas e 45 operações: 30 sem código, 26 ILPF, 13 SAF, 8 ILP e 4 ILF. As glebas de ILPF do piloto somam 4.121 ha distintos, com mediana de 100 ha; as de SAF, 1.638 ha; as de ILP, 934 ha; as de ILF, 73 ha.

**O que a base mostra fora do piloto.** Em Goiás, 480 operações têm algum código de integração nos 14 anos, mas só 66 têm polígono; antes de 2019, nenhuma tem. No Brasil, 90% das glebas de ILPF vêm de um único banco e se concentram em PA, TO e RO. No ILP, 7.892 das 10.713 glebas do país estão no Rio Grande do Sul, espalhadas por muitos bancos — coerente com soja e pasto de inverno. As contagens de Goiás estão no `resumo.json`; as de banco e UF saem do `03_detalhes.py` sobre os CSV do SICOR, que não estão publicados. A concentração em um único banco pode ser artefato do preenchimento do campo, não um retrato do crédito.

**Como cruzamos com as leituras.** O `02_cruzar.py` comparou três coisas: as glebas do SICOR, os 26 tiles e os centroides das amostras atuais do LAPIG. Dos 91 pontos de amostra que caem dentro dos tiles, 6 caem dentro de alguma gleba de integração: 3 são amostras de integração e 3 são de outras classes. Os outros 85 ficam fora: 50 amostras de integração e 35 de outras classes. O mesmo resumo diz que nenhuma das 81 glebas do piloto tem amostra atual. Os dois números usam critérios diferentes: a gleba entra no piloto quando seu ponto representativo cai dentro dos tiles, e a gleba "tem amostra" quando algum centroide de amostra cai dentro do polígono. Uma gleba pode conter uma amostra e ficar fora do piloto pelo ponto representativo; por isso as duas contagens não se contradizem, mas também não respondem à mesma pergunta.

Além disso, o Gemini leu 74 fichas do piloto com a mesma pergunta das leituras de imagem: há renques? Nenhuma ficha batia com o código declarado. As glebas marcadas como ILPF eram custeio de soja de um mesmo ano, não um sistema com árvores.

**Por que não bateu.** O código do SICOR é uma declaração de crédito, não um mapa de uso do solo. Ele diz que o produtor pegou um financiamento enquadrado em uma linha de integração, não que o talhão tenha renques na safra de referência. Quatro coisas explicam o desencontro:

- Uma parte grande dos registros é "sem código (só subprograma)": 21.396 de 48.561 no Brasil (44%), 226 de 338 em Goiás (67%) e 30 de 81 no piloto (37%). Nesses casos, a classe só existe na descrição do subprograma, não no código de integração.
- As 26 glebas de ILPF do piloto são todas da safra 2021/2022, com soja como produto e custeio. É um recorte de um ano agrícola, não a descrição de um sistema com árvores.
- A gleba é a área informada na operação de crédito. O polígono não é o talhão do sistema integrado.
- A data da operação é a data de emissão, não a data de implantação do sistema. Um custeio de soja pode ser de uma área que já era ILPF, ou de uma área que nunca foi.

Há ainda dois limites práticos. Só 40,4% das operações de interesse têm gleba (28.988 de 71.764), e 252 geometrias foram descartadas por invalidez. E o ponto representativo da gleba pode ficar fora do tile mesmo que o polígono encoste no tile, o que reduz o recorte do piloto.

**O que recomendaríamos a quem for testar o mesmo caminho.** Só o que as fontes sustentam:

1. **Não usar o código de integração como rótulo.** Ele serve para levantar candidatos, não para afirmar o que existe no campo.
2. **Separar "código de integração" de "só subprograma" e olhar os dois grupos.** Boa parte da base está no segundo grupo (44% no Brasil, 67% em Goiás e 37% no piloto), e ele tem outra natureza: é investimento em pastagem, correção de solo, cercas e outros itens, não necessariamente um sistema integrado.
3. **Ler produto, finalidade e atividade antes de aceitar a classe.** No piloto, o código ILPF vinha de custeio de soja, e as 74 fichas não confirmaram nenhuma.
4. **Tratar a gleba como área financiada, não como talhão.** Conferir o polígono, o ponto representativo e a relação com a área de interesse.
5. **Contar com cobertura incompleta.** Quatro de cada dez operações de interesse têm gleba, e 252 geometrias foram inválidas.
6. **Confirmar em imagem de várias datas e, se possível, com inspeção de campo.** O código sozinho não passou no teste das 74 fichas.
7. **Se repetir em outra região, refazer o mesmo cruzamento com as amostras atuais e usar o piloto como controle negativo.** O valor do exercício é mostrar rápido que o código não basta, antes de gastar leitura de imagem.

Fonte: DIARIO.md; BALANCO.md; 01_filtrar_sicor.py; 02_cruzar.py; 03_detalhes.py; dados_log.txt; cruzar_log.txt; resumo.json.

## Inspeção de imagem por IA: confere, não acha

A ficha usada nas leituras tinha três quadros: uma imagem CBERS-4A de 2 m com o contorno da área, um detalhe de 500 m e uma série de NDVI do Sentinel-2 de 2020 a 2025. Cinco configurações de modelo leram as mesmas 58 fichas de resposta conhecida: 18 com árvores e 40 sem.

| Leitor | Viu renque onde há árvores (de 18) | Inventou renque onde não há |
|---|---:|---:|
| Gemini 3.8 Flash, esforço médio | 7 | 0 de 40 |
| Gemini 3.8 Flash, esforço alto | 9 | 0 de 37 |
| Gemini 4 Hydrogen, esforço alto | 9 | 0 de 40 |
| Gemini 4 Hydrogen, esforço xhigh | 7 | 0 de 40 |
| DeepSeek v4.1 Flash, esforço máximo | 6 | 0 de 40 |

Nenhum modelo inventou renque. Todos deixaram passar metade ou mais: o melhor viu 9 dos 18. E os renques vistos são sempre parte das mesmas 9 fichas (F009, F034, F062, F081, F084, F085, F090, F107 e F109). Nenhum modelo viu renques nas outras 9 fichas com árvores. O limite é da ficha, com uma data só e um recorte em volta do centro, não do modelo.

O Hydrogen em esforço alto foi o melhor custo-benefício: empatou com o 3.8 alto em 9 de 18, não inventou nenhum, gastou cerca de 10 mil tokens por ficha e leu as 58 em 6,4 min, sem erro. O custo em cota foi estimado em cerca de 0,04 ponto por leitura, contra 0,14 do 3.8 alto na esteira (estimativas grosseiras, porque o medidor só mostra pontos inteiros e as fichas não eram as mesmas). O 3.8 alto gastou cerca de 49 mil tokens por ficha. O Hydrogen xhigh viu menos (7 de 18) e custou cerca de 4 vezes mais cota e 3 vezes mais tempo; não compensou. Na segunda leitura, o 3.8 alto foi o único que aprovou as 11 fichas que a marcação humana chamou de "sim", incluindo as 2 que caem sobre talhões IPF da base da equipe. O Hydrogen alto aprovou 9 dessas 11 e rejeitou 2 que eram verdadeiras (F0353 e F0360). A base é pequena: 18 fichas.

A régua foi uma marcação humana de 50 fichas, sem ver a resposta da IA. Das 13 que a IA aprovou com nota máxima, a marcação humana deu 11 "sim", 1 "sim com ressalva" e 1 "não sei"; nenhuma recebeu "não". Mas 24 das 50 ficaram em "não dá para dizer", e 5 fichas rejeitadas pela IA (1 na segunda leitura e 4 na primeira) receberam "sim com ressalva". A consequência prática é que uma ficha de uma data só não basta: a tela de inspeção passou a mostrar o mesmo lugar em 2023, 2024, 2025 e 2026, em duas escalas, e a série temporal.

O teste de formato de ficha comparou duas versões no conjunto de 58 pontos de ensino. O formato f1, com 3 datas de 400 m em imagens separadas, acertou 13 dos 28 pontos com árvore e deu 1 falso em 30. Nos 12 talhões que têm as duas fichas, o f1 viu 6 renques, contra 5 da ficha antiga; o Hydrogen via 8 desses 12 com a ficha antiga. O ganho do f1 sozinho é pequeno. O f2, com o f1 mais quatro ampliações, imagem de referência e passo a passo, não rodou: não há leituras dele para comparar, e por isso não houve escolha entre f1 e f2.

Fonte: DIARIO.md; BALANCO.md; ANALISE-DEEPSEEK-2026-11-13.md.

## Semelhança por embedding: negativo

O AlphaEarth representa cada lugar por um vetor numérico anual, construído a partir de imagens de satélite. A ideia era procurar, nesses vetores, lugares parecidos com as amostras conhecidas de IPF e de ILP. Foram 50 candidatos para IPF e 50 para ILP. Só 1 dos 50 candidatos de IPF tinha renque, e nenhum dos 50 de ILP tinha. A maioria dos 50 de IPF era pasto com árvores nativas espalhadas, o que explica o negativo. Um controle de 30 pontos ao acaso rendeu 1 lido como integração (uma ILP), então o 1 em 50 não é sinal forte. A frente foi abandonada: o resultado não justificava o custo de continuar.

Fonte: DIARIO.md; BALANCO.md.

## Detector de fileiras: candidatas, mas enxerga pouco

O detector procura textura periódica de fileiras em imagem de 2 m. Foi escrito para achar renques em CBERS-4A, sem IA, e varreu os 26 tiles. O funil foi este:

- Cerca de 971 regiões candidatas, somando 26.755 ha antes de qualquer confirmação.
- Filtro de espaçamento maior ou igual a 12 m e área maior ou igual a 1,5 ha.
- Filtro de persistência: a fileira tinha de aparecer também em 2023 ou em 2026. Nos 24 tiles novos, isso reduziu de 464 para 149 regiões.
- Primeira leitura por IA em 249 fichas, com 45 "sim" e 1 "incerto"; as 46 foram relidas.
- Segunda leitura rigorosa: 39 aprovadas, sendo 38 nota A e 1 nota B; 7 rejeitadas, que não entraram no pacote. São 1.109 ha, 26 locais distintos em 14 tiles, com mais de 3 km entre si; 37 não têm amostra atual a menos de 300 m. A classe sugerida pela IA é 33 IPF e 6 ILF, mas a classe final é trabalho de inspeção.

O detector, porém, enxerga pouco. Dos 17 talhões com árvores que a equipe já conhece dentro dos tiles, contando a classe de qualquer ano, ele marcou 2. No grupo de medição, marcou 0 de 8. O gargalo da esteira é o detector, não a leitura por IA: a leitura quase não dá falso positivo, mas só lê o que o detector aponta.

A persistência entre anos foi o achado mais útil. Exigir que a fileira apareça em mais de um ano cortou 68 das 82 regiões que a primeira leitura havia rejeitado e manteve 12 das 13 aprovadas com nota A. Aplicado antes da leitura, reduz o número de fichas a ler para cerca de 30% sem quase perder amostra boa. A única aprovada que se perderia, F0353, tem fileiras visíveis em 2026; o detector é que falhou naquela data. Como o detector é sensível à época da imagem, varrer com duas datas também deve achar regiões que hoje escapam.

Os limites registrados são: nenhuma conferência humana das 39; a classe é palpite da IA; o contorno é parcial em talhões pequenos; espaçamento menor que 12 m não confirmou nenhuma vez.

Fonte: DIARIO.md; BALANCO.md; PROXIMA-ETAPA.md; medicao-3-detector-de-renques/resumo_entrega.json.

## Classificação: o melhor resultado técnico, ainda sem amostra confirmada

### Classificador de recortes de 2 m

O classificador recebe um recorte de 400 m de lado e responde se o recorte tem árvores. A base foi dividida antes de qualquer treino em 241 talhões: 164 de ensino, com 28 talhões com árvores e 136 sem, e 77 de medição, com 13 com árvores e 64 sem. Para chegar aos 241, ficaram de fora 7 registros (6 com safra considerada impossível e 1 com código 0); a regra de safra foi revista depois, e 2026/2027 é uma safra válida, então a divisão pode ter perdido casos. Não foi refeita nesta exportação. O treino usou 856 recortes: 652 do ensino e 204 negativos difíceis, tirados de áreas urbanas e de terraços que o detector confundia. O número coincide com os 856 trabalhos da fila de artigos por coincidência; o relatório do classificador registra 652 + 204. O modelo é o DINOv2 base, com pesos públicos e congelado, mais uma regressão logística treinada por cima. O limiar de probabilidade foi 0,09, escolhido na validação cruzada do ensino; a decisão do talhão é a maioria das datas disponíveis, com empate valendo positivo.

Na validação cruzada do ensino, o modelo achou 20 dos 28 talhões com árvores, com 16 falsos em 136 talhões sem árvores. Na medição, feita uma única vez depois de o modelo estar salvo, achou 7 dos 8 talhões com árvores dentro dos tiles, contra 0 de 8 do detector antigo. Em todos os talhões de medição com árvores, achou 8 de 13. Marcou 6 falsos nos 61 talhões sem árvores que tinham imagem; 3 talhões ficaram sem cena. A precisão foi 8 de 14. O treino gastou 33 minutos de placa T4 e 0,57 unidade do Colab.

O resultado é o melhor da frente técnica, mas tem duas ressalvas. A primeira é que o rótulo do caderno é "árvore", não "renque": inclui árvore espalhada, plantio denso e silvicultura. A segunda é que a medição usou recortes centrados em talhões conhecidos. Numa varredura de 4,52 milhões de hectares, com cerca de 10% de falsos por talhão, apareceriam muitas regiões falsas; a varredura precisaria de máscaras, do filtro de persistência e das leituras por IA depois. O classificador ainda não foi usado para varrer a área.

**O classificador fora da medição.** Ele não varreu a área, mas foi aplicado a três conjuntos menores: marcou 62 das 249 regiões persistentes do detector; 35 das 39 regiões aprovadas pelas duas leituras de IA; e, em 169 pontos onde o mapa e a varredura discordam, marcou árvore em 40 (24%). Nenhum desses usos é uma varredura da área; são testes pontuais, e o 169/40 é o embrião do teste de discordância entre o mapa e o classificador.

### Curvas de EVI2

O método da equipe foi reproduzido. A fonte é o Sentinel-2 TOA, coleção `COPERNICUS/S2_HARMONIZED`, com a máscara Cloud Score Plus e limiar `cs` maior ou igual a 0,6. O EVI2 é calculado como `2,5 × (B8 − B4) / (B8 + 2,4 × B4 + 1)`, com reflectâncias de 0 a 1. A mediana é feita por pixel dentro do mês e depois dentro do polígono; meses vazios são preenchidos por interpolação linear, de outubro a outubro. Em 21 registros do ensino, as curvas calculadas reproduziram a planilha da equipe com correlação mediana 1,000000 e diferença média absoluta de 3,7 × 10⁻⁸; a maior diferença em um único mês foi de 9,5 × 10⁻⁶ (0,0000095, quinta casa decimal).

O método foi aplicado às 39 amostras da safra 2024/2025: 33 IPF e 6 ILF. Em 12 amostras, 17 dos 507 meses (3,4%) não tinham observação válida e foram interpolados; a amostra F0780 tem três meses seguidos interpolados. O repositório público da equipe diz limiar de nuvem 0,5, mas só 0,6 reproduziu a planilha. O script exato das curvas não é público; o método foi reconstruído por tentativa e conferido por reprodução.

### Teste de separação da TempCNN

A receita pública da equipe foi reescrita e treinada 40 vezes no Colab, com quatro formas de separar os dados e 10 sementes em cada uma, sempre com as mesmas 1.607 linhas das 1.962 da planilha (sem o arquivo de configuração da equipe). O caso A é o da equipe: separação por linha e parada do treino olhando o próprio teste. O B separa por linha, mas a parada usa uma validação separada. O C separa por lugar, e nenhum lugar aparece em dois lados. O D separa por bloco de cerca de 11 km.

| Caso | Acurácia média em 10 sementes |
|---|---:|
| A, como a equipe | 58,2% ± 3,7 |
| B, parada em validação separada | 52,2% ± 5,8 |
| C, tudo separado por lugar | 49,8% ± 5,3 |
| D, por bloco | 50,8% ± 7,8 |

A diferença A menos C é de +8,4 pontos percentuais, com intervalo de 95% de [+3,3; +13,6]. Mas boa parte disso vem da parada no próprio teste: A menos B é +6,0 [+1,2; +10,8], e B também treina com 20% menos linhas. A comparação mais limpa, B menos C, dá +2,4 [−4,0; +8,9], um intervalo que inclui zero. Ou seja: o teste usado para parar o treino infla a nota; separar por lugar, sozinho, não mostrou efeito nos números. O F1 por classe no caso A foi: Agricultura 79, Pastagem 68, ILP 51, IPF 48, Agrofloresta 22, ILPF 11 e ILF 0; as classes raras têm de 0 a 6 linhas no teste. A ressalva é a mesma: é a reimplementação com 1.607 das 1.962 linhas e sem o arquivo de configuração da equipe.

O teste gastou 0,05 unidade do Colab: 34,7 minutos de treino em CPU, 52 segundos por rodada, em uma única sessão sem placa de vídeo.

Fonte: medicao-4-classificador/RELATORIO.md; curvas-evi2/RELATORIO.md; teste-separacao/RELATORIO.md; teste-separacao/COMO-FOI-FEITO.md; DIARIO.md; BALANCO.md.

## Auditoria do mapa e tela TVI: pronta, não lida

A equipe publicou em 09/11/2026 a versão 1.0 do mapa da TempCNN para a área piloto. A auditoria faz uma pergunta só: dos lugares que o mapa chama de IPF, quantos têm de fato árvores plantadas em fileiras na safra 2024/2025? É uma auditoria piloto, com 100 pontos, não uma validação do mapa.

O desenho foi gravado antes de ver qualquer imagem: 100 pixels sorteados com chance igual entre os 2,37 milhões de pixels de IPF da imagem publicada, 15 controles com árvores e 20 sem árvores, 15 repetições escondidas e 30 pontos de reserva. A inspeção é cega: a fila só tem identificador e coordenada, e o gabarito fica à parte. O protocolo tem seis respostas (renque, plantio fechado, árvores espalhadas, vegetação nativa, sem árvores, não dá para dizer) e uma definição de renque com cinco critérios. O desenho foi revisado por quatro IAs antes de qualquer imagem.

O que está pronto: 1.360 recortes de 2 m, em 600 m e 1.500 m de lado, da estação seca de 2023 a 2026, somando 172 MB; 148 dos 150 pontos têm imagem de 2024 e 2025, e dois têm só 2025. A tela de inspeção foi testada. A tela tipo TVI, um protótipo de estudo e não o TVI oficial, mostra os quatro anos em ordem cronológica, a série de NDVI de 2019 a 2025, as seis respostas, a resposta da IA só depois de o inspetor gravar a dele, e uma supervisão com concordância e kappa.

O que falta: a leitura dos 150 pontos por IA, que estava prevista para depois de 14/11, e a leitura de um inspetor da equipe. O gabarito estava fechado na última anotação. Por isso a frente é inconclusiva: a estrutura está pronta, mas não há resultado para contar.

Os sinais que motivaram a auditoria são preliminares e não devem ser lidos como conclusão. O mapa atribui 394 mil ha (8,7% da área) a classes com árvores integradas: IPF 179 mil, ILPF 143 mil, Agrofloresta 60 mil e ILF 12 mil. Do "IPF" do mapa, 26% cai onde o MapBiomas publicado não mostra uso agropecuário, 46% em pastagem, 13% em mosaico, 8% em agricultura e 7% em floresta plantada; a contagem do sorteio no relatório da auditoria é essa, e a abertura do mesmo relatório traz 42/15/14/3, que não é a contagem final. Nas 39 áreas do detector, 32 têm pixel no mapa: em 14 a classe majoritária é Pastagem; 13 têm maioria de classes com árvore e 13 têm menos de 10% de árvore. Dos 100 pontos de IPF sorteados, 93 são de borda. O programa do mapa dá a cada pixel a classe mais provável entre nove, sem classe de vegetação nativa, sem máscara e sem opção de rejeitar. A auditoria existe justamente para testar isso.

Esses números já são a conta corrigida. A primeira versão, sem tratar a projeção Web Mercator das imagens, dava 33% do IPF fora do uso agropecuário e 30 das 39 áreas com pixel; a corrigida deu 26% e 32. O 2,37 milhões é a contagem de pixels da PNG de 30 m usada no sorteio (`01_sortear.py` conta 2.371.461 pixels), não a área do mapa; a área de 179 mil ha vem da estatística da equipe. As duas não são a mesma conta: a PNG é a imagem de visualização e inclui bordas.

Fonte: auditoria-mapa/LEIA-ME.md; auditoria-mapa/PROTOCOLO.md; auditoria-mapa/RELATORIO-tela.md; tela-tvi/LEIA-ME.md; DIARIO.md; BALANCO.md.

## Artigos: a única frente com resultado real

**A ideia.** Artigos, teses, dissertações e publicações técnicas dizem onde existem fazendas e áreas experimentais com sistemas integrados. A coordenada do texto quase nunca marca o talhão: costuma ser a sede da fazenda, a estação experimental ou a cidade. O que a frente fez foi extrair coordenadas muito confiáveis, com o trecho literal, a informação de a que elas se referem, a classe e o ano. A coordenada é uma pista; a confirmação vem da imagem e, depois, da inspeção.

**A busca.** A base principal é o OpenAlex. O filtro pede trabalhos com texto aberto, autor de instituição brasileira, publicados a partir de 2005, em cinco buscas: ILP, ILPF, silvipastoril, ILF e agroflorestal, em português e inglês. Revisões e modelagens ficam de fora, assim como o que a rota antiga já tinha lido. A fila inicial ficou com 856 trabalhos, em ordem sorteada. Dos 856, 588 foram lidos e 268 ficaram sem PDF; não houve descarte por escopo. Uma rota anterior, com BDTD, Embrapa e busca na web, teve 131 documentos e 181 locais; ela é a origem dos 25 candidatos que depois foram lidos um a um. Dos 25, 5 tiveram nota A (Santa Brígida em Ipameri, Boa Vereda em Cachoeira Dourada e três áreas no DF), todas fora dos 26 tiles. A rota antiga é uma etapa separada; os 588 vêm da fila nova do OpenAlex. Esses 131 documentos e as 5 nota A não estão em `documentos.csv` nem no site. Ela mostrou por que a coordenada do texto costuma ser a sede ou a cidade.

**O piloto.** Os 30 primeiros documentos deram 24 estudos de campo. Desses 24, 16 tinham coordenada (7 de nível A, 4 de B e 5 de C) e 8 não tinham. A IA não deixou passar nenhuma coordenada de local: o único documento com coordenada que ela não listou trazia a faixa de uma região inteira, não um ponto.

**A extração.** O DeepSeek lê os textos em lotes de 2, cada lote numa pasta isolada, e devolve para cada local: o trecho literal da coordenada, a que ela se refere (parcela, área experimental, fazenda ou sede, município, ou não diz), as classes estudadas e de comparação, os anos de implantação e de avaliação, a área e a figura ou croqui, se houver. O pedido proíbe usar outra fonte, abrir arquivo fora da pasta ou alterar arquivo. O texto do artigo é tratado como dado de terceiros: a IA deve ignorar instruções que apareçam dentro dele.

**A conferência.** O programa confere três coisas: o trecho literal existe no texto, a precisão é calculada pela grafia e o número decimal bate com o trecho. Ele também procura coordenadas no texto inteiro, para achar o que a IA deixou passar. Na rota antiga, a conferência também verificava se a coordenada caía no município citado, pela malha do IBGE, e juntava locais repetidos entre documentos quando as coordenadas estavam a menos de 3 km ou tinham o mesmo nome e município. Duas checagens novas rebaixam o nível: minuto ou segundo acima de 60 vira C, e ponto a menos de 1 km da sede municipal ou com 25% ou mais de área construída num raio de 100 m vira C. Entre 1 e 3 km da sede, o ponto continua A ou B, com aviso. Em 80 documentos, essas checagens pegaram 7 dos 27 A. Exemplos: Parnaíba a 90 m da sede, com 95% construído; Belterra a 60 m; Confins com 99% construído. Santa Brígida estava escrita como "17°68′" e caía a cerca de 55 km do lugar. O filtro de nomes também passou a remover o nome do proprietário citado depois do nome da fazenda.

**Os níveis.** A significa área experimental, precisão de segundos (cerca de 30 m) e classe e ano no texto. B significa precisão boa, mas a coordenada é da fazenda ou da sede. C significa precisão só em minutos (~1,8 km) ou pior que 100 m, número ilegível, coordenada fora do Brasil, coordenada impossível (minuto ou segundo acima de 60), trecho que não existe no texto ou uma das checagens acima. O nível A vale para o texto: uma área experimental com precisão de segundos ainda pode ser a sede da estação, e é por isso que a imagem é necessária.

**Os números finais.** Foram 588 documentos com texto lido, 458 coordenadas extraídas e conferidas, sendo 125 de nível A, 105 de B e 228 de C. A soma 125 + 105 + 228 fecha 458. Dos 230 pontos A/B, 43 foram confirmados na imagem, 139 ficaram incertos e 48 não conferem; os 228 pontos C não passaram pela conferência de imagem. O site público mostra os níveis A e B, com lista filtrável por nível, classe, UF e busca, mapa de satélite com o círculo da margem de erro da coordenada, ficha com o trecho literal, links para Google Maps, Google Earth, Esri Wayback, DOI e documento, exportação CSV e link direto por ponto. O EVI é calculado à parte, com Landsat 5, 7, 8 e 9 da coleção C2 L2, 30 m, de 1985 a 2025, no pixel de cada ponto A ou B.

**Por que deu certo.** O que está publicado permite conferir a cadeia no essencial: o trecho literal permite conferir a coordenada no texto, o programa confere o número e o trecho, o nível de precisão diz o que a coordenada representa, e a conferência na imagem ajuda a eliminar o caso de a coordenada ser a sede ou a cidade. O site deixa qualquer pessoa refazer a conferência. Os relatórios internos que descrevem os testes, porém, não estão neste repositório. E a fonte é independente das amostras da equipe: um lugar citado em artigo não foi escolhido por um modelo treinado nas amostras atuais.

**Limites.** A coordenada do artigo costuma ser a sede ou a cidade, não o talhão. O nível A vale para o texto, não para o campo. Muitos documentos não têm PDF acessível, e a fila inicial de 856 trabalhos não é o universo da literatura. A classe é a que o artigo declara, no ano do estudo, e o sistema pode ter mudado até 2024/2025. A conferência na imagem confirmou 43 dos 230 pontos A/B; 139 ficaram incertos e 48 não conferem. Os 228 pontos C não foram conferidos. Confirmar na imagem também não é confirmar a classe em campo: é o passo que elimina sede, cidade e coordenada errada. E o próprio acervo precisa de inspeção para virar amostra.

**Nota sobre as contagens.** A última anotação do `DIARIO.md`, em 13/11, registra 380 documentos e 241 coordenadas (73 A, 69 B, 135 C). Os números finais usados aqui, 588 documentos, 458 coordenadas (125 A, 105 B, 228 C) e 43 dos 230 pontos A/B confirmados na imagem, são a contagem final do experimento. O diário não registra a passagem de 380 para 588; a soma dos níveis finais, porém, fecha exatamente 458.

Fonte: RESULTADO.md; COMO-RODAR.md; PEDIDO.md; DIARIO.md; rota-artigos/LEIA-ME.md; rota-artigos/ANALISE-ANOS-E-CLASSES.md.

## Lições

1. **Rótulo de banco não é rótulo de campo.** O código de integração do SICOR não descreveu o uso do solo em 74 fichas; as "ILPF" eram custeio de soja de um mesmo ano.
2. **IA de imagem confere, não acha.** Em cinco configurações, nenhum modelo inventou renque em 40 fichas sem árvores, mas o melhor viu 9 de 18; metade das áreas com árvores passou.
3. **A ficha de uma data só limita a decisão.** Na régua de 50 fichas, 24 ficaram em "não dá para dizer"; o mesmo lugar em várias datas e a série temporal mudam a pergunta.
4. **Separe ensino e medição antes de treinar, e meça uma vez.** A base foi dividida em 164 talhões de ensino e 77 de medição; o classificador foi medido uma vez e achou 7 de 8 talhões com árvores nos tiles.
5. **O teste usado para parar o treino infla a nota.** A acurácia caiu de 58,2% para 52,2% quando a parada deixou de olhar o teste, mas B também treina com 20% menos linhas; separar por lugar não mostrou efeito (B menos C: +2,4 pontos percentuais, intervalo de −4,0 a +8,9).
6. **Coordenada de artigo é pista, não amostra.** A coordenada costuma ser a sede ou a cidade; o que dá valor é o trecho literal, o nível de precisão e a conferência na imagem. A frente dos artigos foi a única que produziu um acervo utilizável.

Fonte: BALANCO.md; DIARIO.md; teste-separacao/RELATORIO.md; rota-artigos/LEIA-ME.md.
