# Revisões do plano por outras IAs

**Frente:** revisão cruzada do plano do experimento por quatro modelos, em 12/11/2026.

## O que foi testado

O plano do experimento foi escrito e submetido a revisores independentes antes de virar execução. Foram dois pedidos:

1. **`PEDIDO.md`** — a situação, os números até 12/11 e o plano em três caminhos (auditar o mapa, melhorar o classificador, fechar os artigos). Três modelos responderam: Gemini 4 Hydrogen (esforço alto), DeepSeek v4.1 Flash (esforço máximo) e Kimi K3.1 Pro.
2. **`PEDIDO-2-plano-revisado.md`** — o plano revisado depois das três opiniões, com as restrições do pesquisador (trabalho individual, sem envolver a equipe antes de ter resultado, cotas limitadas). O Claude Fable 5.2 revisou essa versão.

Os pareceres são textos independentes; alguns marcam **[F]** o que foi conferido nos arquivos e **[O]** o que é opinião. Nenhum revisor rodou treino, leitura de imagem ou varredura.

## Resultado

**Em resumo:** quatro pareceres; o plano corrigiu a conta do mapa (33% → 26%), a safra 2026/2027 e a parada do treino; os pareceres discordam sobre a ordem das etapas.

- **A revisão mudou o plano.** Foram aceitos: corrigir a conta do mapa para Web Mercator (33% → 26%); reconhecer que 2026/2027 é safra válida; tratar o classificador como ordenador, não como juiz; separar o teste da TempCNN para depois da confirmação humana; não ampliar os artigos antes de fechar os 5 a 7 candidatos; e registrar que o rótulo é "árvore", não "renque".
- **O erro maior apontado foi no código da equipe:** `repo_04.py` separa treino e teste por linha (o mesmo talhão em safras diferentes cai dos dois lados) e usa o teste para a parada antecipada. O teste de separação da frente de classificação (`../classificacao/`) confirmou que a parada no teste infla a nota; separar por lugar, sozinho, não mostrou efeito.
- **A conta do mapa foi corrigida por causa da revisão:** a primeira versão tratava as imagens como grade regular em latitude; elas estão em Web Mercator. O número do IPF fora do uso agropecuário caiu de 33% para 26%.
- **Os pareceres discordam em pontos importantes:** o Gemini recomendou testar a TempCNN antes de buscar mais dados; o DeepSeek e o Kimi recomendaram o contrário (primeiro definir renque, depois auditar o mapa e confirmar as 39, e só então treinar). O plano revisado adotou a segunda ordem.
- **Nenhum parecer é uma medição.** São opiniões informadas pelos arquivos; os números que citam são os do diário e dos relatórios da época, alguns depois corrigidos.

## Como ler

Não há código nesta frente: o material é o pedido e os quatro pareceres. Os arquivos citados nos pareceres (`DIARIO.md`, `ANALISE-CAMINHOS.md`, `RELATORIO-classificador.md`, `RELATORIO-curvas.md`, `LEIA-ME-artigos.md`, `repo_03.py`, `repo_04.py`, `repo_05.py`, `cruzar.py`, `nas39.py`, `CONTEXTO.md`) são internos e não estão publicados. As notas de publicação no topo dos dois pedidos e a nota desta pasta explicam isso. Os links absolutos dos pareceres foram trocados pelos nomes dos arquivos entre crases; nenhum aponta para fora do repositório.

## Arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `LEIA-ME.md` | Este texto. |
| `resultados/PEDIDO.md` | Pedido original de revisão, com a situação e o plano em três caminhos. |
| `resultados/PEDIDO-2-plano-revisado.md` | Pedido de revisão do plano revisado, com as restrições do pesquisador. |
| `resultados/gemini-4-hydrogen-high.md` | Parecer do Gemini 4 Hydrogen (esforço alto). |
| `resultados/deepseek-v4.1-flash-max.md` | Parecer do DeepSeek v4.1 Flash (esforço máximo). |
| `resultados/kimi-k3.1-pro.md` | Parecer do Kimi K3.1 Pro. |
| `resultados/claude-fable-5.2-revisao-do-plano.md` | Parecer do Claude Fable 5.2 sobre o plano revisado. |

Os nomes dos arquivos são os dos modelos que responderam, não os de pessoas. Os pareceres foram publicados como foram escritos, com a limpeza de caminhos e de identificadores de talhões.

## Limites

- Os pareceres são opinião, não resultado experimental.
- Foram escritos antes das correções de 13/11; alguns números (por exemplo, o "um terço" do IPF) são a versão preliminar. A conta corrigida está no `../auditoria-mapa/LEIA-ME.md` e no resumo principal.
- Os revisores não tiveram acesso a todos os dados; o Claude, por exemplo, não abriu `ANALISE-CAMINHOS.md`, `RELATORIO-curvas.md` nem `LEIA-ME-artigos.md`.
- As recomendações foram discutidas e aceitas ou rejeitadas pelo pesquisador; o material registra o debate, não uma decisão automática.
- Não há exemplo de imagem nesta frente: o material é textual.

## Fonte

`opinioes-2026-11-12/PEDIDO.md`, `opinioes-2026-11-12/PEDIDO-2-plano-revisado.md` e os quatro pareceres; `DIARIO.md` (seções 232–246 e 268–275); `BALANCO.md` (Frente D). Os arquivos internos citados nos pareceres não estão neste repositório.
