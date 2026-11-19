# Dados completos das coordenadas

Esta pasta é uma exportação de leitura dos dados que alimentam o site
`coordenadas-ilpf-artigos`. O site mostra só os pontos de nível A e B; aqui
estão também as 228 coordenadas de nível C e a lista dos 588 documentos lidos.

Nada nesta pasta altera o site. Os arquivos foram gerados a partir dos dados
do pipeline (a pasta `dados/` e o `site/referencia.js`), que não estão
incluídos neste repositório. O `gerar.py` fica como registro de como a
exportação foi feita; ele só roda no ambiente do pipeline.

## Arquivos

| arquivo | o que é |
|---|---|
| `gerar.py` | Script Python (só biblioteca padrão) que lê as fontes do pipeline e grava os quatro arquivos de dados desta pasta. |
| `coordenadas-todas.csv` | 458 linhas: uma por coordenada de nível A, B ou C. Separador `;`, codificação UTF-8 com BOM. |
| `locais-sem-coordenada.csv` | 200 linhas: locais descritos nos artigos para os quais a leitura não achou coordenada. Não são coordenadas jogadas fora. |
| `documentos.csv` | 588 linhas: uma por documento lido, com a situação de cada um. |
| `croquis.geojson` | 3 polígonos desenhados à mão para um artigo (Piquete P4, Piquete P5 e vegetação nativa da Fazenda Capivara). |
| `LEIA-ME.md` | Este arquivo. |

## Como os arquivos foram gerados

O `gerar.py` lê `../../dados/coordenadas.csv`, `extracao.json`,
`checagens.json`, `confirmacao_imagem.json`, `resumo.json`, `fila.json`,
`sessoes.json`, `candidatos.json` e `candidatos_novo.json`, além de
`../../site/referencia.js`. Nenhum desses arquivos está neste repositório: os
PDFs e os dados do pipeline não foram publicados. Por isso o script não roda a
partir do repositório público; ele fica como registro de como os quatro
arquivos de dados desta pasta foram gerados.

No ambiente do pipeline, ele usa caminhos relativos ao próprio arquivo, então
pode ser rodado de qualquer pasta. Ele sobrescreve os quatro arquivos de dados
e não mexe em mais nada.

## `coordenadas-todas.csv`

Uma linha por coordenada, ordenada por nível (A, B, C) e, dentro do nível,
por `id_documento` e `id_ponto`. As colunas são:

| coluna | significado |
|---|---|
| `nivel` | `A`, `B` ou `C`, conforme a conferência por programa do `04_conferir.py` (não publicado). |
| `motivo_classificacao` | Explicação em português do motivo do nível. Para A, descreve os critérios que o programa exigiu; para B e C, traduz os motivos registrados no `coordenadas.csv` e nas checagens. |
| `id_ponto` | Chave do ponto. Para A e B é `id_do_documento-número`, a mesma do site; para C é `id_do_documento-Cnúmero`. |
| `id_documento` | Id do trabalho no OpenAlex (começa com `W`). |
| `titulo` | Título do artigo, tese ou publicação. |
| `ano_publicacao` | Ano de publicação. |
| `doi` | DOI sem o prefixo `https://doi.org/`; vazio quando não há. |
| `link` | Link do PDF ou da página do documento. |
| `pagina` | Página do PDF onde aparece a coordenada, quando o texto permite saber. |
| `figura_ou_mapa` | Figura, mapa ou croqui citado pelo artigo, como o texto descreve. |
| `coordenada_literal` | A coordenada copiada do texto, com graus, minutos, segundos, letras e sinais como aparecem na fonte. Quebras de linha internas foram mantidas. |
| `trecho_localizacao` | Trecho curto, também copiado do texto, que diz onde fica o local. Nomes de proprietários foram substituídos por `[nome omitido]`; o resto é literal. |
| `lat` | Latitude em graus decimais; sul é negativo. Vazio em 1 linha de nível C que não pôde ser convertida (`W3131906203`, coordenada em UTM). |
| `lon` | Longitude em graus decimais; oeste é negativo. Vazio em 2 linhas: `W3131906203` (UTM) e `W7218150270` (longitude incompleta no texto). |
| `precisao_m` | Margem aproximada em metros, calculada pela forma escrita (segundos, minutos ou casas decimais). `0` quer dizer menos de 1 m; `1850` quer dizer cerca de 1,8 km. Vazio quando não dá para calcular. |
| `a_que_se_refere` | A que a coordenada se refere: `parcela`, `área experimental`, `fazenda ou sede`, `município` ou `não diz`. |
| `local` | Nome do local como o artigo o chama. |
| `fazenda` | Fazenda, estação, instituição ou propriedade. Vazio quando o texto não informa. |
| `municipio` | Município. Vazio quando o texto não informa. |
| `uf` | Unidade da federação. Vazio quando o texto não informa. |
| `classes` | Classes estudadas e de comparação, no formato `ILP (estudado) | Pastagem (comparação)`. Repetições idênticas foram consolidadas. |
| `periodo` | Anos de implantação e de avaliação, no formato `implantação 2010; avaliação 2021`. Vários sistemas são separados por ` | `. Vazio quando o texto não dá ano. |
| `conferencia_imagem` | Conferência visual na imagem de satélite, só para A e B: `sim — nota`, `incerto — nota` ou `não — nota`. Para C fica vazio, porque a conferência de imagem foi feita só nos pontos A e B. `incerto` é o que o site chama de "compatível, sem confirmação". |

