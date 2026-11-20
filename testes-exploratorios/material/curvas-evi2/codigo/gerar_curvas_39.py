# -*- coding: utf-8 -*-
"""Gera as curvas de EVI2 de 13 meses das 39 amostras (safra 2024/2025).

Metodo identificado e validado contra samples_iCLS.csv (21 registros de ensino,
MAD ~ 1e-8, r = 1.0):
  - COPERNICUS/S2_HARMONIZED (reflectancia de topo de atmosfera)
  - Cloud Score Plus, banda 'cs' >= 0.6
  - EVI2 = 2.5 * (B8 - B4) / (B8 + 2.4 * B4 + 1), reflectancias 0-1
  - mediana mensal por pixel (mes calendario) e depois mediana no poligono
  - meses vazios preenchidos por interpolacao linear entre vizinhos
"""
import os
import ee, geopandas as gpd, pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJ = os.environ.get('EE_PROJETO', 'SEU-PROJETO')
GPKG = 'amostras_renques_candidatas.gpkg'
CSV_OUT = 'curvas_evi2_39.csv'
PNG_OUT = 'curvas_39.png'

MESES = ['Out', 'Nov', 'Dez', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out+1']


def meses_safra(y0):
    return [(y0, m) for m in range(10, 13)] + [(y0 + 1, m) for m in range(1, 11)]


def evi2(im):
    b4 = im.select('B4').multiply(0.0001)
    b8 = im.select('B8').multiply(0.0001)
    v = b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(2.4)).add(1))
    return v.rename('evi2').copyProperties(im, ['system:time_start'])


def preencher(vals):
    """Interpolacao linear; bordas repetem o vizinho valido mais proximo."""
    x = np.array([np.nan if v is None else float(v) for v in vals], dtype=float)
    good = ~np.isnan(x)
    if good.sum() == 0:
        return x
    if good.sum() == 1:
        return np.full(len(x), x[good][0])
    idx = np.arange(len(x))
    x[~good] = np.interp(idx[~good], idx[good], x[good])
    return x


def main():
    ee.Initialize(project=PROJ)
    a = gpd.read_file(GPKG, layer='poligonos')
    a = a.sort_values('id').reset_index(drop=True)
    feats = [ee.Feature(ee.Geometry(row.geometry.__geo_interface__), {'id': row.id})
             for row in a.itertuples()]
    fc = ee.FeatureCollection(feats)
    geom_all = fc.geometry()

    s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    csp = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
    y0 = 2024
    col = (s2.filterDate(f'{y0}-10-01', f'{y0 + 1}-10-31')
           .filterBounds(geom_all)
           .linkCollection(csp, ['cs'])
           .map(lambda im: im.updateMask(im.select('cs').gte(0.6)))
           .map(evi2))

    imgs = []
    for i, (y, m) in enumerate(meses_safra(y0), 1):
        ini = f'{y}-{m:02d}-01'
        fim = f'{y + 1}-01-01' if m == 12 else f'{y}-{m + 1:02d}-01'
        imgs.append(col.filterDate(ini, fim).median().rename(f'EVI2_{i:02d}'))
    img = ee.Image.cat(imgs)

    props = img.reduceRegions(fc, ee.Reducer.median(), 10, tileScale=4).getInfo()['features']
    by_id = {f['properties']['id']: f['properties'] for f in props}

    rows = []
    for row in a.itertuples():
        raw = [by_id.get(row.id, {}).get(f'EVI2_{i:02d}') for i in range(1, 14)]
        filled = preencher(raw)
        rows.append(dict(ID_ponto=row.id,
                         tipo_integ=5 if row.classe_sugerida == 'IPF' else 7,
                         tipo_amostra='poligonal',
                         n_meses_vazios=int(sum(v is None for v in raw)),
                         **{f'EVI2_{i:02d}': float(filled[i - 1]) for i in range(1, 14)},
                         **{f'bruto_{i:02d}': ('' if raw[i - 1] is None else float(raw[i - 1])) for i in range(1, 14)}))
    df = pd.DataFrame(rows)
    df.to_csv('cobertura_39.csv', index=False)
    out = df[['ID_ponto', 'tipo_integ', 'tipo_amostra'] + [f'EVI2_{i:02d}' for i in range(1, 14)]]
    out.to_csv(CSV_OUT, index=True)
    print(out.to_string(index=False))
    print('\nmeses vazios:', int(df.n_meses_vazios.sum()))
    print(df[df.n_meses_vazios > 0][['ID_ponto', 'n_meses_vazios']].to_string(index=False))

    # --- grafico: 39 curvas + medianas IPF e Pastagem da planilha ---
    plano = pd.read_csv('samples_iCLS.csv')
    plano = plano[plano.tipo_amostra == 'poligonal']
    med_ipf = plano[plano.tipo_integ == 5][[f'EVI2_{i:02d}' for i in range(1, 14)]].median().values
    med_pas = plano[plano.tipo_integ == 1][[f'EVI2_{i:02d}' for i in range(1, 14)]].median().values

    fig, ax = plt.subplots(figsize=(11, 6.2))
    x = np.arange(13)
    for _, r in df.iterrows():
        y = r[[f'EVI2_{i:02d}' for i in range(1, 14)]].astype(float).values
        cor = '#2b6cb0' if r.tipo_integ == 5 else '#2f855a'
        ax.plot(x, y, color=cor, lw=0.8, alpha=0.28)
    ax.plot(x, med_ipf, color='#c53030', lw=3.2, label='Mediana IPF (planilha)')
    ax.plot(x, med_pas, color='#4a5568', lw=3.2, ls='--', label='Mediana Pastagem (planilha)')
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], color='#2b6cb0', lw=2, label='Amostras IPF (33)'),
               Line2D([0], [0], color='#2f855a', lw=2, label='Amostras ILF (6)'),
               Line2D([0], [0], color='#c53030', lw=3, label='Mediana IPF (planilha)'),
               Line2D([0], [0], color='#4a5568', lw=3, ls='--', label='Mediana Pastagem (planilha)')]
    ax.legend(handles=handles, loc='upper right', frameon=False)
    ax.set_xticks(x); ax.set_xticklabels(MESES)
    ax.set_ylabel('EVI2 (mediana mensal)')
    ax.set_xlabel('Mes da safra 2024/2025')
    ax.set_title('39 amostras de renques — EVI2 mensal (out/2024 a out/2025)')
    ax.grid(alpha=0.2)
    ax.set_ylim(0, max(0.85, float(df[[f'EVI2_{i:02d}' for i in range(1, 14)]].max().max()) + 0.05))
    fig.tight_layout()
    fig.savefig(PNG_OUT, dpi=200)
    print('PNG salvo:', PNG_OUT)


if __name__ == '__main__':
    main()
