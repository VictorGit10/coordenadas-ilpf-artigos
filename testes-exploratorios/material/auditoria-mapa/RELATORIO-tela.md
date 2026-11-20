# Relatório — tela de inspeção cega (auditoria piloto ILPF)

> **Nota de publicação.** O código da tela (`baixar_recortes.py`, `analisar_recortes.py`, `verificar_recortes.py`, `inspecao.html`) e os 1.360 recortes não estão neste material. Este relatório fica como registro do que foi construído e conferido.


**Pasta:** `auditoria/tela`
**Execução:** 12/11/2026
**Fonte das imagens:** CBERS-4A WPM, coleção aberta do INPE `CB4A-WPM-PCA-FUSED-1` (TCI, 2 m, cor verdadeira), estação seca.
**Protocolo:** `PROTOCOLO.md` (a pergunta e as seis respostas).

Não abri nenhum arquivo de gabarito. Os dados de auditoria usados e todos os arquivos do projeto lidos/gerados estão na pasta original da tela, que não é publicada aqui.

## 1. O que foi entregue

| Arquivo | Para que serve |
|---|---|
| `baixar_recortes.py` | Baixa os recortes das duas listas, com retomada, espera/retentativa em erro de rede e no máximo 4 downloads simultâneos. Gera `recortes/indice.csv`, `recortes/falhas.csv`, `dados.js` e as imagens. |
| `recortes/` | **1.360 JPEGs** (600 m e 1.500 m) referenciados pelo índice, mais `indice.csv`, `falhas.csv` e logs. Soma dos JPEGs usados: **172,5 MB**. |
| `inspecao.html` | Página única, abre direto do disco, um ponto por vez, imagens de 2024/2025 em destaque e 2023/2026 menores, seis respostas, observação, teclas 1–6, setas, progresso, `localStorage`, “Baixar respostas” e link “ver no mapa”. |
| `dados.js` | Lista de pontos e arquivos, gerada pelo `baixar_recortes.py`. A página não usa `fetch`. |
| `analisar_recortes.py` | Recalcula as contagens deste relatório a partir do índice. |
| `verificar_recortes.py` | Abre todos os JPEGs do índice e confere tamanho, brilho e cruz. |

## 2. Como os recortes foram feitos

Para cada um dos **180 pontos** (150 da fila + 30 da reserva), e para cada ano na ordem **2024, 2025, 2023, 2026**:

1. Consulta o STAC do INPE no retângulo de ±0,02° em volta do ponto, de **1º de maio a 30 de setembro** (estação seca).
2. Ordena as cenas por: cobre o ponto, menor nuvem declarada (quando existe) e data mais recente; tenta até 10 cenas do mesmo ano.
3. Descarta o recorte quando:
   - mais de 10% é preenchimento preto (borda da cena);
   - na imagem **bruta**, mais de 30% dos pixels são claros e azulados (`cinza > 100`, `B > R`, saturação < 0,25) — nuvem/nevoa;
   - mais de 30% é branco puro ou mais de 35% é preto;
   - mais de 40% é nuvem ou a média fica abaixo de 18 / acima de 240;
   - o desvio-padrão é menor que 5, ou o centro de 600 m tem mais de 55% de nuvem, 60% de preto/branco ou desvio menor que 3.
4. Grava duas imagens por cena aprovada: **1.500 m** (750 px, 2 m/px nativo) e **600 m** (600 px, recorte central de 300 px ampliado).
5. Desenha a **cruz fina amarela com contorno preto** no centro (1 px amarelo, 3 px preto, vão de 6–8 px no meio, braços de 24–30 px) e a **data da cena** no canto inferior esquerdo.
6. Salva em arquivo temporário e troca com `os.replace`; o índice é reescrito sem duplicatas. Em erro de rede, espera e tenta de novo (o GDAL também tem retentativas).

