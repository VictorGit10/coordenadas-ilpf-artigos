# Sorteio dos pontos da auditoria piloto do mapa (semente fixa). Gera lista cega e gabarito separados.
import json,os,numpy as np,pandas as pd,geopandas as gpd
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
SEM=20261112; rng=np.random.default_rng(SEM)
RAIZ=os.environ.get('ILPF_RAIZ',os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D=os.environ.get('ILPF_MAPA_DADOS',os.path.join(RAIZ,'mapa_equipe','dados'))
R=os.environ.get('ILPF_SICOR_REPO',os.path.join(RAIZ,'..','ilpf-sicor','repo'))
OUT=os.environ.get('ILPF_AUDITORIA',os.path.join(RAIZ,'auditoria'))
BASE=os.environ.get('ILPF_AMOSTRAS',os.path.join(RAIZ,'ilpf-amostras'))
M=lambda la: np.log(np.tan(np.pi/4+np.radians(la)/2)); IM=lambda y: np.degrees(2*np.arctan(np.exp(y))-np.pi/2)
c=json.load(open(R+r'\assets_cnn_30m_manifest.json',encoding='utf-8'))['tiles']
m=json.load(open(R+r'\assets_mb_75m_manifest.json',encoding='utf-8'))['tiles']
pal={1:(237,220,75),2:(47,201,18),3:(60,77,10),4:(178,243,35),5:(240,41,7),6:(214,121,16),7:(188,185,21),8:(113,128,150),9:(27,67,50)}
codes=np.array(list(pal)); cols=np.array([pal[k] for k in pal])
mbn={(255,217,102):'pastagem',(233,116,237):'agricultura',(255,239,195):'mosaico',(102,90,58):'floresta_plantada',(0,0,0):'fora_uso_agro'}
mb=[(t['bounds'],np.array(Image.open(os.path.join(D,os.path.basename(t['file']))).convert('RGBA'))) for t in m if os.path.exists(os.path.join(D,os.path.basename(t['file'])))]
def mbclass(lat,lon):
    for ((s,w),(n,e)),a in mb:
        if s<lat<n and w<lon<e:
            h,wd=a.shape[:2]; y=int((M(n)-M(lat))/(M(n)-M(s))*h); x=int((lon-w)/(e-w)*wd); p=a[min(y,h-1),min(x,wd-1)]
            return mbn.get(tuple(int(v) for v in p[:3]) if p[3]>0 else (0,0,0),'outra_cor')
    return 'sem_mb'
tiles=[]; cand=[]; cover=0
for i,t in enumerate(c):
    f=os.path.join(D,os.path.basename(t['file']))
    if not os.path.exists(f): print('FALTA',f); continue
    a=np.array(Image.open(f).convert('RGBA')); tiles.append((t['bounds'],a))
    d5=((a[:,:,:3].astype(np.int32)-np.array(pal[5]))**2).sum(2)
    ys,xs=np.nonzero((d5<300)&(a[:,:,3]>0)); cover+=(a[:,:,3]>0).sum()
    cand.append(np.stack([np.full(len(ys),i),ys,xs],1))
cand=np.concatenate(cand); print('pixels IPF no mapa publicado:',len(cand),'| pixels com mapa:',cover)
pick=cand[rng.choice(len(cand),130,replace=False)]
rows=[]
for k,(i,y,x) in enumerate(pick):
    ((s,w),(n,e)),a=tiles[i]; H,W=a.shape[:2]
    lat=float(IM(M(n)-(y+.5)/H*(M(n)-M(s)))); lon=float(w+(x+.5)/W*(e-w))
    # borda: algum vizinho 3x3 que nao e IPF
    viz=a[max(0,y-1):y+2,max(0,x-1):x+2,:3].astype(int); borda=bool((((viz-np.array(pal[5]))**2).sum(2)>=300).any())
    rows.append(dict(grupo='mapa_IPF' if k<100 else 'reserva_IPF',lon=lon,lat=lat,mapbiomas=mbclass(lat,lon),borda=borda,origem=f'tile{i}_y{y}_x{x}'))
# controles com resposta conhecida: talhoes de ENSINO da equipe (nunca medicao)
d=pd.read_csv(BASE+r'\divisao_ensino_medicao.csv'); d=d[(d.grupo=='ensino')&(d.descartado.isna())]
d['c']=d.tipo_integ.astype(str).str.strip()
g=gpd.read_file(BASE+r'\amostras_ilpf_inspecionadas_4326.gpkg')[['IDs','geometry']].merge(d,on='IDs')
ult=g.sort_values('cropYear').groupby('talhao').tail(1)   # safra mais recente de cada talhao
cls=g.groupby('talhao').c.agg(lambda x:set(x))
pos=ult[ult.talhao.map(lambda t: cls[t]<= {'3','5','7'})]      # sempre com arvores
neg=ult[ult.talhao.map(lambda t: cls[t]<= {'1','2'})]          # sempre pastagem/agricultura
print('talhoes ensino sempre com arvores:',len(pos),'| sempre pastagem/agricultura:',len(neg))
for nome,df,n in [('controle_com_arvores',pos,15),('controle_sem_arvores',neg,20)]:
    for _,r in df.sample(n=min(n,len(df)),random_state=SEM).iterrows():
        p=r.geometry.representative_point(); rows.append(dict(grupo=nome,lon=p.x,lat=p.y,mapbiomas=mbclass(p.y,p.x),borda=False,origem=f'talhao{r.talhao}_classe{r.c}_{r.cropYear}'))
df=pd.DataFrame(rows)
rep=df[df.grupo=='mapa_IPF'].sample(15,random_state=SEM).copy(); rep['origem']='repeticao_de_'+rep.origem; rep['grupo']='repeticao'
df=pd.concat([df,rep],ignore_index=True)
df=df.sample(frac=1,random_state=SEM).reset_index(drop=True)
df['id']=[f'A{i+1:03d}' for i in range(len(df))]
df.to_csv(OUT+r'\gabarito_NAO_ABRIR.csv',index=False)
fila=df[df.grupo!='reserva_IPF'][['id','lon','lat']]; fila.to_csv(OUT+r'\pontos_fila_cega.csv',index=False)
df[df.grupo=='reserva_IPF'][['id','lon','lat']].to_csv(OUT+r'\pontos_reserva_cega.csv',index=False)
print(df.grupo.value_counts().to_dict()); print('fila cega:',len(fila))
print('mapbiomas nos 100:',df[df.grupo=='mapa_IPF'].mapbiomas.value_counts().to_dict(),'| em borda:',int(df[df.grupo=='mapa_IPF'].borda.sum()))
# por que algumas das 39 nao tem pixel
a39=gpd.read_file(os.environ.get('ILPF_A39',os.path.join(RAIZ,'evi2','amostras_renques_candidatas.gpkg')),layer='poligonos').to_crs(4326)
for _,r in a39.iterrows():
    p=r.geometry.representative_point(); st='fora de todas as imagens'
    for ((s,w),(n,e)),a in tiles:
        if s<p.y<n and w<p.x<e:
            H,W=a.shape[:2]; y=int((M(n)-M(p.y))/(M(n)-M(s))*H); x=int((p.x-w)/(e-w)*W); st='com mapa' if a[y,x,3]>0 else 'dentro da imagem, mas transparente'
    if st!='com mapa': print(r['id'],round(p.x,3),round(p.y,3),st)
