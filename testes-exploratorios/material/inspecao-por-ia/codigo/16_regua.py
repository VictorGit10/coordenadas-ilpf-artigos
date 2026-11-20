"""Monta a página da 'régua': 50 fichas embaralhadas para uma pessoa marcar se há renques, sem ver o que a IA respondeu.
Uso: python 16_regua.py <pasta de destino>"""
import json, os, random, sys
from PIL import Image

RAIZ = os.environ.get("ILPF_RAIZ", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = sys.argv[1]
os.makedirs(os.path.join(DEST, "fichas"), exist_ok=True)
alvos = {a["id"]: a for a in json.load(open(os.path.join(RAIZ, "alvos.json"), encoding="utf-8")) if a["grupo"] == "listras"}
prim, rigor = {}, {}
for f in ["rodada5_listras", "rodada6_22KCE_2"]:
    prim.update(json.load(open(os.path.join(RAIZ, "leitura", f, "leituras.json"), encoding="utf-8")))
for f in ["rodada5b_rigor", "rodada5b_rigor2", "rodada6_rigor_22KCE_2"]:
    rigor.update(json.load(open(os.path.join(RAIZ, "leitura", f, "leituras.json"), encoding="utf-8")))
rnd = random.Random(2026)
sim = [f for f in prim if f in alvos and prim[f].get("renques_de_arvores") == "sim"]
nao = [f for f in prim if f in alvos and prim[f].get("renques_de_arvores") != "sim"]
rnd.shuffle(nao)
escolhidas = sim + nao[:50 - len(sim)]
rnd.shuffle(escolhidas)
gab = {}
for i, fid in enumerate(escolhidas, 1):
    Image.open(os.path.join(RAIZ, "fichas", fid + ".png")).convert("RGB").save(os.path.join(DEST, "fichas", f"{i:02d}.jpg"), quality=86)
    gab[f"{i:02d}"] = {"id": fid, "tile": alvos[fid].get("tile"), "primeira_leitura": prim[fid].get("renques_de_arvores"),
                       "segunda_leitura": (rigor.get(fid) or {}).get("nota")}
json.dump(gab, open(os.path.join(RAIZ, "regua_gabarito.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
html = """<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Régua de fichas ILPF</title>
<style>
body{font-family:system-ui,Segoe UI,sans-serif;margin:0;background:#f4f3ef;color:#1d1d1b}
header{padding:10px 16px;background:#fff;border-bottom:1px solid #ddd;display:flex;gap:16px;align-items:center;flex-wrap:wrap;position:sticky;top:0}
h1{font-size:17px;margin:0}#prog{font-variant-numeric:tabular-nums}
main{max-width:1250px;margin:0 auto;padding:12px 16px}
img{width:100%;border:1px solid #ccc;background:#fff}
.q{font-size:16px;margin:10px 0 6px}
.bts{display:flex;gap:8px;flex-wrap:wrap}
button{font:inherit;padding:10px 14px;border:1px solid #999;border-radius:8px;background:#fff;cursor:pointer}
button.on{background:#1f5f3a;color:#fff;border-color:#1f5f3a}
.nav{margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
input[type=text]{font:inherit;padding:8px;flex:1;min-width:220px;border:1px solid #999;border-radius:8px}
details{margin:8px 0;font-size:14px}.fim{background:#fff7d6;padding:10px;border-radius:8px;margin-top:10px}
</style>
<header><h1>Régua de fichas</h1><span id="prog"></span><button id="baixar">Baixar respostas</button></header>
<main>
<details open><summary>Como marcar</summary>
Cada ficha mostra: à esquerda a imagem de satélite de 2 m com o contorno amarelo da área avaliada; à direita o detalhe de 500 m no centro; embaixo a série de NDVI.
A pergunta é uma só: <b>há renques (fileiras paralelas de árvores plantadas, com pasto ou lavoura entre elas) dentro ou junto do contorno amarelo?</b>
Teclas: 1, 2, 3, 4 marcam e avançam; setas esquerda/direita navegam. As respostas ficam guardadas neste navegador; no fim, clique em "Baixar respostas" e salve o arquivo nesta mesma pasta.</details>
<img id="ficha" alt="ficha">
<div class="q">Há renques de árvores dentro ou junto do contorno amarelo?</div>
<div class="bts" id="bts"></div>
<div class="nav"><button id="ant">◀ Anterior</button><button id="prox">Próxima ▶</button><input type="text" id="obs" placeholder="Observação (opcional): o que é, classe provável, dúvida..."></div>
<div class="fim" id="fim" hidden>Todas marcadas. Clique em "Baixar respostas" e salve o arquivo <b>respostas_regua.json</b> nesta pasta.</div>
</main>
<script>
const N=__N__, OPC=[["sim","1 · Sim, nítido"],["sim_ressalva","2 · Sim, com ressalva"],["nao","3 · Não"],["nao_sei","4 · Não dá para dizer"]];
let r={};try{r=JSON.parse(localStorage.getItem("regua_ilpf")||"{}")}catch(e){}
let i=1;for(let k=1;k<=N;k++){if(!r[cod(k)]){i=k;break}}
function cod(k){return String(k).padStart(2,"0")}
function salvar(){try{localStorage.setItem("regua_ilpf",JSON.stringify(r))}catch(e){}}
function mostra(){document.getElementById("ficha").src="fichas/"+cod(i)+".jpg";
 const a=r[cod(i)]||{};document.getElementById("obs").value=a.obs||"";
 const b=document.getElementById("bts");b.innerHTML="";
 OPC.forEach(([v,t])=>{const e=document.createElement("button");e.textContent=t;if(a.resp===v)e.className="on";e.onclick=()=>marca(v);b.appendChild(e)});
 const feitas=Object.values(r).filter(x=>x.resp).length;
 document.getElementById("prog").textContent="Ficha "+i+" de "+N+" · "+feitas+" marcadas";
 document.getElementById("fim").hidden=feitas<N}
function marca(v){r[cod(i)]=Object.assign(r[cod(i)]||{},{resp:v});salvar();if(i<N)i++;mostra()}
document.getElementById("obs").oninput=e=>{r[cod(i)]=Object.assign(r[cod(i)]||{},{obs:e.target.value});salvar()};
document.getElementById("ant").onclick=()=>{if(i>1)i--;mostra()};
document.getElementById("prox").onclick=()=>{if(i<N)i++;mostra()};
document.addEventListener("keydown",e=>{if(e.target.id==="obs")return;
 if("1234".includes(e.key))marca(OPC[+e.key-1][0]);if(e.key==="ArrowLeft"&&i>1){i--;mostra()}if(e.key==="ArrowRight"&&i<N){i++;mostra()}});
document.getElementById("baixar").onclick=()=>{const a=document.createElement("a");
 a.href=URL.createObjectURL(new Blob([JSON.stringify(r,null,1)],{type:"application/json"}));a.download="respostas_regua.json";a.click()};
mostra();
</script></html>""".replace("__N__", str(len(escolhidas)))
open(os.path.join(DEST, "marcar-fichas.html"), "w", encoding="utf-8").write(html)
print(len(escolhidas), "fichas;", len(sim), "com 'sim' na 1a leitura;", len(escolhidas) - len(sim), "com 'não'")
