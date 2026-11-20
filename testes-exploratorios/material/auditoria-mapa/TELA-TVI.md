# LEIA-ME — tela de inspeção do protótipo TVI

> **Nota de publicação.** O código (`tvi.html`, `tvi.css`, `tvi.js`, `dados.js`) e os recortes da tela não estão neste material. O texto descreve o protótipo e serve de referência para quem for reconstruí-lo.


O protótipo tem uma tela de inspeção **estática**: abre direto do disco, sem
servidor, sem banco e sem internet. Ela imita a aparência e o fluxo do TVI
(Temporal Visual Inspection), mas é um **protótipo de estudo**. Não é o TVI
oficial.

## 1. Como abrir

1. Mantenha a pasta inteira como está. A tela precisa de `tvi.html`,
   `tvi.css`, `tvi.js`, `dados.js` e da pasta `recortes/` no mesmo lugar.
2. Dê dois cliques em **`tvi.html`**. Ele abre no navegador.
3. Se o navegador perguntar com o que abrir, escolha Chrome, Edge ou Firefox.
4. Não precisa de internet nem de instalar nada.

Se você copiar só o `tvi.html` para outro lugar, as imagens e os dados não
vão aparecer. Copie a pasta toda.

## 2. Entrar

Na tela de entrada:

1. Em **Campanha**, escolha “Auditoria piloto IPF” (por enquanto é a única).
2. Digite seu **nome de inspetor**. Não há senha.
3. Clique em **Entrar** (ou aperte Enter).

O nome fica guardado no navegador e vai junto com as respostas. Se você
entrar de novo com o mesmo nome, suas respostas anteriores voltam. Se entrar
com outro nome, a tela começa do zero para aquele nome.

## 3. A tela de inspeção

A tela tem quatro partes:

- **Barra escura no topo:** campanha, contador de pontos, barra de progresso,
  seu nome e os botões **Supervisão**, **Baixar respostas** e **Sair**.
- **Linha do ponto:** identificador, coordenada e o link **ver no Wayback**.
  Logo abaixo, recolhida, fica a **Definição: Renque (o “sim”)**.
- **Imagens por ano:** os quatro quadros em ordem cronológica (2023, 2024,
  2025 e 2026), cada um com a data da cena. **2024 e 2025**, os anos da
  pergunta, têm um filete azul e a palavra “safra”. Uma legenda única acima
  das imagens diz a fonte, a resolução e a escala; o seletor **600 m /
  1.500 m** fica à direita.
- **Faixa de classificação:** logo abaixo das imagens, com as seis respostas
  e a observação. À direita dela fica a **Resposta da IA**. Abaixo da faixa
  fica o gráfico da série temporal.

### Responder

- Clique numa das seis respostas ou aperte a **tecla 1 a 6**.
- A resposta é gravada na hora. Ao lado da observação aparece “Resposta
  gravada: …”.
- Escreva o que quiser em **Observação**; o texto é salvo enquanto você digita.
- Use **← Anterior** e **Próximo →**, ou as **setas ← e →**, para mudar de
  ponto.
- A resposta **não avança sozinha** de ponto. Isso é de propósito: assim você
  vê a resposta da IA antes de seguir.

### Imagens, zoom e arrasto

- **600 m / 1.500 m**, na linha acima das imagens, troca o lado do recorte.
  O padrão é 600 m.
- **Roda do mouse** sobre qualquer imagem aproxima. Os quatro quadros
  aproximam juntos, no mesmo lugar.
- **Arraste** com o botão esquerdo do mouse (ou com o dedo, depois de
  aproximar) para mover o enquadramento. O que você move num quadro vale
  para os quatro.
- Os botões **−** e **+**, as teclas **−** e **+** também aproximam. O botão
  **Voltar ao enquadramento** e a tecla **0** desfazem o zoom e o arrasto.
- **Shift + setas** movem o enquadramento. As setas sem Shift continuam
  mudando de ponto. As teclas 1 a 6 continuam respondendo.
- **Clique simples** (sem arrastar) abre a imagem grande; arrastar não abre.
  Clique de novo, aperte **Esc** ou clique no fundo escuro para fechar.
- No modo **1.500 m**, ao aproximar além de 600 m de lado, a tela troca
  sozinha para o recorte de 600 m, mais nítido, quando o enquadramento cabe
  nele.
- A cruz no meio da imagem marca o ponto e acompanha o zoom.
- Se um ano não tiver imagem, o quadro mostra “sem imagem nesta data”. Isso
  acontece em alguns pontos (a maioria em 2026).
- **ver no Wayback ↗** abre o mapa do Esri Wayback em outra aba, centrado no
  ponto. Precisa de internet; a inspeção em si não precisa.

### Definição de renque

A definição fica na linha do ponto, **recolhida**. Clique em
**Definição: Renque (o “sim”)** para abrir os cinco critérios e clique de
novo para fechar. Ela não ocupa espaço na tela enquanto está fechada.

## 4. Respostas de IA

A tela **não** traz resposta de IA por padrão.

1. No painel **Resposta da IA**, ao lado da classificação, clique em
   **Carregar respostas**.
