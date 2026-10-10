"""Recette b31-6b · (1) cartes de liste du bureau B3.1 recalculées avec la TVA documentée ; (2) « Enregistrer le sous-détail sans
changer le PU » (coût seul, historique, PU et verrous conservés) distinct de « Reporter » ; (3) bouton Sous-détail non rogné.
Fixtures fx-v6* de qa_b31_v6.py uniquement ; dossiers réels lus, jamais écrits."""
import os,sys,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
src6=open(os.path.join(ICI0,"qa_b31_v6.py"),encoding="utf-8").read().replace('OUT=os.path.join(ICI,"qa_b31_v6")','OUT=os.path.join(ICI,"qa_b31_v6b")')
exec(src6.split("\nwith sync_playwright() as p:")[0].replace('.replace(\'OUT=os.path.join(ICI,"qa_b31")\',\'OUT=os.path.join(ICI,"qa_b31_v6")\')','.replace(\'OUT=os.path.join(ICI,"qa_b31")\',\'OUT=os.path.join(ICI,"qa_b31_v6b")\')'))
def dhs(c):  # 241440.00 → « 241 440,00 » (espace fine insécable ou normale selon fmtN)
    e,d=divmod(c,100);return re.sub(r"\B(?=(\d{3})+(?!\d))"," ",str(e))+","+f"{d:02d}"