Os níveis não são uma medida de verdade no campo. Eles resumem o que o texto
afirma e o que o programa conseguiu conferir:

- **A:** a coordenada é de parcela ou área experimental, a precisão é de
  segundos (ou melhor) e o texto diz a classe e o ano.
- **B:** a precisão é boa, mas a coordenada é da fazenda, da sede ou da
  estação, ou o texto não diz a que ela se refere, ou falta o ano.
- **C:** precisão só em minutos (~1,8 km) ou pior que 100 m, coordenada de
  município, número que não confere com o texto, trecho que não existe no
  texto, coordenada impossível (minuto ou segundo acima de 60), fora do
  Brasil, ou ponto que cai na cidade ou em área construída.

## `locais-sem-coordenada.csv`

Estas 200 linhas não são coordenadas descartadas. São **locais que o artigo
descreve mas para os quais a leitura não encontrou latitude e longitude**.
Elas ficam separadas para o pesquisador saber o que foi lido e não virou ponto
no mapa.

As colunas são as mesmas de `coordenadas-todas.csv` para os dados de
identificação (`id_documento`, `titulo`, `ano_publicacao`, `doi`, `link`,
`local`, `fazenda`, `municipio`, `uf`, `classes`, `periodo`,
`figura_ou_mapa`, `trecho_localizacao`), mais:

| coluna | significado |
|---|---|
| `nivel` | Sempre `sem coordenada`. |
| `motivo_descarte` | Sempre a mesma explicação: o texto descreve o local, mas não informa latitude e longitude. |
| `id_local` | Chave sequencial do local dentro do documento (`id_do_documento-Sn`). Serve para esta exportação; não é um id do artigo. |

As 200 linhas vêm de 142 documentos: 137 documentos não têm nenhuma
coordenada e 5 têm algumas coordenadas e pelo menos um local sem coordenada.

## `documentos.csv`

Uma linha por documento dos 588 lidos. As colunas são:

| coluna | significado |
|---|---|
| `id_documento` | Id do trabalho no OpenAlex. |
| `titulo` | Título. |
| `ano_publicacao` | Ano de publicação. |
| `doi` | DOI sem `https://doi.org/`; vazio quando não há. |
| `link` | PDF ou página do documento. |
| `estudo_de_campo` | `sim` ou `não`, conforme a leitura do texto. |
| `n_locais` | Quantos locais o texto descreve (pode haver mais de um por documento). |
| `n_coordenadas` | Quantas coordenadas A, B ou C o documento tem. Pode ser maior que `n_locais` quando o mesmo local tem mais de uma coordenada. |
| `n_A`, `n_B`, `n_C` | Quantas coordenadas de cada nível. |
| `situacao` | `com coordenada A/B`, `só coordenada C`, `local sem coordenada` ou `não é estudo de campo`. |

