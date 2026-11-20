# Curvas de EVI2: a receita da equipe, reproduzida

**Frente:** reprodução do método de EVI2 de 13 meses da equipe e aplicação às 39 candidatas do detector. **Data:** 12/11/2026.

## O que foi testado

A equipe usa a curva mensal de EVI2 como entrada da TempCNN. O método foi reconstruído a partir do repositório público `lapig-ufg/LAPIG-Rede-ILPF` e conferido contra a planilha `samples_iCLS.csv`:

- Sentinel-2 **TOA**, coleção `COPERNICUS/S2_HARMONIZED`, bandas B4 e B8;
- máscara **Cloud Score Plus**, banda `cs`, limiar **0,6**;
- EVI2 = `2,5 × (B8 − B4) / (B8 + 2,4 × B4 + 1)`, com reflectâncias de 0 a 1;
- mediana mensal **por pixel** e depois mediana **dentro do polígono**;
- meses sem observação preenchidos por **interpolação linear** entre os meses vizinhos; nas bordas, repete o vizinho válido mais próximo;
- 13 meses, de outubro do ano da safra a outubro do ano seguinte.

A conferência usou 21 registros do grupo de ensino, de todas as classes e safras de 2018/2019 em diante. Depois, o método foi aplicado às **39 candidatas do detector** da safra 2024/2025 (33 IPF e 6 ILF, pela classe sugerida pela IA).

## Resultado

**Em resumo:** a receita foi reproduzida com diferença média de 3,7 × 10⁻⁸ em 21 registros; 17 dos 507 meses das 39 foram interpolados; as curvas são descritivas, não uma validação de classe.

- **A receita foi reproduzida com erro de máquina:** correlação mediana 1,000000 (a menor foi 0,9999999996) e diferença média absoluta de **3,7 × 10⁻⁸**. A maior diferença em um único mês foi **9,5 × 10⁻⁶** (0,0000095, quinta casa decimal). O critério pedido — correlação mediana ≥ 0,9 e diferença média ≤ 0,05 — é atendido com folga.
- **O limiar de nuvem é 0,6, não 0,50.** O pipeline publicado usa 0,50, mas só 0,6 reproduz os casos difíceis da planilha. O script exato das curvas não está no repositório público; o método foi reconstruído por tentativa e conferido por reprodução.
- **Nas 39 candidatas, 12 amostras tiveram 17 meses sem observação válida** (3,4% dos 507 meses), preenchidos por interpolação. A F0780 tem três meses seguidos (novembro/2024 a janeiro/2025) interpolados; a F0505 tem novembro/2024.
- **As curvas são descritivas, não uma validação de classe.** Em geral ficam acima da mediana de Pastagem e próximas da mediana de IPF, como esperado para sistemas com árvores; algumas ILF têm picos fortes no meio da safra, compatíveis com lavoura em rotação.
- **Não há validação direta nas 39:** elas não têm linha na planilha, então não há gabarito para comparar. A validação é nos 21 registros de ensino; o método é o mesmo para todos.

## Como rodar

Os scripts usam arquivos do diretório corrente e o projeto do Earth Engine em `EE_PROJETO` (padrão `"SEU-PROJETO"`). Não há caminho absoluto neles; a pasta de trabalho precisa conter os arquivos de entrada.

```bash
export EE_PROJETO=seu-projeto

# conferir o método nos 21 registros de ensino
python validacao_metodo.py      # lê registros_ensino.gpkg e samples_iCLS.csv

# gerar as curvas das 39 candidatas
python gerar_curvas_39.py       # lê amostras_renques_candidatas.gpkg e samples_iCLS.csv

# gráfico da conferência (opcional; precisa de validacao_20.csv)
python plot_conferencia.py
```

Dependências: Python 3.10+, `earthengine-api` autenticado, `geopandas`, `pandas`, `numpy` e `matplotlib`. O `gerar_curvas_39.py` grava `curvas_evi2_39.csv`, `cobertura_39.csv` e `curvas_39.png`; o `validacao_metodo.py` grava `validacao_20.csv`; o `plot_conferencia.py` grava `conferencia_6.png`.

