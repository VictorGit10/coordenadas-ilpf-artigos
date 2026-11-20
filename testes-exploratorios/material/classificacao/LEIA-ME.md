# Classificação: o melhor resultado técnico, ainda sem amostra confirmada

**Frente:** classificador de recortes de 2 m (DINOv2 congelado + cabeça logística) e teste de separação da TempCNN. **Data:** 12 e 13/11/2026.

## O que foi testado

### Classificador de recortes de 2 m

O classificador recebe um recorte de 400 m de lado do CBERS-4A (200 × 200 px a 2 m) e responde se o recorte tem árvores. A base foi dividida **antes de qualquer treino** em 241 talhões: 164 de ensino (28 com árvores e 136 sem) e 77 de medição (13 com árvores e 64 sem). A divisão foi por blocos de 0,1 grau (cerca de 11 km), com semente fixa; nenhum talhão aparece nos dois lados.

O treino usou **856 recortes**: 652 do ensino (491 centrais + 161 deslocados em 27 talhões grandes) e 204 negativos difíceis, tirados de 102 pontos rejeitados nas leituras de fichas por área urbana/construção (61) ou terraço/curva de nível (41), com 2 datas cada. Descartei leituras cujo cadastro ou motivo indicava sistema com árvore, para não ensinar o modelo a rejeitar plantio. Todos os 102 pontos ficaram a 5 km ou mais de qualquer talhão de medição.

O modelo é o **DINOv2 base `vit_base_patch14_dinov2.lvd142m`**, com pesos públicos e congelado, mais uma **regressão logística** treinada por cima (C = 0,03, `class_weight='balanced'`). A entrada é 448 × 448 px, com 8 transformações dihedral (4 rotações × espelhamento). O limiar de probabilidade é **0,09**, escolhido na validação cruzada do ensino; a decisão do talhão é a maioria das datas disponíveis, com empate valendo positivo.

### Teste de separação da TempCNN

A receita pública da equipe foi reescrita e treinada 40 vezes no Colab (4 casos × 10 sementes), sempre com as mesmas 1.607 linhas das 1.962 da planilha, sem o arquivo de configuração da equipe. O caso A é o da equipe: separação por linha e parada do treino olhando o próprio teste. O B separa por linha, mas a parada usa uma validação separada. O C separa por lugar, e nenhum lugar aparece em dois lados. O D separa por bloco de cerca de 11 km.

## Resultado

**Em resumo:** 7 de 8 talhões com árvores nos tiles (o detector antigo: 0 de 8), 8 de 13 no total e 6 falsos em 61; a TempCNN caiu de 58,2% para 52,2% quando a parada deixou de olhar o teste. É o melhor resultado técnico, ainda sem amostra confirmada.

### Classificador

- **Validação cruzada no ensino:** AUC por imagem 0,874; AUC por talhão 0,918. Com o limiar 0,09, a matriz no nível do talhão ficou TP = 20, FN = 8, TN = 120, FP = 16; sensibilidade 0,714, especificidade 0,882, acurácia balanceada 0,798.
- **Medição, feita uma única vez depois de o modelo estar salvo:** achou **7 dos 8 talhões com árvores dentro dos tiles**, contra 0 de 8 do detector antigo. Em todos os talhões de medição com árvores, achou **8 de 13**. Marcou **6 falsos nos 61 talhões sem árvores** que tinham imagem; 3 talhões ficaram sem cena. A precisão foi 8 de 14 = **57,1%**; acurácia 85,1%, sensibilidade 61,5%, especificidade 90,2%.
- O treino gastou **33 minutos de placa T4** e **0,57 unidade** do Colab.
- **Fora da medição:** o classificador marcou 62 das 249 regiões persistentes do detector; 35 das 39 regiões aprovadas pelas duas leituras de IA; e, em 169 pontos onde o mapa e a varredura discordam, marcou árvore em 40 (24%). Nenhum desses usos é uma varredura da área; são testes pontuais.

**Conclusão, coerente com o resumo principal:** é o melhor resultado técnico da frente, mas ainda **sem amostra confirmada**. O rótulo do caderno é "árvore", não "renque": inclui árvore espalhada, plantio denso e silvicultura. A medição usou recortes centrados em talhões conhecidos; numa varredura de 4,52 milhões de hectares, com cerca de 10% de falsos por talhão, apareceriam muitas regiões falsas. A varredura precisaria de máscaras, do filtro de persistência e das leituras por IA depois.

### Teste de separação da TempCNN