2. Escolha um arquivo `.json` no formato do protocolo, com `"tipo": "ia"`.
3. O status mostra o nome do leitor, o modelo e quantos pontos foram
   carregados. Se o arquivo for de pessoa (`"tipo": "humano"`), a tela recusa.
   Para acrescentar outro arquivo, clique em **Adicionar**; se for o mesmo
   leitor e modelo, o arquivo novo substitui o anterior.

**Regra importante:** a resposta da IA de um ponto **só aparece depois que
você grava a sua resposta naquele ponto**. Enquanto você não responde, o painel
fica com o texto “A resposta da IA aparece depois que você gravar a sua neste
ponto”. A tela não carrega a resposta no fundo antes da hora.

Depois de gravar, aparece, **ao lado da classificação**, o painel
**Resposta da IA** com:

- a resposta da IA;
- a justificativa curta (o campo `observacao` do arquivo);
- se ela **concorda** ou **discorda** da sua resposta.

### Mudar de resposta depois de ver a IA

Se você mudar a resposta depois de ver a da IA, a tela avisa e guarda as duas:

- **resposta original**, com a hora em que foi gravada;
- **resposta revista**, com a hora da mudança.

A resposta original nunca é apagada. No arquivo baixado, ela vai em
`resposta` e a revista em `resposta_revista` (com `hora` e `hora_revista`).
Na supervisão, a resposta revista é a que conta como voto efetivo, mas a
original continua visível.

Se você mudar de resposta antes de carregar a IA, a mudança substitui a
resposta normalmente.

## 5. Baixar as respostas

Clique em **Baixar respostas** na barra do topo. O navegador gera um arquivo:

```
respostas_auditoria_piloto_ipf_<seu_nome>.json
```

Ele vai para a pasta de downloads do navegador. O arquivo tem:

```json
{
  "campanha": "auditoria-piloto-ipf",
  "leitor": "Seu Nome",
  "tipo": "humano",
  "modelo": "",
  "respostas": [
    {
      "id": "A001",
      "resposta": "Renque",
      "observacao": "...",
      "hora": "2026-11-13T...",
      "resposta_revista": null,
      "hora_revista": null
    }
  ]
}
```

As respostas também ficam salvas no navegador (`localStorage`), separadas por
campanha e por nome. Se o navegador bloquear esse armazenamento, a tela avisa:
nesse caso, baixe o arquivo antes de fechar a aba. O botão **Baixar respostas**
é a cópia segura do seu trabalho.

## 6. Supervisão

Clique em **Supervisão** na barra do topo.

1. A tela começa vazia, de propósito.
2. Clique em **Carregar respostas** e escolha **um ou mais** arquivos `.json`
   (pode selecionar vários com Ctrl ou Shift).
3. Cada arquivo vira uma coluna de leitor: pessoa ou IA. O tipo e o modelo
   aparecem embaixo do nome. Para comparar com as suas próprias respostas,
   clique antes em **Baixar respostas** na inspeção e carregue também esse
   arquivo aqui.
4. No topo aparece uma **linha de números** (pontos, leitores, discordâncias,
   concordância média e kappa médio) e, abaixo dela, duas tabelas compactas:
   - **Por resposta**: quantos pontos cada leitor deu em cada uma das seis
     respostas, quantos ficaram sem resposta e o total respondido;
   - **Concordância entre leitores**: para cada par, quantos pontos os dois
     responderam, em quantos concordaram, a concordância simples (%) e o
     **kappa de Cohen** (quando é possível calcular; “—” quando não é).
5. Em **Pontos e votos**, a tabela tem todos os pontos e uma coluna por leitor.
   Linhas com respostas diferentes mostram **“discordam”** em vermelho; as
   demais mostram “concordam”. O selo **rev.** indica resposta revista.
6. Clique em qualquer linha para abrir as imagens dos quatro anos e os votos
   de cada leitor, com observação, hora e revisão. **Esc** fecha.
7. Filtros:
   - **Ponto**: procure por identificador (ex.: A001);
   - **Resposta**: mostra pontos em que pelo menos um leitor deu aquela
     resposta;
   - **Só discordâncias**: só pontos com mais de uma resposta diferente;
   - **Só “não dá para dizer”**;
   - **Limpar filtros** volta tudo.
8. **Limpar leitores** tira todos os arquivos carregados da supervisão.
   **Voltar à inspeção** volta ao trabalho; **Sair** encerra a sessão.

### Arquivos fictícios de teste

Em `teste/` há dois arquivos **inventados**, só para testar a supervisão:

- `teste/FICTICIO_inspetor.json` — leitor “FICTÍCIO inspetor”, tipo humano;
- `teste/FICTICIO_ia.json` — leitor “FICTÍCIO IA”, tipo ia.

Eles não são carregados automaticamente e **não são dados reais**. Não use as
respostas deles para concluir nada sobre os pontos. Para testar, abra a
supervisão e carregue os dois; a concordância e as discordâncias aparecem.

## 7. Mostrar só uma parte dos pontos (opcional)

No endereço da página, depois de `tvi.html`, você pode acrescentar:

