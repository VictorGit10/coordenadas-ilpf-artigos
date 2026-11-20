# Parecer do Gemini 4 Hydrogen (esforço alto)

Separo abaixo o que é **fato conferido** nos arquivos desta pasta do que é **opinião** técnica.

---

### 1. O raciocínio se sustenta? Onde há falhas ou extrapolação

**Fatos conferidos:**
- Em `RELATORIO-classificador.md`, o modelo (`vit_base_patch14_dinov2.lvd142m` congelado + regressão logística) escolheu arquitetura **e** limiar (`0,09`) sobre o mesmo OOF da validação cruzada (linhas 43–57, 224). Na medição única, acertou **7/8** nos tiles e **8/13** no total, com **6/61** falsos e **1/1** erro na única Silvicultura (o único talhão de Silvicultura, negativo; linha 132). Os 204 negativos difíceis vieram de fichas já rejeitadas pela esteira anterior, não de amostragem da paisagem (linha 19).
- Em `DIARIO.md` (linha 134) e `ANALISE-CAMINHOS.md` (linha 137), registra-se que as instruções do Gemini foram calibradas nas "58 conhecidas", que podem conter talhões do grupo `medicao`.
- Em `repo_04.py`, o script da equipe faz `train_test_split` por **linha** (linhas 138–140) e usa `(X_test, y_test)` para `EarlyStopping` e `ModelCheckpoint` por `val_accuracy` (linhas 176–182). Além disso, há split prévio 60% SSL / 40% fine-tuning (`repo_03.py`, linha 108; `repo_04.py`, linha 106).

**Opinião:**
- A extrapolação de ~10% (ou 2–5%) de falsos para 4,52 Mha (`ANALISE-CAMINHOS.md`, linhas 88–93) subestima o risco fora de talhões centrados: o classificador não viu cerrado ralo, mata ciliar, pivôs aleatórios nem silvicultura suficiente (errou o único caso). O número de falsos pode ser bem maior.
- Há um salto conceitual recorrente: os modelos de 2 m detectam **renques visíveis**, não **sistemas integrados** (ILP é invisível em 2 m; IPF jovem/denso e pasto arborizado confundem o rótulo `arvore`, como admite `RELATORIO-classificador.md`, linha 217). Enquanto a esteira não for cruzada contra as 58 conhecidas, nenhuma métrica da esteira completa sobre a `medicao` é defensável.

---

### 2. A leitura do mapa v1.0 é sólida?

**Fatos conferidos:**
- Em `repo_04.py` (linhas 30–33) e `repo_05.py` (linhas 29–32), a TempCNN classifica apenas 9 classes (`1..9`) — **não existe classe de vegetação nativa**. O `repo_05.py` oferece modos `pixel`, `segmento` (SLIC de ~25 ha) e `cluster_temporal`.
- `cruzar.py` (linhas 19–28) e `nas39.py` (linhas 18–23) leem PNGs RGB (30 m vs 75 m) supondo grade linear em `lat/lon`, casamento por distância RGB e, em `nas39.py`, sem limiar de cor (bordas com *antialiasing* viram classe).

**Opinião:**
A leitura é preliminar e **não deve ser afirmada como crítica** sem checagem. Explicações alternativas plausíveis para os 33% de "IPF" no transparente do MapBiomas e para 15/30 das 39 caírem em Pastagem:
1. **Projeção/renderização:** tiles PNG web costumam usar Web Mercator (`EPSG:3857`), e tratá-los como grade `lat/lon` desloca coordenadas; soma-se a diferença 30 m vs 75 m e *antialiasing*.
2. **Falta de classe nativa na TempCNN:** se o mapa v1.0 não foi mascarado por área antrópica, cerrado/mata nativa é **forçado** a cair em IPF/ILPF/Agrofloresta/Pastagem — hipótese fortíssima que explica ambos os números.
3. **Resolução e escala:** nas 39 (ainda não confirmadas), segmentação SLIC de ~25 ha dilui renques pequenos (1,5–10 ha) na pastagem ao redor.

**Como conferir antes:** checar o CRS real e a legenda exata da camada MapBiomas; inspecionar ~50 pontos sorteados de "IPF no transparente" diretamente sobre Sentinel-2/Esri Wayback; confirmar com a equipe se o mapa v1.0 usa SLIC/pixel e se já teve máscara nativa.