| Caso | Acurácia média em 10 sementes |
|---|---:|
| A, como a equipe | 58,2% ± 3,7 |
| B, parada em validação separada | 52,2% ± 5,8 |
| C, tudo separado por lugar | 49,8% ± 5,3 |
| D, por bloco | 50,8% ± 7,8 |

A diferença A − C é de +8,4 pontos percentuais, com intervalo de 95% de [+3,3; +13,6]. Mas boa parte vem da parada no próprio teste: A − B é +6,0 [+1,2; +10,8], e B também treina com 20% menos linhas. A comparação mais limpa, B − C, dá +2,4 [−4,0; +8,9], um intervalo que inclui zero. Ou seja: **o teste usado para parar o treino infla a nota; separar por lugar, sozinho, não mostrou efeito nos números.**

O F1 por classe no caso A foi: Agricultura 79, Pastagem 68, ILP 51, IPF 48, Agrofloresta 22, ILPF 11 e ILF 0; as classes raras têm de 0 a 6 linhas no teste. O teste gastou 0,05 unidade do Colab: 34,7 minutos de treino em CPU, 52 segundos por rodada, numa única sessão sem placa de vídeo.

**Ressalva:** é a reimplementação com 1.607 das 1.962 linhas e sem o arquivo de configuração da equipe. A divisão publicada também tratou 2026/2027 como safra impossível; depois se verificou que ela é válida, então a divisão pode ter perdido casos. Não foi refeita nesta exportação.

## Como rodar

Os scripts foram escritos para a pasta de trabalho do experimento e para o Colab. A raiz é lida de `ILPF_RAIZ`; os recortes e o modelo ficam em `classificador/recortes/` e `classificador/modelo/`, ao lado dos scripts.

```bash
# 1. dividir os talhões (precisa do GPKG da equipe, não publicado)
python 22_dividir_talhoes.py

# 2. baixar os recortes de 400 m (CBERS-4A, 3 datas da estação seca)
python baixar_recortes.py ensino
python baixar_recortes.py negativos
python baixar_recortes.py medicao

# 3. treinar no Colab (T4): empacotar, subir e rodar treinar_colab.py
python empacotar.py todos

# 4. medir uma única vez, depois de o modelo estar salvo
python medir_colab.py
python avaliar_medicao.py

# 5. classificar pontos novos
python classificar.py --entrada pontos.csv --saida saida.csv
python classificar.py --entrada pontos.csv --datas 3 --saida saida.csv
```

Dependências: Python 3.10+, `numpy`, `pandas`, `geopandas`, `shapely`, `pyproj`, `Pillow`, `requests`, `rasterio`; no Colab, `torch`, `timm` e `scikit-learn`; para a TempCNN, `tensorflow` e uma sessão de CPU ou GPU. O `classificar.py` precisa de `torch` e `timm`, e do `modelo/` com `config.json` e a cabeça; sem a cabeça, ele não roda.

**Entradas que não estão publicadas e por quê:**

