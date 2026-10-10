"""Recette b31-6 · TVA documentée, provenance durable, historique automatique, coût / marge, comparaison des scénarios.
Base simulée locale (harnais de qa_b31.py) + dossiers FICTIFS « fx-v6* » uniquement ; Claude simulé ; les dossiers réels sont lus,
jamais écrits (vérifié à la fin). Les montants attendus sont recalculés ici en Python, indépendamment de la page."""
import os,sys,json,math,re,base64
import pypdf
ICI0=os.path.dirname(os.path.abspath(__file__))
M=json.load(open(os.path.join(ICI0,"srv","mockdb_b31.json"),encoding="utf-8"))
P0={"org":"fx","ref":"FXV6","url":""}
def ao(ref,est,soc="sakdat",cat="Travaux",**k):
    a={"ref":ref,"categorie":cat,"obj":"Construction fictive d'un bloc sanitaire (test b31-6)","est":est,"soc":soc,"statut":"En préparation","mo":"MAÎTRE D'OUVRAGE FICTIF","lim":"2026-12-15",
       "portail":dict(P0,ref=ref),"exig":{"estimation":est,"estimationSource":"FICTIF (test)"},"lieux":["LAAYOUNE"],"decision":{"verdict":"Go","le":"2026-10-01","qui":"u_qa","soc":soc}}
    a.update(k);return a
Q=[25,140,6,300,1,2400]
L6=[{"n":"1","d":"Béton armé pour semelles (v6)","u":"m³","q":25,"s":"A. Gros œuvre"},{"n":"2","d":"Carrelage grès cérame (v6)","u":"m²","q":140,"s":"B. Revêtements"},
    {"n":"3","d":"Porte isoplane bois (v6)","u":"U","q":6,"s":"C. Menuiserie"},{"n":"4","d":"Conduite PVC DN 110 (v6)","u":"ml","q":300,"s":"D. Plomberie"},
    {"n":"5","d":"Installation de chantier (v6)","u":"ENS","q":1,"s":"A. Gros œuvre"},{"n":"6","d":"Acier HA (v6)","u":"kg","q":2400,"s":"A. Gros œuvre"}]
PU={"0-0":1600,"0-1":210,"0-2":3400,"0-3":170,"0-4":28000,"0-5":13.5}
TVA20={"taux":20,"etat":"confirme","src":{"doc":"CPS FICTIF (test), article TVA","page":"1"},"mixte":False,"lignes":{},"par":"u_qa","le":"2026-10-01T00:00:00.000Z"}
# sous-détail fictif : une ressource connue par catégorie et par ligne (déboursé sec simple à recalculer)
DSR={"0-0":[("mat",1,900),("mo",6,30),("mt",1,50),("tr",1,30)],"0-1":[("mat",1,110),("mo",1,25)],"0-2":[("mat",1,2100),("mo",4,30)],
     "0-3":[("mat",1,85),("mo",0.5,30),("tr",1,4)],"0-4":[("mo",80,30),("mt",10,600),("tr",5,400)],"0-5":[("mat",1,8.2),("mo",0.05,30)]}
def sd_of(rows,soc):
    o={"mat":[],"mo":[],"mt":[],"tr":[]}
    for t,q,pu in rows:o[t].append({"d":f"Ressource {t} (fictive)","u":"u","q":q,"pu":pu,"st":"devis" if t=="mat" else "interne","four":"FOURNISSEUR FICTIF" if t=="mat" else "","date":"2026-09-15" if t=="mat" else "","soc":soc})
    return o
K6={"fc":5,"fg":8,"al":2,"ben":10}
for k,est,soc in (("fx-v6t",250000,"sakdat"),("fx-v6a",250000,"sakdat"),("fx-v6m",250000,"sakdat"),("fx-v6c",250000,"sakdat"),("fx-v6o",250000,"alwaad-ataib"),("fx-v6s",250000,"sakdat"),("fx-v6e",250000,"sakdat")):
    M["ao"][k]=ao(k.upper(),est,soc=soc);M["bp"][k]={"lots":[{"lignes":json.loads(json.dumps(L6))}],"cadre":False,"alertes":[]}
for k in ("fx-v6t","fx-v6m","fx-v6s","fx-v6e"):M["bpx"][k]={"p":dict(PU),"q":{},"soc":"sakdat","tva":dict(TVA20,soc="sakdat")}
M["bpx"]["fx-v6a"]={"p":dict(PU),"q":{},"soc":"sakdat"}                                         # aucun taux : TVA non renseignée
M["bpx"]["fx-v6c"]={"p":dict(PU),"q":{},"soc":"sakdat","tva":dict(TVA20,soc="sakdat"),"k":K6,"sd":{k:sd_of(v,"sakdat") for k,v in DSR.items()}}
M["bpx"]["fx-v6o"]={"p":{k:999 for k in PU},"q":{},"soc":"alwaad-ataib","tva":dict(TVA20,soc="alwaad-ataib"),
    "sd":{"0-0":{"mat":[{"d":"Ciment CPJ45 autre société","u":"t","q":1,"pu":999,"st":"devis","four":"FOURNISSEUR AUTRE","date":"2026-09-01","soc":"alwaad-ataib"}],"mo":[],"mt":[],"tr":[]}}}
# b31-6b : cartes de liste (hypothèse, mixte) et coût seul sur ligne verrouillée
for k,t in (("fx-v6h",{"taux":10,"etat":"hypothese","src":None,"mixte":False,"lignes":{}}),("fx-v6x",{"taux":20,"etat":"confirme","src":{"doc":"CPS FICTIF art. 9","page":"6"},"mixte":True,"lignes":{"0-1":10,"0-3":10}})):
    M["ao"][k]=ao(k.upper(),250000);M["bp"][k]={"lots":[{"lignes":json.loads(json.dumps(L6))}],"cadre":False,"alertes":[]};M["bpx"][k]={"p":dict(PU),"q":{},"soc":"sakdat","tva":dict(t,par="u_qa",le="2026-10-01T00:00:00.000Z",soc="sakdat")}
