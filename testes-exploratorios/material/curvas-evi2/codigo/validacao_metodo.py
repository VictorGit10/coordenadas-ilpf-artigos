# -*- coding: utf-8 -*-
"""Valida o metodo EVI2 reconstruido contra samples_iCLS.csv (apenas registros de ensino)."""
import os
import ee, geopandas as gpd, pandas as pd, numpy as np, json, time

PROJ = os.environ.get('EE_PROJETO', 'SEU-PROJETO')
G = gpd.read_file('registros_ensino.gpkg').set_index('IDs')
DF = pd.read_csv('samples_iCLS.csv')
POLY = DF[DF.tipo_amostra == 'poligonal'].set_index('ID_ponto')


def months(crop_year):
    y0 = int(crop_year[:4])
    return [(y0, m) for m in range(10, 13)] + [(y0 + 1, m) for m in range(1, 11)]


def evi2(im):
    b4 = im.select('B4').multiply(0.0001)
    b8 = im.select('B8').multiply(0.0001)
    v = b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(2.4)).add(1))
    return v.rename('evi2').copyProperties(im, ['system:time_start'])


def curve(ee_geom, crop_year, cs=0.6, sensor='COPERNICUS/S2_HARMONIZED'):
    s2 = ee.ImageCollection(sensor)
    csp = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
    y0 = int(crop_year[:4])
    col = (s2.filterDate(f'{y0}-10-01', f'{y0 + 1}-10-31')
           .filterBounds(ee_geom)
           .linkCollection(csp, ['cs'])
           .map(lambda im: im.updateMask(im.select('cs').gte(cs)))
           .map(evi2))
    imgs = []
    for i, (y, m) in enumerate(months(crop_year), 1):
        ini = f'{y}-{m:02d}-01'
        fim = f'{y + 1}-01-01' if m == 12 else f'{y}-{m + 1:02d}-01'
        imgs.append(col.filterDate(ini, fim).median().rename(f'EVI2_{i:02d}'))
    img = ee.Image.cat(imgs)
    fc = ee.FeatureCollection([ee.Feature(ee_geom)])
    props = img.reduceRegions(fc, ee.Reducer.median(), 10).first().getInfo()['properties']
    return [props.get(f'EVI2_{i:02d}') for i in range(1, 14)]


def fill_linear(vals):
    """Preenche None por interpolacao linear entre meses vizinhos; bordas por repeticao do vizinho."""
    x = np.array([np.nan if v is None else float(v) for v in vals], dtype=float)
    n = len(x)
    idx = np.arange(n)
    good = ~np.isnan(x)
    if good.sum() == 0:
        return x
    if good.sum() == 1:
        return np.full(n, x[good][0])
    x[~good] = np.interp(idx[~good], idx[good], x[good])
    return x


def main():
    ee.Initialize(project=PROJ)
    ids = [(28, '2018/2019'), (31, '2021/2022'), (34, '2024/2025'),
           (661, '2019/2020'), (16, '2021/2022'), (13, '2023/2024'),
           (747, '2018/2019'), (749, '2020/2021'),
           (104, '2018/2019'), (17, '2022/2023'), (19, '2024/2025'),
           (47, '2018/2019'), (49, '2020/2021'), (51, '2022/2023'), (66, '2024/2025'),
           (1119, '2021/2022'), (1120, '2022/2023'), (1122, '2023/2024'), (1121, '2024/2025'),
           (1132, '2019/2020'), (898, '2019/2020')]
    rows = []
    t0 = time.time()
    for ID, cy in ids:
        geom = ee.Geometry(G.loc[ID].geometry.__geo_interface__)
        raw = curve(geom, cy)
        filled = fill_linear(raw)
        truth = np.array([float(POLY.loc[ID][f'EVI2_{i:02d}']) for i in range(1, 14)])
        d = np.abs(filled - truth)
        corr = np.corrcoef(filled, truth)[0, 1]
        rows.append(dict(ID=ID, cropYear=cy, classe=int(G.loc[ID].tipo_integ),
                         n_missing=int(sum(v is None for v in raw)), mad=float(d.mean()),
                         corr=float(corr),
                         **{f'obs_{i:02d}': (None if raw[i - 1] is None else float(raw[i - 1])) for i in range(1, 14)},
                         **{f'calc_{i:02d}': float(filled[i - 1]) for i in range(1, 14)},
                         **{f'csv_{i:02d}': float(truth[i - 1]) for i in range(1, 14)}))
        print(f'{ID:>5} {cy} cls{int(G.loc[ID].tipo_integ)} miss={rows[-1]["n_missing"]} MAD={d.mean():.4f} r={corr:.4f}', flush=True)
    out = pd.DataFrame(rows)
    out.to_csv('validacao_20.csv', index=False)
    print('\nmedian corr =', out['corr'].median())
    print('mean MAD   =', out['mad'].mean())
    print('median MAD =', out['mad'].median())
    print('max MAD    =', out['mad'].max())
    # MAD por mes (media entre registros)
    per_month = []
    for i in range(1, 14):
        per_month.append(float(np.mean(np.abs(out[f'calc_{i:02d}'] - out[f'csv_{i:02d}']))))
    print('MAD por mes:', [round(x, 4) for x in per_month])
    json.dump({'median_corr': float(out['corr'].median()), 'mean_mad': float(out['mad'].mean()),
               'per_month_mad': per_month}, open('validacao_metricas.json', 'w'), indent=1)
    print('elapsed', time.time() - t0)


if __name__ == '__main__':
    main()
