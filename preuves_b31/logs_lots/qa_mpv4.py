"""Recette mpv-4 · B1.1 : détail PAR LOT (pmmp_enrichi.lots). Critères par lot évalués sur un MÊME lot (contre-exemple croisé),
critères globaux sur l'annonce, OU dans un axe / ET entre axes, inconnus (popup non lu, partiel) seulement sur demande, comptes
dédupliqués par annonce, lots correspondants affichés, provenance. Banc qa_b21dec ; lots injectés EN MÉMOIRE (aucune écriture)
sur de vraies annonces alloties du catalogue ; attentes recalculées en Python avec la même règle."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50&&S.enrState==='ok'"
NL="()=>+document.getElementById('mpv-lt').innerText.split(' ')[0]"
CAT=json.load(open(os.path.join(SRV,"catalogue.json"),encoding="utf-8"))
REAL=(json.load(open(os.path.join(SRV,"catalogue_details.json"),encoding="utf-8")).get("pmmp_enrichi") or {}).get("lots")
nref=lambda s:re.sub(r"\s+"," ",s or "").strip().upper()
LOT=lambda n,**k:{"num":str(n),"intitule":f"Lot fictif {n}","ni":[],"na":[],**k}
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);pg.wait_for_function(WAIT,timeout=30000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");AK=lambda:ev("()=>Object.keys(S.ao).length")
    w0=len(W());k0=AK();ev(B11);pg.wait_for_timeout(600)
    OUV=ev("()=>MPV.base.R.filter(e=>!e.x._ferme).map(e=>'pmmp:'+e.x.o+':'+e.x.r)")
    X={f"pmmp:{x['o']}:{x['r']}":x for x in CAT["items"]};OPEN=[X[k] for k in OUV if k in X]
    AL=sorted([k for k in OUV if X[k]["lots"] or X[k]["allot"]],key=lambda k:(X[k]["cat"],k))
    cats=sorted({X[k]["cat"] for k in AL});kA=next(k for k in AL if X[k]["cat"]==cats[0]);kB=next(k for k in AL if X[k]["cat"]!=X[kA]["cat"])
    kC,kD,kE,kF=[k for k in AL if k not in (kA,kB)][:4]
    q1=[{"m":"Equipement","s":"B","sl":"Travaux routiers","q":"B.3","ql":"Ouvrages","c":"2"}]
    SYN={kA:{"statut":"lu","n":2,"n_annonce":2,"lots":[LOT(1,est=3e6,tp=False,cau=60000.0,q=q1,ni=["ag","vis"]),LOT(2,est=5e5,tp=True,cau=10000.0,ni=["q","ag","vis"])]},
         kB:{"statut":"lu","n":2,"n_annonce":2,"lots":[LOT(1,est=2e6,tp=True,ni=["q","ag"]),LOT(2,est=4e6,tp=True,ni=["q","ag"])]},
         kC:{"statut":"partiel","n":1,"n_annonce":3,"lots":[LOT(1,est=3e6,tp=False)]},
         kE:{"statut":"lu","n":1,"n_annonce":1,"lots":[LOT(1,est=0.0,tp=True,ni=["cau"])]},
         kF:{"statut":"lu","n":1,"n_annonce":1,"lots":[LOT(1,est=3e6,tp=True)]}}
    LOTS={"par_id":{k:{**v,"lu_le":"2026-10-18T11:00:00+00:00","ref":X[k]["ref"] if k!=kF else "AUTRE-REF"} for k,v in SYN.items()},"inaccessibles":{},"couverture":{"alloties":len(AL),"lues":4,"partielles":1,"inaccessibles":0,"non_lues":len(AL)-5,"lots":7}}
    ev("L=>{window.__lots0=S.enr.lots;S.enr.lots=L;render();}",LOTS)
    # ---------- règle Python (même lot) ----------
    def units(x):
        k=f"pmmp:{x['o']}:{x['r']}"
        if not(x["lots"] or x["allot"]):return[dict(det=x["det"],est=x["est"],tp=x["tp"],cau=x["cau"],q=x["q"] or [],lot=None)]
        r=SYN.get(k) if k!=kF else None;U=[]
        if r:U=[dict(det=True,est=l.get("est"),tp=l.get("tp"),cau=l.get("cau"),q=l.get("q") or [],lot=l["num"]) for l in r["lots"]]
        if not r or r["statut"]!="lu":U.append(dict(det=False,est=None,tp=None,cau=None,q=[],lot=None))
        return U
    def mts15(u):m=u["est"];return bool(m and m>0 and 1e6<=m<5e6)
    def mtsnp(u):return u["det"] and not u["est"]
    def tpo(u):return u["tp"] is True
    def qeq(u):return any((q.get("m") or "")=="Equipement" for q in u["q"])
    UNK={"mts":lambda u:u["est"] is None,"tp":lambda u:u["tp"] is None,"qual":lambda u:not u["det"]}
    def match(x,crit,inc=()):
        H=[]
        for u in units(x):
            ok,unk=True,False
            for g,f in crit:
                if f(u):continue
                if g in inc and UNK[g](u):unk=True;continue
                ok=False;break
            if ok:H.append((u,unk))
        if not H:return None
        return{"unk":all(h[1] for h in H),"lots":[h[0]["lot"] for h in H if not h[1] and h[0]["lot"]]}
    def VF(**k):
        ev("k=>{S.vf={...JSON.parse(JSON.stringify(VF0)),sort:S.vf.sort,...k};vfSave();MPV.page=1;render();}",k);pg.wait_for_timeout(250)
    GOT=lambda:ev("()=>Object.fromEntries(MPV.base.R.map(e=>[e,mpvMatch(e,S.vf,null)]).filter(([,r])=>r.ok).map(([e,r])=>['pmmp:'+e.x.o+':'+e.x.r,{unk:r.unk,lots:r.lots||[]}]))")
    def expect(crit,inc=()):return{f"pmmp:{x['o']}:{x['r']}":match(x,crit,inc) for x in OPEN if match(x,crit,inc)}
    def same(got,exp):return set(got)==set(exp) and all(got[k]["unk"]==exp[k]["unk"] and (got[k]["lots"] or [])==(exp[k]["lots"] or []) for k in exp)
    # ===== A. contre-exemple croisé =====
    VF(mts=["1-5"],tp="oui");G=GOT();E=expect([("mts",mts15),("tp",tpo)])
    chk(kA not in G and kB in G and G[kB]["lots"]==["1","2"] and same(G,E) and ev(NL)==len(E),f"estimation 1–5 M ET TPE : l'annonce {X[kA]['ref']} (lot 1 = 3 M non réservé, lot 2 = 0,5 M réservé) N'EST PAS retenue ; {X[kB]['ref']} retenue par ses lots 1 et 2, comptée une fois ; {len(E)} annonces = recalcul Python")
    VF(mts=["1-5"]);G=GOT();chk(G.get(kA,{}).get("lots")==["1"] and same(G,expect([("mts",mts15)])),"estimation 1–5 M seule : annonce A retenue par son lot 1")
    VF(tp="oui");G=GOT();chk(G.get(kA,{}).get("lots")==["2"] and same(G,expect([("tp",tpo)])),"TPE seule : annonce A retenue par son lot 2")
    VF(qsys=["Equipement"],tp="oui");G=GOT();chk(kA not in G and same(G,expect([("qual",qeq),("tp",tpo)])),"qualification « Equipement » (lot 1) ET TPE (lot 2) : pas de correspondance fictive")
    VF(qsys=["Equipement"]);G=GOT();chk(G.get(kA,{}).get("lots")==["1"],"qualification seule : lot 1")
    # ===== B. inconnus : popup partiel / non lu / référence discordante =====
    VF(mts=["1-5"],tp="oui");n0=ev(NL);VF(mts=["1-5"],tp="oui",inc=["tp","mts"]);G=GOT();E=expect([("mts",mts15),("tp",tpo)],("tp","mts"));nu=ev("()=>+(document.querySelector('[data-mpv-nu-list]')||{dataset:{mpvNuList:0}}).dataset.mpvNuList")
    chk(kC not in expect([("mts",mts15),("tp",tpo)]) and G.get(kC,{}).get("unk") is True and G.get(kD,{}).get("unk") is True and G.get(kF,{}).get("unk") is True and same(G,E) and nu==sum(1 for v in E.values() if v["unk"]),
        f"popup partiel ({X[kC]['ref']}), non lu ({X[kD]['ref']}), référence discordante ({X[kF]['ref']}) : inconnus, retenus seulement sur demande et signalés ({nu} sur {len(E)}) ; sans inclusion {n0}")
    # ===== C. critères globaux sur l'annonce (ET) =====
    VF(mts=["1-5"],tp="oui",cats=[c for c in ("Travaux","Fournitures","Services") if c!=X[kB]["cat"]]);G=GOT()
    chk(kB not in G and same(G,{k:v for k,v in expect([("mts",mts15),("tp",tpo)]).items() if X[k]["cat"]!=X[kB]["cat"]}),"catégorie (critère d'annonce) ET critères par lot : annonce B exclue par sa catégorie")
    VF(mts=["1-5","lt1"],tp="oui");G=GOT();chk(G.get(kA,{}).get("lots")==["2"],"OU dans l'axe estimation (moins de 1 M OU 1–5 M) ET TPE : annonce A retenue par son lot 2 seulement")
    # ===== D. estimation 0 non exploitable =====
    VF(mts=["np"]);G=GOT();chk(G.get(kE,{}).get("lots")==["1"] and kB not in G and same(G,expect([("mts",mtsnp)])),"lot à estimation 0 : « Non publiée ou 0 (non exploitable) », jamais compté comme montant")
    # ===== E. tiroir : comptes du même moteur =====
    VF(tp="oui");pg.click("#mpv-tf");pg.wait_for_timeout(350);pg.click("#mpv-dn-mts");pg.wait_for_timeout(250)
    c15=ev("()=>+document.querySelector('[data-mpv-o=\"mts:1-5\"] .mpv-on').innerText");e15=len(expect([("mts",mts15),("tp",tpo)]))
    pg.click("#mpv-dn-cond");pg.wait_for_timeout(200);rule=ev("()=>!!document.querySelector('[data-mpv-lotrule]')")
    pg.click("#mpv-dn-dispo");pg.wait_for_timeout(200);cov=ev("()=>(document.querySelector('[data-mpv-cov=lots]')||{innerText:''}).innerText");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    chk(c15==e15 and rule and "Détail par lot" in cov,f"tiroir sous « TPE » : compte « 1 à 5 M » = {c15} (même lot, recalcul {e15}) ; règle par lot expliquée ; couverture : {cov[:110]}")
    # ===== F. liste et fiche =====
    VF(tp="oui");ev("k=>{MPV.sel=k.slice(5);render();}",kA)
    P=ev("()=>{const p=document.querySelector('[data-mpv-panel]');return{t:p.innerText,ok:(p.querySelector('[data-mpv-lotok]')||{dataset:{}}).dataset.mpvLotok,on:[...p.querySelectorAll('.mpv-lot.on')].map(l=>l.dataset.mpvLot),n:p.querySelectorAll('.mpv-lot').length,st:p.querySelector('[data-mpv-lots]').dataset.mpvLots}}")
    row=ev("k=>{const d=document.createElement('div');d.innerHTML=mpvRow(MPV.base.by.get(k.slice(5)),{},false);return(d.querySelector('.mpv-lotm')||{textContent:''}).textContent}",kA)
    chk(P["ok"]=="2" and P["on"]==["2"] and P["n"]==2 and P["st"]=="lu" and "lu le" in P["t"] and "Non indiqué sur PMMP" in P["t"] and "Par lot" in P["t"] and row.startswith("Lot 2 correspondant"),f"fiche A : 2 lots détaillés, lot 2 signalé comme correspondant, valeurs « - » = non indiqué, provenance datée ; ligne : « {row} »")
    ev("k=>{MPV.sel=k.slice(5);render();}",kE);tE=ev("()=>document.querySelector('[data-mpv-panel]').innerText")
    ev("k=>{MPV.sel=k.slice(5);render();}",kD);tD=ev("()=>[document.querySelector('[data-mpv-lots]').dataset.mpvLots,document.querySelector('[data-mpv-panel]').innerText]")
    ev("k=>{MPV.sel=k.slice(5);render();}",kC);tC=ev("()=>!!document.querySelector('[data-mpv-lotpart]')")
    chk("0 sur PMMP (non exploitable)" in tE and tD[0]=="non_lu" and "pas encore lu" in tD[1] and tC,"fiche : estimation 0 non exploitable, popup non lu = inconnu, lecture partielle signalée")
    kN=next((k for k in OUV if not X[k]["det"]),None)
    if kN:
        ev("k=>{S.enr.fiches={inaccessibles:{[k]:{tentatives:3,dernier_echec:'2026-10-18T12:00:00+00:00'}}};}",kN);ev("k=>{MPV.sel=k.slice(5);render();}",kN)
        pv=ev("()=>{const d=document.createElement('div');d.innerHTML=vProvDetail(MPV.base.by.get(MPV.sel).x);return d.firstChild.dataset.vePro||d.firstChild.dataset.veProv}");ev("()=>{delete S.enr.fiches;}")
        pv2=ev("()=>{const d=document.createElement('div');d.innerHTML=vProvDetail(MPV.base.by.get(MPV.sel).x);return d.firstChild.dataset.veProv}")
        chk(pv=="inaccessible" and pv2 in ("sans","obsolete"),f"fiche inaccessible après essais ≠ pas encore lue ({pv} / {pv2})")
    # ===== F2. qualification publiée sans code (Laboratoires) et avec code alphanumérique (Y / Y1), même lot =====
    ql=[{"m":"Laboratoires","s":None,"sl":"CONTROLE DE QUALITE","q":None,"ql":"CONTROLE DES TRAVAUX DE BATIMENT","c":"4"}]
    qy=[{"m":"Equipement","s":"Y","sl":"Amenagement des cours d'eau","q":"Y1","ql":"Travaux de recalibrage","c":"3"}]
    L2=json.loads(json.dumps(LOTS));L2["par_id"][kA]["lots"][0]["q"]=ql;L2["par_id"][kA]["lots"][1]["q"]=qy;ev("L=>{S.enr.lots=L;render();}",L2)
    VF(sects=["Laboratoires|CONTROLE DE QUALITE"]);G=GOT();a1=G.get(kA,{}).get("lots")
    VF(qqual=["Equipement|Y|Y1"]);G=GOT();a2=G.get(kA,{}).get("lots")
    VF(qcls=["Laboratoires|4"],qqual=["Equipement|Y|Y1"]);G=GOT();a3=kA in G
    VF();pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dn-cond");pg.wait_for_timeout(200);ev("()=>{MPV.dwOpen={qual:true};mpvDwRender();}");pg.wait_for_timeout(200)
    opt=ev("()=>[...document.querySelectorAll('[data-mpv-o^=\"sects:\"]')].map(b=>b.dataset.mpvO)");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    chk(a1==["1"] and a2==["2"] and not a3 and "sects:Laboratoires|CONTROLE DE QUALITE" in opt,f"secteur publié sans code (Laboratoires) filtrable par son libellé, Y / Y1 gardés ; classe Laboratoires du lot 1 ET qualification Y1 du lot 2 : pas de correspondance croisée")
    ev("L=>{S.enr.lots=L;render();}",LOTS)
    # ===== F3. visite non lue (ancienne lecture) : inconnue, jamais « non indiquée » =====
    kV=next(k for k in OUV if X[k]["det"] and not X[k]["vis"] and not (X[k]["lots"] or X[k]["allot"]))
    VF(vis="non");a0=kV in GOT()
    ev("k=>{S.enr.fiches={inaccessibles:{},visite_non_lue:[k]};render();}",kV)
    VF(vis="non");a1=kV in GOT();VF(vis="non",inc=["vis"]);G=GOT();a2=G.get(kV,{}).get("unk")
    ev("k=>{MPV.sel=k.slice(5);render();}",kV);pv=ev("()=>(document.querySelector('[data-mpv-panel] [data-mpv-vis]')||{dataset:{}}).dataset.mpvVis")
    ev("()=>{delete S.enr.fiches;render();}")
    chk(a0 and not a1 and a2 is True and pv=="non_lue",f"visite d'une ancienne lecture : exclue de « non indiquée », incluse seulement sur demande comme inconnue ; fiche « {pv} »")
    # ===== F4. Disponibilité : un compteur par champ, visite non lue sur sa propre ligne =====
    kV2=sorted(k for k in OUV if X[k]["det"] and not (X[k]["lots"] or X[k]["allot"]))[:3]
    ev("ks=>{S.enr.fiches={inaccessibles:{},visite_non_lue:ks};render();}",kV2)
    VF();pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dn-dispo");pg.wait_for_timeout(200)
    DI=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-mpv-cov^=\"u-\"]')].map(l=>[l.dataset.mpvCov.slice(2),[+l.dataset.mpvN,l.innerText]]))")
    old=ev("()=>document.getElementById('mpv-s-dispo').innerText.includes('Sans qualification / agrément / visite connus')");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    nvis=ev("()=>MPV.base.R.filter(e=>MPV_UNK.vis(e.x)).length");ev("()=>{delete S.enr.fiches;render();}")
    chk(sorted(DI)==sorted(["qual","ag","vis","tp","mts","cau","doms"]) and not old and DI["vis"][0]==nvis and DI["vis"][0]>=3 and "ancienne lecture" in DI["vis"][1],f"Disponibilité : un compteur par champ ; visite inconnue {DI['vis'][0]} sur sa propre ligne ({DI['vis'][1][:120]}) ; plus de libellé fusionné")
    # ===== G. puces, brouillon, recherche enregistrée =====
    VF(mts=["1-5"],tp="oui");CH=ev("()=>[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.innerText)");pg.click('.mpv-r4 [data-vfx="tp"]');pg.wait_for_timeout(300)
    chk(len(CH)==2 and ev("()=>[S.vf.tp,S.vf.mts.length]")==["",1] and kA in GOT(),"puces : retirer « TPE » rend l'annonce A (lot 1)")
    pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.click("#mpv-dn-cond");pg.wait_for_timeout(200);ev("()=>{MPV.dwOpen={tp:true};mpvDwRender();}");pg.wait_for_timeout(200)
    pg.click('[data-mpv-o="tp:oui"]');pg.wait_for_timeout(200);dn=ev("()=>+document.querySelector('[data-mpv-dwn]').dataset.mpvDwn");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    chk(dn==len(expect([("mts",mts15),("tp",tpo)])) and ev("()=>S.vf.tp")=="","brouillon : compte avec « TPE » recalculé par lot, Annuler n'applique rien")
    nw=len(W());VF(mts=["1-5"],tp="oui");pg.click("#mpv-tf");pg.wait_for_timeout(300);pg.fill("#mpv-svn","QA lots TPE 1-5M");pg.click("#mpv-svb");pg.wait_for_timeout(500);pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    VF();sv=ev("()=>S.saved.find(r=>r.nom==='QA lots TPE 1-5M')");ev("v=>{S.vf={...JSON.parse(JSON.stringify(VF0)),...v,sort:S.vf.sort};render();}",sv["vf"]);pg.wait_for_timeout(250)
    chk([w for w in W()[nw:]]==[["set","veille/recherches"]] and kA not in GOT() and kB in GOT(),"recherche enregistrée puis rechargée : même règle par lot")
    # ===== H. sans données par lot : rien n'est inventé =====
    ev("()=>{S.enr.lots=null;render();}");VF(tp="oui");G=GOT();ev("L=>{S.enr.lots=L;render();}",LOTS)
    chk(not any(k in G for k in AL),"données par lot absentes : aucune annonce allotie retenue sur un critère par lot")
    if REAL:
        ev("L=>{S.enr.lots=L;render();}",REAL)
        RK=[k for k in AL if k in REAL["par_id"] and nref(REAL["par_id"][k]["ref"])==nref(X[k]["ref"])]
        VF(tp="oui");G=GOT();bad=[k for k in RK if (k in G)!=any(l.get("tp") is True for l in REAL["par_id"][k]["lots"])]
        chk(not bad,f"données réelles publiées : {len(RK)} annonces alloties lues ; « TPE » retenue ⇔ un lot réservé ({len([k for k in RK if k in G])})")
        ev("L=>{S.enr.lots=L;render();}",LOTS)
    ev("()=>{S.enr.lots=window.__lots0;render();}")
    chk(len([w for w in W()[w0:] if w[1]!="veille/recherches"])==0 and AK()==k0,"aucune écriture métier, aucun dossier créé")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
    ctx.close()
    for w,sch in ((390,"light"),(1440,"dark")):
        c=b.new_context(viewport={"width":w,"height":860},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function(WAIT,timeout=30000);q.wait_for_timeout(400);q.evaluate(B11);q.wait_for_timeout(500)
        q.evaluate("L=>{S.enr.lots=L;S.vf={...JSON.parse(JSON.stringify(VF0)),sort:S.vf.sort,tp:'oui'};MPV.sel=null;render();}",LOTS);q.evaluate("k=>{MPV.sel=k.slice(5);MPV.mob='panel';render();}",kA);q.wait_for_timeout(300)
        M_=q.evaluate("()=>({doc:document.documentElement.scrollWidth-document.documentElement.clientWidth,lots:document.querySelectorAll('.mpv-lot').length})")
        q.screenshot(path=f"{OUT}/mpv4_lots_{w}_{sch}.png",full_page=False);chk(M_["doc"]<=0 and M_["lots"]==2 and not e,f"{w} px {sch} : détail par lot sans débordement {M_}")
        c.close()
    b.close()
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
