# -*- coding: utf-8 -*-
"""
Roda os casos A, B, C (e D, se pedido) do pedido em PEDIDO.md.

A = 60/40 por linha; ajuste fino com 25% de teste por linha, estratificado;
    parada antecipada olhando o proprio teste.
B = igual a A, mas a parada antecipada olha 20% de validacao tirada do treino;
    o teste so e usado no fim.
C = todas as divisoes (60/40, validacao e teste) por grupo_id.
D = como C, mas por bloco.

Uso:
    python rodar.py --casos A B C --sementes 42 43 ... 51
    python rodar.py --conferir          # so confere as divisoes, sem TensorFlow
    python rodar.py --resumo            # le resultados.csv e imprime o resumo

O CSV e escrito em modo append, uma linha por (caso, semente); rodadas ja
presentes sao puladas (use --forcar para refazer).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Constantes reconstruidas da receita publica (ver RELATORIO.md)
# ---------------------------------------------------------------------------
CLASSES = list(range(1, 10))
NOMES = {
    1: "Pastagem", 2: "Agricultura", 3: "ILPF", 4: "ILP", 5: "IPF",
    6: "Agrofloresta", 7: "ILF", 8: "Outros", 9: "Silvicultura",
}
COLUNAS_EVI = [f"EVI2_{i:02d}" for i in range(1, 14)]

# repo_03 / repo_04
SSL_NUM_HEADS = 3
SSL_FILTERS = 16
SSL_KERNEL_SIZES = (3, 5, 7)
SSL_N_BLOCOS = 2
SSL_DROPOUT = 0.2
SSL_L2 = 1e-6
SSL_LR = 1e-3
SSL_PACIENCIA = 8
# valores de settings.yaml que NAO sao publicos (suposicoes, ver relatorio)
SSL_EPOCHS = 100
SSL_BATCH = 16
SSL_VALIDATION_SPLIT = 0.2

FT_LR = 1e-4
FT_EPOCHS = 100
FT_BATCH = 16
FT_PACIENCIA = 20
AUG_MULTIPLIER = 3
FT_TEST_SIZE = 0.25
VAL_FRACAO_DO_TREINO = 0.20
FRACAO_PRETREINO = 0.60

SEMENTES_PADRAO = list(range(42, 52))

BASE_PADRAO = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def carregar_dados(base: Path):
    amostras = pd.read_csv(base / "samples_iCLS.csv")
    grupos = pd.read_csv(base / "grupos.csv")
    m = amostras.merge(
        grupos[["ID_ponto", "tipo_amostra", "grupo_id", "bloco"]],
        on=["ID_ponto", "tipo_amostra"],
        how="inner",
        validate="one_to_one",
    ).reset_index(drop=True)
    if len(m) != 1607:
        raise RuntimeError(f"esperava 1607 linhas apos o merge, veio {len(m)}")
    if len(m[m["tipo_amostra"] == "poligonal"]) != 759:
        raise RuntimeError("esperava 759 poligonais")
    if len(m[m["tipo_amostra"] == "pontual"]) != 848:
        raise RuntimeError("esperava 848 pontuais")
    X = m[COLUNAS_EVI].interpolate(
        method="linear", limit_direction="both", axis=1
    ).to_numpy(dtype="float32")
    if np.isnan(X).any():
        raise RuntimeError("ainda ha NaN nos EVI2 depois da interpolacao")
    y = m["tipo_integ"].to_numpy(dtype="int64")
    if not set(np.unique(y)) <= set(CLASSES):
        raise RuntimeError(f"classes inesperadas: {np.unique(y)}")
    return X, y, m


def _tts(idx, y, test_size, seed, nome, avisos):
    """train_test_split estratificado, com queda para nao estratificado se
    alguma classe tiver menos de 2 exemplos no subconjunto."""
    try:
        return train_test_split(
            idx, test_size=test_size, random_state=seed, stratify=y[idx]
        )
    except ValueError as exc:
        avisos.append(f"{nome}: estratificacao impossivel ({exc}); usei sorteio simples")
        return train_test_split(idx, test_size=test_size, random_state=seed)


def _particionar_por_chave(chaves, meta, alvo_fracao, rng, tamanhos):
    """Sorteia chaves (grupos/blocos) ate somar a fracao alvo de linhas.
    Devolve (escolhidas, restantes). O ultimo grupo pode passar do alvo."""
    unicas = np.asarray(sorted(set(chaves)))
    ordem = rng.permutation(len(unicas))
    total = len(meta)
    alvo = alvo_fracao * total
    escolhidas, resto, soma = [], [], 0
    for pos in ordem:
        chave = unicas[pos]
        if soma < alvo:
            escolhidas.append(chave)
            soma += tamanhos[chave]
        else:
            resto.append(chave)
    if not escolhidas or not resto:  # seguranca
        corte = max(1, int(round(alvo_fracao * len(unicas))))
        escolhidas, resto = list(unicas[ordem[:corte]]), list(unicas[ordem[corte:]])
    return escolhidas, resto


def dividir(caso, y, meta, seed):
    """Devolve dict com arrays de indices posicionais e metadados da divisao."""
    avisos = []
    n = len(y)
    idx = np.arange(n)
    out = {"caso": caso, "semente": seed, "avisos": avisos}

    if caso in ("A", "B"):
        pre, fine = _tts(idx, y, 1 - FRACAO_PRETREINO, seed, "60/40", avisos)
        tr, te = _tts(fine, y, FT_TEST_SIZE, seed, "teste 25%", avisos)
        if caso == "B":
            tr, val = _tts(tr, y, VAL_FRACAO_DO_TREINO, seed, "validacao 20% do treino", avisos)
            out["validacao_e_o_teste"] = False
        else:
            val = np.array([], dtype=int)
            out["validacao_e_o_teste"] = True
        out.update(pre=pre, treino=tr, val=val, teste=te)

    else:  # C: grupo_id ; D: bloco
        chave = "grupo_id" if caso == "C" else "bloco"
        chaves = meta[chave].to_numpy()
        tamanhos = pd.Series(chaves).value_counts().to_dict()
        rng = np.random.RandomState(seed)
        pre_ch, fine_ch = _particionar_por_chave(chaves, meta, FRACAO_PRETREINO, rng, tamanhos)
        mascara = lambda lista: np.flatnonzero(np.isin(chaves, lista))  # noqa: E731
        pre = mascara(pre_ch)
        fine = mascara(fine_ch)
        rng = np.random.RandomState(seed + 1)
        te_ch, tr_ch = _particionar_por_chave(chaves[fine], meta.iloc[fine], FT_TEST_SIZE, rng, tamanhos)
        te = mascara(te_ch)
        tr_todo = mascara(tr_ch)
        rng = np.random.RandomState(seed + 2)
        val_ch, tr_ch = _particionar_por_chave(chaves[tr_todo], meta.iloc[tr_todo], VAL_FRACAO_DO_TREINO, rng, tamanhos)
        val = mascara(val_ch)
        tr = mascara(tr_ch)
        out.update(pre=pre, treino=tr, val=val, teste=te, chave_divisao=chave)
    out["validacao_e_o_teste"] = out.get("validacao_e_o_teste", False)
    return out


# ---------------------------------------------------------------------------
# Rede (import tardio: permite conferir as divisoes sem TensorFlow)
# ---------------------------------------------------------------------------
def _bloco_tempcnn(x, filtros, kernel, dropout, l2, nome):
    from tensorflow.keras import layers, regularizers

    x = layers.Conv1D(filtros, kernel_size=kernel, padding="same",
                      kernel_regularizer=regularizers.l2(l2), name=nome)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    if dropout > 0:
        x = layers.Dropout(dropout)(x)
    return x


def build_autoencoder_1d(input_shape, num_heads, filters, kernel_sizes, n_blocos,
                         dropout, l2):
    """Copia fiel de repo_03.build_autoencoder_1d."""
    from tensorflow.keras import layers, Model

    if len(kernel_sizes) != num_heads:
        raise ValueError("num_heads != len(kernel_sizes)")
    inputs = layers.Input(shape=input_shape, name="EVI_Input")
    cabecas = []
    for i, k in enumerate(kernel_sizes, start=1):
        h = inputs
        for j in range(1, n_blocos + 1):
            h = _bloco_tempcnn(h, filters, k, dropout, l2, nome=f"cabeca{i}_conv{j}")
        cabecas.append(h)
    latente = cabecas[0] if len(cabecas) == 1 else layers.Concatenate(name="Espaco_Latente")(cabecas)
    dec = layers.Conv1D(filters, kernel_size=3, padding="same", activation="relu")(latente)
    dec = layers.BatchNormalization()(dec)
    saida = layers.Conv1D(1, kernel_size=3, padding="same", activation="linear",
                          name="Reconstrucao_EVI")(dec)
    autoencoder = Model(inputs=inputs, outputs=saida, name="Autoencoder_SSL")
    encoder = Model(inputs=inputs, outputs=latente, name="Encoder_TempCNN")
    return autoencoder, encoder


def build_ssl_classifier(encoder_model, input_shape, num_classes):
    """Copia fiel de repo_04.build_ssl_classifier (freeze_encoder=False)."""
    from tensorflow.keras import layers, Model

    encoder_model.trainable = True
    inputs = layers.Input(shape=input_shape, name="Classifier_Input")
    features = encoder_model(inputs)
    x = layers.Flatten(name="Flatten_Features")(features)
    x = layers.Dense(32, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="Output_TipoInteg")(x)
    return Model(inputs=inputs, outputs=outputs, name="TempCNN_TipoInteg_FineTuned")


def augment_evi_series(X, y, multiplier):
    """Copia fiel de repo_04.augment_evi_series."""
    X_aug, y_aug = list(X), list(y)
    for _ in range(multiplier):
        for series, rotulo in zip(X, y):
            ruido = np.random.normal(0, 0.015, series.shape)
            X_aug.append(np.clip(series + ruido, -1.0, 1.0))
            y_aug.append(rotulo)
            mascarada = series.copy()
            pos = np.random.randint(0, len(series))
            mascarada[pos] = np.mean(series)
            X_aug.append(mascarada)
            y_aug.append(rotulo)
    return np.array(X_aug), np.array(y_aug)


def treinar_e_avaliar(X, y, div, seed, epochs_ssl=SSL_EPOCHS, epochs_ft=FT_EPOCHS,
                      verboso=0):
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.utils.class_weight import compute_class_weight

    tf.get_logger().setLevel("ERROR")
    np.random.seed(seed)
    tf.random.set_seed(seed)
    try:
        tf.keras.utils.set_random_seed(seed)
    except AttributeError:
        pass
    tf.keras.backend.clear_session()

    # O LabelEncoder da receita transforma tipo_integ 1..9 em 0..8; como as
    # classes sao contiguas, y - 1 e equivalente.
    Xp = X[div["pre"]]
    Xtr, ytr = X[div["treino"]], y[div["treino"]] - 1
    Xte, yte = X[div["teste"]], y[div["teste"]] - 1
    if len(div["val"]):
        Xva, yva = X[div["val"]], y[div["val"]] - 1
    else:
        Xva, yva = None, None

    # 1) pre-treino auto-supervisionado, so nas linhas do lado "pre-treino"
    autoencoder, encoder = build_autoencoder_1d(
        input_shape=(X.shape[1], 1), num_heads=SSL_NUM_HEADS, filters=SSL_FILTERS,
        kernel_sizes=SSL_KERNEL_SIZES, n_blocos=SSL_N_BLOCOS,
        dropout=SSL_DROPOUT, l2=SSL_L2,
    )
    autoencoder.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=SSL_LR), loss="mse")
    h_ssl = autoencoder.fit(
        Xp, Xp, epochs=epochs_ssl, batch_size=SSL_BATCH,
        validation_split=SSL_VALIDATION_SPLIT,
        callbacks=[EarlyStopping(monitor="val_loss", patience=SSL_PACIENCIA,
                                 restore_best_weights=True)],
        verbose=verboso,
    )

    # 2) ajuste fino
    modelo = build_ssl_classifier(encoder, input_shape=(X.shape[1], 1),
                                  num_classes=len(CLASSES))
    modelo.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=FT_LR),
                   loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    Xtr_aug, ytr_aug = augment_evi_series(Xtr, ytr, AUG_MULTIPLIER)
    # A receita usa dict(enumerate(compute_class_weight(...))); isso so esta
    # correto se as classes forem 0..k-1 sem buracos. Aqui a chave e o proprio
    # rotulo, para nao deslocar pesos quando alguma classe faltar no treino.
    classes_presentes = np.unique(ytr_aug)
    pesos = compute_class_weight("balanced", classes=classes_presentes, y=ytr_aug)
    pesos_dict = {int(c): float(w) for c, w in zip(classes_presentes, pesos)}

    validacao = (Xte, yte) if div["validacao_e_o_teste"] else (Xva, yva)
    h_ft = modelo.fit(
        Xtr_aug, ytr_aug, validation_data=validacao,
        epochs=epochs_ft, batch_size=FT_BATCH, class_weight=pesos_dict,
        callbacks=[EarlyStopping(monitor="val_accuracy", mode="max",
                                 patience=FT_PACIENCIA, restore_best_weights=True)],
        verbose=verboso,
    )

    proba = modelo.predict(Xte, verbose=0)
    pred = np.argmax(proba, axis=1)
    return pred, len(h_ssl.history["loss"]), len(h_ft.history["loss"])


# ---------------------------------------------------------------------------
# Uma rodada
# ---------------------------------------------------------------------------
def rodar_uma(caso, seed, X, y, meta, epochs_ssl=SSL_EPOCHS, epochs_ft=FT_EPOCHS):
    inicio = time.time()
    div = dividir(caso, y, meta, seed)
    avisos = list(div["avisos"])

    pred, ep_ssl, ep_ft = treinar_e_avaliar(X, y, div, seed, epochs_ssl, epochs_ft)

    yte = y[div["teste"]] - 1  # 0..8, igual ao LabelEncoder da receita
    rotulos = list(range(len(CLASSES)))
    acuracia = accuracy_score(yte, pred)
    f1_macro = f1_score(yte, pred, labels=rotulos, average="macro", zero_division=0)
    f1_por_classe = f1_score(yte, pred, labels=rotulos, average=None, zero_division=0)
    suporte = np.bincount(yte, minlength=len(CLASSES)) if len(yte) else np.zeros(len(CLASSES), int)
    # macro calculado so sobre as classes que existem no teste (secundario,
    # para separar "modelo pior" de "classe que sumiu do teste")
    presentes = [c for c, s in zip(rotulos, suporte) if s > 0]
    f1_macro_presentes = f1_score(yte, pred, labels=presentes, average="macro",
                                  zero_division=0)

    lugares = meta["grupo_id"].to_numpy()
    blocos = meta["bloco"].to_numpy()
    pre_l = set(lugares[div["pre"]]); tr_l = set(lugares[div["treino"]])
    va_l = set(lugares[div["val"]]); te_l = set(lugares[div["teste"]])
    lados = [pre_l, tr_l, va_l, te_l]
    vaz_lugares = any(lados[i] & lados[j] for i in range(4) for j in range(i + 1, 4))

    pre_b = set(blocos[div["pre"]]); tr_b = set(blocos[div["treino"]])
    va_b = set(blocos[div["val"]]); te_b = set(blocos[div["teste"]])
    lados_b = [pre_b, tr_b, va_b, te_b]
    vaz_blocos = any(lados_b[i] & lados_b[j] for i in range(4) for j in range(i + 1, 4))

    soma = sum(len(div[k]) for k in ("pre", "treino", "val", "teste"))
    ausentes = [NOMES[c + 1] for c, s in zip(rotulos, suporte) if s == 0]

    linha = {
        "caso": caso,
        "semente": seed,
        "acuracia": round(float(acuracia), 6),
        "f1_macro": round(float(f1_macro), 6),
        "f1_macro_presentes": round(float(f1_macro_presentes), 6),
        **{f"f1_classe_{c}": round(float(v), 6) for c, v in zip(CLASSES, f1_por_classe)},
        **{f"suporte_classe_{c}": int(v) for c, v in zip(CLASSES, suporte)},
        "n_linhas_pretreino": len(div["pre"]),
        "n_linhas_treino": len(div["treino"]),
        "n_linhas_validacao": len(div["val"]),
        "n_linhas_teste": len(div["teste"]),
        "n_lugares_pretreino": len(pre_l),
        "n_lugares_treino": len(tr_l),
        "n_lugares_validacao": len(va_l),
        "n_lugares_teste": len(te_l),
        "n_blocos_pretreino": len(pre_b),
        "n_blocos_treino": len(tr_b),
        "n_blocos_validacao": len(va_b),
        "n_blocos_teste": len(te_b),
        "teste_lugares_no_treino": len(te_l & tr_l),
        "teste_lugares_no_pretreino": len(te_l & pre_l),
        "teste_lugares_em_qualquer_lado": len(te_l & (tr_l | pre_l | va_l)),
        "soma_linhas": soma,
        "ok_soma": soma == len(y),
        "vazamento_lugares_entre_lados": bool(vaz_lugares),
        "vazamento_blocos_entre_lados": bool(vaz_blocos),
        "validacao_e_o_teste": bool(div["validacao_e_o_teste"]),
        "classes_ausentes_teste": ";".join(ausentes),
        "epocas_ssl": int(ep_ssl),
        "epocas_ft": int(ep_ft),
        "tempo_s": round(time.time() - inicio, 1),
        "avisos": " | ".join(avisos),
    }
    return linha


def _colunas(base: Path):
    # monta as colunas na ordem em que rodar_uma devolve
    linha = {
        "caso": "", "semente": 0, "acuracia": 0.0, "f1_macro": 0.0,
        "f1_macro_presentes": 0.0,
        **{f"f1_classe_{c}": 0.0 for c in CLASSES},
        **{f"suporte_classe_{c}": 0 for c in CLASSES},
    }
    for k in ("pretreino", "treino", "validacao", "teste"):
        linha[f"n_linhas_{k}"] = 0
    for k in ("pretreino", "treino", "validacao", "teste"):
        linha[f"n_lugares_{k}"] = 0
    for k in ("pretreino", "treino", "validacao", "teste"):
        linha[f"n_blocos_{k}"] = 0
    linha.update({
        "teste_lugares_no_treino": 0, "teste_lugares_no_pretreino": 0,
        "teste_lugares_em_qualquer_lado": 0, "soma_linhas": 0, "ok_soma": False,
        "vazamento_lugares_entre_lados": False, "vazamento_blocos_entre_lados": False,
        "validacao_e_o_teste": False, "classes_ausentes_teste": "",
        "epocas_ssl": 0, "epocas_ft": 0, "tempo_s": 0.0, "avisos": "",
    })
    return list(linha.keys())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _env(nome, padrao=None):
    return os.environ.get(nome, padrao)


def main():
    # Os defaults podem vir de variaveis de ambiente porque o `colab exec`
    # nao repassa argumentos de linha de comando para o arquivo.
    casos_env = _env("CASOS")
    sementes_env = _env("SEMENTES")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=_env("PASTA_DADOS", str(BASE_PADRAO)))
    ap.add_argument("--casos", nargs="+", choices=list("ABCD"),
                    default=casos_env.split(",") if casos_env else ["A", "B", "C"])
    ap.add_argument("--sementes", nargs="+", type=int,
                    default=[int(s) for s in sementes_env.split(",")] if sementes_env else SEMENTES_PADRAO)
    ap.add_argument("--saida", default=_env("SAIDA", "resultados.csv"))
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--conferir", action="store_true",
                    help="so confere as divisoes (nao precisa de TensorFlow)")
    ap.add_argument("--resumo", action="store_true",
                    help="le o CSV e imprime medias/desvios por caso")
    ap.add_argument("--epocas-ssl", type=int, default=SSL_EPOCHS)
    ap.add_argument("--epocas-ft", type=int, default=FT_EPOCHS)
    # parse_known_args: quando executado pelo kernel do Colab, o sys.argv
    # recebe argumentos internos do kernel (ex.: ...kernel-xxx.json).
    args, _ = ap.parse_known_args()

    base = Path(args.base)
    print(f"base={base.resolve()}", flush=True)
    try:
        import tensorflow as tf
        print(f"tensorflow={tf.__version__}", flush=True)
    except ImportError:
        print("tensorflow=ausente", flush=True)
    X, y, meta = carregar_dados(base)
    print(f"dados={X.shape} classes={np.bincount(y, minlength=10)[1:].tolist()}", flush=True)
    saida = base / args.saida

    if args.resumo:
        df = pd.read_csv(saida)
        print(df.groupby("caso")[["acuracia", "f1_macro"]].agg(["mean", "std", "count"]).to_string())
        return

    if args.conferir:
        for caso in args.casos:
            for seed in args.sementes:
                div = dividir(caso, y, meta, seed)
                partes = {k: len(div[k]) for k in ("pre", "treino", "val", "teste")}
                soma = sum(partes.values())
                lugares = meta["grupo_id"].to_numpy()
                conj = [set(lugares[div[k]]) for k in ("pre", "treino", "val", "teste")]
                inter = sum(len(conj[i] & conj[j]) for i in range(4) for j in range(i + 1, 4))
                blocos = meta["bloco"].to_numpy()
                conj_b = [set(blocos[div[k]]) for k in ("pre", "treino", "val", "teste")]
                inter_b = sum(len(conj_b[i] & conj_b[j]) for i in range(4) for j in range(i + 1, 4))
                apoio = np.bincount(y[div["teste"]], minlength=10)[CLASSES]
                print(f"{caso} s={seed}: {partes} soma={soma} "
                      f"inter_grupos={inter} inter_blocos={inter_b} "
                      f"classes_fora_teste={[c for c, s in zip(CLASSES, apoio) if s == 0]}")
        return

    feitos = set()
    if saida.exists() and not args.forcar:
        antigo = pd.read_csv(saida)
        feitos = {(str(c), int(s)) for c, s in zip(antigo["caso"], antigo["semente"])}
        print(f"{len(feitos)} rodadas ja no CSV; pulando.")

    colunas = _colunas(base)
    log = base / "log_treino.txt"
    for caso in args.casos:
        for seed in args.sementes:
            if (caso, seed) in feitos:
                continue
            print(f"[{time.strftime('%H:%M:%S')}] caso {caso} semente {seed} ...", flush=True)
            try:
                linha = rodar_uma(caso, seed, X, y, meta,
                                  epochs_ssl=args.epocas_ssl, epochs_ft=args.epocas_ft)
            except Exception:
                texto = traceback.format_exc()
                with open(log, "a", encoding="utf-8") as f:
                    f.write(f"\n=== FALHA caso {caso} semente {seed} ===\n{texto}\n")
                print(texto, flush=True)
                raise
            df = pd.DataFrame([linha], columns=colunas)
            df.to_csv(saida, mode="a", header=not saida.exists(), index=False,
                      encoding="utf-8")
            print(f"    acc={linha['acuracia']:.4f} f1={linha['f1_macro']:.4f} "
                  f"tempo={linha['tempo_s']}s aux={linha['classes_ausentes_teste'] or '-'}",
                  flush=True)
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"caso={caso} semente={seed} acc={linha['acuracia']} "
                        f"f1={linha['f1_macro']} tempo={linha['tempo_s']} "
                        f"ep_ssl={linha['epocas_ssl']} ep_ft={linha['epocas_ft']} "
                        f"avisos={linha['avisos']}\n")
    print("fim.")


if __name__ == "__main__":
    sys.exit(main())