A ordem é por situação (A/B, depois só C, depois sem coordenada, depois não
estudo de campo) e, dentro de cada grupo, por `id_documento`.

## A fila de 856 e os 588 lidos

A fila inicial do OpenAlex tinha 856 trabalhos. As quatro sessões de leitura
tentaram os 856: 588 foram lidos e 268 ficaram sem PDF (13 na sessão 1, 18 na
2, 154 na 3 e 83 na 4). Não há trabalho da fila que tenha sido deixado de
tentar; os 268 são falhas de download, não descartes por escopo. A lista dos
268 está em `dados/sessoes.json` (campo `falhas` de cada sessão) e em
`dados/baixados.json` (campo `falhas`); nenhum dos dois está publicado.

A rota anterior, com BDTD, Embrapa e busca na web, leu 131 documentos e achou
181 locais; dela saíram 25 candidatos e 5 regiões nota A (Santa Brígida em
Ipameri, Boa Vereda em Cachoeira Dourada e três áreas no DF), todas fora dos
26 tiles. Esses 131 documentos e as 5 nota A não estão em `documentos.csv` nem
no site. O total de documentos lidos no experimento é 588 + 131 = 719.

## `croquis.geojson`

Há 3 polígonos desenhados, todos do artigo `W4220961814` (Oliveira et al.,
2022, sobre a Fazenda Capivara, em Santo Antônio de Goiás/GO):

- `capivara-P4`: Piquete P4, ILP;
- `capivara-P5`: Piquete P5, ILP;
- `capivara-NV`: área de vegetação nativa vizinha.

Cada feição tem `properties.id_documento` (o id OpenAlex do artigo) e
`properties.descricao` (nome, classe, município, figura de origem e áreas).
Também estão lá `id_area`, `nome`, `classe`, `area_artigo`,
`area_desenho`, `figura`, `titulo`, `autores`, `ano`, `revista`, `doi` e
`historia`.

As coordenadas estão em WGS84, na ordem do GeoJSON (`[longitude, latitude]`),
e os anéis foram fechados. As áreas foram desenhadas à mão a partir da Figura
2 do artigo; a área do desenho é próxima da área que o artigo informa
(P4: 7,3 ha no desenho contra 7,5 ha no artigo; P5: 7,7 ha contra 8,1 ha).

Não há outros desenhos vetorizados. 151 documentos dos 588 citam mapa ou
croqui, mas nenhum deles foi transformado em polígono nesta exportação: a
figura deles está apenas no PDF. Os 3 polígonos acima vêm de um artigo fora
dos 588 (`W4220961814`), da camada de referência do site; por isso esse id não
aparece em `documentos.csv`.

## Como os números se reconciliam

| número | o que é |
|---|---|
| **588** | Documentos lidos (`extracao.json`). |
| **513** | Documentos classificados como estudo de campo. |
| **75** | Documentos que não são estudo de campo (revisão, modelagem, texto sem área de campo). |
| **644** | Locais descritos nos 513 documentos de campo. |
| **444** | Locais com pelo menos uma coordenada. |
| **200** | Locais sem coordenada (as linhas de `locais-sem-coordenada.csv`). |
| **458** | Coordenadas: 444 locais com coordenada, sendo que 12 locais têm mais de uma coordenada (11 com 2 e 1 com 4), o que acrescenta 14 linhas. |
| **125 A + 105 B + 228 C = 458** | Contagem por nível. Bate com o resumo do pipeline (`dados/resumo.json`) e com o site (`site/dados.js`), que não estão neste repositório. |
| **230** | Pontos A e B que aparecem no site (125 + 105). |
| **228** | Pontos C que só aparecem nesta exportação. |
| **376** | Documentos com pelo menos uma coordenada A, B ou C. |
| **188** | Documentos com coordenada A/B (o melhor nível deles é A ou B). |
| **188** | Documentos só com coordenada C. |
| **137** | Documentos de campo sem nenhuma coordenada. |
| **43** | Pontos A/B (dos 230) confirmados na imagem de satélite; 139 ficaram incertos e 48 não conferem. |