A imagem de 600 m é o centro exato do recorte de 1.500 m; a cruz é desenhada depois da ampliação, então fica nítida.

## 3. Cobertura real

### 3.1 Fila (150 pontos)

| Situação | Pontos |
|---|---:|
| Com 2024 **e** 2025 | **148** |
| Só 2024 | **0** |
| Só 2025 | **2** (A119 e A174) |
| Sem nenhuma das duas | **0** |

### 3.2 Reserva (30 pontos)

| Situação | Pontos |
|---|---:|
| Com 2024 **e** 2025 | **30** |
| Só 2024 | **0** |
| Só 2025 | **0** |
| Sem nenhuma das duas | **0** |

### 3.3 Cobertura por ano

| Ano | Fila (de 150) | Reserva (de 30) |
|---|---:|---:|
| 2024 | 148 | 30 |
| 2025 | 150 | 30 |
| 2023 | 148 | 30 |
| 2026 | 121 | 23 |
| Quatro anos | 119 | 23 |

Resumo da execução final: **680 point-anos com imagem**, **32 sem cena** e **8 com cenas mas nenhuma imagem aprovada**, de 720 point-anos. O índice tem **1.360 linhas com `ok=1`** (duas escalas por point-ano).

### 3.4 Pontos sem 2024 e 2025 e reservas

**Nenhum ponto da fila ficou sem as duas datas principais.** Portanto, **nenhuma reserva precisa substituir ponto algum**. Os 30 pontos de reserva também têm 2024 e 2025; a lista está em `pontos_reserva_cega.csv` e os recortes em `recortes/`. Se algum ponto for descartado por outro motivo, o primeiro reserva da ordem do arquivo é **A017**.

Os dois pontos da fila com só uma data principal são **A119** e **A174**: os dois têm 2025 e 2026, mas não têm 2024. Eles podem ser julgados pela imagem de 2025; não precisam de reserva.

## 4. Conferências feitas

- **Download completo:** a execução final terminou as 720 tarefas com o resumo acima; o índice foi reescrito e o `dados.js` foi gerado.
- **5 recortes de pontos diferentes abertos e conferidos visualmente:**
  - `A024_2024_1500.jpg` (2024-09-05)
  - `A049_2024_1500.jpg` (2024-09-15)
  - `A071_2024_600.jpg` (2024-09-16)
  - `A097_2024_600.jpg` (2024-09-26)
  - `A118_2025_600.jpg` (2025-09-23)

  Em todos a cruz está no centro, com vão no meio, e a imagem não é preta. A071 é um solo claro, mas tem textura e a cruz aparece; A118 tem tom azulado, mas as copas são visíveis.
- **Correção feita durante a revisão:** a primeira cena de A064 em 2024 (2024-09-16) tinha nuvem evidente e passou no filtro inicial. O filtro foi reforçado com a checagem na imagem bruta e a cena foi refeita com **2024-08-16**.
- **Conferência automática:** `verificar_recortes.py` abriu os **1.360 JPEGs** do índice: **0 problemas** de tamanho, brilho ou cruz. O brilho médio ficou entre **31,2** e **226,5**. Em 60 imagens o centro tem cor amarelada do próprio terreno (pasto/solo), não a cruz; a inspeção visual confirmou o vão.
- **JavaScript:** o script inline de `inspecao.html` foi extraído para `_check_inspecao.js` e passou em `node --check` (saída 0). Os três scripts Python passaram em `python -m py_compile`.
- **Página:** testada com Chrome headless (Playwright): A001 abriu com 8 imagens 600×600/750×750, sem erro de console; teclas 1–6, setas, observação, ampliação, `localStorage`, download de `respostas_auditoria.json` e a amostra `?n=5&semente=7` funcionaram. Também conferi A118 (sem 2026) e A119 (sem 2024 e 2023): os lugares “sem imagem” aparecem corretamente.

## 5. Problemas encontrados