**Entradas que não estão publicadas e por quê:**

- `samples_iCLS.csv`: a planilha da equipe, com 1.962 linhas, `ID_ponto`, classe e os 13 valores de EVI2. É amostra da equipe; a regra 1 do briefing manda excluir. O script usa a planilha só para comparar e para as medianas de IPF e Pastagem do gráfico.
- `registros_ensino.gpkg`: os 859 polígonos do grupo de ensino da equipe. Não publicado.
- `amostras_renques_candidatas.gpkg`: o GeoPackage das 39 candidatas. Os mesmos 39 polígonos estão em `../detector-de-renques/resultados/amostras_renques_candidatas.geojson` e a tabela em `.csv`; o GPKG não foi duplicado.
- `validacao_20.csv`, `validacao_resumo.csv` e `conferencia_6.png`: a conferência registro a registro e o gráfico dos 21 registros de ensino, com identificadores da equipe. Não publicados.
- `curvas_evi2_39.csv` e `cobertura_39.csv`: a tabela por amostra e os valores brutos por mês das 39. Não publicados por causa da regra do briefing para `curvas-evi2/*_39.csv`. O agregado e a curva de uma candidata estão em `resultados/`.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `codigo/validacao_metodo.py` | Recalcula a curva de 21 registros de ensino e compara com a planilha. |
| `codigo/gerar_curvas_39.py` | Gera as curvas de 13 meses das 39 candidatas e o gráfico. |
| `codigo/plot_conferencia.py` | Desenha 6 registros da conferência (planilha × cálculo). |
| `resultados/validacao_metricas.json` | Correlação mediana, MAD médio, MAD máximo e MAD por mês da conferência. |
| `resultados/evi2_por_classe.csv` | Mediana mensal das 33 IPF e das 6 ILF, sem identificadores. |
| `resultados/evi2_F0284.csv` | A curva de 13 meses da candidata F0284, usada no exemplo comentado. |
| `exemplo/evi2_candidatas.png` | As 39 curvas (azul = IPF, verde = ILF) sobre as medianas de IPF (vermelha) e Pastagem (cinza tracejada) da planilha. |

## O que se vê no exemplo

`exemplo/evi2_candidatas.png` mostra as 39 curvas de EVI2 da safra 2024/2025. As linhas finas azuis são as 33 candidatas sugeridas como IPF; as verdes, as 6 sugeridas como ILF. As linhas grossas são as medianas de IPF (vermelha) e de Pastagem (cinza tracejada) calculadas da planilha da equipe, não das candidatas. As candidatas ficam, em geral, acima da Pastagem e em torno da IPF; a linha verde que sobe muito em abril–maio é uma ILF com pico de lavoura. O gráfico é **descritivo**: não prova que as 39 sejam IPF ou ILF, porque a classe é palpite da IA e ninguém conferiu os polígonos em campo.

## Limites

- O script exato das curvas não é público; a evidência é a reprodução exata em 21 registros, não a leitura do código original.
- O limiar 0,6 não está no pipeline publicado (que diz 0,50). Isso indica que o script das curvas usava outro limiar ou outra versão.
- 17 dos 507 meses das 39 (3,4%) foram interpolados; em F0780 são três meses seguidos. O valor interpolado pode suavizar uma mudança real.
- As 39 não têm gabarito; a conferência é só no ensino.
- A geometria usada é a do GeoPackage como está; todas as 39 eram polígonos válidos, não vazios.
- A classe das 39 é a sugerida pela IA, não a final.

## Fonte

`curvas-evi2/RELATORIO.md`, `DIARIO.md` (seção 214–220), `BALANCO.md` (Frente C), `gerar_curvas_39.py`, `validacao_metodo.py` e `validacao_metricas.json`. O relatório interno completo, com a tabela dos 21 registros, não está neste repositório.
