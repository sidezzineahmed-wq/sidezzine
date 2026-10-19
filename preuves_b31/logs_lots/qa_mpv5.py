"""Recette mpv-5 · B1.1 : fiche complète (résumé + sections repliables) sur les données publiées (complements_fiche).
Même ID que l'utilisateur (e5w/1041719), cas alloti (g3h/1044229), fiche ré-analysée (contact / pièces « pas encore lus »),
fiche sans compléments, contact « non publié » simulé en mémoire. Liens vérifiés sans clic (aucun formulaire soumis).
Mobile 390 px : sans débordement ni colonne étroite. Aucune écriture."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50&&S.enrState==='ok'"
CAT=json.load(open(os.path.join(SRV,"catalogue.json"),encoding="utf-8"));X={f"pmmp:{x['o']}:{x['r']}":x for x in CAT["items"]}
CF=json.load(open(os.path.join(SRV,"catalogue_details.json"),encoding="utf-8"))["pmmp_enrichi"]["complements_fiche"]["par_id"]
K1,K2="pmmp:e5w:1041719","pmmp:g3h:1044229"
KR=next(k for k in sorted(CF) if CF[k].get("reanalyse_le") and not (X[k]["lots"] or X[k]["allot"]) and k in X)
KN=next((k for k in sorted(X) if k not in CF and X[k]["det"] and not (X[k]["lots"] or X[k]["allot"])),None)
SIMN=KN is None  # couverture complète : « sans compléments » simulé en mémoire (retrait temporaire, restauré)
if SIMN:KN=next(k for k in sorted(X) if X[k]["det"] and not (X[k]["lots"] or X[k]["allot"]) and k not in (K1,K2))
PAN="()=>{const p=document.querySelector('[data-mpv-panel]');const q=s=>p.querySelector(s);return{t:p.innerText,html:p.innerHTML,"\
    "sum:p.querySelector('.mpv-kv').innerText,docs:[...p.querySelectorAll('[data-mpv-doc] a')].map(a=>[a.href,a.target,a.innerText]),"\
    "dst:(q('[data-mpv-docs]')||{dataset:{}}).dataset.mpvDocs,cst:(q('[data-mpv-contact]')||{dataset:{}}).dataset.mpvContact,"\
    "ech:(q('[data-mpv-ech]')||{dataset:{}}).dataset.mpvEch,ret:(q('[data-mpv-ret]')||{dataset:{}}).dataset.mpvRet,"\
    "pc:!!q('.mpv-fiche5 [data-mpv-pcode]'),pcSum:!!q('.mpv-kv:not(.mpv-kv5) [data-mpv-pcode]'),"\
    "secs:[...p.querySelectorAll('[data-mpv-fs]')].map(d=>d.dataset.mpvFs),forms:p.querySelectorAll('form').length,"\
    "acts:!!(q('[data-mpv-suivre]')||q('[data-mpv-demander]')||q('[data-mpv-odce]')||q('[data-mpv-analyse]')),pmmp:!!q('[data-mpv-pmmp]')}}"
OPEN="()=>{document.querySelectorAll('[data-mpv-panel] details.mpv-fs').forEach(d=>d.open=true);}"
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);pg.wait_for_function(WAIT,timeout=30000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()")
    w0=len(W());ev(B11);pg.wait_for_timeout(600)
    def sel(k):ev("k=>{S.vf={...JSON.parse(JSON.stringify(VF0)),sort:S.vf.sort};MPV.sel=k.slice(5);render();}",k);pg.wait_for_timeout(250);ev(OPEN);pg.wait_for_timeout(100);return ev(PAN)
    # ===== A. exemple de l'utilisateur, même ID =====
    P=sel(K1);t=P["t"]
    chk(P["secs"]==["cond","dep","docs","contact","src"],f"{K1} : résumé puis 5 sections repliables {P['secs']}")
    chk("Réservé" in t and re.search(r"Réservé TPE / PME\s*\n?\s*Non",t) is not None,"TPE / PME = « Non » (champ officiel) ; objet « Réservé… » conservé, rien déduit")
    chk(P["ech"]=="lu" and "19/10/2026 à 10:00" in t and "LES CONCURRENTS DOIVENT DEPOSER LES PROSPECTUS" in t and "Distinct de la date limite de remise des plis (20/10/2026" in t,
        "prospectus : date 19/10/2026 10:00 et texte publié, distincts de la remise des plis 20/10 09:00")
    chk(P["ret"]=="lu" and "Avenue Abi Imran Fassi ain kadous" in t and "0,00 DH (publié sur PMMP)" in t,"retrait Avenue Abi Imran Fassi ; prix des plans 0 publié (vrai zéro)")
    chk(all(d in t for d in X[K1]["dom"]) and len(X[K1]["dom"])==3 and re.search(r"Variante\s*\n?\s*Non",t) and re.search(r"Réunion\s*\n?\s*Non indiqué",t),"3 domaines, variante Non, réunion non indiquée (« - »)")
    chk("20/10/2026 · 09:00" in t and "09:00 à 09:00" not in t and "Distinct de la date limite de remise des plis (20/10/2026 · 09:00)." in t,
        "date limite de remise des plis affichée une seule fois avec son heure (ligne et distinction prospectus)")
    chk("bureau de Monsieur le Président" in t and "marchespublics.gov.ma" in t,"dépôt sur le portail, ouverture au bureau du Président")
    U="https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=1041719&orgAcronyme=e5w"
    chk(P["dst"]=="lu" and P["docs"]==[[U,"_blank","Ouvrir sur PMMP (nouvel onglet)"]] or (P["docs"] and P["docs"][0][0]==U and P["docs"][0][1]=="_blank"),f"DCE 648 Ko : lien public PMMP du même ID, nouvel onglet ({P['docs']})")
    chk("648 Ko" in t and "le document n'est pas joint dans EAIOS" in t and P["forms"]==0,"libellé : document sur PMMP, non joint dans EAIOS ; aucun formulaire dans la fiche")
    chk(P["cst"]=="lu" and "Coordonnées professionnelles publiées" in t and "E-mail" in t,"contact administratif publié affiché (bloc administratif de la fiche)")
    chk(P["pc"] and not P["pcSum"] and "Code procédure PMMP" not in P["sum"],"code procédure PMMP déplacé dans « Source de la fiche » (hors résumé)")
    chk(P["acts"] and P["pmmp"],"actions Suivre / Demander / Ouvrir et « Voir sur PMMP » conservées")
    # ===== B. alloti =====
    P=sel(K2);t=P["t"]
    chk("Par lot : voir le détail des lots" in t and P["ech"]=="lu" and "15,36 Mo" in t and P["dst"]=="lu","g3h/1044229 alloti : valeurs par lot renvoyées au détail des lots (aucune somme), DCE 15,36 Mo")
    chk(not re.search(r"Estimation\s*\n?\s*[\d ]+,\d\d DH",P["sum"]),"alloti : aucune estimation globale inventée")
    # ===== C. ré-analyse hors ligne : contact / pièces pas encore lus =====
    # contact non récupérable (refus de l'état) simulé en mémoire si toutes les ré-analyses réelles l'ont récupéré
    ev("k=>{const r=S.enr.complements_fiche.par_id[k];window.__kr=JSON.stringify(r);if(r.statuts.contact!=='non_lu'){r.statuts.contact='non_lu';delete r.contact;delete r.sources_blocs;}}",KR)
    P=sel(KR);t=P["t"];ev("k=>{S.enr.complements_fiche.par_id[k]=JSON.parse(window.__kr);render();}",KR)
    chk(P["cst"]=="non_lu" and P["dst"]=="non_lu" and "Non publié" not in t and t.count("Pas encore lu (relecture de la fiche")>=2,f"{KR} ré-analysé : contact et pièces « pas encore lus », jamais « non publiés »")
    chk("ré-analysée hors ligne le" in t and ev("()=>document.querySelector('[data-mpv-cflu]').dataset.mpvCflu")==CF[KR]["lu_le"],"source : date réelle de lecture gardée, ré-analyse datée à part")
    # ===== D. fiche sans compléments =====
    if SIMN:ev("k=>{window.__kn=S.enr.complements_fiche.par_id[k];delete S.enr.complements_fiche.par_id[k];}",KN)
    P=sel(KN);t=P["t"]
    if SIMN:ev("k=>{S.enr.complements_fiche.par_id[k]=window.__kn;render();}",KN)
    chk(P["ret"]=="non_lu" and P["cst"]=="non_lu" and "Non publié" not in t,f"{KN} sans compléments : retrait / contact « pas encore lus »")
    # ===== E. contact non publié (simulé en mémoire) =====
    ev("k=>{const r=S.enr.complements_fiche.par_id[k];window.__c=JSON.stringify(r);r.statuts.contact='non_publie';delete r.contact;}",K1);P=sel(K1)
    chk(P["cst"]=="non_publie" and "Non publié sur la fiche PMMP" in P["t"],"contact absent d'une page lue au-delà : « non publié »")
    ev("k=>{S.enr.complements_fiche.par_id[k]=JSON.parse(window.__c);render();}",K1)
    # ===== F. référence discordante : rien n'est joint =====
    ev("k=>{const r=S.enr.complements_fiche.par_id[k];window.__r=r.ref;r.ref='AUTRE';}",K1);P=sel(K1)
    R_=ev("()=>document.querySelector('[data-mpv-ret]').innerText")
    chk(P["ret"]=="non_lu" and "Avenue" not in R_ and "Pas encore lu" in R_ and P["dst"]=="non_lu","référence lue ≠ catalogue : compléments non utilisés (retrait, pièces pas encore lus)")
    ev("k=>{S.enr.complements_fiche.par_id[k].ref=window.__r;render();}",K1)
    # ===== G. échappement et liens officiels (valeurs hostiles injectées EN MÉMOIRE, aucun clic) =====
    ev("""k=>{const r=S.enr.complements_fiche.par_id[k];window.__g=JSON.stringify(r);
      r.ech_txt='<img src=x onerror="window.__xss=1">PROSPECTUS';r.ret='<script>window.__xss=2</script>Rue';
      r.contact={nom:'<b onclick=1>Agent</b>',email:'x" onmouseover="window.__xss=3',tel:'05',fax:null};
      r.docs=[{type:'dce',libelle:'A',taille:'1 Ko',url:'javascript:window.__xss=4'},
              {type:'reglement',libelle:'B',taille:'1 Ko',url:'index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=999&orgAcronyme=e5w'},
              {type:'complement',libelle:'C',taille:'1 Ko',url:'index.php?page=entreprise.EntrepriseAccueilAuthentifie&refConsultation=1041719&orgAcronyme=e5w'},
              {type:'dce',libelle:'D',taille:'1 Ko',url:'https://evil.example/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=1041719&orgAcronyme=e5w'}];}""",K1)
    P=sel(K1)
    G_=ev("""()=>{const p=document.querySelector('[data-mpv-panel]');return{img:p.querySelectorAll('.mpv-fiche5 img').length,scr:p.querySelectorAll('.mpv-fiche5 script').length,
      b:p.querySelectorAll('.mpv-fiche5 b[onclick]').length,mail:p.querySelectorAll('.mpv-fiche5 a[href^="mailto:"]').length,
      hrefs:[...p.querySelectorAll('.mpv-fiche5 a[href]')].map(a=>a.getAttribute('href')),xss:window.__xss||0,
      txt:p.querySelector('[data-mpv-echt]').innerText}}""")
    FICHE="https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1041719&orgAcronyme=e5w"
    chk(G_["img"]==0 and G_["scr"]==0 and G_["b"]==0 and G_["xss"]==0 and "<img src=x" in G_["txt"],"textes source échappés (balises affichées comme texte, rien exécuté)")
    chk(G_["mail"]==0,"e-mail invalide : affiché en texte, aucun lien mailto")
    chk(all(h.startswith("https://www.marchespublics.gov.ma/index.php?page=entreprise.Entreprise") and "refConsultation=1041719&orgAcronyme=e5w" in h for h in G_["hrefs"]) and G_["hrefs"].count(FICHE)>=4,
        f"liens hostiles / autre ID / page soumissionnaire / autre hôte remplacés par la fiche PMMP du même ID ({len(G_['hrefs'])} liens)")
    ev("k=>{S.enr.complements_fiche.par_id[k]=JSON.parse(window.__g);render();}",K1)
    # ===== H. contact relevé dans l'état de page d'une lecture conservée : provenance affichée =====
    KE=next((k for k in sorted(CF) if (CF[k].get("sources_blocs") or {}).get("contact")=="etat_de_page" and k in X and not (X[k]["lots"] or X[k]["allot"])),None)
    if KE:
        P=sel(KE);t=P["t"]
        chk(P["cst"]=="lu" and "état de page de cette lecture" in t and P["dst"]=="non_lu" and ev("()=>!!document.querySelector('[data-mpv-docpmmp]')"),
            f"{KE} : contact de l'état de page avec sa date de lecture ; pièces « pas encore lues » avec lien vers la fiche PMMP")
    # ===== I. pièces : vide confirmé avec preuve, inventaire daté à part, lien d'avis officiel du même ID =====
    ev("""k=>{const r=S.enr.complements_fiche.par_id[k];window.__i=JSON.stringify(r);r.docs=[];r.docs_preuve='liens_officiels_tous_masques';r.docs_lu_le='2026-10-19T21:00:00+00:00';}""",K1)
    P=sel(K1);t=P["t"]
    chk(P["dst"]=="lu" and "Aucune pièce publiée : constaté sur la fiche PMMP (liens officiels tous masqués)" in t and "Liste relevée le" in t,"aucune pièce CONFIRMÉE avec sa preuve ; date propre de l'inventaire affichée")
    ev("""k=>{const r=S.enr.complements_fiche.par_id[k];r.docs=[{type:'avis',libelle:'Extrait de PV',taille:null,url:'index.php?page=entreprise.ExtraitPV&refConsultation=1041719&orgAcronyme=e5w'}];delete r.docs_lu_le;}""",K1)
    P=sel(K1)
    chk(P["docs"] and P["docs"][0][0]=="https://www.marchespublics.gov.ma/index.php?page=entreprise.ExtraitPV&refConsultation=1041719&orgAcronyme=e5w","extrait de PV publié : lien officiel du même ID conservé")
    ev("k=>{S.enr.complements_fiche.par_id[k]=JSON.parse(window.__i);render();}",K1)
    # ===== J. « Source et couverture » : couverture réelle des pièces, jamais 100 % avant la fin =====
    CV=json.load(open(os.path.join(SRV,"catalogue_details.json"),encoding="utf-8"))["pmmp_enrichi"]["complements_fiche"]["couverture"]["docs"]
    ev("()=>{MPV.bandOpen=true;render();}");pg.wait_for_timeout(200)
    B_=ev("()=>{const e=document.querySelector('[data-mpv-couvdocs]');return e?{d:e.dataset.mpvCouvdocs,t:e.innerText}:null}")
    n_=CV["lu"]+CV["non_publie"]+CV["non_lu"]
    chk(B_ and B_["d"]==f"{CV['lu']}/{n_}" and f"Inventaires des pièces lus : {CV['lu']} sur {n_} consultations" in B_["t"] and f"inventaires pas encore lus : {CV['non_lu']} consultations" in B_["t"] and "Compte de consultations, pas de fichiers" in B_["t"] and ("100 %" not in B_["t"] or CV["non_lu"]==0),
        f"Source et couverture : inventaires lus {CV['lu']} sur {n_} consultations, pas encore lus {CV['non_lu']} (aucun 100 % prématuré)")
    ev("()=>{MPV.bandOpen=false;render();}")
    chk(len(W()[w0:])==0,"aucune écriture");chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
    ctx.close()
    for w,sch in ((390,"light"),(1440,"dark")):
        c=b.new_context(viewport={"width":w,"height":860},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function(WAIT,timeout=30000);q.wait_for_timeout(400);q.evaluate(B11);q.wait_for_timeout(500)
        q.evaluate("k=>{MPV.sel=k.slice(5);MPV.mob='panel';render();}",K1);q.wait_for_timeout(300);q.evaluate(OPEN);q.wait_for_timeout(150)
        M_=q.evaluate("""()=>{const p=document.querySelector('[data-mpv-panel]'),dd=[...p.querySelectorAll('.mpv-kv dd')].filter(d=>d.offsetParent);
          return{doc:document.documentElement.scrollWidth-document.documentElement.clientWidth,minDd:Math.min(...dd.map(d=>d.getBoundingClientRect().width)),
          pw:p.getBoundingClientRect().width,cut:dd.filter(d=>d.scrollWidth>d.clientWidth+1).length}}""")
        ok=M_["doc"]<=0 and M_["cut"]==0 and (w>640 or M_["minDd"]>=0.8*M_["pw"]-40)
        q.screenshot(path=f"{OUT}/mpv5_fiche_{w}_{sch}.png",full_page=True);chk(ok and not e,f"{w} px {sch} : fiche ouverte sans débordement ni valeur coupée {M_}")
        c.close()
    b.close()
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
