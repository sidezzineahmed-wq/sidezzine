"""Recette mpv-6c · états de chargement de « DCE à récupérer » / « Mes consultations suivies ».
Serveur local qui RETARDE ou REFUSE les fichiers du catalogue (base simulée, aucune écriture EAIOS).
A. catalogue lent : tant qu'il charge, jamais « absente du catalogue » ni « pas encore relevé » ; « Chargement de l'inventaire » ;
   compteurs provisoires annoncés puis recalculés (recalcul indépendant : dates des dossiers, puis dates PMMP) ; état réel ensuite.
B. catalogue en erreur : inventaire « indisponible » explicite, jamais « absente ».
Usage : python3 qa_mpv6c.py [js]   (js = script à tester, servi en app/eaios.js)"""
import os,sys,json,time,threading,http.server,functools,shutil
ICI0=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(ICI0,"qa_mpv6.py"),encoding="utf-8").read()
exec(src.split("\nwith sync_playwright() as p:")[0].replace('OUT=os.path.join(ICI,"qa_mpv6")','OUT=os.path.join(ICI,"qa_mpv6c")'))
JS=sys.argv[1] if len(sys.argv)>1 else os.path.join(SRV,"app","eaios.js")
SRVC=os.path.join(ICI,"srv6c");shutil.rmtree(SRVC,ignore_errors=True);shutil.copytree(SRV,SRVC,symlinks=True);shutil.copy(JS,os.path.join(SRVC,"app","eaios.js"))
MODE={"delai":0,"erreur":False}
class Hd(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path.split("?")[0].lstrip("/").startswith("catalogue"):
            if MODE["erreur"]:self.send_error(500);return
            time.sleep(MODE["delai"])
        return super().do_GET()
sv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Hd,directory=SRVC));threading.Thread(target=sv.serve_forever,daemon=True).start()
URLC=f"http://127.0.0.1:{sv.server_address[1]}/index.html"
# consultation suivie réelle présente au catalogue, inventaire lu
CAT=json.load(open(os.path.join(SRV,"catalogue.json"),encoding="utf-8"));CK={f"{x['o']}:{x['r']}" for x in CAT["items"]}
GK=None
for i,a in M["ao"].items():
    p=a.get("portail") or {}
    if p.get("ref") and f"{p.get('org')}:{p['ref']}" in CK and (CF.get(f"pmmp:{p['org']}:{p['ref']}") or {}).get("statuts",{}).get("docs")=="lu" and not a.get("base"):
        GK=f"p:{p['org']}:{p['ref']}";break
def ouvrir(b,w=1440,h=1000):
    ctx=b.new_context(viewport={"width":w,"height":h});ctx.add_init_script(INIT);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URLC);pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>100",timeout=40000);return ctx,pg,errs
EXPC="""cat=>{const C=cat&&S.cat?new Map(S.cat.items.map(x=>[x.o+':'+x.r,x])):null,G={};Object.entries(S.ao).forEach(([id,a])=>{if(!a||!(a.portail||a.veille))return;const k=a.portail&&a.portail.ref?a.portail.org+':'+a.portail.ref:'b:'+(a.base||id);(G[k]=G[k]||[]).push(id);});
  let n=0;Object.entries(G).forEach(([k,ids])=>{if(ids.some(id=>{const E=dceEtat(id,S.ao[id]);return E.k==='pret';}))return;const b=S.ao[ids.find(i=>!S.ao[i].base)||ids[0]],c=C&&C.get(k);
    const L=c?limEtat({lim:c.lim,h:c.h},Date.now()):limEtat({lim:b.lim,h:mpvH(b.heure)},Date.now());if(L.passe)return;if(ids.some(id=>['À examiner','En préparation'].includes(S.ao[id].statut)))n++;});return n;}"""
