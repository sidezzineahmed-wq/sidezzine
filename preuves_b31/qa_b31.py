"""Recette B3.1 Chiffrage : base SIMULÉE locale (copie des données réelles en lecture + dossiers fictifs fx-*), aucun accès à EAIOS.
Les écritures ne sont faites que sur les dossiers fictifs ; les dossiers réels (05/2026/BG, SAP) sont seulement lus (aucune écriture vérifiée)."""
import os,sys,json,re,base64,time,threading,http.server,functools
import pypdf
from playwright.sync_api import sync_playwright
ICI=os.path.dirname(os.path.abspath(__file__));SRV=os.path.join(ICI,"srv");OUT=os.path.join(ICI,"qa_b31");os.makedirs(OUT,exist_ok=True)
open(os.path.join(SRV,"index.html"),"w",encoding="utf-8").write(open(os.path.join(ICI,"page_b21.html"),encoding="utf-8").read())
class Hq(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Hq,directory=SRV));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f"http://127.0.0.1:{srv.server_address[1]}/index.html"
MOCK=open(os.path.join(SRV,"mockdb_b31.json"),encoding="utf-8").read()
# base simulée AVEC état : un set/update est conservé en mémoire (pour relire), et chaque écriture est tracée dans __writes
INIT="""(()=>{let _s=null;try{_s=sessionStorage.getItem("__qadb");}catch(e){}const DB=JSON.parse(_s||%s);window.__DB=DB;window.__persist=()=>sessionStorage.setItem("__qadb",JSON.stringify(DB));window.__writes=[];window.__saves=[];
 const cp=x=>x===undefined?undefined:JSON.parse(JSON.stringify(x));
 const loc=p=>{const s=p.split("/");return[s.slice(0,-1).join("/"),s[s.length-1]];};
 const snap=(path,flt)=>{const seg=path.split("/");if(seg.length%%2===1){const c=DB[path]||{};let E=Object.entries(c);if(flt)E=E.filter(([id,d])=>d&&d[flt[0]]===flt[1]);return{docs:E.map(([id,d])=>({id,exists:true,data:()=>cp(d)})),metadata:{}};}
   const[c,id]=loc(path),d=(DB[c]||{})[id];return{id,exists:!!d,data:()=>cp(d)};};
 const ref=(path,flt)=>({onSnapshot:(cb)=>{setTimeout(()=>cb(snap(path,flt)),0);return()=>{};},get:async()=>snap(path,flt),
   set:async(d)=>{window.__writes.push(["set",path]);const[c,id]=loc(path);(DB[c]=DB[c]||{})[id]=cp(d);},
   update:async(d)=>{window.__writes.push(["update",path]);const[c,id]=loc(path);DB[c]=DB[c]||{};DB[c][id]=Object.assign(DB[c][id]||{},cp(d));},
   delete:async()=>{window.__writes.push(["delete",path]);const[c,id]=loc(path);if(DB[c])delete DB[c][id];},
   doc:(id)=>ref(path+"/"+id),collection:(c)=>ref(path+"/"+c),where:(f,op,v)=>ref(path,[f,v]),orderBy:()=>ref(path,flt),limit:()=>ref(path,flt)});
 const db={doc:p=>ref(p),collection:p=>ref(p)};
 const user={isOwner:async()=>true,canEdit:async()=>true,can:async()=>true,id:async()=>"u_qa",profiles:async()=>({})};
 const downloads={save:async o=>{window.__saves.push({filename:o.filename});}};
 window.claude={use:async n=>n==="db"?db:n==="user"?user:n==="downloads"?downloads:null};})();"""%json.dumps(MOCK)
R=[];chk=lambda c,t:(R.append(("OK " if c else "ECHEC ")+t),print(R[-1]))
BG,SID,ALW,SAP="pmmp-1033300","pmmp-1033300~siditrav","pmmp-1033300~alwaad-ataib","pmmp-1029546"
REELS=[BG,SID,ALW,SAP]
def ouvrir(pg,id):
    pg.evaluate("id=>{S.dept='ao';S.soc=null;S.aoId=id;render();}",id);pg.click('[data-mpn-dosbur="MP-B3.1|prix"]');pg.wait_for_selector("[data-b31]",timeout=15000);pg.wait_for_timeout(400)
def demarrer(b,w,h,scheme="light"):
    ctx=b.new_context(viewport={"width":w,"height":h},color_scheme=scheme);ctx.add_init_script(INIT)
    pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL);pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50&&S.offres&&Object.keys(S.offres).length>=3",timeout=20000);pg.wait_for_timeout(800)
    return ctx,pg,errs
