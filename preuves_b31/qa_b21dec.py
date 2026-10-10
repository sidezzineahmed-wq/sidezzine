"""Recette b21d-1 · Décision d'Ahmed par société (bureau B2.1). Base simulée locale ; dossiers FICTIFS « fx-dec* » seulement pour
les écritures ; le dossier réel 05/2026/BG n'est que lu (aucune écriture vérifiée)."""
import os,sys,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
M=json.load(open(os.path.join(ICI0,"srv","mockdb_b31.json"),encoding="utf-8"))
RC=json.loads(json.dumps(M["rc"]["pmmp-1033300"]));NP=len(RC["pieces"])
def ao(ref,soc,lim,**k):
    a={"ref":ref,"categorie":"Travaux","obj":"Consultation fictive (test décision B2.1)","est":800000,"soc":soc,"statut":"À examiner","mo":"MAÎTRE D'OUVRAGE FICTIF","lim":lim,"heure":"10H",
       "portail":{"org":"fxdec","ref":ref,"url":""},"exig":{"estimation":800000,"estimationSource":"FICTIF","cautionMode":"montant","caution":10000}}
    a.update(k);return a
M["ao"]["fx-dec"]=ao("FX-DEC","sakdat","2026-12-15",fichiers={"refs":{"id":"x","nom":"refs.pdf","soc":"sakdat","statut":"VÉRIFIÉ"}})
M["ao"]["fx-dec~siditrav"]=ao("FX-DEC","siditrav","2026-12-15",base="fx-dec",statut="En préparation",decision={"verdict":"Go","le":"2026-10-01","qui":"autre_compte","parallele":True},
    dcePieces={"cps":{"cachete":{"id":"c1","soc":"siditrav","statut":"VÉRIFIÉ"}},"rc":{"cachete":{"id":"c2","soc":"siditrav","statut":"VÉRIFIÉ"}}})
M["ao"]["fx-dec~alwaad-ataib"]=ao("FX-DEC","alwaad-ataib","2026-12-15",base="fx-dec",statut="Abandonné",decision={"verdict":"No-Go","le":"2026-10-02","qui":"autre_compte","motif":"plan de charge"},
    fichiers={"refs":{"id":"y","nom":"refs.pdf","soc":"sakdat","statut":"VÉRIFIÉ"}})   # preuve d'une AUTRE société : jamais « Prêt »
M["ao"]["fx-decc"]=ao("FX-DECC","sakdat","2026-09-01",statut="En préparation",decision={"verdict":"Go","le":"2026-08-20","qui":"autre_compte"})
for k in ("fx-dec","fx-decc"):M["rc"][k]=json.loads(json.dumps(RC))
L3=[{"n":"1","d":"Ligne fictive A","u":"U","q":3,"s":"A. Section"},{"n":"2","d":"Ligne fictive B","u":"m²","q":10,"s":"A. Section"}]
for k in ("fx-dec","fx-dec~siditrav"):M["bp"][k]={"lots":[{"lignes":L3}],"cadre":False,"alertes":[]}
M["bpx"]["fx-dec"]={"p":{"0-0":1111.11,"0-1":22.22},"q":{},"soc":"sakdat","tva":{"taux":20,"etat":"confirme","src":{"doc":"CPS FICTIF","page":"1"},"mixte":False,"lignes":{}}}
M["bpx"]["fx-dec~siditrav"]={"p":{"0-0":999.99},"q":{},"soc":"siditrav","tva":{"taux":20,"etat":"confirme","src":{"doc":"CPS FICTIF","page":"1"},"mixte":False,"lignes":{}}}
json.dump(M,open(os.path.join(ICI0,"srv","mockdb_b21dec.json"),"w",encoding="utf-8"),ensure_ascii=False)
src=open(os.path.join(ICI0,"qa_b31.py"),encoding="utf-8").read().replace("mockdb_b31.json","mockdb_b21dec.json").replace('OUT=os.path.join(ICI,"qa_b31")','OUT=os.path.join(ICI,"qa_b21dec")')
exec(src.split("\nwith sync_playwright() as p:")[0])
def dec(pg,id):
    pg.evaluate("id=>{S.dept='ao';S.soc=null;S.aoId=id;render();}",id);pg.click('[data-mpn-dosbur="MP-B2.1|dec"]');pg.wait_for_selector("[data-b21d]",timeout=15000);pg.wait_for_timeout(400)
