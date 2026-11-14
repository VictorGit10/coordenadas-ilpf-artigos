# Coordenadas de sistemas integrados tiradas de artigos

Site estático com coordenadas de áreas de ILP, ILPF, IPF, ILF e SAF, e das áreas de comparação dos mesmos estudos (pastagem, lavoura, floresta plantada, vegetação nativa). Elas foram tiradas de artigos, teses e publicações técnicas brasileiras de acesso aberto.

Cada ponto traz:
- o trecho original com a coordenada e a página;
- a que a coordenada se refere;
- a margem da escrita (o círculo no mapa);
- as classes, os anos de implantação e de avaliação, a fazenda e o município;
- os links do documento e da imagem de satélite.

O botão "Baixar CSV" exporta o que estiver filtrado.

## Níveis
- **A:** coordenada da área experimental ou da parcela, com precisão de segundos ou melhor, classe e ano no texto.
- **B:** precisão boa, mas a coordenada é da fazenda, da sede ou da estação, ou falta o ano.
- Ficam fora as coordenadas só em minutos (~1,8 km), as que não conferem com o texto e as que caem na cidade. Cai na cidade o ponto a menos de 1 km da sede municipal ou com 25% ou mais de área construída num raio de 100 m (ESA WorldCover 2021).

## Conferência na imagem
O nível A ou B diz o que o texto afirma da coordenada, não se o sistema existe no lugar. Por isso cada ponto tem um segundo selo, da conferência na imagem de satélite atual (Google, 700 m de lado): **confirmado** (o sistema aparece), **compatível, sem confirmação** (o uso do solo é plausível, mas o sistema não se distingue), **não confere** (a imagem não mostra o sistema descrito) ou **sem conferência**. O site tem filtro por esse status.

Em 14/11/2026 foram conferidos 118 pontos: 17 confirmados, 78 compatíveis e 22 não conferem. Os outros 112 ainda não foram conferidos. A conferência olha 700 m em volta do ponto e não substitui a inspeção do talhão.

## Como foi feito
A IA (DeepSeek v4.1 Flash) leu os textos e copiou o trecho literal. Um programa conferiu se o trecho existe, calculou a precisão, checou se o número bate e se é possível, e mediu a distância à sede municipal e a área construída.
