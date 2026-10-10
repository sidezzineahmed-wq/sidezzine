"""Recette b31-4 · Objectif en % sur bordereau vide, partiel ou complet (proposition justifiée puis ajustement, aperçu, application).
Base simulée locale (harnais de qa_b31.py) + dossiers FICTIFS « fx-p* » ; Claude simulé (S.sample remplacé par un faux
déterministe). Écritures seulement sur les dossiers fictifs ; les dossiers réels sont lus, jamais écrits."""
import os,sys,json
ICI0=os.path.dirname(os.path.abspath(__file__))
M=json.load(open(os.path.join(ICI0,"srv","mockdb_b31.json"),encoding="utf-8"))
P0={"org":"fx","ref":"FXP","url":""}
def ao(ref,est,soc="sakdat",**k):
    a={"ref":ref,"categorie":"Travaux","obj":"Construction fictive d'un bloc sanitaire (test)","est":est,"soc":soc,"statut":"En préparation","mo":"MAÎTRE D'OUVRAGE FICTIF","lim":"2026-12-15",
       "portail":dict(P0,ref=ref),"exig":{"estimation":est,"estimationSource":"FICTIF (test)","delai":"4 mois (fictif)"},"lieux":["LAAYOUNE"],"decision":{"verdict":"Go","le":"2026-10-01","qui":"u_qa","soc":soc}}
    a.update(k);return a
L6=[{"n":"1","d":"Béton armé pour semelles, dosé à 350 kg/m3","u":"m³","q":25,"s":"A. Gros œuvre"},
    {"n":"2","d":"Revêtement de sol en carreaux de grès cérame","u":"m²","q":140,"s":"B. Revêtements"},
    {"n":"3","d":"Porte isoplane en bois, y compris quincaillerie","u":"U","q":6,"s":"C. Menuiserie"},
    {"n":"4","d":"Conduite PVC DN 110 pour évacuation","u":"ml","q":300,"s":"D. Plomberie"},
    {"n":"5","d":"Installation de chantier et repli","u":"ENS","q":1,"s":"A. Gros œuvre"},
    {"n":"6","d":"Acier HA pour béton armé","u":"kg","q":2400,"s":"A. Gros œuvre"}]
for k in ("fx-pvide","fx-ppart","fx-pcomp","fx-plock","fx-pq"):M["ao"][k]=ao(k.upper(),1200000)
M["ao"]["fx-pref"]=ao("FX-PREF",500000)                      # même société : référence interne (béton m³)
M["ao"]["fx-pautre"]=ao("FX-PAUTRE",500000,soc="alwaad-ataib")  # autre société : ses prix ne doivent JAMAIS servir
def tag(suf,keep=()):
    L=json.loads(json.dumps(L6))
    for i,x in enumerate(L):
        if i not in keep:x["d"]+=suf
    return L
