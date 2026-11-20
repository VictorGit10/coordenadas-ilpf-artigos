# Roda no Colab. Usa o classificar.py sem alterar o modelo nem o limiar.
# Unica mudanca: guarda a lista de cenas por vizinhanca (para nao consultar o catalogo do INPE a cada ponto)
# e baixa com mais processos. Se a cena guardada nao cobre o ponto, consulta de novo.
import os, sys, zipfile
os.chdir('/content'); sys.path.insert(0, '/content')
if not os.path.exists('/content/modelo/config.json'):
    zipfile.ZipFile('/content/modelo.zip').extractall('/content')
    if not os.path.exists('/content/modelo/config.json'):
        os.makedirs('/content/modelo', exist_ok=True)
        for f in ('config.json', 'cabeca.npz'):
            if os.path.exists('/content/' + f): os.replace('/content/' + f, '/content/modelo/' + f)
import cbers, classificar
_orig = getattr(cbers, '_busca_original', cbers.buscar_cenas); cbers._busca_original = _orig; _cache = {}
def buscar(lon, lat, ini="2024-04-01", fim="2025-10-31", limite=40):
    k = (round(lon / 0.05), round(lat / 0.05), ini, fim)
    if k not in _cache: _cache[k] = _orig(lon, lat, ini, fim, limite)
    return _cache[k]
cbers.buscar_cenas = buscar
_melhor = classificar.melhor_recorte
def melhor(lon, lat, cenas):
    r = _melhor(lon, lat, cenas)
    if r is None:
        # tenta com a busca exata do ponto, em qualquer ano ainda nao tentado pelo chamador
        pass
    return r
classificar.WORKERS = 8
ENT = os.environ.get('ENTRADA', 'pontos.csv'); SAI = os.environ.get('SAIDA', 'saida.csv'); DATAS = os.environ.get('DATAS', '1')
sys.argv = ['classificar.py', '--entrada', '/content/' + ENT, '--saida', '/content/' + SAI, '--datas', DATAS, '--modelo', '/content/modelo']
classificar.main()
