"""Test ciblé b31-2 : historique consultatif (aucune action legacy d'écriture) et verrous respectés par les chemins %, IA et rechargement.
Base simulée locale (harnais de qa_b31.py) ; écritures seulement sur les dossiers fictifs, dossiers réels lus."""
import os,sys,json
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"qa_b31.py"),encoding="utf-8").read()
exec(src.split("with sync_playwright() as p:")[0])
OK_RE=["propExport(","bpExport(","S.propOpen=","S.bpOpen","S.bpLot","S.simOpen","S.varOpen","S.dvOpen","B31.dlg=null"]
LEGACY_W=["propApply","offreRetenir","offreValider","bpSave","dvLire","dvBiblio","localStorage.removeItem","p.moi=","isoCheck","bpX(id)"]
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decisionPrix||null])})",REELS)
    # brut : les écrans hérités contiennent bien des actions d'écriture (sinon le test ne prouverait rien)
    raw=ev("id=>{const a=S.ao[id];return vOffres(id,a)+vPrixTrace(id,a)+vPropChiffreur(id,a)}",BG)
    chk("Appliquer au bordereau" in raw and "data-act" in raw,"BG : l'ancienne proposition contient le bouton legacy « Appliquer au bordereau » (cas réel)")
    ouvrir(pg,BG);pg.click("[data-b31-hist]");pg.wait_for_selector(".b31-dlg")
    def audit():
        return ev("""()=>{const d=document.querySelector('.b31-dlg');return{acts:[...d.querySelectorAll('[data-act]')].map(e=>[e.textContent.trim().slice(0,60),String(ACTS[e.dataset.act]||'').replace(/\\s+/g,' ')]),
          ro:[...d.querySelectorAll('[data-b31-ro]')].map(e=>e.textContent.trim()),actifs:[...d.querySelectorAll('input:not([disabled]),select:not([disabled]),textarea:not([disabled])')].length,
          upk:d.querySelectorAll('[data-upk]').length,docs:d.querySelectorAll('[data-doc],[data-dl]').length,txt:d.innerText}}""")
    A=audit()
    mut=[a for a in A["acts"] if any(w in a[1] for w in LEGACY_W) or not any(o in a[1] for o in OK_RE)]
    chk(not mut,f"historique BG : aucune action d'écriture legacy active ({len(A['acts'])} actions restantes, toutes de consultation) {mut[:3]}")
    chk(any("Appliquer au bordereau" in r for r in A["ro"]) and not any("Appliquer au bordereau" in a[0] for a in A["acts"]),f"« Appliquer au bordereau » affiché désactivé (lecture seule) : {[r[:60] for r in A['ro']][:4]}")
    chk(any("Télécharger" in a[0] for a in A["acts"]) and "Texte" not in "" and "Offres figées" in A["txt"] and "Ancienne proposition du Chiffreur" in A["txt"],"téléchargements et preuves (offres figées, ancienne proposition) conservés")
    chk(A["actifs"]==0 and A["upk"]==0,"aucun champ de saisie ni envoi de fichier actif dans l'historique")
    rawdocs=ev("id=>{const a=S.ao[id],t=document.createElement('template');t.innerHTML=vOffres(id,a)+vPrixTrace(id,a)+vPropChiffreur(id,a)+vSimu(id,a)+vSourcing(id,a);return t.content.querySelectorAll('[data-doc],[data-dl]').length}",BG)
    chk(A["docs"]==rawdocs,f"aperçus / téléchargements de documents conservés ({A['docs']}/{rawdocs})")
    # dépliage du simulateur hérité puis nouvel audit (les outils précédents restent consultatifs)
    pg.click(".b31-dlg details.b31-old summary");pg.wait_for_timeout(150)
    sb=pg.query_selector(".b31-dlg details.b31-old [data-act]")
    if sb:sb.click();pg.wait_for_timeout(300)
    if not pg.query_selector(".b31-dlg"):pg.click("[data-b31-hist]");pg.wait_for_selector(".b31-dlg")
    A2=audit();mut2=[a for a in A2["acts"] if any(w in a[1] for w in LEGACY_W) or not any(o in a[1] for o in OK_RE)]
    chk(not mut2 and A2["actifs"]==0,f"après dépliage des outils précédents : toujours aucune action ni saisie d'écriture ({len(A2['acts'])} actions)")
    # clic sur un libellé neutralisé : rien ne se passe
    w0=len(ev("()=>window.__writes"));bx0=ev("id=>JSON.stringify(S.bpx[id]||null)",BG)
    ro=pg.query_selector(".b31-dlg [data-b31-ro]")
    if ro:ro.click();pg.wait_for_timeout(300)
    chk(len(ev("()=>window.__writes"))==w0 and ev("id=>JSON.stringify(S.bpx[id]||null)",BG)==bx0,"clic sur l'action legacy neutralisée : aucune écriture, bordereau BG inchangé")
    chk(not any("b31Restaurer" in a[1] for a in A["acts"]+A2["acts"]) and not any("Recharger" in a[0] for a in A["acts"]),"historique : plus aucune action d'écriture, y compris « Recharger » (déplacé vers « Brouillons »)")
    pg.screenshot(path=f"{OUT}/bg_historique_consultatif.png")
    # ===== verrous : nouveaux chemins (fictif fx-trv) =====
    r=ev("""()=>{const id='fx-trv',a=S.ao[id],X=bpX(id);X.lock={};const p0=X.p['0-1'];B31.prev[id]=b31Previsu(id,a,-10);X.lock={'0-1':true};const n=window.__writes.length;
      b31Appliquer(id,a);return{p:X.p['0-1'],p0,w:window.__writes.length-n,prev:!!B31.prev[id]}}""")
    chk(r["p"]==r["p0"] and r["w"]==0 and not r["prev"],"% : ligne verrouillée APRÈS l'aperçu → rien n'est appliqué, aperçu à refaire")
    r=ev("""()=>{const id='fx-trv',a=S.ao[id],X=bpX(id);X.lock={'0-0':true};const p0=X.p['0-0'];B31.prev[id]=b31Previsu(id,a,-10);b31Appliquer(id,a);
      return{p:X.p['0-0'],p0,src:(X.srcL||{})['0-0']||null,autres:X.srcL['0-1']&&X.srcL['0-1'].m}}""")
    chk(r["p"]==r["p0"] and r["src"] is None and r["autres"]=="pct","% : ligne verrouillée inchangée, autres lignes ajustées")
    r=ev("""()=>{const id='fx-trv',a=S.ao[id],X=bpX(id);X.lock={'0-2':true};const p0=X.p['0-2'];b31Accepter(id,a,'0-2',99.99,'Claude (test)','2026-10-06');return{p:X.p['0-2'],p0}}""")
    chk(r["p"]==r["p0"],"IA : acceptation refusée sur une ligne verrouillée")
    r=ev("""async()=>{const id='fx-trv',a=S.ao[id],X=bpX(id);X.lock={};B31.vers[id]=[];const v=await b31Version(id,a,'base');X.p['0-0']=777.77;X.lock={'0-0':true};X.srcL['0-0']={m:'manuel'};
      for(let i=0;i<2;i++)await b31Restaurer(id,a,Object.assign({doc_id:id+'~v'+v.version},v));return{p0:X.p['0-0'],l:X.lock['0-0'],p1:X.p['0-1'],v1:v.pu['0-1']}}""")
    pg.evaluate("()=>{B31.dlg=null;render();}");ouvrir(pg,"fx-trv");pg.click("[data-b31-vers]");pg.wait_for_selector(".b31-dlg [data-b31-rest]")
    chk(pg.query_selector_all(".b31-dlg [data-b31-rest]") and "lignes verrouillées" in pg.inner_text(".b31-dlg"),"bureau : panneau « Brouillons » avec « Recharger dans le brouillon »")
    pg.screenshot(path=f"{OUT}/fx_brouillons.png");pg.click(".b31-dlg .fsx")
    chk(r["p0"]==777.77 and r["l"] is True and r["p1"]==r["v1"],"rechargement d'un brouillon : ligne verrouillée conservée, autres lignes rechargées")
    reel1=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decisionPrix||null])})",REELS)
    vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x  # bpX() initialise en mémoire un objet vide (comportement existant, jamais écrit)
    o0,o1=json.loads(reel0),json.loads(reel1);o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    if o0!=o1:print("DIFF",[k for k in o0 if o0[k]!=o1[k]],[i for i,(u,v) in enumerate(zip(o0["x"],o1["x"])) if u!=v])
    chk(o0==o1 and not ecr_reel(pg),"dossiers réels : aucune écriture, offres et prix inchangés")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
print(sum(x.startswith("OK") for x in R),"/",len(R))
