"""Recette mph-1 · accueil du département Marchés publics. Banc fictif de qa_b21dec (base simulée locale) ; les seuls ajouts
(dossiers FX-MPH-* pour les dates, états chargement/erreur) sont faits en mémoire de la page de test. Aucune écriture attendue."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
ACC="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnAller({});render();}"
# recalcul indépendant (règles annoncées) : horloge de Casablanca comparée à la minute, statuts, dédoublonnage dossier société
EXP="""(soc)=>{const tz='Africa/Casablanca',P=d=>{const p=new Intl.DateTimeFormat('en-US',{timeZone:tz,hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).formatToParts(d),g=t=>+p.find(x=>x.type===t).value;return[g('year'),g('month'),g('day'),g('hour')%24,g('minute')];};
 const n=P(new Date()),nk=((n[0]*100+n[1])*100+n[2])*1e4+n[3]*100+n[4];const seen=new Set(),O=[],E=[];
 Object.entries(S.ao).forEach(([id,a])=>{if(!a||!a.soc||!['À examiner','En préparation'].includes(a.statut))return;if(soc&&a.soc!==soc)return;
   let pas=false;const m=String(a.lim||'').match(/^(\\d{4})-(\\d{2})-(\\d{2})/);if(m){const x=String(a.heure||'').match(/(\\d{1,2})\\s*[hH:]\\s*(\\d{2})?/),h=x&&+x[1]<24?+x[1]:23,mi=x&&+x[1]<24?+(x[2]||0):59;const k=((+m[1]*100+ +m[2])*100+ +m[3])*1e4+h*100+mi;pas=k<nk;}
   if(pas){E.push(id);return;}const kk=(a.base||id)+'|'+a.soc;if(seen.has(kk))return;seen.add(kk);O.push(id);});
 const dec=O.filter(id=>{const a=S.ao[id];return a.statut==='À examiner'&&(!a.decision||a.decision.verdict==='À reprendre');}),dep=O.filter(id=>S.ao[id].statut==='En préparation');
 const U={},per={},inc=[];O.forEach(id=>{const a=S.ao[id],base=a.base&&S.ao[a.base]?a.base:id,e=b21dEval(base,S.ao[base],a.soc,{oid:id,sid:a.soc,a});if(!e.dc.rcOk){inc.push(id);return;}const K=new Set();
   e.dc.docs.forEach(d=>{if(!['miss','redac','ready'].includes(d.kind))return;d.fields.filter(f=>!f.fait).forEach(f=>K.add('f:'+f.k));d.autres.forEach(x=>K.add(x.vk?'v:'+x.vk:'t:'+x.t));});
   e.dc.proofs.filter(z=>z.k!=='joint').forEach(z=>K.add(z.vk?'v:'+z.vk:'p:'+z.std));per[id]=K.size;if(K.size){U[a.soc]=U[a.soc]||new Set();K.forEach(k=>U[a.soc].add(k));}});
 return{open:O,dec,dep,info:Object.values(U).reduce((s,x)=>s+x.size,0),soc:Object.fromEntries(Object.entries(U).map(([k,v])=>[k,v.size])),per,inc,ech:E.filter(id=>S.ao[id].statut==='En préparation')};}"""
CARDS="()=>Object.fromEntries([...document.querySelectorAll('[data-mph-card]')].map(c=>[c.dataset.mphCard,c.dataset.mphN]))"
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");AK=lambda:ev("()=>Object.keys(S.ao).length")
    w0=len(W());k0=AK();ev(ACC);pg.wait_for_timeout(500)
    # ===== A. accueil : composition, sans bloc employé ni contenu de maquette =====
    T=pg.inner_text("#view")
    chk(ev("()=>!!document.querySelector('[data-mph]')") and "Marchés publics" in T and "Pilotez vos appels d'offres, de la veille au résultat." in T and not re.search(r"Nommer cet employé|Certifi|En observation|Ombre|MAQUETTE|DONNÉES D'EXEMPLE|Des projets au service|AO EX-0",T),"accueil : titre, sous-titre ; bloc Analyste AO / nomination / certification absent ; aucun contenu de maquette")
    chk([x.strip() for x in ev("()=>[...document.querySelectorAll('.mph-sh h2,.mph-qa h2')].map(h=>h.innerText)")]==["Vos priorités","Dossiers prioritaires","Services et bureaux","Accès rapides"],"sections dans l'ordre de la maquette : Vos priorités, Dossiers prioritaires, Services et bureaux, Accès rapides")
    chk(ev("()=>{const d=document.querySelector('[data-side-tab=\"departements\"]');return d&&d.getAttribute('aria-current')==='true'}") and ev("()=>!!document.querySelector('[data-side-dept=\"ao\"][aria-current]')"),"barre latérale : « Départements » marqué comme rubrique parente, « Marchés publics » courant (shell inchangé ailleurs)")
    # ===== B. compteurs réels, unités, périmètre =====
    X=ev(EXP,"");C=ev(CARDS)
    chk(C=={"dec":str(len(X["dec"])),"info":str(X["info"]),"depot":str(len(X["dep"]))},f"compteurs = recalcul indépendant (ouverts, Casablanca, dédoublonnés) : décisions {len(X['dec'])}, données société {X['info']}, dépôts {len(X['dep'])} ; non évalués {len(X['inc'])} {C}")
    chk(len(X["inc"])==0 or ev("()=>+(document.querySelector('[data-mph-inc]')||{dataset:{mphInc:0}}).dataset.mphInc")==len(X["inc"]),f"dossiers au RC non relevé : signalés « non évalués », jamais comptés comme complets ({len(X['inc'])})")
    chk(not ev("()=>[...document.querySelectorAll('.mph-pc,.mph-pc *')].some(e=>/b21d-ok|p-grn|mph-ok/.test(e.className&&e.className.baseVal===undefined?e.className:''))"),"aucun vert sur les cartes de tâches")
    pg.click('[data-mph-go="dec"]');pg.wait_for_timeout(400)
    L1=ev("()=>({n:+document.querySelector('[data-mph-lc]').dataset.mphLc,ids:[...document.querySelectorAll('[data-mph-row]')].map(r=>r.dataset.mphRow),h:document.getElementById('mpn-h').innerText})")
    chk(L1["n"]==len(X["dec"]) and sorted(L1["ids"])==sorted(X["dec"]) and L1["h"]=="Décisions à prendre","« Examiner » : liste exactement égale au compteur (mêmes dossiers)")
    if L1["ids"]:
        i0=L1["ids"][0];pg.click(f'[data-mph-row="{i0}"] [data-mph-open]');pg.wait_for_timeout(600)
        chk(ev("()=>[S.aoId,document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue]")==[i0,"MP-B2.1|dec"],"ligne « Examiner » : ouvre ce dossier sur la décision B2.1 (aucun choix fait)")
        pg.click('[data-mpn-retour]');pg.wait_for_timeout(500);chk(ev("()=>[S.aoId,!!document.querySelector('[data-mph-liste=\"dec\"]')]")==[None,True],"retour du dossier : revient à la liste « Décisions à prendre »")
    pg.click('[data-mph-retour]');pg.wait_for_timeout(300)
    pg.click('[data-mph-go="depot"]');pg.wait_for_timeout(400)
    L3=ev("()=>({n:+document.querySelector('[data-mph-lc]').dataset.mphLc,ids:[...document.querySelectorAll('[data-mph-row]')].map(r=>r.dataset.mphRow),e:+((document.querySelector('[data-mph-lech]')||{dataset:{}}).dataset.mphLech||0)})")
    chk(L3["n"]==len(X["dep"]) and sorted(L3["ids"])==sorted(X["dep"]) and L3["e"]==len(X["ech"]),f"« Préparer » : liste = dépôts à finaliser ; échus sans dépôt listés à part, hors compteur ({len(X['ech'])})")
    pg.click('[data-mph-retour]');pg.wait_for_timeout(300);pg.click('[data-mph-go="info"]');pg.wait_for_timeout(500)
    L2=ev("()=>({n:+document.querySelector('[data-mph-lc]').dataset.mphLc,s:Object.fromEntries([...document.querySelectorAll('[data-mph-lsoc]')].map(x=>[x.dataset.mphLsoc,+x.dataset.mphLn])),lab:[...document.querySelectorAll('[data-mph-lsoc]')].map(x=>x.querySelector('.mph-mut').innerText.split(' · '))})")
    chk(L2["n"]==X["info"] and L2["s"]==X["soc"] and sum(L2["s"].values())==X["info"] and all(len(l)==len(set(l)) for l in L2["lab"]),f"« Compléter » : données uniques par société (RIB DH/AE compté une fois), somme = compteur {L2['s']}")
    # recoupement avec la destination : le résumé « À compléter / vérifier » (b21d-11) du dossier ouvert
    first=ev("()=>{const b=document.querySelector('[data-mph-lsoc] [data-mph-open]');return b?b.dataset.mphOpen:null}")
    if first:
        pg.click(f'[data-mph-lsoc] [data-mph-open="{first}"]');pg.wait_for_timeout(800)
        sm=ev("()=>(document.querySelector('[data-b21d-sum]')||{dataset:{}}).dataset.b21dSum||''")
        chk(ev("()=>S.aoId")==first and sm.split("|")[-1]==str(X["per"][first]),f"recoupement : le panneau Décision « À compléter / vérifier » du dossier ouvert annonce les mêmes données ({sm} ; accueil {X['per'][first]})")
    ev(ACC);pg.wait_for_timeout(300)
    # ===== C. filtre société et recherche =====
    socs=ev("()=>SOC.map(z=>z.sid)");tested=0
    for s in [x for x in socs if x in ("sakdat","alwaad-ataib","siditrav")]:
        pg.select_option("#mph-soc",s);pg.wait_for_timeout(400);Xs=ev(EXP,s);Cs=ev(CARDS)
        RR=ev("()=>[...document.querySelectorAll('[data-mph-row]')].map(r=>S.ao[r.dataset.mphRow].soc)")
        chk(Cs=={"dec":str(len(Xs["dec"])),"info":str(Xs["info"]),"depot":str(len(Xs["dep"]))} and all(r==s for r in RR) and ev("()=>document.activeElement&&document.activeElement.id")=="mph-soc",f"filtre société {s} : compteurs et dossiers prioritaires de cette société seulement {Cs} ; focus conservé");tested+=1
    pg.select_option("#mph-soc","");pg.wait_for_timeout(300)
    pg.click("#mph-q");pg.keyboard.type("FX-DEC",delay=20);pg.wait_for_timeout(300)
    RA=ev("()=>[...document.querySelectorAll('[data-mph-rao]')].map(b=>b.dataset.mphRao)");chk(RA and all(ev("i=>String(S.ao[i].ref).includes('FX-DEC')",i) for i in RA) and ev("()=>document.activeElement.id")=="mph-q","recherche « FX-DEC » : AO correspondants, focus conservé dans le champ")
    pg.keyboard.press("Escape");pg.wait_for_timeout(200);chk(ev("()=>[MPH.q,!!document.querySelector('.mph-res')]")==["",False],"Échap : recherche effacée")
    pg.fill("#mph-q","juridique");pg.wait_for_timeout(300);pg.click('[data-mph-rbur="MP-B2.2"]');pg.wait_for_timeout(400)
    chk(ev("()=>[MPN.vue,MPN.bur]")==["bur","MP-B2.2"],"recherche bureau « juridique » → bureau B2.2 (route existante)")
    ev(ACC);ev("()=>{MPH.q='';render();}");pg.fill("#mph-q","sakd");pg.wait_for_timeout(300);pg.click('[data-mph-rsoc="sakdat"]');pg.wait_for_timeout(300)
    chk(ev("()=>[MPH.soc,document.getElementById('mph-soc').value]")==["sakdat","sakdat"],"recherche société → filtre société synchronisé")
    pg.select_option("#mph-soc","");pg.wait_for_timeout(300)
    # ===== D. dates : Casablanca, heure connue/inconnue, échues, inconnues (dossiers FICTIFS en mémoire) =====
    ev("""()=>{const tz='Africa/Casablanca',f=d=>{const p=new Intl.DateTimeFormat('en-CA',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(d),g=t=>p.find(x=>x.type===t).value;return[g('year')+'-'+g('month')+'-'+g('day'),g('hour')+':'+g('minute')];};
      const o=(ms)=>f(new Date(Date.now()+ms)),A=(r,lim,h,st)=>({ref:r,obj:'Objet fictif '+r,soc:'riyada-build',statut:st||'À examiner',lim,heure:h,mo:'MO FICTIF'});
      const p1=o(30*60e3),p2=o(-2*60e3),p3=o(0),p5=o(-36*3600e3);
      S.ao['fx-mph-1']=A('FX-MPH-1',p1[0],p1[1]);S.ao['fx-mph-2']=A('FX-MPH-2',p2[0],p2[1],'En préparation');S.ao['fx-mph-3']=A('FX-MPH-3',p3[0],'');S.ao['fx-mph-4']=A('FX-MPH-4','','');S.ao['fx-mph-5']=A('FX-MPH-5',p5[0],'',"En préparation");
      S.ao['fx-mph-6']=A('FX-MPH-6',p1[0],p1[1],'Déposé');MPH.soc='riyada-build';render();}""");pg.wait_for_timeout(400)
    DT=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-mph-row]')].map(r=>[S.ao[r.dataset.mphRow].ref,r.querySelector('[data-l=\"Date limite\"]').innerText.replace(/\\n/g,' | ')]))")
    OR=ev("()=>[...document.querySelectorAll('[data-mph-row]')].map(r=>S.ao[r.dataset.mphRow].ref)")
    chk("Dans moins d'1 h" in DT.get("FX-MPH-1","") and re.search(r"\d\d/\d\d/\d{4} à \d\d:\d\d",DT.get("FX-MPH-1","")) and "heure non précisée" in DT.get("FX-MPH-3","") and "Aujourd'hui" in DT.get("FX-MPH-3","") and "FX-MPH-2" not in DT and "FX-MPH-5" not in DT and "FX-MPH-6" not in DT,f"dates : heure exacte et relatif (Casablanca) ; heure inconnue signalée ; échues et déposés exclus des priorités {DT}")
    ev("()=>{MPH.soc='';render();}");ev("()=>{MPH.soc='riyada-build';mphPrio('tous');}");pg.wait_for_timeout(300)
    OT=ev("()=>[...document.querySelectorAll('[data-mph-row]')].map(r=>[S.ao[r.dataset.mphRow].ref,r.querySelector('[data-l=\"Date limite\"]').innerText])")
    chk(OT and OT[-1][0]=="FX-MPH-4" and "Date limite inconnue" in OT[-1][1] and [x[0] for x in OT].index("FX-MPH-1")<[x[0] for x in OT].index("FX-MPH-3"),f"ordre : échéance la plus proche d'abord, date inconnue en dernier et affichée honnêtement {[x[0] for x in OT]}")
    ev("()=>{mphPrio('depot');}");pg.wait_for_timeout(300)
    chk(ev("()=>document.querySelector('[data-mph-lech]')&&document.querySelector('[data-mph-lech]').innerText.includes('FX-MPH-2')&&document.querySelector('[data-mph-lech]').innerText.includes('FX-MPH-5')"),"échus sans dépôt (heure dépassée de 2 min ; date d'hier sans heure) : hors compteur, listés comme lecture seule")
    # même calcul sous un autre fuseau du poste
    c2=b.new_context(viewport={"width":1440,"height":1000},timezone_id="America/New_York");c2.add_init_script(INIT);q2=c2.new_page();q2.goto(URL);q2.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q2.wait_for_timeout(800)
    q2.evaluate(ACC);q2.wait_for_timeout(400);q2.evaluate("()=>{mphPrio('tous');}");q2.wait_for_timeout(300)
    NY=q2.evaluate("()=>[...document.querySelectorAll('[data-mph-row]')].slice(0,3).map(r=>{const a=S.ao[r.dataset.mphRow];return[a.lim,a.heure,r.querySelector('[data-l=\"Date limite\"] small').innerText]})")
    chk(all(x[2].startswith(x[0][8:10]+"/"+x[0][5:7]+"/"+x[0][:4]) and (not x[1] or re.sub(r"[hH]",":",x[1]).split(":")[0].zfill(2) in x[2]) for x in NY),f"poste sur un autre fuseau (New York) : la date et l'heure affichées restent celles du marché (Casablanca) {NY}");c2.close()
    ev("()=>{['fx-mph-1','fx-mph-2','fx-mph-3','fx-mph-4','fx-mph-5','fx-mph-6'].forEach(k=>delete S.ao[k]);MPH.soc='';}");ev(ACC);pg.wait_for_timeout(300)
    # ===== E. dossiers prioritaires =====
    PR=ev("()=>[...document.querySelectorAll('[data-mph-row]')].map(r=>{const a=S.ao[r.dataset.mphRow];return[r.dataset.mphRow,a.base||r.dataset.mphRow,a.soc,[...r.querySelectorAll('td')].map(t=>t.dataset.l)]})")
    chk(1<=len(PR)<=5 and len({(x[1],x[2]) for x in PR})==len(PR) and all(x[3]==["Dossier","Société","Étape","À faire","Date limite","Action"] for x in PR) and all(x[0] in X["open"] for x in PR),f"dossiers prioritaires : 1 à 5 lignes, dossiers ouverts uniquement, dédoublonnés par dossier société, colonnes Dossier/Société/Étape/À faire/Date limite/Action ({len(PR)})")
    chk(ev("()=>{const b=document.querySelector('[data-mph-tous]');return b&&b.innerText.includes('Voir tous les dossiers')}"),"« Voir tous les dossiers »")
    ev("()=>{MPH.soc='__aucune__';render();}");chk(ev("()=>!!document.querySelector('[data-mph-vide]')&&!document.querySelector('[data-mph-row]')&&[...document.querySelectorAll('[data-mph-card]')].every(c=>c.dataset.mphN==='0')"),"aucun dossier ouvert (filtre sans résultat) : zéros honnêtes et état vide, pas d'exemples");ev("()=>{MPH.soc='';render();}")
    # ===== F. chargement / erreur =====
    ev("()=>{window.__st=S.aoState;S.aoState='attente';MPH.ck=null;render();}");LD=ev("()=>[[...document.querySelectorAll('[data-mph-card]')].map(c=>c.dataset.mphN),document.querySelector('[data-mph-etat]')&&document.querySelector('[data-mph-etat]').innerText]")
    ev("()=>{S.aoState='err';S.dbErr=Object.assign(S.dbErr||{},{ao:'réseau (test)'});render();}");ER=ev("()=>[document.querySelector('[data-mph-etat]').innerText,!!document.querySelector('[data-mph-card] .mph-cta')]")
    ev("()=>{S.aoState=window.__st;MPH.ck=null;render();}")
    chk(LD[0]==["","",""] and "Chargement" in (LD[1] or "") and "interrompue" in ER[0] and ER[1],"chargement : « — » et « Chargement des dossiers… » ; erreur : message explicite + « Recharger » (aucun zéro inventé)")
    # ===== G. services et bureaux : 14 routes, onglets, clavier =====
    TB=ev("()=>[...document.querySelectorAll('[data-mph-svc]')].map(t=>[t.dataset.mphSvc,t.getAttribute('role'),t.getAttribute('aria-selected')])")
    chk([x[0] for x in TB]==["MP-S1","MP-S2","MP-S3","MP-S4","MP-S5"] and all(x[1]=="tab" for x in TB) and [x[2] for x in TB].count("true")==1 and TB[1][2]=="true",f"cinq onglets S1–S5 (navigation, un seul ouvert : S2 par défaut)")
    pg.focus('[data-mph-svc="MP-S2"]');pg.keyboard.press("ArrowRight");pg.wait_for_timeout(200)
    chk(ev("()=>[MPH.svc,document.activeElement.dataset.mphSvc]")==["MP-S3","MP-S3"],"clavier : flèche droite → S3 sélectionné et focalisé")
    vus=[]
    for s in ["MP-S1","MP-S2","MP-S3","MP-S4","MP-S5"]:
        ev(ACC);ev(f"()=>{{MPH.svc='{s}';render();}}");ids=ev("()=>[...document.querySelectorAll('[data-mph-bur]')].map(b=>b.dataset.mphBur)")
        for bid in ids:
            ev(ACC);ev(f"()=>{{MPH.svc='{s}';render();}}");pg.click(f'[data-mph-bur="{bid}"]');pg.wait_for_timeout(250)
            ok=ev("i=>MPN.vue==='bur'&&MPN.bur===i&&document.getElementById('mpn-h').innerText.includes(MPD_BUR.find(b=>b.id===i).nom)",bid);vus.append((bid,ok))
    chk(len(vus)==14 and all(o for _,o in vus) and [b for b,_ in vus]==ev("()=>MPD_BUR.map(b=>b.id)"),f"14 bureaux (B1.1 ; B2.1–2.4 ; B3.1–3.4 ; B4.1–4.2 ; B5.1–5.3) : chacun ouvre sa vraie vue bureau")
    AC={}
    for k in ["dossiers","agenda","textes","equipe","coffre"]:
        ev(ACC);pg.wait_for_timeout(150);pg.click(f'[data-mph-acces="{k}"]');pg.wait_for_timeout(300);AC[k]=ev("()=>S.dept==='coffre'?'coffre':MPN.vue+':'+MPN.trans")
    chk(AC=={"dossiers":"trans:dossiers","agenda":"trans:agenda","textes":"trans:textes","equipe":"trans:equipe","coffre":"coffre"},f"accès rapides : vraies destinations {AC}")
    ev(ACC);pg.click('[data-mph-equipe]');pg.wait_for_timeout(250);e1=ev("()=>MPN.vue+':'+MPN.trans")
    ev(ACC);pg.click('[data-mph-deps]');pg.wait_for_timeout(250);e2=ev("()=>[S.dept,S.tab]")
    pg.click('[data-side-dept="ao"]');pg.wait_for_timeout(400);e3=ev("()=>!!document.querySelector('[data-mph]')")
    chk(e1=="trans:equipe" and e2==[None,"departements"] and e3,"lien discret « Équipe numérique » ; fil « Départements » ; retour à l'accueil depuis la barre latérale")
    chk(len(W())==w0 and AK()==k0 and not errs,f"navigation, filtres, recherche, listes : aucune écriture, aucun dossier créé, aucune erreur {errs[:2]}")
    ctx.close()
    # ===== H. responsive clair / sombre =====
    for (w,h,sch) in ((390,844,"light"),(390,844,"dark"),(615,900,"light"),(768,1000,"dark"),(1440,1000,"light"),(1440,1000,"dark")):
        tag=f"{w}{'_sombre' if sch=='dark' else ''}";c=b.new_context(viewport={"width":w,"height":h},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q.wait_for_timeout(800);q.evaluate(ACC);q.wait_for_timeout(500)
        M=q.evaluate("""()=>{const v=document.querySelector('.mph'),V=v.getBoundingClientRect(),out=[...v.querySelectorAll('.mph-pc,.mph-tw,.mph-tabs [role=tab],.mph-bc,.mph-act,.mph-qa,.mph-sel,.mph-srch')].filter(x=>{const r=x.getBoundingClientRect();return r.right>V.right+1||r.left<V.left-1}).length;
          const pc=[...v.querySelectorAll('.mph-pl')].map(x=>x.getBoundingClientRect().width);return{ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,out,pc:Math.min(...pc),menus:document.querySelectorAll('.mph nav[aria-label*=Services]').length,
          ink:getComputedStyle(document.querySelector('.mph-h1')).color,bg:getComputedStyle(document.querySelector('.mph-pc')).backgroundColor}}""")
        q.screenshot(path=f"{OUT}/mph_{tag}.png",full_page=True)
        dark=sch=="dark";lum=lambda c:sum(int(x) for x in re.findall(r"\d+",c)[:3])
        chk(M["ov"]<=1 and M["out"]==0 and M["pc"]>=100 and M["menus"]==0 and not e and ((lum(M["ink"])>lum(M["bg"])) if dark else (lum(M["ink"])<lum(M["bg"]))),f"{tag} : aucun débordement, cartes/onglets/bureaux dans la page, texte lisible, pas de second menu {M}")
        c.close()
    b.close()
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