for k in ("fx-pvide","fx-pref","fx-pautre"):M["bp"][k]={"lots":[{"lignes":tag("",range(6))}],"cadre":False,"alertes":[]}
M["bp"]["fx-ppart"]={"lots":[{"lignes":tag(" (lot partiel)",(0,))}],"cadre":False,"alertes":[]}
for k in ("fx-pcomp","fx-plock"):M["bp"][k]={"lots":[{"lignes":tag(" (lot complet)")}],"cadre":False,"alertes":[]}
M["bp"]["fx-pq"]={"lots":[{"lignes":json.loads(json.dumps(L6[:3]))+[{"n":"4","d":"Ligne fictive à quantité illisible","u":"ml","q":None,"s":"D. Plomberie"}]}],"cadre":False,"alertes":[]}
M["bpx"]["fx-ppart"]={"p":{"0-1":200,"0-2":3200,"0-4":30000},"q":{},"soc":"sakdat"}
M["bpx"]["fx-pcomp"]={"p":{"0-0":1600,"0-1":210,"0-2":3400,"0-3":170,"0-4":28000,"0-5":13.5},"q":{},"soc":"sakdat"}
M["bpx"]["fx-plock"]={"p":{"0-0":1600,"0-1":210,"0-2":3400,"0-3":170,"0-4":28000,"0-5":13.5},"q":{},"soc":"sakdat","lock":{"0-4":True}}
M["bpx"]["fx-pref"]={"p":{"0-0":1550},"q":{},"soc":"sakdat","t":1790000000000}
M["bpx"]["fx-pautre"]={"p":{"0-0":999,"0-1":999.99,"0-2":999,"0-3":999,"0-4":999,"0-5":999},"q":{},"soc":"alwaad-ataib"}
json.dump(M,open(os.path.join(ICI0,"srv","mockdb_b31_pct.json"),"w",encoding="utf-8"),ensure_ascii=False)
src=open(os.path.join(ICI0,"qa_b31.py"),encoding="utf-8").read().replace("mockdb_b31.json","mockdb_b31_pct.json").replace('OUT=os.path.join(ICI,"qa_b31")','OUT=os.path.join(ICI,"qa_b31_pct")')
exec(src.split("with sync_playwright() as p:")[0])
FX=["fx-pvide","fx-ppart","fx-pcomp","fx-plock","fx-pref","fx-pautre","fx-pq"]
# faux Claude déterministe : PU par nature d'unité (structure hétérogène), justification et confiance ; trace des invites
STUB="""(mode)=>{window.__prompts=[];const U={"m³":1500,"m²":220,"U":3500,"ml":180,"ENS":25000,"kg":14};
  S.sample=mode==="absent"?null:{json:async(pr,opt)=>{window.__prompts.push(pr);if(mode==="echec")throw{code:"rate_limited"};if(mode==="illisible")return"pas du JSON";
    const L=pr.split("LIGNES :\\n")[1].split("\\n").filter(Boolean).map(l=>JSON.parse(l));
    return{lignes:L.map(z=>({k:z.k,pu:mode==="trou"&&z.n==="4"?null:U[z.unite]||null,inclut:"fourniture et pose",justification:"Hypothèse pour "+z.unite+" ("+z.quantite+") : "+z.designation.slice(0,30),confiance:z.unite==="ENS"?"basse":"moyenne"}))};}};}"""
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    W=lambda:len(ev("()=>window.__writes"))
    # ===== 1. saisie du pourcentage =====
    P=ev("()=>['+5','-10','7,25','0','-0','−12,5 %','-99,99','-100','-150','abc','5..2','',' 1000'].map(t=>[b31ParsePct(t),b31PctErr(t)])")
    chk([x[0] for x in P]==[5,-10,7.25,0,0,-12.5,-99.99,None,None,None,None,None,1000],f"pourcentages acceptés (hausse, baisse, décimal, zéro) / refusés : {[x[0] for x in P]}")
    chk("cible TTC nulle ou négative" in P[7][1] and "cible TTC nulle ou négative" in P[8][1] and "non reconnu" in P[9][1] and P[11][1] is None,"refus explicites : −100 % et moins (cible ≤ 0), valeur non numérique ; champ vide sans message")
    r=ev("()=>[b31Cible(120000000,7.25),b31Cible(120000000,0),b31Cible(120000000,5),b31Cible(120000000,-10)]")
    chk(r==[128700000,120000000,126000000,108000000],f"cibles TTC exactes : +7,25 % {r[0]/100:.2f} · 0 % {r[1]/100:.2f} · +5 % {r[2]/100:.2f} · −10 % {r[3]/100:.2f}")
    # ===== 2. bordereau vide, IA absente : aucun arbitraire, rien d'écrit =====
    ev(STUB,"absent");w0=W()
    pr=ev("()=>{const r=b31Previsu('fx-pvide',S.ao['fx-pvide'],5);return{ok:r.ok,k:r.k,why:r.why,m:r.manque}}")
    chk(not pr["ok"] and pr["k"]=="base" and "aucune répartition arbitraire" in pr["why"] and len(pr["m"])==5,f"vide sans IA : aperçu refusé, 5 lignes sans base (la 6e a une référence interne) — « {pr['why'][:100]}… »")
    bs=ev("()=>b31Bases('fx-pvide',S.ao['fx-pvide']).map(z=>[z.r.k,z.m||null,z.pu,z.lab||''])")
    chk(bs[0][1]=="ref" and bs[0][2]==1550 and "FX-PREF" in bs[0][3],f"référence interne de la MÊME société utilisée pour le béton m³ : {bs[0]}")
    chk(all(z[2]!=999 and z[2]!=999.99 for z in bs),"FIN-ISO-001 : aucun prix du dossier d'une autre société (ALWAAD fictif, 999 DH) n'est repris")
    ouvrir(pg,"fx-pvide");pg.click('[data-b31-mode="pct"]');pg.fill('[data-b31-pct="fx-pvide"]',"+5");pg.wait_for_timeout(500)
    t=pg.inner_text(".b31-sim");chk("Proposition IA indisponible" in t and "Aucune répartition arbitraire" in t,"interface : IA indisponible annoncée, pas de répartition inventée")
    pg.click('[data-b31-prev]');pg.wait_for_selector('[data-b31-need="base"]');pg.screenshot(path=f"{OUT}/vide_sans_ia.png",full_page=False)
    chk(W()==w0,"vide sans IA : aucune écriture")
    # ===== 3. échec et réponse illisible de l'IA =====
    ev(STUB,"echec");ev("()=>b31ProposerIA('fx-pvide',S.ao['fx-pvide'])");pg.wait_for_timeout(300)
    r=ev("()=>({e:B31.propErr['fx-pvide'],p:!!B31.propIA['fx-pvide']})")
    chk(r["e"]["k"]=="echec" and "trop de demandes" in r["e"]["t"] and not r["p"],f"IA en échec : message clair, aucune proposition — « {r['e']['t'][:90]}… »")
    ev(STUB,"illisible");ev("()=>b31ProposerIA('fx-pvide',S.ao['fx-pvide'])");pg.wait_for_timeout(300)
    r=ev("()=>({e:B31.propErr['fx-pvide'],p:!!B31.propIA['fx-pvide']})")
    chk(r["e"]["k"]=="echec" and "illisible" in r["e"]["t"] and not r["p"],"IA : réponse illisible → échec explicite, aucune proposition")
    chk(W()==w0,"échecs IA : aucune écriture")
    # ===== 4. vide : proposition IA justifiée puis ajustement à la cible (+5 %) =====
    ev(STUB,"ok");ev("()=>b31ProposerIA('fx-pvide',S.ao['fx-pvide'])");pg.wait_for_timeout(300)
    r=ev("()=>{const P=B31.propIA['fx-pvide'];return{n:P.n,nn:P.nn,soc:P.soc,ks:Object.keys(P.L).sort(),pr:window.__prompts.join('\\n')}}")
    chk(r["n"]==5 and r["nn"]==0 and r["soc"]=="sakdat" and r["ks"]==["0-1","0-2","0-3","0-4","0-5"],f"proposition IA : 5 PU (lignes sans base seulement), société SAKDAT : {r['ks']}")
    chk("999" not in r["pr"] and "ALWAAD" not in r["pr"].upper() and "FX-PREF" in r["pr"] and "désignation" in r["pr"].lower() or "designation" in r["pr"],"invite : désignations, unités, quantités, références de la même société ; aucun prix ni nom d'une autre société")
    chk("AUCUNE base de prix, mercuriale" in r["pr"],"invite : aucune mercuriale prétendue, hypothèses déclarées")
    chk(W()==w0,"proposition IA : aucune écriture (ni bordereau, ni chiffrage, ni journal)")
    pr=ev("""()=>{const r=b31Previsu('fx-pvide',S.ao['fx-pvide'],5);return{ok:r.ok,cible:r.cibleC,ttc:r.T&&r.T.ttcC,reste:r.resteC,nIA:r.nIA,nRef:r.nRef,
      rows:r.rows.map(z=>[z.k,z.m,z.base,z.apres,z.conf,z.just]),f:r.f}}""")
    chk(pr["ok"] and pr["cible"]==126000000 and abs(pr["reste"])<=600,f"+5 % sur bordereau vide : cible {pr['cible']/100:.2f} TTC, obtenu {pr['ttc']/100:.2f}, écart d'arrondi {pr['reste']/100:+.2f} DH")
    ratios=[round(z[3]/z[2],6) for z in pr["rows"]]
    chk(len(set(round(x,3) for x in ratios))==1 and len(set(z[3] for z in pr["rows"]))==6,f"structure conservée (même coefficient {ratios[0]} sur toutes les bases), PU hétérogènes selon la nature — pas de répartition égale : {[z[3] for z in pr['rows']]}")
    chk(pr["nIA"]==5 and pr["nRef"]==1 and all(z[5] for z in pr["rows"]) and all(z[4] in ("haute","moyenne","basse") for z in pr["rows"]),"chaque PU proposé porte sa source, sa justification et sa confiance")
    chk(W()==w0,"aperçu : aucune écriture")
    pg.fill('[data-b31-pct="fx-pvide"]',"+5");pg.wait_for_timeout(500);pg.click('[data-b31-prev]');pg.wait_for_selector("[data-b31-prv]")
    t=pg.inner_text("[data-b31-prv]");chk("Proposition IA / hypothèses à vérifier" in t and "TTC cible" in t and "TTC obtenu" in t and "écart d'arrondi" in t and "à confirmer" in t,"interface : bandeau « Proposition IA / hypothèses à vérifier », TTC cible / obtenu, arrondi, TVA à confirmer")
    pg.click('[data-b31-just] summary');pg.wait_for_timeout(200);pg.screenshot(path=f"{OUT}/vide_apercu_plus5.png",full_page=True)
    chk(pg.locator("[data-b31-jk]").count()==6,"interface : justification ligne par ligne (6)")
    chk(W()==w0,"aucune écriture avant « Appliquer »")
    pg.click('[data-b31-appl]');pg.wait_for_timeout(600)
    ap=ev("()=>{const X=bpX('fx-pvide');return{p:X.p,src:X.srcL,w:window.__writes.slice(),db:window.__DB.bpx['fx-pvide'],pv:S.ao['fx-pvide'].prixValide||null,dec:S.ao['fx-pvide'].decision,st:S.ao['fx-pvide'].statut}}")
    ww=[w for w in ap["w"][w0:]]
    chk(ww==[["set","bpx/fx-pvide"]],f"appliquer : une seule écriture, le bordereau du dossier fictif : {ww}")
    chk(len(ap["p"])==6 and all(ap["src"][k]["m"]=="pct" and ap["src"][k]["base"] in ("ia","ref") for k in ap["p"]) and ap["db"]["meta"]["baseCout"].startswith("HYPOTHÈSE"),"PU enregistrés avec leur origine (objectif %, base IA / référence) ; base de coût « HYPOTHÈSE »")
    chk(ap["pv"] is None and ap["dec"]["verdict"]=="Go" and ap["st"]=="En préparation","rien n'est validé : pas de prix validé, décision et statut inchangés (brouillon)")
    st=ev("()=>{const a=S.ao['fx-pvide'],E=b31Etat('fx-pvide',a);return[E.statut.k,E.complet,E.T.ttcC]}")
    chk(st[0]=="brouillon" and st[1],f"statut après application : {st[0]}, offre complète {st[2]/100:.2f} TTC (brouillon)")
    # ===== 5. partiel −10 % : PU saisis gardés comme base, manques proposés =====
    ev(STUB,"ok");w0=W()
    pr=ev("()=>{const r=b31Previsu('fx-ppart',S.ao['fx-ppart'],-10);return{ok:r.ok,k:r.k,m:r.manque}}")
    chk(not pr["ok"] and pr["k"]=="base" and pr["m"]==["4","6"],f"partiel sans proposition : 2 lignes sans base indiquées ({pr['m']}) — béton couvert par la référence interne")
    ev("()=>b31ProposerIA('fx-ppart',S.ao['fx-ppart'])");pg.wait_for_timeout(300)
    pr=ev("()=>{const r=b31Previsu('fx-ppart',S.ao['fx-ppart'],-10);return{ok:r.ok,cible:r.cibleC,ttc:r.T.ttcC,rows:r.rows.map(z=>[z.k,z.m,z.base,z.apres]),nEx:r.nEx,nIA:r.nIA}}")
    chk(pr["ok"] and pr["cible"]==108000000 and pr["nEx"]==3 and pr["nIA"]==2 and abs(pr["ttc"]-pr["cible"])<=600,f"−10 % sur partiel : 3 PU saisis + 1 référence + 2 IA, obtenu {pr['ttc']/100:.2f} / cible {pr['cible']/100:.2f}")
    ev("()=>{B31.pct['fx-ppart']='-10';B31.prev['fx-ppart']=b31Previsu('fx-ppart',S.ao['fx-ppart'],-10);b31Appliquer('fx-ppart',S.ao['fx-ppart']);}");pg.wait_for_timeout(300)
    ap=ev("()=>{const X=bpX('fx-ppart');return{src:X.srcL,w:window.__writes.slice()}}")
    chk([w for w in ap["w"][w0:]]==[["set","bpx/fx-ppart"]] and ap["src"]["0-1"]["base"]=="existant" and ap["src"]["0-3"]["base"]=="ia","partiel appliqué : PU saisis ajustés (base « existant »), PU manquants remplis (base « ia »)")
    # ===== 6. complet : comportement d'ajustement inchangé (+5 et −10), aucune proposition =====
    TOL=round(sum(x["q"] for x in L6)*0.5*1.2)+2  # borne théorique de l'arrondi des PU au centime : Σ qté × 0,005 DH × 1,2
    for pc,cb in ((5,126000000),(-10,108000000)):
        r=ev("p=>{const r=b31Previsu('fx-pcomp',S.ao['fx-pcomp'],p),X=bpX('fx-pcomp');return{ok:r.ok,c:r.cibleC,t:r.T.ttcC,nProp:r.nProp,ratio:r.rows.map(z=>z.apres/X.p[z.k])}}",pc)
        chk(r["ok"] and r["c"]==cb and r["nProp"]==0 and max(r["ratio"])-min(r["ratio"])<0.001 and abs(r["t"]-cb)<=TOL,f"complet {pc:+d} % : ajustement proportionnel seul (aucune proposition), obtenu {r['t']/100:.2f} / cible {cb/100:.2f} (écart dans la borne d'arrondi {TOL/100:.2f} DH)")
    r=ev("()=>[7.25,0].map(p=>{const r=b31Previsu('fx-pcomp',S.ao['fx-pcomp'],p);return[r.ok,r.cibleC,r.T.ttcC]})")
    chk(r[0][0] and r[0][1]==128700000 and r[1][0] and r[1][1]==120000000,f"décimal +7,25 % → cible {r[0][1]/100:.2f} (obtenu {r[0][2]/100:.2f}) ; 0 % → cible = estimation {r[1][1]/100:.2f} (obtenu {r[1][2]/100:.2f})")
    # ===== 7. verrous : conservés ; objectif inatteignable =====
    r=ev("()=>{const id='fx-plock',X=bpX(id),r=b31Previsu(id,S.ao[id],-10);return{ok:r.ok,keys:r.rows.map(z=>z.k),P4:r.P['0-4'],lockN:r.lockN}}")
    chk(r["ok"] and "0-4" not in r["keys"] and r["P4"]==28000 and r["lockN"]==1,"ligne verrouillée : prix et source conservés, hors ajustement")
    r=ev("()=>{const id='fx-plock',X=bpX(id),sv=X.p['0-4'];X.p['0-4']=2000000;const r=b31Previsu(id,S.ao[id],-10);X.p['0-4']=sv;return{ok:r.ok,k:r.k,why:r.why}}")
    chk(not r["ok"] and r["k"]=="inatteignable" and "totalisent déjà" in r["why"],f"verrouillées > cible : objectif inatteignable annoncé — « {r['why'][:110]}… »")
    # ===== 8. invalidation de l'aperçu =====
    w0=W()
    r=ev("""()=>{const id='fx-pcomp',a=S.ao[id],X=bpX(id),out={};B31.pct[id]='-10';
      B31.prev[id]=b31Previsu(id,a,-10);X.p['0-0']=1601;b31Appliquer(id,a);out.data=!!B31.prev[id];X.p['0-0']=1600;
      B31.prev[id]=b31Previsu(id,a,-10);X.q['0-3']=301;b31Appliquer(id,a);out.qte=!!B31.prev[id];delete X.q['0-3'];
      B31.prev[id]=b31Previsu(id,a,-10);B31.pct[id]='-12';b31Appliquer(id,a);out.pct=!!B31.prev[id];B31.pct[id]='-10';
      B31.prev[id]=b31Previsu(id,a,-10);a.soc='siditrav';b31Appliquer(id,a);out.soc=!!B31.prev[id];a.soc='sakdat';
      B31.prev[id]=b31Previsu(id,a,-10);X.lock={'0-1':true};b31Appliquer(id,a);out.lock=!!B31.prev[id];X.lock={};
      out.p=X.p['0-0'];return out}""")
    chk(not any([r["data"],r["qte"],r["pct"],r["soc"],r["lock"]]) and r["p"]==1600 and W()==w0,"aperçu invalidé (rien appliqué, aucune écriture) si PU, quantité, pourcentage, société ou verrou changent avant « Appliquer »")
    r=ev("""()=>{const id='fx-pvide',a=S.ao[id];const P=b31PropIA(id,a);a.soc='siditrav';const Q=b31PropIA(id,a);a.soc='sakdat';return[!!P,!!Q]}""")
    chk(r==[True,False],"changement de société : la proposition IA de la société précédente n'est plus utilisée")
    ouvrir(pg,"fx-pcomp");pg.click('[data-b31-mode="pct"]');pg.fill('[data-b31-pct="fx-pcomp"]',"-10");pg.wait_for_timeout(500);pg.click('[data-b31-prev]');pg.wait_for_selector("[data-b31-prv]")
    ev("()=>{bpX('fx-pcomp').p['0-0']=1599;render();}");pg.wait_for_timeout(300)
    chk(pg.locator('[data-b31-perime]').count()==1 and pg.locator('[data-b31-appl]').count()==0,"interface : aperçu périmé signalé, bouton « Appliquer » retiré")
    ev("()=>{bpX('fx-pcomp').p['0-0']=1600;delete B31.prev['fx-pcomp'];render();}")
    # ===== 9. quantité illisible : obstacle affiché, rien d'inventé =====
    r=ev("()=>{const r=b31Previsu('fx-pq',S.ao['fx-pq'],5);return{ok:r.ok,k:r.k,why:r.why,m:r.manque}}")
    chk(not r["ok"] and r["k"]=="quantite" and r["m"]==["4"] and "n'invente aucune quantité" in r["why"],"quantité illisible : obstacle explicite, ligne indiquée, aucune quantité inventée")
    # ===== 10. proposition partielle de l'IA (une ligne sans estimation) =====
    ev("()=>{delete B31.propIA['fx-pq'];}");ev(STUB,"trou")
    ev("()=>{S.ao['fx-ppart2']=JSON.parse(JSON.stringify(S.ao['fx-pvide']));S.ao['fx-ppart2'].ref='FX-PPART2';S.bp['fx-ppart2']=S.bp['fx-pvide'];S.ao['fx-ppart2'].soc='riyada-build';S.bpx['fx-ppart2']={p:{},q:{},soc:'riyada-build'};}")
    ev("()=>b31ProposerIA('fx-ppart2',S.ao['fx-ppart2'])");pg.wait_for_timeout(300)
    r=ev("()=>{const r=b31Previsu('fx-ppart2',S.ao['fx-ppart2'],5);return{ok:r.ok,why:r.why,m:r.manque,e:B31.propErr['fx-ppart2']}}")
    chk(not r["ok"] and r["m"]==["4"] and r["e"]["k"]=="partiel" and "sans estimation de l'IA" in r["why"],"IA partielle : la ligne sans estimation reste à saisir ; aperçu refusé, rien d'arbitraire")
    # ===== 11. dossier réel ALWAAD (lecture seule) : base incomplète annoncée, aucune écriture =====
    w0=W();r=ev("id=>{const a=S.ao[id],B=b31Bases(id,a),st=b31BaseStat(B),R=b31Refs(id,a),own=Object.values(R).flat().every(x=>S.ao[x.oid].soc===a.soc&&S.bpx[x.oid].soc===a.soc);const r=b31Previsu(id,a,-10);return{st,ok:r.ok,k:r.k,own,soc:a.soc}}",ALW)
    chk(not r["ok"] and r["k"] in ("base","quantite") and r["own"] and W()==w0,f"réel ALWAAD (lecture) : aperçu {r['k']} annoncé, bases {r['st']}, références internes toutes de {r['soc']}, aucune écriture")
    ouvrir(pg,ALW);pg.click('[data-b31-mode="pct"]');pg.fill(f'[data-b31-pct="{ALW}"]',"+5");pg.wait_for_timeout(500);pg.screenshot(path=f"{OUT}/alwaad_pct_lecture.png");chk(W()==w0,"réel ALWAAD : interface ouverte en mode %, aucune écriture")
    # ===== 12. mobile et sombre =====
    ctx2,pg2,errs2=demarrer(b,390,844,"dark")
    pg2.evaluate(STUB,"ok");pg2.evaluate("()=>{S.ao['fx-ppart2']=JSON.parse(JSON.stringify(S.ao['fx-pvide']));S.ao['fx-ppart2'].ref='FX-PPART2';S.ao['fx-ppart2'].soc='riyada-build';S.bp['fx-ppart2']=S.bp['fx-pvide'];S.bpx['fx-ppart2']={p:{},q:{},soc:'riyada-build'};}")
    ouvrir(pg2,"fx-ppart2");pg2.click('[data-b31-mode="pct"]');pg2.fill('[data-b31-pct="fx-ppart2"]',"-10");pg2.wait_for_timeout(400)
    pg2.click('[data-b31-propia]');pg2.wait_for_timeout(500);pg2.click('[data-b31-prev]');pg2.wait_for_selector("[data-b31-prv]");pg2.wait_for_timeout(200)
    ov=pg2.evaluate("()=>document.documentElement.scrollWidth-window.innerWidth");pg2.locator(".b31-sim").screenshot(path=f"{OUT}/mobile_sombre_apercu.png")
    chk(ov<=1,f"mobile 390 px sombre : aucun débordement horizontal ({ov}px)")
    # ===== bilan =====
    reel1=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x  # bpX() initialise en mémoire un objet vide (comportement existant, jamais écrit)
    o0,o1=json.loads(reel0),json.loads(reel1);o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    chk(o0==o1 and not ecr_reel(pg) and not ecr_reel(pg2),"données réelles (BG, SIDITRAV, ALWAAD, SAP) : offres, PU, décisions et prix validés inchangés ; aucune écriture réelle")
    chk(not errs and not errs2,f"aucune erreur JavaScript ({errs+errs2})")
    b.close()
n=sum(1 for x in R if x.startswith("OK"));print(f"\n{n}/{len(R)} OK");json.dump(R,open(os.path.join(OUT,"resultats.json"),"w"),ensure_ascii=False,indent=1)
