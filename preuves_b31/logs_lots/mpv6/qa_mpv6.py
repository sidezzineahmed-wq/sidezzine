"""Recette mpv-6 · « Mes consultations suivies » et « DCE à récupérer » (suivi au niveau du groupe). Base SIMULÉE locale :
copie des 118 dossiers réels lus (lecture seule, aucune écriture vérifiée) + dossiers fictifs fx-* pour les écritures.
Aucun accès à EAIOS, aucun téléchargement, aucun formulaire PMMP."""
import os,json,glob,re,threading,http.server,functools,datetime
from playwright.sync_api import sync_playwright
ICI=os.path.dirname(os.path.abspath(__file__));SRV=os.path.join(ICI,"srv6");OUT=os.path.join(ICI,"qa_mpv6");os.makedirs(OUT,exist_ok=True)
DBR=os.path.join(ICI,"..","audit_suivi_db","ao")
M=json.load(open(os.path.join(ICI,"srv","mockdb_b31.json"),encoding="utf-8"))
REEL={}
for p in glob.glob(os.path.join(DBR,"*.json")):
    d=json.load(open(p,encoding="utf-8"));REEL[os.path.basename(p)[:-5].replace("@","~")]=d.get("data",d)
M["ao"]=json.loads(json.dumps(REEL))
J=lambda n:(datetime.date.today()+datetime.timedelta(days=n)).isoformat()
def fx(ref,org,lim,**k):
    a={"ref":"FX/"+ref,"obj":"Consultation fictive "+ref+" (recette mpv-6)","mo":"ACHETEUR FICTIF "+org.upper(),"lim":lim,"heure":"10H","est":0,"statut":"À examiner","checks":{},"fichiers":{},
       "cree":J(-3),"portail":{"org":org,"ref":ref,"url":""},"veille":{"source":"PMMP","detecte_le":J(-3)+"T08:00:00Z"}}
    a.update(k);return a
M["ao"]["fx-g1"]=fx("990001","fxa",J(5),suivi={"niveau":"groupe","le":J(-1)+"T09:00:00Z"},note="Suivie au niveau du groupe")                 # groupe, sans société, DCE à récupérer
M["ao"]["fx-g2"]=fx("990002","fxa",J(12),soc="alwaad-ataib",mode="seule",mem=[],dceDemandeLe=J(-1)+"T10:00:00Z",dceDemande=J(-1),
    note="Suivie depuis la veille nationale. Société proposée par défaut : ALWAAD ATAIB, à confirmer à la décision.")                              # ancien suivi ALWAAD d'office + demande
M["ao"]["fx-g3"]=fx("990003","fxa",J(20),suivi={"niveau":"groupe","le":J(-2)+"T09:00:00Z"})
M["ao"]["fx-g3~sakdat"]=fx("990003","fxa",J(20),soc="sakdat",base="fx-g3",statut="En préparation",decision={"verdict":"Go","le":J(-1),"qui":"autre"},
    fichiers={"dce":{"id":"blobfx3","nom":"DCE_990003.zip"}})                                                                                        # DCE réellement joint
M["ao"]["fx-g4"]=fx("990004","fxa",J(-4),suivi={"niveau":"groupe"})                                                                              # échue, DCE non reçu
M["ao"]["fx-g5"]=fx("990005","fxa",J(9),suivi={"niveau":"groupe"})
M["ao"]["fx-g5b"]=fx("990005","fxb",J(9),suivi={"niveau":"groupe"},mo="AUTRE ACHETEUR FXB")                                                    # même numéro, autre organisme
M["ao"]["fx-g6"]=fx("990006","fxa",J(15),suivi={"niveau":"groupe"},dceDemandeLe=J(-1)+"T11:00:00Z",dceDemande=J(-1),
    fichiers={"caution":{"id":"blobc","nom":"caution.pdf"}})                                                                                       # demande + pièce non-DCE : PAS reçu
