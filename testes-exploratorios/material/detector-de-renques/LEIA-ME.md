# Detector de renques: candidatas, não confirmadas

**Frente:** detector de textura periódica em CBERS-4A de 2 m, varredura dos 26 tiles e duas leituras por IA. **Data:** 11 a 13/11/2026.

## O que foi testado

O detector procura a assinatura de um renque: faixa escura de copa, de 4 a 15 m de largura, repetida a cada 10 a 60 m, com direção bem definida e faixa clara de pasto ou lavoura entre as fileiras. Ele não usa IA: converte a imagem para cinza, estima a direção do gradiente, projeta a janela nessa direção, mede o espectro 1D e exige coerência espacial entre janelas vizinhas.

A varredura cobriu os 26 tiles do Cerrado goiano, em blocos de 5 km com 300 m de sobreposição. Depois vieram três filtros: espaçamento maior ou igual a 12 m e área maior ou igual a 1,5 ha; persistência da fileira em 2023 ou 2026; e duas leituras por IA (a primeira em 249 fichas, a segunda rigorosa nas 46 que a primeira aprovou ou deixou em dúvida).

## Resultado

**Em resumo:** 39 candidatas (38 nota A, 1 nota B), 1.109 ha, 26 locais em 14 tiles; 7 não entraram no pacote; o detector marcou 2 dos 17 talhões com árvores já conhecidos. São candidatas, não confirmadas.

O funil, coerente com o resumo principal:

| Etapa | Quantidade |
|---|---:|
| Tiles varridos | 26 |
| Regiões candidatas antes dos filtros | cerca de 970 (26.755 ha) |
| Persistência em 2023 ou 2026, nos 24 tiles novos | 464 → 149 |
| Fichas na 1ª leitura | 249 |
| "Sim" + "incerto" na 1ª leitura | 45 + 1 = 46 |
| Aprovadas na 2ª leitura | **39** (38 nota A, 1 nota B) |
| Rejeitadas | 7 (6 nota C + 1 sem 2ª leitura) |
| Área aprovada | **1.109 ha** |
| Locais distintos | **26**, em 14 tiles, com mais de 3 km entre si |
| Sem amostra atual a menos de 300 m | 37 das 39 |

- A classe sugerida pela IA é **33 IPF e 6 ILF**, mas é palpite; a classe final é trabalho de inspeção.
- **O detector enxerga pouco:** dos 17 talhões com árvores que a equipe já conhece dentro dos tiles, ele marcou 2. No grupo de medição, marcou 0 de 8. O gargalo da esteira é o detector, não a leitura por IA.
- **A persistência foi o achado mais útil:** exigir fileira em mais de um ano cortou 68 das 82 regiões que a primeira leitura havia rejeitado e manteve 12 das 13 aprovadas com nota A. Aplicada antes da leitura, reduz o número de fichas a ler para cerca de 30% sem quase perder amostra boa. A única aprovada que se perderia é a F0353, que tem fileiras visíveis em 2026; o detector é que falhou naquela data.
- **Nenhuma das 39 foi conferida por pessoa.** São candidatas, não amostras confirmadas. O contorno é parcial em talhões pequenos, e espaçamento menor que 12 m não confirmou nenhuma vez.

## Exemplos

As duas fichas abaixo são de **candidatas do detector**, feitas com CBERS-4A de 2 m (INPE, coleção aberta) e a série de NDVI do Sentinel-2. Não são amostras da equipe.

### `exemplo/F0284.png`

Candidata do tile `22KGE_2`, polígono de **8,95 ha**, imagem de **17/08/2025**. A ficha tem três quadros: (A) contexto de 1.300 m com o contorno amarelo da área e o quadrado ciano do detalhe; (B) detalhe de 500 m no centro, onde se veem fileiras escuras paralelas de árvores adultas acompanhando a curva de nível, com pasto claro entre elas; (C) série de NDVI do Sentinel-2 de 2020 a 2025, com subida na chuva e descida suave na seca, sem pico de lavoura. A primeira leitura disse "sim", classe IPF, confiança 0,9, 40 m de espaçamento; a segunda leitura deu **nota A**, 6 fileiras e 30 m; o detector media 25,6 m. É o exemplo comentado de ponta a ponta no `../LEIA-ME.md`.

### `exemplo/F0505.png`

Candidata do tile `22KEG_2`, polígono de **2,72 ha**, imagem de **01/06/2025**. O detalhe B mostra cinco fileiras de árvores adultas com pasto entre elas; o contorno amarelo cobre só parte do conjunto. A primeira leitura disse "sim", IPF, 0,9, 27 m; a segunda deu **nota A**, 5 fileiras e 27 m. A série de EVI2 desta candidata tem novembro/2024 interpolado (não observado), o que está registrado no `../curvas-evi2/LEIA-ME.md`.

## Como rodar

Os scripts foram escritos para a pasta de trabalho do experimento. A raiz é lida de `ILPF_RAIZ`; o projeto do Earth Engine, de `EE_PROJETO` (padrão `"SEU-PROJETO"`).

```bash
export ILPF_RAIZ=/caminho/ilpf-exp
export EE_PROJETO=seu-projeto

# 1. varredura (não usa IA; precisa de internet para o STAC do INPE)
python varrer.py --todos --processos 4
# ou um tile só
python varrer.py --tile 22KGE_2

# 2. fichas dos candidatos (grupo 'listras' em alvos.json)
python 02_fichas.py fichas --so listras

# 3. duas leituras (Gemini pelo agy; prompt em leitura/PEDIDO.md)
python 04_ler.py rodada5_listras --grupos listras --modelo gemini-3.8-flash-high --lote 4
python 04_ler.py rodada5b_rigor --grupos listras --modelo gemini-3.8-flash-high --lote 1

# 4. empacotar as aprovadas
python 13_empacotar.py /caminho/entrega

# 5. persistência (opcional; não usa IA)
python 15_persistencia.py
```

