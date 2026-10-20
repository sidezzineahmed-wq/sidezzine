"""Recette complémentaire mpv-6 : NOUVEAU dossier groupe (créé par « Suivre », sans société) -> dépôt ZIP (échec puis réussite),
« reçu » seulement avec de vrais fichiers DCE persistés ; faux positifs (demande, marqueurs, pièce étrangère, inventaire PMMP) ;
Ouvrir le dossier -> Décision sans société imposée ; lecture seule ; données réelles et historiques inchangées.
Base SIMULÉE locale (copie lue des dossiers réels + fictifs fx-*), aucun accès à EAIOS ni à PMMP."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(ICI0,"qa_mpv6.py"),encoding="utf-8").read()
exec(src.split("\nwith sync_playwright() as p:")[0].replace('OUT=os.path.join(ICI,"qa_mpv6")','OUT=os.path.join(ICI,"qa_mpv6b")'))
# faux positifs possibles de « reçu » (dossiers fictifs, chacun sa consultation)
M["ao"]["fx-m1"]=fx("990101","fxa",J(10),suivi={"niveau":"groupe"},dceDemandeLe=J(-1)+"T10:00:00Z",dceDemande=J(-1))                       # demande seule
M["ao"]["fx-m2"]=fx("990102","fxa",J(10),suivi={"niveau":"groupe"},dceRecupereLe=J(-1)+"T10:00:00Z",dceImport={"lot":"x","n":3,"zip":"DCE.zip"},
    dceRecup={"etat":"termine"},statut="À examiner")                                                                                              # marqueurs sans fichier
M["ao"]["fx-m3"]=fx("990103","fxa",J(10),suivi={"niveau":"groupe"},fichiers={"caution":{"id":"bc","nom":"caution.pdf"},"refs":{"id":"br","nom":"refs.pdf"}})  # pièces non DCE
M["ao"]["fx-m4"]=fx("990104","fxa",J(10),suivi={"niveau":"groupe"},fichiers={"dce":{"nom":"DCE.zip"}})                                      # fichier DCE non persisté (sans id)
M["ao"]["fx-m5"]=fx("990105","fxa",J(10),suivi={"niveau":"groupe"})
M["ao"]["fx-m5o"]=fx("990105","fxb",J(10),suivi={"niveau":"groupe"},fichiers={"dce":{"id":"bo","nom":"DCE_autre_organisme.pdf"}})          # DCE d'une AUTRE consultation (même numéro, autre organisme)
json.dump(M,open(os.path.join(SRV,"mockdb_mpv6.json"),"w",encoding="utf-8"),ensure_ascii=False)
MOCK=open(os.path.join(SRV,"mockdb_mpv6.json"),encoding="utf-8").read()
INIT=None;exec(INITSRC.replace('upload:async b=>({id:"qa"+(++_na)','upload:async b=>{if(window.__failUpload)throw{code:"quota_exceeded"};return{id:"qa"+(++_na)').replace('contentType:b.type}),list','contentType:b.type};},list'))
assert "__failUpload" in INIT
REELS=set(REEL)
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()")
    REEL0=ev("ids=>JSON.stringify(ids.map(i=>[i,window.__DB.ao[i]]))",sorted(REELS))
    ev("()=>{window.__jl=[];const o=logJ;logJ=t=>{window.__jl.push(String(t));return o(t);};}")   # journal capturé (la base simulée n'a pas collection().add)
    ev(B11);pg.wait_for_timeout(400)
    # ===== 1. nouveau dossier groupe par « Suivre » (consultation réelle du catalogue, ouverte, non suivie) =====
    x=ev("()=>{const dm=mpvDosMap();const e=mpvBase().R.find(e=>!e.x._ferme&&e.x._d>=3&&!dm[e.x.r+'/'+e.x.o]&&!S.ao['pmmp-'+e.x.r]&&!(mpvCf(e.x)&&mpvCfSt(e.x,'docs')==='lu'));return{k:e.k,r:e.x.r,o:e.x.o}}")
    ev("k=>{MPV.tab='cons';MPV.sel=k;MPV.conf={t:'suivre',k};render();}",x["k"]);pg.wait_for_timeout(300);pg.click('[data-mpv-confok]');pg.wait_for_timeout(1200)
    nid="pmmp-"+x["r"];d0=ev("i=>window.__DB.ao[i]",nid);gk=f"p:{x['o']}:{x['r']}"
    chk(d0 and "soc" not in d0 and "mode" not in d0 and "mem" not in d0 and (d0.get("suivi") or {}).get("niveau")=="groupe","nouveau dossier groupe créé par « Suivre » : aucun champ société (soc/mode/mem absents)")
    # ===== 2. panneau DCE du nouveau dossier : aucun « undefined », aucune société =====
    ev("k=>{MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.sel=k;render();}",gk);pg.wait_for_timeout(300)
    P=ev("()=>{const p=document.querySelector('[data-mpv6-dpanel]');return{k:p.dataset.mpv6Dpanel,t:p.innerText,h:p.innerHTML,st:p.querySelector('[data-mpv6-dst]').dataset.mpv6Dst,j:(p.querySelector('[data-mpv6-joindre]')||{dataset:{}}).dataset.mpv6Joindre}}")
    soc=[n for n in ("ALWAAD","SAKDAT","SIDITRAV","Société") if n.lower() in P["t"].lower()]
    chk(P["k"]==gk and P["st"]=="afaire" and P["j"]==nid and "undefined" not in P["h"] and "null" not in P["t"] and not soc,f"panneau DCE du nouveau dossier : À récupérer, dépôt sur {nid}, aucun « undefined »/« null », aucune société {soc}")
    # ===== 3. échec d'envoi : rien de rattaché, reste non reçu =====
    w0=len(W());ev("()=>{window.__failUpload=true;}");pg.set_input_files('[data-mpv6-joindre] input[type=file]',ZIPF)
    pg.wait_for_function("id=>!(S.dceIng||{})[id]",arg=nid,timeout=30000);pg.wait_for_timeout(600)
    wf=W()[w0:];F1=ev("i=>({mem:mpvDce([i]).k,db:Object.keys((window.__DB.ao[i]||{}).fichiers||{}),dcef:!!(window.__DB.dcef||{})[i],rec:(window.__DB.ao[i]||{}).dceRecupereLe||null,pan:document.querySelector('[data-mpv6-dst]').dataset.mpv6Dst})",nid)
    chk(not [w for w in wf if w[1].startswith(("ao/","dcef/"))] and F1["mem"]=="afaire" and F1["db"]==[] and not F1["dcef"] and F1["rec"] is None and F1["pan"]=="afaire",f"échec d'envoi : aucune écriture dossier/registre, statut reste « À récupérer » {F1} {wf}")
    # ===== 4. réussite : vrais fichiers DCE persistés -> reçu ; aucune société ni « undefined » écrits =====
    w0=len(W());ev("()=>{window.__failUpload=false;}");pg.set_input_files('[data-mpv6-joindre] input[type=file]',ZIPF)
    pg.wait_for_function("id=>!(S.dceIng||{})[id]",arg=nid,timeout=30000);pg.wait_for_timeout(1200)
    ws=W()[w0:];D=ev("i=>({a:window.__DB.ao[i],r:(window.__DB.dcef||{})[i]})",nid)
    keys=sorted((D["a"].get("fichiers") or {}).keys());dumps=json.dumps(D,ensure_ascii=False)
    chk(sorted(set(w[1] for w in ws if not w[1].startswith("journal")))==sorted(["ao/"+nid,"dcef/"+nid]) and all("undefined" not in w[1] for w in W()),f"réussite : écritures sur ao/{nid} et dcef/{nid} seulement, aucun chemin « undefined » {ws}")
    chk(any(re.fullmatch(r"dce(_\d+)?",k) for k in keys) and all((D["a"]["fichiers"][k] or {}).get("id") for k in keys) and "soc" not in D["a"] and "undefined" not in dumps
        and all("soc" not in (v or {}) for v in D["a"]["fichiers"].values()),f"fichiers DCE réellement persistés (avec identifiant d'asset), sans attribution à une société ; clés {keys}")
    pan=ev("()=>{const p=document.querySelector('[data-mpv6-dpanel]');return p?{st:p.querySelector('[data-mpv6-dst]').dataset.mpv6Dst,h:p.innerHTML}:null}")
    jrn=ev("()=>window.__jl.filter(q=>/DCE déposé|suivie \\(groupe\\)/.test(q))")
    chk(ev("i=>mpvDce([i]).k",nid)=="pret" and (pan is None or (pan["st"]=="pret" and "undefined" not in pan["h"])) and jrn and all("undefined" not in q for q in jrn),f"statut « DCE reçu » après fichiers joints ; journal sans « undefined » {jrn[:2]}")
    # persistance : rechargement de la page sur la base simulée enregistrée
    ev("()=>window.__persist()");pg.reload();pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>100",timeout=40000);pg.wait_for_timeout(800)
    chk(ev("i=>mpvDce([i]).k",nid)=="pret" and gk not in ev("()=>mpvDceGroupes(Date.now()).O.map(g=>g.k)"),"après rechargement : reçu relu de la base (fichiers persistés), sortie de la file DCE")
    # ===== 5. faux positifs : jamais « reçu » =====
    st=ev("()=>Object.fromEntries(['fx-m1','fx-m2','fx-m3','fx-m4','fx-m5','fx-m5o'].map(i=>[i,mpvDce([i]).k]))")
    G=ev("()=>{mpvDceGroupes(Date.now());return Object.fromEntries(['p:fxa:990101','p:fxa:990102','p:fxa:990103','p:fxa:990104','p:fxa:990105','p:fxb:990105'].map(k=>[k,MPV6.by.get(k).dce.k]))}")
    chk(st["fx-m1"]=="encours" and G["p:fxa:990101"]=="encours","demande seule : « Demande enregistrée », jamais reçu")
    chk(st["fx-m2"]=="afaire","marqueurs sans fichier (dceRecupereLe, dceImport, dceRecup terminé) : pas reçu")
    chk(st["fx-m3"]=="afaire","pièces non DCE (caution, références) : pas reçu")
    chk(st["fx-m4"]=="afaire","entrée DCE sans fichier persisté (pas d'identifiant d'asset) : pas reçu")
    chk(G["p:fxa:990105"]=="afaire" and G["p:fxb:990105"]=="pret","DCE d'une autre consultation (même numéro, autre organisme) : ne rend pas reçue celle-ci")
    inv=ev("()=>{const B=mpvBase(),dm=mpvDosMap();const e=B.R.find(e=>!e.x._ferme&&mpvCf(e.x)&&mpvCfSt(e.x,'docs')==='lu'&&(mpvCf(e.x).docs||[]).some(d=>d.type==='dce')&&dm[e.x.r+'/'+e.x.o]);if(!e)return null;const g=(mpvDceGroupes(Date.now()),MPV6.by.get('p:'+e.x.o+':'+e.x.r));return{k:g.k,dce:g.dce.k,f:mpv6Fichiers(g).length}}")
    chk(inv is None or (inv["f"]>0) == (inv["dce"] in ("pret","partiel")),f"inventaire PMMP lu avec un DCE publié : statut décidé par les seuls fichiers joints {inv}")
    # ===== 6. Ouvrir le dossier -> Décision : choix des sociétés seulement là, aucune imposée =====
    ev(B11);pg.wait_for_timeout(300);ev("k=>{MPV.tab='suiv';MPN.outil='veille';MPV.outil='veille';MPV6.ss.sel=k;MPV6.ss.q='';render();}",gk);pg.wait_for_timeout(300)
    w0=len(W());pg.click('[data-mpv6-panel] [data-mpv6-dossier]');pg.wait_for_timeout(800)
    dv=ev("()=>({id:S.aoId,t:document.getElementById('view').innerText})");sv=[(n,dv["t"][max(0,m.start()-70):m.start()+30].replace(chr(10)," | ")) for n in ("ALWAAD","SAKDAT","SIDITRAV") for m in re.finditer(n,dv["t"],re.I)][:4]
    chk(dv["id"]==nid and "undefined" not in dv["t"] and len(W())==w0,f"Ouvrir le dossier : dossier {nid} ouvert, aucun « undefined », rien d'écrit (sociétés citées : {sv})")
    # toutes les étapes du dossier groupe : aucun texte vide de société, « undefined », « NaN », aucune écriture
    steps=ev("()=>[...document.querySelectorAll('[data-mpn-dosbur]')].map(b=>b.dataset.mpnDosbur)");bad=[]
    for stp in steps:
        ev("i=>{S.aoId=i;}",nid);pg.click(f'[data-mpn-dosbur="{stp}"]');pg.wait_for_timeout(500)
        t=ev("()=>document.getElementById('view').innerText")
        for pat in (r"undefined",r"\bNaN\b",r"· ·",r"·\s*·",r"pour \.",r"de \)"):
            if re.search(pat,t):bad.append((stp,pat,t[max(0,re.search(pat,t).start()-60):re.search(pat,t).start()+40]))
    chk(steps and not bad and len(W())==w0 and not errs,f"{len(steps)} étapes du dossier groupe parcourues : aucun « undefined »/« NaN »/emplacement société vide, rien d'écrit {bad[:3]}")
    ev("i=>{MPN.dos=null;mpvOuvrir(i,null);}",nid);pg.wait_for_timeout(600)
    pg.click("text=Décision d'Ahmed");pg.wait_for_selector("[data-b21d]",timeout=15000);pg.wait_for_timeout(500)
    d1=ev("()=>({ns:!!document.querySelector('[data-b21d-nosel]'),cur:[...document.querySelectorAll('.b21d-it[aria-current=true]')].length,pan:!!document.querySelector('[data-b21d-panel]'),n:document.querySelectorAll('[data-b21d-item]').length,und:document.querySelector('[data-b21d]').innerHTML.includes('undefined')})")
    chk(d1["ns"] and d1["cur"]==0 and not d1["pan"] and d1["n"]>=2 and not d1["und"] and len(W())==w0,f"Décision : {d1['n']} sociétés proposées, aucune sélectionnée ni imposée, rien d'écrit {d1}")
    pg.click('[data-b21d-item="sakdat"]');pg.wait_for_timeout(400)
    chk(ev("()=>(document.querySelector('[data-b21d-panel]')||{dataset:{}}).dataset.b21dPanel")=="sakdat" and len(W())==w0,"choisir une société (clic) : panneau de cette société seulement, toujours rien d'écrit")
    pg.click('[data-b21d-godec]');pg.wait_for_timeout(400);pg.click('[data-b21d-choix="reex"]');pg.wait_for_timeout(200)
    pg.fill('[data-b21d-motif="s:sakdat"]',"Recette fictive : à réexaminer");pg.wait_for_timeout(200);pg.click('[data-b21d-confirmer]');pg.wait_for_timeout(1500)
    sib=nid+"~sakdat";S2=ev("ids=>ids.map(i=>window.__DB.ao[i]||null)",[nid,sib]);wd=[w for w in W()[w0:] if w[1].startswith("ao/")]
    chk(S2[1] and S2[1].get("soc")=="sakdat" and S2[1].get("base")==nid and (S2[1].get("decision") or {}).get("verdict")=="À reprendre" and "soc" not in S2[0] and "decision" not in S2[0]
        and sorted(set(w[1] for w in wd))==["ao/"+sib],f"décision confirmée : dossier séparé {sib} créé pour SAKDAT seulement à ce moment ; dossier groupe sans société ni décision {wd}")
    chk((S2[1].get("fichiers") or {}).get("dce",{}).get("id")==(S2[0].get("fichiers") or {}).get("dce",{}).get("id"),"le dossier séparé reprend le DCE reçu du dossier groupe (règle existante creerSib), sans autre pièce")
    # ===== 7. lecture seule (permissions existantes) =====
    ev(B11);pg.wait_for_timeout(300);ev("()=>{S.readOnly=true;MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.sel='p:fxa:990101';render();}");pg.wait_for_timeout(400)
    ro=ev("()=>{const p=document.querySelector('[data-mpv6-dpanel]');return{j:!!p.querySelector('[data-mpv6-joindre] input'),d:!!p.querySelector('[data-mpv6-demande]'),t:p.innerText.includes('Lecture seule')}}")
    ev("()=>{MPN.dos=null;mpvOuvrir('fx-m1','dec');}");pg.wait_for_timeout(900);rd=ev("()=>({p:!!document.querySelector('[data-b21d-prendre],[data-b21d-godec]')})")
    ev("()=>{S.readOnly=false;render();}")
    chk(not ro["j"] and not ro["d"] and ro["t"] and not rd["p"],f"lecture seule : ni dépôt, ni demande, ni décision possibles {ro} {rd}")
    # ===== 8. données réelles, signatures et historiques inchangés =====
    REEL1=ev("ids=>JSON.stringify(ids.map(i=>[i,window.__DB.ao[i]]))",sorted(REELS))
    chk(REEL1==REEL0 and not [w for w in W() if w[1].startswith("ao/") and w[1][3:] in REELS],"118 dossiers réels copiés (sociétés, décisions, decisionHist, pièces cachetées/signées) strictement inchangés")
    chk(not errs,f"aucune erreur JavaScript {errs[:3]}")
    # mobile : Décision sans société imposée
    ctx.close();ctx,pg,errs=demarrer(b,390,844);ev=lambda js,*a:pg.evaluate(js,*a)
    ev(B11);pg.wait_for_timeout(300)
    ev("i=>{MPN.dos=null;mpvOuvrir(i,'dec');}","fx-g1");pg.wait_for_selector("[data-b21d]",timeout=15000);pg.wait_for_timeout(500)
    m=ev("()=>({mob:document.querySelector('[data-b21d]').dataset.b21dMob,cur:document.querySelectorAll('.b21d-it[aria-current=true]').length,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth})")
    chk(m["mob"]=="list" and m["cur"]==0 and m["ov"]<=0 and not errs,f"mobile 390 px : Décision ouvre la liste des sociétés, aucune imposée, sans débordement {m}")
    ctx.close();b.close()
open(os.path.join(OUT,"resultat.txt"),"w",encoding="utf-8").write("\n".join(R))
print(sum(r.startswith("OK") for r in R),"/",len(R))