---

### 3. O plano dos três caminhos é o melhor uso do que existe?

**Opinião:** Não na forma resumida em `CONTEXTO.md` — falta a peça central já proposta em `ANALISE-CAMINHOS.md` (Caminho B: testar a TempCNN antes de buscar mais dados).
- **Cortaria/adiaria:** o Caminho 3 (SIGEF/OSM/busca manual para artigos). Dados de artigos costumam ser antigos (2006–2016) e muitos SAF são quintais invisíveis em 2 m (`LEIA-ME-artigos.md`, linhas 48–52; `ANALISE-CAMINHOS.md`, linha 61). Apenas feche `T0004`/`T0006` e aproveite as 5 nota A já prontas.
- **Acrescentaria e reordenaria:**
  1. **Primeiro:** experimento controlado da TempCNN (com split por blocos, sem vazamento, multi-seed) testando o efeito das 39 amostras e da adição de classe negativa de vegetação nativa.
  2. **Segundo:** unificar a auditoria do mapa v1.0 e a validação das 39 + artigos numa **única campanha cega no TVI** (com pontos de controle sem árvore e sem mostrar rótulo da IA), aproveitando que o TVI já tem Esri Wayback (`ANALISE-CAMINHOS.md`, linha 39).
  3. **Terceiro:** só evoluir o classificador 2 m (com negativos de mata nativa, cerrado e silvicultura do MapBiomas) após os passos 1 e 2 mostrarem onde está o ganho real.

---

### 4. Caminho mais inovador e justificável

**Opinião:** Dois caminhos de alto impacto e baixo custo em GPU Colab:
1. **Preservar a geometria dos patch tokens do DINOv2 + fusão temporal:** hoje `RELATORIO-classificador.md` (linha 37) tira a **média** dos patch tokens, destruindo a informação espacial de listras paralelas. Extrair a grade `32×32` de patches do DINOv2 (448 px) e aplicar uma cabeça leve de MIL (*Multiple Instance Learning*) ou espectro/autocorrelação 2D sobre os patches — opcionalmente combinada aos embeddings/EVI2 — detecta renques parciais dentro de recortes de 400 m sem treinar backbone pesado. *Custo:* ~1–3 unidades Colab T4. *Risco:* ainda limitado a 28 positivos; exige regularização forte.
2. **Amostragem ativa guiada por desacordo:** cruzar o mapa TempCNN com o classificador 2 m em 1–2 tiles (após máscara nativa) para achar tanto **falsos da TempCNN** (nativa/pasto virando IPF) quanto **positivos omitidos**. *Custo:* baixo (~1–2 unidades Colab). *Risco:* retroalimentar viés se não houver triagem humana cega no fim.

---

### 5. Como garantir amostra de IA defensável para treino ou validação

**Opinião:**
- **Para validação:** amostra de IA **não valida** sozinha. Exige inspeção humana probabilística, **cega** (sem nota/classe da IA visível), com controles negativos misturados e checagem temporal compatível com a safra 2024/2025.
- **Para treino:** (a) isolamento espacial por blocos entre calibração/prompting/limiar, treino e teste final; (b) separação em metadados de amostras confirmadas vs candidatas de IA; (c) ablação pareada (com vs sem amostras de IA, múltiplas seeds, e versão excluindo as 8 amostras a <11 km da medição apontadas em `ANALISE-CAMINHOS.md`, linha 138), verificando não-piora em Pastagem e Silvicultura.

---

### 6. Resultado final mais convincente para mostrar à equipe

**Opinião:** Um pacote conciso e acionável com três entregas juntas:
1. **Campanha GeoJSON pronta para o TVI** (~100–130 pontos cegos: as 39 candidatas + 5–7 dos artigos com classe bibliográfica + pontos sorteados do mapa v1.0 + controles sem árvore).
2. **Diagnóstico construtivo do mapa v1.0** (após checar CRS/legenda e inspecionar amostra): se confirmado que "IPF" vaza para vegetação nativa por ausência dessa classe negativa, essa descoberta por si só já melhora a v2.0 da equipe.
3. **Teste limpo da TempCNN** (split por blocos corrigido): mostrando o impacto real das novas amostras e de uma classe negativa nativa — mais os 8 erros de cadastro já encontrados no GPKG (`DIARIO.md`, linha 121).