```
?n=40&semente=7
```

Isso mostra uma amostra de 40 dos 150 pontos. A mesma semente (`7`) mostra
sempre os mesmos pontos; outra semente sorteia outra amostra. Sem o `n`, a
tela mostra a lista completa. A supervisão continua mostrando todos os pontos
da campanha, porque ela lê os arquivos de resposta, não a amostra da sessão.

## 8. Trocar ou acrescentar campanha

Todos os pontos, imagens, anos, pergunta e respostas ficam em **`dados.js`**.
A tela lê a lista `window.CAMPANHAS` desse arquivo. Para outra campanha, o
arquivo `dados.js` precisa ter a mesma estrutura. O modelo completo está no
cabeçalho do próprio `dados.js` e no `RELATORIO.md`.

Em resumo, cada campanha é um bloco com:

- `chave` (identificador curto, sem espaços), `nome`, `pergunta`;
- `safra` (`rotulo`, `inicio`, `fim`), `anos`, `anosDestaque`;
- `escalas` (ex.: `[600, 1500]`) e `escalaPadrao`;
- `fonte`, `fonteCurta`, `resolucao`;
- `respostas` (as respostas válidas, na ordem das teclas 1 a 6);
- `definicao` (título, itens e nota do painel recolhível);
- `pontos`: cada um com `id`, `lon`, `lat`, `atributos` (opcional) e `anos`,
  onde cada ano tem as escalas com `arquivo` e `data`.

Para trocar a campanha, troque o conteúdo de `dados.js` (mantendo a estrutura)
e recarregue `tvi.html`; a nova campanha aparece na lista de entrada. As
imagens podem ficar em outra pasta, desde que o caminho em `arquivo` seja
relativo ao `tvi.html`.

Se a nova campanha tiver outra pergunta, mude `pergunta`, `definicao`,
`respostas` e `safra`. Se tiver outros anos ou escalas, mude `anos`,
`anosDestaque`, `escalas` e `escalaPadrao`. A lista `anos` é a ordem em que
os quadros aparecem: use ordem cronológica (por exemplo, 2023, 2024, 2025,
2026). Não é preciso mexer no `tvi.html`, no `tvi.css` nem no `tvi.js` para
trocar os pontos.

O arquivo é JavaScript. Se você não programa, peça a alguém para copiar o
bloco de uma campanha e trocar os valores; é fácil errar uma vírgula.

A **série temporal** é opcional e fica em `series.js`. Se a nova campanha não
tiver série, a tela mostra “série temporal não carregada” (ou “não
disponível para este ponto”, se houver uma série de outra campanha). O arquivo
`series.js` atual é da campanha piloto: 150 pontos, NDVI mensal de 2019 a
2025.

## 9. Problemas comuns

- **“dados.js não foi encontrado”** — o `dados.js` não está ao lado do
  `tvi.html`. Abra o `tvi.html` de dentro da pasta, não uma cópia solta.
- **Imagens em branco ou “sem imagem”** — confira se a pasta `recortes/`
  está no lugar e se os caminhos terminam com o nome certo. Alguns pontos
  realmente não têm imagem em certos anos (a maioria em 2026).
- **A resposta da IA não aparece** — responda o ponto primeiro. O painel da
  IA fica ao lado da classificação. Depois, confira se o arquivo é
  `"tipo": "ia"` e se o campo `campanha` é o mesmo da tela. O painel também
  não mostra resposta se a IA não tiver aquele ponto.
- **A roda do mouse aproxima em vez de rolar a página** — é de propósito: a
  roda pertence ao zoom das imagens. Para rolar, use a barra de rolagem, a
  roda fora das imagens ou aperte **0** e use as setas da página.
- **O zoom não move** — o arrasto só tem efeito depois de aproximar. Em
  600 m ou 1.500 m inteiros, a imagem toda já está à vista; use **+** ou a
  roda, depois arraste. **Shift + setas** também movem.
- **A supervisão está vazia** — ela começa vazia; carregue um ou mais
  arquivos. Para testar, use os dois `FICTICIO_*.json`.
- **O navegador bloqueou o armazenamento local** — use **Baixar respostas**
  antes de fechar a aba. A tela avisa quando isso acontece.
- **“série temporal não carregada”** — o `series.js` está ausente ou nulo.
  É opcional; não impede a inspeção.
- **O gráfico aparece, mas com falhas** — meses sem imagem limpa (nuvem) são
  omitidos; a linha se interrompe nesses meses.

## 10. O que a tela guarda e o que ela não faz

- Guarda: seu nome, a campanha escolhida, suas respostas, observações e horas;
  no navegador e no arquivo que você baixar.
- Não guarda: senha (não existe), respostas de outras pessoas (a não ser que
  você carregue os arquivos na supervisão) e a resposta da IA antes de você
  responder.
- Não envia nada para a internet. O link do Wayback só abre se você clicar.
- Não é o TVI oficial. É um protótipo de estudo feito para a auditoria piloto.

No rodapé de todas as telas está escrito: **“Protótipo de estudo. Não é o TVI
oficial.”**
