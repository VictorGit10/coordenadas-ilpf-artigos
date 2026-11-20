# Auditoria piloto do mapa: protocolo (gravado em 12/11/2026, antes de ver qualquer imagem)

## Pergunta
Para cada ponto: **"Na safra 2024/2025 (outubro de 2024 a outubro de 2025), este ponto estava num talhão com árvores plantadas em fileiras?"**

## Definição de renque (o "sim")
Vale "renque" quando, nas imagens de 2024 ou 2025, se vê tudo isto:
1. **Fileiras de árvores**: linhas de copas, retas ou acompanhando o terreno, **paralelas entre si**.
2. **Pelo menos 3 fileiras** lado a lado.
3. **Faixa aberta entre as fileiras** (pasto ou lavoura) mais larga que a própria fileira. Na prática, de uns 10 m a 50 m entre uma fileira e outra.
4. O conjunto ocupa **pelo menos 1,5 ha**.
5. O ponto cai **dentro desse conjunto** (na fileira ou na faixa entre fileiras).

## As respostas possíveis
| Resposta | Quando |
|---|---|
| **Renque** | Atende aos cinco itens acima. |
| **Plantio fechado** | Árvores plantadas em linha, mas sem faixa aberta entre elas (eucalipto denso, seringal, pomar). |
| **Árvores espalhadas** | Pasto ou lavoura com árvores soltas, sem fileiras. |
| **Vegetação nativa** | Mata, cerrado, mata de beira de rio: copas irregulares, sem linhas. |
| **Sem árvores** | Pasto limpo, lavoura, solo, água, cidade. |
| **Não dá para dizer** | Imagem ruim, nuvem, ou dúvida real entre duas respostas. |

Se havia renque em 2023 e ele foi cortado antes de outubro de 2024, a resposta é o que se vê em 2024/2025.

## Os pontos (sorteados com semente fixa 20261112; script `codigo/01_sortear.py`)
| Grupo | Quantos | Para quê |
|---|---|---|
| Sorteados entre os pixels que o mapa publicado chama de IPF | 100 | O número principal |
| Controles: talhões da equipe (grupo de ensino) sempre classificados com árvores | 15 | Medir o acerto de quem inspeciona |
| Controles: talhões da equipe (grupo de ensino) sempre pastagem ou agricultura | 20 | Idem |
| Repetições escondidas de pontos do primeiro grupo | 15 | Medir a consistência de quem inspeciona |

- Total: 150 julgamentos, embaralhados. A fila (`pontos_fila_cega.csv`) só tem identificador e coordenada. O gabarito fica em arquivo separado e só é aberto depois de todos os julgamentos.
- Há 30 pontos de reserva do mesmo sorteio, para substituir pontos sem imagem, na ordem do arquivo.
- Quem inspeciona **não vê** a classe do mapa, o MapBiomas, nem a resposta de outra pessoa ou IA.
- Os 100 pontos foram sorteados com chance igual entre todos os pixels de IPF dos 26 tiles (2,37 milhões de pixels na imagem publicada de 30 m). Bordas não foram excluídas (93 dos 100 têm vizinho de outra classe).

## Quem inspeciona
1. **Leitura por IA** (Gemini), com esta mesma definição e as mesmas imagens, em todos os 150.
2. **Leitura humana** (o pesquisador) numa parte sorteada, sem ver a resposta da IA, para medir a concordância.
3. A confirmação que vale para a equipe é a dos inspetores dela, repetindo os mesmos pontos.

## Como o resultado será dito
"De 100 pontos que o mapa chama de IPF: X renque, P plantio fechado, E árvores espalhadas, N vegetação nativa, S sem árvores, D não dá para dizer", com intervalo de confiança, e com o acerto medido nos 35 controles e a consistência nas 15 repetições. É uma **auditoria piloto**, não uma validação.

## O que não se muda depois
Definição, lista de pontos, semente e regra de contagem. Se algo precisar mudar, registra-se aqui a mudança e o motivo, antes de abrir o gabarito.

## Mudança registrada em 13/11/2026 (antes de qualquer leitura e com o gabarito fechado)
- **O que mudou:** a leitura humana do pesquisador numa parte sorteada foi retirada.
- **Motivo:** ele não é inspetor, e a leitura dele não mede melhor do que os 35 controles de resposta conhecida, que já medem o acerto da IA.
- **O que fica:** a IA lê os 150 pontos. A leitura humana que vale é a de um inspetor da equipe, se o resultado justificar.
- Definição, pontos, semente e regra de contagem não mudaram.