M["ao"]["fx-v6k"]=ao("FX-V6K",250000);M["bp"]["fx-v6k"]={"lots":[{"lignes":json.loads(json.dumps(L6))}],"cadre":False,"alertes":[]}
M["bpx"]["fx-v6k"]=json.loads(json.dumps(M["bpx"]["fx-v6c"]));M["bpx"]["fx-v6k"]["lock"]={"0-4":True}
M["prix"]={"biblio":{"items":[{"t":"mat","d":"Ciment groupe sans société","u":"t","pu":777,"at":"2026-01-01"},{"t":"mat","d":"Ciment groupe alwaad","u":"t","pu":888,"at":"2026-01-01","soc":"alwaad-ataib"},{"t":"mat","d":"Ciment propre sakdat","u":"t","pu":1111,"at":"2026-02-01","soc":"sakdat","src":"Devis fournisseur fictif"}]}}
json.dump(M,open(os.path.join(ICI0,"srv","mockdb_b31_v6.json"),"w",encoding="utf-8"),ensure_ascii=False)
src=open(os.path.join(ICI0,"qa_b31.py"),encoding="utf-8").read().replace("mockdb_b31.json","mockdb_b31_v6.json").replace('OUT=os.path.join(ICI,"qa_b31")','OUT=os.path.join(ICI,"qa_b31_v6")')
exec(src.split("\nwith sync_playwright() as p:")[0])
# ---------- calculs de référence, indépendants de la page ----------
def cts(x):return int(round(float(x)*100+1e-9)) if abs(float(x)*100-round(float(x)*100))<1e-6 else int(math.floor(float(x)*100+0.5))
def ligneC(q,pu):return (cts(q)*cts(pu)+50)//100
HTL={k:ligneC(Q[int(k[2:])],v) for k,v in PU.items()};HT=sum(HTL.values())
def tva(groups):return sum((h*r*100+5000)//10000 if isinstance(r,int) else math.floor((h*r+50)/100) for r,h in groups.items())
def tvai(h,r):return (h*r+50)//100
def CR(rows,K=K6):
    ds=sum(q*pu for _,q,pu in rows);a=ds*K["fc"]/100;b=(ds+a)*K["fg"]/100;c=(ds+a+b)*K["al"]/100;return round(ds,2),round(ds+a+b+c+1e-9,2)
STUB_SD="""(mode)=>{window.__prompts=[];S.sample=mode==="absent"?null:{json:async(pr)=>{window.__prompts.push(pr);if(mode==="echec")throw{code:"rate_limited"};
  if(pr.includes("SOUS-DÉTAIL HYPOTHÉTIQUE"))return{ressources:[{categorie:"mat",designation:"Ciment (hypothèse IA)",unite:"t",quantite:0.35,pu:1300},{categorie:"mo",designation:"Maçon (hypothèse IA)",unite:"h",quantite:5,pu:28},{categorie:"tr",designation:"Transport (hypothèse IA)",unite:"voyage",quantite:0.1,pu:null}],justification:"Ratios usuels supposés, aucun devis.",confiance:"basse"};
  const L=pr.split("LIGNES :\\n")[1].split("\\n").filter(Boolean).map(l=>JSON.parse(l));return{lignes:L.map(z=>({k:z.k,pu:100,inclut:"x",justification:"y",confiance:"moyenne"}))};}};}"""
FAIL_DB="""(quoi)=>{const d0=window.__db0=window.__db0||S.db;S.db={doc:p=>{const r=d0.doc(p);if((quoi==='ev'&&p.startsWith('chiffrage_evenements/'))||(quoi==='bpx'&&p.startsWith('bpx/')))return Object.assign({},r,{set:async()=>{window.__writes.push(['REFUS',p]);throw{code:'permission_denied'}}});return r;},collection:p=>d0.collection(p)};}"""
OK_DB="()=>{if(window.__db0)S.db=window.__db0;}"
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    W=lambda:len(ev("()=>window.__writes"))
    WS=lambda n:[w for w in ev("()=>window.__writes")[n:]]
    TOT="id=>{const a=S.ao[id],T=b31Tot(id,bpX(id).p),B=bpTot(id),M=b31TvaM(id,a);return{ht:T.htC,tva:T.tvaC,ttc:T.ttcC,bht:B.ht,bttc:B.ttc,etat:M.etat,ok:M.ok,txt:M.txt,par:T.parTaux}}"
    SETT="""async([id,t])=>{const a=S.ao[id];B31.tvaEd[id]=Object.assign({taux:'',etat:'hypothese',doc:'',page:'',mixte:false,lignes:{}},t);window.__toasts=[];const o=window.toast;window.toast=m=>{window.__toasts.push(m);};try{await b31TvaEnregistrer(id,a);}finally{window.toast=o;}return window.__toasts;}"""
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}")
    # ===== 1. TVA : 20 / 10 / 0 / absente / hypothèse / conflit DCE / mixte =====
    r=ev(TOT,"fx-v6t");T20=tvai(HT,20)
    chk(r["ht"]==HT and r["tva"]==T20 and r["ttc"]==HT+T20 and r["etat"]=="confirme" and r["ok"] and abs(r["bttc"]-(HT+T20)/100)<1e-9 and "CPS FICTIF" in r["txt"] and "p. 1" in r["txt"],f"TVA 20 % confirmée (CPS fictif, p. 1) : HT {HT/100:.2f}, TVA {T20/100:.2f}, TTC {(HT+T20)/100:.2f} ; bpTot identique")
    r=ev(TOT,"fx-v6a")
    chk(r["etat"]=="absent" and r["tva"] is None and r["ttc"] is None and r["ht"]==HT and "aucun taux inventé" in r["txt"],"TVA absente : HT calculé, TVA et TTC non calculés, « aucun taux inventé »")
    pr=ev("id=>{const r=b31Previsu(id,S.ao[id],-10);return{ok:r.ok,k:r.k,why:r.why}}","fx-v6a")
    chk(not pr["ok"] and pr["k"]=="tva" and "aucun taux n'est supposé" in pr["why"],"objectif % refusé sans taux de TVA (cible TTC non convertible en HT)")
    w0=W();t=ev(SETT,["fx-v6a",{"taux":"10","etat":"confirme","doc":"CPS FICTIF art. 9","page":""}])
    chk(W()==w0 and any("exige le document source ET la page" in x for x in t),"taux « confirmé » sans page : refusé, rien n'est écrit")
    t=ev(SETT,["fx-v6a",{"taux":"abc","etat":"hypothese"}]);chk(W()==w0 and any("non reconnu" in x for x in t),"taux non numérique : refusé, rien n'est écrit")
    t=ev(SETT,["fx-v6a",{"taux":"10","etat":"hypothese","doc":"","page":""}]);pg.wait_for_timeout(200)
    r=ev(TOT,"fx-v6a");T10=tvai(HT,10);ww=WS(w0)
    chk(r["etat"]=="hypothese" and r["tva"]==T10 and r["ttc"]==HT+T10 and not r["ok"] and ww==[["set","chiffrage_evenements/fx-v6a~e1"],["set","bpx/fx-v6a"]],f"TVA 10 % saisie en hypothèse : TVA {T10/100:.2f}, TTC {(HT+T10)/100:.2f} ; événement e1 PUIS bordereau ({ww})")
    vb=ev("id=>b31Bloquants(id,S.ao[id],b31Etat(id,S.ao[id]))","fx-v6a")
    chk(any("TVA non confirmée" in x for x in vb),"validation bloquée tant que la TVA n'est qu'une hypothèse")
    pr=ev("id=>{const r=b31Previsu(id,S.ao[id],0);return{ok:r.ok,cht:r.cibleHtC,c:r.cibleC,ttc:r.T&&r.T.ttcC}}","fx-v6a")
    chk(pr["ok"] and pr["cht"]==round(pr["c"]*100/110),f"objectif 0 % avec TVA 10 % : cible HT = cible TTC ÷ 1,10 ({pr['cht']/100:.2f}) — aucun 20 % codé")
    t=ev(SETT,["fx-v6a",{"taux":"0","etat":"confirme","doc":"CPS FICTIF art. 9 (exonération)","page":"4"}]);pg.wait_for_timeout(200)
    r=ev(TOT,"fx-v6a");chk(r["etat"]=="confirme" and r["tva"]==0 and r["ttc"]==HT and r["ok"],f"TVA 0 % confirmée (exonération fictive, p. 4) : TTC = HT = {HT/100:.2f}")
    e=ev("id=>window.__DB.chiffrage_evenements[id+'~e2']","fx-v6a")
    chk(e and e["type"]=="tva" and e["totaux_avant"]["ttc"]==f"{(HT+T10)//100}.{(HT+T10)%100:02d}" and e["totaux_apres"]["ttc"]==f"{HT//100}.{HT%100:02d}" and e["tva_apres"]["etat"]=="confirme" and e["soc"]=="sakdat" and e["par"],"changement de taux tracé : événement « tva » avec TTC avant / après, état, société, auteur")
    # conflit avec le taux relevé dans le DCE
    r=ev("id=>{const a=S.ao[id];a.exig.tva=14;const M=b31TvaM(id,a),B=b31Bloquants(id,a,b31Etat(id,a)),G=b31Garde44(id,a,null,null);delete a.exig.tva;return{c:M.conflit,b:B,g:G.bloque}}","fx-v6t")
    chk(r["c"] and "14 %" in r["c"] and any("14 %" in x for x in r["b"]) and r["g"],"taux relevé dans le DCE (14 %) ≠ taux saisi (20 %) : conflit bloquant (validation et garde d'application)")
    r=ev("id=>{const a=S.ao[id],X=bpX(id),t0=X.tva;X.tva=null;a.exig.tva=10;a.exig.sources={tva:'CPS fictif p. 3'};const M=b31TvaM(id,a),T=b31Tot(id,X.p);X.tva=t0;delete a.exig.tva;delete a.exig.sources;return{e:M.etat,ok:M.ok,t:T.tvaC,txt:M.txt}}","fx-v6t")
    chk(r["e"]=="dce" and not r["ok"] and r["t"]==T10 and "à confirmer" in r["txt"],"taux seulement relevé automatiquement dans le DCE : utilisé pour le calcul, affiché « à confirmer », validation exigée")
    # taux mixtes : lignes 2 et 4 à 10 %, autres à 20 %
    w0=W();t=ev(SETT,["fx-v6m",{"taux":"20","etat":"confirme","doc":"CPS FICTIF art. 9","page":"6","mixte":True,"lignes":{"0-1":"10","0-3":"10,0"}}]);pg.wait_for_timeout(200)
    r=ev(TOT,"fx-v6m");h10=HTL["0-1"]+HTL["0-3"];h20=HT-h10;TM=tvai(h10,10)+tvai(h20,20)
    chk(r["tva"]==TM and r["ttc"]==HT+TM and abs(r["bttc"]-(HT+TM)/100)<1e-9 and set(r["par"].keys())=={"10","20"} and r["ok"],f"DCE mixte : TVA 10 % sur {h10/100:.2f} + 20 % sur {h20/100:.2f} = {TM/100:.2f} ; TTC {(HT+TM)/100:.2f} (B3.1 = bpTot)")
    pr=ev("id=>{const r=b31Previsu(id,S.ao[id],-5);return{ok:r.ok,c:r.cibleC,ttc:r.T.ttcC,cht:r.cibleHtC}}","fx-v6m")
    chk(pr["ok"] and pr["cht"] is None and abs(pr["ttc"]-pr["c"])<=round(sum(Q)*0.6),f"objectif −5 % en taux mixtes : cible {pr['c']/100:.2f}, obtenu {pr['ttc']/100:.2f} (facteur sur les TTC de chaque ligne)")
    # exports Word / Excel cohérents
    ev("()=>{S.downloads={save:async o=>{window.__saves.push({filename:o.filename});}};window.withCachet=window.withCachet||null;}")
    ex=ev("async id=>{await b31Export(id,S.ao[id],'xls');return B31.dernierExport.html}","fx-v6m")
    chk("TVA 20 %" in ex and "TVA 10 %" in ex and f"{(HT+TM)//100}.{(HT+TM)%100:02d}" in ex and "Arrêté" in ex,"export Excel (taux mixtes) : une ligne de TVA par taux, TTC identique au calcul, arrêté en lettres")
    ex=ev("async id=>{await b31Export(id,S.ao[id],'xls');return B31.dernierExport.html}","fx-v6t")
    chk(f"{(HT+T20)//100}.{(HT+T20)%100:02d}" in ex and "TVA 20 %" in ex,"export Excel (20 % confirmée) : TTC identique")
    ev("id=>{const X=bpX(id);window.__tv=X.tva;X.tva=null;}","fx-v6s");ex=ev("async id=>{await b31Export(id,S.ao[id],'xls');return B31.dernierExport.html}","fx-v6s");ev("id=>{bpX(id).tva=window.__tv;}","fx-v6s")
    chk("taux non renseigné" in ex and "non calculé" in ex and "Arrêté le présent" not in ex and "aucun taux inventé" in ex,"export sans taux : TVA « non renseignée », TTC « non calculé », aucun arrêté en lettres")
    # PDF
    ev("()=>b31Pdf('fx-v6m')");pg.wait_for_function("()=>B31.pdf['fx-v6m']&&!B31.pdfBusy",timeout=30000)
    b64=ev("()=>{const e=B31.pdf['fx-v6m'].bytes;let s='';for(let i=0;i<e.length;i+=0x8000)s+=String.fromCharCode.apply(null,e.subarray(i,i+0x8000));return btoa(s)}")
    open(f"{OUT}/fx_v6m.pdf","wb").write(base64.b64decode(b64));Tp=re.sub(r"\s+"," "," ".join(x.extract_text() or "" for x in pypdf.PdfReader(f"{OUT}/fx_v6m.pdf").pages))
    chk("TVA 10 %" in Tp and "TVA 20 %" in Tp and "Arrêté à" in Tp and "TVA du dossier" in Tp and "confirmée" in Tp,"PDF (taux mixtes) : TVA par taux, arrêté, état et source de la TVA")
    pg.keyboard.press("Escape");ev("()=>{const v=document.getElementById('viewer');if(v)v.hidden=true;}")
    # validation et offre figée avec TVA documentée (fictif)
    vl=ev("""id=>{const a=S.ao[id];b31Valider(id,a);b31Valider(id,a);const O=offreCourante(id,a),T=bpTot(id);return{pv:a.prixValide&&a.prixValide.tva,ttc:O&&O.total_ttc,tv:O&&O.bpu.map(l=>l.tva),int:O?offreIntegre(O):['absente'],fait:prixFait(id,a,T),st:b31Etat(id,a).statut.k}}""","fx-v6m")
    chk(vl["ttc"]==f"{(HT+TM)//100}.{(HT+TM)%100:02d}" and vl["tv"]==["20","10","20","10","20","20"] and not vl["int"] and vl["fait"] and vl["st"]=="valide" and vl["pv"]["etat"]=="confirme","validation (fictif, TVA mixte confirmée) : offre figée au même TTC, taux par ligne figés, intégrité vérifiée, prixValide avec TVA documentée")
    lg=ev("()=>Object.values(S.offres).filter(o=>!String(o.ao_id).startsWith('fx-')).map(o=>[o.offer_id,offreIntegre(o).length])")
    chk(lg and all(x[1]==0 for x in lg),f"offres figées réelles antérieures (sans taux par ligne) : intégrité inchangée ({len(lg)} offres, recalcul d'origine)")
    # ===== 2. provenance durable et historique automatique (objectif %) =====
    ouvrir(pg,"fx-v6e");pg.click('[data-b31-mode="pct"]');pg.fill('[data-b31-pct="fx-v6e"]',"-10");pg.wait_for_timeout(500);ev("()=>{const id='fx-v6e';bpX(id).lock={'0-4':true};window.__DB.bpx[id].lock={'0-4':true};render();}")
    pg.click('[data-b31-prev]');pg.wait_for_selector("[data-b31-prv]");w0=W();pg.click('[data-b31-appl="1"]');pg.wait_for_timeout(700)
    ww=WS(w0);D=ev("()=>window.__DB")
    e1=D["chiffrage_evenements"].get("fx-v6e~e1");X=D["bpx"]["fx-v6e"]
    chk(ww==[["set","chiffrage_evenements/fx-v6e~e1"],["set","bpx/fx-v6e"]],f"objectif −10 % : événement immuable écrit AVANT le bordereau, sans « Enregistrer le brouillon » ({ww})")
    pv=X["srcL"]["0-0"]
    chk(e1["type"]=="objectif" and len(e1["lignes"])==5 and e1["soc"]=="sakdat" and e1["par"] and e1["le"] and e1["totaux_avant"]["ttc"] and e1["totaux_apres"]["ttc"] and e1["contexte"]["pct"]==-10 and e1["contexte"]["verrouillees"]==1 and e1["hash"],"événement : 5 lignes (verrouillée exclue), avant / après, TTC avant / après, auteur, date, contexte (%, verrous), empreinte")
    chk(pv["v"]==6 and pv["pu_base"]==1600 and pv["pu_avant"]==1600 and pv["coef_pct"]==-10 and pv["applique"]==X["p"]["0-0"] and pv["par"] and pv["le"] and pv["evt"]=="e1" and pv["methode"]=="existant" and "0-4" not in X["srcL"],"provenance enregistrée : PU avant, base avant coefficient, coefficient %, facteur, PU appliqué, auteur, date, événement ; ligne verrouillée sans provenance nouvelle")
    pg.evaluate("()=>window.__persist()");pg.reload();pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.bpx['fx-v6e']",timeout=20000);pg.wait_for_timeout(800)
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}")
    ouvrir(pg,"fx-v6e");pg.wait_for_timeout(400)
    s=ev("()=>bpX('fx-v6e').srcL['0-0']");chk(s and s["v"]==6 and s["pu_base"]==1600 and s["evt"]=="e1","après rechargement : provenance détaillée relue depuis le stockage")
    pg.click('[data-b31-provb="0-0"]');pg.wait_for_selector('[data-b31-provd="0-0"]');d=pg.inner_text('[data-b31-provd="0-0"]')
    chk("PU de base (avant coefficient)" in d and "1 600,00" in d.replace(" "," ").replace("\xa0"," ") and "−10 %" in d and "e1" in d and "Appliqué par" in d,"interface : détail de provenance (base, coefficient, auteur, date, événement) accessible après rechargement")
    pg.screenshot(path=f"{OUT}/fx_v6_provenance.png")
    pg.click("[data-b31-hist]");pg.wait_for_selector("[data-b31-ev='1']");h=pg.inner_text(".b31-dlg")
    chk("Événements de prix (1" in h and "e1" in h and "appliqué" in h,"historique : événement e1 listé avec statut « appliqué » (déduit du bordereau enregistré)")
    pg.screenshot(path=f"{OUT}/fx_v6_historique.png");pg.click(".b31-dlg .fsx")
    pg.evaluate("()=>sessionStorage.removeItem('__qadb')")
    # ===== 3. saisie manuelle effective (interface), valeur identique, IA, verrous =====
    ouvrir(pg,"fx-v6e");w0=W()
    pg.fill("#bpi0-1","233,5".replace(",","."));pg.wait_for_timeout(200)
    chk(W()==w0 and "non enregistré" in pg.inner_text("#bpt0-1"),"frappe en cours : rien n'est écrit, montant affiché « non enregistré » (valeur en attente)")
    chk(ev("()=>bpX('fx-v6e').p['0-1']")!=233.5,"frappe en cours : PU enregistré inchangé tant que la saisie n'est pas validée")
    pg.press("#bpi0-1","Enter");pg.wait_for_timeout(600);ww=WS(w0)
    e=ev("()=>window.__DB.chiffrage_evenements['fx-v6e~e2']")
    chk(ww==[["set","chiffrage_evenements/fx-v6e~e2"],["set","bpx/fx-v6e"]] and e["type"]=="manuel" and e["lignes"][0]["apres"]==233.5 and e["lignes"][0]["prov"]["m"]=="manuel" and ev("()=>bpX('fx-v6e').p['0-1']")==233.5,"saisie manuelle validée (Entrée) : événement « manuel » puis bordereau ; provenance « saisie manuelle »")
    w0=W();pg.fill("#bpi0-1","233.50");pg.press("#bpi0-1","Enter");pg.wait_for_timeout(500)
    chk(W()==w0,"même valeur ressaisie : modification non effective, rien n'est écrit")
    w0=W();ev("()=>{const id='fx-v6e';bpX(id).lock['0-2']=true;window.__DB.bpx[id].lock['0-2']=true;}")
    ev("async()=>{await b31Manuel('fx-v6e',S.ao['fx-v6e'],'0-2','1')}");ev("async()=>{await b31Accepter('fx-v6e',S.ao['fx-v6e'],'0-2',5,'Claude (test)','2026-10-01')}");pg.wait_for_timeout(300)
    chk(W()==w0 and ev("()=>bpX('fx-v6e').p['0-2']")!=1,"ligne verrouillée : saisie manuelle et acceptation IA refusées, rien n'est écrit")
    w0=W();ev("async()=>{await b31Accepter('fx-v6e',S.ao['fx-v6e'],'0-3',181.25,'Claude — estimation du modèle (test)','2026-10-09T10:00:00Z',{inc:'fourniture et pose',hyp:'rendement supposé',conf:'moyenne'})}");pg.wait_for_timeout(300)
    e=ev("()=>window.__DB.chiffrage_evenements['fx-v6e~e3']");pv=ev("()=>bpX('fx-v6e').srcL['0-3']")
    chk(WS(w0)==[["set","chiffrage_evenements/fx-v6e~e3"],["set","bpx/fx-v6e"]] and e["type"]=="ia" and pv["propose"]==181.25 and pv["applique"]==181.25 and pv["confiance"]=="moyenne" and pv["hypotheses"]=="rendement supposé" and pv["par"],"acceptation IA : événement « ia », provenance (proposé, appliqué, hypothèses, confiance, auteur)")
    # ===== 4. échecs de stockage, version concurrente =====
    w0=W();ev(FAIL_DB,"ev");p0=ev("()=>JSON.stringify(bpX('fx-v6e').p)");ev("async()=>{await b31Manuel('fx-v6e',S.ao['fx-v6e'],'0-1','240')}");pg.wait_for_timeout(300);ev(OK_DB)
    chk([w for w in WS(w0) if w[0]!="REFUS"]==[] and ev("()=>JSON.stringify(bpX('fx-v6e').p)")==p0 and any("historique non enregistré" in x for x in ev("()=>window.__toastLog")),"historique refusé par le stockage : AUCUN prix écrit, bordereau inchangé, message explicite")
    w0=W();ev(FAIL_DB,"bpx");ev("async()=>{await b31Manuel('fx-v6e',S.ao['fx-v6e'],'0-1','240')}");pg.wait_for_timeout(300);ev(OK_DB)
    ww=WS(w0);D=ev("()=>window.__DB.chiffrage_evenements")
    chk(ww==[["set","chiffrage_evenements/fx-v6e~e4"],["REFUS","bpx/fx-v6e"],["set","chiffrage_evenements/fx-v6e~e5"]] and D["fx-v6e~e5"]["type"]=="echec_ecriture" and D["fx-v6e~e5"]["ref"]=="fx-v6e~e4" and ev("()=>JSON.stringify(bpX('fx-v6e').p)")==p0 and any("prix non enregistrés" in x for x in ev("()=>window.__toastLog")),"bordereau refusé après l'historique : état local restauré, événement « échec » ajouté, aucun « enregistré » affiché")
    ouvrir(pg,"fx-v6e");pg.click("[data-b31-hist]");pg.wait_for_selector("[data-b31-ev='4']");h=ev("()=>document.querySelector(\"[data-b31-ev='4']\").innerText")
    chk("non appliqué" in h,"historique : l'événement e4 est affiché « non appliqué : écriture du bordereau refusée »");pg.click(".b31-dlg .fsx")
    w0=W();ev("()=>{window.__DB.bpx['fx-v6e'].p['0-5']=99;}");ev("async()=>{await b31Manuel('fx-v6e',S.ao['fx-v6e'],'0-1','250')}");pg.wait_for_timeout(300)
    chk(WS(w0)==[] and any("diffère de celui affiché" in x for x in ev("()=>window.__toastLog")),"bordereau modifié ailleurs (version concurrente) : rien n'est écrit, rechargement demandé")
    ev("()=>{window.__DB.bpx['fx-v6e'].p['0-5']=bpX('fx-v6e').p['0-5'];window.__DB.chiffrage_evenements['fx-v6e~e6']={ao_id:'fx-v6e',soc:'sakdat',seq:6,type:'manuel',label:'écrit ailleurs'};B31.ev['fx-v6e']=B31.ev['fx-v6e'].filter(e=>e.seq<6);}")
    w0=W();ev("async()=>{const L=B31.ev['fx-v6e'];await b31ChargerEv('fx-v6e');B31.ev['fx-v6e']=L;}")
    r=ev("async()=>{const id='fx-v6e',a=S.ao[id];const o=b31ChargerEv;b31ChargerEv=async()=>{};try{await b31Ecrire(id,a,{type:'manuel',lignes:[{k:'0-1',apres:260,prov:null}]});return 'ecrit'}catch(e){return e.message}finally{b31ChargerEv=o;}}")
    chk("existe déjà" in r and WS(w0)==[],f"numéro d'événement déjà pris (écriture concurrente) : création refusée, aucun écrasement ({r[:60]})")
    # ===== 5. coût, marge, sous-détail propre à la société =====
    C=ev("id=>{const a=S.ao[id],ET=b31Etat(id,a),Mg=b31Marge(ET.C,ET.T);return{k:ET.C.k,N:ET.C.N,cout:ET.C.coutC,ds:ET.C.dsC,ht:ET.T.htC,m:Mg&&Mg.mC,pct:Mg&&Mg.pct,perte:ET.C.perte,def:ET.C.kDefaut}}","fx-v6c")
    exp=sum(ligneC(Q[int(k[2:])],CR(v)[1]) for k,v in DSR.items());dse=sum(ligneC(Q[int(k[2:])],CR(v)[0]) for k,v in DSR.items())
    chk(C["k"]==6 and C["cout"]==exp and C["ds"]==dse and C["m"]==HT-exp and abs(C["pct"]-(HT-exp)/HT*100)<1e-9 and not C["def"],f"coût complet 6/6 : déboursé sec {dse/100:.2f}, coût de revient (hors bénéfice) {exp/100:.2f}, vente {HT/100:.2f}, marge {(HT-exp)/100:.2f} = {(HT-exp)/HT*100:.2f} % de la vente HT")
    ouvrir(pg,"fx-v6c");rc=pg.inner_text("#b31-recap")
    chk("Déboursé sec HT" in rc and "Coût de revient HT" in rc and "base : vente HT" in rc and "Marge HT" in rc,"récapitulatif : déboursé sec, coût de revient (hors bénéfice), vente, marge et base du taux explicites")
    pg.screenshot(path=f"{OUT}/fx_v6_couts.png")
    r=ev("id=>{const X=bpX(id),r=X.sd['0-3'].mat[0],sv=r.pu;r.pu='';const ET=b31Etat(id,S.ao[id]),M=b31Marge(ET.C,ET.T),c=b31SdCalc(id,'0-3',S.ao[id]);r.pu=sv;return{k:ET.C.k,m:M,inc:c.inc,cu:b31CoutU(id,'0-3')}}","fx-v6c")
    chk(r["k"]==5 and r["m"] is None and r["inc"] and "prix inconnu" in r["inc"][0],"ressource sans prix : coût de la ligne INCONNU (jamais 0), couverture 5/6, marge globale non calculée")
    r=ev("id=>{const X=bpX(id),sv=X.p['0-4'];X.p['0-4']=1000;const ET=b31Etat(id,S.ao[id]),M=b31Marge(ET.C,ET.T);const o={perte:ET.C.perte,m:M&&M.mC,p:M&&M.perte};X.p['0-4']=sv;return o}","fx-v6c")
    chk(r["perte"]==["5"],f"ligne vendue sous son coût de revient signalée (N° 5) ; marge globale {r['m']/100:.2f}")
    r=ev("id=>{const X=bpX(id),sv=JSON.stringify(X.p);Object.keys(X.p).forEach(k=>X.p[k]=+(X.p[k]*0.5).toFixed(2));const ET=b31Etat(id,S.ao[id]),M=b31Marge(ET.C,ET.T),h=b31Recap(id,S.ao[id],ET);X.p=JSON.parse(sv);return{p:M.perte,m:M.mC,h:h.includes('Offre à perte')}}","fx-v6c")
    chk(r["p"] and r["m"]<0 and r["h"],f"offre à perte (PU divisés par 2, calcul pur) : marge {r['m']/100:.2f} DH, « Offre à perte » affiché")
    r=ev("()=>{const B=b31SdBiblio(S.ao['fx-v6c']);return{d:B.L.map(z=>z.d+'|'+z.pu),h:B.horsSoc}}")
    chk(not any("999" in x or "777" in x or "888" in x or "autre société" in x for x in r["d"]) and any("Ciment propre sakdat|1111" in x for x in r["d"]) and r["h"]==2,f"bibliothèque de sous-détail : seules les ressources de SAKDAT ; 2 entrées du groupe (sans société / autre société) exclues ; aucun prix d'ALWAAD ({len(r['d'])} entrées)")
    pg.click('[data-b31-sd="0-0"]');pg.click('[data-b31-sdopen="0-0"]');pg.wait_for_selector(".b31-sdp");sp=pg.inner_text(".b31-sdp")
    chk("Transport" in sp and "Matériel" in sp and "Main-d'œuvre" in sp and "Coût de revient (hors bénéfice)" in sp and "Prix de vente théorique HT" in sp and "FIN-ISO-001" in sp and "bibliothèque du groupe" in sp,"panneau sous-détail : matériaux, main-d'œuvre, matériel, transport, frais, coût de revient, prix de vente ; bibliothèque du groupe hors société exclue (message)")
    opts=ev("()=>[...document.querySelectorAll('#b31-sdl-mat option')].map(o=>o.value)");chk("Ciment propre sakdat" in opts and not any("groupe" in o or "autre" in o for o in opts),f"suggestions de ressources : uniquement la société ({opts})")
    pg.screenshot(path=f"{OUT}/fx_v6_sousdetail.png")
    # ressource d'une autre société injectée : exclue et signalée
    r=ev("id=>{const X=bpX(id);X.sd['0-1'].mat.push({d:'Ressource étrangère',u:'u',q:1,pu:5,st:'devis',soc:'alwaad-ataib'});const c=b31SdCalc(id,'0-1',S.ao[id]),ET=b31Etat(id,S.ao[id]),B=b31Bloquants(id,S.ao[id],ET);X.sd['0-1'].mat.pop();return{etr:c.etr,cpl:c.complet,b:B.some(x=>x.includes('FIN-ISO-001'))}}","fx-v6c")
    chk(r["etr"] and not r["cpl"] and r["b"],"ressource rattachée à une autre société : exclue du coût (ligne inconnue) et validation bloquée (FIN-ISO-001)")
    # proposition IA de sous-détail (hypothèse) puis acceptation humaine, puis report
    ev(STUB_SD,"ok");pg.click(".b31-dlg .fsx");ev("()=>{const id='fx-v6s';delete bpX(id).sd;}");ouvrir(pg,"fx-v6s");pg.click('[data-b31-sd="0-0"]');pg.click('[data-b31-sdopen="0-0"]');pg.wait_for_selector(".b31-sdp")
    w0=W();pg.click('[data-b31-sdia]');pg.wait_for_selector('[data-b31-sdprop]');t=pg.inner_text('[data-b31-sdprop]')
    chk(W()==w0 and "hypothèse à vérifier" in t and "sans devis, sans fournisseur ni date" in t,"proposition IA de sous-détail : affichée comme hypothèse, aucun devis / fournisseur / date inventé, rien n'est écrit")
    pmt=ev("()=>window.__prompts.slice(-1)[0]");chk("n'invente ni fournisseur, ni date" in pmt and "MÊME société" not in pmt or "SAKDAT" in pmt,"invite IA : interdiction d'inventer fournisseur, date ou devis ; société nommée")
    pg.click('[data-b31-sdacc]');pg.wait_for_timeout(300);sd=ev("()=>bpX('fx-v6s').sd['0-0']");p00=ev("()=>bpX('fx-v6s').p['0-0']")
    chk(all(r["st"]=="ia" and r["four"]=="" and r["date"]=="" and r["soc"]=="sakdat" for t2 in ("mat","mo","tr") for r in sd[t2]) and p00==1600,"acceptation humaine : ressources marquées « proposition IA (hypothèse) », sans fournisseur ni date ; PU du bordereau inchangé")
    c=ev("()=>b31SdCalc('fx-v6s','0-0',S.ao['fx-v6s'])");chk(not c["complet"] and "prix inconnu" in " ".join(c["inc"]),"ressource IA sans prix : coût inconnu, report impossible")
    ev("()=>{const r=bpX('fx-v6s').sd['0-0'].tr[0];r.pu=250;r.st='hypothese';}");ev("()=>{const id='fx-v6s';window.__DB.bpx[id]=JSON.parse(JSON.stringify(bpX(id)));render();}");pg.wait_for_timeout(200)
    c=ev("()=>b31SdCalc('fx-v6s','0-0',S.ao['fx-v6s'])");w0=W();pg.click('[data-b31-sdrep]');pg.wait_for_timeout(500)
    e=ev("()=>Object.values(window.__DB.chiffrage_evenements).filter(e=>e.ao_id==='fx-v6s').pop()");pv=ev("()=>bpX('fx-v6s').srcL['0-0']")
    chk(WS(w0)==[["set","chiffrage_evenements/fx-v6s~e1"],["set","bpx/fx-v6s"]] and e["type"]=="sous_detail" and ev("()=>bpX('fx-v6s').p['0-0']")==c["pv"] and pv["pu_base"]==c["cr"] and pv["confiance"]=="basse" and "hypothèse" in (pv["hypotheses"] or ""),f"report du sous-détail : événement puis bordereau ; PU = prix de vente théorique {c['pv']} ; base = coût de revient {c['cr']} ; hypothèses signalées")
    # ===== 6. comparaison des scénarios =====
    ev("()=>{const id='fx-v6c',a=S.ao[id];return b31SaveDoc(id,a,{scenarios:{prudent:{pct:5},equilibre:{pct:-5},competitif:{pct:-25}},actif:'equilibre'},'scénarios test b31-6')}");pg.wait_for_timeout(200)
    ouvrir(pg,"fx-v6c");ev("()=>{bpX('fx-v6c').lock={'0-4':true};window.__DB.bpx['fx-v6c'].lock={'0-4':true};}");w0=W();pg.click('[data-b31-mode="pct"]');pg.click('[data-b31-cmpo="1"]');pg.wait_for_selector("[data-b31-cmp]")
    SC=ev("id=>b31Comparer(id,S.ao[id]).map(z=>({k:z.k,ok:z.pr&&z.pr.ok,m:z.m,why:z.pr&&z.pr.why,g:z.pr&&z.pr.g44&&z.pr.g44.bloque}))","fx-v6c")
    est=25000000;cib=[round(est*(10000+500)/10000),round(est*(10000-500)/10000),round(est*(10000-2500)/10000)]
    chk([z["ok"] for z in SC]==[True,True,True] and [z["m"]["cible_ttc"] for z in SC]==[f"{c//100}.{c%100:02d}" for c in cib],f"comparaison : 3 scénarios calculés sur les PU de la société, cibles {[c/100 for c in cib]}")
    chk(all(z["m"]["verrouillees"]==1 and z["m"]["cout_couverture"]=="6/6" and z["m"]["marge_ht"] is not None for z in SC),"chaque scénario : lignes verrouillées (1), couverture du coût 6/6, marge calculée (coût complet)")
    chk(SC[2]["g"] and SC[2]["m"]["art44"]=="bas" and not SC[0]["g"] and not SC[1]["g"],"scénario « Compétitif » −25 % en travaux : hors bornes art. 44 B → application bloquée (signalé), les autres dans les bornes")
    T=pg.inner_text("[data-b31-cmp]");chk("TTC obtenu après arrondis" in T and "Coût connu (couverture)" in T and "Marge (base : vente HT)" in T and "Hors bornes" in T and "Lignes verrouillées" in T,"tableau côte à côte : % demandé, TTC cible / obtenu, HT, TVA, coût connu, marge, art. 44, verrous")
    chk(W()==w0,"comparaison : aucune écriture (aperçus non destructifs)")
    pg.screenshot(path=f"{OUT}/fx_v6_comparaison.png")
    r=ev("id=>{const X=bpX(id),sv=X.sd['0-2'];delete X.sd['0-2'];const R=b31Comparer(id,S.ao[id]);X.sd['0-2']=sv;return R.map(z=>[z.m.cout_couverture,z.m.marge_ht])}","fx-v6c")
    chk(all(x[0]=="5/6" and x[1] is None for x in r),"coût partiel : marge des scénarios NON calculée (jamais estimée)")
    p0=ev("()=>JSON.stringify(window.__DB.bpx['fx-v6c'].p)");w0=W();pg.click('[data-b31-cmpfig]');pg.wait_for_timeout(400);e=ev("()=>Object.values(window.__DB.chiffrage_evenements).filter(e=>e.ao_id==='fx-v6c').pop()")
    chk(e["type"]=="comparaison" and len(e["contexte"]["scenarios"])==3 and e["contexte"]["scenarios"][2]["bloque44"] and e["hash"] and WS(w0)==[["set","chiffrage_evenements/fx-v6c~e1"]] and ev("()=>JSON.stringify(window.__DB.bpx['fx-v6c'].p)")==p0,"comparaison figée : un seul événement immuable avec les métriques des 3 scénarios ; prix inchangés")
    ev("()=>{B31.dlg=null;render();}");ouvrir(pg,"fx-v6c");pg.click('[data-b31-mode="pct"]');pg.click('[data-b31-cmpo="1"]');pg.wait_for_selector("[data-b31-cmp]")
    pg.click('[data-b31-cmpprev="equilibre"]');pg.wait_for_selector("[data-b31-prv]");t=pg.inner_text("[data-b31-prv]")
    chk("scénario « Équilibré »" in t and "Coût connu 6/6" in t,"« Prévisualiser ce scénario » : aperçu frais du scénario (coût et marge affichés)")
    w0=W();pg.click('[data-b31-appl="1"]');pg.wait_for_timeout(700);e=ev("()=>Object.values(window.__DB.chiffrage_evenements).filter(e=>e.ao_id==='fx-v6c').sort((x,y)=>x.seq-y.seq).pop()")
    chk(WS(w0)[:1]==[["set",f"chiffrage_evenements/fx-v6c~e{e['seq']}"]] and e["type"]=="objectif" and e["contexte"]["scenario"]=="Équilibré" and e["contexte"]["marge_ht"] is not None and e["contexte"]["cout_couverture"]=="6/6","application du scénario (après aperçu) : événement avec métriques (scénario, coût, marge) puis bordereau")
    # aperçu périmé si la TVA change ; garde art. 44 intacte en handler
    r=ev("""async id=>{const a=S.ao[id],X=bpX(id);B31.pct[id]='-5';B31.prev[id]=b31Previsu(id,a,-5);const n=window.__writes.length,t0=X.tva;X.tva=Object.assign({},t0,{taux:10});await b31Appliquer(id,a);X.tva=t0;
       const n1=window.__writes.length;const pr=b31Previsu(id,a,-30);pr.g44={bloque:false,raisons:[]};B31.pct[id]='-30';B31.prev[id]=pr;await b31Appliquer(id,a);return{tva:n1-n,g:window.__writes.length-n1,prev:B31.prev[id]&&B31.prev[id].g44&&B31.prev[id].g44.bloque}}""","fx-v6c")
    chk(r["tva"]==0 and r["g"]==0 and r["prev"],"aperçu périmé si la TVA change (rien n'est écrit) ; aperçu falsifié hors bornes (−30 %) : garde b31-5 recalculée dans le gestionnaire, rien n'est écrit")
    vv=ev("async id=>{const a=S.ao[id];B31.vers[id]=[];const v=await b31Version(id,a,'b31-6');return v}","fx-v6c")
    chk(vv["tva"]["etat"]=="confirme" and vv["couts"]["couverture"]=="6/6" and vv["couts"]["marge"] and len(vv["scenarios"])==3 and vv["dernier_evenement"] and vv["hash"],"brouillon immuable : TVA documentée, coûts / marge, métriques des scénarios et dernier événement inclus dans l'empreinte")
    # ===== 7. isolement : événements d'une autre société ignorés ; dossier réel sans historique =====
    ev("()=>{window.__DB.chiffrage_evenements['fx-v6c~e99']={ao_id:'fx-v6c',soc:'alwaad-ataib',seq:99,type:'manuel',label:'intrus'};}")
    ev("async()=>{await b31ChargerEv('fx-v6c');}");r=ev("id=>{return{n:b31EvSoc(id,S.ao[id]).filter(e=>e.seq===99).length,h:b31EvHtml(id,S.ao[id])}}","fx-v6c")
    chk(r["n"]==0 and "autre société ignoré" in r["h"],"événement rattaché à une autre société : ignoré et signalé")
    w0=W();ouvrir(pg,ALW);pg.click("[data-b31-hist]");pg.wait_for_selector("[data-b31-ev0]");h=pg.inner_text("[data-b31-ev0]")
    chk("Aucun événement de prix" in h and ("aucun passé n'est reconstitué" in h or "aucun PU" in h) and W()==w0,f"dossier réel ALWAAD : aucun événement inventé ni passé reconstitué (« {h[:110]}… »), aucune écriture")
    pg.click(".b31-dlg .fsx");t=pg.inner_text("[data-b31-tva]");chk("Non renseignée" in t or "non renseignée" in t,"dossier réel ALWAAD : TVA « non renseignée », aucun taux supposé")
    chk(not errs,f"1440 : aucune erreur JavaScript {errs[:3]}")
    reel1=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    o0,o1=json.loads(reel0),json.loads(reel1);vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x
    o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    chk(o0==o1 and not ecr_reel(pg),f"dossiers réels : offres, PU, décisions strictement inchangés ; aucune écriture {ecr_reel(pg)[:2]}")
    ctx.close()
    # ===== 8. mobile 390 clair et sombre =====
    for (w,hh,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre"),(1440,900,"dark","sombre")):
        ctx,pg,errs=demarrer(b,w,hh,sch);ev=lambda js,*a:pg.evaluate(js,*a)
        ev("async()=>{const id='fx-v6c',a=S.ao[id];await b31SaveDoc(id,a,{scenarios:{prudent:{pct:5},equilibre:{pct:-5},competitif:{pct:-25}}},'scénarios test b31-6');}")
        ouvrir(pg,"fx-v6c");pg.wait_for_timeout(300)
        ov=pg.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth");chk(ov<=1,f"{tag} : aucun défilement horizontal, carte TVA et récapitulatif ({ov} px)")
        pg.locator("[data-b31-tva]").scroll_into_view_if_needed();pg.screenshot(path=f"{OUT}/fx_v6_tva_{tag}.png")
        pg.click('[data-b31-sd="0-0"]');pg.click('[data-b31-sdopen="0-0"]');pg.wait_for_selector(".b31-sdp");pg.wait_for_timeout(200)
        ov=pg.evaluate("()=>{const p=document.querySelector('.b31-sdp');return Math.max(document.documentElement.scrollWidth-document.documentElement.clientWidth,p.scrollWidth-p.clientWidth)}")
        chk(ov<=1,f"{tag} : panneau sous-détail sans débordement horizontal ({ov} px)");pg.screenshot(path=f"{OUT}/fx_v6_sousdetail_{tag}.png");pg.click(".b31-sdp .fsx")
        pg.click('[data-b31-mode="pct"]');pg.click('[data-b31-cmpo="1"]');pg.wait_for_selector("[data-b31-cmp]");pg.wait_for_timeout(200)
        ov=pg.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth");chk(ov<=1,f"{tag} : comparaison des scénarios lisible (tableau défilant dans son cadre, page sans débordement : {ov} px)")
        pg.screenshot(path=f"{OUT}/fx_v6_comparaison_{tag}.png")
        chk(not errs,f"{tag} : aucune erreur JavaScript {errs[:2]}");ctx.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump([x for x in R],open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
