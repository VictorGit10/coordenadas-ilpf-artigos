# Monta as duas listas de pontos para o classificador:
#  A) centro das 564 regioes do detector de listras (249 que passaram na permanencia + 315 que nao passaram)
#  B) grade de 400 m num raio de 5 km em volta de cada lugar de artigo com coordenada em GO/DF
import json, math, csv, os
R = os.environ.get('ILPF_RAIZ', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); OUT = os.environ.get('ILPF_USO', os.path.join(R, 'classificador', 'uso'))
A = json.load(open(R + '/alvos.json', encoding='utf-8'))
with open(OUT + '/pontos_detector.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['id', 'lon', 'lat', 'grupo']); n = 0
    for a in A:
        if a['grupo'] in ('listras', 'listras_nao_persistente'):
            w.writerow([a['id'], round(float(a['lon']), 6), round(float(a['lat']), 6), a['grupo']]); n += 1
print('detector:', n)

loc = [l for l in json.load(open(R + '/texto/locais_v2.json', encoding='utf-8'))['locais'] if l['lat'] is not None and l['em_go_df']]
print('lugares:', len(loc))
PASSO, RAIO = 400.0, 5000.0
pts = []  # (lon, lat, local, dist)
for l in loc:
    klat = 110574.0; klon = 111320.0 * math.cos(math.radians(l['lat']))
    k = int(RAIO // PASSO)
    for i in range(-k, k + 1):
        for j in range(-k, k + 1):
            dx, dy = i * PASSO, j * PASSO; d = math.hypot(dx, dy)
            if d > RAIO: continue
            pts.append((l['lon'] + dx / klon, l['lat'] + dy / klat, l['local_id'], d))
# tira pontos a menos de 200 m de outro ja aceito (lugares vizinhos se sobrepoem)
aceitos = []; grade = {}
for lon, lat, lid, d in pts:
    cx, cy = int(lon * 111320 * math.cos(math.radians(-16)) // 200), int(lat * 110574 // 200)
    rep = False
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            for (lo2, la2) in grade.get((cx + a, cy + b), []):
                if math.hypot((lon - lo2) * 107000, (lat - la2) * 110574) < 200: rep = True
    if rep: continue
    grade.setdefault((cx, cy), []).append((lon, lat)); aceitos.append((lon, lat, lid, d))
with open(OUT + '/pontos_artigos.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['id', 'lon', 'lat', 'local', 'dist_m'])
    for n, (lon, lat, lid, d) in enumerate(aceitos):
        w.writerow([f'G{n:05d}', round(lon, 6), round(lat, 6), lid, int(d)])
print('grade artigos:', len(pts), '->', len(aceitos))
