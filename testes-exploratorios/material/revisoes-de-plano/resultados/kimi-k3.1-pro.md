# Parecer do Kimi K3.1 Pro

Li todos os arquivos da pasta, sem executar código. **“Fato” abaixo significa que conferi o relato ou o código fornecido; não reexecutei as análises nem examinei os dados brutos.** Assim, os números de `DIARIO.md` e dos relatórios são resultados documentados, não verificações independentes.

## 1. O raciocínio se sustenta parcialmente

A separação entre **encontrar renques**, **confirmar sua presença** e **atribuir a classe do sistema** é correta e importante. Também é fato que `repo_04.py` separa treino/teste por linha e usa o teste em `validation_data` para parada antecipada e seleção do melhor modelo. Como há safras repetidas do mesmo talhão, a separação pode produzir vazamento espacial/temporal; o teste certamente não é intocado. Isso contrasta com a “avaliação cega independente” descrita em `methodology.html`.

Há, porém, conclusões excessivas:

- **“0 falsos em 40” não demonstra que a IA é confiável para confirmar em geral.** Zero erros nessa amostra ainda permite uma taxa real de alguns por cento, além de haver seleção de casos e calibração prévia das instruções nas mesmas 58 fichas (`DIARIO.md`). A régua, com 24/50 “não dá para dizer”, mostra que a evidência visual frequentemente é insuficiente.
- O classificador não mede exatamente “renque”: o próprio `RELATORIO-classificador.md` informa que o rótulo inclui árvores espalhadas, plantios densos e Silvicultura. Portanto, **7/8 é detecção do rótulo “árvore”, não da classe IPF nem necessariamente de renques**. Com oito positivos, o intervalo de incerteza é enorme. Os seis falsos devem ser calculados sobre os 61 negativos com imagem, não 64.
- A validação cruzada agrupada é adequada, mas modelo e limiar foram escolhidos no mesmo OOF; o relatório reconhece o otimismo. Os negativos difíceis, originados das leituras de IA, também não representam toda a paisagem.
- A estimativa de “1 a 5 verdadeiros por 100 regiões” em `ANALISE-CAMINHOS.md` é especulativa: transpõe falsos por talhão centrado para recortes arbitrários e usa as 39 áreas ainda não confirmadas como estimativa de prevalência.
- Reproduzir EVI2 quase exatamente em 21 registros (`RELATORIO-curvas.md`) é forte validação **do processamento**, não das classes das 39 amostras.

A maior contradição é recomendar testar a TempCNN com as 39 **antes** da inspeção, usando classes admitidamente palpitadas pela IA. Eventual melhora não provaria boa amostragem; poderia apenas reforçar rótulos errados. Além disso, faltam pesos e `settings.yaml`, logo não é possível garantir “os mesmos parâmetros da equipe”.

## 2. A leitura do mapa é um sinal de auditoria, não evidência de erro

Os cruzamentos são preliminares e não sustentam “um terço do IPF está errado”. `cruzar.py` interpreta transparência do MapBiomas como ausência de uso agropecuário sem legenda conferida; transparência pode representar outra classe, ausência de dados ou recorte da visualização. `nas39.py` atribui sempre a cor mais próxima, sem o limiar de distância usado em `cruzar.py`, e somente 30/39 polígonos têm pixels.

Explicações alternativas incluem resolução e omissões do MapBiomas, diferenças de data, fragmentos nativos dentro de sistemas integrados, desalinhamento, contornos parciais e mistura dentro do polígono. **Pastagem majoritária não exclui renques estreitos.** Por outro lado, `repo_05.py` força cada pixel válido a uma das nove classes por `argmax`, sem rejeição por baixa confiança; num mapa sem vegetação nativa explícita, isso pode gerar comissão sistemática.

Antes de afirmar algo: conferir rasters originais, legendas, CRS, alinhamento, bordas, paleta e significado do alfa. Depois, sortear pontos proporcionais à área dentro de cada classe e obter interpretação humana independente. O classificador pode ser comparado, **não usado como gabarito**. “Tem árvores plantadas” também não equivale a “a classe IPF está correta”.

## 3. Eu mudaria a ordem

1. Fixar definições operacionais e construir a referência humana cega, multidata, incluindo aprovados, rejeitados, incertos e controles de mata nativa, silvicultura, pomar, urbano e pastagem.
2. Fazer a checagem técnica barata do mapa e uma auditoria piloto com amostragem probabilística, pesos de área e intervalos de confiança.
3. Confirmar as 39 e fechar apenas as 5–7 regiões já encontradas pelos artigos. O texto histórico não comprova a classe em 2024/2025.
4. Só então ampliar o classificador e ensaiar 2–3 tiles.

Cortaria novas disputas entre LLMs, busca de ILP por EVI2, ampliação ampla de artigos/SIGEF e varredura completa por enquanto. O teste TempCNN viria depois da confirmação, com protocolo pré-fixado, separação espacial por talhão, validação própria para parada e sementes pareadas.

## 4. Inovação preferível: aprendizado ativo, não uma rede maior

Usaria **discordância entre mapa TempCNN, DINOv2 e MapBiomas para priorizar inspeção humana**, mantendo também uma amostra aleatória. No classificador, múltiplos recortes/datas por talhão poderiam ser tratados por aprendizado de múltiplas instâncias, adequado ao rótulo de talhão. Um piloto com features congeladas custaria provavelmente poucas unidades de Colab — o treino atual gastou 0,57 —, mais trabalho humano. O risco é viés de seleção, controlado pela amostra aleatória e pelo teste bloqueado. Fine-tuning profundo com apenas 28 talhões positivos teria custo maior e alto risco de sobreajuste.

## 5. Quando uma amostra assistida por IA é defensável

Quando tiver classe e safra definidas, geometria e data conferíveis, proveniência completa e confirmação humana cega; idealmente dois intérpretes, adjudicação e categoria “incerto”. Treino e validação devem ser separados antes, por talhão e bloco espacial, sem reutilizar o teste para prompts, limiar ou modelo. Artigos fornecem pista e evidência documental, não confirmação automática atual. Para validação de mapa, é indispensável amostragem probabilística independente dos candidatos da IA.

## 6. Resultado mais convincente

Um pacote pequeno e auditável: **amostras efetivamente confirmadas, campanha TVI cega, desempenho do detector com incerteza e auditoria piloto do mapa**. O experimento TempCNN seria um complemento, não a peça central. Mesmo um resultado negativo seria valioso se rigoroso; menos convincente seria apresentar 39 “novas amostras de IPF/ILF” ou acusar erro do mapa antes dessa confirmação.