norm=lambda t:t.replace(" "," ").replace("\xa0"," ")
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    W=lambda:len(ev("()=>window.__writes"));WS=lambda n:ev("()=>window.__writes")[n:]
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}")
    RES="id=>{const s=aoSteps(id,S.ao[id]).find(x=>x.k==='prix');return s&&s.res}"
    # ===== 1. cartes de liste =====
    w0=W();T20=tvai(HT,20);h10=HTL["0-1"]+HTL["0-3"];TM=tvai(h10,10)+tvai(HT-h10,20);T10=tvai(HT,10)
    r=norm(ev(RES,"fx-v6a"));chk("Bordereau chiffré, à valider : "+dhs(HT)+" DH HT · TTC non calculé — TVA à renseigner" in r and dhs(HT+T20) not in r,f"carte, taux absent : HT et « TTC non calculé — TVA à renseigner », aucun TTC à 20 % ({r})")
    r=norm(ev(RES,"fx-v6h"));chk(r.endswith("Bordereau chiffré, à valider : "+dhs(HT+T10)+" DH TTC — TVA 10 % hypothèse non confirmée"),f"carte, taux en hypothèse : TTC v6 nommé hypothèse ({r})")
    r=norm(ev(RES,"fx-v6x"));chk(r.endswith("Bordereau chiffré, à valider : "+dhs(HT+TM)+" DH TTC (TVA mixte (20 %, 10 %) confirmée)"),f"carte, DCE mixte : total v6 par taux ({r})")
    r=norm(ev(RES,"fx-v6t"));chk(r.endswith("Bordereau chiffré, à valider : "+dhs(HT+T20)+" DH TTC"),f"carte, taux confirmé unique : libellé existant, TTC v6 ({r})")
    L=norm(ev("()=>{MPN.bur='MP-B3.1';const t=document.createElement('div');t.innerHTML=mpnFile('prix');return t.innerText}"))
    chk(dhs(HT)+" DH HT · TTC non calculé — TVA à renseigner" in L and "TVA 10 % hypothèse non confirmée" in L and "TVA mixte (20 %, 10 %) confirmée" in L,"liste du bureau B3.1 (mpnFile « prix ») : mêmes résumés que les cartes")
    r=norm(ev(RES,BG)or"");chk("TTC non calculé — TVA à renseigner" in r,f"réel BG (lecture) : la carte ne prétend plus un TTC à 20 % ({r[-90:]})")
    r=norm(ev("id=>b31ResumeTTC(id,S.ao[id])","fx-v6a"));chk(r==dhs(HT)+" DH HT · TTC non calculé — TVA à renseigner","parcours express : même résumé (b31ResumeTTC)")
    vh=ev("""()=>{const id='fx-v6t',a=S.ao[id],X=bpX(id),t0=X.tva;b31Valider(id,a);b31Valider(id,a);X.tva=null;const r=aoSteps(id,a).find(x=>x.k==='prix').res;X.tva=t0;return r}""")
    chk("montant historique de l'offre figée, pas un TTC actuel (TVA non renseignée)" in vh,f"montant validé antérieur affiché alors que la TVA n'est plus renseignée : nommé historique ({norm(vh)[-110:]})")
    chk(not [w for w in WS(w0) if not any(f"/{x}" in w[1] or f"/{x}~" in w[1] for x in ("fx-v6t",))],"cartes : lecture seule (seule la validation fictive fx-v6t a écrit)")
    # ===== 2. sous-détail : coût seul, PU inchangé =====
    ouvrir(pg,"fx-v6k");P0=ev("()=>window.__DB.bpx['fx-v6k'].p");L0=ev("()=>window.__DB.bpx['fx-v6k'].lock");S0=ev("()=>window.__DB.bpx['fx-v6k'].srcL||{}");p0=ev("()=>JSON.stringify(window.__DB.bpx['fx-v6k'].p)")
    pg.click('[data-b31-sd="0-4"]');pg.click('[data-b31-sdopen="0-4"]');pg.wait_for_selector(".b31-sdp")
    chk(pg.locator("[data-b31-sdsave]").count()==1 and pg.locator("[data-b31-sdrep]").count()==0 and "Ligne verrouillée" in pg.inner_text(".b31-sdp"),"ligne verrouillée : « Enregistrer le sous-détail sans changer le PU » proposé, « Reporter » absent")
    w0=W();pg.fill('[data-b31sd="mo|0|pu"]',"35");pg.wait_for_timeout(300)
    chk(W()==w0 and pg.is_visible("[data-b31-sdpend]"),"modification du coût : rien n'est écrit en arrière-plan, « non enregistrées » affiché")
    ev("()=>{const Y=bpX('fx-v6k');}");pg.click("[data-b31-sdsave]");pg.wait_for_timeout(600)
    ww=WS(w0);D=ev("()=>window.__DB");e=D["chiffrage_evenements"]["fx-v6k~e1"]
    cr0=CR(DSR["0-4"])[1];cr1=CR([("mo",80,35),("mt",10,600),("tr",5,400)])[1]
    chk(ww==[["set","chiffrage_evenements/fx-v6k~e1"],["set","bpx/fx-v6k"]] and e["type"]=="cout" and e["lignes"]==[] and e["contexte"]["cout_avant"]["cout_revient"]==cr0 and e["contexte"]["cout_apres"]["cout_revient"]==cr1 and e["contexte"]["pu_actuel"]==28000,f"enregistrement coût seul : événement « cout » (coût de revient {cr0} → {cr1}, PU 28 000 inchangé) PUIS bordereau")
    chk(D["bpx"]["fx-v6k"]["p"]==P0 and D["bpx"]["fx-v6k"]["lock"]==L0 and (D["bpx"]["fx-v6k"].get("srcL") or {})==S0 and D["bpx"]["fx-v6k"]["sd"]["0-4"]["mo"][0]["pu"]==35,"tous les PU, verrous et provenances conservés ; sous-détail enregistré")
    mg=e["contexte"]["marge_unitaire"];chk(abs(mg-round(28000-cr1,2))<1e-9,f"marge calculée contre le PU de vente actuel : {mg} DH")
    pg.evaluate("()=>window.__persist()");pg.reload();pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.bpx['fx-v6k']",timeout=20000);pg.wait_for_timeout(800)
    ev("()=>{window.__toastLog=[];const o=window.toast;window.toast=m=>{window.__toastLog.push(String(m));return o(m);};}")
    ouvrir(pg,"fx-v6k");c=ev("()=>b31SdCalc('fx-v6k','0-4',S.ao['fx-v6k'])");chk(c["cr"]==cr1,"après rechargement : coût relu depuis le stockage")
    pg.click("[data-b31-hist]");pg.wait_for_selector("[data-b31-evcout]",state="attached");h=norm(pg.text_content("[data-b31-evcout]"))
    chk("coût de revient" in h and "(inchangé)" in h and "marge" in h,f"historique : coût avant / après, PU inchangé, marge ({h[:120]})");pg.click(".b31-dlg .fsx")
    pg.evaluate("()=>sessionStorage.removeItem('__qadb')")
    # coût partiel inconnu
    pg.click('[data-b31-sd="0-1"]');pg.click('[data-b31-sdopen="0-1"]');pg.wait_for_selector(".b31-sdp");w0=W();pg.fill('[data-b31sd="mat|0|pu"]',"");pg.wait_for_timeout(200);pg.click("[data-b31-sdsave]");pg.wait_for_timeout(600)
    e=ev("()=>Object.values(window.__DB.chiffrage_evenements).filter(e=>e.ao_id==='fx-v6k').sort((x,y)=>x.seq-y.seq).pop()");C=ev("id=>{const ET=b31Etat(id,S.ao[id]);return{k:ET.C.k,m:b31Marge(ET.C,ET.T)}}","fx-v6k")
    chk(e["type"]=="cout" and e["contexte"]["cout_apres"]["complet"] is False and e["contexte"]["cout_apres"]["cout_revient"] is None and C["k"]==5 and C["m"] is None and ev("()=>JSON.stringify(window.__DB.bpx['fx-v6k'].p)")==p0,"coût rendu partiel : enregistré « inconnu » (jamais 0), couverture 5/6, marge non calculée, PU inchangés")
    # échecs de stockage
    w0=W();pg.fill('[data-b31sd="mat|0|pu"]',"111");pg.wait_for_timeout(200);ev(FAIL_DB,"ev");pg.click("[data-b31-sdsave]");pg.wait_for_timeout(500);ev(OK_DB)
    chk([w for w in WS(w0) if w[0]!="REFUS"]==[] and ev("()=>!!B31.sdBase['fx-v6k']") and any("Sous-détail non enregistré" in x for x in ev("()=>window.__toastLog")),"historique refusé : rien n'est écrit, modifications toujours en attente, message « non enregistré »")
    w0=W();ev(FAIL_DB,"bpx");pg.click("[data-b31-sdsave]");pg.wait_for_timeout(500);ev(OK_DB);ww=WS(w0)
    chk(len(ww)==3 and ww[1]==["REFUS","bpx/fx-v6k"] and "echec" in json.dumps(ev("(d)=>window.__DB.chiffrage_evenements[d]",ww[2][1].split("/")[1])) and ev("()=>!!B31.sdBase['fx-v6k']") and ev("()=>JSON.stringify(window.__DB.bpx['fx-v6k'].p)")==p0,"bordereau refusé : événement « échec » ajouté, coût NON enregistré (en attente), PU inchangés")
    # le sous-détail en attente ne fuit pas par une autre action ; verrou refusé tant qu'il est en attente
    w0=W();ev("async()=>{await b31Manuel('fx-v6k',S.ao['fx-v6k'],'0-2','3333')}");pg.wait_for_timeout(300);D=ev("()=>window.__DB.bpx['fx-v6k']")
    chk(D["p"]["0-2"]==3333 and D["sd"]["0-1"]["mat"][0]["pu"]=="" ,"saisie d'un PU pendant un sous-détail en attente : le PU est écrit, le sous-détail non enregistré n'est PAS écrit avec lui")
    pg.click(".b31-sdp .fsx");w0=W();pg.click('[data-b31-lock="0-0"]');pg.wait_for_timeout(300)
    chk(W()==w0 and any("avant de changer un verrou" in x for x in ev("()=>window.__toastLog")),"changement de verrou refusé tant qu'un sous-détail est en attente (aucune écriture)")
    ev("()=>{B31.sd={id:'fx-v6k',k:'0-1'};render();}");pg.wait_for_selector("[data-b31-sdannul]");pg.click("[data-b31-sdannul]");pg.wait_for_timeout(200)
    chk(not ev("()=>!!B31.sdBase['fx-v6k']") and ev("()=>bpX('fx-v6k').sd['0-1'].mat[0].pu")=="","« Annuler les modifications » : retour au sous-détail enregistré")
    # « Reporter » reste distinct et explicite (ligne non verrouillée)
    pg.fill('[data-b31sd="mat|0|pu"]',"100");pg.wait_for_timeout(200);w0=W();pg.click("[data-b31-sdrep]");pg.wait_for_timeout(600);D=ev("()=>window.__DB.bpx['fx-v6k']");e=ev("()=>Object.values(window.__DB.chiffrage_evenements).filter(e=>e.ao_id==='fx-v6k').sort((x,y)=>x.seq-y.seq).pop()")
    chk(e["type"]=="sous_detail" and e["contexte"]["cout_apres"]["complet"] and D["p"]["0-1"]==e["lignes"][0]["apres"] and D["sd"]["0-1"]["mat"][0]["pu"]==100 and D["lock"]=={"0-4":True},"« Reporter » : action distincte, coût et PU écrits ensemble après l'événement, verrous intacts")
    # ===== 3. bouton Sous-détail non rogné (1440) =====
    ouvrir(pg,"fx-v6k");o=ev("()=>[...document.querySelectorAll('tr.b31-r .b31-sdb')].map(b=>{const r=b.getBoundingClientRect(),c=b.closest('td').getBoundingClientRect();return[b.scrollWidth<=b.clientWidth+1,r.right<=c.right+0.5,r.left>=c.left-0.5]})")
    chk(o and all(all(x) for x in o),f"1440 : bouton « Sous-détail » entièrement visible dans sa cellule ({len(o)} lignes)");pg.screenshot(path=f"{OUT}/fx_v6b_1440.png")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
    reel1=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    o0,o1=json.loads(reel0),json.loads(reel1);vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x
    o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    chk(o0==o1 and not ecr_reel(pg),f"dossiers réels : inchangés, aucune écriture {ecr_reel(pg)[:2]}");ctx.close()
    for (w,hh,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre")):
        ctx,pg,errs=demarrer(b,w,hh,sch);ev=lambda js,*a:pg.evaluate(js,*a);ouvrir(pg,"fx-v6k")
        L=ev("()=>{const r=document.querySelector('tr.b31-r');return{d:getComputedStyle(r).display,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth}}")
        chk(L["d"]=="grid" and L["ov"]<=1,f"{tag} : lignes en cartes inchangées, aucun débordement ({L['ov']} px)")
        pg.click('[data-b31-sd="0-4"]');pg.click('[data-b31-sdopen="0-4"]');pg.wait_for_selector("[data-b31-sdsave]");pg.wait_for_timeout(600);pg.screenshot(path=f"{OUT}/fx_v6b_sousdetail_{tag}.png")
        ov=ev("()=>{const p=document.querySelector('.b31-sdp');return Math.max(document.documentElement.scrollWidth-document.documentElement.clientWidth,p.scrollWidth-p.clientWidth)}");chk(ov<=1 and not errs,f"{tag} : panneau sous-détail (deux actions) sans débordement, aucune erreur ({ov} px)");ctx.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