json.dump(M,open(os.path.join(SRV,"mockdb_mpv6.json"),"w",encoding="utf-8"),ensure_ascii=False)
REELS=set(REEL)
class Hq(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Hq,directory=SRV));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f"http://127.0.0.1:{srv.server_address[1]}/index.html"
src=open(os.path.join(ICI,"qa_b31.py"),encoding="utf-8").read();INITSRC=src[src.index('INIT="""'):src.index('R=[];chk=')]
MOCK=open(os.path.join(SRV,"mockdb_mpv6.json"),encoding="utf-8").read();INITSRC=INITSRC.replace('window.claude={use:async n=>n==="db"?db:n==="user"?user:n==="downloads"?downloads:null};','let _na=0;const assets={upload:async b=>({id:"qa"+(++_na),url:"/_blob/qa"+_na,sizeBytes:b.size,contentType:b.type}),list:async()=>({assets:[],usage:{}}),delete:async()=>{}};window.claude={use:async n=>n==="db"?db:n==="user"?user:n==="downloads"?downloads:n==="assets"?assets:null};');assert 'assets' in INITSRC;exec(INITSRC)
import zipfile,io
ZIPF=os.path.join(OUT,'DCE_990001_fictif.zip')
with zipfile.ZipFile(ZIPF,'w') as z:
    z.writestr('RC_fictif.pdf',b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF')
    z.writestr('CPS_fictif.docx',b'PK fictif')
R=[];chk=lambda c,t:(R.append(("OK " if c else "ECHEC ")+t),print(R[-1]))
CAT=json.load(open(os.path.join(SRV,"catalogue.json"),encoding="utf-8"));CK={f"{x['o']}:{x['r']}":x for x in CAT["items"]}
CF=json.load(open(os.path.join(SRV,"catalogue_details.json"),encoding="utf-8"))["pmmp_enrichi"]["complements_fiche"]["par_id"]
def demarrer(b,w,h,scheme="light"):
    ctx=b.new_context(viewport={"width":w,"height":h},color_scheme=scheme);ctx.add_init_script(INIT);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL);pg.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>100",timeout=40000);pg.wait_for_timeout(800);return ctx,pg,errs
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
# ----- attendus calculés sur les données (aucun chiffre fixe) -----
grp={}
for i,a in M["ao"].items():
    if not (a.get("portail") or a.get("veille")):continue
    p=a.get("portail") or {};k=f"p:{p.get('org','')}:{p['ref']}" if p.get("ref") else "b:"+(a.get("base") or i);grp.setdefault(k,[]).append(i)
