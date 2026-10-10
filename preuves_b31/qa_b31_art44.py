"""Recette b31-5 · seuils de l'art. 44 B bloquants (objectif en % et validation du chiffrage).
Dossiers FICTIFS seulement (fixtures de qa_b31_pct.py) ; dossiers réels lus, jamais écrits ; aucune application ni validation réelle."""
import os,json
ICI0=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(ICI0,"qa_b31_pct.py"),encoding="utf-8").read().replace('OUT=os.path.join(ICI,"qa_b31_pct")','OUT=os.path.join(ICI,"qa_b31_art44")')
exec(src.split("\nwith sync_playwright() as p:")[0])
CLONE="""([src,dst,cat,obj])=>{const a=JSON.parse(JSON.stringify(S.ao[src]));a.ref=dst.toUpperCase();if(cat!=null)a.categorie=cat;if(obj)a.obj=obj;S.ao[dst]=a;
  S.bp[dst]=JSON.parse(JSON.stringify(S.bp[src]));S.bpx[dst]=JSON.parse(JSON.stringify(S.bpx[src]));S.bpx[dst].lock={};return true}"""
PV="""([id,p])=>{const r=b31Previsu(id,S.ao[id],p);return{ok:r.ok,why:r.why||null,c:r.cibleC,t:r.T&&r.T.ttcC,b:r.g44&&r.g44.bloque,R:r.g44?r.g44.raisons:[],v:r.g44?r.g44.verifier:null,A:r.A44&&r.A44.k}}"""
AP="""async([id,p])=>{const a=S.ao[id],X=bpX(id),p0=JSON.stringify(X.p),n=window.__writes.length;B31.pct[id]=String(p);B31.prev[id]=b31Previsu(id,a,p);b31Appliquer(id,a);await new Promise(r=>setTimeout(r,300));
  return{w:window.__writes.slice(n),same:JSON.stringify(X.p)===p0,toast:(document.querySelector('.toast')||{}).textContent||''}}"""
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    W=lambda:len(ev("()=>window.__writes"))
    for d in (["fx-pcomp","fx-t1","Travaux",None],["fx-pcomp","fx-t2","Travaux",None],["fx-pcomp","fx-f1","Fournitures",None],["fx-pcomp","fx-s1","Services","Fourniture de services de transport (test)"],
              ["fx-pcomp","fx-e1","Services","Études techniques et maîtrise d'œuvre (test)"],["fx-pcomp","fx-i1","",None],["fx-pcomp","fx-v1","Travaux",None]):ev(CLONE,d)
    # ===== 1. bornes exactes et juste au-delà (travaux −20 % / +20 %) =====
    r={x:ev(PV,["fx-t1",x]) for x in (-20,-20.01,20,20.01)}
    chk(r[-20]["c"]==96000000 and r[20]["c"]==144000000,"cibles aux bornes : −20 % = 960 000,00 · +20 % = 1 440 000,00 TTC (estimation 1 200 000)")
    chk(r[-20.01]["b"] and r[20.01]["b"] and any("Cible demandée" in t and "−20 %" in t and "dépassement" in t for t in r[-20.01]["R"]) and any("Cible demandée" in t and "+20 %" in t and "excessive" in t for t in r[20.01]["R"]),
        f"travaux −20,01 % et +20,01 % : bloqués, raison, seuil et dépassement — « {r[-20.01]['R'][0][:150]}… »")
    chk(r[-20.01]["ok"] and r[20.01]["ok"],"aperçu hors bornes conservé pour simulation (ok), mais marqué bloqué")
    cib=lambda R:not any(t.startswith("Cible demandée") for t in R)
    chk(cib(r[-20]["R"]) and cib(r[20]["R"]),f"exactement −20 % et +20 % : la cible elle-même n'est pas bloquée (bornes incluses) ; TTC obtenu {r[-20]['t']/100:.2f} / {r[20]['t']/100:.2f} contrôlé séparément")
    # ===== 2. fournitures et services hors études : −25 % / +20 % =====
    f={x:ev(PV,["fx-f1",x]) for x in (-25,-25.01,20.01)};sv=ev(PV,["fx-s1",-25.01])
    chk(cib(f[-25]["R"]) and f[-25.01]["b"] and any("−25 %" in t for t in f[-25.01]["R"]) and f[20.01]["b"] and sv["b"],"fournitures / services : −25 % = borne incluse ; −25,01 % et +20,01 % bloqués")
    t2=ev(PV,["fx-t1",-22]);f2=ev(PV,["fx-f1",-22])
    chk(t2["b"] and any(t.startswith("Cible demandée") for t in t2["R"]) and cib(f2["R"]),"−22 % : cible bloquée en travaux (borne −20 %), cible admise en fournitures (borne −25 %)")
    # ===== 3. études et catégorie inconnue : « à vérifier », aucun seuil inventé =====
    e=ev(PV,["fx-e1",-40]);i=ev(PV,["fx-i1",35])
    chk(not e["b"] and e["v"] and "aucun seuil inventé" in e["v"] and not i["b"] and i["v"],f"études −40 % et catégorie inconnue +35 % : non bloqués, « à vérifier » — « {e['v'][:90]}… »")
    # ===== 4. arrondi qui fait franchir le seuil (cible dans les bornes, TTC obtenu dehors) =====
    trouve=ev("""()=>{const out=[];for(const id of ['fx-t1','fx-f1']){const bas=id==='fx-f1'?-25:-20;
        for(let i=0;i<=60;i++){const p=Math.round((bas+i*0.001)*1000)/1000,q=+p.toFixed(2);const r=b31Previsu(id,S.ao[id],q);if(r.ok&&r.g44.bloque&&r.g44.raisons.every(t=>t.startsWith('TTC obtenu')))out.push([id,q,r.cibleC,r.T.ttcC,r.g44.raisons[0]]);}
        for(let i=0;i<=60;i++){const q=+(20-i*0.001).toFixed(2);const r=b31Previsu(id,S.ao[id],q);if(r.ok&&r.g44.bloque&&r.g44.raisons.every(t=>t.startsWith('TTC obtenu')))out.push([id,q,r.cibleC,r.T.ttcC,r.g44.raisons[0]]);}}
      return out}""")
    if not trouve:
        # construction déterministe : PU d'une ligne de grande quantité rendant l'arrondi défavorable à la borne exacte
        trouve=ev("""()=>{const out=[],id='fx-t2',X=bpX(id);for(let c=0;c<400&&!out.length;c++){X.p['0-5']=13.5+c*0.0137;for(const q of [-20,20]){const r=b31Previsu(id,S.ao[id],q);
          if(r.ok&&r.g44.bloque&&r.g44.raisons.every(t=>t.startsWith('TTC obtenu')))out.push([id,q,r.cibleC,r.T.ttcC,r.g44.raisons[0]]);}}return out}""")
    chk(bool(trouve),f"arrondi franchissant le seuil : cible dans les bornes mais TTC obtenu dehors → bloqué ({trouve[0][0]} {trouve[0][1]:+} % : cible {trouve[0][2]/100:.2f}, obtenu {trouve[0][3]/100:.2f}) — « {trouve[0][4][:120]}… »" if trouve else "arrondi franchissant le seuil : aucun cas construit")
    if trouve:
        id0,q0=trouve[0][0],trouve[0][1];w0=W();a=ev(AP,[id0,q0])
        chk(not a["w"] and a["same"] and "Application bloquée" in a["toast"],f"arrondi franchissant le seuil : « Appliquer » refusé dans le gestionnaire, aucune écriture, aucun PU corrigé — « {a['toast'][:110]}… »")
    # ===== 5. gestionnaire direct : bouton contourné, aperçu falsifié =====
    w0=W();a=ev(AP,["fx-t1",-20.01])
    chk(not a["w"] and a["same"] and "Application bloquée" in a["toast"] and "dépassement" in a["toast"],"b31Appliquer appelé directement sur un aperçu hors bornes : refusé, aucune écriture")
    a=ev("""async()=>{const id='fx-t1',a=S.ao[id],X=bpX(id),p0=JSON.stringify(X.p),n=window.__writes.length;B31.pct[id]='20.01';const pr=b31Previsu(id,a,20.01);pr.g44={bloque:false,raisons:[]};pr.A44={k:'bornes'};B31.prev[id]=pr;b31Appliquer(id,a);await new Promise(r=>setTimeout(r,300));
      return{w:window.__writes.slice(n),same:JSON.stringify(X.p)===p0}}""")
    chk(not a["w"] and a["same"],"aperçu falsifié (g44 marqué « non bloqué ») : le gestionnaire recalcule et refuse, aucune écriture")
    pg.evaluate("()=>{S.dept='ao';}");ouvrir(pg,"fx-t1");pg.click('[data-b31-mode="pct"]');pg.fill('[data-b31-pct="fx-t1"]',"-20,01");pg.wait_for_timeout(500);pg.click('[data-b31-prev]');pg.wait_for_selector("[data-b31-bloque44]")
    bt=ev("()=>{const b=document.querySelector('[data-b31-appl]');return{dis:b.disabled,act:b.hasAttribute('data-act'),t:document.querySelector('[data-b31-bloque44]').innerText}}")
    chk(bt["dis"] and not bt["act"] and "Application bloquée" in bt["t"] and "borne" in bt["t"],"interface : bandeau « Application bloquée — art. 44 B », raison et borne, bouton désactivé sans action")
    pg.locator(".b31-sim").screenshot(path=f"{OUT}/apercu_bloque_moins20_01.png")
    pg.evaluate("()=>{const b=document.querySelector('[data-b31-appl]');b.disabled=false;b.click();}");pg.wait_for_timeout(500)
    chk(W()==w0,"bouton réactivé à la main dans le DOM puis cliqué : aucune écriture")
    # ===== 6. changement périmant l'aperçu (estimation, catégorie, TVA, verrous) =====
    w0=W()
    r=ev("""()=>{const id='fx-v1',a=S.ao[id],X=bpX(id),p0=JSON.stringify(X.p),o={};B31.pct[id]='-10';
      B31.prev[id]=b31Previsu(id,a,-10);a.exig.estimation=900000;b31Appliquer(id,a);o.est=!!B31.prev[id]&&B31.prev[id].sig===b31PrevSig(id,a,-10);a.exig.estimation=1200000;
      B31.prev[id]=b31Previsu(id,a,-10);a.categorie='Fournitures';b31Appliquer(id,a);o.cat=JSON.stringify(X.p)!==p0;a.categorie='Travaux';
      B31.prev[id]=b31Previsu(id,a,-10);a.exig.tva=14;b31Appliquer(id,a);o.tva=JSON.stringify(X.p)!==p0;const g=b31Garde44(id,a,b31Cible(120000000,-10),null);delete a.exig.tva;
      B31.prev[id]=b31Previsu(id,a,-10);X.lock={'0-0':true};b31Appliquer(id,a);o.lock=JSON.stringify(X.p)!==p0;X.lock={};o.p=JSON.stringify(X.p)===p0;o.gtva=g.bloque;return o}""");pg.wait_for_timeout(400)
    chk(not r["cat"] and not r["tva"] and not r["lock"] and r["p"] and W()==w0,"aperçu périmé si estimation, catégorie, TVA ou verrou changent : rien appliqué, aucune écriture")
    chk(r["gtva"],"TVA relevée ≠ taux de calcul : application bloquée par la garde")
    a=ev("""async()=>{const id='fx-v1',a=S.ao[id],X=bpX(id),p0=JSON.stringify(X.p),n=window.__writes.length;B31.pct[id]='-10';B31.prev[id]=b31Previsu(id,a,-10);a.exig.estimation=1000000;a.est=1000000;
      const r=b31Previsu(id,a,-10);B31.prev[id]=Object.assign(r,{});a.exig.estimation=1200000;a.est=1200000;b31Appliquer(id,a);await new Promise(r=>setTimeout(r,300));return{w:window.__writes.slice(n).length,same:JSON.stringify(X.p)===p0}}""")
    chk(a["w"]==0 and a["same"],"estimation remontée après l'aperçu (la cible deviendrait hors bornes) : refus, aucune écriture")
    # ===== 7. parcours dans les bornes inchangé =====
    w0=W();a=ev(AP,["fx-v1",-10])
    chk(a["w"]==[["set","bpx/fx-v1"]] and not a["same"],"dans les bornes (−10 %) : application inchangée, une seule écriture sur le dossier fictif")
    st=ev("()=>{const a=S.ao['fx-v1'];return[b31Etat('fx-v1',a).statut.k,a.prixValide||null]}")
    chk(st==["brouillon",None],"après application : brouillon, rien de validé")
    bok=[x for x in (ev(PV,["fx-t1",-20]),ev(PV,["fx-t1",20])) if not x["b"]]
    chk(bool(bok),f"borne exacte avec TTC obtenu dans les bornes : application permise ({len(bok)} cas sur 2)")
    # ===== 8. validation du chiffrage : aucun contournement hors bornes =====
    w0=W()
    v=ev("""async()=>{const id='fx-t2',a=S.ao[id],X=bpX(id);Object.keys(X.p).forEach(k=>{X.p[k]=Math.round(X.p[k]*0.7*100)/100;});const ET=b31Etat(id,a),B=b31Bloquants(id,a,ET);
      const n=window.__writes.length;b31Valider(id,a);b31Valider(id,a);b31Valider(id,a);await new Promise(r=>setTimeout(r,200));return{k:ET.A44.k,B,w:window.__writes.slice(n),pv:a.prixValide||null,of:Object.values(S.offres).filter(o=>o.ao_id===id).length}}""")
    chk(v["k"]=="bas" and any("Validation bloquée" in x for x in v["B"]) and not v["w"] and v["pv"] is None and v["of"]==0,f"validation d'une offre à −30 % (travaux) : refusée même après plusieurs appuis, aucune offre figée, aucune écriture — « {[x for x in v['B'] if 'Validation' in x][0][:110]}… »")
    v=ev("()=>{const id='fx-e1',a=S.ao[id],X=bpX(id);Object.keys(X.p).forEach(k=>{X.p[k]=Math.round(X.p[k]*0.6*100)/100;});const ET=b31Etat(id,a);return{k:ET.A44.k,B:b31Bloquants(id,a,ET)}}")
    chk(v["k"]=="verifier" and not any("art. 44" in x for x in v["B"]),"études à −40 % : aucun seuil inventé, validation non bloquée par l'art. 44 (à vérifier)")
    # ===== 9. ALWAAD réel : lecture seule =====
    w0=W();r=ev("id=>{const a=S.ao[id],R=b31Regime(a),G=b31Garde44(id,a,b31Cible(b31Est(a).c,-25),null);return{R:R.k,b:G.bloque}}",ALW)
    chk(W()==w0,f"ALWAAD réel : garde évaluée en lecture seule (régime {r['R']}, −25 % bloqué : {r['b']}), aucune écriture")
    reel1=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x
    o0,o1=json.loads(reel0),json.loads(reel1);o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    chk(o0==o1 and not ecr_reel(pg),"données réelles inchangées : aucune écriture sur BG, SIDITRAV, ALWAAD, SAP")
    chk(not errs,f"aucune erreur JavaScript ({errs})")
    b.close()
n=sum(1 for x in R if x.startswith("OK"));print(f"\n{n}/{len(R)} OK");json.dump(R,open(os.path.join(OUT,"resultats.json"),"w"),ensure_ascii=False,indent=1)
