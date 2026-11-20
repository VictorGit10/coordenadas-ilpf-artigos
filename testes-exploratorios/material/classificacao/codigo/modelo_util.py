"""Utilitarios do modelo: carregar backbone, extrair features, aplicar cabeca."""
import json
import os

import numpy as np
import torch
from PIL import Image

# 8 transformacoes dihedral: 4 rotacoes x espelhamento horizontal
ANGULOS = [(k, f) for f in (False, True) for k in range(4)]
N_TTA = len(ANGULOS)


def transformar(img, k, flip):
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if k:
        img = img.rotate(90 * k, expand=True)
    return img


def carregar_base(base, input_size):
    import timm
    kwargs = dict(pretrained=True, num_classes=0)
    if "vit" in base or "swin" in base or "deit" in base:
        kwargs.update(img_size=input_size, dynamic_img_size=True)
    model = timm.create_model(base, **kwargs)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    return model


def norma(model):
    cfg = getattr(model, "pretrained_cfg", {}) or {}
    mean = cfg.get("mean", (0.485, 0.456, 0.406))
    std = cfg.get("std", (0.229, 0.224, 0.225))
    return np.asarray(mean, np.float32), np.asarray(std, np.float32)


def preparar(img, size, mean, std):
    img = img.convert("RGB").resize((size, size), Image.BILINEAR)
    x = np.asarray(img, np.float32) / 255.0
    x = (x - mean) / std
    return torch.from_numpy(np.ascontiguousarray(x.transpose(2, 0, 1)))


def _extrair_batch(model, batch):
    with torch.no_grad():
        out = model.forward_features(batch)
    if out.ndim == 3:
        npre = int(getattr(model, "num_prefix_tokens", 1) or 0)
        if npre:
            cls = out[:, 0]
            patches = out[:, npre:].mean(1)
            feat = torch.cat([cls, patches], 1)
        else:
            feat = out.mean(1)
    elif out.ndim == 4:
        feat = out.mean(dim=(2, 3))
    else:
        feat = out
    return feat.float().cpu().numpy()


def extrair_pil(model, imgs, size, mean, std, batch=8):
    """Como extrair_lista, mas recebe PIL images/np.ndarray. Devolve (N,8,D)."""
    n = len(imgs)
    feats = None
    for ini in range(0, n, 16):
        bloco = imgs[ini:ini + 16]
        xs = []
        for img in bloco:
            if isinstance(img, np.ndarray):
                img = Image.fromarray(img)
            for k, f in ANGULOS:
                xs.append(preparar(transformar(img, k, f), size, mean, std))
        saidas = []
        for i in range(0, len(xs), batch):
            b = torch.stack(xs[i:i + batch])
            if torch.cuda.is_available():
                b = b.cuda()
            saidas.append(_extrair_batch(model, b))
        arr = np.concatenate(saidas, 0)
        dim = arr.shape[1]
        if feats is None:
            feats = np.zeros((n, N_TTA, dim), np.float32)
        feats[ini:ini + len(bloco)] = arr.reshape(len(bloco), N_TTA, dim)
    return feats


def extrair_lista(model, caminhos, size, mean, std, batch=8, log=None, passo=100):
    """Devolve (N, 8, D) float32 com as 8 visoes de cada imagem."""
    n = len(caminhos)
    feats = None
    dim = None
    for ini in range(0, n, 16):
        bloco = caminhos[ini:ini + 16]
        xs = []
        for p in bloco:
            img = Image.open(p).convert("RGB")
            for k, f in ANGULOS:
                xs.append(preparar(transformar(img, k, f), size, mean, std))
        saidas = []
        for i in range(0, len(xs), batch):
            b = torch.stack(xs[i:i + batch])
            if torch.cuda.is_available():
                b = b.cuda()
            saidas.append(_extrair_batch(model, b))
        arr = np.concatenate(saidas, 0)
        dim = arr.shape[1]
        arr = arr.reshape(len(bloco), N_TTA, dim).astype(np.float32)
        if feats is None:
            feats = np.zeros((n, N_TTA, dim), np.float32)
        feats[ini:ini + len(bloco)] = arr
        if log and ((ini // 16) % max(1, passo // 16) == 0):
            log(f"    features {ini + len(bloco)}/{n}")
    return feats


def aplicar_cabeca(feats, cab):
    """feats (N,8,D) -> probabilidade media das 8 visoes."""
    n, t, d = feats.shape
    x = feats.reshape(-1, d).astype(np.float64)
    x = (x - cab["mean"]) / cab["scale"]
    z = x @ cab["coef"] + float(np.asarray(cab["intercept"]).ravel()[0])
    p = 1.0 / (1.0 + np.exp(-z))
    return p.reshape(n, t).mean(1)


def carregar_cabeca(pasta):
    z = np.load(os.path.join(pasta, "cabeca.npz"))
    return {k: z[k] for k in z.files}


def carregar_config(pasta):
    with open(os.path.join(pasta, "config.json"), encoding="utf-8") as f:
        return json.load(f)
