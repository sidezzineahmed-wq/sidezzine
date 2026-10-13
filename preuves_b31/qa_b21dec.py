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
    # ===== b21d-3 : la note d'analyse n'est ni calculée ni rendue dans la vue Décision ; aller-retour par le routage existant =====
    ev("()=>{window.__nNote=0;const o1=vNoteB21,o2=aoNote;vNoteB21=function(){window.__nNote++;return o1.apply(this,arguments);};aoNote=function(){window.__nNote++;return o2.apply(this,arguments);};}")
    dec(pg,"fx-dec");V=ev("""()=>{const m=document.querySelector('[data-mpn-dossier-vue]');return{vue:m.dataset.mpnDossierVue,h2:document.getElementById('mpn-h').innerText.trim(),note:document.querySelectorAll('[data-b21],.b21-dash,.b21-orig,[data-b21-pdf],[data-b21-sec]').length,
      txt:m.innerText,titres:[...m.querySelectorAll('h2,h3')].map(x=>x.innerText.trim()).filter(t=>/Décision d.Ahmed|Note d.analyse/i.test(t)),n:window.__nNote,btn:!!document.querySelector('[data-b21d-voirnote]'),det:!!document.querySelector('details.b21d-note summary')&&[...document.querySelectorAll('details.b21d-note summary')].some(x=>/Note d.analyse/.test(x.innerText))}}""")
    chk(V["vue"]=="MP-B2.1|dec" and V["note"]==0 and V["n"]==0 and not re.search(r"Note d'origine|Aperçu PDF|Télécharger PDF|Avis enregistré de l'Analyste|Recommandation par société|Fiche d'information",V["txt"]),f"vue Décision : note d'analyse ni calculée ({V['n']} appel) ni rendue (aucun bloc, PDF de note, avis Analyste ni recommandation)")
    chk(V["h2"]=="Décision d'Ahmed" and V["titres"]==["Décision d'Ahmed"] and V["btn"] and not V["det"],f"titre unique « Décision d'Ahmed » (titres trouvés : {V['titres']}) ; bouton « Voir la note d'analyse », plus de lien repliable")
    pg.click("[data-b21d-voirnote]");pg.wait_for_selector("[data-b21]",timeout=15000);pg.wait_for_timeout(400)
    N=ev("()=>({id:S.aoId,vue:document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue,b21:document.querySelector('[data-b21]').dataset.b21,h2:document.getElementById('mpn-h').innerText.trim(),dec:document.querySelectorAll('[data-b21d]').length,voir:!!document.querySelector('[data-b21-dec]'),pdf:document.querySelectorAll('[data-b21-pdf]').length})")
    chk(N["id"]=="fx-dec" and N["vue"]=="MP-B2.1|note" and N["b21"]=="fx-dec" and N["dec"]==0 and N["pdf"]>=1 and N["voir"],f"« Voir la note d'analyse » : vraie vue Note d'analyse du même dossier (complète, PDF de note disponible), sans les cartes de décision ({N})")
    pg.click("[data-b21-dec]");pg.wait_for_selector("[data-b21d]",timeout=15000);pg.wait_for_timeout(300)
    chk(ev("()=>[S.aoId,document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue,document.querySelectorAll('[data-b21]').length]")==["fx-dec","MP-B2.1|dec",0],"retour « Ouvrir la décision » (carte 09 de la note) depuis la note : vue Décision du même dossier, sans la note")
    ev("()=>{const L=b31Sibs('fx-dec',S.ao['fx-dec']).find(x=>x.soc==='siditrav');S.aoId=L.id;MPN.dos=Object.assign({},MPN.dos,{id:L.id});mpnDosAller('MP-B2.1','dec');render();}");pg.wait_for_selector("[data-b21d]");pg.click("[data-b21d-voirnote]");pg.wait_for_selector("[data-b21]");pg.wait_for_timeout(300)
    chk(ev("()=>[S.aoId,document.querySelector('[data-b21]').dataset.b21,MPN.dos.k]")==["fx-dec~siditrav","fx-dec~siditrav","note"],"depuis le dossier SIDITRAV : la note ouverte est celle du dossier SIDITRAV (même dossier, même société)")
    chk(len(W())==w0,"navigation Décision ↔ Note : aucune écriture")
    dec(pg,"fx-dec")
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
    # ===== b21d-4 : toutes les sociétés actuelles du groupe ; cartes compactes ; ajout sans Go =====
    HORS="()=>[...document.querySelectorAll('[data-b21d-hors]')].map(c=>({sid:c.dataset.b21dHors,v:c.dataset.b21dCompat,pill:c.querySelector('[data-b21d-cv]').innerText,n:(c.querySelector('[data-b21d-n]')||{dataset:{}}).dataset.b21dN||null,mot:c.querySelectorAll('.b21d-mot li').length,txt:c.innerText,dis:c.querySelector('[data-b21d-ajout]').disabled,bl:(c.querySelector('[data-b21d-bloque]')||{}).innerText||''}))"
    dec(pg,"fx-dec");G=ev("()=>({soc:SOC.map(z=>z.sid),full:[...document.querySelectorAll('[data-b21d-oid]')].map(c=>c.dataset.b21dSoc),cpt:document.querySelector('[data-b21d-compte]').dataset.b21dCompte,cptT:document.querySelector('[data-b21d-compte]').innerText})");H=ev(HORS)
    tous=G["full"]+[h["sid"] for h in H]
    chk(sorted(tous)==sorted(G["soc"]) and len(tous)==len(set(tous)) and len(G["soc"])==9 and G["cpt"]==f"{len(set(G['full']))}/9" and "ajoutée" in G["cptT"],f"liste dynamique (SOC = {len(G['soc'])} sociétés) : chaque société une seule fois, {len(G['full'])} cartes dossier + {len(H)} cartes compactes ; compteur « {G['cptT']} »")
    real=ev("()=>Object.fromEntries(SOC.map(z=>{const v=compatEval('fx-dec',S.ao['fx-dec'],z.sid);return[z.sid,[v.v,v.n.ok+'/'+v.n.ko+'/'+v.n.inc,v.contre.length]]}))")
    chk(all(h["v"]==real[h["sid"]][0] and h["n"]==real[h["sid"]][1] and h["mot"]==min(3,real[h["sid"]][2])+(1 if real[h["sid"]][2]>3 else 0) for h in H) and all("Pas encore ajoutée à cet AO" in h["txt"] for h in H),"cartes compactes : nom, « Pas encore ajoutée à cet AO », verdict, compteurs et motifs repris du vrai moteur B2.3 (compatEval)")
    chk(all(h["pill"]=="Compatibilité RC : À vérifier" for h in H) and not any("Compatible" in h["pill"] for h in H),"moteur réel (exigences du marché inconnues) : toutes « À vérifier », aucune compatibilité inventée")
    chk(all(not h["dis"] for h in H if h["sid"]!="siditrav"),"ajout proposé aux sociétés non bloquées par les règles existantes (parCompat)")
    # ordre et cas : compatible / inconnue (moteur indisponible) / incompatible / art. 27 (substitution limitée à cette page de test)
    ev("""()=>{window.__ce=compatEval;window.__pc=parCompat;compatEval=function(id,a,sid){const v=window.__ce(id,a,sid);
      if(sid==='up-modulor')return Object.assign({},v,{v:'Possible',contre:[],n:{ok:8,ko:0,inc:0}});
      if(sid==='build-chantier')return Object.assign({},v,{v:'Inconnue',n:null,contre:[]});
      if(sid==='signalsud-sahara')return Object.assign({},v,{v:'Écartée',contre:['Attestation fiscale : incompatible en l\\'état, justificatif daté échu (test)'].concat(v.contre),n:{ok:0,ko:1,inc:7}});return v;};
      parCompat=function(id,a,sid){if(sid==='sahara-iaamar')return{st:'non',why:'Même signataire que SAKDAT (test) : interdit par l\\'article 27 du décret 2-22-431'};return window.__pc(id,a,sid);};render();}""")
    H=ev(HORS);o=[h["sid"] for h in H];V={h["sid"]:h for h in H}
    chk(o==["up-modulor","structure-chantier","build-chantier","riyada-build","sahara-iaamar","signalsud-sahara"],f"ordre : ajoutées (cartes dossier), puis compatibles, à vérifier, incompatibles ({o})")
    chk(V["up-modulor"]["pill"]=="Compatibilité RC : Compatible" and V["build-chantier"]["pill"]=="Compatibilité RC : À vérifier" and "non calculable" in V["build-chantier"]["txt"] and not V["build-chantier"]["dis"],"compatibilité inconnue (verdict B2.3 non déterminé) : « À vérifier », jamais compatible")
    chk(V["signalsud-sahara"]["pill"]=="Compatibilité RC : Incompatible en l'état" and V["signalsud-sahara"]["dis"] and "Écartée pour ce marché" in V["signalsud-sahara"]["bl"] and "justificatif daté échu" in V["signalsud-sahara"]["txt"],f"incompatible : visible avec ses raisons, ajout bloqué par parCompat ({V['signalsud-sahara']['bl']})")
    chk(V["sahara-iaamar"]["dis"] and "article 27" in V["sahara-iaamar"]["bl"] and V["sahara-iaamar"]["pill"]=="Compatibilité RC : À vérifier",f"art. 27 : ajout bloqué avec la raison ({V['sahara-iaamar']['bl']}), compatibilité affichée à part")
    w0=len(W());ev("()=>b21dAjouter('fx-dec','signalsud-sahara')");pg.wait_for_timeout(200);chk(len(W())==w0 and "Écartée" in ev("()=>window.__toastLog.slice(-1)[0]"),"appel direct de l'ajout d'une société incompatible : refusé, rien n'est écrit")
    pg.locator(".b21d-hs").screenshot(path=f"{OUT}/hors_ao_1440.png")
    ev("()=>{compatEval=window.__ce;parCompat=window.__pc;render();}")
    # ajout réel de la fixture : riyada-build
    ev("()=>{window.__prep=0;const o=prepDemarrer;prepDemarrer=function(){window.__prep++;return o.apply(this,arguments);};}")
    av=ev("()=>JSON.stringify({d:S.ao['fx-dec'].decision||null,s:S.ao['fx-dec'].soc,st:S.ao['fx-dec'].statut,sid:S.ao['fx-dec~siditrav'].decision,o:Object.keys(S.offres).length,x:['fx-dec','fx-dec~siditrav'].map(i=>S.bpx[i]&&S.bpx[i].p)})")
    w0=len(W());pg.click('[data-b21d-ajout="riyada-build"]');pg.wait_for_timeout(250)
    chk(len(W())==w0 and ev("()=>S.ao['fx-dec~riyada-build']") is None and "Confirmer l'ajout" in pg.inner_text('[data-b21d-ajout="riyada-build"]') and "sans décision (aucun Go)" in ev("()=>window.__toastLog.slice(-1)[0]"),"Ajouter : premier appui = confirmation (« sans décision, aucun Go »), rien n'est créé")
    pg.click('[data-b21d-ajout="riyada-build"]');pg.wait_for_timeout(900);n=ev("()=>S.ao['fx-dec~riyada-build']");ww=W()[w0:]
    chk(n and n["soc"]=="riyada-build" and n["base"]=="fx-dec" and n["statut"]=="À examiner" and "decision" not in n and n["ajout"]["le"] and n["ajout"]["qui"] and ww==[["set","ao/fx-dec~riyada-build"]] and ev("()=>window.__prep")==0,f"ajout confirmé : dossier séparé fx-dec~riyada-build créé par creerSib (sansGo), statut « À examiner », aucune décision ni Go, préparation non lancée ; une seule écriture ({ww})")
    iso=ev("""()=>{const n=S.ao['fx-dec~riyada-build'];const X=S.bpx['fx-dec~riyada-build'];return{bpx:!!X&&(Object.keys(X.p||{}).length>0||Object.keys(X.q||{}).length>0||!!X.tva),wb:window.__writes.some(w=>/^(bpx|offres|chiffrage)\//.test(w[1])&&w[1].includes('riyada')),off:Object.values(S.offres).some(o=>o.ao_id==='fx-dec~riyada-build'),k:Object.keys(n).sort(),cach:Object.values(n.dcePieces||{}).some(x=>x&&(x.cachete||x.sig||x.sigPages)),fich:Object.keys(n.fichiers||{})}}""")
    chk(not iso["bpx"] and not iso["wb"] and not iso["off"] and not iso["cach"] and iso["fich"] in ([],["dce"]) and not any(k in iso["k"] for k in ("prixValide","decisionPrix","bpx","offre","checks_x")),f"dossier isolé : aucun prix, aucune offre, aucune pièce cachetée ou signée recopiée (FIN-ISO-001) ; fichiers {iso['fich']}")
    ap=ev("()=>JSON.stringify({d:S.ao['fx-dec'].decision||null,s:S.ao['fx-dec'].soc,st:S.ao['fx-dec'].statut,sid:S.ao['fx-dec~siditrav'].decision,o:Object.keys(S.offres).length,x:['fx-dec','fx-dec~siditrav'].map(i=>S.bpx[i]&&S.bpx[i].p)})")
    st2=ev("()=>({id:S.aoId,vue:document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue,full:[...document.querySelectorAll('[data-b21d-oid]')].map(c=>c.dataset.b21dSoc),hors:[...document.querySelectorAll('[data-b21d-hors]')].map(c=>c.dataset.b21dHors),cpt:document.querySelector('[data-b21d-compte]').dataset.b21dCompte,ret:[...document.querySelectorAll('[data-b21d-ret]')].map(x=>x.dataset.b21dRet),v:document.querySelector('[data-b21d-soc=\"riyada-build\"] [data-b21d-verdict]').dataset.b21dVerdict})")
    chk(av==ap and st2["id"]=="fx-dec" and st2["vue"]=="MP-B2.1|dec","dossier ouvert, sa société, ses décisions et les prix des autres dossiers inchangés ; on reste sur la vue Décision")
    chk(st2["full"].count("riyada-build")==1 and "riyada-build" not in st2["hors"] and st2["cpt"]=="4/9" and st2["v"]=="aucune" and st2["ret"]==["siditrav"],f"la carte compacte devient carte dossier (sans doublon), compteur 4/9, « Aucune décision », retenues = Go réels seulement ({st2['ret']})")
    w0=len(W());ev("()=>b21dAjouter('fx-dec','riyada-build')");pg.wait_for_timeout(200);chk(len(W())==w0,"second ajout de la même société : refusé, rien n'est créé")
    # actualisation : rechargement complet depuis la base simulée
    ev("()=>window.__persist()");pg.reload();pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);pg.wait_for_timeout(800)
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}");dec(pg,"fx-dec")
    st3=ev("()=>({full:[...document.querySelectorAll('[data-b21d-oid]')].map(c=>c.dataset.b21dSoc),hors:[...document.querySelectorAll('[data-b21d-hors]')].map(c=>c.dataset.b21dHors),cpt:document.querySelector('[data-b21d-compte]').dataset.b21dCompte,dec:S.ao['fx-dec~riyada-build'].decision||null,ret:[...document.querySelectorAll('[data-b21d-ret]')].map(x=>x.dataset.b21dRet)})")
    chk(st3["full"].count("riyada-build")==1 and "riyada-build" not in st3["hors"] and st3["cpt"]=="4/9" and st3["dec"] is None and st3["ret"]==["siditrav"] and len(st3["full"])+len(st3["hors"])==9,f"après rechargement : état stable (carte dossier unique, 4/9, aucune décision créée) {st3['cpt']}")
    W=lambda:ev("()=>window.__writes.slice()")
    # consultation clôturée : lecture seule
    dec(pg,"fx-decc");w0=len(W());T=pg.inner_text("[data-b21d]")
    HC=ev(HORS);chk("Consultation clôturée le" in T and pg.locator("[data-b21d-dec]").count()==0 and pg.locator("[data-b21d-ajout]:not([disabled])").count()==0 and "décision en lecture seule" in T,"consultation clôturée : décision en lecture, ni Go / No-Go, aucun ajout actif, aucune soumission")
    chk(len(HC)+pg.locator("[data-b21d-oid]").count()==9 and all(h["dis"] and "date limite passée" in h["bl"] for h in HC),f"consultation clôturée : les 9 sociétés restent visibles ; « Ajouter » désactivé avec la raison « {HC[0]['bl'] if HC else ''} »")
    ev("()=>b21dAjouter('fx-decc','riyada-build')");pg.wait_for_timeout(200);chk(len(W())==w0 and "date limite passée" in ev("()=>window.__toastLog.slice(-1)[0]"),"clôturée : appel direct de l'ajout refusé, rien n'est écrit")
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
        nv=q.evaluate("()=>({note:document.querySelectorAll('[data-b21],[data-b21-pdf]').length,b:!!document.querySelector('[data-b21d-voirnote]')})")
        hm=q.evaluate("()=>{const s=document.querySelector('.b21d-hs');if(!s)return null;const R=s.getBoundingClientRect(),C=[...s.querySelectorAll('.b21d-mini')].map(c=>{const r=c.getBoundingClientRect();return r.left>=R.left-1&&r.right<=R.right+1&&c.scrollWidth<=c.clientWidth+1});return{n:C.length,ok:C.every(Boolean)}}")
        chk(hm and hm["n"]==6 and hm["ok"],f"{tag} : 6 cartes compactes lisibles, sans débordement ({hm})")
        q.locator(".b21d-hs").screenshot(path=f"{OUT}/hors_ao_{tag}.png")
        q.click("[data-b21d-voirnote]");q.wait_for_selector("[data-b21]",timeout=15000);q.wait_for_timeout(300);q.click("[data-b21-dec]");q.wait_for_selector("[data-b21d]",timeout=15000);q.wait_for_timeout(300)
        chk(nv["note"]==0 and nv["b"] and q.evaluate("()=>document.querySelectorAll('[data-b21]').length")==0,f"{tag} : vue Décision sans note ; aller-retour vers la note et retour à la Décision")
        chk(hv and max(tw)<=1,f"{tag} : en-têtes Pièce / Statut / Action visibles, colonne Action entière (aucun défilement interne : {max(tw)} px)")
        chk(L["ov"]<=1 and (L["dessous"] if w<600 else L["droite"]) and not e,f"{tag} : {'décision sous le tableau' if w<600 else 'décision à droite'}, aucun débordement ({L})")
        q.locator('[data-b21d-soc="siditrav"]').screenshot(path=f"{OUT}/fx_dec_{tag}.png");c.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
