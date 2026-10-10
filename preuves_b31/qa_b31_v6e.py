"""Recette b31-6e · arrêté en lettres dans la carte Récapitulatif (même formule que le PDF), dynamique ; fixtures fx-v6* seulement."""
import os,sys,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
src6=open(os.path.join(ICI0,"qa_b31_v6.py"),encoding="utf-8").read().replace('OUT=os.path.join(ICI,"qa_b31_v6")','OUT=os.path.join(ICI,"qa_b31_v6e")')
exec(src6.split("\nwith sync_playwright() as p:")[0])
sp=lambda t:re.sub(r"\s+"," ",str(t).replace(" "," ").replace("\xa0"," ")).strip()
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    ARR="()=>{const e=document.querySelector('#b31-recap [data-b31-arrete]'),t=document.querySelector('#b31-recap .b31-ttc');return e?{k:e.dataset.b31Arrete,t:e.textContent,apres:t&&t.nextElementSibling===e}:null}"
    chk(ev("()=>enLettres(3048097.90)")=="Trois millions quarante-huit mille quatre-vingt-dix-sept dirhams et quatre-vingt-dix centimes" and ev("()=>b31ArreteTxt(304809790)")=="Arrêté le présent bordereau à la somme de : Trois millions quarante-huit mille quatre-vingt-dix-sept dirhams et quatre-vingt-dix centimes toutes taxes comprises.","formule commune : 3 048 097,90 → « Arrêté le présent bordereau à la somme de : Trois millions … quatre-vingt-dix centimes toutes taxes comprises. »")
    ouvrir(pg,"fx-v6t");a=ev(ARR);ttc=ev("id=>b31Etat(id,S.ao[id]).T.ttcC","fx-v6t")
    chk(a and a["k"]=="ok" and a["apres"] and sp(a["t"])==sp(ev(f"()=>b31ArreteTxt({ttc})")),f"Récapitulatif (TVA 20 % confirmée) : arrêté juste sous Total TTC — « {sp(a['t'])[:100]}… »")
    pdf=ev("id=>{const {dd}=b31PdfDoc(id,S.ao[id]);return JSON.stringify(dd.content)}","fx-v6t")
    chk(json.dumps(a["t"],ensure_ascii=False)[1:-1] in pdf or a["t"] in json.loads(json.dumps(pdf)),"texte identique à l'arrêté du PDF du bordereau")
    tb=sp(pg.inner_text(".b31-arr"));chk(sp(a["t"]) in tb,"la phrase sous le tableau utilise la même formule")
    pg.screenshot(path=f"{OUT}/recap_1440.png",clip={"x":1080,"y":0,"width":360,"height":900}) if False else pg.locator("#b31-recap").screenshot(path=f"{OUT}/recap_1440.png")
    # dynamique : PU puis TVA
    ev("async()=>{await b31Manuel('fx-v6t',S.ao['fx-v6t'],'0-1','215')}");pg.wait_for_timeout(500);a2=ev(ARR);t2=ev("id=>b31Etat(id,S.ao[id]).T.ttcC","fx-v6t")
    chk(t2!=ttc and sp(a2["t"])==sp(ev(f"()=>b31ArreteTxt({t2})")),f"après changement de PU (ligne 2 → 215) : arrêté recalculé ({t2/100:.2f} TTC)")
    ev("async()=>{const id='fx-v6t',a=S.ao[id];B31.tvaEd[id]={taux:'10',etat:'confirme',doc:'CPS FICTIF art. 9',page:'3',mixte:false,lignes:{}};await b31TvaEnregistrer(id,a);}");pg.wait_for_timeout(500)
    a3=ev(ARR);t3=ev("id=>b31Etat(id,S.ao[id]).T.ttcC","fx-v6t");chk(t3<t2 and sp(a3["t"])==sp(ev(f"()=>b31ArreteTxt({t3})")),f"après changement de TVA (20 → 10 %) : arrêté recalculé ({t3/100:.2f} TTC)")
    ouvrir(pg,"fx-v6x");a=ev(ARR);t=ev("id=>b31Etat(id,S.ao[id]).T.ttcC","fx-v6x");chk(a["k"]=="ok" and sp(a["t"])==sp(ev(f"()=>b31ArreteTxt({t})")),"TVA mixte : arrêté sur le TTC calculé par taux")
    ouvrir(pg,"fx-v6a");a=ev(ARR);chk(a["k"]=="indisponible" and "TVA non renseignée" in a["t"] and "dirham" not in a["t"] and a["apres"],f"TVA absente : « {sp(a['t'])} » (aucun montant)")
    ev("async()=>{await b31Manuel('fx-v6s',S.ao['fx-v6s'],'0-2','')}");ouvrir(pg,"fx-v6s");a=ev(ARR);chk(a["k"]=="indisponible" and "1 PU manquant(s) sur 6" in a["t"] and "dirham" not in a["t"],f"bordereau incomplet : « {sp(a['t'])} »")
    ouvrir(pg,BG);a=ev(ARR);chk(a["k"]=="indisponible" and "TVA non renseignée" in a["t"],"réel BG (lecture, base simulée) : arrêté non disponible tant que la TVA n'est pas renseignée")
    reel1=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    o0,o1=json.loads(reel0),json.loads(reel1);vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x;o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    chk(o0==o1 and not ecr_reel(pg) and not errs,f"dossiers réels inchangés, aucune écriture réelle, aucune erreur {errs[:2]}");ctx.close()
    for (w,hh,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre"),(1440,900,"dark","1440_sombre")):
        c=b.new_context(viewport={"width":w,"height":hh},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q.wait_for_timeout(800);ouvrir(q,"fx-v6t")
        r=q.evaluate("()=>{const e=document.querySelector('#b31-recap [data-b31-arrete]'),R=e.getBoundingClientRect(),C=document.querySelector('#b31-recap .b31-rec').getBoundingClientRect(),cs=getComputedStyle(e);return{ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,dans:R.left>=C.left-0.5&&R.right<=C.right+0.5,coul:cs.color,fond:cs.backgroundColor}}")
        chk(r["ov"]<=1 and r["dans"] and not e,f"{tag} : arrêté lisible dans la carte, sans débordement (texte {r['coul']} sur {r['fond']})");q.locator("#b31-recap").screenshot(path=f"{OUT}/recap_{tag}.png");c.close()
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