Fechando os 513 documentos de campo: 188 com A/B + 188 só com C + 137 sem
coordenada = 513. Os outros 75 completam os 588.

### Por que o `coordenadas.csv` tem 779 linhas e o resumo fala em 458?

Não há 321 coordenadas escondidas. A conta é:

- 458 linhas de coordenada (A, B e C);
- 200 linhas de local sem coordenada (as que estão em
  `locais-sem-coordenada.csv`);
- 121 quebras de linha dentro de campos entre aspas (principalmente no
  `texto_literal`, que às vezes ocupa duas ou três linhas).

458 + 200 + 121 = **779 linhas físicas de dados**, sem contar o cabeçalho. O
arquivo tem 659 registros CSV (1 cabeçalho + 658 linhas de dados); quem conta
linhas físicas vê 779, 780 ou 781 conforme a ferramenta conte ou não o
cabeçalho, a última linha ou um caractere de controle (`U+001C`) que veio de
um PDF. O conteúdo real é 658 registros: 458 coordenadas e 200 locais sem
coordenada.

### Coordenadas repetidas

Há 5 pares de linhas com o mesmo `id_documento` e o mesmo par latitude/
longitude. Eles foram mantidos, porque o artigo descreve mais de um local no
mesmo ponto ou cita o mesmo local duas vezes (duas grafias ou duas páginas).
Por isso 458 linhas correspondem a 453 pares únicos de documento + latitude +
longitude. O caso mais visível é o do artigo `W4302742817`, em que os "Site
13" e "Site 14" têm a mesma coordenada; é também por isso que
`confirmacao_imagem.json` tem 229 chaves para 230 pontos A/B: os dois sites
compartilham a mesma chave de conferência.

### Os 43 confirmados

A conferência na imagem foi feita nos 230 pontos A/B. Como dois pontos
compartilham a mesma coordenada, existem 229 chaves em
`confirmacao_imagem.json`. O resultado dos 230 pontos é:

- **43** `sim` (confirmados);
- **139** `incerto` (o site chama de "compatível, sem confirmação");
- **48** `não` (não conferem).

43 + 139 + 48 = 230. O número 43 não é um nível novo nem muda A ou B; é um
selo separado, que olha a imagem de satélite atual.

## O que não bateu

- O `dados/resumo.json` traz `docs_com_coord_regex = 380` e
  `docs_com_coord_ia = 376`, mas a lista `docs_regex_mas_ia_nao` tem 20 ids,
  não 4. Os 20 ids realmente não têm coordenada no `coordenadas.csv`. Os
  contadores e a lista parecem vir de execuções diferentes do script; os
  totais usados nesta exportação (588, 513, 458, 125, 105, 228) batem com o
  CSV e com o site.
- O `site/README.md` diz que os 230 pontos estavam conferidos (43 + 139 +
  48). O arquivo `confirmacao_imagem.json` tem 229 chaves porque dois pontos
  A (Site 13 e Site 14) compartilham a mesma coordenada e, portanto, a mesma
  conferência. Não falta ponto.
- Uma linha de nível C não tem latitude nem longitude: `W3131906203` (a
  coordenada está em UTM). Outra, `W7218150270`, tem a latitude
  (`-21.145408`) e a longitude vazia, porque o texto traz só a latitude e um
  pedaço da longitude. No total, `lat` está vazio em 1 linha e `lon` em 2; as
  duas continuam no arquivo com o motivo explicado.
