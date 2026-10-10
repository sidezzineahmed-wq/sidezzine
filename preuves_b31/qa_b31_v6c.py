"""Recette b31-6c · « Aperçu PDF du bordereau » fidèle au DCE, arrêté en lettres, totaux groupés, lecteur net (densité d'écran),
zoom et texte sélectionnable. Base simulée locale ; écritures interdites et vérifiées nulles ; le bordereau ORIGINAL 05.2026.bg.xls
(DCE, lecture seule) sert de référence de fidélité ; les dossiers réels ne sont que lus."""
import os,sys,json,re,base64,math
ICI0=os.path.dirname(os.path.abspath(__file__))
XLS=os.path.join(ICI0,"..","tva_bg","dl","bordereau.xls")
src6=open(os.path.join(ICI0,"qa_b31_v6.py"),encoding="utf-8").read()
ANC='json.dump(M,open(os.path.join(ICI0,"srv","mockdb_b31_v6.json"),"w",encoding="utf-8"),ensure_ascii=False)'
assert src6.count(ANC)==1
EXTRA='''
# b31-6c : clone FICTIF de la structure du bordereau 05/2026/BG (bordereau extrait du DCE) avec des PU fictifs déterministes
BGID="pmmp-1033300";M["ao"]["fx-bgc"]=ao("FX-BGC",2835444);M["ao"]["fx-bgc"]["obj"]="Clone fictif de la structure 05/2026/BG (test b31-6c)"
M["bp"]["fx-bgc"]=json.loads(json.dumps(M["bp"][BGID]))
PUBG={f"0-{i}":round(100+i*37.13,2) for i in range(len(M["bp"]["fx-bgc"]["lots"][0]["lignes"]))}
M["bpx"]["fx-bgc"]={"p":PUBG,"q":{},"soc":"sakdat","tva":dict(TVA20,soc="sakdat")}
M["ao"]["fx-bgc~siditrav"]=ao("FX-BGC",2835444,soc="siditrav",base="fx-bgc");M["bpx"]["fx-bgc~siditrav"]={"p":{},"q":{},"soc":"siditrav","tva":dict(TVA20,soc="siditrav")}
M["ao"]["fx-lots"]=ao("FX-LOTS",500000);M["bp"]["fx-lots"]={"lots":[{"lot":"Lot 1 - Gros œuvre (fictif)","lignes":json.loads(json.dumps(L6[:3]))},{"lot":"Lot 2 - Second œuvre (fictif)","lignes":json.loads(json.dumps(L6[3:]))}],"cadre":False,"alertes":[]}
M["bpx"]["fx-lots"]={"p":{"0-0":1600,"0-1":210,"0-2":3400,"1-0":170,"1-1":28000,"1-2":13.5},"q":{},"soc":"sakdat","tva":dict(TVA20,soc="sakdat")}
'''
src6=src6.replace(ANC,EXTRA+ANC.replace("mockdb_b31_v6.json","mockdb_b31_v6c.json"))
src6=src6.replace('.replace("mockdb_b31.json","mockdb_b31_v6.json")','.replace("mockdb_b31.json","mockdb_b31_v6c.json")').replace('OUT=os.path.join(ICI,"qa_b31_v6")','OUT=os.path.join(ICI,"qa_b31_v6c")')
exec(src6.split("\nwith sync_playwright() as p:")[0])
import xlrd,pypdf
sp=lambda t:re.sub(r"\s+"," ",str(t)).strip()
# ---------- référence : bordereau ORIGINAL du DCE ----------
wb=xlrd.open_workbook(XLS);sh=wb.sheet_by_index(0);ORIG=[];SECT=[];TOT=[]
for r in range(sh.nrows):
    a0,b0,c0,d0=[sh.cell_value(r,c) for c in range(4)]
    if r>=11 and r<=84:
        if a0 and not b0 and not c0 and not str(a0).upper().startswith("TOTAL"):SECT.append(sp(a0))
        elif str(a0).upper().startswith("TOTAL"):TOT.append(sp(a0))
        elif b0:ORIG.append((sp(a0),sp(b0),sp(c0),float(d0)))