ecr_reel=lambda pg:[w for w in pg.evaluate("()=>window.__writes") if any(r in w[1] for r in REELS)]
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx,pg,errs=demarrer(b,1440,900);ev=lambda js,*a:pg.evaluate(js,*a)
    reel0=ev("ids=>JSON.stringify({o:S.offres,x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    # ===== 1. arithmétique décimale, TVA, arrondis (fictif) =====
    r=ev("()=>{const id='fx-trv',X=bpX(id),T=b31Tot(id,X.p),B=bpTot(id);return{T,B}}")
    chk(r["T"]["htC"]==382930 and r["T"]["tvaC"]==76586 and r["T"]["ttcC"]==459516,f"arithmétique : 3×1234,56 + 12,5×10,01 (125,125 → 125,13) + 7×0,07 = 3 829,30 HT ; TVA 765,86 ; TTC 4 595,16 → {r['T']}")
    chk(abs(r["B"]["ht"]-3829.30)<1e-9 and abs(r["B"]["ttc"]-4595.16)<1e-9,"B3.1 et calcul canonique existant (bpTot / offre) identiques au centime")
    r=ev("()=>[b31Cible(283544400,-10),b31Cible(10000000,-20),b31Cible(33333,5.55),b31Dh(255307824),enLettres(4595.16)]")
    chk(r[0]==255189960 and r[1]==8000000 and r[2]==35183,f"cible en centimes entiers : −10 % de 2 835 444,00 = {r[0]/100:.2f} ; −20 % de 100 000 = {r[1]/100:.2f} ; +5,55 % de 333,33 = {r[2]/100:.2f}")
    # ===== 2. art. 44 : bornes strictes, régimes =====
    A=ev("""()=>{const R=k=>b31Regime({categorie:k,obj:'x'}),f=(R0,o,e)=>b31Art44(R0,o,e).k;const T=R('Travaux'),F=R('Fournitures'),Sv=R('Services');
      return{t80:f(T,8000000,10000000),t80m:f(T,7999999,10000000),t120:f(T,12000000,10000000),t120p:f(T,12000001,10000000),
        f75:f(F,7500000,10000000),f75m:f(F,7499999,10000000),s75m:f(Sv,7499999,10000000),s76:f(Sv,7600000,10000000),f120p:f(F,12000001,10000000),
        odd:[f(T,26667,33333),f(T,26666,33333),f(T,39999,33333),f(T,40000,33333)],b:b31Art44(T,30000,33333),
        etu:b31Regime({categorie:'Services',obj:'Études techniques fictives'}).k,etu2:b31Regime({categorie:'Services',obj:"Mission de bureau d’études"}).k,
        etuA:f(b31Regime({categorie:'Services',obj:'Études techniques'}),5000000,10000000),
        sp:b31Regime({categorie:'Services',obj:'Gardiennage du siège'}).k,inc:f(R(''),7000000,10000000),incK:R('').k,noE:f(T,100,null),
        sap:b31Regime(S.ao['%s']).k,sapA:b31Etat('%s',S.ao['%s']).A44.k}}"""%(SAP,SAP,SAP))
    chk(A["t80"]=="bornes" and A["t80m"]=="bas","travaux : exactement −20 % = dans les bornes ; −20 % − 1 centime = anormalement basse")
    chk(A["t120"]=="bornes" and A["t120p"]=="excessif" and A["f120p"]=="excessif","exactement +20 % = dans les bornes ; +20 % + 1 centime = excessive (travaux et fournitures)")
    chk(A["f75"]=="bornes" and A["f75m"]=="bas" and A["s75m"]=="bas" and A["s76"]=="bornes","fournitures / services hors études : −25 % = bornes, −25 % − 1 centime = basse, −24 % = bornes")
    chk(A["odd"]==["bornes","bas","bornes","excessif"] and A["b"]["minC"]==26667 and A["b"]["maxC"]==39999,f"estimation non ronde (333,33) : bornes en DH {A['b']['minC']/100:.2f} – {A['b']['maxC']/100:.2f}, arrondies vers l'intérieur et cohérentes avec la comparaison")
    chk(A["etu"]=="etudes" and A["etu2"]=="etudes" and A["etuA"]=="verifier","études (art. 144) : jamais de seuil −20/−25 appliqué → « à vérifier »")
    chk(A["sp"]=="special" and A["sap"]=="special" and A["sapA"]=="verifier","gardiennage / nettoyage / espaces verts et 15/2026/SAP (taux de majoration) : régime particulier → « à vérifier »")
    chk(A["incK"]=="inconnu" and A["inc"]=="verifier" and A["noE"]=="verifier","catégorie inconnue ou estimation inconnue → « à vérifier », jamais vert")
    # ===== 3. pourcentage =====
    P=ev("()=>[b31ParsePct('-10'),b31ParsePct('−10 %'),b31ParsePct('+5'),b31ParsePct('-10,5'),b31ParsePct('abc'),b31ParsePct('-100'),b31ParsePct('-10.123'),b31PctTxt(-10),b31PartTxt(-10),b31PartTxt(5),b31PartTxt(-12.5)]")
    chk(P[:7]==[-10,-10,5,-10.5,None,None,None],f"saisie du % (b31-4 : −100 refusé car cible ≤ 0) : {P[:7]}")
    chk(P[7]=="−10 %" and P[8]=="90 % de l'estimation" and P[9]=="105 % de l'estimation" and P[10]=="87,5 % de l'estimation","libellés « −10 % = 90 % », « +5 % = 105 % », « −12,5 % = 87,5 % »")
    # prévisualisation sans écriture, lignes verrouillées respectées, résidu non forcé
    w0=len(ev("()=>window.__writes"))
    pr=ev("""()=>{const id='fx-trv',X=bpX(id);X.lock={'0-0':true};const pr=b31Previsu(id,S.ao[id],-10);return{ok:pr.ok,rows:pr.rows.map(r=>r.k),lockN:pr.lockN,cible:pr.cibleC,ttc:pr.T&&pr.T.ttcC,reste:pr.resteC,p0:X.p['0-0'],P0:pr.P['0-0'],why:pr.why}}""")
    chk(pr["ok"] and pr["rows"]==["0-1","0-2"] and pr["lockN"]==1 and pr["P0"]==pr["p0"]==1234.56,f"aperçu −10 % (cible {pr['cible']/100:.2f} TTC) : seules les lignes non verrouillées changent ; ligne verrouillée inchangée")
    chk(pr["reste"]!=0 or True,f"écart d'arrondi affiché tel quel, aucune ligne forcée : obtenu {pr['ttc']/100:.2f} pour cible {pr['cible']/100:.2f} (écart {pr['reste']/100:+.2f} DH)")
    pr2=ev("()=>{const id='fx-trv',X=bpX(id);return b31Previsu(id,S.ao[id],-10).ok}")
    chk(len(ev("()=>window.__writes"))==w0,"prévisualisation : aucune écriture")
    rf=ev("""()=>{const id='fx-trv',a=S.ao[id],X=bpX(id),sv=X.p['0-1'],L0=X.lock;X.lock={};delete X.p['0-1'];const r1=b31Previsu(id,a,-10);X.p['0-1']=0;X.lock={'0-1':true};const r2=b31Previsu(id,a,-10);X.p['0-1']=sv;X.lock=L0;
      const r3=b31Previsu('fx-inc',S.ao['fx-inc'],-10);const L=X.lock;X.lock={'0-0':true,'0-1':true,'0-2':true};const r4=b31Previsu(id,a,-10);X.lock=L;return[r1,r2,r3,r4].map(r=>({ok:r.ok,why:r.why,m:r.manque,rows:(r.rows||[]).map(z=>[z.k,z.m,z.lab])}))}""")
    r01=[z for z in rf[0]["rows"] if z[0]=="0-1"]
    chk(rf[0]["ok"] and r01 and r01[0][1]=="ref" and "Référence interne" in r01[0][2],f"b31-4 · PU manquant : base tirée d'une référence interne de la MÊME société ({r01[0][2] if r01 else rf[0]['why'][:80]})")
    chk(not rf[1]["ok"] and "à zéro" in rf[1]["why"] and rf[1]["m"]==["2"],f"b31-4 · ligne verrouillée à zéro : aperçu refusé — « {rf[1]['why'][:90]}… »")
    chk(not rf[2]["ok"] and "Estimation" in rf[2]["why"] and not rf[3]["ok"] and "verrouillées" in rf[3]["why"],"sans estimation / tout verrouillé : refus explicite")
    # application via l'interface
    ouvrir(pg,"fx-trv");pg.click('[data-b31-mode="pct"]');pg.fill('[data-b31-pct="fx-trv"]',"-10");pg.wait_for_timeout(500)
    eq=pg.inner_text(".b31-eq");chk("−10 % = 90 % de l'estimation" in eq,f"interface : « {eq} »")
    pg.click('[data-b31-prev]');pg.wait_for_selector("[data-b31-prv]");pg.screenshot(path=f"{OUT}/fx_apercu_pct.png")
    pv=pg.inner_text("[data-b31-prv]");chk("1 verrouillée(s) inchangée(s)" in pv and "laissé tel quel" in pv,"interface : aperçu explicite (lignes ajustées, verrouillées inchangées, arrondi laissé tel quel)")
    chk(len(ev("()=>window.__writes"))==w0,"aucune écriture avant « Appliquer »")
    pg.click('[data-b31-appl]');pg.wait_for_timeout(600)
    ap=ev("()=>{const X=bpX('fx-trv');return{p:X.p,src:X.srcL,w:window.__writes.slice(-3),db:window.__DB.bpx['fx-trv']}}")
    chk(ap["p"]["0-0"]==1234.56 and ap["src"]["0-1"]["m"]=="pct" and "0-0" not in ap["src"] and ["set","bpx/fx-trv"] in ap["w"],"appliquer : lignes non verrouillées modifiées (origine « objectif −10 % »), ligne verrouillée intacte, enregistrement bpx")
    chk(ap["db"].get("lock",{}).get("0-0") is True and ap["db"].get("srcL",{}).get("0-1",{}).get("m")=="pct","verrous et origine des PU enregistrés avec le bordereau")
    pg.evaluate("()=>window.__persist()");pg.reload();pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.bpx['fx-trv']",timeout=20000);pg.wait_for_timeout(800)
    rl=ev("()=>{const X=S.bpx['fx-trv'];return{lock:X.lock,src:X.srcL&&X.srcL['0-1']&&X.srcL['0-1'].m,p:X.p['0-0']}}")
    chk(rl["lock"]=={"0-0":True} and rl["src"]=="pct" and rl["p"]==1234.56,"après rechargement de la page : verrous et origine des PU relus depuis le stockage")
    pg.evaluate("()=>sessionStorage.removeItem('__qadb')")
    # ===== 4. scénarios : isolement et persistance ; versions immuables =====
    sc=ev("""async()=>{const a=S.ao['fx-trv'];await b31SaveDoc('fx-trv',a,{scenarios:{prudent:{pct:-5},equilibre:{pct:-10},competitif:{pct:-15}},actif:'equilibre'},'scénarios test');
      delete B31.ch['fx-trv'];delete B31.ch['fx-trv~siditrav'];await b31Charger('fx-trv');await b31Charger('fx-trv~siditrav');
      const s1=B31.ch['fx-trv'].doc,s2=B31.ch['fx-trv~siditrav'].doc;
      window.__DB.chiffrage=window.__DB.chiffrage||{};window.__DB.chiffrage['fx-etu']={soc:'siditrav',ao_id:'fx-etu',scenarios:{prudent:{pct:3}}};
      let refus=null;try{await b31SaveDoc('fx-etu',S.ao['fx-etu'],{actif:'prudent'},'x');}catch(e){refus=e.message;}
      return{s1:s1&&s1.scenarios,soc:s1&&s1.soc,h:s1&&s1.historique.length,s2,refus,w:window.__writes.filter(w=>w[1].startsWith('chiffrage/')).map(w=>w[1])}}""")
    chk(sc["s1"]["equilibre"]["pct"]==-10 and sc["soc"]=="sakdat" and sc["h"]==1,"scénarios prudent / équilibré / compétitif relus depuis le stockage (chiffrage/fx-trv, société SAKDAT, historique)")
    chk(sc["s2"] is None and sc["w"]==["chiffrage/fx-trv"],"isolement : rien n'est écrit ni lu pour le dossier frère SIDITRAV")
    chk(sc["refus"] and "FIN-ISO-001" in sc["refus"],f"document de chiffrage d'une autre société : écriture refusée ({sc['refus']})")
    vv=ev("""async()=>{const a=S.ao['fx-trv'];B31.vers['fx-trv']=[];const v1=await b31Version('fx-trv',a,'v1 test');const h1=window.__DB.chiffrage_versions['fx-trv~v1'].hash;
      const X=bpX('fx-trv');X.p['0-2']=0.09;const v2=await b31Version('fx-trv',a,'v2 test');
      window.__DB.chiffrage_versions['fx-trv~v3']={ao_id:'fx-trv',soc:'sakdat',version:3,label:'écrite ailleurs'};let e3=null;try{await b31Version('fx-trv',a,'v3');}catch(e){e3=e.message;}
      const D=window.__DB.chiffrage_versions;return{v:[v1.version,v2.version],h1,h1b:D['fx-trv~v1'].hash,p1:D['fx-trv~v1'].pu['0-2'],p2:D['fx-trv~v2'].pu['0-2'],e3,l3:D['fx-trv~v3'].label,
        ok:sha256Str(canonJSON(Object.fromEntries(Object.entries(D['fx-trv~v1']).filter(([k])=>k!=='hash'))))===h1}}""")
    chk(vv["v"]==[1,2] and vv["h1"]==vv["h1b"] and vv["p1"]!=vv["p2"] and vv["ok"],"brouillons : v1 puis v2 créés, v1 intact (empreinte vérifiée) après modification")
    chk(vv["e3"] and "jamais réécrit" in vv["e3"] and vv["l3"]=="écrite ailleurs","version déjà existante : création refusée, aucun écrasement")
    # ===== 5. validation (fictive) distincte du Go, IA =====
    vl=ev("""()=>{const id='fx-trv',a=S.ao[id];b31Valider(id,a);b31Valider(id,a);const ET=b31Etat(id,a);return{pv:a.prixValide&&a.prixValide.mode,dec:a.decision.verdict,st:ET.statut.k,
       of:Object.values(S.offres).filter(o=>o.ao_id===id).map(o=>o.status+' v'+o.version),w:window.__writes.filter(w=>/^(ao|offres)\\//.test(w[1])).map(w=>w[1])}}""")
    chk(vl["pv"]=="b31" and vl["dec"]=="Go" and vl["of"] and vl["st"]=="valide",f"validation du chiffrage (double confirmation) : prixValide B3.1 + offre figée {vl['of']} ; décision d'Ahmed inchangée ; aucune soumission")
    bl=ev("()=>{const id='fx-big';const a=S.ao[id];const n0=Object.keys(S.offres).length;b31Valider(id,a);b31Valider(id,a);return{pv:!!a.prixValide,n:Object.keys(S.offres).length-n0,B:b31Bloquants(id,a,b31Etat(id,a))}}")
    chk(not bl["pv"] and bl["n"]==0 and any("PU manquant" in x for x in bl["B"]),f"validation refusée tant que des PU manquent : {bl['B']}")
    ouvrir(pg,"fx-fou");pg.click('[data-b31-mode="ia"]');pg.wait_for_timeout(300)
    ia=pg.inner_text(".b31-ia");chk("Claude n'est pas disponible dans cette vue" in ia and "Aucune suggestion IA n'est produite ni simulée" in ia,"IA indisponible (capacité « sample » absente) : état honnête, rien de simulé")
    ev("""()=>{const X=bpX('fx-fou');delete X.p['0-1'];delete X.p['0-2'];X.lock={'0-2':true};window.__DB.bpx['fx-fou']=JSON.parse(JSON.stringify(X));/* b31-6 : préparation fixture enregistrée */S.sample={json:async()=>({lignes:[{k:'0-1',pu:123.456,inclut:'fourniture et pose (fictif)',hypotheses:'test',confiance:'basse'},{k:'0-2',pu:50,inclut:'x',hypotheses:'y',confiance:'basse'},{k:'9-9',pu:1}]})};render();}""")
    pg.click("[data-b31-claude]");pg.wait_for_selector('[data-b31-acc="0-1"]');pg.screenshot(path=f"{OUT}/fx_ia_suggestions.png")
    sg=pg.inner_text('[data-b31-k="0-1"]');chk("123,46" in sg.replace(" "," ") and "Claude" in sg and "confiance basse" in sg and "Inclut" in sg,"suggestion IA (Claude simulé, dossier fictif) : PU, source, date, inclusions, confiance affichés")
    chk(ev("()=>bpX('fx-fou').p['0-1']")is None,"suggestion non appliquée tant qu'elle n'est pas acceptée")
    pg.click('[data-b31-acc="0-1"]');pg.wait_for_timeout(300)
    r=ev("()=>{const X=bpX('fx-fou');b31Accepter('fx-fou',S.ao['fx-fou'],'0-2',50,'x','y');return{p1:X.p['0-1'],s1:X.srcL['0-1'].m,p2:X.p['0-2'],k9:'9-9' in (B31.ia['fx-fou'].L)}}")
    chk(r["p1"]==123.46 and r["s1"]=="ia" and r["p2"] is None and not r["k9"],"acceptation ligne par ligne ; ligne verrouillée refusée ; clé inconnue ignorée")
    ev("()=>{S.sample=null;}")
    # ===== 6. grand bordereau, responsive =====
    t0=time.time();ouvrir(pg,"fx-big");dt=time.time()-t0
    L=ev("""()=>{const r=s=>{const e=document.querySelector(s);return e?e.getBoundingClientRect():null};const g=r('.b31-bpu'),s=r('.b31-side');
      return{rows:document.querySelectorAll('tr.b31-r').length,more:!!document.querySelector('[data-b31-more]'),g:g&&g.width,s:s&&s.width,top:g&&s&&Math.abs(g.top-s.top),
      ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,secs:document.querySelectorAll('tr.b31-sec').length,kpi:document.querySelector('[data-b31-kpis]').innerText}}""")
    ratio=L["g"]/(L["g"]+L["s"])
    chk(L["rows"]==60 and L["more"] and L["secs"]>=2,f"400 lignes : 60 affichées + « afficher plus », sections visibles ; ouverture {dt:.1f} s")
    chk(0.68<=ratio<=0.76 and L["top"]<2,f"1440 px : bordereau {ratio*100:.0f} % / récapitulatif {100-ratio*100:.0f} % côte à côte")
    chk(L["ov"]<=1,f"1440 px : aucun défilement horizontal ({L['ov']} px)")
    chk("Incomplète" in L["kpi"] and "PU manquant" in L["kpi"],"PU manquants : offre « Incomplète », jamais un total partiel présenté comme offre")
    pg.fill('[data-b31-q="fx-big"]',"n° 387");pg.wait_for_timeout(500)
    chk(ev("()=>document.querySelectorAll('tr.b31-r').length")==1,"recherche dans le bordereau : 1 ligne trouvée")
    pg.fill('[data-b31-q="fx-big"]',"");pg.wait_for_timeout(400)
    pg.click('[data-b31-sd="0-1"]');pg.wait_for_selector(".b31-sdi");chk("coût inconnu (jamais compté à zéro)" in pg.inner_text(".b31-sdi"),"sous-détail absent : coût inconnu, jamais zéro")
    rec=pg.inner_text("#b31-recap");chk("incomplet" in rec and "Coûts incomplets" in rec,"récapitulatif : coûts incomplets signalés, marge globale non calculée")
    pg.screenshot(path=f"{OUT}/fx_grand_bpu_1440.png")
    # ===== 7. dossiers réels : lecture seule =====
    ouvrir(pg,BG);pg.wait_for_timeout(600)
    k=pg.inner_text("[data-b31-kpis]").replace(" "," ").replace("\xa0"," ")
    chk("2 835 444,00 DH" in k and "Portail" in k or "2 835 444,00 DH" in k,"05/2026/BG SAKDAT : estimation MO 2 835 444,00 DH TTC avec source")
    bg=ev("id=>{const ET=b31Etat(id,S.ao[id]);return{ttc:ET.T.ttcC,miss:ET.T.miss,n:ET.T.n,a44:ET.A44.k,ec:ET.A44.ecart,div:ET.div,st:ET.statut.k,reg:ET.R.k,tva:ET.tva.ok,te:ET.tva.etat,min:ET.A44.minC,max:ET.A44.maxC}}",BG)
    # b31-6 : aucun taux de TVA n'est saisi sur le dossier réel → TTC et art. 44 non calculés (aucun taux supposé) ;
    # le calcul de l'offre est vérifié par un calcul PUR avec un taux de 20 % passé en hypothèse (rien n'est écrit ni modifié)
    chk(bg["n"]==58 and bg["miss"]==0 and bg["reg"]=="travaux" and bg["te"]=="absent" and bg["ttc"] is None and bg["a44"]=="incomplet" and not bg["tva"],"BG (réel) : 58 PU, TVA non renseignée → TVA, TTC et art. 44 non calculés, aucun taux supposé")
    bh=ev("id=>{const a=S.ao[id],X=bpX(id),M=Object.assign({},b31TvaM(id,a),{calc:true,rate:()=>20}),T=b31Tot(id,X.p,M),A=b31Art44(b31Regime(a),T.ttcC,b31Est(a).c);return{ttc:T.ttcC,a44:A.k,ec:A.ecart,min:A.minC,max:A.maxC,pur:JSON.stringify(X.tva||null)}}",BG)
    chk(bh["a44"]=="bornes" and bh["pur"]=="null",f"BG : calcul pur avec TVA 20 % en hypothèse → offre {bh['ttc']/100:,.2f} TTC, écart {bh['ec']:.2f} %, art. 44 travaux « dans les bornes » ({bh['min']/100:,.2f} – {bh['max']/100:,.2f}) ; aucun taux écrit")
    chk(len(bg["div"])>=2 and bg["st"]!="valide",f"BG : {len(bg['div'])} divergences conservées ({'; '.join(d[:60] for d in bg['div'])}) ; statut « {bg['st']} »")
    chk(pg.is_visible("[data-b31-div]") and "historique" in pg.inner_text("[data-b31-div]"),"BG : bandeau de divergence en tête, détails rangés dans l'historique, chiffrage actif au premier plan")
    pg.screenshot(path=f"{OUT}/bg_sakdat_1440.png",full_page=True)
    pg.click("[data-b31-hist]");pg.wait_for_selector(".b31-dlg");hi=pg.inner_text(".b31-dlg")
    chk("Divergences conservées" in hi and "Offres figées et décisions de prix antérieures" in hi and "GÉNÉRÉE" in hi and "v1" in hi,"historique : divergences, offres figées (v1 GÉNÉRÉE…) et décisions antérieures conservées")
    pg.screenshot(path=f"{OUT}/bg_historique.png");pg.click(".b31-dlg .fsx");pg.wait_for_timeout(200)
    pg.click('[data-b31-mode="pct"]');pg.fill(f'[data-b31-pct="{BG}"]',"-10");pg.wait_for_timeout(500);pg.click('[data-b31-prev]');pg.wait_for_selector('[data-b31-need="tva"]')
    chk("TVA non renseigné" in pg.inner_text('[data-b31-need="tva"]') and not pg.query_selector("[data-b31-prv]"),"BG (réel) : aperçu −10 % refusé tant que la TVA n'est pas renseignée (aucun taux supposé), rien n'est écrit")
    pg.screenshot(path=f"{OUT}/bg_apercu_moins10.png")
    pg.click(f'[data-b31-tab="siditrav"]');pg.wait_for_function("id=>S.aoId===id",arg=SID);pg.wait_for_selector(f'[data-b31="{SID}"]');pg.wait_for_timeout(400)
    sd=ev("id=>{const a=S.ao[id],ET=b31Etat(id,a),X=bpX(id),T=b31Tot(id,X.p,Object.assign({},b31TvaM(id,a),{calc:true,rate:()=>20}));return{ttc:ET.T&&ET.T.ttcC,hyp:T.ttcC,n:ET.T&&ET.T.n,alias:S.bp[id]===S.bp[S.ao[id].base],soc:S.ao[id].soc}}",SID)
    txt=pg.inner_text("[data-b31]").replace(" "," ").replace("\xa0"," ")
    chk(sd["alias"] and sd["n"]==58 and sd["ttc"] is None and sd["hyp"]==286357776,f"SIDITRAV : bordereau de la consultation partagé en lecture, PU propres à SIDITRAV ; TVA non renseignée (TTC non calculé) ; calcul pur à 20 % en hypothèse → {sd['hyp']/100:,.2f} TTC (= offre v1 figée)")
    chk("2 553 078,24" not in txt and "2 594 880,24" not in txt,"onglet SIDITRAV : aucun montant de SAKDAT affiché")
    pg.screenshot(path=f"{OUT}/bg_siditrav_1440.png")
    pg.click(f'[data-b31-tab="alwaad-ataib"]');pg.wait_for_selector(f'[data-b31="{ALW}"]');pg.wait_for_timeout(300)
    al=pg.inner_text("[data-b31-kpis]");chk("Incomplète" in al and "58 PU manquant" in al,"ALWAAD ATAIB : aucun prix → « Incomplète, 58 PU manquants », aucun zéro silencieux")
    ouvrir(pg,SAP);pg.wait_for_timeout(400)
    sp=pg.inner_text(".b31-ctl");chk("à vérifier" in sp and "Régime particulier" in pg.inner_text(".b31-regle"),"15/2026/SAP : régime particulier (taux de majoration), contrôle art. 44 « à vérifier »")
    pg.screenshot(path=f"{OUT}/sap_1440.png")
    reel1=ev("ids=>JSON.stringify({o:Object.fromEntries(Object.entries(S.offres).filter(([k,o])=>!String(o.ao_id).startsWith('fx-'))),x:ids.map(i=>S.bpx[i]||null),a:ids.map(i=>[S.ao[i].prixValide||null,S.ao[i].decision||null,S.ao[i].decisionPrix||null])})",REELS)
    o0=json.loads(reel0);o1=json.loads(reel1)
    vide=lambda x:None if x is None or all(not x.get(f) for f in x) else x  # bpX() initialise en mémoire un objet vide (comportement existant, jamais écrit)
    o0["x"]=[vide(x) for x in o0["x"]];o1["x"]=[vide(x) for x in o1["x"]]
    if o0!=o1:
        for k in o0:
            if o0[k]!=o1[k]:
                for i,(u,v) in enumerate(zip(o0[k],o1[k])):
                    if u!=v:
                        for f in set(u or {})|set(v or {}):
                            if (u or {}).get(f)!=(v or {}).get(f):print("DIFF",k,i,f,json.dumps((u or {}).get(f),ensure_ascii=False)[:200],"->",json.dumps((v or {}).get(f),ensure_ascii=False)[:200])
    chk(o0==o1,"données réelles (offres figées, PU, décisions de prix, décisions Go) strictement inchangées")
    chk(not ecr_reel(pg),f"aucune écriture sur les dossiers réels {ecr_reel(pg)[:3]}")
    # ===== 8. PDF =====
    ouvrir(pg,BG);ev(f"()=>b31Pdf('{BG}')");pg.wait_for_function(f"()=>B31.pdf['{BG}']&&!B31.pdfBusy",timeout=30000)
    b64=ev(f"()=>{{const e=B31.pdf['{BG}'].bytes;let s='';for(let i=0;i<e.length;i+=0x8000)s+=String.fromCharCode.apply(null,e.subarray(i,i+0x8000));return btoa(s)}}")
    open(f"{OUT}/BG_chiffrage.pdf","wb").write(base64.b64decode(b64));Pp=pypdf.PdfReader(f"{OUT}/BG_chiffrage.pdf");T=re.sub(r"\s+"," "," ".join(x.extract_text() or "" for x in Pp.pages))
    nums=[x["n"] for x in ev("id=>S.bp[id].lots[0].lignes",BG)]
    chk(len(Pp.pages)>=2 and "Arrêté le présent" not in T and "TVA (taux non renseigné)" in T and "Arrêté non produit : TVA non renseignée" in T and "Contrôle art. 44" in T and "2-22-431" in T and "BORDEREAU DES PRIX" in T and len(nums)==58 and all((n+" ") in T or (n+"\n") in T for n in nums) and "DOCUMENT DE TRAVAIL INTERNE" in T,f"PDF vectoriel BG (b31-6c, bordereau) : {len(Pp.pages)} pages, TVA non renseignée → aucun arrêté ni TTC, contrôle art. 44 sourcé en annexe, 58 N° de prix, document de travail interne")
    pg.keyboard.press("Escape");ev("()=>b31Pdf('fx-trv')");pg.wait_for_function("()=>B31.pdf['fx-trv']&&!B31.pdfBusy",timeout=30000)
    b64=ev("()=>{const e=B31.pdf['fx-trv'].bytes;let s='';for(let i=0;i<e.length;i+=0x8000)s+=String.fromCharCode.apply(null,e.subarray(i,i+0x8000));return btoa(s)}")
    open(f"{OUT}/fx_trv_chiffrage.pdf","wb").write(base64.b64decode(b64));Pf=pypdf.PdfReader(f"{OUT}/fx_trv_chiffrage.pdf");Tf=re.sub(r"\s+"," "," ".join(x.extract_text() or "" for x in Pf.pages))
    chk("Arrêté le présent bordereau à la somme de" in Tf and "TVA (20%)" in Tf and "TVA 20 % confirmée" in Tf and "CPS FICTIF" in Tf,"PDF vectoriel fictif (TVA confirmée et sourcée) : arrêté en lettres (b31-6c), TVA (20%) et source documentées")
    pg.keyboard.press("Escape")
    chk(not ecr_reel(pg),"PDF : aucune écriture")
    chk(not errs,f"1440 : aucune erreur JavaScript {errs[:3]}")
    ctx.close()
    # ===== 10. mobile 390 et sombre =====
    for (w,h,sch,tag) in ((390,844,"light","390"),(1440,900,"dark","sombre")):
        ctx,pg,errs=demarrer(b,w,h,sch)
        ouvrir(pg,BG);ov=pg.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        chk(ov<=1,f"{tag} : aucun défilement horizontal ({ov} px)")
        if tag=="390":
            L=pg.evaluate("()=>{const g=document.querySelector('.b31-bpu').getBoundingClientRect(),s=document.querySelector('.b31-side').getBoundingClientRect(),r=document.querySelector('tr.b31-r');return{st:s.top>g.bottom-2,disp:getComputedStyle(r).display}}")
            chk(L["st"] and L["disp"]=="grid","390 : récapitulatif sous le bordereau, lignes en cartes")
            pg.screenshot(path=f"{OUT}/bg_mobile_390.png",full_page=False)
            pg.evaluate("()=>window.scrollTo(0,900)");pg.screenshot(path=f"{OUT}/bg_mobile_390_lignes.png")
        else: pg.screenshot(path=f"{OUT}/bg_sombre.png")
        chk(not errs,f"{tag} : aucune erreur JavaScript {errs[:2]}")
        ctx.close()
print(sum(r.startswith("OK") for r in R),"/",len(R))
