"""Gera uma primeira versao do RELATORIO.md a partir dos arquivos produzidos.
O RELATORIO.md final foi revisado e complementado a mao (teste do classificar.py,
matriz de confusao da medicao, notas de tempo/unidades).
"""
import json
import os
from collections import Counter

import pandas as pd

from comum import BASE, DADOS, GPKG, MODELO

CLASSES = {1: "Pastagem", 2: "Agricultura", 3: "ILPF", 4: "ILP",
           5: "IPF", 6: "SAF", 7: "ILF", 8: "Outros", 9: "Silvicultura"}


def ler_json(p, padrao=None):
    if not os.path.exists(p):
        return padrao
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def fmt_p(p):
    return "—" if pd.isna(p) else f"{p:.3f}"


def main():
    ens = pd.read_csv(os.path.join(DADOS, "recortes_ensino.csv"))
    neg = pd.read_csv(os.path.join(DADOS, "recortes_negativos.csv"))
    med = pd.read_csv(os.path.join(DADOS, "recortes_medicao.csv"))
    cfg = ler_json(os.path.join(MODELO, "config.json"), {})
    cv = ler_json(os.path.join(MODELO, "cv_resultados.json"), {})
    av = ler_json(os.path.join(BASE, "resultado", "medicao_avaliacao.json"), {})
    tab = pd.read_csv(os.path.join(BASE, "resultado", "medicao_tabela.csv"))
    colab = ler_json(os.path.join(BASE, "colab_resumo.json"), {})

    n_ens, n_neg, n_med = len(ens), len(neg), len(med)
    n_treino = n_ens + n_neg
    pos_img = int(ens.rotulo.sum())
    neg_img = n_ens - pos_img + n_neg
    n_pos_tal = ens[ens.rotulo == 1].talhao.nunique()
    n_neg_tal = ens[ens.rotulo == 0].talhao.nunique()
    tipos = Counter(ens.tipo)
    anos = Counter(ens.ano.astype(str))
    datas_tal = ens.groupby("talhao").data.nunique().value_counts().to_dict()

    L = []
    L.append("# Classificador de renques: relatório")
    L.append("")
    L.append("Data: 12/11/2026. Pasta de trabalho: `classificador/`.")
    L.append("")
    L.append("## Resumo")
    L.append("")
    L.append(
        f"Treinei um classificador de recortes de 400 m do CBERS-4A (2 m) para dizer "
        f"se o recorte tem árvores/renques. O treino usou **{n_treino} recortes** "
        f"({n_ens} do grupo `ensino` e {n_neg} negativos difíceis), com "
        f"**{n_pos_tal} talhões positivos** e **{n_neg_tal} negativos** no ensino. "
        f"O modelo é uma **cabeça logística** sobre features congeladas de "
        f"**{cfg.get('base_model', '?')}** (entrada {cfg.get('input_size', '?')} px, "
        f"8 visões dihedral). A validação cruzada foi 5-fold agrupada por bloco; "
        f"o limiar foi escolhido no ensino. Só depois disso o grupo `medicao` foi "
        f"baixado e medido, uma única vez.")
    L.append("")
    if av:
        L.append(
            f"Na medição, dos **8 talhões com árvore dentro dos tiles**, o "
            f"classificador achou **{av['arvore_nos_tiles']['positivos']} de "
            f"{av['arvore_nos_tiles']['n']}** (o detector antigo achava "
            f"{av.get('detector_marcou_8', 0)}). Dos **{av['arvore_todos']['n']} "
            f"talhões de medição com árvore**, achou "
            f"**{av['arvore_todos']['positivos']}**. Dos "
            f"**{av['sem_arvore']['n']} sem árvore**, marcou "
            f"**{av['sem_arvore']['positivos']}** como positivo.")
    L.append("")

    L.append("## 1. Dados e recortes")
    L.append("")
    L.append("O caderno tem 241 talhões (EPSG:4326): 164 de ensino (28 com árvore, "
             "136 sem) e 77 de medição (13 com árvore, 64 sem). O rótulo positivo "
             "é a coluna `arvore` (códigos 3, 5, 6, 7 e os poucos casos marcados "
             "como árvore no caderno).")
    L.append("")
    L.append(f"Para cada talhão de ensino fiz recortes de 400 m de lado "
             f"(`meio_m=200`, 200×200 px a 2 m), centrados no ponto representativo, "
             f"em até 3 datas da estação seca (maio–setembro) de anos diferentes. "
             f"Total do ensino: **{n_ens} recortes** — {tipos.get('centro', 0)} "
             f"centrais e {tipos.get('deslocado', 0)} deslocados dentro de 27 "
             f"talhões grandes (≥100 ha). Todos os 28 talhões positivos têm 3 datas.")
    L.append("")
    L.append(f"Datas por ano no ensino: {dict(sorted(anos.items()))}. "
             f"Datas por talhão: {dict(sorted(datas_tal.items()))}.")
    L.append("")
    L.append(f"Negativos difíceis: **{n_neg} recortes** de 102 pontos rejeitados "
             f"nas leituras de fichas por área urbana/construção (61) ou terraço/"
             f"curva de nível (41), 2 datas cada. Descartei leituras cujo cadastro "
             f"ou motivo indicava sistema com árvore (ILPF, ILF, IPF, SAF, "
             f"silvicultura, lavoura perene etc.) para não ensinar o modelo a "
             f"rejeitar plantio. Todos os 102 pontos ficaram a **≥5 km de qualquer "
             f"talhão de medição** (menor distância: 6,5 km).")
    L.append("")
    L.append(f"Total para treino: **{n_treino} recortes** "
             f"({pos_img} positivos e {neg_img} negativos).")
    L.append("")
    L.append(f"Para a medição: **{n_med} recortes** de {med.talhao.nunique()} "
             f"talhões com cena (dos 77 do caderno; 3 não tinham cena CBERS), mesmo "
             f"protocolo, mas só recortes centrais.")
    L.append("")

    L.append("## 2. Como a medição ficou de fora")
    L.append("")
    L.append("A ordem foi rígida: primeiro baixei e montei o ensino; depois treinei, "
             "comparei modelos, escolhi o limiar e salvei `modelo/`; só então baixei "
             "os recortes de medição, subi para o Colab e rodei `medir_colab.py`. "
             "O CSV de medição enviado ao Colab não tem `arvore` nem `nos_tiles`, e a "
             "coluna `rotulo` vai vazia; a junção com o gabarito foi feita depois, "
             "no PC, por `avaliar_medicao.py`.")
    L.append("")
    L.append("Não mudei nada depois de ver o resultado da medição. Se eu tivesse "
             "mudado, este resultado não valeria; não foi o caso.")
    L.append("")

    L.append("## 3. Modelo")
    L.append("")
    L.append(f"- Base: **{cfg.get('base_model', '?')}** (pesos públicos do DINOv2/"
             f"LVD-142M via `timm`), congelada.")
    L.append(f"- Entrada: {cfg.get('input_size', '?')}×{cfg.get('input_size', '?')} px "
             f"(recorte de 400 m reamostrado).")
    L.append(f"- Features: CLS + média dos tokens de patch (ViT) ou média global "
             f"(CNN), com as 8 transformações dihedral (4 rotações × espelhamento).")
    L.append(f"- Cabeça: regressão logística L2, `class_weight='balanced'`, "
             f"C={cfg.get('C', '?')}.")
    L.append(f"- Treino: {cfg.get('n_imagens', '?')} recortes, "
             f"{cfg.get('n_positivas', '?')} positivos.")
    L.append(f"- Decisão do talhão: maioria das datas disponíveis; empate = positivo.")
    L.append(f"- Limiar de probabilidade: **{cfg.get('limiar', '?')}**.")
    L.append("")
    L.append("Também testei, na validação cruzada, ConvNeXt-Tiny e DINOv2 em 224 px. "
             "A escolha do modelo foi feita pela AUC no nível do talhão (média das "
             "datas de centro), que é a métrica que interessa; a AUC por imagem "
             "ficou como secundária.")
    L.append("")

    L.append("## 4. Validação cruzada no ensino")
    L.append("")
    L.append("5 folds, `StratifiedGroupKFold(shuffle=True, random_state=42)`, "
             "agrupando por `bloco` (todos os recortes do mesmo bloco ficam no mesmo "
             "fold) e cada negativo difícil como grupo próprio. As features de treino "
             "incluem as 8 visões; na validação a probabilidade é a média das 8.")
    L.append("")
    L.append("| configuração | entrada | C | AUC imagem | AUC talhão | balanceada@0,5 | sens@0,5 | spec@0,5 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for tag, r in (cv.get("configs") or {}).items():
        if "erro" in r:
            L.append(f"| {tag} | — | — | — | — | — | — | — |")
            continue
        L.append(f"| {tag} | {r.get('size')} | {r.get('C')} | "
                 f"{r.get('auc_oof', float('nan')):.3f} | "
                 f"{r.get('auc_talhao', float('nan')):.3f} | "
                 f"{r.get('bal_05', float('nan')):.3f} | "
                 f"{r.get('sens_05', float('nan')):.2f} | "
                 f"{r.get('spec_05', float('nan')):.2f} |")
    L.append("")
    o = cfg.get("oof_talhao") or {}
    if o:
        L.append(f"Com o modelo escolhido e o limiar **{cfg.get('limiar')}**, a matriz "
                 f"de confusão no nível do talhão (OOF) ficou: "
                 f"TP={o.get('tp')}, FN={o.get('fn')}, TN={o.get('tn')}, FP={o.get('fp')}; "
                 f"sensibilidade {o.get('sens', 0):.3f}, especificidade "
                 f"{o.get('spec', 0):.3f}, acurácia balanceada {o.get('bal', 0):.3f}.")
    L.append("")
    L.append("A curva completa do limiar está em `modelo/cv_resultados.json`. "
             "O limiar foi o que maximizou a acurácia balanceada no talhão; "
             "empates foram resolvidos pela maior sensibilidade.")
    L.append("")

    L.append("## 5. Medição (uma vez, no fim)")
    L.append("")
    if av:
        L.append("### 5.1 Os 8 talhões com árvore dentro dos tiles")
        L.append("")
        L.append(f"O classificador marcou **{av['arvore_nos_tiles']['positivos']} de "
                 f"{av['arvore_nos_tiles']['n']}**. O detector antigo "
                 f"(`detector_marcou`) marcava {av.get('detector_marcou_8', 0)}.")
        L.append("")
        det = tab[(tab.arvore) & (tab.nos_tiles) & (tab.decisao == 1)].talhao.tolist()
        miss = tab[(tab.arvore) & (tab.nos_tiles) & (tab.decisao == 0)].talhao.tolist()
        L.append("Detectados: " + ", ".join(str(int(t)) for t in det) + ". "
                 "Não detectado: " + (", ".join(str(int(t)) for t in miss) or "nenhum") + ".")
        L.append("")
        L.append("### 5.2 Todos os talhões de medição com árvore")
        L.append("")
        L.append(f"O classificador marcou **{av['arvore_todos']['positivos']} de "
                 f"{av['arvore_todos']['n']}**.")
        miss = tab[(tab.arvore) & (tab.decisao == 0)].talhao.tolist()
        L.append("")
        L.append("Ficaram de fora: " + ", ".join(str(int(t)) for t in miss) + ".")
        L.append("")
        L.append("### 5.3 Falsos positivos nos talhões sem árvore")
        L.append("")
        L.append(f"Marcou **{av['sem_arvore']['positivos']} de {av['sem_arvore']['n']}** "
                 f"talhões sem árvore como positivo (3 dos 64 não tinham cena e "
                 f"ficaram 'sem dado'; nos 61 com cena, {av['sem_arvore']['positivos']} "
                 f"falsos). Por classe:")
        L.append("")
        L.append("| classe | talhões | marcados positivo |")
        L.append("|---|---|---|")
        for k, v in (av.get("sem_arvore_por_classe") or {}).items():
            L.append(f"| {k} | {v['n']} | {v['falsos']} |")
        L.append("")
        if av.get("sem_dados"):
            L.append(f"Sem nenhuma data válida: {av['sem_dados']}.")
            L.append("")

    L.append("### 5.4 Talhão a talhão")
    L.append("")
    L.append("`rotulo` = 1 se o talhão tem árvore no caderno; `nos_tiles` = está nos "
             "tiles; `decisão` = 1 positivo, 0 negativo, -1 sem dado. As "
             "probabilidades são por data, na ordem em que aparecem.")
    L.append("")
    L.append("| talhão | cod | classe | nos_tiles | rótulo | datas e probabilidades | decisão |")
    L.append("|---|---|---|---|---|---|---|")
    for _, r in tab.sort_values("talhao").iterrows():
        datas = str(r.get("datas", "")).split("|") if pd.notna(r.get("datas")) else []
        probs = str(r.get("probs", "")).split("|") if pd.notna(r.get("probs")) else []
        pares = "; ".join(f"{d}: {p}" for d, p in zip(datas, probs)) or "—"
        dec = {1: "positivo", 0: "negativo", -1: "sem dado"}.get(int(r.decisao), "?")
        L.append(f"| {int(r.talhao)} | {int(r.cod)} | {r.classe} | "
                 f"{int(bool(r.nos_tiles))} | {int(bool(r.arvore))} | {pares} | {dec} |")
    L.append("")

    L.append("## 6. Comparação com o detector antigo")
    L.append("")
    if av:
        L.append(f"O detector de textura antigo marcava {av.get('detector_marcou_8', 0)} "
                 f"dos 8 talhões com árvore nos tiles e "
                 f"{av.get('detector_marcou_todos', 0)} dos "
                 f"{av['arvore_todos']['n']} com árvore. O classificador marcou "
                 f"{av['arvore_nos_tiles']['positivos']} e "
                 f"{av['arvore_todos']['positivos']}, respectivamente.")
    L.append("")

    L.append("## 7. Colab: tempo e unidades")
    L.append("")
    if colab:
        L.append(f"- Sessão: `{colab.get('sessao', 'renque1')}`.")
        L.append(f"- GPU: {colab.get('gpu', 'T4')}.")
        L.append(f"- Início: {colab.get('inicio', '?')} (UTC).")
        L.append(f"- Fim: {colab.get('fim', '?')} (UTC).")
        L.append(f"- Tempo ligada: **{colab.get('duracao_min', '?')} minutos**.")
        L.append(f"- Taxa mostrada pelo CLI: {colab.get('taxa', '?')} unidades/hora.")
        L.append(f"- Saldo antes: {colab.get('saldo_antes', '?')} unidades; "
                 f"depois: {colab.get('saldo_depois', '?')}.")
        L.append(f"- Unidades gastas: **{colab.get('unidades', '?')}** "
                 f"(diferença de saldo; o CLI também mostrou a taxa).")
        L.append(f"- A VM foi encerrada com `colab stop`; `colab sessions` ficou vazio.")
    else:
        L.append("(preencher com os dados do `colab_log.txt`)")
    L.append("")

    L.append("## 8. Como usar")
    L.append("")
    L.append("```")
    L.append("python classificar.py --entrada pontos.csv --saida saida.csv")
    L.append("python classificar.py --entrada pontos.csv --datas 3 --saida saida.csv")
    L.append("```")
    L.append("")
    L.append("`pontos.csv` precisa de `lon` e `lat` (e opcionalmente `id`). "
             "O script baixa um recorte de 400 m por ponto, extrai as features e "
             "devolve `prob` (média das 8 visões) e `decisao`. Com `--datas 3` ele "
             "usa até 3 anos e decide pela maioria (empate = positivo), que é o "
             "protocolo da medição; com o padrão (`--datas 1`) usa a cena mais "
             "recente, que é mais rápido para varrer tiles. Precisa de `torch` e "
             "`timm`; roda no Colab ou em máquina com GPU/CPU.")
    L.append("")
    L.append("## 9. Arquivos gerados")
    L.append("")
    L.append("- `modelo/config.json`: modelo base, tamanho de entrada, C, limiar e regra.")
    L.append("- `modelo/cabeca.npz`: pesos da cabeça logística (coef, intercept, "
             "média e escala das features).")
    L.append("- `modelo/cv_resultados.json`: resultados dos modelos e curva do limiar.")
    L.append("- `modelo/ensino_oof.csv` e `modelo/ensino_talhoes_oof.csv`: previsões "
             "out-of-fold do ensino.")
    L.append("- `classificar.py`: recebe uma lista de (lon, lat) e devolve a "
             "probabilidade; usa `modelo/` e o mesmo protocolo de recorte.")
    L.append("- `dados/recortes_*.csv`: índice dos recortes (talhão, grupo, rótulo, "
             "data, arquivo).")
    L.append("- `resultado/medicao_tabela.csv` e `resultado/medicao_probabilidades.csv`: "
             "resultado da medição.")
    L.append("")

    L.append("## 10. Problemas e limitações")
    L.append("")
    L.append("- **Poucos positivos**: 28 talhões com árvore no ensino e 13 na medição. "
             "A validação cruzada tem ruído; um único talhão muda a sensibilidade "
             "em vários pontos percentuais.")
    L.append("- **Rótulo é do talhão, não do recorte**: um recorte de 400 m pode "
             "pegar estrada, mata ciliar ou vizinho. Em talhões pequenos, boa parte "
             "do recorte é de fora. Isso mete ruído nos dois lados.")
    L.append("- **Rótulo `arvore` não é exatamente 'renque'**: há talhões de pasto "
             "com árvores espalhadas marcados como positivos, e plantios densos "
             "marcados como positivos. O modelo aprende o rótulo do caderno, não "
             "uma definição botânica de renque.")
    L.append("- **Cobertura do CBERS**: em 2026 faltou cena em várias regiões; "
             "2023 e 2024 cobriram a maior parte. Por isso 1 talhão ficou com 2 "
             "datas e os demais com 3. Em medição, talhões sem cena ficam 'sem dado'.")
    L.append("- **Nuvem e borda de cena**: o QA rejeita recortes com muito preto/"
             "branco, mas nuvem fina e sombra podem passar; o realce por percentis "
             "muda o tom de cada data.")
    L.append("- **Negativos difíceis**: os pontos vieram de leituras de fichas, não "
             "de uma varredura exaustiva. Cidade, galpão e terraço estão "
             "representados, mas não todas as variantes. Também há fragmento de "
             "mata nativa em alguns recortes, o que é útil (não é renque) mas "
             "dificulta a separação.")
    L.append("- **5 positivos ficaram de fora na medição**: 128 (Silvicultura), "
             "151, 153 e 213 (IPF) e 240 (ILF). Em 151 e 213 só uma das três datas "
             "passou do limiar; a regra de maioria derrubou o talhão.")
    L.append("- **Limiar baixo (0,09)**: as probabilidades não estão calibradas; "
             "o valor serve para a regra de maioria, não como confiança absoluta. "
             "Muitos negativos ficam entre 0,01 e 0,09.")
    L.append("- **3 talhões de medição sem cena** (2, 228, 229, todos sem árvore): "
             "ficaram 'sem dado' e não entram como acerto nem erro.")
    L.append("- **Limiar escolhido no OOF**: a acurácia balanceada do ensino é "
             "otimista, porque o mesmo OOF foi usado para escolher modelo e limiar. "
             "A medição é a única estimativa não enviesada, e ela tem só 13 positivos.")
    L.append("- **Sem mudança pós-medição**: nenhum parâmetro foi alterado depois "
             "de ver os números da medição. Se alguém quiser mexer no limiar olhando "
             "a medição, o número deixa de valer.")
    L.append("")

    with open(os.path.join(BASE, "RELATORIO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("RELATORIO.md salvo", len(L), "linhas")


if __name__ == "__main__":
    main()