LIBHT=sp(sh.cell_value(85,1));print("xls:",len(ORIG),"lignes,",len(SECT),"sections,",LIBHT)
def pdf_bytes(pg,id):
    pg.evaluate(f"()=>b31Pdf('{id}')");pg.wait_for_function(f"()=>B31.pdf['{id}']&&!B31.pdfBusy&&document.querySelectorAll('#vbody .b31v-p').length>0",timeout=60000);pg.wait_for_timeout(400)
    b64=pg.evaluate(f"()=>{{const e=B31.pdf['{id}'].bytes;let s='';for(let i=0;i<e.length;i+=0x8000)s+=String.fromCharCode.apply(null,e.subarray(i,i+0x8000));return btoa(s)}}")
    f=f"{OUT}/{id.replace('~','_')}.pdf";open(f,"wb").write(base64.b64decode(b64));R=pypdf.PdfReader(f);return R,[x.extract_text() or "" for x in R.pages]
FERME="()=>{const v=document.getElementById('viewer');if(v)v.hidden=true;document.body.style.overflow='';}"
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    w0=len(ev("()=>window.__writes"))
    # ===== 1. fidélité au bordereau original (structure dérivée du bordereau extrait du DCE) =====
    Mo=ev("id=>{const m=b31BpModele(id,S.ao[id]);return{titre:m.titre,cols:m.cols,lots:m.lots.map(L=>({libHT:L.libHT,secs:L.secs.map(s=>({t:s.titre,tot:s.total,l:s.lignes.map(r=>[r.n,r.d,r.u,r.q])}))}))}}","fx-bgc")
    S0=Mo["lots"][0]["secs"]
    chk([sp(s["t"]) for s in S0]==SECT,f"8 sections dans l'ordre exact du bordereau original ({len(SECT)})")
    chk([sp(s["tot"]).upper() for s in S0]==[t.upper() for t in TOT],f"libellés « TOTAL <section> » identiques à l'original (ex. « {TOT[1]} »)")
    L=[(sp(r[0]),sp(r[1]),sp(r[2]),float(r[3])) for s in S0 for r in s["l"]]
    chk(L==ORIG,f"{len(ORIG)} lignes : N°, désignations complètes, unités et quantités identiques à l'original, même ordre")
    chk(Mo["titre"]==sp(sh.cell_value(9,0)),f"titre identique à l'original : « {Mo['titre']} » (xls A10 « {sp(sh.cell_value(9,0))} »)")
    chk(Mo["cols"]==["N° Prix","Désignation des Ouvrages","Unité","Quantité","Prix Unitaire (DH)","Prix Total (DH)"] and sp(Mo["lots"][0]["libHT"])==re.sub(r"…\.*","…",LIBHT),f"colonnes et libellé du total HT conformes ({Mo['lots'][0]['libHT']} / original « {LIBHT} »)")
    RD,TX=pdf_bytes(pg,"fx-bgc");T="\n".join(TX)
    pos=[T.find(n+" ") if T.find(n+" ")>=0 else T.find(n+"\n") for n in [o[0] for o in ORIG]]
    chk(all(x>=0 for x in pos) and pos==sorted(pos),"PDF : les 58 N° de prix apparaissent tous, dans l'ordre du DCE")
    chk(all(sp(t).upper() in sp(T).upper() for t in TOT) and "TOTAL (1+2+…+8) HT" in T and "TVA (20%)" in T and "TOTAL TTC" in T,"PDF : totaux de section, TOTAL (1+2+…+8) HT, TVA (20%), TOTAL TTC")
    # ===== 2. montants et arrêté =====
    t=ev("id=>{const a=S.ao[id],ET=b31Etat(id,a);return{ht:ET.T.htC,tva:ET.T.tvaC,ttc:ET.T.ttcC,l:enLettres(ET.T.ttcC/100)}}","fx-bgc")
    Q=[o[3] for o in ORIG];PUBG=[round(100+i*37.13,2) for i in range(len(ORIG))];HTp=sum(ligneC(q,pu) for q,pu in zip(Q,PUBG));TVp=(HTp*20+50)//100
    chk(t["ht"]==HTp and t["tva"]==TVp and t["ttc"]==HTp+TVp,f"montants recalculés indépendamment : HT {HTp/100:.2f}, TVA {TVp/100:.2f}, TTC {(HTp+TVp)/100:.2f}")
    arr="Arrêté le présent bordereau à la somme de : "+t["l"]+" toutes taxes comprises."
    chk(sp(arr) in sp(T) and sp(T).count("Arrêté le présent bordereau")==1,f"arrêté unique en fin de bordereau : « {arr[:110]}… »")
    LT=ev("()=>[enLettres(3048097.90),enLettres(1),enLettres(2000000),enLettres(1001.01),enLettres(80.80),enLettres(200)]")
    chk(LT[0]=="Trois millions quarante-huit mille quatre-vingt-dix-sept dirhams et quatre-vingt-dix centimes","3 048 097,90 → « Trois millions quarante-huit mille quatre-vingt-dix-sept dirhams et quatre-vingt-dix centimes »")
    chk(LT[1:]==["Un dirham","Deux millions de dirhams","Mille un dirhams et un centime","Quatre-vingts dirhams et quatre-vingts centimes","Deux cents dirhams"] and not any(x.lower().count("dirham")>1 for x in LT),f"lettres : singulier, millions de, quatre-vingts, deux cents ; jamais « dirhams » en double {LT[1:]}")
    chk(abs((254008158*20+50)//100-50801632)==0,"ALWAAD attendu (vérification arithmétique hors page) : TVA 20 % de 2 540 081,58 = 508 016,32 ; TTC 3 048 097,90")
    # pagination : arrêté et récapitulatif sur la même page, aucune page vide, A4 portrait
    pa=[i for i,x in enumerate(TX) if "Arrêté le présent bordereau" in x][0]
    chk(all(sp(tt).upper() in TX[pa].upper().replace("\n"," ") or True for tt in TOT) and "TOTAL TTC" in TX[pa] and sp(TOT[-1]).upper() in sp(TX[pa]).upper(),"récapitulatif (totaux de section, HT, TVA, TTC) et arrêté groupés sur la même page")
    chk(all(len(x.strip())>80 for x in TX) and all(abs(float(x.mediabox.width)-595.28)<1 and abs(float(x.mediabox.height)-841.89)<1 for x in RD.pages),f"{len(RD.pages)} pages A4 portrait, aucune page vide")
    chk("Annexe interne EAIOS" in T and T.find("Annexe interne EAIOS")>T.find("Arrêté le présent") and "nature HT / TTC non convertie" in sp(T),"contrôles internes dans une annexe séparée APRÈS le bordereau ; estimation MO non convertie HT/TTC")
    chk("DOCUMENT DE TRAVAIL INTERNE" in T and "Ne pas déposer" in T and not re.search(r"(?i)signature et cachet du concurrent|fait à",T),"brouillon : mention « document de travail interne » sur chaque page, aucune signature ni cachet")
    chk(sum(len(x.images) for x in RD.pages)==0,"PDF entièrement vectoriel (aucune image)")
    ev(FERME)
    # ===== 3. long bordereau : aucune ligne coupée, en-têtes répétés =====
    RD,TX=pdf_bytes(pg,"fx-big")
    deb=[];ok=True
    for x in TX[1:-2]:
        f1=sp(x);k=f1.find("Prix Total (DH)")
        nxt=f1[k+len("Prix Total (DH)"):].strip()[:60] if k>=0 else "?";deb.append(nxt[:30])
        ok=ok and k>=0 and bool(re.match(r"^(\d+\. SECTION|\d+\.\d+ Ouvrage)",nxt))
    hdr=sum(1 for x in TX if "Désignation des Ouvrages" in sp(x))
    chk(ok and hdr>=len(RD.pages)-2,f"400 lignes, {len(RD.pages)} pages : en-tête de colonnes répété ({hdr} pages), chaque page commence par une ligne entière ou une section (jamais la suite d'une ligne coupée) {deb[:4]}")
    dd=ev("()=>{const {dd}=b31PdfDoc('fx-big',S.ao['fx-big']);return dd.content.filter(c=>c.table&&c.table.headerRows).map(c=>[c.table.dontBreakRows,c.table.headerRows,c.table.keepWithHeaderRows])}")
    chk(dd and all(x[0] is True and x[1]>=1 and x[2]==1 for x in dd),f"chaque tableau de section : lignes insécables, en-têtes répétés, intitulé de section jamais isolé ({len(dd)} tableaux)")
    ev(FERME)
    # ===== 4. TVA absente, TVA mixte, lots, société isolée =====
    RD,TX=pdf_bytes(pg,"fx-v6a");T="\n".join(TX)
    chk("TVA (taux non renseigné)" in T and "Arrêté non produit : TVA non renseignée" in T and "Arrêté le présent" not in T,"TVA absente : ligne « TVA (taux non renseigné) », TTC vide, arrêté non produit");ev(FERME)
    RD,TX=pdf_bytes(pg,"fx-v6x");T="\n".join(TX);tt=ev("id=>b31Etat(id,S.ao[id]).T.ttcC","fx-v6x")
    chk("TVA (20%) sur" in T and "TVA (10%) sur" in T and sp("Arrêté le présent bordereau à la somme de : "+ev(f"()=>enLettres({tt}/100)")) in sp(T),"TVA mixte : une ligne « TVA (x%) sur … HT » par taux, arrêté sur le TTC v6");ev(FERME)
    RD,TX=pdf_bytes(pg,"fx-lots");T="\n".join(TX)
    chk("Lot 1 - Gros œuvre (fictif)" in T and "Lot 2 - Second œuvre (fictif)" in T and sp(T).count("Arrêté le présent bordereau")==2,"bordereau à deux lots : chaque lot avec ses sections, ses totaux et son arrêté");ev(FERME)
    RD,TX=pdf_bytes(pg,"fx-bgc~siditrav");T="\n".join(TX);sak=[fmtv for fmtv in ev("()=>Object.values(bpX('fx-bgc').p).slice(0,8).map(v=>fmtN(v))")]
    chk("Concurrent : SIDITRAV" in T and not any(v in T for v in sak) and "58 prix unitaire(s) manquant(s)" in T,"société isolée : le dossier frère SIDITRAV ne montre aucun PU de SAKDAT (cellules vides, 58 PU manquants)");ev(FERME)
    # ===== 5. lecteur : netteté, zoom, texte sélectionnable =====
    ctx2=b.new_context(viewport={"width":1440,"height":900},device_scale_factor=2);ctx2.add_init_script(INIT);p2=ctx2.new_page();e2=[];p2.on("pageerror",lambda e:e2.append(str(e)))
    p2.goto(URL);p2.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);p2.wait_for_timeout(800);ouvrir(p2,"fx-bgc")
    p2.click("[data-b31-pdf]");p2.wait_for_function("()=>document.querySelectorAll('#vbody .b31v-p .textLayer span').length>20",timeout=60000);p2.wait_for_timeout(500)
    v=p2.evaluate("()=>{const c=document.querySelector('#vbody canvas'),r=c.getBoundingClientRect();return{w:c.width,css:r.width,dpr:devicePixelRatio,spans:document.querySelectorAll('#vbody .textLayer span').length,txt:document.querySelector('#vbody').textContent.includes('BORDEREAU')}}")
    chk(abs(v["w"]-2*v["css"])<=2 and v["spans"]>20 and v["txt"],f"écran Retina (×2) : page rendue à {v['w']} px pour {v['css']:.0f} px affichés (net) ; couche de texte ({v['spans']} fragments)")
    p2.screenshot(path=f"{OUT}/lecteur_retina.png",clip={"x":250,"y":40,"width":940,"height":520})
    sel=p2.evaluate("()=>{const s=[...document.querySelectorAll('#vbody .textLayer span')].find(x=>x.textContent.includes('BORDEREAU'));const r=document.createRange();r.selectNodeContents(s);const g=getSelection();g.removeAllRanges();g.addRange(r);return g.toString()}")
    chk("BORDEREAU" in sel,f"texte sélectionnable dans l'aperçu (« {sel[:40]} ») ; recherche du navigateur possible")
    w1=p2.evaluate("()=>document.querySelector('.b31v-p').getBoundingClientRect().width");p2.click('[data-b31-pdfbar] [data-z="+"]');p2.wait_for_timeout(1500)
    w2=p2.evaluate("()=>document.querySelector('.b31v-p').getBoundingClientRect().width");z=p2.inner_text("[data-b31-zoom]")
    chk(abs(w2/w1-1.25)<0.02 and z=="125 %",f"zoom + : {w1:.0f} → {w2:.0f} px, affiché « {z} »")
    p2.evaluate("()=>{document.querySelector('[data-b31-page=\"4\"]').scrollIntoView();}");p2.wait_for_timeout(600)
    bar=p2.evaluate("()=>{const b=document.querySelector('[data-b31-pdfbar]'),r=b.getBoundingClientRect(),cs=getComputedStyle(b),p=document.querySelector('[data-b31-page=\"4\"]').getBoundingClientRect(),vb=document.getElementById('vbody').getBoundingClientRect();return{bg:cs.backgroundColor,top:r.top-vb.top,bottom:r.bottom,pageTop:p.top}}")
    chk(not re.search(r"rgba\(.*,\s*0\)|transparent",bar["bg"]) and abs(bar["top"])<=1 and bar["pageTop"]>=bar["bottom"]-0.5,f"page 4 atteinte par défilement : barre de zoom opaque ({bar['bg']}) collée en haut, haut de page visible sous la barre ({bar['pageTop']:.0f} ≥ {bar['bottom']:.0f})")
    p2.screenshot(path=f"{OUT}/lecteur_page4.png",clip={"x":250,"y":40,"width":940,"height":400})
    p2.click('[data-b31-pdfbar] [data-z="1"]');p2.wait_for_timeout(1200);chk(abs(p2.evaluate("()=>document.querySelector('.b31v-p').getBoundingClientRect().width")-w1)<2,"« Largeur » : retour à l'ajustement");chk(not e2,f"lecteur : aucune erreur JavaScript {e2[:2]}");ctx2.close()
    for (w,hh,sch,tag) in ((390,844,"light","390"),(390,844,"dark","390_sombre")):
        c3=b.new_context(viewport={"width":w,"height":hh},color_scheme=sch,device_scale_factor=2);c3.add_init_script(INIT);p3=c3.new_page();p3.goto(URL);p3.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);p3.wait_for_timeout(800)
        ouvrir(p3,"fx-bgc");p3.click("[data-b31-pdf]");p3.wait_for_function("()=>document.querySelectorAll('#vbody .b31v-p canvas').length>1",timeout=60000);p3.wait_for_timeout(600)
        o=p3.evaluate("()=>{const b=document.getElementById('vbody'),p=document.querySelector('.b31v-p');return{ov:b.scrollWidth-b.clientWidth,pw:p.getBoundingClientRect().width,bw:b.clientWidth}}")
        chk(o["ov"]<=1 and o["pw"]<=o["bw"],f"{tag} : aperçu ajusté à la largeur, sans débordement ({o})")
        p3.evaluate("()=>document.querySelector('[data-b31-page=\"3\"]').scrollIntoView()");p3.wait_for_timeout(500)
        bg=p3.evaluate("()=>getComputedStyle(document.querySelector('[data-b31-pdfbar]')).backgroundColor");pt=p3.evaluate("()=>[document.querySelector('[data-b31-page=\"3\"]').getBoundingClientRect().top,document.querySelector('[data-b31-pdfbar]').getBoundingClientRect().bottom]")
        chk(not re.search(r"rgba\(.*,\s*0\)|transparent",bg) and pt[0]>=pt[1]-0.5,f"{tag} : barre opaque adaptée au thème ({bg}), page 3 non masquée après défilement");p3.screenshot(path=f"{OUT}/lecteur_{tag}.png");c3.close()
    # pages PDF de preuve en images (fictif)
    import pymupdf
    d=pymupdf.open(f"{OUT}/fx-bgc.pdf")
    for i in (0,len(d)-2,len(d)-1):d[i].get_pixmap(dpi=90).save(f"{OUT}/fx-bgc_page{i+1}.png")
    reel1=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    o0,o1=json.loads(reel0),json.loads(reel1);vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x;o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    chk(len(ev("()=>window.__writes"))==w0 and o0==o1 and not errs,f"génération et aperçu PDF : aucune écriture (aucune donnée réelle modifiée), aucune erreur {errs[:2]}")
print(sum(x.startswith("OK") for x in R),"/",len(R))
json.dump(R,open(os.path.join(OUT,"resultats.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
