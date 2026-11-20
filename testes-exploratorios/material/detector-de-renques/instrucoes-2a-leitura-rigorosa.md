# Segunda leitura, rigorosa: há mesmo renques de árvores nesta ficha?

Cada ficha (`F....png` nesta pasta) foi apontada por uma primeira leitura como tendo **renques de árvores** (fileiras de árvores paralelas e regulares com pasto ou lavoura entre elas), dentro ou junto do contorno amarelo. Seu papel é o de **revisor cético**: procure motivos para duvidar. Abra e olhe cada imagem. Use só o que está na ficha.

A ficha tem: **A** (esquerda) imagem de satélite de 2 m com o contorno amarelo da área avaliada; **B** (direita) detalhe de 500 m × 500 m no centro; **C** (embaixo) série de NDVI do Sentinel-2.

## Notas
- **A — renque nítido:** pelo menos 4 fileiras de árvores claramente paralelas, com espaçamento regular (10 a 60 m), cada fileira contínua ou quase contínua, formando um conjunto que ocupa boa parte da área.
- **B — renque provável, com ressalva:** há fileiras paralelas, mas são poucas (2 ou 3), falhadas, muito jovens ou ocupam só um canto da área.
- **C — não é renque:** árvores esparsas que por acaso se alinham, árvores ao longo de cerca, estrada, curso d'água ou terraço, faixas de vegetação nativa irregulares, linhas de lavoura perene (café, citros), talhão de floresta plantada maciça, ou qualquer outra coisa.

## Responda para cada ficha
```json
{
  "id": "F0000",
  "nota": "A | B | C",
  "fileiras_contadas": 0,
  "espacamento_m": 0,
  "origem_das_arvores": "plantadas em linha | nativas deixadas em faixa | nao da para dizer",
  "entre_as_fileiras": "pasto | lavoura | os dois | indefinido",
  "serie_tem_lavoura": "sim | nao",
  "onde_estao_os_renques": "dentro do contorno | parte dentro e parte fora | quase tudo fora",
  "motivo_da_duvida": "o principal motivo para duvidar, ou vazio se for nota A sem ressalva"
}
```
`espacamento_m` é a distância entre fileiras vizinhas medida na ficha (o quadro B tem 500 m de lado). `serie_tem_lavoura` é "sim" se a série de NDVI mostrar ciclos de lavoura anual (pico alto e queda brusca) em algum ano.

Responda **apenas** com uma lista JSON (um objeto por ficha, na ordem pedida), sem texto antes nem depois.
