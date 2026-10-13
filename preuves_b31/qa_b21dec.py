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
M["ao"]["fx-deca"]=ao("FX-DECA","sakdat","2026-09-01",statut="Attribué",decision={"verdict":"Go","le":"2026-08-10","qui":"autre_compte"})
M["ao"]["fx-decn"]=ao("FX-DECN","up-modulor","2026-09-01",statut="Non retenu",decision={"verdict":"Go","le":"2026-08-11","qui":"autre_compte"})
M["ao"]["fx-decc"]=ao("FX-DECC","sakdat","2026-09-01",statut="En préparation",decision={"verdict":"Go","le":"2026-08-20","qui":"autre_compte"})
for k in ("fx-dec","fx-decc","fx-deca","fx-decn"):M["rc"][k]=json.loads(json.dumps(RC))
NATT=sum(1 for x in RC["pieces"] if x.get("env")=="attributaire")
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
def ouvre(pg,sid):
    if pg.evaluate("s=>(document.querySelector('[data-b21d-carte=\"'+s+'\"]')||{dataset:{}}).dataset.b21dOuvert",sid)!="1":
        pg.click(f'[data-b21d-tog="{sid}"]');pg.wait_for_timeout(250)
HORS1="s=>{const c=document.querySelector('[data-b21d-hors=\"'+s+'\"]');return{sid:s,v:c.dataset.b21dCompat,pill:c.querySelector('[data-b21d-cv]').innerText,n:(c.querySelector('[data-b21d-n]')||{dataset:{}}).dataset.b21dN||null,mot:c.querySelectorAll('.b21d-mot li').length,txt:c.innerText,dis:c.querySelector('[data-b21d-ajout]').disabled,bl:(c.querySelector('[data-b21d-bloque]')||{}).innerText||''}}"
def hors(pg):
    out=[]
    for s in pg.evaluate("()=>[...document.querySelectorAll('[data-b21d-hors]')].map(c=>c.dataset.b21dHors)"):
        ouvre(pg,s);out.append(pg.evaluate(HORS1,s))
    return out
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()")
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}")
    reel0=ev("ids=>JSON.stringify(ids.map(i=>[S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc,S.ao[i].decisionHist||null]))",REELS)
    dec(pg,"fx-dec");w0=len(W())
    PC="""s=>{const c=document.querySelector('[data-b21d-soc="'+s+'"]'),rows=[...c.querySelectorAll('tbody tr')].filter(r=>!r.classList.contains('b21d-sec')),t=c.querySelector('table.b21d-tab'),th=[...t.querySelectorAll('thead th')];
      const row=p=>rows.find(r=>r.innerText.includes(p));return{soc:s,n:rows.length,v:c.querySelector('[data-b21d-verdict]').dataset.b21dVerdict,pre:!!c.querySelector('[data-b21d-dec][aria-pressed="true"]'),
      st:Object.fromEntries(['CPS et RC','attestations de référence','Bordereau des prix'].map(p=>[p,row(p)?row(p).dataset.b21dK:null])),ks:rows.map(r=>r.dataset.b21dK),fin:!!c.querySelector('[data-b21d-fin]'),txt:c.innerText,
      bp:(r=>r?{t:r.innerText,go:(r.querySelector('[data-b21d-go]')||{dataset:{}}).dataset.b21dGo}:null)(row('Bordereau des prix')),ae:(r=>r?(r.querySelector('[data-b21d-go]')||{dataset:{}}).dataset.b21dGo:null)(row("Acte d'engagement")),
      hd:{txt:th.map(x=>x.innerText.trim()),vis:getComputedStyle(t.tHead).display!=='none'&&th.every(x=>x.getBoundingClientRect().height>0),scope:th.every(x=>x.getAttribute('scope')==='col'),cap:!!t.caption,lab:t.getAttribute('aria-label')}}}"""
    C=[]
    for sid in ev("()=>[...document.querySelectorAll('[data-b21d-oid]')].map(c=>c.dataset.b21dSoc)"):ouvre(pg,sid);C.append(ev(PC,sid))
    CB={x["soc"]:x for x in C}
    chk(sorted(CB)==["alwaad-ataib","sakdat","siditrav"] and all(x["n"]==NP-NATT for x in C),f"une carte par société candidate (3), {NP-NATT} pièces avant dépôt chacune (les {NATT} pièces de l'attributaire sont hors Décision) (détails ouverts une carte à la fois), construites depuis les pièces du RC")
    T="\n".join(x["txt"] for x in C)
    chk("Enveloppe 1 · Dossier administratif" in T and "Enveloppe 1 · Dossier technique" in T and "Enveloppe 2 · Offre financière" in T and T.find("Enveloppe 1 · Dossier administratif")<T.find("Enveloppe 2 · Offre financière"),"sections Enveloppe 1 (administratif puis technique) puis Enveloppe 2 (financier)")
    chk(not re.search(r"(?i)recommand|conclusion automatique|la plus avancée",T+pg.inner_text("[data-b21d]")) and CB["sakdat"]["v"]=="aucune" and not CB["sakdat"]["pre"],"aucune recommandation, conclusion automatique ni présélection ; SAKDAT sans décision affiché « Aucune décision »")
    st=lambda s_,p_:CB[s_]["st"].get(p_)
    chk(st("siditrav","CPS et RC")=="pret" and st("sakdat","CPS et RC")!="pret" and st("alwaad-ataib","CPS et RC")!="pret","« CPS et RC signés » Prêt seulement pour SIDITRAV (CPS et RC cachetés VÉRIFIÉ à son nom)")
    chk(st("sakdat","attestations de référence")=="pret" and st("alwaad-ataib","attestations de référence")!="pret","références Prêt pour SAKDAT (fichier VÉRIFIÉ à son nom) ; jamais pour ALWAAD avec un fichier au nom d'une autre société")
    ks=[k for x in C for k in x["ks"]];chk(set(ks)<= {"pret","verif","joindre","compl","nonexige","prep"} and "joindre" in ks and "compl" in ks and "verif" in ks and "prep" in ks,f"statuts limités à Prêt / À vérifier / À joindre / À compléter / À préparer (+ non exigé), aucun état de chiffrage ni « si attribué » : {sorted(set(ks))}")
    TT=T.replace(" "," ").replace("\xa0"," ")
    chk(not re.search(r"Chiffrage de|PU saisis|Ouvrir le chiffrage|chiffrage B3\.1|Couverture|TVA|Chiffré|Après attribution|Si attribué|attributaire \(si",T) and not re.search(r"TTC|\bHT\b",TT) and not re.search(r"1 111,11|999,99|22,22",TT) and all(not x["fin"] for x in C),"Décision : ni bloc « Chiffrage de … », ni PU / couverture / TVA / validation, ni lien « Ouvrir le chiffrage », ni section après attribution")
    chk(st("sakdat","Bordereau des prix")=="prep" and st("siditrav","Bordereau des prix")=="prep" and CB["sakdat"]["bp"]["go"]=="pieces" and "Préparation" in CB["sakdat"]["bp"]["t"] and CB["sakdat"]["ae"]=="pieces" and ev("()=>document.querySelectorAll('[data-b21d] [data-b21d-go=\"prix\"]').length")==0,"enveloppe 2 (AE, bordereau) : exigences du RC « À préparer », lien générique Préparation (B3.2), aucun lien vers le chiffrage B3.1")
    RS=ev("()=>{const a=S.ao['fx-dec'];return b21dSibs('fx-dec',a).map(x=>{const D=b21dCarteData(x.oid,x.a,x.sid);return[x.sid,D.reste.length,D.reste.filter(r=>r.env!=='e1').length,D.rows.filter(r=>r.env==='e1'&&!['pret','nonexige','attrib','prep'].includes(r.k)).length]})}")
    chk(all(r[1]==r[3] and r[2]==0 for r in RS) and all(CB[r[0]]["txt"].count("avant dépôt")>=1 for r in RS),f"points restants = pièces de l'enveloppe 1 non prêtes, hors offre financière et hors après attribution ({[(r[0],r[1]) for r in RS]})")
    chk(all(x["hd"]["txt"]==["Pièce","Statut","Action"] and x["hd"]["vis"] and x["hd"]["scope"] and x["hd"]["cap"] and "pièce, statut, action" in x["hd"]["lab"] for x in C),"en-têtes Pièce / Statut / Action visibles (scope=col), légende et libellé accessibles sur chaque tableau")
    chk(len(W())==w0,"affichage : aucune écriture")
    # ===== b21d-6 : pièces de l'attributaire dans la vue Résultat (B4.2) du même dossier ; rien d'écrit ; B3.1 intact =====
    ev("()=>{window.__b31n=0;const o=b31Etat;b31Etat=function(){window.__b31n++;return o.apply(this,arguments);};}")
    dec(pg,"fx-dec");ouvre(pg,"sakdat");ouvre(pg,"siditrav");chk(ev("()=>window.__b31n")==0,"Décision (résumés et détails) : le chiffrage B3.1 n'est ni recalculé ni lu (b31Etat appelé 0 fois)")
    w6=len(W());a6=ev("()=>JSON.stringify(['fx-dec','fx-dec~siditrav','fx-deca','fx-decn'].map(i=>[S.ao[i].statut,S.ao[i].decision||null,S.ao[i].soc]))")
    ouvre(pg,"sakdat");pg.click('[data-b21d-carte="sakdat"] [data-b21d-vres]');pg.wait_for_timeout(500)
    RES="""()=>{const s=document.querySelector('[data-b21d-apres]');if(!s)return null;return{vue:document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue,id:S.aoId,k:s.dataset.b21dApres,soc:s.dataset.b21dResSoc,txt:s.innerText,rows:[...s.querySelectorAll('tbody tr[data-b21d-k]')].map(r=>[r.dataset.b21dK,(r.querySelector('[data-b21d-go]')||{dataset:{}}).dataset.b21dGo||null]),det:!!s.querySelector('details'),n:document.querySelectorAll('[data-b21d-apres]').length}}"""
    r6=ev(RES)
    chk(r6 and r6["vue"]=="MP-B4.2|res" and r6["id"]=="fx-dec" and r6["soc"]=="sakdat" and r6["k"]=="conditionnel" and r6["n"]==1 and len(r6["rows"])==NATT and all(k in ("aprod","pret") for k,_ in r6["rows"]) and all(g=="coffre" for k,g in r6["rows"] if k=="aprod"),f"lien « Résultat (B4.2) » de la carte SAKDAT : vue Résultat du même dossier, {NATT} pièces de l'attributaire de SAKDAT avec actions coffre ({r6 and r6['rows']})")
    chk("Conditionnel : à produire seulement si le marché est attribué à SAKDAT" in r6["txt"] and "Aucun résultat n'est supposé" in r6["txt"] and "Source" in r6["txt"] and "coffre de SAKDAT" in r6["txt"],"Résultat : section clairement conditionnelle (rien supposé attribué, rien lancé), sources RC et coffre de la société")
    pg.click('[data-b21d-apres] [data-b21d-go="coffre"]');pg.wait_for_timeout(300);chk(ev("()=>S.soc")=="sakdat","action coffre depuis Résultat : ouvre le coffre de SAKDAT (société propriétaire du dossier)")
    dec(pg,"fx-dec");ouvre(pg,"siditrav");pg.click('[data-b21d-carte="siditrav"] [data-b21d-vres]');pg.wait_for_timeout(500);r7=ev(RES)
    chk(r7 and r7["id"]=="fx-dec~siditrav" and r7["soc"]=="siditrav" and "SIDITRAV" in r7["txt"] and "SAKDAT" not in r7["txt"],"depuis la carte SIDITRAV : Résultat du dossier SIDITRAV, pièces au nom de SIDITRAV seulement")
    ev("id=>{S.dept='ao';S.soc=null;S.aoId=id;render();}","fx-deca");pg.click('[data-mpn-dosbur="MP-B4.2|res"]');pg.wait_for_timeout(500);r8=ev(RES)
    chk(r8 and r8["k"]=="attribue" and "Marché attribué à SAKDAT" in r8["txt"] and len(r8["rows"])==NATT,"dossier fictif « Attribué » : pièces à produire au titre de l'attribution")
    ev("id=>{S.dept='ao';S.soc=null;S.aoId=id;render();}","fx-decn");pg.click('[data-mpn-dosbur="MP-B4.2|res"]');pg.wait_for_timeout(500);r9=ev(RES)
    chk(r9 and r9["k"]=="nonretenu" and "Sans objet" in r9["txt"] and r9["det"] and r9["soc"]=="up-modulor","dossier fictif « Non retenu » : « Sans objet », liste repliée pour mémoire")
    chk(len(W())==w6 and ev("()=>JSON.stringify(['fx-dec','fx-dec~siditrav','fx-deca','fx-decn'].map(i=>[S.ao[i].statut,S.ao[i].decision||null,S.ao[i].soc]))")==a6,"Résultat : aucune écriture, aucune attribution ni résultat créé, statuts / décisions / sociétés inchangés")
    ouvrir(pg,"fx-dec");b6=ev("()=>{const E=b31Etat('fx-dec',S.ao['fx-dec']);return{n:E.T.n,miss:E.T.miss,p:S.bpx['fx-dec'].p,v:!!document.querySelector('[data-b31]')}}")
    chk(b6["v"] and b6["n"]==2 and b6["miss"]==0 and b6["p"]=={"0-0":1111.11,"0-1":22.22} and len(W())==w6,"B3.1 intact : vue chiffrage du dossier, 2/2 PU et prix fictifs inchangés, aucune écriture")
    # ===== b21d-5 : cartes repliées, une seule ouverte, filtres, Modifier, Actualiser, changement d'AO =====
    dec(pg,"fx-dec");pg.evaluate("()=>{B21D.ui={id:null,open:null,f:'tout'};render();}");pg.wait_for_timeout(200);w0=len(W());dec0=ev("()=>JSON.stringify(['fx-dec','fx-dec~siditrav','fx-dec~alwaad-ataib'].map(i=>[S.ao[i].decision||null,S.ao[i].statut]))")
    SUM="""()=>[...document.querySelectorAll('[data-b21d-carte]')].map(c=>{const t=c.querySelector('[data-b21d-tog]'),d=c.querySelector('.b21d-det');return{sid:c.dataset.b21dCarte,ouv:c.dataset.b21dOuvert,aj:c.querySelector('[data-b21d-aj]').dataset.b21dAj,cv:c.querySelector('[data-b21d-cv]').innerText,reste:c.querySelector('[data-b21d-reste]').dataset.b21dReste,sdec:c.querySelector('[data-b21d-sdec]').innerText,
      exp:t.getAttribute('aria-expanded'),ctl:t.getAttribute('aria-controls')===d.id&&!!document.getElementById(t.getAttribute('aria-controls')),lab:t.innerText,hid:d.hidden,vide:d.innerHTML==='',btns:c.querySelectorAll('[data-b21d-dec],[data-b21d-ajout],tbody').length}})"""
    S0=ev(SUM);B={x["sid"]:x for x in S0}
    chk(len(S0)==9 and all(x["ouv"]=="0" and x["exp"]=="false" and x["ctl"] and x["hid"] and x["vide"] and x["btns"]==0 and x["lab"].startswith("Afficher les détails") for x in S0),"toutes les cartes repliées au départ : détails absents du DOM (région vide et masquée), aucun bouton Go / No-Go / Ajouter ni tableau rendu ; aria-expanded=false, aria-controls valide")
    ref=ev("""()=>{const a=S.ao['fx-dec'];return Object.fromEntries(b21dSibs('fx-dec',a).map(x=>[x.sid,[compatEval(x.oid,x.a,x.sid).v,b21dCarteData(x.oid,x.a,x.sid).reste.length]]))}""")
    lab={"Possible":"Compatible","À vérifier":"À vérifier","Écartée":"Incompatible en l'état"}
    chk(all(B[k]["aj"]=="1" and B[k]["cv"]=="Compatibilité RC : "+lab[v[0]] and B[k]["reste"]==str(v[1]) for k,v in ref.items()) and sum(x["aj"]=="1" for x in S0)==3,f"résumé des sociétés ajoutées : « Ajoutée », compatibilité réelle de leur dossier (compatEval), points restants ({ {k:v[1] for k,v in ref.items()} })")
    chk(B["siditrav"]["sdec"]=="Décision : Go · 01/10/2026" and B["alwaad-ataib"]["sdec"]=="Décision : No-Go · 02/10/2026" and B["sakdat"]["sdec"]=="Non décidée" and all(B[k]["sdec"]=="Non décidée" and B[k]["reste"]=="" for k in B if B[k]["aj"]=="0"),"résumé : décision humaine actuelle avec date, ou « Non décidée » (état seulement)")
    R5=ev("()=>({r:document.querySelector('[data-b21d-resume]').innerText,f:Object.fromEntries([...document.querySelectorAll('[data-b21d-f]')].map(b=>[b.dataset.b21dF,[+b.dataset.b21dFn,b.getAttribute('aria-pressed')]])),st:document.querySelector('[data-b21d-fstat]').getAttribute('role')})")
    cats=ev("()=>{const a=S.ao['fx-dec'],X=b21dSibs('fx-dec',a),h=new Set(X.map(x=>x.sid));return X.map(x=>compatEval(x.oid,x.a,x.sid).v).concat(SOC.filter(z=>!h.has(z.sid)).map(z=>compatEval('fx-dec',a,z.sid).v))}")
    exp={"tout":9,"ajoutees":3,"compat":cats.count("Possible"),"averif":cats.count("À vérifier"),"incompat":cats.count("Écartée")}
    chk(R5["r"]=="9 sociétés · 3 ajoutées · 6 non ajoutées" and {k:v[0] for k,v in R5["f"].items()}==exp and R5["f"]["tout"][1]=="true" and R5["st"]=="status",f"résumé « {R5['r']} » ; filtres avec comptes calculés par compatEval {exp} ; « Tout » sélectionné (aria-pressed), état annoncé (role=status)")
    pg.click('[data-b21d-tog="sakdat"]');pg.wait_for_timeout(250);S1={x["sid"]:x for x in ev(SUM)}
    chk(S1["sakdat"]["exp"]=="true" and S1["sakdat"]["lab"].startswith("Masquer les détails") and not S1["sakdat"]["hid"] and S1["sakdat"]["btns"]>0 and ev("()=>document.activeElement&&document.activeElement.dataset.b21dTog")=="sakdat","« Afficher les détails » : tableau, décisions et motif rendus ; bouton « Masquer les détails », aria-expanded=true, focus conservé sur le bouton")
    pg.click('[data-b21d-tog="siditrav"]');pg.wait_for_timeout(250);S2={x["sid"]:x for x in ev(SUM)}
    chk(S2["siditrav"]["exp"]=="true" and S2["sakdat"]["exp"]=="false" and S2["sakdat"]["vide"] and sum(x["ouv"]=="1" for x in S2.values())==1,"une seule carte ouverte : ouvrir SIDITRAV replie SAKDAT (ses détails sont retirés du DOM)")
    pg.focus('[data-b21d-tog="siditrav"]');pg.keyboard.press("Enter");pg.wait_for_timeout(250);k1=ev("()=>document.querySelector('[data-b21d-carte=\"siditrav\"]').dataset.b21dOuvert")
    pg.keyboard.press("Space");pg.wait_for_timeout(250);k2=ev("()=>[document.querySelector('[data-b21d-carte=\"siditrav\"]').dataset.b21dOuvert,document.activeElement.dataset.b21dTog]")
    chk(k1=="0" and k2==["1","siditrav"],"clavier : Entrée replie, Espace rouvre, le focus reste sur le bouton")
    pg.click('[data-b21d-f="ajoutees"]');pg.wait_for_timeout(250);F1=ev("()=>({c:[...document.querySelectorAll('[data-b21d-carte]')].map(c=>c.dataset.b21dCarte),p:document.querySelector('[data-b21d-f=\"ajoutees\"]').getAttribute('aria-pressed'),s:document.querySelector('[data-b21d-fstat]').innerText,o:B21D.ui.open})")
    chk(sorted(F1["c"])==["alwaad-ataib","sakdat","siditrav"] and F1["p"]=="true" and "« Ajoutées » : 3 sociétés affichées sur 9" in F1["s"] and F1["o"]=="siditrav","filtre « Ajoutées » : 3 cartes, bouton pressé, état annoncé ; la carte ouverte (encore visible) reste ouverte")
    pg.click('[data-b21d-f="compat"]');pg.wait_for_timeout(250);F2=ev("()=>({n:document.querySelectorAll('[data-b21d-carte]').length,v:(document.querySelector('[data-b21d-vide]')||{}).innerText||'',o:B21D.ui.open})")
    chk(F2["n"]==0 and "Aucune société dans le filtre « Compatibles »" in F2["v"] and F2["o"] is None,f"filtre vide (« Compatibles » : 0 avec le moteur réel) : message clair et « Tout afficher » ; carte ouverte refermée ({F2['v'][:60]}…)")
    pg.click('[data-b21d-vide] button');pg.wait_for_timeout(250);chk(ev("()=>[document.querySelectorAll('[data-b21d-carte]').length,B21D.ui.f]")==[9,"tout"],"« Tout afficher » : les 9 sociétés, ordre b21d-4")
    # compatibilité orthogonale à « ajoutée » (substitution limitée à cette page de test)
    ev("""()=>{window.__ce5=compatEval;compatEval=function(id,a,sid){const v=window.__ce5(id,a,sid);if(sid==='siditrav'||sid==='up-modulor')return Object.assign({},v,{v:'Possible'});if(sid==='signalsud-sahara')return Object.assign({},v,{v:'Écartée'});return v;};render();}""")
    pg.click('[data-b21d-f="compat"]');pg.wait_for_timeout(250);F3=ev("()=>({c:[...document.querySelectorAll('[data-b21d-carte]')].map(c=>c.dataset.b21dCarte),n:Object.fromEntries([...document.querySelectorAll('[data-b21d-f]')].map(b=>[b.dataset.b21dF,+b.dataset.b21dFn]))})")
    chk(F3["c"]==["siditrav","up-modulor"] and F3["n"]=={"tout":9,"ajoutees":3,"compat":2,"averif":6,"incompat":1},f"filtres orthogonaux : « Compatibles » montre une société ajoutée (SIDITRAV) et une non ajoutée, dans l'ordre b21d-4 ; comptes {F3['n']}")
    pg.click('[data-b21d-f="incompat"]');pg.wait_for_timeout(250);chk(ev("()=>[...document.querySelectorAll('[data-b21d-carte]')].map(c=>c.dataset.b21dCarte)")==["signalsud-sahara"],"filtre « Incompatibles » : SIGNALSUD SAHARA seule")
    ev("()=>{compatEval=window.__ce5;render();}")
    # Modifier (retenues) : bonne carte ouverte, filtre rendu visible, défilement et focus sur le motif
    pg.evaluate("()=>window.scrollTo(0,0)");pg.click('[data-b21d-modifier="siditrav"]');pg.wait_for_timeout(1200)
    M=ev("()=>{const c=document.querySelector('[data-b21d-carte=\"siditrav\"]'),r=c&&c.getBoundingClientRect();return{f:B21D.ui.f,o:B21D.ui.open,vis:!!r&&r.top<innerHeight&&r.bottom>0,foc:document.activeElement&&document.activeElement.dataset.b21dMotif,ouv:c&&c.dataset.b21dOuvert}}")
    chk(M["f"]=="tout" and M["o"]=="siditrav" and M["ouv"]=="1" and M["vis"] and M["foc"]=="fx-dec~siditrav",f"« Modifier » (retenues) depuis un filtre qui cachait SIDITRAV : filtre « Tout », carte SIDITRAV ouverte, défilement et focus sur son motif ({M})")
    # Actualiser : filtre et carte ouverte conservés, rien d'écrit
    pg.click('[data-b21d-f="ajoutees"]');pg.wait_for_timeout(250);pg.click('[data-b21d-maj]');pg.wait_for_timeout(400)
    chk(ev("()=>[B21D.ui.f,B21D.ui.open,document.querySelector('[data-b21d-carte=\"siditrav\"]').dataset.b21dOuvert]")==["ajoutees","siditrav","1"],"« Actualiser » : filtre « Ajoutées » et carte SIDITRAV ouverte conservés")
    chk(len(W())==w0 and ev("()=>JSON.stringify(['fx-dec','fx-dec~siditrav','fx-dec~alwaad-ataib'].map(i=>[S.ao[i].decision||null,S.ao[i].statut]))")==dec0,"ouvrir, fermer, filtrer, Modifier, Actualiser : aucune écriture, décisions et statuts identiques")
    # changement d'AO : état d'affichage réinitialisé
    dec(pg,"fx-decc");U=ev("()=>[B21D.ui.id,B21D.ui.f,B21D.ui.open,document.querySelectorAll('[data-b21d-carte][data-b21d-ouvert=\"1\"]').length]")
    dec(pg,"fx-dec");U2=ev("()=>[B21D.ui.f,B21D.ui.open]")
    chk(U==["fx-decc","tout",None,0] and U2==["tout",None],f"changer d'AO réinitialise filtre et carte ouverte (aucune carte d'un autre dossier reste ouverte) {U}")
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
    ouvre(pg,"siditrav");ev("()=>{const c=document.querySelector('[data-b21d-soc=\"siditrav\"] [data-b21d-go=\"pieces\"]');c.click();}");pg.wait_for_timeout(400)
    r=ev("()=>({id:S.aoId,bur:MPN.dos&&MPN.dos.bur,k:MPN.dos&&MPN.dos.k})");chk(r["id"]=="fx-dec~siditrav" and r["bur"]=="MP-B3.2" and r["k"]=="pieces",f"action « pièces » de SIDITRAV : ouvre SON dossier au bureau B3.2 ({r})")
    dec(pg,"fx-dec");ouvre(pg,"sakdat");ev("()=>document.querySelector('[data-b21d-soc=\"sakdat\"] [data-b21d-go=\"coffre\"]').click()");pg.wait_for_timeout(300)
    chk(ev("()=>S.soc")=="sakdat","action « coffre » de SAKDAT : ouvre le coffre de SAKDAT (handler de la barre latérale)")
    # décision Go : deux appuis, seul le dossier de la société est écrit, rien d'automatique
    dec(pg,"fx-dec");ouvre(pg,"sakdat");w0=len(W());pg.click(f'{CARD("sakdat")} [data-b21d-dec="Go"]');pg.wait_for_timeout(300)
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
    ouvre(pg,"siditrav");pg.click(f'{CARD("siditrav")} [data-b21d-dec="Go"]');pg.wait_for_timeout(200);pg.click(f'{CARD("siditrav")} [data-b21d-dec="Go"]');pg.wait_for_timeout(400)
    chk(ev("()=>[S.ao['fx-dec~siditrav'].decision.verdict,S.ao['fx-dec~siditrav'].statut,S.ao['fx-dec~siditrav'].decisionHist.length]")==["Go","En préparation",2],"réversible : nouveau Go, historique complet (2 décisions remplacées)")
    # ===== b21d-4 : toutes les sociétés actuelles du groupe ; cartes compactes ; ajout sans Go =====
    HORS0="()=>[...document.querySelectorAll('[data-b21d-hors]')].map(c=>({sid:c.dataset.b21dHors,v:c.dataset.b21dCompat,pill:c.querySelector('[data-b21d-cv]').innerText,n:(c.querySelector('[data-b21d-n]')||{dataset:{}}).dataset.b21dN||null,mot:c.querySelectorAll('.b21d-mot li').length,txt:c.innerText,dis:c.querySelector('[data-b21d-ajout]').disabled,bl:(c.querySelector('[data-b21d-bloque]')||{}).innerText||''}))"
    dec(pg,"fx-dec");G=ev("()=>({soc:SOC.map(z=>z.sid),full:[...document.querySelectorAll('[data-b21d-oid]')].map(c=>c.dataset.b21dSoc),cpt:document.querySelector('[data-b21d-compte]').dataset.b21dCompte,cptT:document.querySelector('[data-b21d-compte]').innerText})");H=hors(pg)
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
    H=hors(pg);o=[h["sid"] for h in H];V={h["sid"]:h for h in H}
    chk(o==["up-modulor","structure-chantier","build-chantier","riyada-build","sahara-iaamar","signalsud-sahara"],f"ordre : ajoutées (cartes dossier), puis compatibles, à vérifier, incompatibles ({o})")
    chk(V["up-modulor"]["pill"]=="Compatibilité RC : Compatible" and V["build-chantier"]["pill"]=="Compatibilité RC : À vérifier" and "non calculable" in V["build-chantier"]["txt"] and not V["build-chantier"]["dis"],"compatibilité inconnue (verdict B2.3 non déterminé) : « À vérifier », jamais compatible")
    chk(V["signalsud-sahara"]["pill"]=="Compatibilité RC : Incompatible en l'état" and V["signalsud-sahara"]["dis"] and "Écartée pour ce marché" in V["signalsud-sahara"]["bl"] and "justificatif daté échu" in V["signalsud-sahara"]["txt"],f"incompatible : visible avec ses raisons, ajout bloqué par parCompat ({V['signalsud-sahara']['bl']})")
    chk(V["sahara-iaamar"]["dis"] and "article 27" in V["sahara-iaamar"]["bl"] and V["sahara-iaamar"]["pill"]=="Compatibilité RC : À vérifier",f"art. 27 : ajout bloqué avec la raison ({V['sahara-iaamar']['bl']}), compatibilité affichée à part")
    w0=len(W());ev("()=>b21dAjouter('fx-dec','signalsud-sahara')");pg.wait_for_timeout(200);chk(len(W())==w0 and "Écartée" in ev("()=>window.__toastLog.slice(-1)[0]"),"appel direct de l'ajout d'une société incompatible : refusé, rien n'est écrit")
    pg.locator(".b21d-socs").screenshot(path=f"{OUT}/hors_ao_1440.png")
    ev("()=>{compatEval=window.__ce;parCompat=window.__pc;render();}")
    # ajout réel de la fixture : riyada-build
    ev("()=>{window.__prep=0;const o=prepDemarrer;prepDemarrer=function(){window.__prep++;return o.apply(this,arguments);};}")
    av=ev("()=>JSON.stringify({d:S.ao['fx-dec'].decision||null,s:S.ao['fx-dec'].soc,st:S.ao['fx-dec'].statut,sid:S.ao['fx-dec~siditrav'].decision,o:Object.keys(S.offres).length,x:['fx-dec','fx-dec~siditrav'].map(i=>S.bpx[i]&&S.bpx[i].p)})")
    ouvre(pg,"riyada-build");w0=len(W());pg.click('[data-b21d-ajout="riyada-build"]');pg.wait_for_timeout(250)
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
    dec(pg,"fx-decc");w0=len(W());ouvre(pg,"sakdat");T=pg.inner_text("[data-b21d]");nd=pg.locator("[data-b21d-dec]").count()
    HC=hors(pg);chk("Consultation clôturée le" in T and nd==0 and pg.locator("[data-b21d-ajout]:not([disabled])").count()==0 and "décision en lecture seule" in T,"consultation clôturée : décision en lecture, ni Go / No-Go, aucun ajout actif, aucune soumission")
    chk(len(HC)+pg.locator("[data-b21d-oid]").count()==9 and all(h["dis"] and "date limite passée" in h["bl"] for h in HC),f"consultation clôturée : les 9 sociétés restent visibles ; « Ajouter » désactivé avec la raison « {HC[0]['bl'] if HC else ''} »")
    ev("()=>b21dAjouter('fx-decc','riyada-build')");pg.wait_for_timeout(200);chk(len(W())==w0 and "date limite passée" in ev("()=>window.__toastLog.slice(-1)[0]"),"clôturée : appel direct de l'ajout refusé, rien n'est écrit")
    chk(ev("()=>S.ao['fx-decc'].decision.verdict")=="Go","décision existante conservée (clôturée)")
    pg.click('[data-b21d-maj]');pg.wait_for_timeout(300);chk(len(W())==w0,"Actualiser : relecture sans écriture ni changement de décision")
    # dossier réel lu seulement
    dec(pg,BG);n3=ev("()=>document.querySelectorAll('[data-b21d-oid]').length");pg.screenshot(path=f"{OUT}/reel_bg_lecture.png")
    reel1=ev("ids=>JSON.stringify(ids.map(i=>[S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc,S.ao[i].decisionHist||null]))",REELS)
    chk(n3==3 and reel0==reel1 and not ecr_reel(pg) and not errs,f"dossier réel BG (base simulée) : 3 cartes en lecture, décisions et statuts inchangés, aucune écriture réelle, aucune erreur {errs[:2]}")
    dec(pg,"fx-dec");pg.screenshot(path=f"{OUT}/fx_dec_1440.png",full_page=False)
    ouvre(pg,"siditrav");pg.locator('[data-b21d-soc="siditrav"]').screenshot(path=f"{OUT}/fx_dec_carte_siditrav.png");ctx.close()
    for (w,h,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre"),(1440,900,"dark","1440_sombre")):
        c=b.new_context(viewport={"width":w,"height":h},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q.wait_for_timeout(800);dec(q,"fx-dec")
        sm=q.evaluate("()=>{const C=[...document.querySelectorAll('[data-b21d-carte]')];return{n:C.length,ouv:C.filter(c=>c.dataset.b21dOuvert==='1').length,ok:C.every(c=>{const r=c.getBoundingClientRect(),b=c.querySelector('[data-b21d-tog]').getBoundingClientRect();return b.left>=r.left-1&&b.right<=r.right+1&&b.height>=36&&c.scrollWidth<=c.clientWidth+1}),fb:[...document.querySelectorAll('[data-b21d-f]')].every(b=>b.getBoundingClientRect().height>=34),ov:document.documentElement.scrollWidth-document.documentElement.clientWidth}}")
        chk(sm["n"]==9 and sm["ouv"]==0 and sm["ok"] and sm["fb"] and sm["ov"]<=1,f"{tag} : 9 résumés repliés, boutons « Afficher les détails » et filtres lisibles, sans débordement ({sm})")
        q.locator(".b21d-socs").screenshot(path=f"{OUT}/replie_{tag}.png");ouvre(q,"siditrav")
        L=q.evaluate("()=>{const c=document.querySelector('[data-b21d-soc=\"siditrav\"]'),t=c.querySelector('.b21d-main').getBoundingClientRect(),d=c.querySelector('.b21d-dec').getBoundingClientRect();return{ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,dessous:d.top>=t.bottom-2,droite:d.left>=t.right-2}}")
        hv=q.evaluate("""()=>{const t=document.querySelector('[data-b21d-soc="siditrav"] table.b21d-tab');return getComputedStyle(t.tHead).display!=='none'&&[...t.tHead.querySelectorAll('th')].map(x=>x.innerText.trim()).join('|')==='Pièce|Statut|Action'}""")
        tw=q.evaluate("""()=>[...document.querySelectorAll('.b21d-tw')].map(t=>t.scrollWidth-t.clientWidth)""")
        nv=q.evaluate("()=>({note:document.querySelectorAll('[data-b21],[data-b21-pdf]').length,b:!!document.querySelector('[data-b21d-voirnote]')})")
        ouvre(q,"riyada-build");hm=q.evaluate("()=>{const c=document.querySelector('[data-b21d-carte=\"riyada-build\"]'),r=c.getBoundingClientRect(),b=c.querySelector('[data-b21d-ajout]').getBoundingClientRect();return{ok:b.left>=r.left-1&&b.right<=r.right+1&&c.scrollWidth<=c.clientWidth+1,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth}}")
        chk(hm["ok"] and hm["ov"]<=1,f"{tag} : détails d'une société non ajoutée (motifs, Ajouter) lisibles sans débordement ({hm})");q.locator('[data-b21d-carte="riyada-build"]').screenshot(path=f"{OUT}/hors_ao_{tag}.png");ouvre(q,"siditrav")
        q.click("[data-b21d-voirnote]");q.wait_for_selector("[data-b21]",timeout=15000);q.wait_for_timeout(300);q.click("[data-b21-dec]");q.wait_for_selector("[data-b21d]",timeout=15000);q.wait_for_timeout(300)
        chk(nv["note"]==0 and nv["b"] and q.evaluate("()=>document.querySelectorAll('[data-b21]').length")==0,f"{tag} : vue Décision sans note ; aller-retour vers la note et retour à la Décision")
        chk(hv and max(tw)<=1,f"{tag} : en-têtes Pièce / Statut / Action visibles, colonne Action entière (aucun défilement interne : {max(tw)} px)")
        chk(L["ov"]<=1 and (L["dessous"] if w<600 else L["droite"]) and not e,f"{tag} : {'décision sous le tableau' if w<600 else 'décision à droite'}, aucun débordement ({L})")
        q.locator('[data-b21d-soc="siditrav"]').screenshot(path=f"{OUT}/fx_dec_{tag}.png")
        q.evaluate("id=>{S.dept='ao';S.soc=null;S.aoId=id;render();}","fx-dec");q.click('[data-mpn-dosbur="MP-B4.2|res"]');q.wait_for_timeout(500)
        rm=q.evaluate("()=>{const s=document.querySelector('[data-b21d-apres]');const t=s.querySelector('.b21d-tw');return{ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,tw:t?t.scrollWidth-t.clientWidth:0,w:s.scrollWidth-s.clientWidth}}")
        chk(rm["ov"]<=1 and rm["tw"]<=1 and rm["w"]<=1 and not e,f"{tag} : section après attribution (Résultat) lisible, sans débordement ({rm})");q.locator('[data-b21d-apres]').screenshot(path=f"{OUT}/resultat_{tag}.png");c.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