TABN="()=>+(document.querySelector('[data-mpv-tab=dce] .mpv-tn')||{innerText:'(-1)'}).innerText.replace(/[()]/g,'')"
INV="()=>{const p=document.querySelector('[data-mpv6-dpanel]');return p?{inv:(p.querySelector('[data-mpv6-inv]')||{dataset:{}}).dataset.mpv6Inv,t:p.innerText}:null}"
with sync_playwright() as p:
    b=p.chromium.launch()
    # ===== A. catalogue lent (12 s) + saisie dans la recherche pendant le chargement =====
    MODE.update(delai=12,erreur=False);ctx,pg,errs=ouvrir(b);ev=lambda js,*a:pg.evaluate(js,*a)
    ev(B11);ev("k=>{MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.sel=k;render();}",GK);pg.wait_for_timeout(400)
    A0=ev("()=>({cat:S.catState,t:document.querySelector('.mpv').innerText})");I0=ev(INV)
    chk(A0["cat"]=="loading" and I0 and I0["inv"]=="chargement" and "absente du catalogue" not in I0["t"] and "pas encore été relevée" not in I0["t"] and "Chargement de l'inventaire" in I0["t"],
        f"catalogue en chargement : panneau DCE « Chargement de l'inventaire », jamais « absente » ni « pas encore relevée » ({GK}, inv={I0 and I0['inv']})")
    chk("Chargement du catalogue" in A0["t"],"bandeau et file : chargement annoncé (dates des dossiers en attendant)")
    ev("k=>{MPV.tab='suiv';MPN.outil='veille';MPV.outil='veille';MPV6.ss.sel=k;render();}",GK);pg.wait_for_timeout(300)
    S0=ev("()=>{const p=document.querySelector('[data-mpv6-panel]');return p.innerText}")
    chk("Absente du catalogue" not in S0 and "Chargement du catalogue" in S0,"panneau Suivies pendant le chargement : « Chargement du catalogue », jamais « absente »")
    ev("()=>{MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';render();}");pg.wait_for_timeout(300)
    n0=ev(TABN);e0=ev(EXPC,False);note=ev("()=>(document.querySelector('[data-mpv6-catwait]')||{innerText:''}).innerText")
    chk(n0==e0 and "provisoires" in note,f"pendant le chargement : compteur DCE {n0} = recalcul sur les dates des dossiers ({e0}), annoncé provisoire")
    # saisie dans la recherche DCE (focus dans le champ) au moment où le catalogue arrive : il doit s'appliquer sans perturber la saisie
    pg.click('[data-mpv6-q="ds"]');pg.keyboard.type("zzqa",delay=40)
    try:
        pg.wait_for_function("()=>S.catState==='ok'",timeout=40000);bloque=False
    except Exception:
        bloque=True
    pg.wait_for_timeout(600)
    F=ev("()=>{const a=document.activeElement;return{cat:S.catState,att:!!S.catAttente,q:a&&a.dataset?a.dataset.mpv6Q:null,v:a&&a.value,c:a&&a.selectionStart,st:MPV6.ds.q}}")
    chk(not bloque and F["cat"]=="ok" and not F["att"],f"focus dans la recherche pendant l'arrivée du catalogue : chargement terminé, jamais bloqué {F}")
    chk(F["q"]=="ds" and F["v"]=="zzqa" and F["c"]==4 and F["st"]=="zzqa",f"saisie intacte : focus, texte et curseur conservés {F}")
    pg.keyboard.press("Control+a");pg.keyboard.press("Backspace");pg.wait_for_timeout(700)
    pg.wait_for_function("()=>S.catState==='ok'&&S.enrState==='ok'",timeout=60000);pg.wait_for_timeout(800)
    n1=ev(TABN);e1=ev(EXPC,True);hd=ev("()=>+document.querySelector('[data-mpv6-dn]').dataset.mpv6Dn");nw=ev("()=>!!document.querySelector('[data-mpv6-catwait]')")
    chk(n1==e1==hd and not nw,f"catalogue arrivé : compteur recalculé {n0} → {n1} (= recalcul sur les dates PMMP {e1}, en-tête {hd}), mention provisoire retirée")
    ev("k=>{MPV6.ss.q='';MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.sel=k;render();}",GK);pg.wait_for_timeout(400);I1=ev(INV)
    chk(I1 and I1["inv"]=="lu" and "absente" not in I1["t"],f"après chargement : état réel de l'inventaire ({I1 and I1['inv']})")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}");ctx.close()
    # ===== B. catalogue en erreur =====
    MODE.update(delai=0,erreur=True);ctx,pg,errs=ouvrir(b);ev=lambda js,*a:pg.evaluate(js,*a)
    pg.wait_for_function("()=>S.catState==='absent'",timeout=30000);ev(B11)
    ev("k=>{MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.sel=k;render();}",GK);pg.wait_for_timeout(400);I2=ev(INV);T2=ev("()=>document.querySelector('.mpv').innerText")
    chk(I2 and I2["inv"]=="erreur" and "absente du catalogue" not in I2["t"] and "indisponible" in I2["t"] and "Catalogue indisponible" in T2,f"catalogue en erreur : inventaire « indisponible » explicite, jamais « absente » ({I2 and I2['inv']})")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}");ctx.close()
    # ===== C. normal : consultation réellement absente du catalogue (dossier fictif) =====
    MODE.update(delai=0,erreur=False);ctx,pg,errs=ouvrir(b);ev=lambda js,*a:pg.evaluate(js,*a)
    pg.wait_for_function("()=>S.catState==='ok'&&S.enrState==='ok'",timeout=30000);ev(B11)
    ev("()=>{MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.sel='p:fxa:990001';render();}");pg.wait_for_timeout(400);I3=ev(INV)
    chk(I3 and I3["inv"]=="inconnu" and "absente du catalogue" in I3["t"],"catalogue chargé : une consultation vraiment absente reste « inconnu (absente du catalogue) »")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}");ctx.close();b.close()
open(os.path.join(OUT,"resultat.txt"),"w",encoding="utf-8").write("\n".join(R))
print(sum(r.startswith("OK") for r in R),"/",len(R))