NG=len(grp)
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()")
    ev(B11);pg.wait_for_timeout(500)
    tabs=ev("()=>[...document.querySelectorAll('[data-mpv-tab]')].map(b=>[b.dataset.mpvTab,b.innerText])")
    chk([t[0] for t in tabs]==["cons","suiv","dce"] and tabs[1][1].startswith("Mes consultations suivies") and tabs[2][1].startswith("DCE à récupérer"),f"ordre des onglets {tabs}")
    n_suiv=int(re.search(r"\((\d+)\)",tabs[1][1]).group(1));chk(n_suiv==NG,f"compteur « Mes consultations suivies » = groupes par ID officiel calculés ({n_suiv} = {NG}, {len(M['ao'])} dossiers)")
    chk(ev("()=>!!document.querySelector('.mpv-kpis')"),"onglet Consultations : indicateurs globaux affichés")
    # ===== Suivies =====
    pg.click('[data-mpv-tab="suiv"]');pg.wait_for_timeout(300)
    chk(not ev("()=>!!document.querySelector('.mpv-kpis')"),"onglet Suivies : pas de bloc d'indicateurs globaux répété")
    s=ev("()=>document.querySelector('[data-mpv6-sum]').dataset.mpv6Sum");chk(s.split("|")[0]==str(NG),f"résumé suivies {s}")
    txt=ev("()=>document.querySelector('.mpv6').innerText")
    soc=[n for n in ["ALWAAD","SAKDAT","SIDITRAV","BUILD","STRUCTURE","Société suivie","Société non indiquée"] if n.lower() in txt.lower()]
    chk(not soc,f"aucun nom/champ de société dans la vue Suivies (trouvés : {soc})")
    chk(ev("()=>document.querySelectorAll('[data-mpv6-row]').length")<=10 and ev("()=>!!document.querySelector('[data-mpv6=suiv] .mpv-pg')")==(NG>10),"pagination par 10")
    # recherche par référence
    pg.fill('[data-mpv6-q="ss"]',"FX/990005");pg.wait_for_timeout(700)
    rows=ev("()=>[...document.querySelectorAll('[data-mpv6-row]')].map(r=>r.dataset.mpv6Row)");chk(sorted(rows)==["p:fxa:990005","p:fxb:990005"],f"même numéro, deux organismes = deux consultations distinctes {rows}")
    pg.fill('[data-mpv6-q="ss"]',"");pg.wait_for_timeout(700)
    pg.select_option('[data-mpv6-f="ss.etat"]',"clos");pg.wait_for_timeout(300)
    et=ev("()=>[...document.querySelectorAll('[data-mpv6-row] [data-mpv6-etat]')].map(x=>x.dataset.mpv6Etat)");chk(et and set(et)=={"clos"},f"filtre État = Clôturées ({len(et)} lignes affichées)")
    pg.select_option('[data-mpv6-f="ss.etat"]',"tout");pg.select_option('[data-mpv6-f="ss.dce"]',"recu");pg.wait_for_timeout(300)
    rec=ev("()=>[...document.querySelectorAll('[data-mpv6-row]')].map(r=>r.dataset.mpv6Row)");chk("p:fxa:990003" in rec and "p:fxa:990006" not in rec,"statut DCE « Reçu » : fichiers DCE joints (fx 990003) ; une demande + caution (990006) n'est pas reçu")
    pg.select_option('[data-mpv6-f="ss.dce"]',"");pg.wait_for_timeout(200)
    # panneau fx-g2 (ancien ALWAAD d'office)
    ev("()=>{MPV6.ss.q='FX/990002';render();}");pg.wait_for_timeout(200);pg.click('[data-mpv6-sel="ss:p:fxa:990002"]');pg.wait_for_timeout(300)
    P=ev("()=>{const p=document.querySelector('[data-mpv6-panel]');return{t:p.innerText,dce:p.querySelector('[data-mpv6-pdce]').dataset.mpv6Pdce,et:p.querySelector('[data-mpv6-petat]').dataset.mpv6Petat,socn:!!p.querySelector('[data-mpv6-socnote]'),dos:(p.querySelector('[data-mpv6-dossier]')||{dataset:{}}).dataset.mpv6Dossier,godce:!!p.querySelector('[data-mpv6-godce]'),pmmp:!!p.querySelector('[data-mpv6-pmmp]')}}")
    chk(P["et"]=="ouv" and "Remise des plis" in P["t"] and P["dce"]=="encours" and P["socn"] and "Choix des sociétés : à l'étape Décision" in P["t"],f"panneau : Consultation ouverte, Remise des plis, DCE « {P['dce']} », note Choix des sociétés")
    chk("ALWAAD" not in P["t"].upper() and P["dos"]=="fx-g2" and P["godce"] and P["pmmp"],"panneau sans société (ancien ALWAAD d'office masqué) ; Ouvrir le dossier, Accéder à la récupération du DCE, lien PMMP")
    pg.click('[data-mpv6-godce]');pg.wait_for_timeout(400)
    D=ev("()=>({tab:MPV.tab,sel:(document.querySelector('[data-mpv6-dpanel]')||{dataset:{}}).dataset.mpv6Dpanel,foc:document.activeElement&&document.activeElement.id})")
    chk(D["tab"]=="dce" and D["sel"]=="p:fxa:990002",f"« Accéder à la récupération du DCE » → onglet DCE, même consultation sélectionnée {D}")
    # ===== DCE =====
    chk(not ev("()=>!!document.querySelector('.mpv-kpis')"),"onglet DCE : pas de bloc d'indicateurs globaux répété")
    G=ev("()=>{const G=mpvDceGroupes(Date.now());return{O:G.O.map(g=>g.k),E:G.E.map(g=>g.k)}}")
    dn=ev("()=>+document.querySelector('[data-mpv6-dn]').dataset.mpv6Dn");tn=int(re.search(r"\((\d+)\)",ev("()=>document.querySelector('[data-mpv-tab=dce]').innerText")).group(1))
    chk(dn==len(G["O"])==tn,f"compteur DCE dérivé : en-tête {dn} = onglet {tn} = file {len(G['O'])}")
    chk("p:fxa:990001" in G["O"] and "p:fxa:990006" in G["O"] and "p:fxa:990003" not in G["O"] and "p:fxa:990004" in G["E"] and "p:fxa:990004" not in G["O"],"file : ouvertes non reçues ; reçue exclue ; échue dans l'accordéon hors compteur")
    cn=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-mpv6-cf]')].map(b=>[b.dataset.mpv6Cf,+b.dataset.mpv6Cn]))")
    chk(cn["tout"]==dn and cn["sans"]+cn["dem"]+cn.get("partiel",0)==dn,f"compteurs réels de la file {cn}")
    ech=ev("()=>+document.querySelector('[data-mpv6-ech]').dataset.mpv6Ech");chk(ech==len(G["E"]),f"accordéon échues : {ech} (hors compteur)")
    txt=ev("()=>document.querySelector('.mpv6').innerText")
    soc=[n for n in ["ALWAAD","SAKDAT","SIDITRAV","BUILD CHANTIER","STRUCTURE CHANTIER","Société suivie","Société non indiquée"] if n.lower() in txt.lower()]
    chk(not soc,f"aucun nom/champ de société dans la vue DCE (trouvés : {soc})")
    # panneau DCE fx-g1 : inventaire inconnu, actions
    ev("()=>{MPV6.ds.q='';MPV6.ds.sel='p:fxa:990001';render();}");pg.wait_for_timeout(250)
    Q=ev("()=>{const p=document.querySelector('[data-mpv6-dpanel]');return{t:p.innerText,inv:p.querySelector('[data-mpv6-inv]').dataset.mpv6Inv,st:p.querySelector('[data-mpv6-dst]').dataset.mpv6Dst,j:p.querySelector('[data-mpv6-joints]').dataset.mpv6Joints,joindre:(p.querySelector('[data-mpv6-joindre]')||{innerText:''}).innerText,dem:!!p.querySelector('[data-mpv6-demande]'),docs:[...p.querySelectorAll('[data-mpv6-docs]')].map(a=>[a.href,a.target]),forms:p.querySelectorAll('form').length}}")
    chk(Q["inv"]=="inconnu" and "inconnu" in Q["t"] and Q["st"]=="afaire" and Q["j"]=="0",f"panneau DCE : inventaire inconnu explicite, statut À récupérer, aucun fichier joint {Q['inv']}/{Q['st']}")
    chk("Joindre le DCE au dossier" in Q["joindre"] and Q["dem"] and Q["forms"]==0 and Q["docs"] and Q["docs"][0][1]=="_blank" and "refConsultation=990001" in Q["docs"][0][0] and "orgAcronyme=fxa" in Q["docs"][0][0],
        f"actions : Ouvrir les documents sur PMMP (même ID/org, nouvel onglet), Joindre le DCE, demande interne distincte ; aucun formulaire {Q['docs']}")
    # demande interne (dossier fictif) : confirmation, écriture sur fx-g1 seulement, statut ≠ reçu
    w0=len(W());pg.click('[data-mpv6-demande]');pg.wait_for_timeout(200);chk(ev("()=>!!document.querySelector('[data-mpv-confok]')") and "n'est pas un DCE reçu" in ev("()=>document.querySelector('.mpv-conf').innerText"),"demande interne : confirmation explicite « n'est pas un DCE reçu »")
    pg.click('[data-mpv-confok]');pg.wait_for_timeout(900);w=W()[w0:]
    st=ev("()=>mpvDce(['fx-g1']).k");chk(any("ao/fx-g1"==x[1] for x in w) and st=="encours" and all("fx-g1" in x[1] or x[1].startswith("journal") for x in w),f"demande enregistrée sur fx-g1 seulement ({w}) ; statut « {st} », pas reçu")
    # inventaire lu sur une consultation réelle suivie (lecture seule)
    reel_lu=None
    for k,ids in grp.items():
        if not k.startswith("p:") or k[2:] not in CK: continue
        o,r=k[2:].split(":");c=CF.get(f"pmmp:{o}:{r}")
        if c and (c.get("statuts") or {}).get("docs")=="lu" and c.get("docs"): reel_lu=k;break
    if reel_lu:
        ev("k=>{MPV6.ds.sel=k;render();}",reel_lu);pg.wait_for_timeout(250)
        I=ev("()=>{const p=document.querySelector('[data-mpv6-dpanel]');return{inv:p.querySelector('[data-mpv6-inv]').dataset.mpv6Inv,docs:[...p.querySelectorAll('[data-mpv6-doc] a')].map(a=>[a.href,a.target])}}")
        o,r=reel_lu[2:].split(":")
        chk(I["inv"]=="lu" and I["docs"] and all(("refConsultation="+r) in h and ("orgAcronyme="+o) in h and t=="_blank" for h,t in I["docs"]),f"inventaire PMMP réellement lu ({reel_lu}) : liens officiels même ID/org {len(I['docs'])}")
    else: chk(True,"aucune consultation suivie réelle avec inventaire lu dans cette base (cas non applicable)")
    # Joindre le DCE au dossier : dépôt du ZIP existant (dceIngerer) sur le dossier fictif fx-g1 ; « reçu » seulement après fichiers joints
    ev("()=>{MPV.tab='dce';MPN.outil='f:dce';MPV6.ds.sel='p:fxa:990001';render();}");pg.wait_for_timeout(300)
    jz=ev("()=>{const z=document.querySelector('[data-mpv6-joindre]');return z?{id:z.dataset.mpv6Joindre,t:z.innerText,inp:!!z.querySelector('input[type=file][accept*=zip]')}:null}")
    chk(jz and jz["id"]=="fx-g1" and "Joindre le DCE au dossier" in jz["t"] and jz["inp"],f"« Joindre le DCE au dossier » : dépôt du ZIP existant sur le dossier de la consultation {jz}")
    w0=len(W());pg.set_input_files('[data-mpv6-joindre] input[type=file]',ZIPF);pg.wait_for_function("()=>!(S.dceIng||{})['fx-g1']",timeout=30000);pg.wait_for_timeout(1500)
    w=W()[w0:];st=ev("()=>mpvDce(['fx-g1']).k");pp=ev("()=>{const p=document.querySelector('[data-mpv6-dpanel]');return p?{st:p.querySelector('[data-mpv6-dst]').dataset.mpv6Dst,j:p.querySelector('[data-mpv6-joints]').dataset.mpv6Joints}:null}")
    chk(st=="pret" and w and all(x[1] in ("ao/fx-g1","dcef/fx-g1") or x[1].startswith("journal") for x in w) and (pp is None or pp["st"]=="pret"),f"ZIP joint : statut « reçu » (fichiers réellement joints), écritures sur fx-g1 seulement {w} {pp}")
    G2=ev("()=>mpvDceGroupes(Date.now()).O.map(g=>g.k)");chk("p:fxa:990001" not in G2,"après dépôt : la consultation sort de la file DCE à récupérer")
    # Ouvrir le dossier → dossier existant ; étape Décision sans société présélectionnée
    ev(B11);pg.wait_for_timeout(300);ev("()=>{MPV.tab='suiv';MPN.outil='veille';MPV.outil='veille';MPV6.ss.q='FX/990001';MPV6.ss.sel='p:fxa:990001';render();}");pg.wait_for_timeout(300)
    w0=len(W());pg.click('[data-mpv6-panel] [data-mpv6-dossier]');pg.wait_for_timeout(700)
    ov=ev("()=>({id:S.aoId,vue:MPN.vue,err:0})");chk(ov["id"]=="fx-g1" and len(W())==w0,f"« Ouvrir le dossier » ouvre le dossier existant de la consultation ({ov}), rien d'écrit")
    for did,lab in (("fx-g1","suivi groupe"),("fx-g2","ancien ALWAAD d'office")):
        ev("id=>{MPN.dos=null;mpvOuvrir(id,'dec');}",did);pg.wait_for_timeout(900)
        d=ev("()=>({ns:!!document.querySelector('[data-b21d-nosel]'),sel:(document.querySelector('.b21d-it[aria-current=true]')||{dataset:{}}).dataset.b21dItem||null,n:document.querySelectorAll('[data-b21d-item]').length,panel:!!document.querySelector('[data-b21d-panel]')})")
        chk(d["ns"] and d["sel"] is None and d["n"]>=1 and not d["panel"],f"Décision ({lab}) : {d['n']} sociétés listées, aucune présélectionnée, « Choisissez une société » {d}")
    # le dossier séparé d'une société garde sa société
    ev("()=>{MPN.dos=null;mpvOuvrir('fx-g3~sakdat','dec');}");pg.wait_for_timeout(900)
    chk(ev("()=>(document.querySelector('.b21d-it[aria-current=true]')||{dataset:{}}).dataset.b21dItem")=="sakdat","dossier séparé SAKDAT (décision existante) : société conservée")
    # Suivre (consultation réelle du catalogue, non suivie) : dossier groupe, aucune société, aucune réécriture
    ev(B11);pg.wait_for_timeout(300)
    x=ev("()=>{const dm=mpvDosMap();const e=mpvBase().R.find(e=>!e.x._ferme&&!dm[e.x.r+'/'+e.x.o]&&!S.ao['pmmp-'+e.x.r]);return e?{k:e.k,r:e.x.r,o:e.x.o}:null}")
    ev("k=>{MPV.tab='cons';MPV.sel=k;MPV.conf={t:'suivre',k};render();}",x["k"]);pg.wait_for_timeout(300)
    ct=ev("()=>document.querySelector('.mpv-conf').innerText");chk("ALWAAD" not in ct.upper() and "Aucune société n'est choisie" in ct and "étape Décision" in ct,f"confirmation Suivre sans société : « {ct[:120]}… »")
    w0=len(W());pg.click('[data-mpv-confok]');pg.wait_for_timeout(1200);w=W()[w0:]
    nid="pmmp-"+x["r"];d=ev("id=>window.__DB.ao[id]||null",nid)
    chk([y for y in w if y[1].startswith("ao/")]==[["set","ao/"+nid]] and d and "soc" not in d and (d.get("suivi") or {}).get("niveau")=="groupe" and d["portail"]["org"]==x["o"] and "ALWAAD" not in d.get("note","").upper(),
        f"Suivre : un seul dossier créé {nid}, sans société, suivi.niveau=groupe, ID officiel {x['o']}:{x['r']}")
    ev("()=>{MPV.tab='suiv';MPN.outil='veille';render();}");pg.wait_for_timeout(300)
    n2=int(re.search(r"\((\d+)\)",ev("()=>document.querySelector('[data-mpv-tab=suiv]').innerText")).group(1));chk(n2==NG+1,f"compteur suivies +1 après Suivre ({n2})")
    # second Suivre de la même consultation : rien n'est créé
    w0=len(W());ev("k=>{const e=mpvBase().by.get(k);suivre(e.x);}",x["k"]);pg.wait_for_timeout(800);chk(not [y for y in W()[w0:] if y[1].startswith("ao/")],"Suivre une consultation déjà suivie : aucune écriture")
    reel_w=[y for y in W() if y[1].startswith("ao/") and y[1][3:] in REELS];chk(not reel_w,f"aucune écriture sur les dossiers réels copiés ({reel_w})")
    chk(not errs,f"aucune erreur JavaScript {errs[:3]}")
    pg.screenshot(path=os.path.join(OUT,"suivies_1440.png"),full_page=False)
    ev("()=>{MPV.tab='dce';MPN.outil='f:dce';MPV6.ds.sel=null;render();}");pg.wait_for_timeout(300);pg.screenshot(path=os.path.join(OUT,"dce_1440.png"),full_page=False)
    ctx.close()
    # ===== mobile 390 px =====
    for sch in ("light","dark"):
        ctx,pg,errs=demarrer(b,390,844,sch);ev=lambda js,*a:pg.evaluate(js,*a);ev(B11);pg.wait_for_timeout(300)
        for tab in ("suiv","dce"):
            pg.click(f'[data-mpv-tab="{tab}"]');pg.wait_for_timeout(400)
            ov=ev("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
            lst=ev("()=>getComputedStyle(document.querySelector('.mpv-lst')).display");pan=ev("()=>getComputedStyle(document.querySelector('.mpv-pan')).display")
            pg.screenshot(path=os.path.join(OUT,f"{tab}_390_{sch}_liste.png"))
            pg.click('[data-mpv6-row] button');pg.wait_for_timeout(400)
            lst2=ev("()=>getComputedStyle(document.querySelector('.mpv-lst')).display");foc=ev("()=>document.activeElement&&document.activeElement.id")
            pg.screenshot(path=os.path.join(OUT,f"{tab}_390_{sch}_panneau.png"))
            pg.click('[data-mpv-back]');pg.wait_for_timeout(300);back=ev("()=>getComputedStyle(document.querySelector('.mpv-lst')).display")
            chk(ov<=0 and lst!="none" and pan=="none" and lst2=="none" and foc in ("mpv6-ph","mpv6-dph") and back!="none",f"mobile {sch} {tab} : empilé liste → panneau (focus {foc}) → retour, sans débordement ({ov}px)")
        chk(not errs,f"mobile {sch} : aucune erreur JavaScript {errs[:2]}");ctx.close()
    b.close()
open(os.path.join(OUT,"resultat.txt"),"w",encoding="utf-8").write("\n".join(R))
print(sum(r.startswith("OK") for r in R),"/",len(R))
