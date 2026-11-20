# Revisão do plano revisado

Li `CONTEXTO.md`, `PLANO-REVISADO.md`, `DIARIO.md`, as três opiniões, `RELATORIO-classificador.md`, `cruzar_merc.py`, `nas39_merc.py` e trechos de `repo_04.py` e `repo_05.py`. Não rodei nada nem alterei arquivos; não abri `ANALISE-CAMINHOS.md`, `RELATORIO-curvas.md` nem `LEIA-ME-artigos.md`.

## O que conferi nos arquivos

- **Correção Mercator:** `cruzar_merc.py` e `nas39_merc.py` tratam a latitude em Mercator e a longitude linear, o que está certo.
- **Limiar de cor:** `nas39_merc.py` continua sem ele (linha 26), ao contrário do `cruzar_merc.py` (`d<300`, linha 24). A crítica do Kimi segue valendo para os números das 39.
- **Áreas sem pixel:** o `nas39_merc.py` só conta pixel com arquivo baixado e alfa > 0. As 7 áreas sem pixel são, portanto, tile não baixado ou transparência no próprio mapa. A segunda hipótese contraria o "cobre a área toda" do diário.
- **`repo_05.py`:** argmax (linhas 182 e 285), máscara só para pixel sem dado, raster de confiança e três modos, sendo `pixel` o padrão (linha 49).
- **`repo_04.py`:** separação por linha (138–140) e teste usado na parada antecipada e na escolha do modelo (176–182).
- **Classificador:** recontei a tabela talhão a talhão: 8 de 13 achados e 6 falsos em 61.
- **Queda entre datas:** em quatro talhões de medição a probabilidade cai de 0,68–0,99 em 2024 para menos de 0,16 em 2026.

## 1. O plano

A ordem está certa (opinião). Vejo quatro problemas:

- **Passo 2 contra a restrição:** pelo diário, o repositório público só tem PNG. Obter o "dado original" exige pedir à equipe. A alternativa é validar o georreferenciamento do PNG com os talhões conhecidos.
- **Falta a data de referência:** a queda de probabilidade nos quatro talhões acima é compatível com corte das árvores. O Esri Wayback tem datas irregulares. A tela deveria mostrar também os recortes CBERS datados de 2024 e 2025, e a pergunta deve ser "havia renque na safra 2024/2025?".
- **Passo 4 mistura três finalidades em 100–150 pontos:** estimar o mapa, confirmar as 39 e calibrar o inspetor. Nenhuma fica com tamanho suficiente.
- **A IA quase sumiu do plano:** sobra uma inspeção manual, o que enfraquece o "exemplo de uso de IA". Proponho o remédio no item 5.

## 2. As opiniões

- **Gemini:** recomendou testar a TempCNN primeiro com as 39 não confirmadas. O plano fez bem em rejeitar.
- **DeepSeek:** calculou o intervalo sobre 6/64, e o correto é 6/61. O Kimi já havia apontado.
- **Kimi:** não achei erro.

Pontos bons que o plano ignorou:

1. **Teste da validação da equipe (DeepSeek):** comparar separação por linha com separação por talhão na planilha. É barato e não depende de inspeção, porque o elo `ID_ponto` = `IDs` já existe. Faltam os pesos e a configuração, então seria uma comparação relativa.
2. **Discordância entre fontes (os três):** usar a discordância entre mapa, classificador e MapBiomas para escolher uma segunda leva de pontos, separada da amostra sorteada.
3. **Proximidade da medição:** 8 das 39 ficam perto de talhões de medição, segundo Gemini e DeepSeek. Não conferi.
4. **SAF:** a base tem 0 polígonos de SAF e o mapa tem 60 mil ha de Agrofloresta. Vale saber de onde vem esse treino, possivelmente dos pontos de outros estados.

## 3. Inspetor único, não especialista e autor

Enfraquece bastante (opinião): o resultado vira auditoria piloto, não validação. Isso basta para o objetivo, que é convencer a equipe a refazer a inspeção com os inspetores dela. Mitigações sem envolver ninguém:

- **Cegar o estrato:** a tela não mostra a classe do mapa, o MapBiomas nem a IA. Pontos de IPF e controles ficam embaralhados na mesma fila. É a mitigação mais importante, porque o autor já espera que o mapa erre.
- **Controles com resposta conhecida:** talhões da equipe com árvores como positivos e talhões de pastagem e agricultura como negativos. Assim se mede o acerto do próprio inspetor.
- **Repetição:** 15 pontos repetidos sem aviso, para medir a consistência dele.
- **Protocolo congelado:** definição, semente e lista de pontos gravadas antes de ver qualquer imagem.
- **"Não dá para dizer" como categoria:** o número sai com os dois limites, tudo contado como sim e tudo como não. Na régua foram 24 de 50; se passar de 20% com várias datas, o número é fraco.
- **Entrega replicável:** os mesmos pontos em GeoJSON, prontos para a equipe repetir no TVI.

## 4. Amostragem

- **População:** pixels que o mapa chama de IPF nos 26 tiles (179 mil ha).
- **Sorteio:** 100 pixels com probabilidade igual. Sorteio simples de pixel já dá proporção de área; a distorção do Mercator na faixa de latitude do piloto é de poucos por cento e basta declará-la.
- **Estratos:** os cinco do MapBiomas publicado, com alocação proporcional: 42 em pastagem, 26 fora de uso agropecuário, 15 em agricultura, 14 em mosaico e 3 em floresta plantada.
- **Bordas:** não excluir, só marcar. Excluir enviesa a favor do mapa.
- **Pergunta:** "o ponto cai num talhão com árvores plantadas em fileiras na safra 2024/2025?"
- **Respostas:** renque; silvicultura densa; pasto com árvores espalhadas; vegetação nativa; sem árvores; não dá para dizer.
- **Precisão:** com 100 pontos, cerca de ±10 pontos percentuais (intervalo de Wilson).
- **Fora da estimativa, na mesma fila:** 20 controles negativos, 15 positivos e 15 repetições. São 150 julgamentos, umas 5 a 6 horas.
- **As 39:** sessão separada. Não são amostra sorteada e não entram no número.
- **ILPF e Agrofloresta:** segunda leva, com 60 e 40 pontos, se a primeira valer a pena.

## 5. Menor resultado que vale mostrar

Uma página com três coisas:

- a frase "de 100 pontos de IPF, X têm renque, Y são vegetação nativa, Z não têm árvores e W são indecidíveis", com intervalo;
- a constatação de que o `repo_05.py` não tem máscara nem rejeição;
- o GeoJSON dos pontos.

Ordem: definição escrita, conferências do passo 2 sem o dado original, tela reaproveitando a página da régua, e os 150 julgamentos. Não gasta Colab.

Depois disso, o classificador roda nos mesmos 100 pontos, por menos de 1 unidade de Colab. Se concordar com o humano, ele permite estender a auditoria a milhares de pontos, e é aí que entra o uso justificável de IA.

## 6. Bobinho ou ambicioso

Não vejo nada bobinho. O passo 5 é ambicioso demais como passo único (opinião):

- **TempCNN:** sem pesos, sem configuração e com 13 positivos na medição, a diferença "com e sem amostras" dificilmente será detectável.
- **Cabeça com grade de patches:** com 28 talhões positivos, o risco de sobreajuste é alto.

Eu trocaria esse passo pelo teste "linha contra talhão" e pelo classificador atual usado como ordenador. O resto ficaria para depois de a equipe entrar.