Dependências: Python 3.10+, `numpy`, `opencv-python`, `shapely`, `pyproj`, `Pillow`, `matplotlib`, `requests`, `rasterio`, `geopandas`. A varredura consulta o catálogo STAC aberto do INPE (`CB4A-WPM-PCA-FUSED-1`). A leitura precisa do `agy` no `PATH`; a persistência precisa de `detector.py` e `cbers.py` na mesma pasta.

**Entradas que não estão publicadas e por quê:**

- `alvos.json`: contém os polígonos das 564 regiões candidatas e também as amostras da equipe e as glebas do SICOR. As 39 aprovadas estão publicadas em `resultados/`; o arquivo completo não, por causa dos outros grupos.
- `fichas/`: cerca de 555 PNGs, 0,96 GB, incluindo fichas de amostras da equipe. Só as duas candidatas de exemplo foram publicadas.
- `fichas_meta.json`: data e cena de cada ficha, inclusive das amostras da equipe. Não publicado.
- `leitura/`: cerca de 2,1 GB de leituras brutas, lotes e respostas. O que importa está agregado em `resultados/`.
- `varredura/candidatos/`: as 564 regiões brutas da varredura, antes dos filtros. As 39 aprovadas estão em `resultados/amostras_renques_candidatas.*`; as outras 525 não foram publicadas neste formato. A tabela do classificador em `../classificacao/resultados/uso_saida_detector.csv` lista as 564 com coordenada e probabilidade, porque a regra 2 permite as candidatas do detector.
- `tiles.json`: publicado em versão mínima em `codigo/tiles.json`, só com nome e limites dos 26 tiles, para o `varrer.py --todos` funcionar. O arquivo original também tinha contagem de classes do mapa da equipe.
- `instrucoes-1a-leitura.md` e `instrucoes-2a-leitura-rigorosa.md`: os prompts. Para rodar o `04_ler.py`, copie o prompt desejado para `$ILPF_RAIZ/leitura/PEDIDO.md`, como o script espera.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `instrucoes-1a-leitura.md` | Prompt da primeira leitura: há renques? qual classe? qual espaçamento? |
| `instrucoes-2a-leitura-rigorosa.md` | Prompt da segunda leitura: nota A, B ou C, com checagem cética. |
| `codigo/detector.py` | O detector de textura periódica (OpenCV/NumPy), sem IA. |
| `codigo/varrer.py` | Varre um tile, uma bbox ou os 26 tiles em blocos, funde regiões e grava GeoJSON. |
| `codigo/02_fichas.py` | Monta a ficha PNG de três quadros para cada candidato. |
| `codigo/04_ler.py` | Manda as fichas ao Gemini (`agy`) em lotes e junta as respostas. |
| `codigo/13_empacotar.py` | Junta as duas leituras e grava CSV, GeoJSON, GeoPackage e as fichas. |
| `codigo/15_persistencia.py` | Roda o detector em 2023/2026 e mede a persistência das fileiras. |
| `codigo/cbers.py` | Leitor dos recortes CBERS-4A do catálogo aberto do INPE. |
| `codigo/tiles.json` | Nome e limites dos 26 tiles (versão mínima, sem contagem de classes). |
| `resultados/amostras_renques_candidatas.csv` | As **39 candidatas aprovadas**, com coordenada, área, nota, leitura e ficha. Separador `;`, UTF-8 com BOM. |
| `resultados/amostras_renques_candidatas.geojson` | Os mesmos 39 polígonos, em EPSG:4326. |
| `resultados/resumo_entrega.json` | Contagem do funil: 249 lidas, 39 empacotadas, 38 A, 1 B, 6 C, 204 sem renque na 1ª leitura. |
| `resultados/persistencia.json` | Para cada uma das 100 regiões lidas, o veredito e a cobertura do detector em 2024/2025, 2023 e 2026. |
| `resultados/funil.csv` | O funil em tabela, para leitura rápida. |
| `exemplo/F0284.png` | Ficha de uma candidata com nota A (8,95 ha). |
| `exemplo/F0505.png` | Ficha de uma candidata com nota A (2,72 ha). |

## Limites

- **Nenhuma conferência humana das 39.** A nota A/B é da segunda leitura da IA, não de um inspetor.
- A classe sugerida é palpite da IA; o contorno é parcial em talhões pequenos.
- O detector é sensível à época da imagem; varrer com duas datas deve achar regiões que hoje escapam.
- Espaçamento menor que 12 m não confirmou nenhuma vez.
- A varredura cobre 26 tiles. O detector foi calibrado em 23 recortes de exemplo (11 positivos e 12 negativos); a taxa de acerto fora deles não foi medida.
- A persistência usa 2023 e 2026; o catálogo de 2 m do INPE começa em março de 2023, então não há 2020–2022.

## Fonte

`DIARIO.md` (seções 5, 7b, 108–113 e 136–212), `BALANCO.md` (Frentes A e B), `medicao-3-detector-de-renques/resumo_entrega.json`, `persistencia.json` e os scripts. Os relatórios internos completos não estão neste repositório.