- **2026 é o ano mais fraco:** 121 dos 150 pontos da fila e 23 dos 30 reservas têm imagem de 2026. Faltam 28 point-anos por ausência de cena no catálogo e 8 por cena só na borda do tile. Como 2026 é a última prioridade, isso não afeta a pergunta principal, que usa 2024 e 2025.
- **Duas datas principais:** A119 e A174 não têm 2024 (só 2025/2026). Não há ponto sem 2024 e 2025 ao mesmo tempo.
- **Oito cenas descartadas por borda**, todas de 2026: A012, A030, A089, A091, A100, A112, A146 e A158. O motivo está em `recortes/falhas.csv` (o log guarda também tentativas antigas; essas oito são as que continuam sem imagem); o programa tentou outras datas do mesmo ano.
- **Nuvem em A064/2024:** a cena de 2024-09-16 tinha nuvem/nevoa azulada e passou no filtro inicial; depois da revisão, foi trocada por 2024-08-16. O filtro atual rejeita esse tipo de cena pela fração de pixels claros e azulados na imagem bruta.
- **Tom azulado em algumas cenas** (por exemplo A118): é característica do TCI do CBERS em parte das datas. As copas e fileiras continuam visíveis; quando a dúvida for real, a resposta “Não dá para dizer” está disponível.
- **Rede:** não houve falha persistente nesta execução. O programa tem espera, novas tentativas e retomada; se uma execução for interrompida, basta rodar de novo.
- **Chave do JSON:** o arquivo `respostas_auditoria.json` usa a chave `observação` (com acento), em UTF-8, além de `id`, `resposta` e `hora`. Os valores de `resposta` são `renque`, `plantio_fechado`, `arvores_espalhadas`, `vegetacao_nativa`, `sem_arvores` e `nao_da_para_dizer`.
- **Amostra:** `?n=40&semente=7` seleciona uma parte sorteada de forma repetível, mas **preserva a ordem da fila**; não é uma reordenação.

## 6. Como rodar de novo

```bat
cd auditoria/tela
python baixar_recortes.py
```

- **Retomada:** para cada ponto/ano, se as duas escalas estão no `indice.csv` e no disco, o programa pula. Para completar o que faltou, rode o mesmo comando de novo.
- **Refazer tudo** (ou um ponto/ano) e sobrescrever as imagens:
  `python baixar_recortes.py --refazer`
  `python baixar_recortes.py --refazer --pontos A064 --anos 2024`
- **Só regerar o `dados.js`:** `python baixar_recortes.py --so-dados`
- **Teste rápido:** `python baixar_recortes.py --limite 3`
- **Recalcular as contagens:** `python analisar_recortes.py`
- **Conferir os JPEGs:** `python verificar_recortes.py`
- **Abrir a página:** `auditoria/tela/inspecao.html`
- **Amostra repetível:** `inspecao.html?n=40&semente=7`
- No fim da inspeção, clique em **“Baixar respostas”** e salve `respostas_auditoria.json` nesta pasta.

## 7. Limitações

- É uma **auditoria piloto**, não uma validação. A definição, a lista de pontos e a regra de contagem são as do `PROTOCOLO.md`.
- A cobertura de 2026 é menor porque há menos cenas de estação seca no catálogo e algumas foram descartadas por nuvem/borda. 2026 é a última prioridade; 2024 e 2025 estão praticamente completos.
- A imagem de 600 m é ampliada de 300 px nativos (2 m/px); ela não cria detalhe novo, só facilita a leitura.
- O TCI do CBERS tem variação de cor entre datas (às vezes puxa para o azul/roxo). Isso não foi tratado como nuvem quando as fileiras continuam visíveis.

## 8. Arquivos de teste

Os arquivos `teste_*`, `thumb_*`, `raw_*`, `teste_pagina*.png`, `_check_inspecao.js` e `_teste_respostas*.json` são sobras das conferências e não são usados pela página. Nada foi apagado.
