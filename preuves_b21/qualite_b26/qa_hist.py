"""Test ciblé b21-5 : observation historique (« soit demain ») face à l'échéance calculée aujourd'hui (date passée), écran et PDF."""
import os,sys,json,re,base64,pypdf
sys.argv=[sys.argv[0]]
src=open("qa.py").read();exec(src.split("R=[];chk=")[0])
R=[];chk=lambda c,t:(R.append(("OK " if c else "ECHEC ")+t),print(R[-1]))
BG="pmmp-1033300";D=json.load(open("srv/mockdb.json"));ALERTE=D["ao"][BG]["exig"]["alertes"][0]
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={"width":1440,"height":900});ctx.add_init_script(INIT)
    pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL);pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);pg.wait_for_timeout(800)
    ev=lambda js,*a:pg.evaluate(js,*a)
    avant=ev("id=>JSON.stringify(S.ao[id].exig)",BG)
    # 1. ordre et étiquettes (données réelles BG : date limite 25/09/2026, lecture du 24/09)
    O=ev("id=>{const a=S.ao[id],E=b21Etat(id,a);return b21Synth(id,a,E.F,E).O}",BG)
    chk(O[0].get("calc") and O[0]["t"].startswith("Date limite passée (25/09/2026"),f"1er obstacle = échéance calculée aujourd'hui : « {O[0]['t']} »")
    h=[o for o in O if o["t"]==ALERTE]
    chk(len(h)==1,"alerte historique « soit demain » reprise avec son texte d'origine exact (non réécrite)")
    o=h[0];lab=o.get("obs",{}).get("lab","")
    chk(o["obs"]["perime"] and re.search(r"Observation du 23/09/2026 \(heure du Maroc\)",lab) and "à réévaluer" in lab,f"alerte historique datée et étiquetée : « {lab} »")
    chk(O.index(o)>0 and all(not x.get("obs",{}).get("perime") for x in O[:O.index(o)] if not x.get("calc")) ,f"observation périmée classée après l'échéance calculée et les obstacles actuels (rang {O.index(o)+1}/{len(O)})")
    # 2. cas unitaires
    U=ev("""()=>[b21Obs("ouverture le 25/09/2026, soit demain","2026-09-24T10:00:00Z","lecture du DCE"),
      b21Obs("à remettre au plus tard le 01/09/2026","2026-08-20T10:00:00Z","lecture du DCE"),
      b21Obs("garantie exigée jusqu'au 31/12/2027","2026-09-24T10:00:00Z","lecture du DCE"),
      b21Obs("dépôt demain",null,"analyse juridique")].map(x=>x.obs)""")
    chk(U[0]["perime"] and "à réévaluer" in U[0]["lab"],f"« soit demain » → à réévaluer : {U[0]['lab']}")
    chk(U[1]["perime"] and U[1]["motif"]=="date citée déjà passée","date citée déjà passée → à réévaluer")
    chk(not U[2]["perime"] and "réévaluer" not in U[2]["lab"] and U[2]["lab"].startswith("Observation du"),f"date future sans formulation relative → datée, non périmée : {U[2]['lab']}")
    chk("date non enregistrée" in U[3]["lab"] and U[3]["perime"],f"sans date de lecture → « {U[3]['lab']} »")
    # 3. cas inverse : date limite demain (calcul du jour) + vieille alerte « demain »
    r=ev("""id=>{const a0=S.ao[id],t=new Date(today0().getTime()+864e5),iso=t.getFullYear()+'-'+String(t.getMonth()+1).padStart(2,'0')+'-'+String(t.getDate()).padStart(2,'0');
      const a=Object.assign({},a0,{lim:iso});const E=b21Etat(id,a);return b21Synth(id,a,E.F,E).O.map(o=>[o.t,!!o.calc,!!(o.obs&&o.obs.perime)])}""",BG)
    chk(r[0][1] and "dans 1 jour" in r[0][0] and r[-1][2],f"date limite réelle demain : échéance calculée en tête « {r[0][0]} », ancienne alerte en dernier")
    # 4. affichage de la synthèse
    ev("id=>{S.dept='ao';S.soc=null;S.aoId=id;render();}",BG);pg.click('[data-mpn-dosbur="MP-B2.1|note"]');pg.wait_for_selector("[data-b21]");pg.wait_for_timeout(500)
    li=ev("()=>[...document.querySelectorAll('.b21-obs li')].map(l=>l.innerText.replace(/\\s+/g,' '))")
    chk(li and li[0].startswith("Calcul du jour") and "Date limite passée" in li[0],f"synthèse écran, 1re ligne : « {li[0][:90] if li else ''} »")
    chk(all("Échéance immédiate" not in x or "Observation du" in x for x in li),"synthèse écran : aucune « Échéance immédiate … demain » sans date ni étiquette")
    pan=ev("""()=>{const b=document.querySelector('[data-b21-pan="obstacles"]');if(!b)return null;b.click();const d=document.getElementById('b21-dlg');const t=d?d.innerText:'';if(d)d.close();return t}""")
    chk(pan and "Texte d'origine conservé tel quel" in pan and ALERTE[:40] in pan.replace("\n"," ") and "Alerte relevée à la lecture du DCE" in pan,"panneau détaillé : texte d'origine intact, source et mention « texte d'origine conservé »")
    # 5. PDF (mêmes octets que l'aperçu et le téléchargement)
    b64=ev("async id=>{const e=await b21PdfOctets(id);let s='';for(let i=0;i<e.bytes.length;i+=0x8000)s+=String.fromCharCode.apply(null,e.bytes.subarray(i,i+0x8000));return btoa(s)}",BG)
    os.makedirs("qa_pdf",exist_ok=True);open("qa_pdf/BG_hist.pdf","wb").write(base64.b64decode(b64))
    P=pypdf.PdfReader("qa_pdf/BG_hist.pdf");T=re.sub(r"\s+"," "," ".join(x.extract_text() or "" for x in P.pages))
    i=T.find("Obstacles relevés");s=T[i:T.find("Prochaines actions",i)]
    chk("Calcul du jour" in s and s.find("Date limite passée")<s.find("Échéance immédiate"),"PDF : échéance calculée avant l'observation historique")
    j=s.find("Échéance immédiate");chk(j>0 and re.search(r"Observation du 23/09/2026 \(heure du Maroc\) · lecture du DCE — à réévaluer",s[max(0,j-120):j]) is not None,"PDF : observation historique précédée de sa date et de « à réévaluer »")
    chk("Texte d'origine conservé tel quel" in s,"PDF : mention du texte d'origine conservé")
    chk(ev("id=>JSON.stringify(S.ao[id].exig)",BG)==avant and ev("()=>window.__writes.length")==0,"données stockées inchangées, aucune écriture en base")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
print(sum(r.startswith("OK") for r in R),"/",len(R))