- Dezoito linhas de nível C não têm `precisao_m` porque a forma escrita não
  permite calcular a margem (UTM, número incompleto, texto corrompido).

## Limitações

- O nível A ou B diz o que o texto afirma da coordenada, não se o sistema
  existe no lugar. A conferência na imagem é um selo separado e olha 700 m em
  volta do ponto; não substitui a inspeção do talhão.
- O motivo da classificação foi traduzido do que o `04_conferir.py` e o
  `checagens.json` registraram. Não foi feita uma nova leitura dos artigos.
- Para A, o motivo descreve os critérios do programa (parcela/área
  experimental, precisão de segundos, classe e ano no texto). Para B e C, ele
  traduz os motivos gravados no CSV.
- A precisão de 17 linhas de nível C foi calculada errado pelo pipeline. As
  15 linhas do `W2531023108` têm minutos decimais com três casas
  (`S27 47.963`), o que dá cerca de 2 m, não os 111 m registrados.
  `W2625001271-C1` e `W2887145174-C1` têm só minutos inteiros (`19°05’` e
  `07°25’`), o que dá cerca de 1,8 km, não os 31 m registrados. Elas continuam
  C no arquivo; o motivo registrado inclui "o número não confere com o texto"
  (e, em `W2887145174-C1`, também "a coordenada é da fazenda ou da sede"), mas
  essa checagem do número foi afetada pelo mesmo erro de leitura dos minutos.
  Corrigido o cálculo, essas linhas poderiam ser reavaliadas numa revisão;
  nesta exportação não foram reclassificadas. O motivo de cada uma traz a
  ressalva `(precisão calculada incorretamente pelo pipeline; ver LEIA-ME)`.
- O motivo "o número não confere com o texto", que aparece em 65 linhas C, é
  genérico. O `04_conferir.py` (não publicado) grava só essa frase; não guarda
  qual número foi comparado, qual era o esperado nem o trecho. O `checagens.json` guarda apenas
  a distância à sede municipal e a área construída num raio de 100 m. Por isso
  o motivo não foi detalhado nesta exportação: para saber o número, é preciso
  reler o `texto_literal` e o `trecho_localizacao` da linha. Não foi feita uma
  nova leitura dos artigos.
- Em 11 linhas C, o `coordenada_literal` traz só um dos eixos (latitude ou
  longitude), embora o `trecho_localizacao` às vezes tenha os dois; o
  `lat`/`lon` pode estar certo, mas o campo que serve de prova documental está
  incompleto. Não corrigimos nesta exportação porque isso exigiria reler o
  artigo. Exemplo: `W2898179498-C1`.
- Títulos, anos, DOI e links dos 588 documentos vêm do `fila.json`. Há 68
  documentos sem DOI; o link do PDF ou da página existe para todos.
- Os PDFs e as imagens não estão incluídos. O `link` leva ao documento
  original.
- Nomes de proprietários foram substituídos por `[nome omitido]`, como já
  acontece no site. Nomes de fazendas, assentamentos, escolas e instituições
  foram mantidos. Caracteres de controle vindos dos PDFs foram trocados por
  espaço; o resto do `coordenada_literal` e do `trecho_localizacao` é literal.
- Campos de local, fazenda, município, UF, classe e período ficam vazios
  quando o artigo não informa. Não foram preenchidos por dedução.
- As 200 linhas de `locais-sem-coordenada.csv` são locais sem coordenada, não
  coordenadas descartadas. Nenhuma coordenada A/B/C foi removida por ser
  duplicata.
- Só existem 3 polígonos vetorizados, de um único artigo fora dos 588. Os
  mapas dos 151 documentos dos 588 que citam figura ou croqui estão nos PDFs,
  não aqui. O artigo do croqui (`W4220961814`) não faz parte dos 588 documentos
  lidos; ele vem da camada de referência do site.
- O `id_ponto` dos níveis A e B é o mesmo do site. O dos níveis C é novo
  (`-C1`, `-C2`...) e não aparece no site.
