"""Recette b21d-8 (liste des sociétés + panneau ; reprend b21d-1 · Décision d'Ahmed par société (bureau B2.1). Base simulée locale ; dossiers FICTIFS « fx-dec* » seulement pour
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
src=open(os.path.join(ICI0,"qa_b31.py"),encoding="utf-8").read().replace("mockdb_b31.json","mockdb_b21dec.json").replace('OUT=os.path.join(ICI,"qa_b31")','OUT=os.path.join(ICI,"qa_b21dec")').replace('update:async(d)=>{window.__writes.push(["update",path]);const[c,id]=loc(path);DB[c]=DB[c]||{};DB[c][id]=Object.assign(DB[c][id]||{},cp(d));},','update:async(d)=>{window.__writes.push(["update",path]);const[c,id]=loc(path);DB[c]=DB[c]||{};if(!DB[c][id])throw{code:"invalid_argument"};const mg=(t,x)=>{Object.entries(x).forEach(([k,v])=>{if(v&&typeof v==="object"&&!Array.isArray(v)&&t[k]&&typeof t[k]==="object"&&!Array.isArray(t[k]))mg(t[k],v);else t[k]=v;});return t;};mg(DB[c][id],cp(d));},')
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
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()")
    TL="()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}";ev(TL)
    last=lambda:ev("()=>window.__toastLog.slice(-1)[0]||''")
    reel0=ev("ids=>JSON.stringify(ids.map(i=>[S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc,S.ao[i].decisionHist||null]))",REELS)
    sel=lambda sid:(pg.click(f'[data-b21d-item="{sid}"]'),pg.wait_for_timeout(250))
    AOK=lambda:ev("()=>Object.keys(S.ao).sort().join(',')")
    OUV=lambda:(ev("()=>{const s=B21D.ui.sel;document.querySelectorAll('[data-b21d-panel] [data-b21d-dk=\"miss\"]').forEach(d=>B21D.ui.dOpen[s+'|'+d.dataset.b21dDoc]=true);render();}"),pg.wait_for_timeout(200))
    # ===== A. liste : toutes les sociétés, badges, filtres, recherche — sans création ni écriture =====
    dec(pg,"fx-dec");w0=len(W());k0=AOK()
    L0=ev("()=>[...document.querySelectorAll('[data-b21d-item]')].map(b=>({sid:b.dataset.b21dItem,b:[...b.querySelectorAll('[data-b21d-badge]')].map(x=>x.innerText),cur:b.getAttribute('aria-current')}))")
    soc=ev("()=>SOC.map(z=>z.sid)")
    chk(sorted(x["sid"] for x in L0)==sorted(soc) and len(L0)==9 and ev("()=>document.querySelector('[data-b21d-total]').dataset.b21dTotal")=="9","liste : les 9 sociétés actuelles du groupe, chacune une fois (avec ou sans dossier)")
    T=pg.inner_text("[data-b21d]")
    chk("Ajoutée à cet AO" not in T and "Pas encore ajoutée" not in T and all(x["b"] for x in L0),"plus de statut principal « Ajoutée / Non ajoutée » ; chaque société porte au moins un badge d'état")
    EV=ev("""()=>{const a=S.ao['fx-dec'],X=b21dSibs('fx-dec',a);return SOC.map(z=>{const e=b21dEval('fx-dec',a,z.sid,X.find(x=>x.sid===z.sid)||null);return{sid:z.sid,el:e.el.k,info:e.info,nVer:e.nVer,pret:e.pret,B:e.B.map(b=>b[1])}})}""")
    FN=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-b21d-f]')].map(b=>[b.dataset.b21dF,+b.dataset.b21dFn]))")
    exp={"toutes":9,"pretes":sum(e["pret"] for e in EV),"comp":sum(e["info"]>0 for e in EV),"verif":sum(e["el"]=="averif" or e["nVer"]>0 for e in EV),"non":sum(e["el"]=="non" for e in EV)}
    chk(FN==exp,f"filtres Toutes / Prêtes / À compléter / À vérifier / Non éligible : comptes dynamiques issus de l'évaluation réelle {FN}")
    multi=[e for e in EV if len(e["B"])>1]
    chk(len(multi)>=1 and all(any(x["sid"]==e["sid"] and len(x["b"])>=1 for x in L0) for e in multi),f"plusieurs badges si nécessaire (ex. {multi[0]['sid']} : {multi[0]['B']})")
    pg.click('[data-b21d-f="comp"]');pg.wait_for_timeout(250);F1=ev("()=>({c:[...document.querySelectorAll('[data-b21d-item]')].map(b=>b.dataset.b21dItem),p:document.querySelector('[data-b21d-f=\"comp\"]').getAttribute('aria-pressed'),s:document.querySelector('[data-b21d-fstat]').getAttribute('role')})")
    chk(sorted(F1["c"])==sorted(e["sid"] for e in EV if e["info"]>0) and F1["p"]=="true" and F1["s"]=="status","filtre « À compléter » : sociétés avec informations manquantes ; état sélectionné annoncé (aria-pressed, role=status)")
    pg.click('[data-b21d-f="non"]');pg.wait_for_timeout(250);chk(ev("()=>!!document.querySelector('[data-b21d-vide]')")==(exp["non"]==0),"filtre vide (« Non éligible » sur ces fixtures) : message et « Tout afficher »")
    pg.click('[data-b21d-f="toutes"]');pg.wait_for_timeout(200);pg.fill("#b21d-q","sak");pg.wait_for_timeout(300)
    chk(ev("()=>[...document.querySelectorAll('[data-b21d-item]')].map(b=>b.dataset.b21dItem)")==["sakdat"] and ev("()=>document.activeElement&&document.activeElement.id")=="b21d-q","recherche « sak » : SAKDAT seule, focus conservé dans le champ")
    pg.fill("#b21d-q","zzz");pg.wait_for_timeout(300);chk("pour « zzz »" in ev("()=>(document.querySelector('[data-b21d-vide]')||{}).innerText||''"),"recherche sans résultat : message clair")
    pg.click('[data-b21d-vide] button');pg.wait_for_timeout(250)
    sel("alwaad-ataib");P1=ev("()=>({p:document.querySelector('[data-b21d-panel]').dataset.b21dPanel,c:document.querySelector('[data-b21d-item=\"alwaad-ataib\"]').getAttribute('aria-current'),f:document.activeElement&&document.activeElement.id})")
    chk(P1=={"p":"alwaad-ataib","c":"true","f":"b21d-ph"},"sélection : un seul panneau (ALWAAD), ligne marquée aria-current, focus sur le titre du panneau")
    sel("up-modulor");chk(len(W())==w0 and AOK()==k0,"sélectionner, chercher, filtrer : aucune écriture, aucun dossier créé")
    # ===== B. documents par pièce du RC, champs sous la bonne pièce, prêt =====
    sel("alwaad-ataib")
    DOC=lambda:ev("()=>Object.fromEntries([...document.querySelectorAll('[data-b21d-panel] [data-b21d-doc]')].map(d=>[d.dataset.b21dDoc,{k:d.dataset.b21dDk,f:[...d.querySelectorAll('[data-b21d-fr]')].map(r=>r.dataset.b21dFr.split('|')[1]),t:d.innerText}]))")
    D0c=ev("()=>[...document.querySelectorAll('[data-b21d-panel] [data-b21d-dk=\"miss\"]')].map(d=>[d.dataset.b21dDoc,d.dataset.b21dDopen,d.querySelectorAll('[data-b21d-fr]').length,d.querySelector('[data-b21d-dtog]').getAttribute('aria-expanded')])")
    chk(D0c and all(x[1]=="0" and x[2]==0 and x[3]=="false" for x in D0c),f"pièces à compléter repliées par défaut (nom, nombre de manques, « Afficher ») ; rien n'est rendu dedans {D0c}")
    OUV();D1=DOC();PM=ev("()=>{const a=S.ao['fx-dec'],f={...pfDefaults(a,'alwaad-ataib'),...((a.pieces||{})['alwaad-ataib']||{})};return{dh:pfMissing('dh',a,'alwaad-ataib',f),ae:pfMissing('ae',a,'alwaad-ataib',f)}}")
    mp={"signataire":"gerants","téléphone":"tel","e-mail":"mail","RIB":"rib","localité de la banque":"banque","Capital":"capital","CNSS":"cnss","RC":"rc","Patente":"patente","ICE":"ice","Siège":"siege"}
    edh=[mp[x] for x in PM["dh"] if x in mp];eae=[mp[x] for x in PM["ae"] if x in mp]
    chk(D1["dsh"]["f"]==edh and D1["ae"]["f"]==eae and D1["dsh"]["k"]=="miss" and D1["ae"]["k"]=="miss",f"champs sous la bonne pièce, d'après le générateur existant pfMissing : DH {edh}, AE {eae}")
    chk("montant" not in (D1["ae"]["t"].lower().split("montants :")[0]) and "Préparation (B3)" in D1["ae"]["t"],"AE : montant HT, lot, rabais exclus de la décision (préparés en B3)")
    VIS=ev("()=>({c:[...document.querySelectorAll('[data-b21d-panel] [data-b21d-doc]')].map(d=>[d.dataset.b21dDoc,d.dataset.b21dDk,d.closest('[data-b21d-loc]')?d.closest('[data-b21d-loc]').dataset.b21dLoc:'',(d.querySelector('[data-b21d-path]')||{}).innerText||'']),g:[...document.querySelectorAll('[data-b21d-panel] [data-b21d-loc]')].map(g=>[g.dataset.b21dLoc,g.querySelector('.b21d-gh').innerText]),sum:(document.querySelector('[data-b21d-sum]')||{dataset:{}}).dataset.b21dSum,h:(document.getElementById('b21d-ah')||{}).innerText,ctx:document.querySelector('[data-b21d-acv] > .b21d-src').innerText})")
    UQx=len(set(edh)|set(eae))+1   # champs société uniques (RIB commun compté une fois) + la preuve « attestations de référence » (une seule donnée du coffre, aussi citée sous la note des moyens)
    chk(VIS["h"]=="À compléter / vérifier" and "ALWAAD ATAIB" in VIS["ctx"] and "FX-DEC" in VIS["ctx"] and sorted(x[0] for x in VIS["c"])==["ae","dsh","moyens","refs"] and VIS["sum"]==f"4|{UQx}",f"« À compléter / vérifier » (ALWAAD · AO FX-DEC) : seules les pièces avec une donnée société manquante ou une preuve à vérifier ; résumé 4 pièces / {UQx} données uniques (RIB compté une fois) {VIS['c']} {VIS['sum']}")
    LOC={x[0]:x[2] for x in VIS["c"]};PTH={x[0]:x[3] for x in VIS["c"]}
    chk([g[0] for g in VIS["g"]]==["1|adm","1|tec","2|fin"] and LOC=={"dsh":"1|adm","refs":"1|tec","moyens":"1|tec","ae":"2|fin"} and PTH["dsh"].startswith("Destination : Enveloppe 1 › Dossier administratif › Déclaration") and PTH["moyens"].startswith("Destination : Enveloppe 1 › Dossier technique › Note sur les moyens") and PTH["ae"].startswith("Destination : Enveloppe 2 › Offre financière › Acte d'engagement"),f"chemin réel du RC (plis + enveloppe de chaque pièce) : DH → Env. 1 administratif, note des moyens → Env. 1 technique, AE → Env. 2 offre financière {VIS['g']}")
    TM=D1["moyens"]["t"];chk(D1["moyens"]["k"]=="miss" and "À corriger dans : coffre de ALWAAD ATAIB" in TM and ev("()=>!!document.querySelector('[data-b21d-doc=\"moyens\"] [data-b21d-aref=\"refs\"]')") and not __import__("re").search(r"non structur|générateur|repères|\[à compléter|Rédaction en préparation|Rédigée",TM) and "Exigences à préciser après lecture du CPS" in pg.inner_text("[data-b21d-alr]"),"note des moyens : affichée seulement pour la donnée société manquante (références → renvoi vers la même pièce du coffre) ; lieu de correction = coffre ; besoins CPS : alerte « Exigences à préciser après lecture du CPS », aucune rédaction demandée")
    chk(not set(D1)&{"caution","bpu","cpsrc","sdp"} and "Lignes de caution" not in " ".join(x[0] for x in VIS["c"]),f"plus rendus dans la Décision : récépissé de caution, BPU (B3), CPS/RC sans manque, pièces prêtes {sorted(D1)}")
    sel("sakdat");OUV();D2=DOC()
    RI=ev("()=>({r:(document.querySelector('[data-b21d-rien]')||{dataset:{}}).dataset.b21dRien,p:!!document.querySelector('[data-b21d-acv] [data-b21d-prepgo]'),miss:document.querySelectorAll('[data-b21d-panel] [data-b21d-dk=\"miss\"],[data-b21d-panel] [data-b21d-dk=\"proof\"]').length,t:document.querySelector('[data-b21d-acv]').innerText})")
    chk(not D2 and RI["miss"]==0 and RI["r"]=="partiel" and RI["p"] and "Aucune donnée société manquante identifiée" in RI["t"] and "Rien à compléter ici" not in RI["t"] and "Exigences à préciser après lecture du CPS" in RI["t"],"SAKDAT : aucune carte (rien de manquant) ; besoins CPS non établis → « Exigences à préciser », pas de « Rien à compléter » ; « Ouvrir Préparation »")
    T2=pg.inner_text("[data-b21d-panel]")
    chk("ne signifie pas offre prête au dépôt" in T2 and not pg.locator("[data-b21d] table").count() and not __import__("re").search(r"Chiffrage de|PU saisis|Après attribution|attributaire|TVA|TTC",T2),"panneau : mention « ne signifie pas offre prête au dépôt » ; aucun tableau, chiffrage ni après attribution")
    chk("Éligibilité pour cet AO" in T2 and "Source" in T2 and ev("()=>!!document.querySelector('[data-b21d-everif]')"),"bande « Éligibilité pour cet AO » : statut, raison, source, action « Vérifier »")
    # ===== C. enregistrement automatique partagé (profil de LA société) =====
    sel("alwaad-ataib");SID="alwaad-ataib";w1=len(W());db0=ev("()=>JSON.stringify(window.__DB.societes)");dec0=ev("()=>JSON.stringify(Object.keys(S.ao).filter(i=>i.startsWith('fx-dec')).map(i=>[i,S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc]))")
    OUV();I=f'[data-b21d-doc="dsh"] [data-b21d-pf="{SID}|tel"]';pg.click(I);pg.keyboard.type("06123",delay=40);c1=ev("i=>{const e=document.querySelector(i);return[e.value,e.selectionStart]}",I);pg.keyboard.type("45678",delay=40);c2=ev("i=>{const e=document.querySelector(i);return[e.value,e.selectionStart,document.activeElement===e]}",I)
    chk(c1==["06123",5] and c2==["0612345678",10,True] and len(W())==w1,"saisie sous la DH : curseur stable, aucune écriture pendant la frappe")
    pg.wait_for_timeout(2200);ww=W()[w1:]
    chk(ww==[["update",f"societes/{SID}"]] and ev("s=>window.__DB.societes[s].profil.tel",SID)=="0612345678" and ev(f"()=>document.querySelector('[data-b21d-pfkey=\"{SID}|tel\"]').dataset.b21dPfst")=="ok","pause : enregistré dans le profil d'ALWAAD (update du seul champ), « Enregistré ✓ » après réponse de la base")
    R1=f'[data-b21d-doc="dsh"] [data-b21d-pf="{SID}|rib"]';pg.click(R1);pg.keyboard.type("1234567890")
    ptr=ev(f"()=>{{const r=document.querySelector('[data-b21d-doc=\"ae\"] [data-b21d-fr=\"{SID}|rib\"]');return r?[r.dataset.b21dFref||'',!!r.querySelector('input')]:null}}")
    pg.keyboard.type("12345678901234");pg.keyboard.press("Tab");pg.wait_for_timeout(900)
    rw=[w for w in W()[w1:] if w[1]==f"societes/{SID}"];RES=ev(f"()=>[...document.querySelectorAll('[data-b21d-fr=\"{SID}|rib\"]')].map(r=>[r.closest('[data-b21d-doc]').dataset.b21dDoc,r.dataset.b21dFres||'',r.innerText.includes('Renseigné dans le coffre')])")
    chk(ptr==["dsh",False] and ev("s=>window.__DB.societes[s].profil.rib",SID)=="123456789012345678901234" and len(rw)==2 and sorted(RES)==[["ae","1",True],["dsh","1",True]],f"RIB : une seule occurrence saisissable (l'AE renvoie à la DH) ; une seule écriture ; après confirmation de la base, DH et AE affichent « Renseigné dans le coffre ✓ » {RES}")
    # changement de société pendant une saisie : rien n'est perdu ni envoyé à une autre société
    M1=f'[data-b21d-doc="dsh"] [data-b21d-pf="{SID}|mail"]';pg.click(M1);pg.keyboard.type("contact@exemple.ma");pg.click('[data-b21d-item="sakdat"]');pg.wait_for_timeout(900)
    chk(ev("s=>window.__DB.societes[s].profil.mail",SID)=="contact@exemple.ma" and ev("()=>(window.__DB.societes.sakdat.profil||{}).mail")!="contact@exemple.ma" and ev("()=>document.querySelector('[data-b21d-panel]').dataset.b21dPanel")=="sakdat","changer de société pendant la saisie : la valeur part dans le profil d'ALWAAD seulement, jamais chez SAKDAT")
    ev("""()=>{window.__fail=1;const o=S.db.doc.bind(S.db);window.__dbdoc=S.db.doc;S.db.doc=p=>{const r=o(p);if(String(p).startsWith('societes/'))return Object.assign({},r,{update:async d=>{if(window.__fail>0){window.__fail--;throw{code:'unavailable'};}return r.update(d);},set:async d=>{if(window.__fail>0){window.__fail--;throw{code:'unavailable'};}return r.set(d);}});return r;};}""")
    sel(SID);OUV();B1=f'[data-b21d-doc="ae"] [data-b21d-pf="{SID}|banque"]';pg.click(B1);pg.keyboard.type("BANQUE FICTIVE QA");pg.click('[data-b21d-item="sakdat"]');pg.wait_for_timeout(900)
    pend=ev(f"()=>!!document.querySelector('[data-b21d-item=\"{SID}\"] [data-b21d-pend]')")
    sel(SID);OUV();E1=ev(f"()=>{{const i=document.querySelector('[data-b21d-doc=\"ae\"] [data-b21d-pf=\"{SID}|banque\"]');return{{v:i.value,st:document.querySelector('[data-b21d-pfkey=\"{SID}|banque\"]').dataset.b21dPfst,r:!!document.querySelector('[data-b21d-pfretry=\"{SID}|banque\"]')}}}}")
    chk(pend and E1=={"v":"BANQUE FICTIVE QA","st":"err","r":True} and "banque" not in ev("s=>window.__DB.societes[s].profil",SID),"échec pendant un changement de société : « Saisie non enregistrée » dans la liste, brouillon conservé, « Échec » + « Réessayer »")
    pg.click(f'[data-b21d-pfretry="{SID}|banque"]');pg.wait_for_timeout(800);ev("()=>{S.db.doc=window.__dbdoc;}")
    chk(ev("s=>window.__DB.societes[s].profil.banque",SID)=="BANQUE FICTIVE QA","« Réessayer » : enregistré")
    # conflit
    S2="up-modulor";sel(S2);OUV();ev("s=>{window.__DB.societes[s].profil=Object.assign(window.__DB.societes[s].profil||{},{tel:'0700000000 (ailleurs)'});}",S2);T1=f'[data-b21d-doc="dsh"] [data-b21d-pf="{S2}|tel"]'
    pg.fill(T1,"0611111111");pg.focus(T1);pg.keyboard.press("Tab");pg.wait_for_timeout(800)
    C1=ev(f"()=>[document.querySelector('[data-b21d-pfkey=\"{S2}|tel\"]').dataset.b21dPfst,!!document.querySelector('[data-b21d-pfforce=\"{S2}|tel\"]')]")
    chk(C1==["conflit",True] and ev("s=>window.__DB.societes[s].profil.tel",S2)=="0700000000 (ailleurs)","modification concurrente : « Conflit », rien n'est écrasé sans choix explicite")
    pg.click(f'[data-b21d-pfforce="{S2}|tel"]');pg.wait_for_timeout(700);chk(ev("s=>window.__DB.societes[s].profil.tel",S2)=="0611111111","« Remplacer par ma saisie » : seul ce champ est remplacé")
    pg.fill(f'[data-b21d-doc="dsh"] [data-b21d-pf="{S2}|mail"]',"pas-un-mail");pg.focus(f'[data-b21d-doc="dsh"] [data-b21d-pf="{S2}|mail"]');pg.keyboard.press("Tab");pg.wait_for_timeout(500)
    chk(ev(f"()=>document.querySelector('[data-b21d-pfkey=\"{S2}|mail\"]').dataset.b21dPfst")=="invalid" and "mail" not in (ev("s=>window.__DB.societes[s].profil",S2) or {}),"valeur invalide : « À corriger », rien n'est écrit")
    o0=json.loads(db0);n0=ev("()=>window.__DB.societes")
    chk(all(n0[k]==o0[k] for k in o0 if k not in (SID,S2)) and sorted(n0[SID]["profil"].keys())==["banque","mail","maj","rib","tel"] and sorted(n0[S2]["profil"].keys())==["maj","tel"],"isolation : autres sociétés intactes ; chez ALWAAD et UP-MODULOR, seuls les champs saisis")
    chk(ev("()=>JSON.stringify(Object.keys(S.ao).filter(i=>i.startsWith('fx-dec')).map(i=>[i,S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc]))")==dec0 and not [w for w in W()[w1:] if w[1].startswith("ao/")],"saisies : aucune décision, aucun dossier créé ni modifié")
    ev("()=>window.__persist()");pg.reload();pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50&&S.dbState==='ok'",timeout=20000);pg.wait_for_timeout(900);ev(TL)
    dec(pg,"fx-dec");sel(SID);OUV();D4=DOC()
    chk("dsh" not in D4 and "ae" not in D4 and ev("s=>profilOf(s).rib",SID)=="123456789012345678901234","après rechargement : informations relues de la base ; DH et AE d'ALWAAD complètes → retirées de « À compléter / vérifier »")
    W=lambda:ev("()=>window.__writes.slice()")
    # ===== D. décision : ouverture sans écriture, confirmation explicite =====
    sel("sakdat");w2=len(W())
    chk(pg.locator('[data-b21d-choix]').count()==0 and "Aucune décision enregistrée" in pg.inner_text("[data-b21d-decsec]"),"décision : aucun choix affiché avant « Prendre une décision »")
    pg.click('[data-b21d-prendre]');pg.wait_for_timeout(250)
    O=ev("()=>({c:[...document.querySelectorAll('[data-b21d-choix]')].map(b=>[b.dataset.b21dChoix,b.getAttribute('aria-checked'),b.innerText]),cf:document.querySelector('[data-b21d-confirmer]').disabled})")
    chk([x[2] for x in O["c"]]==["Participer","Ne pas participer","À réexaminer"] and all(x[1]=="false" for x in O["c"]) and O["cf"] and len(W())==w2,"« Prendre une décision » : Participer / Ne pas participer / À réexaminer, aucun choix initial, confirmation désactivée, rien d'écrit")
    pg.click('[data-b21d-choix="nepas"]');pg.wait_for_timeout(200);chk(len(W())==w2 and ev("()=>document.querySelector('[data-b21d-choix=\"nepas\"]').getAttribute('aria-checked')")=="true","choisir n'enregistre rien")
    pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(300);chk(len(W())==w2 and "Motif obligatoire" in last(),"« Ne pas participer » sans motif : refusé")
    pg.click('[data-b21d-choix="participer"]');pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(600);ww=W()[w2:];d=ev("()=>S.ao['fx-dec']")
    chk(ww==[["set","ao/fx-dec"]] and d["decision"]["verdict"]=="Go" and d["statut"]=="En préparation" and d["soc"]=="sakdat" and "Participer" in ev("()=>document.querySelector('[data-b21d-decact]').innerText"),"« Participer » confirmé : enregistré comme Go (mapping inchangé en base) sur le seul dossier SAKDAT")
    chk("Modifier la décision" in ev("()=>document.querySelector('[data-b21d-prendre]').innerText") and ev("()=>document.querySelector('[data-b21d-item=\"sakdat\"] [data-b21d-idec]').innerText")=="Participer","décision existante : date, auteur, motif ; « Modifier la décision » ; badge « Participer » dans la liste")
    chk(ev("()=>[S.ao['fx-dec~siditrav'].decision.verdict,S.ao['fx-dec~alwaad-ataib'].decision.verdict]")==["Go","No-Go"],"décisions des autres sociétés conservées")
    # société sans dossier : « Participer » crée d'abord son dossier indépendant, sans finances
    sel("up-modulor");w3=len(W());pg.click('[data-b21d-prendre]');pg.wait_for_timeout(250)
    chk(ev("()=>[...document.querySelectorAll('[data-b21d-choix]')].map(b=>b.disabled)")==[False,False,False] and "dossier séparé" in pg.inner_text("[data-b21d-decsec]") and ev("()=>S.ao['fx-dec~up-modulor']") is None and len(W())==w3,"société sans dossier : les trois choix disponibles, création annoncée, rien n'est créé ni écrit à l'ouverture")
    ev("()=>{window.__prep=0;const o=prepDemarrer;prepDemarrer=function(){window.__prep++;return o.apply(this,arguments);};}")
    pg.click('[data-b21d-choix="participer"]');pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(1200);n=ev("()=>S.ao['fx-dec~up-modulor']");ww=[w for w in W()[w3:] if w[1].startswith("ao/")]
    iso=ev("()=>({bpx:!!(S.bpx['fx-dec~up-modulor']&&Object.keys(S.bpx['fx-dec~up-modulor'].p||{}).length),off:Object.values(S.offres).some(o=>o.ao_id==='fx-dec~up-modulor'),cach:Object.values((S.ao['fx-dec~up-modulor']||{}).dcePieces||{}).some(x=>x&&(x.cachete||x.sig))})")
    chk(n and n["soc"]=="up-modulor" and n["base"]=="fx-dec" and n["decision"]["verdict"]=="Go" and n["statut"]=="En préparation" and ww==[["set","ao/fx-dec~up-modulor"],["set","ao/fx-dec~up-modulor"]] and not any(iso.values()) and ev("()=>window.__prep")==1,f"« Participer » confirmé sans dossier : dossier indépendant créé (creerSib, sans finances ni pièces signées), puis participation enregistrée ({ww})")
    # ===== b21d-9 : Ne pas participer / À réexaminer pour une société sans dossier =====
    ST=lambda i:ev("i=>{const x=S.ao[i];return x?{v:(x.decision||{}).verdict||null,st:x.statut,m:(x.decision||{}).motif||'',h:(x.decisionHist||[]).map(z=>z.verdict),base:x.base,soc:x.soc}:null}",i)
    PU=lambda i:ev("i=>({bpx:!!(S.bpx[i]&&(Object.keys(S.bpx[i].p||{}).length||S.bpx[i].tva)),off:Object.values(S.offres).some(o=>o.ao_id===i),ecr:window.__writes.filter(w=>/^(bpx|offres|chiffrage)\//.test(w[1])&&w[1].includes(i)).length})",i)
    p0=ev("()=>window.__prep");sel("riyada-build");w6=len(W());pg.click('[data-b21d-prendre]');pg.wait_for_timeout(200);pg.click('[data-b21d-choix="nepas"]');pg.wait_for_timeout(200)
    chk(len(W())==w6 and ST("fx-dec~riyada-build") is None,"sans dossier : ouvrir puis choisir « Ne pas participer » n'écrit et ne crée rien")
    pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(300);chk(len(W())==w6 and ST("fx-dec~riyada-build") is None and "Motif obligatoire" in last(),"« Ne pas participer » sans motif : refusé, aucun dossier créé")
    pg.fill('[data-b21d-motif="s:riyada-build"]',"plan de charge (test)");pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(1200)
    s1=ST("fx-dec~riyada-build");ww=[w for w in W()[w6:] if w[1].startswith("ao/")]
    chk(s1=={"v":"No-Go","st":"Abandonné","m":"plan de charge (test)","h":[],"base":"fx-dec","soc":"riyada-build"} and ww==[["set","ao/fx-dec~riyada-build"],["set","ao/fx-dec~riyada-build"]],f"« Ne pas participer » confirmé : dossier indépendant créé puis No-Go enregistré (statut Abandonné, motif) {ww}")
    chk(ev("()=>window.__prep")==p0 and not any(PU("fx-dec~riyada-build").values()) and "Ne pas participer" in ev("()=>document.querySelector('[data-b21d-item=\"riyada-build\"] [data-b21d-idec]').innerText"),"aucune préparation lancée, aucun PU / offre / chiffrage ; badge « Ne pas participer » dans la liste")
    pg.click('[data-b21d-prendre]');pg.wait_for_timeout(200);pg.click('[data-b21d-choix="reex"]');pg.fill('[data-b21d-motif="s:riyada-build"]',"à revoir après visite (test)");pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(600);s2=ST("fx-dec~riyada-build")
    chk(s2["v"]=="À reprendre" and s2["st"]=="À examiner" and s2["h"]==["No-Go"] and ev("()=>window.__prep")==p0,"« Modifier la décision » → « À réexaminer » : statut À examiner, décision précédente dans l'historique, aucune préparation")
    sel("build-chantier");w7=len(W());pg.click('[data-b21d-prendre]');pg.click('[data-b21d-choix="reex"]');pg.fill('[data-b21d-motif="s:build-chantier"]',"exigences à relire (test)");pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(1200);s3=ST("fx-dec~build-chantier")
    chk(s3 and s3["v"]=="À reprendre" and s3["st"]=="À examiner" and s3["h"]==[] and ev("()=>window.__prep")==p0 and not any(PU("fx-dec~build-chantier").values()) and len([w for w in W()[w7:] if w[1].startswith("ao/")])==2,"« À réexaminer » sans dossier : dossier créé à la confirmation, statut À examiner, aucune préparation ni chiffrage")
    # société non éligible (art. 27 sur la fixture) : non-participation mémorisée, participation toujours refusée
    NE=ev("""()=>{const a=S.ao['fx-dec'],X=b21dSibs('fx-dec',a);return SOC.map(z=>z.sid).filter(s=>!X.some(x=>x.sid===s)&&b21dEval('fx-dec',a,s,null).el.k==='non')}""")
    chk(len(NE)>=1,f"cas fictif « Non éligible » sans dossier disponible ({NE})")
    sid9=NE[0];sel(sid9);w8=len(W());pg.click('[data-b21d-prendre]');pg.click('[data-b21d-choix="participer"]');pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(500)
    chk(len(W())==w8 and ST("fx-dec~"+sid9) is None and "Participation impossible" in last(),f"{sid9} (non éligible) : « Participer » refusé, aucun dossier créé")
    pg.click('[data-b21d-choix="nepas"]');pg.fill(f'[data-b21d-motif="s:{sid9}"]',"non éligible : même signataire (test)");pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(1200);s4=ST("fx-dec~"+sid9)
    act9=ev("s=>consultSibs(S.ao['fx-dec']).some(([o,b])=>b.soc===s)",sid9)
    chk(s4 and s4["v"]=="No-Go" and s4["st"]=="Abandonné" and not act9 and ev("()=>window.__prep")==p0,f"{sid9} (non éligible) : « Ne pas participer » mémorisé (dossier hors offre, statut Abandonné, exclu des offres actives)")
    pg.click('[data-b21d-prendre]');pg.click('[data-b21d-choix="participer"]');w9=len(W());pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(500)
    chk(len(W())==w9 and ST("fx-dec~"+sid9)["v"]=="No-Go" and "Participation impossible" in last(),f"{sid9} : « Participer » sur ce dossier reste refusé par la règle d'éligibilité (aucun contournement)")
    ev("()=>{B21D.dec=null;render();}")
    # blocage d'éligibilité (règle existante, état simulé dans la page de test)
    sel("siditrav");w4=len(W())
    ev("""()=>{window.__ce8=compatEval;compatEval=function(id,a,sid){const v=window.__ce8(id,a,sid);if(sid==='siditrav'){const c=(v.crits||[]).map(x=>Object.assign({},x));c.push({lab:'Qualification et classification',k:'Qualification & classification',e:'ko',motif:'justificatif échu le 01/01/2026, exigée pour ce marché (test)',src:'Coffre-fort EAIOS (test)',attrib:false});return Object.assign({},v,{crits:c});}return v;};render();}""")
    G1=ev("()=>({e:document.querySelector('[data-b21d-elig]').dataset.b21dElig,t:document.querySelector('[data-b21d-elig]').innerText,n:+document.querySelector('[data-b21d-f=\"non\"]').dataset.b21dFn,b:[...document.querySelectorAll('[data-b21d-item=\"siditrav\"] [data-b21d-badge]')].map(x=>x.innerText)})")
    pg.click('[data-b21d-prendre]');pg.click('[data-b21d-choix="participer"]');pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(400)
    NN=ev("""()=>{const a=S.ao['fx-dec'],X=b21dSibs('fx-dec',a);return SOC.map(z=>{const e=b21dEval('fx-dec',a,z.sid,X.find(x=>x.sid===z.sid)||null);return[z.sid,e.el.k,e.el.non.map(r=>r.t+' | '+(r.src||'')).join(' ; ')]}).filter(x=>x[1]==='non')}""")
    chk(all(x[0]=="siditrav" or ("article 27" in x[2] or "décret" in x[2]) for x in NN),f"autres « Non éligible » éventuels : uniquement par la règle art. 27 existante, sourcée ({[(x[0],x[2][:70]) for x in NN if x[0]!='siditrav']})")
    chk(G1["e"]=="non" and "Non éligible" in G1["t"] and "Source" in G1["t"] and G1["n"]==len(NN) and any(x.replace("✕","").strip()=="Non éligible" for x in G1["b"]) and len(W())==w4 and "Participation impossible" in last(),"incompatibilité confirmée et sourcée : « Non éligible » (bande, badge, filtre) ; « Participer » refusé avec la raison, rien d'écrit")
    ev("()=>{compatEval=window.__ce8;B21D.dec=null;render();}")
    # consultation clôturée : lecture seule
    dec(pg,"fx-decc");w5=len(W());chk(pg.locator('[data-b21d-prendre]').count()==0 and pg.locator('[data-b21d-godec]').count()==0 and pg.locator('[data-b21d-declock2]').count()==1 and "lecture seule" in pg.inner_text("[data-b21d-decsec]"),"consultation clôturée : décision en lecture seule, pas de « Prendre une décision »")
    ev("()=>{B21D.dec={sid:'sakdat',v:'participer'};}");ev("()=>b21dConfirmer('fx-decc','sakdat')");pg.wait_for_timeout(300)
    chk(len(W())==w5 and "clôturée" in last() and ev("()=>S.ao['fx-decc'].decision.verdict")=="Go","clôturée : confirmation directe refusée, décision existante conservée")
    # ===== b21d-10 =====
    dec(pg,"fx-dec");sel("sakdat");w10=len(W());st0=ev("()=>S.ao['fx-dec'].statut")
    L10=ev("()=>({det:[...document.querySelectorAll('[data-b21d] details')].map(d=>d.innerText.slice(0,40)).filter(t=>/Statut administratif/.test(t)).length,chips:[...document.querySelectorAll('[data-b21d] button')].filter(b=>['À examiner','Déposé','Attribué','Non retenu'].includes(b.innerText.trim())).length,st:(document.querySelector('[data-b21d-statut]')||{}).innerText||''})")
    AD=ev("()=>{const o=aoDecision('fx-dec',S.ao['fx-dec']);return{lec:o.includes('data-statut-lecture'),btn:/>(Attribué|Déposé|Non retenu)<\/button>/.test(o)}}")
    ev("()=>decide('fx-dec','Go')");ev("()=>decide('fx-dec~siditrav','No-Go')");pg.wait_for_timeout(300)
    chk(L10["det"]==0 and L10["chips"]==0 and "ne se modifie pas directement" in L10["st"] and AD=={"lec":True,"btn":False},f"Décision : plus de changement libre de statut ; état du dossier affiché en lecture seule ({L10['st'][:60]}…) ; ancien bloc aoDecision en lecture")
    chk(len(W())==w10 and ev("()=>S.ao['fx-dec'].statut")==st0 and ev("()=>S.ao['fx-dec~siditrav'].decision.verdict")=="Go" and "Décision d'Ahmed" in last(),"ancien gestionnaire decide() : n'enregistre plus rien, ne change ni décision ni société (renvoi vers la décision B2.1)")
    # note des moyens : dépend des données de la société ; rédaction par la Préparation
    ev("()=>{window.__refs=JSON.stringify(D0('sakdat').references||null);D0('sakdat').references=[{mo:'MO FICTIF',objet:'Prestation fictive (test)'}];render();}")
    A1=ev("()=>({m:!!document.querySelector('[data-b21d-panel] [data-b21d-doc=\"moyens\"]'),a:[...document.querySelectorAll('[data-b21d-alrdoc]')].map(x=>x.dataset.b21dAlrdoc)})")
    ev("()=>{S.ao['fx-dec'].noteMoyens={soc:'sakdat',html:'<p>texte fictif</p>'};render();}");A2=ev("()=>({a:[...document.querySelectorAll('[data-b21d-alrdoc]')].map(x=>x.dataset.b21dAlrdoc),r:(document.querySelector('[data-b21d-rien]')||{dataset:{}}).dataset.b21dRien,t:document.querySelector('[data-b21d-acv]').innerText,p:!!document.querySelector('[data-b21d-acv] [data-b21d-prepgo]')})")
    ev("()=>{delete S.ao['fx-dec'].noteMoyens;const r=JSON.parse(window.__refs);if(r)D0('sakdat').references=r;else delete D0('sakdat').references;render();}")
    chk(not A1["m"] and "moyens" in A1["a"] and "moyens" not in A2["a"] and A2["r"]=="1" and "Rien à compléter ici" in A2["t"] and "ne signifie ni offre prête au dépôt" in A2["t"] and A2["p"] and len(W())==w10,"note des moyens avec les données société présentes : pas de carte ; besoins CPS non établis → alerte ; note rédigée par la Préparation et rien d'autre → « Rien à compléter ici » + « Ouvrir Préparation » (sans prétendre prêt au dépôt) (état simulé en mémoire)")
    sel("alwaad-ataib");OUV();M3=ev("()=>{const d=document.querySelector('[data-b21d-panel] [data-b21d-doc=\"moyens\"]'),q=document.querySelector('[data-b21d-panel] [data-b21d-dk=\"proof\"][data-b21d-doc=\"refs\"]');return{k:d.dataset.b21dDk,ref:(d.querySelector('[data-b21d-aref]')||{dataset:{}}).dataset.b21dAref,r:q?q.querySelector('[data-b21d-renseigner]').dataset.b21dRenseigner:null,src:q?!!q.querySelector('details.b21d-rcs'):false,cor:q?q.innerText.includes('À corriger dans : coffre de ALWAAD ATAIB'):false}}")
    chk(M3=={"k":"miss","ref":"refs","r":"Attestations de bonne exécution","src":True,"cor":True},f"références manquantes : une seule carte preuve (Env. 1 technique, source RC repliable, correction au coffre d'ALWAAD) ; la note des moyens y renvoie (pas de doublon) {M3}")
    pg.click('[data-b21d-panel] [data-b21d-dk="proof"][data-b21d-doc="refs"] [data-b21d-renseigner]');pg.wait_for_timeout(500)
    chk(ev("()=>[S.dept,SOC[S.cur]&&SOC[S.cur].sid,(document.querySelector('.piece.b21d-cible .nm')||{}).textContent]")==["coffre","alwaad-ataib","Attestations de bonne exécution"],"« Vérifier au coffre » (carte preuve) : coffre d'ALWAAD, pièce références mise en vue")
    # accordéon : replier enregistre d'abord, aucune perte ; « Aller au champ »
    dec(pg,"fx-dec");sel("build-chantier");pg.click('[data-b21d-dtog="dsh"]');pg.wait_for_timeout(250);w11=len(W())
    pg.click('[data-b21d-doc="dsh"] [data-b21d-pf="build-chantier|tel"]');pg.keyboard.type("0612121212",delay=30);cc=ev("()=>[document.activeElement.value,document.activeElement.selectionStart]")
    pg.click('[data-b21d-dtog="dsh"]');pg.wait_for_timeout(800)
    chk(cc==["0612121212",10] and ev("()=>window.__DB.societes['build-chantier'].profil.tel")=="0612121212" and ev("()=>document.querySelector('[data-b21d-doc=\"dsh\"]').dataset.b21dDopen")=="0" and [w for w in W()[w11:] if w[1]=="societes/build-chantier"]==[["update","societes/build-chantier"]],"replier une pièce pendant la saisie : la valeur est d'abord enregistrée (aucun brouillon perdu), curseur stable pendant la frappe")
    pg.click('[data-b21d-dtog="ae"]');pg.wait_for_timeout(250);pg.click('[data-b21d-doc="ae"] [data-b21d-goto="build-chantier|rib"]');pg.wait_for_timeout(400)
    chk(ev("()=>[document.querySelector('[data-b21d-doc=\"dsh\"]').dataset.b21dDopen,document.activeElement&&document.activeElement.dataset.b21dPf]")==["1","build-chantier|rib"],"« Aller au champ » (AE → DH) : ouvre la pièce et place le focus dans l'unique saisie du RIB")
    # en-tête sticky : identité et accès à la décision, clavier ; aucune écriture
    w12=len(W());stk=ev("()=>getComputedStyle(document.querySelector('[data-b21d-sticky]')).position")
    pg.focus('[data-b21d-godec]');pg.keyboard.press("Enter");pg.wait_for_timeout(700)
    G=ev("()=>({open:!!document.querySelector('#b21d-dform'),f:document.activeElement&&document.activeElement.getAttribute('role'),ch:[...document.querySelectorAll('[data-b21d-choix]')].map(b=>b.getAttribute('aria-checked'))})")
    pg.click('[data-b21d-godec]');pg.wait_for_timeout(500);G2=ev("()=>!!document.querySelector('#b21d-dform')")
    chk(stk=="sticky" and G["open"] and G["f"]=="radio" and G["ch"]==["false","false","false"] and G2 and len(W())==w12,"en-tête sticky (nom, badges, « Prendre une décision ») : au clavier, ouvre le vrai bloc décision et place le focus sur le premier choix ; aucun choix ni écriture ; second appui ne referme rien")
    ev("()=>{B21D.dec=null;render();}")
    # couleurs et icônes distinctes ; filtres orthogonaux expliqués
    CL=ev("()=>{const m={};document.querySelectorAll('[data-b21d-badge]').forEach(b=>{m[b.dataset.b21dBadge]=b.className.split(' ').pop()+'|'+b.innerText.trim()[0]});return{m,h:(document.querySelector('[data-b21d-fhint]')||{}).innerText||''}}")
    chk(CL["m"].get("comp","").startswith("b21d-or|✎") and CL["m"].get("verif","").startswith("b21d-ye|?") and (CL["m"].get("non") or "b21d-ko|✕").startswith("b21d-ko|✕") and "plusieurs filtres" in CL["h"],f"couleurs et icônes : orange ✎ infos société, jaune ? éligibilité à vérifier, rouge ✕ incompatibilité, vert ✓ prouvée ; « Une société peut apparaître dans plusieurs filtres » {CL['m']}")
    # ===== E. Note, Résultat, B3.1 =====
    dec(pg,"fx-dec");ev("()=>{window.__nNote=0;const o1=vNoteB21,o2=aoNote;vNoteB21=function(){window.__nNote++;return o1.apply(this,arguments);};aoNote=function(){window.__nNote++;return o2.apply(this,arguments);};}");render_=ev("()=>{render();return window.__nNote}")
    chk(render_==0 and ev("()=>document.querySelectorAll('[data-b21],[data-b21-pdf]').length")==0 and ev("()=>document.getElementById('mpn-h').innerText.trim()")=="Décision d'Ahmed","vue Décision : la note d'analyse n'est ni calculée ni rendue ; titre « Décision d'Ahmed »")
    pg.click('[data-b21d-tab="note"]');pg.wait_for_selector("[data-b21]",timeout=15000);pg.wait_for_timeout(300)
    chk(ev("()=>[S.aoId,document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue]")==["fx-dec","MP-B2.1|note"],"onglet « Note d'analyse » : vraie vue Note du même dossier")
    pg.click("[data-b21-dec]");pg.wait_for_selector("[data-b21d]",timeout=15000);pg.wait_for_timeout(300);chk(ev("()=>document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue")=="MP-B2.1|dec","retour à la Décision depuis la note")
    pg.click('[data-b21d-tab="res"]');pg.wait_for_timeout(500)
    chk(ev("()=>[document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue,(document.querySelector('[data-b21d-apres]')||{dataset:{}}).dataset.b21dApres]")==["MP-B4.2|res","conditionnel"],"onglet « Résultat » : vue B4.2 avec la section après attribution (b21d-6)")
    ouvrir(pg,"fx-dec");b6=ev("()=>{const E=b31Etat('fx-dec',S.ao['fx-dec']);return{n:E.T.n,p:S.bpx['fx-dec'].p,v:!!document.querySelector('[data-b31]')}}")
    chk(b6["v"] and b6["n"]==2 and b6["p"]=={"0-0":1111.11,"0-1":22.22},"B3.1 intact : chiffrage du dossier et prix fictifs inchangés")
    # ===== F. dossier réel BG : lecture seule =====
    dec(pg,BG);nb=ev("()=>document.querySelectorAll('[data-b21d-item]').length");pg.screenshot(path=f"{OUT}/reel_bg_lecture.png")
    reel1=ev("ids=>JSON.stringify(ids.map(i=>[S.ao[i].decision||null,S.ao[i].statut,S.ao[i].soc,S.ao[i].decisionHist||null]))",REELS)
    chk(nb==9 and reel0==reel1 and not ecr_reel(pg) and not errs,f"dossier réel BG (base simulée) : 9 sociétés en lecture, décisions inchangées, aucune écriture réelle, aucune erreur {errs[:2]}")
    dec(pg,"fx-dec");sel("alwaad-ataib");pg.screenshot(path=f"{OUT}/fx_dec_1440.png",full_page=True);ctx.close()
    # ===== b21d-11 : emplacement RC honnête, Préparation intacte, dernier manque résolu =====
    ctx2,pg,errs2=demarrer(b,1440,1000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");dec(pg,"fx-dec");sel("alwaad-ataib")
    AK=lambda:ev("()=>Object.keys(S.ao).length")
    ev("()=>{window.__plis=S.rc['fx-dec'].plis;delete S.rc['fx-dec'].plis;render();}")
    U1=ev("()=>({g:[...document.querySelectorAll('[data-b21d-panel] [data-b21d-loc]')].map(g=>[g.dataset.b21dLoc,g.querySelector('.b21d-gh').innerText]),p:[...document.querySelectorAll('[data-b21d-panel] [data-b21d-path]')].map(x=>x.innerText)})")
    ev("()=>{S.rc['fx-dec'].plis=window.__plis;render();}")
    chk(len(U1["g"])==1 and U1["g"][0][0]=="?" and "emplacement dans le pli à confirmer" in U1["g"][0][1].lower() and U1["p"] and all("Enveloppe" not in x and "emplacement dans le pli à confirmer" in x for x in U1["p"]),f"RC sans structure de plis lue : « Emplacement dans le pli à confirmer », aucune enveloppe supposée {U1['g']}")
    ev("()=>{window.__pc=S.rc['fx-dec'].pieces;S.rc['fx-dec'].pieces=[];render();}")
    U2=ev("()=>({inc:!!document.querySelector('[data-b21d-rcinc]'),rien:!!document.querySelector('[data-b21d-rien]'),c:document.querySelectorAll('[data-b21d-panel] [data-b21d-dk]').length,t:document.querySelector('[data-b21d-acv]').innerText})")
    ev("()=>{S.rc['fx-dec'].pieces=window.__pc;render();}")
    chk(U2["inc"] and not U2["rien"] and U2["c"]==0 and "rien n'est supposé complet" in U2["t"],"exigences du RC inconnues : signalé, ni « Rien à compléter » ni pièce supposée")
    k0=AK();w0=len(W());sel("build-chantier")
    NB=ev("()=>({pn:!!document.querySelector('[data-b21d-prepnone]'),pg:!!document.querySelector('[data-b21d-acv] [data-b21d-prepgo]'),ctx:document.querySelector('[data-b21d-acv] > .b21d-src').innerText})")
    chk(NB["pn"] and not NB["pg"] and "aucun dossier" in NB["ctx"] and AK()==k0 and len(W())==w0,"société sans dossier : pas de lien Préparation (créée seulement à la confirmation), rien n'est créé en consultant")
    PR=ev("""()=>{const a=S.ao['fx-dec'],X=b21dSibs('fx-dec',a).find(x=>x.sid==='alwaad-ataib'),d=b21dDocs('fx-dec',a,'alwaad-ataib',X);return{std:d.docs.map(z=>z.std),np:S.rc['fx-dec'].pieces.length}}""")
    ev("()=>b21dAller('fx-dec~siditrav','MP-B3.2','pieces')");pg.wait_for_timeout(700);TP=pg.inner_text("#view")
    chk(all(x in PR["std"] for x in ("caution","bpu","cpsrc","moyens","dsh","ae")) and PR["np"]==NP and "cautionnement provisoire" in TP and "Bordereau des prix" in TP,f"rien n'est effacé : pièces du RC ({PR['np']}) et documents (caution, BPU, CPS/RC, note des moyens) toujours calculés et affichés dans la Préparation (B3.2)")
    dec(pg,"fx-dec");SC="structure-chantier";sel(SC)
    ev("s=>{const g=[{nom:'GÉRANT FICTIF QA',qualite:'Gérant',signe:'unique'}];window.__DB.societes[s]=window.__DB.societes[s]||{};window.__DB.societes[s].profil=Object.assign(window.__DB.societes[s].profil||{},{gerants:g});const d=D0(s);d.profil=Object.assign({},d.profil||{},{gerants:g});try{socApply(s)}catch(e){};render();}",SC)
    OUV();VAL={"tel":"0612345678","fax":"0522000000","mail":"qa@exemple.ma","rib":"123456789012345678901234","ice":"123456789012345","capital":"100000"}
    FD=ev("s=>[...document.querySelectorAll('[data-b21d-doc=\"dsh\"] input[data-b21d-pf]')].map(i=>i.dataset.b21dPf.split('|')[1])",SC)
    FA=ev("s=>[...document.querySelectorAll('[data-b21d-doc=\"ae\"] input[data-b21d-pf]')].map(i=>i.dataset.b21dPf.split('|')[1])",SC)
    nA=ev("()=>document.querySelectorAll('[data-b21d-doc=\"ae\"] [data-b21d-autre]').length")
    k1=AK();w1=len(W())
    for k in FD[:-1]:
        q=f'[data-b21d-doc="dsh"] [data-b21d-pf="{SC}|{k}"]';pg.click(q);pg.keyboard.type(VAL.get(k,"VALEUR FICTIVE QA"));pg.keyboard.press("Tab");pg.wait_for_timeout(900)
    kl=FD[-1];pg.click(f'[data-b21d-doc="dsh"] [data-b21d-pf="{SC}|{kl}"]');pg.keyboard.type(VAL.get(kl,"VALEUR FICTIVE QA"))
    AI=f'[data-b21d-doc="ae"] [data-b21d-pf="{SC}|{FA[0]}"]';pg.click(AI);pg.keyboard.type("BAN",delay=40);pg.wait_for_timeout(1000)
    Z=ev("i=>({dh:!!document.querySelector('[data-b21d-panel] [data-b21d-doc=\"dsh\"]'),f:document.activeElement===document.querySelector(i),v:document.activeElement.value,c:document.activeElement.selectionStart,sum:(document.querySelector('[data-b21d-sum]')||{dataset:{}}).dataset.b21dSum})",AI)
    pg.keyboard.type("QUE QA",delay=30);Z2=ev("i=>[document.activeElement===document.querySelector(i),document.activeElement.value]",AI)
    pr=ev("s=>window.__DB.societes[s].profil",SC)
    chk(FD and all(pr.get(k)==VAL.get(k,"VALEUR FICTIVE QA") for k in FD) and not Z["dh"] and Z["f"] and Z["v"]=="BAN" and Z["c"]==3 and Z2==[True,"BANQUE QA"] and AK()==k1 and not [w for w in W()[w1:] if w[1].startswith("ao/")],f"dernier manque de la DH confirmé par la base : la carte disparaît ; la saisie en cours dans l'AE garde focus, valeur et curseur ; aucune décision ni dossier créé (DH {FD}, AE {FA}, {Z})")
    if nA==0:
        for k in FA[:-1]:
            q=f'[data-b21d-doc="ae"] [data-b21d-pf="{SC}|{k}"]'
            if not ev("q=>!!document.querySelector(q)",q):continue
            pg.click(q);pg.keyboard.press("Control+A");pg.keyboard.type(VAL.get(k,"BANQUE QA") if k!=FA[0] else "BANQUE QA");pg.keyboard.press("Tab");pg.wait_for_timeout(900)
        ql=f'[data-b21d-doc="ae"] [data-b21d-pf="{SC}|{FA[-1]}"]'
        if ev("q=>!!document.querySelector(q)",ql):pg.click(ql);pg.keyboard.press("Control+A");pg.keyboard.type(VAL.get(FA[-1],"BANQUE QA"))
        pg.keyboard.press("Tab");pg.wait_for_timeout(1200)
        Z3=ev("()=>({ae:!!document.querySelector('[data-b21d-panel] [data-b21d-doc=\"ae\"]'),body:document.activeElement===document.body,id:document.activeElement&&document.activeElement.id})")
        chk(not Z3["ae"] and not Z3["body"],f"dernière information de l'AE (Tab) : la carte disparaît, le focus n'est pas perdu ({Z3})")
    ctx2.close()
    # ===== G. mobile / sombre =====
    for (w,h,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre"),(1440,900,"dark","1440_sombre")):
        c=b.new_context(viewport={"width":w,"height":h},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q.wait_for_timeout(800);dec(q,"fx-dec")
        v1=q.evaluate("()=>{const l=document.querySelector('.b21d-l'),p=document.querySelector('.b21d-p');return{l:getComputedStyle(l).display!=='none',p:getComputedStyle(p).display!=='none',ov:document.documentElement.scrollWidth-document.documentElement.clientWidth}}")
        q.click('[data-b21d-item="alwaad-ataib"]');q.wait_for_timeout(300);q.click('[data-b21d-dtog="dsh"]');q.wait_for_timeout(300)
        v2=q.evaluate("()=>{const l=document.querySelector('.b21d-l'),p=document.querySelector('.b21d-p'),P=p.getBoundingClientRect(),F=[...p.querySelectorAll('[data-b21d-fr] input')].every(i=>{const r=i.getBoundingClientRect();return r.left>=P.left-1&&r.right<=P.right+1&&r.height>=30});return{l:getComputedStyle(l).display!=='none',p:getComputedStyle(p).display!=='none',ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,F,back:getComputedStyle(document.querySelector('[data-b21d-back]')).display!=='none'}}")
        if w<600:
            chk(v1["l"] and not v1["p"] and not v2["l"] and v2["p"] and v2["back"] and v2["F"] and v1["ov"]<=1 and v2["ov"]<=1,f"{tag} : sélecteur de sociétés puis panneau (bouton « ← Sociétés »), champs lisibles, aucun débordement ({v2})")
            q.locator(".b21d-p").screenshot(path=f"{OUT}/panneau_{tag}.png");q.click('[data-b21d-back]');q.wait_for_timeout(250)
            chk(q.evaluate("()=>getComputedStyle(document.querySelector('.b21d-l')).display!=='none'&&document.activeElement&&document.activeElement.dataset.b21dItem==='alwaad-ataib'"),f"{tag} : retour à la liste, focus sur la société")
            q.locator(".b21d-l").screenshot(path=f"{OUT}/liste_{tag}.png")
        else:
            chk(v1["l"] and v1["p"] and v2["F"] and v2["ov"]<=1 and not e,f"{tag} : liste et panneau côte à côte, champs lisibles, aucun débordement")
            q.screenshot(path=f"{OUT}/fx_dec_{tag}.png",full_page=True)
        q.evaluate("()=>{B21D.ui.mob='panel';render();}");q.wait_for_timeout(150)
        ctr=q.evaluate("""()=>{const L=c=>{const m=c.match(/[\d.]+/g).map(Number),f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)};return 0.2126*f(m[0])+0.7152*f(m[1])+0.0722*f(m[2])};
          const bg=el=>{let e=el;while(e){const c=getComputedStyle(e).backgroundColor;if(c&&!/rgba\(0, 0, 0, 0\)|transparent/.test(c)&&!(c.startsWith('rgba')&&+c.split(',')[3].replace(')','')<0.5))return c;e=e.parentElement;}return'rgb(255,255,255)'};
          const r=(a,b)=>{const x=L(a),y=L(b);return(Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)};const n=document.querySelector('[data-b21d-item][aria-current="true"] .b21d-in');if(!n)return 99;return Math.round(r(getComputedStyle(n).color,bg(n.closest('.b21d-it')))*10)/10}""")
        chk(ctr>=4.5,f"{tag} : société sélectionnée lisible (contraste {ctr})")
        chk(not e,f"{tag} : aucune erreur JavaScript {e[:2]}");c.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