CARD=lambda s:f'[data-b21d-soc="{s}"]'
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()")
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}")
    reel0=ev("ids=>JSON.stringify(ids.map(i=>[S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc,S.ao[i].decisionHist||null]))",REELS)
    dec(pg,"fx-dec");w0=len(W())
    C=ev("()=>[...document.querySelectorAll('[data-b21d-oid]')].map(c=>({soc:c.dataset.b21dSoc,oid:c.dataset.b21dOid,n:[...c.querySelectorAll('tbody tr')].filter(r=>!r.classList.contains('b21d-sec')).length,v:c.querySelector('[data-b21d-verdict]').dataset.b21dVerdict}))")
    chk(sorted(x["soc"] for x in C)==["alwaad-ataib","sakdat","siditrav"] and all(x["n"]==NP for x in C),f"une carte par société candidate (3), {NP} pièces chacune, construites depuis les pièces du RC")
    T=pg.inner_text("[data-b21d]")
    chk("Enveloppe 1 · Dossier administratif" in T and "Enveloppe 1 · Dossier technique" in T and "Enveloppe 2 · Offre financière" in T and T.find("Enveloppe 1 · Dossier administratif")<T.find("Enveloppe 2 · Offre financière"),"sections Enveloppe 1 (administratif puis technique) puis Enveloppe 2 (financier)")
    chk(not re.search(r"(?i)recommand|conclusion automatique|la plus avancée",T) and next(x for x in C if x["soc"]=="sakdat")["v"]=="aucune" and ev("()=>document.querySelector('[data-b21d-soc=\"sakdat\"] [data-b21d-dec][aria-pressed=\"true\"]')") is None,"aucune recommandation, conclusion automatique ni présélection ; SAKDAT sans décision affiché « Aucune décision »")
    st=lambda s,piece:ev("([s,p])=>{const c=document.querySelector('[data-b21d-soc=\"'+s+'\"]');const r=[...c.querySelectorAll('tbody tr')].find(r=>r.innerText.includes(p));return r?r.dataset.b21dK:null}",[s,piece])
    chk(st("siditrav","CPS et RC")=="pret" and st("sakdat","CPS et RC")!="pret" and st("alwaad-ataib","CPS et RC")!="pret","« CPS et RC signés » Prêt seulement pour SIDITRAV (CPS et RC cachetés VÉRIFIÉ à son nom)")
    chk(st("sakdat","attestations de référence")=="pret" and st("alwaad-ataib","attestations de référence")!="pret","références Prêt pour SAKDAT (fichier VÉRIFIÉ à son nom) ; jamais pour ALWAAD avec un fichier au nom d'une autre société")
    ks=ev("()=>[...document.querySelectorAll('[data-b21d-k]')].map(r=>r.dataset.b21dK)");chk(set(ks)<= {"pret","verif","joindre","compl","nonexige","attrib","chiffre","chval"} and "joindre" in ks and "compl" in ks and "verif" in ks,f"statuts limités à Prêt / À vérifier / À joindre / À compléter (+ non exigé, si attribué, chiffré) : {sorted(set(ks))}")
    fin=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-b21d-oid]')].map(c=>[c.dataset.b21dSoc,(c.querySelector('[data-b21d-fin]')||{}).innerText||'']))")
    TT=pg.inner_text("[data-b21d]").replace(" "," ").replace("\xa0"," ")
    chk("2/2 PU saisis" in fin["sakdat"] and "1/2 PU saisis" in fin["siditrav"] and not re.search(r"TTC|\bHT\b",TT) and not re.search(r"1 111,11|999,99|22,22",TT),"aucun montant HT / TVA / TTC ni PU dans la vue multi-sociétés : couverture (2/2, 1/2 PU) et validation seulement")
    chk(st("sakdat","Bordereau des prix")=="chiffre" and st("siditrav","Bordereau des prix")=="compl","bordereau : « Chiffré · à valider » quand tous les PU de la société sont saisis (non validé), « À compléter » si partiel")
    bp=ev("""()=>{const r=[...document.querySelectorAll('[data-b21d-soc="sakdat"] tbody tr')].find(r=>r.innerText.includes('Bordereau des prix'));return{t:r.innerText,go:r.querySelector('[data-b21d-go]').dataset.b21dGo}}""")
    chk("Chiffré · à valider" in bp["t"] and "Couverture 2/2 PU saisis" in bp["t"] and "signature et cachet restent à faire" in bp["t"] and "Ouvrir" in bp["t"] and bp["go"]=="prix","bordereau rempli : couverture réelle, signature non prétendue, action « Ouvrir » le chiffrage B3.1")
    ae=ev("""()=>{const r=[...document.querySelectorAll('[data-b21d-soc="sakdat"] tbody tr')].find(r=>r.innerText.includes("Acte d'engagement"));return r.querySelector('[data-b21d-go]').dataset.b21dGo}""")
    chk(ae=="pieces","acte d'engagement : action vers sa préparation (pièces B3.2), pas le chiffrage")
    hd=ev("""()=>[...document.querySelectorAll('[data-b21d-oid]')].map(c=>{const t=c.querySelector('table.b21d-tab'),th=[...t.querySelectorAll('thead th')];return{txt:th.map(x=>x.innerText.trim()),vis:getComputedStyle(t.tHead).display!=='none'&&th.every(x=>x.getBoundingClientRect().height>0),scope:th.every(x=>x.getAttribute('scope')==='col'),cap:!!t.caption,lab:t.getAttribute('aria-label')}})""")
    chk(all(h["txt"]==["Pièce","Statut","Action"] and h["vis"] and h["scope"] and h["cap"] and "pièce, statut, action" in h["lab"] for h in hd),"en-têtes Pièce / Statut / Action visibles (scope=col), légende et libellé accessibles sur chaque tableau")
    chk(len(W())==w0,"affichage : aucune écriture")
    # actions = handlers existants de la bonne société
    ev("()=>{const c=document.querySelector('[data-b21d-soc=\"siditrav\"] [data-b21d-go=\"pieces\"]');c.click();}");pg.wait_for_timeout(400)
    r=ev("()=>({id:S.aoId,bur:MPN.dos&&MPN.dos.bur,k:MPN.dos&&MPN.dos.k})");chk(r["id"]=="fx-dec~siditrav" and r["bur"]=="MP-B3.2" and r["k"]=="pieces",f"action « pièces » de SIDITRAV : ouvre SON dossier au bureau B3.2 ({r})")
    dec(pg,"fx-dec");ev("()=>document.querySelector('[data-b21d-soc=\"sakdat\"] [data-b21d-go=\"coffre\"]').click()");pg.wait_for_timeout(300)
    chk(ev("()=>S.soc")=="sakdat","action « coffre » de SAKDAT : ouvre le coffre de SAKDAT (handler de la barre latérale)")
    # décision Go : deux appuis, seul le dossier de la société est écrit, rien d'automatique
    dec(pg,"fx-dec");w0=len(W());pg.click(f'{CARD("sakdat")} [data-b21d-dec="Go"]');pg.wait_for_timeout(300)
    chk(len(W())==w0 and ev("()=>S.ao['fx-dec'].decision")is None and pg.locator(f'{CARD("sakdat")} .b21d-arm').count()==1,"Go : premier appui = demande de confirmation, rien n'est écrit")
    pg.click(f'{CARD("sakdat")} [data-b21d-dec="Go"]');pg.wait_for_timeout(500);d=ev("()=>S.ao['fx-dec']");ww=[w for w in W()[w0:] if w[1].startswith("ao/")]
    chk(d["decision"]["verdict"]=="Go" and d["decision"]["le"] and d["decision"]["qui"] and d["statut"]=="En préparation" and d["soc"]=="sakdat" and ww==[["set","ao/fx-dec"]],f"Go confirmé : décision (verdict, date, auteur) sur le seul dossier SAKDAT, société inchangée ({ww})")
    chk(ev("()=>[S.ao['fx-dec~siditrav'].decision.verdict,S.ao['fx-dec~alwaad-ataib'].decision.verdict]")==["Go","No-Go"],"les décisions des autres sociétés sont conservées")
    # No-Go sans motif refusé ; avec motif : historique conservé
    w0=len(W());pg.click(f'{CARD("sakdat")} [data-b21d-dec="No-Go"]');pg.wait_for_timeout(200);chk(len(W())==w0 and any("motif" in x for x in ev("()=>window.__toastLog")),"No-Go sans motif : refusé, rien n'est écrit")
    pg.fill(f'{CARD("sakdat")} [data-b21d-motif]',"délai trop court (test)");pg.click(f'{CARD("sakdat")} [data-b21d-dec="No-Go"]');pg.wait_for_timeout(200);pg.click(f'{CARD("sakdat")} [data-b21d-dec="No-Go"]');pg.wait_for_timeout(400)
    d=ev("()=>S.ao['fx-dec']");chk(d["decision"]["verdict"]=="No-Go" and d["decision"]["motif"]=="délai trop court (test)" and d["statut"]=="Abandonné" and d["decisionHist"][-1]["verdict"]=="Go" and d["decisionHist"][-1]["remplaceLe"] and d["fichiers"]["refs"]["statut"]=="VÉRIFIÉ","No-Go avec motif : décision remplacée tracée (historique), pièces conservées")
    chk(pg.locator(f'{CARD("sakdat")} .b21d-hist').count()==1,"historique des décisions affiché dans la carte")
    # entreprises retenues, retirer (réversible), Go de nouveau
    R0=ev("()=>[...document.querySelectorAll('[data-b21d-ret]')].map(x=>x.dataset.b21dRet)");chk(R0==["siditrav"],f"« Entreprises retenues » = uniquement les Go réels ({R0})")
    w0=len(W());pg.click('[data-b21d-retirer="siditrav"]');pg.wait_for_timeout(200);chk(len(W())==w0,"Retirer sans motif : refusé (motif demandé dans la carte)")
    pg.fill(f'{CARD("siditrav")} [data-b21d-motif]',"reprendre l'étude (test)");pg.click('[data-b21d-retirer="siditrav"]');pg.wait_for_timeout(200);pg.click(f'{CARD("siditrav")} [data-b21d-dec="À reprendre"]');pg.wait_for_timeout(400)
    s2=ev("()=>S.ao['fx-dec~siditrav']");chk(s2["decision"]["verdict"]=="À reprendre" and s2["statut"]=="À examiner" and s2["dcePieces"]["cps"]["cachete"]["statut"]=="VÉRIFIÉ" and s2["decisionHist"][-1]["verdict"]=="Go","Retirer = « À reprendre » tracé, pièces cachetées conservées")
    chk(ev("()=>[...document.querySelectorAll('[data-b21d-ret]')].length")==0,"retirée de la liste des entreprises retenues")
    pg.click(f'{CARD("siditrav")} [data-b21d-dec="Go"]');pg.wait_for_timeout(200);pg.click(f'{CARD("siditrav")} [data-b21d-dec="Go"]');pg.wait_for_timeout(400)
    chk(ev("()=>[S.ao['fx-dec~siditrav'].decision.verdict,S.ao['fx-dec~siditrav'].statut,S.ao['fx-dec~siditrav'].decisionHist.length]")==["Go","En préparation",2],"réversible : nouveau Go, historique complet (2 décisions remplacées)")
    # ajouter une société via le modèle existant (creerSib)
    ab=ev("()=>[...document.querySelectorAll('[data-b21d-ajout]')].map(x=>x.dataset.b21dAjout)");chk("riyada-build" in ab and "sakdat" not in ab and "siditrav" not in ab,f"« Ajouter » propose seulement des sociétés sans dossier, contrôlées par parCompat ({ab})")
    w0=len(W());pg.click('[data-b21d-ajout="riyada-build"]');pg.wait_for_timeout(200);chk(len(W())==w0,"Ajouter : confirmation demandée, rien n'est créé au premier appui")
    pg.click('[data-b21d-ajout="riyada-build"]');pg.wait_for_timeout(800);n=ev("()=>S.ao['fx-dec~riyada-build']")
    chk(n and n["soc"]=="riyada-build" and n["decision"]["verdict"]=="Go" and n["decision"].get("parallele") and not n.get("decisionHist") and ["set","ao/fx-dec~riyada-build"] in W()[w0:],"Ajouter confirmé : dossier séparé créé par le modèle existant (creerSib), aucun prix ni pièce recopié")
    # consultation clôturée : lecture seule
    dec(pg,"fx-decc");w0=len(W());T=pg.inner_text("[data-b21d]")
    chk("Consultation clôturée le" in T and pg.locator("[data-b21d-dec]").count()==0 and pg.locator("[data-b21d-ajout]").count()==0 and "décision en lecture seule" in T,"consultation clôturée : décision en lecture, ni Go / No-Go, ni ajout, aucune soumission")
    chk(ev("()=>S.ao['fx-decc'].decision.verdict")=="Go","décision existante conservée (clôturée)")
    pg.click('[data-b21d-maj]');pg.wait_for_timeout(300);chk(len(W())==w0,"Actualiser : relecture sans écriture ni changement de décision")
    # dossier réel lu seulement
    dec(pg,BG);n3=ev("()=>document.querySelectorAll('[data-b21d-oid]').length");pg.screenshot(path=f"{OUT}/reel_bg_lecture.png")
    reel1=ev("ids=>JSON.stringify(ids.map(i=>[S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc,S.ao[i].decisionHist||null]))",REELS)
    chk(n3==3 and reel0==reel1 and not ecr_reel(pg) and not errs,f"dossier réel BG (base simulée) : 3 cartes en lecture, décisions et statuts inchangés, aucune écriture réelle, aucune erreur {errs[:2]}")
    dec(pg,"fx-dec");pg.screenshot(path=f"{OUT}/fx_dec_1440.png",full_page=False)
    pg.locator('[data-b21d-soc="siditrav"]').screenshot(path=f"{OUT}/fx_dec_carte_siditrav.png");ctx.close()
    for (w,h,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre"),(1440,900,"dark","1440_sombre")):
        c=b.new_context(viewport={"width":w,"height":h},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q.wait_for_timeout(800);dec(q,"fx-dec")
        L=q.evaluate("()=>{const c=document.querySelector('[data-b21d-soc=\"siditrav\"]'),t=c.querySelector('.b21d-main').getBoundingClientRect(),d=c.querySelector('.b21d-dec').getBoundingClientRect();return{ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,dessous:d.top>=t.bottom-2,droite:d.left>=t.right-2}}")
        hv=q.evaluate("""()=>{const t=document.querySelector('[data-b21d-soc="siditrav"] table.b21d-tab');return getComputedStyle(t.tHead).display!=='none'&&[...t.tHead.querySelectorAll('th')].map(x=>x.innerText.trim()).join('|')==='Pièce|Statut|Action'}""")
        tw=q.evaluate("""()=>[...document.querySelectorAll('.b21d-tw')].map(t=>t.scrollWidth-t.clientWidth)""")
        chk(hv and max(tw)<=1,f"{tag} : en-têtes Pièce / Statut / Action visibles, colonne Action entière (aucun défilement interne : {max(tw)} px)")
        chk(L["ov"]<=1 and (L["dessous"] if w<600 else L["droite"]) and not e,f"{tag} : {'décision sous le tableau' if w<600 else 'décision à droite'}, aucun débordement ({L})")
        q.locator('[data-b21d-soc="siditrav"]').screenshot(path=f"{OUT}/fx_dec_{tag}.png");c.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