- `talhoes_divididos.gpkg`: 241 talhões da equipe, com geometria, classe, grupo, bloco, `nos_tiles` e `detector_marcou`. É amostra da equipe; a regra 1 do briefing manda excluir.
- `amostras_ilpf_inspecionadas_4326.gpkg` e `divisao_ensino_medicao.csv`: a entrada da divisão, com os talhões e as safras da equipe. Não publicados.
- `varredura/tiles.json` e `varredura/candidatos/*.geojson`: usados para as colunas `nos_tiles` e `detector_marcou`. A lista mínima dos 26 tiles está em `../detector-de-renques/codigo/tiles.json`; os polígonos das 564 regiões candidatas não estão publicados.
- `recortes/`: as imagens de 400 m centradas nos talhões da equipe. Não publicadas por serem derivadas das amostras da equipe.
- `modelo/cabeca.npz`: a cabeça logística treinada nos 856 recortes. Não é amostra, mas foi ajustada nas amostras da equipe; ficou de fora por cautela. O `config.json` publicado permite reconstruir a arquitetura e o limiar, mas não os pesos da cabeça.
- `dados/recortes_*.csv`: índice dos recortes, com talhão, grupo, rótulo, data e arquivo. Não publicado.
- `medicao_tabela.csv`, `medicao_probabilidades.csv` e `medicao_avaliacao.json`: resultado por talhão da equipe. A regra 1 manda excluir. O agregado está em `resultados/medicao_metricas.json` e `resultados/medicao_resumo.json`.
- `samples_iCLS.csv`, `grupos.csv` e `registros_ensino.gpkg`: planilha e agrupamento da equipe. O teste de separação os usa, mas não os contém; os resultados agregados estão em `resultados/separacao_*.csv`.
- `dados_ensino.zip` e `dados_medicao.zip`: 62 MB e 16 MB de recortes. Não publicados.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `codigo/22_dividir_talhoes.py` | Divide os 241 talhões em ensino e medição por blocos de 0,1 grau. |
| `codigo/baixar_recortes.py` | Baixa os recortes de 400 m do CBERS-4A em até 3 datas da estação seca. |
| `codigo/comum.py` | Caminhos, QA e utilidades de CSV do classificador. |
| `codigo/cbers.py` | Leitor dos recortes CBERS-4A do catálogo aberto do INPE. |
| `codigo/selecionar_negativos.py` | Escolhe os negativos difíceis (urbano/terraço) nas leituras rejeitadas. |
| `codigo/filtrar_negativos.py` | Mantém só os negativos que passaram no filtro e apaga as imagens descartadas. |
| `codigo/empacotar.py` | Empacota os recortes para envio ao Colab. |
| `codigo/preparar_ensino.py` / `codigo/preparar_medicao.py` | Descompactam os pacotes no Colab. |
| `codigo/treinar_colab.py` | Treina a cabeça logística sobre as features congeladas, com validação cruzada por bloco. |
| `codigo/medir_colab.py` | Mede o grupo de medição uma vez com o modelo salvo. |
| `codigo/avaliar_medicao.py` | Junta a previsão com o gabarito e resume os números. |
| `codigo/modelo_util.py` | Carrega o DINOv2, extrai features e aplica a cabeça. |
| `codigo/classificar.py` | Classifica pontos (lon, lat) novos, com 1 ou 3 datas. |
| `codigo/gerar_relatorio.py` | Gera a primeira versão do relatório interno; precisa da tabela por talhão, não publicada. |
| `codigo/qa_dados.py` | Confere contagens, datas, tamanhos e arquivos dos recortes. |
| `codigo/zip_modelo.py` / `codigo/zip_resultado.py` | Empacotam o modelo e o resultado para baixar do Colab. |
| `codigo/montar_pontos.py` | Monta as listas de pontos do detector e da grade dos artigos. |
| `codigo/rodar_colab.py` | Roda o `classificar.py` no Colab, com cache de cenas. |
| `codigo/separacao_rodar.py` | Roda os casos A–D do teste de separação da TempCNN. |
| `codigo/separacao_conferir.py` | Recalcula as divisões e confere os totais do teste de separação. |
| `resultados/config.json` | Backbone, entrada, C, limiar e regra do talhão. |
| `resultados/cv_resultados.json` | AUC, acurácia balanceada e curva do limiar na validação cruzada. |
| `resultados/medicao_metricas.json` | Matriz de confusão e métricas agregadas da medição, sem identificadores. |
| `resultados/medicao_resumo.json` | Contagem de talhões e recortes por classe na medição. |
| `resultados/colab_resumo.json` | Tempo e unidades do Colab. |
| `resultados/separacao_resultados.csv` | As 40 rodadas da TempCNN, com acurácia, F1 e suportes. |
| `resultados/separacao_verificacao.csv` | Conferência das divisões: somas e interseções entre lados. |
| `resultados/uso_saida_detector.csv` | Classificador aplicado às 564 regiões do detector: probabilidade por data e decisão. |

## Limites

- **Poucos positivos:** 28 talhões com árvore no ensino e 13 na medição. Um único talhão muda a sensibilidade em vários pontos percentuais.
- O rótulo é do talhão, não do recorte; um recorte de 400 m pode pegar estrada, mata ciliar ou vizinho. Em talhões pequenos, boa parte do recorte é de fora.
- O rótulo "árvore" não é "renque": há pasto com árvores espalhadas e plantios densos marcados como positivos.
- O limiar 0,09 foi escolhido no mesmo OOF usado para escolher o modelo; a acurácia do ensino é otimista. A medição é a única estimativa não enviesada, e tem só 13 positivos.
- A cobertura do CBERS em 2026 faltou em várias regiões; 3 talhões de medição ficaram sem cena e entram como "sem dado".
- A medição usa recortes centrados em talhões conhecidos; não é uma varredura da área.
- O teste da TempCNN usa 1.607 das 1.962 linhas e não tem o arquivo de configuração da equipe; não é uma cópia do modelo deles.
- Nenhum recorte foi publicado como exemplo: todos os recortes são centrados em talhões da equipe.

## Fonte

`medicao-4-classificador/RELATORIO.md`, `teste-separacao/RELATORIO.md`, `teste-separacao/COMO-FOI-FEITO.md`, `DIARIO.md` (seções 124–175 e 247–255), `BALANCO.md` (Frentes A, C e D). Os relatórios internos completos não estão neste repositório.
