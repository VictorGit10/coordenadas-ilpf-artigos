# Leitura de fichas de uso da terra (Cerrado goiano)

Você vai ler fichas de imagem de talhões rurais em Goiás e responder a perguntas fechadas sobre cada uma. Cada ficha é um arquivo PNG nesta pasta (`F###.png`). Abra e olhe **cada imagem** antes de responder sobre ela. Não use nenhuma outra fonte: só o que está na ficha.

## O que há em cada ficha
- **A (esquerda):** imagem de satélite CBERS-4A com 2 m de resolução, cor natural realçada, norte para cima. O **contorno amarelo** é a área a avaliar. O quadrado ciano mostra onde fica o quadro B.
- **B (direita):** detalhe de 500 m × 500 m no centro da área, na resolução original.
- **C (embaixo):** série de NDVI do Sentinel-2 a cada 15 dias, de julho de 2020 a outubro de 2025, média dentro do contorno. As faixas azuis são a estação chuvosa (outubro a março).

## Como reconhecer cada coisa
- **Renques de árvores:** faixas escuras, paralelas e regulares (retas ou em curva de nível), com faixas mais claras de pasto ou lavoura entre elas. O espaçamento típico entre renques é de 10 a 50 m. Árvores espalhadas sem ordem **não** são renques. Linhas de terraço, rastros de máquina e sulcos de plantio **não** são renques: são linhas finas, sem copa nem sombra.
- **Lavoura perene em linhas (café, citros, seringueira jovem):** linhas finas e muito próximas (menos de 8 m entre elas), cobrindo o talhão inteiro como um pente, em blocos separados por carreadores, muitas vezes com terreiro ou galpão ao lado. Isso é `Agricultura`, **não** renque: no renque de integração sobra uma faixa larga e aberta (10 m ou mais) entre as fileiras de árvores.
- **Floresta plantada maciça (silvicultura):** bloco escuro contínuo, de textura uniforme, com bordas retas e sem faixas abertas entre as linhas.
- **Vegetação nativa:** mancha escura de textura irregular e bordas irregulares.
- **Lavoura anual, na série:** pico alto de NDVI (acima de ~0,75) na estação chuvosa, seguido de queda brusca para perto de 0,2 em poucas semanas (colheita). Um segundo pico agudo logo depois é segunda safra (milho ou sorgo).
- **Pastagem, na série:** sobe na chuva e desce devagar na seca, sem queda brusca; raramente passa de 0,8 e raramente cai abaixo de 0,25.
- **Lavoura seguida de pasto (integração lavoura-pecuária):** pico de lavoura com colheita brusca e, em seguida, um verde moderado que se mantém e decai devagar durante a seca (capim), em vez de solo exposto até a chuva seguinte. Pode também aparecer como anos de lavoura alternados com anos de pasto.
- **Árvores na série:** NDVI alto e estável o ano todo, com pouca variação.

## Classes possíveis
- `ILP`: lavoura e pecuária na mesma área, sem árvores (lavoura seguida de pasto, ou rotação entre anos).
- `IPF`: renques de árvores com pasto entre eles.
- `ILF`: renques de árvores com lavoura entre eles.
- `ILPF`: renques de árvores e, entre eles, sinais de lavoura e de pasto.
- `SAF`: agrofloresta, várias espécies arbóreas misturadas com culturas, em geral área pequena e heterogênea.
- `Silvicultura`: floresta plantada maciça.
- `Pastagem`: pasto sem lavoura nem renques.
- `Agricultura`: lavoura anual ou perene sem sinal de pasto nem renques.
- `Outros`: vegetação nativa, água, área urbana, solo exposto permanente etc.

## O que responder
Para cada ficha, um objeto JSON com exatamente estes campos:

```json
{
  "id": "F000",
  "qualidade_imagem": "boa | regular | ruim",
  "renques_de_arvores": "sim | nao | incerto",
  "espacamento_renques_m": 0,
  "entre_os_renques": "pasto | lavoura | solo exposto | indefinido | nao se aplica",
  "fracao_da_area_com_renques": 0.0,
  "cobertura_dominante": "texto curto",
  "serie_ciclos_de_lavoura": "nenhum | um por ano | dois ou mais por ano | so em alguns anos",
  "serie_pasto_apos_lavoura": "sim | nao | incerto | nao se aplica",
  "classe": "ILP | IPF | ILF | ILPF | SAF | Silvicultura | Pastagem | Agricultura | Outros",
  "segunda_opcao": "uma das classes, ou vazio",
  "confianca": 0.0,
  "motivo": "uma frase dizendo o que você viu na imagem e na série"
}
```

Regras:
- Avalie só o que está **dentro do contorno amarelo**. Se a área for mista, classifique o que domina e diga isso no motivo.
- `espacamento_renques_m` é a distância aproximada entre renques, medida na ficha (o quadro B tem 500 m de lado). Use 0 quando não houver renques.
- `confianca` vai de 0 a 1. Use valores baixos quando a imagem ou a série não permitirem decidir. Não chute para parecer seguro.
- Não tente adivinhar de onde veio a ficha. Todas estão misturadas de propósito.

Responda **apenas** com uma lista JSON (um objeto por ficha, na ordem pedida), sem texto antes nem depois.
