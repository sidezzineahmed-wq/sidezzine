"""Recette mpv-3 · B1.1 : Mode de passation + classification PMMP Etat / CL / EEP (clé pmmp_enrichi de catalogue_details.json, produite par l'ingestion horaire).
Banc qa_b21dec (base simulée, écritures tracées) + copies EN LECTURE du catalogue live et du fichier joint (srv/).
Attentes recalculées en Python depuis les fichiers, + échantillons officiels de la recherche PMMP filtrée (relevé du 17/10 23:58 UTC)."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50&&S.enrState==='ok'"
NL="()=>+document.getElementById('mpv-lt').innerText.split(' ')[0]"
CAT=json.load(open(os.path.join(SRV,"catalogue.json"),encoding="utf-8"));ENR=json.load(open(os.path.join(SRV,"catalogue_details.json"),encoding="utf-8"))["pmmp_enrichi"]
REL=json.load(open(os.path.join(ICI0,"..","pmmp","sonde","releve_classif.json"),encoding="utf-8"))
nref=lambda s:re.sub(r"\s+"," ",s or "").strip().upper()
def tach(x):return (ENR["classification"]["par_entite"].get(x["o"]) or {}).get("code")
def mp(x):
    r=ENR["mode_passation"]["par_id"].get(f"pmmp:{x['o']}:{x['r']}")
    return r["v"] if r and r.get("v") and nref(r.get("ref"))==nref(x.get("ref")) else None
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);pg.wait_for_function(WAIT,timeout=30000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");AK=lambda:ev("()=>Object.keys(S.ao).length")
    w0=len(W());k0=AK();ev(B11);pg.wait_for_timeout(600)
    OUV=set(ev("()=>MPV.base.R.filter(e=>!e.x._ferme).map(e=>'pmmp:'+e.x.o+':'+e.x.r)"))
    X={f"pmmp:{x['o']}:{x['r']}":x for x in CAT["items"]}
    OPEN=[X[k] for k in OUV if k in X]
    def VF(**k):
        ev("k=>{S.vf={...JSON.parse(JSON.stringify(VF0)),sort:S.vf.sort,...k};vfSave();MPV.page=1;render();}",k);pg.wait_for_timeout(250)
    exp=lambda f:sum(1 for x in OPEN if f(x))
    # ===== A. données et provenance =====
    C=ENR["classification"];M=ENR["mode_passation"]
    chk(C["source"]["controle_listes"]["partition_exacte"] and C["source"]["controle_recherche"]["partition_totaux"] and C["couverture"]["entites_inconnues"]==[] and M["couverture"]["reference_discordante"]==[],
        f"enrichissement joint : partition officielle exacte (57 Etat / 16 CL / 4 EEP entités ; totaux filtrés {C['source']['controle_recherche']['totaux']['1']['total']}+{C['source']['controle_recherche']['totaux']['2']['total']}+{C['source']['controle_recherche']['totaux']['3']['total']} = {C['source']['controle_recherche']['totaux']['toutes']['total']}) ; mode connu {M['couverture']['connues']}/{M['couverture']['annonces']}")
    chk(all(v.get("lu_le") and v.get("source") in ("collecteur","complement_eaios") and v["v"] in ("Sur offre de prix","Au rabais / majoration") for v in M["par_id"].values()) and not any(v["v"] in ENR["procedures"]["codes"] for v in M["par_id"].values()),
        "chaque mode : valeur PMMP brute, date de lecture réelle, source ; aucune valeur de mode n'est une procédure")
    chk(ev("()=>[!!document.querySelector('[data-mpv-dis=mode]'),!!document.querySelector('[data-mpv-dis=type]')]")==[False,False],"plus aucun bloc « non disponible » pour mode / classification")
    # ===== B. facettes : ET autres critères, OU multichoix, même moteur =====
    pg.click('[data-mpv-qf="ach"]');pg.wait_for_timeout(350)
    CN=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-mpv-o^=\"tach:\"],[data-mpv-o^=\"mpass:\"]')].map(b=>[b.dataset.mpvO,+b.querySelector('.mpv-on').innerText]))")
    E={"tach:1":exp(lambda x:tach(x)=="1"),"tach:2":exp(lambda x:tach(x)=="2"),"tach:3":exp(lambda x:tach(x)=="3"),"mpass:Sur offre de prix":exp(lambda x:mp(x)=="Sur offre de prix"),"mpass:Au rabais / majoration":exp(lambda x:mp(x)=="Au rabais / majoration")}
    chk(CN==E,f"comptes du tiroir = recalcul Python sur les consultations ouvertes {CN}")
    pg.click('[data-mpv-o="tach:2"]');pg.wait_for_timeout(200);pg.click('[data-mpv-o="tach:3"]');pg.wait_for_timeout(200)
    CN2=ev("()=>+document.querySelector('[data-mpv-o=\"mpass:Au rabais / majoration\"] .mpv-on').innerText");dn=ev("()=>+document.querySelector('[data-mpv-dwn]').dataset.mpvDwn")
    chk(ev("()=>S.vf.tach.length")==0 and dn==exp(lambda x:tach(x) in ("2","3")) and CN2==exp(lambda x:tach(x) in ("2","3") and mp(x)=="Au rabais / majoration"),f"brouillon CL OU EEP : {dn} (rien appliqué) ; compte « Au rabais » recalculé sous ce brouillon ({CN2})")
    pg.click('[data-mpv-o="mpass:Au rabais / majoration"]');pg.wait_for_timeout(200);pg.click("#mpv-dwok");pg.wait_for_timeout(350)
    e1=exp(lambda x:tach(x) in ("2","3") and mp(x)=="Au rabais / majoration")
    CH=ev("()=>[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.innerText)")
    chk(ev(NL)==e1 and CH==["Classification PMMP : Collectivité locale","Classification PMMP : Etablissement public","Mode de passation : Au rabais / majoration"] and ev("()=>document.getElementById('mpv-tf').dataset.mpvTf")=="3",f"appliqué : (CL OU EEP) ET « Au rabais » = {e1} ; 3 puces, « Tous les filtres · 3 »")
    reg=ev("()=>Object.keys(S.cat.regions).find(r=>r.startsWith('Marrakech'))")
    VF(tach=["2"],regs=[reg],cats=["Travaux"])
    e2=ev("r=>MPV.base.R.filter(e=>!e.x._ferme&&e.x._regs.includes(r)&&e.x.cat==='Travaux').map(e=>'pmmp:'+e.x.o+':'+e.x.r)",reg);e2=sum(1 for k in e2 if tach(X[k])=="2")
    chk(ev(NL)==e2,f"ET avec région {reg} et Travaux : {e2}")
    VF(tach=["1"],etat="tout",suivi="non",pert=True)
    e3=ev("()=>{const fm=followedMap();return MPV.base.R.filter(e=>!(e.sc.block||e.sc.s<60)&&!fm[e.x.r+'/'+e.x.o]).map(e=>'pmmp:'+e.x.o+':'+e.x.r)}");e3=sum(1 for k in e3 if tach(X[k])=="1")
    chk(ev(NL)==e3,f"avec les 3 axes (Toutes × Non suivies × Pertinentes) : {e3}")
    # ===== C. inconnus =====
    VF(mpass=["Sur offre de prix"]);a=ev(NL);VF(mpass=["Sur offre de prix"],inc=["mpass"]);bb=ev(NL);nu=ev("()=>+(document.querySelector('[data-mpv-nu-list]')||{dataset:{mpvNuList:0}}).dataset.mpvNuList")
    u=exp(lambda x:mp(x) is None)
    chk(a==exp(lambda x:mp(x)=="Sur offre de prix") and bb==a+u and nu==u and any("mode de passation" in c for c in ev("()=>[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.innerText)")),f"inconnus : « Sur offre de prix » {a} ; + {u} non renseignés seulement sur demande, comptés à part (jamais classés « Sur offre de prix » par défaut)")
    VF(mpass=["Au rabais / majoration"]);chk(ev(NL)==exp(lambda x:mp(x)=="Au rabais / majoration"),"« Au rabais » n'inclut aucune fiche inconnue")
    k0_=next(k for k in OUV if mp(X[k]));ev("k=>{const r=S.enr.mode_passation.par_id[k];r._ref=r.ref;r.ref='AUTRE-REF';}",k0_);VF(mpass=[mp(X[k0_])])
    chk(ev("k=>!MPV.base.R.filter(e=>mpvM(e,S.vf,null)).some(e=>'pmmp:'+e.x.o+':'+e.x.r===k)",k0_),"référence lue ≠ référence du catalogue : jointure refusée (inconnu)")
    ev("k=>{const r=S.enr.mode_passation.par_id[k];r.ref=r._ref;delete r._ref;}",k0_)
    # ===== D. fiche =====
    VF();kS=next(k for k in sorted(OUV) if mp(X[k]) and M["par_id"][k]["source"]=="collecteur");kU=next(k for k in sorted(OUV) if not mp(X[k]))
    ev("k=>{MPV.sel=k.slice(5);render();}",kS);P=ev("()=>{const p=document.querySelector('[data-mpv-panel]');return{t:p.innerText,mp:p.querySelector('[data-mpv-mp]').dataset.mpvMp,ta:p.querySelector('[data-mpv-tach]').dataset.mpvTach,pc:(p.querySelector('[data-mpv-pcode]')||{dataset:{}}).dataset.mpvPcode}}")
    xs=X[kS];lu=M["par_id"][kS]["lu_le"]
    chk(P["mp"]==mp(xs) and P["ta"]==tach(xs) and P["pc"]==ENR["procedures"]["codes"].get(xs["proc"]) and "Procédure" in P["t"] and "fiche PMMP lue le" in P["t"] and "classification PMMP de l'entité publique" in P["t"],f"fiche {xs['ref']} : procédure « {xs['proc']} » (code {P['pc']}) ≠ mode « {P['mp']} » (lu le {lu}) ; classification {P['ta']} de l'entité, provenance affichée")
    ev("k=>{MPV.sel=k.slice(5);render();}",kU);t=ev("()=>document.querySelector('[data-mpv-panel] [data-mpv-mp]').innerText")
    chk("Non renseigné" in t,f"fiche sans lecture : mode « Non renseigné » ({t})")
    # ===== E. échantillons officiels PMMP =====
    for cl in ("2","3"):
        off={f"pmmp:{o}:{r}" for o,r in REL["classes"][cl]["ids"]}
        VF(tach=[cl]);got=set(ev("()=>MPV.base.R.filter(e=>mpvM(e,S.vf,null)).map(e=>'pmmp:'+e.x.o+':'+e.x.r)"))
        inter=off&OUV
        chk(inter<=got and not any(tach(X[k])!=cl for k in got),f"classe {cl} : les {len(inter)} annonces ouvertes renvoyées par la recherche officielle PMMP filtrée sont toutes dans le filtre EAIOS ({len(got)}) ; aucune annonce d'une autre classe")
    # ===== F. puces, brouillon, réinitialiser, recherche enregistrée, migration =====
    VF(tach=["2"],mpass=["Sur offre de prix"]);pg.click('.mpv-r4 [data-vfx="tach:2"]');pg.wait_for_timeout(300)
    chk(ev("()=>[S.vf.tach.length,S.vf.mpass.length]")==[0,1],"puce retirée seule")
    pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dn-ach");pg.wait_for_timeout(200);pg.click('[data-mpv-o="tach:1"]');pg.wait_for_timeout(200);pg.keyboard.press("Escape");pg.wait_for_timeout(250)
    chk(ev("()=>S.vf.tach.length")==0,"Échap : brouillon abandonné")
    pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dwr");pg.wait_for_timeout(200);chk(ev("()=>[MPV.dr.tach.length,MPV.dr.mpass.length,S.vf.mpass.length]")==[0,0,1],"Réinitialiser : brouillon vidé, rien appliqué");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    nw=len(W());VF(tach=["3"],mpass=["Sur offre de prix"],inc=["mpass"]);pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.fill("#mpv-svn","QA EEP offre de prix");pg.click("#mpv-svb");pg.wait_for_timeout(500)
    sv=ev("()=>S.saved.find(r=>r.nom==='QA EEP offre de prix')");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    chk([w for w in W()[nw:]]==[["set","veille/recherches"]] and sv["vf"]["tach"]==["3"] and sv["vf"]["mpass"]==["Sur offre de prix"] and sv["vf"]["inc"]==["mpass"],"recherche enregistrée (action explicite) : classification, mode et inclusion des inconnus conservés")
    MG=ev("()=>{const v={q:'x',regs:[],sort:'lim'};const w=mpvMigr(v);return [v.tach,v.mpass,w.length]}");chk(MG==[[],[],0],"ancienne recherche sans ces critères : migrée sans avertissement inutile")
    # ===== G. données absentes : aucune fausse activation =====
    VF(tach=["1"]);n1=ev(NL);ev("()=>{window.__enr=S.enr;S.enr=null;S.enrState='absent';render();}")
    nA=ev(NL);ch=ev("()=>[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.innerText)");pg.click("#mpv-tf");pg.wait_for_timeout(300)
    dis=ev("()=>[!!document.querySelector('[data-mpv-dis=enr]'),document.querySelectorAll('[data-mpv-o^=\"tach:\"]').length]");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    ev("()=>{S.enr=window.__enr;S.enrState='ok';render();}")
    chk(nA==ev("()=>MPV.base.R.filter(e=>!e.x._ferme).length") and any("non appliqué" in c for c in ch) and dis==[True,0],"enrichissement absent : filtres désactivés et expliqués, puce « non appliqué », aucun résultat inventé")
    # ===== G2. page légère, statuts de lecture, couverture détaillée =====
    PG=ev("""async()=>{const r=await fetch('index.html');const t=await r.text();return{n:t.length,js:!!document.querySelector('script[src^="app/eaios.js"]'),css:!!document.querySelector('link[href^="app/eaios.css"]'),inl:document.querySelectorAll('script:not([src])').length}}""")
    chk(PG["n"]<20000 and PG["js"] and PG["css"],f"index.html allégé ({PG['n']} octets) : script et styles servis en fichiers annexes du même artefact (relecture intégrale possible par le passage horaire)")
    VF();ku=sorted(k for k in OUV if not mp(X[k]))[:2]
    ev("ks=>{const M=S.enr.mode_passation;M.absents=M.absents||{};M.inaccessibles=M.inaccessibles||{};const x0=MPV.base.by.get(ks[0].slice(5)).x;M.absents[ks[0]]={ref:x0.ref,lu_le:'2026-10-18T01:00:00+00:00',source:'complement_eaios'};M.inaccessibles[ks[1]]={tentatives:3,dernier_echec:'2026-10-18T01:05:00+00:00'};}",ku)
    ev("k=>{MPV.sel=k.slice(5);render();}",ku[0]);t0=ev("()=>[document.querySelector('[data-mpv-panel] [data-mpv-mp]').dataset.mpvMpst,document.querySelector('[data-mpv-panel] [data-mpv-mp]').innerText]")
    ev("k=>{MPV.sel=k.slice(5);render();}",ku[1]);t1=ev("()=>[document.querySelector('[data-mpv-panel] [data-mpv-mp]').dataset.mpvMpst,document.querySelector('[data-mpv-panel] [data-mpv-mp]').innerText]")
    VF(mpass=["Sur offre de prix"]);nA=ev(NL)
    chk(t0[0]=="absent" and "champ vide sur la fiche PMMP" in t0[1] and t1[0]=="inaccessible" and "inaccessible après 3 essais" in t1[1] and nA==exp(lambda x:mp(x)=="Sur offre de prix"),f"fiche lue sans mode et fiche inaccessible : signalées comme telles, jamais une valeur ({t0[1][:60]} / {t1[1][:60]})")
    ev("ks=>{const M=S.enr.mode_passation;delete M.absents[ks[0]];delete M.inaccessibles[ks[1]];}",ku)
    VF();pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dn-dispo");pg.wait_for_timeout(200);cv=ev("()=>document.querySelector('[data-mpv-cov=mpass]').innerText");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    c=M["couverture"];chk(f"Connu pour {c['connues']} consultations sur {c['annonces']}" in cv and "fiche lue sans mode" in cv and "pas encore lue" in cv,f"Disponibilité : couverture réelle détaillée ({cv[:140]})")
    # ===== H. clavier, droits, écritures =====
    VF();pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dn-ach");pg.wait_for_timeout(200);pg.focus('[data-mpv-o="mpass:Au rabais / majoration"]');pg.keyboard.press("Space");pg.wait_for_timeout(250)
    chk(ev("()=>[MPV.dr.mpass,document.activeElement.dataset.mpvO]")==[["Au rabais / majoration"],"mpass:Au rabais / majoration"],"clavier : Espace coche l'option, le focus reste sur elle");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    ev("()=>{S.readOnly=true;render();}");VF(tach=["2"]);chk(ev(NL)==exp(lambda x:tach(x)=="2"),"lecture seule : filtrage identique");ev("()=>{S.readOnly=false;render();}")
    chk(len([w for w in W()[w0:] if w[1]!="veille/recherches"])==0 and AK()==k0,"aucune écriture métier, aucun dossier créé")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
    ctx.close()
    for w,sch in ((390,"light"),(768,"dark"),(1440,"light")):
        c=b.new_context(viewport={"width":w,"height":860},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function(WAIT,timeout=30000);q.wait_for_timeout(400);q.evaluate(B11);q.wait_for_timeout(500)
        q.click('[data-mpv-qf="ach"]');q.wait_for_timeout(400);q.evaluate("()=>document.querySelector('[data-mpv-enr]').scrollIntoView()");q.wait_for_timeout(200)
        M_=q.evaluate("()=>{const c=document.getElementById('mpv-dwc');return{ov:c.scrollWidth-c.clientWidth,ok:document.getElementById('mpv-dwok').getBoundingClientRect().bottom<=innerHeight,doc:document.documentElement.scrollWidth-document.documentElement.clientWidth}}")
        q.screenshot(path=f"{OUT}/mpv3_tiroir_{w}_{sch}.png");chk(M_["ov"]<=0 and M_["ok"] and M_["doc"]<=0 and not e,f"{w} px {sch} : bloc mode / classification sans débordement, « Appliquer » visible {M_}")
        c.close()
    b.close()
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
