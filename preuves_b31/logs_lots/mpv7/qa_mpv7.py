"""Recette ISOLÉE mpv-7 : « DCE à récupérer » branché sur la file DCE (dce_demande) et la tâche DCE (fire_trigger).
Base simulée (fusion récursive des update comme ArtifactData), connecteur MCP simulé (appels enregistrés), dossiers fictifs fx-q*.
Aucun accès à EAIOS, à PMMP ni à la tâche réelle. Usage : python3 qa_mpv7.py <eaios.js>"""
import os,sys,json,re,shutil,datetime
ICI0=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(ICI0,"qa_mpv6.py"),encoding="utf-8").read()
exec(src.split("\nwith sync_playwright() as p:")[0].replace('OUT=os.path.join(ICI,"qa_mpv6")','OUT=os.path.join(ICI,"qa_mpv7")'))
JS=sys.argv[1];shutil.copy(JS,os.path.join(SRV,"app","eaios.js"))
N=lambda m=0:(datetime.datetime.utcnow()+datetime.timedelta(minutes=m)).strftime("%Y-%m-%dT%H:%M:%SZ")
for i,r in enumerate(range(990201,990210)):
    M["ao"][f"fx-q{i+1}"]=fx(str(r),"fxq",J(8+i),suivi={"niveau":"groupe"})
M["ao"]["fx-q9~sakdat"]=fx("990209","fxq",J(16),soc="sakdat",base="fx-q9",statut="En préparation",decision={"verdict":"Go","le":J(-1),"qui":"autre"})
CG={"texte":"Conditions <script>window.__xss=1</script> d'utilisation","lien":"https://www.marchespublics.gov.ma/cg.pdf","empreinte":"ab"*32,"portee":"section","algo":"cg-v3","canonique":"> CG\nligne","lue_le":N(-5)}
LAY="""()=>{const pan=document.querySelector('[data-mpv6-dpanel]'),sec=pan&&pan.querySelector('[data-mpv7-dem]');if(!sec)return null;const C=[...sec.querySelectorAll('[data-mpv7-card]')],r=e=>e.getBoundingClientRect();
 const ps=getComputedStyle(pan),pw=r(pan).width-parseFloat(ps.paddingLeft)-parseFloat(ps.paddingRight)-parseFloat(ps.borderLeftWidth)-parseFloat(ps.borderRightWidth);
 return {h:(sec.querySelector('h3')||{}).innerText,n:C.length,k:C.map(c=>c.dataset.mpv7Card),t:C.map(c=>c.querySelector('.mpv7-ct').innerText),d:C.map(c=>c.querySelector('.mpv-mut').innerText),
  b:C.map(c=>[c.querySelector('button').innerText.trim(),c.querySelector('button').className]),stack:C.length==2&&r(C[1]).top>=r(C[0]).bottom-0.5&&Math.abs(r(C[0]).left-r(C[1]).left)<1,
  full:C.every(c=>Math.abs(r(c).width-r(sec).width)<1)&&Math.abs(r(sec).width-pw)<2,bfull:C.every(c=>{const b=c.querySelector('button'),cs=getComputedStyle(c);return Math.abs(r(b).width-(r(c).width-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight)-parseFloat(cs.borderLeftWidth)-parseFloat(cs.borderRightWidth)))<1.5}),
  bg:getComputedStyle(C[1].querySelector('button')).backgroundColor,bg1:getComputedStyle(C[0].querySelector('button')).backgroundColor,
  helper:(pan.querySelector('[data-mpv7-helper]')||{innerText:''}).innerText.trim(),sw:Math.round(r(sec).width),cw:C.map(c=>Math.round(r(c).width)),tech:/exploitant|nom, prénom|e-mail/i.test(pan.innerText),pw:Math.round(pw)}}"""
def laychk(L,lbl):
    chk(L and L["h"]=="Demander le DCE" and L["n"]==2 and L["k"]==["file","now"] and L["t"]==["Mettre en file d'attente","Récupérer maintenant"]
        and L["d"]==["Le collaborateur le récupère à son tour.","Le collaborateur commence la récupération immédiatement."]
        and L["b"][0][0]=="Mettre en file" and L["b"][1][0]=="Récupérer maintenant" and "mpv-bp" in L["b"][1][1] and L["stack"] and L["full"] and L["bfull"] and L["bg"]!=L["bg1"]
        and L["helper"].startswith("Reçu uniquement après vérification et sauvegarde des fichiers.") and not L["tech"],
        f"{lbl} : section « Demander le DCE », 2 cartes empilées pleine largeur, textes validés, bouton bronze, helper concis, aucun détail technique {L and {k:L[k] for k in ('stack','full','bfull','bg','pw','sw','cw','helper')}}")
def dem(did,etat,**k):
    p=M["ao"][did]["portail"];d={"ao_id":did,"ref":p["ref"],"org":p["org"],"reference_attendue":M["ao"][did]["ref"],"etat":etat,"demande_par":"u_autre","demande_le":N(-30),"maj":N(-10),
       "cg":None,"validation":None,"tache":None,"erreur":None,"resultat":None};d.update(k);return d
AUT=["fx-q1","fx-q2","fx-q4","fx-q5","fx-q6","fx-q7","fx-q8","fx-q9","fx-q9~sakdat"]   # fx-q3 : NON autorisé
M["dce"]={"config":{"file":{"actif":True,"trigger":"trig_FICTIF01","dossiers":AUT},"drive":{"actif":True,"server":"Google Drive"}}}
M["dce_demande"]={"fx-q4":dem("fx-q4","ouverture",tache={"run":"r1","jusqu":N(40)}),
  "fx-q5":dem("fx-q5","attente_validation_CG",cg=CG),
  "fx-q6":dem("fx-q6","echec",erreur={"code":"controle","motif":"page de contrôle ou CAPTCHA : arrêt, aucun contournement <b>x</b>","le":N(-3)}),
  "fx-q7":dem("fx-q7","pret",resultat={"stockage":"drive","ref":"fx-q7","verifie_le":N(-2),"fichiers":4,"zip_sha256":"cd"*32,"contenu":"ee"*32,"deja_importe":False,"cles":[],"le":N(-2)}),
  "fx-q8":dem("fx-q8","pret",resultat={"stockage":"drive","ref":"fx-q8","fichiers":0,"zip_sha256":"","cles":[],"le":N(-2)}),
  "fx-q9~sakdat":dem("fx-q9~sakdat","demandee")}
json.dump(M,open(os.path.join(SRV,"mockdb_mpv6.json"),"w",encoding="utf-8"),ensure_ascii=False)
MOCK=open(os.path.join(SRV,"mockdb_mpv6.json"),encoding="utf-8").read()
I2=INITSRC.replace("DB[c][id]=Object.assign(DB[c][id]||{},cp(d));","const mg=(t,x)=>{Object.entries(x).forEach(([k,v])=>{if(v&&typeof v==='object'&&!Array.isArray(v)&&t[k]&&typeof t[k]==='object'&&!Array.isArray(t[k]))mg(t[k],v);else t[k]=cp(v);});};DB[c][id]=DB[c][id]||{};mg(DB[c][id],cp(d));")
assert I2!=INITSRC
I2=I2.replace("set:async(d)=>{window.__writes.push([\"set\",path]);","set:async(d)=>{if(window.__failSet)throw{code:'unavailable'};window.__writes.push([\"set\",path]);")
I2=I2.replace('window.claude={use:async n=>n==="db"?db:','window.__mcp=[];const mcp={callTool:async(s,t,i,o)=>{window.__mcp.push([s,t,i]);if(window.__mcpFail)throw{code:"server_not_connected"};return{payload:{ok:true}};}};window.claude={use:async n=>n==="mcp"?mcp:n==="db"?db:')
assert "__mcp" in I2 and "__failSet" in I2
INIT=None;exec(I2)
LIVE="()=>{S.dceDem=JSON.parse(JSON.stringify(window.__DB.dce_demande||{}));S.dceConf=JSON.parse(JSON.stringify(window.__DB.dce.config));render();}"   # la base réelle pousse ces changements (live)
PAN="()=>{const p=document.querySelector('[data-mpv6-dpanel]');if(!p)return null;const q=s=>p.querySelector(s);return{k:p.dataset.mpv6Dpanel,t:p.innerText,h:p.innerHTML,st:q('[data-mpv6-dst]').dataset.mpv6Dst,"\
    "file:q('[data-mpv7-file]')&&!q('[data-mpv7-file]').disabled,now:q('[data-mpv7-now]')&&!q('[data-mpv7-now]').disabled,vis:!!(q('[data-mpv7-file]')&&q('[data-mpv7-now]')),"\
    "links:[...p.querySelectorAll('a')].map(a=>[a.innerText.trim(),a.href]),invA:p.querySelectorAll('.mpv7-inv a').length,zip:p.querySelectorAll('input[type=file]').length,"\
    "msg:(q('[data-mpv7-msg]')||{dataset:{}}).dataset.mpv7Msg,suivi:(q('[data-mpv7-etat]')||{dataset:{}}).dataset.mpv7Etat}}"
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");MC=lambda:ev("()=>window.__mcp.slice()")
    pg.wait_for_function("()=>S.dceConf&&S.mcp",timeout=20000);ev(B11)
    def sel(k):ev("k=>{MPV.tab='dce';MPN.outil='f:dce';MPV.outil='f:dce';MPV6.ds.q='';MPV6.ds.f='tout';MPV6.ds.sel=k;MPV.conf=null;render();}",k);pg.wait_for_timeout(250);return ev(PAN)
    # ===== filtres et compteurs =====
    sel("p:fxq:990201");G=ev("()=>{const G=mpvDceGroupes(Date.now());return G.O.map(g=>[g.k,g.dce.k])}")
    cat={"afaire":"sans","echec":"sans","file":"attente","cours":"cours","interv":"cours"};exp={"tout":len(G),"sans":0,"attente":0,"cours":0}
    for _,k in G:exp[cat.get(k,"sans")]+=1
    cn=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-mpv6-cf]')].map(b=>[b.dataset.mpv6Cf,+b.dataset.mpv6Cn]))")
    lab=ev("()=>[...document.querySelectorAll('[data-mpv6-cf]')].map(b=>b.innerText.replace(/\\s*\\d+$/,''))")
    chk(lab==["Tous","Sans demande","En attente","En cours"] and cn==exp,f"filtres Tous / Sans demande / En attente / En cours, compteurs réels {cn}")
    st={k:v for k,v in G};chk(st.get("p:fxq:990204")=="cours" and st.get("p:fxq:990205")=="interv" and st.get("p:fxq:990206")=="interv" and "p:fxq:990207" not in st and st.get("p:fxq:990208")=="afaire" and st.get("p:fxq:990209")=="file",
        f"états réels : ouverture=en cours ; CG=intervention ; CAPTCHA=intervention ; Drive vérifié=reçu (hors file) ; « prêt » non vérifié ≠ reçu ; demande d'un autre dossier de la consultation = en attente")
    # ===== panneau : inventaire, un seul lien, deux boutons, pas de ZIP =====
    P=sel("p:fxq:990201")
    pm=[l for l in P["links"] if "marchespublics" in l[1]]
    chk(P["vis"] and P["file"] and P["now"] and P["zip"]==0 and P["invA"]==0 and "demande interne" not in P["t"].lower() and len(pm)==1 and pm[0][0].startswith("Accéder au DCE sur PMMP")
        and "EntrepriseDemandeTelechargementDce" in pm[0][1] and "refConsultation=990201" in pm[0][1] and "orgAcronyme=fxq" in pm[0][1] and "Ajouter" not in P["t"],
        f"panneau : deux boutons visibles, un seul lien « Accéder au DCE sur PMMP » (même ID/org), aucun dépôt ZIP ni ajout manuel {pm}")
    chk("société" not in P["t"].lower().replace("jamais au nom d'une société","").replace("aucune société",""),"panneau sans société")
    laychk(ev(LAY),"bureau 1280 px");pg.screenshot(path=os.path.join(OUT,"cartes_bureau.png"))
    # ===== stockage privé à rétablir (dce/config.sante, constat réel) =====
    ev("()=>{window.__DB.dce.config.sante={stockage:{etat:'a_retablir',constate_le:'2026-10-20T12:58:00Z',motif:'renouvellement de la connexion Google Drive refusé (HTTP 400) au diagnostic de la tâche DCE <b>x</b>'}};}");ev(LIVE)
    P=sel("p:fxq:990201");w0,m0=len(W()),len(MC())
    sx=ev("()=>({b:!!document.querySelector('[data-mpv7-sante=a_retablir]'),t:(document.querySelector('[data-mpv7-sante]')||{innerText:''}).innerText,tab:!!document.querySelector('[data-mpv7-sante-tab]'),wq:!!document.querySelector('[data-mpv7-attente-stock]'),wn:!!document.querySelector('[data-mpv7-now-suspendu]'),h:(document.querySelector('[data-mpv7-sante]')||{innerHTML:''}).innerHTML})")
    chk(sx["b"] and "Connexion au stockage privé à rétablir" in sx["t"] and "20/10" in sx["t"] and sx["tab"] and sx["wq"] and sx["wn"] and P["file"] and not P["now"] and "<b>x</b>" not in sx["h"] and "Récupération en cours" not in P["t"] and "Reçu" not in P["t"].replace("Reçu uniquement",""),
        "stockage bloqué : bandeau « Connexion au stockage privé à rétablir » (date, motif échappé), « Récupérer maintenant » suspendu avec raison, « Mettre en file » possible avec avertissement d'attente, aucun faux statut")
    ev("()=>{mpv7Lancer(mpvDceGroupes(Date.now()).O.find(g=>g.id==='fx-q1'),true);mpv7Relancer({id:'fx-q1'});}");pg.wait_for_timeout(500)
    chk(len(W())==w0 and len(MC())==m0,"stockage bloqué : aucun réveil ni écriture par « Récupérer maintenant » / « Réessayer le démarrage », même appelés directement")
    ev("()=>{delete window.__DB.dce.config.sante;}");ev(LIVE);P=sel("p:fxq:990201")
    chk(P["now"] and not ev("()=>!!document.querySelector('[data-mpv7-sante]')"),"connexion rétablie (champ retiré) : « Récupérer maintenant » de nouveau disponible")
    # ===== Mettre en file : FIFO à deux demandes, puis Récupérer maintenant =====
    w0,m0=len(W()),len(MC());pg.click('[data-mpv7-file="fx-q1"]');pg.wait_for_timeout(700);ev(LIVE)
    d1=ev("()=>window.__DB.dce_demande['fx-q1']");P=sel("p:fxq:990201")
    chk(d1 and d1["etat"]=="demandee" and d1["immediat"] is False and d1["ao_id"]=="fx-q1" and d1["ref"]=="990201" and d1["org"]=="fxq" and len(MC())==m0 and P["st"]=="file" and P["msg"]=="ok" and "Position" in P["t"],
        f"« Mettre en file » : demande écrite (FIFO), aucun réveil, état « En attente » avec position — {P['st']}")
    pg.wait_for_timeout(1100);sel("p:fxq:990202");pg.click('[data-mpv7-file="fx-q2"]');pg.wait_for_timeout(700);ev(LIVE)
    pos=ev("()=>mpv7File()");chk(pos[:3]==["fx-q9~sakdat","fx-q1","fx-q2"] or pos.index("fx-q1")<pos.index("fx-q2"),f"FIFO : ordre de dépôt respecté {pos}")
    P=sel("p:fxq:990202");chk(not P["file"] and P["now"],"déjà en file : « Mettre en file » désactivé, « Récupérer maintenant » propose de passer en tête")
    m0=len(MC());pg.click('[data-mpv7-now="fx-q2"]');pg.wait_for_timeout(700);ev(LIVE)
    pos2=ev("()=>mpv7File()");mc=MC()[m0:]
    chk(pos2[0]=="fx-q2" and ev("()=>window.__DB.dce_demande['fx-q2'].immediat") is True and mc==[["Claude Code Remote","fire_trigger",{"trigger_id":"trig_FICTIF01","text":"DCE-FILE fx-q2"}]],
        f"« Récupérer maintenant » : passe en tête ({pos2[:3]}) et réveille la tâche tout de suite {mc}")
    P=sel("p:fxq:990202");chk("Position 1 sur" in P["t"],"position recalculée depuis la base : 1")
    d2=ev("()=>window.__DB.dce_demande['fx-q2']");P=sel("p:fxq:990202")
    chk(d2["reveil"]["ok"] is True and P["st"]=="file" and "Démarrage demandé" in P["t"] and "n'a pas encore commencé" in P["t"] and "Récupération en cours" not in P["t"],
        "démarrage demandé ≠ prise en charge : réveil enregistré en base, jamais « Récupération en cours » avant la prise par la tâche")
    ev("()=>{window.__DB.dce_demande['fx-q4'].tache.jusqu=new Date(Date.now()+30*6e4).toISOString();}");ev(LIVE);P=sel("p:fxq:990202")
    chk("traite en ce moment une autre demande" in P["t"],"tâche occupée par une autre demande : affiché honnêtement")
    # ===== Récupérer maintenant direct + réveil en échec =====
    ev("()=>{window.__mcpFail=true;}");m0=len(MC());sel("p:fxq:990208");pg.click('[data-mpv7-now="fx-q8"]');pg.wait_for_timeout(700);ev(LIVE);P=sel("p:fxq:990208")
    chk(ev("()=>window.__DB.dce_demande['fx-q8'].etat")=="demandee" and len(MC())==m0+1 and "prochain passage horaire" in ev("()=>(document.querySelector('[data-mpv7-msg]')||{innerText:''}).innerText")+P["t"] or "réveil" in P["t"],
        "réveil impossible (connecteur) : demande conservée en file, message honnête « prochain passage horaire »")
    d8=ev("()=>window.__DB.dce_demande['fx-q8']");P=sel("p:fxq:990208")
    chk(d8["reveil"]["ok"] is False and "non connecté" in (d8["reveil"]["motif"] or "") and "Réessayer le démarrage" in P["t"],"échec du réveil enregistré en base (visible après rechargement) et bouton « Réessayer le démarrage »")
    ev("()=>{window.__mcpFail=false;}");m0=len(MC());pg.click('[data-mpv7-relancer="fx-q8"]');pg.wait_for_timeout(700);ev(LIVE);P=sel("p:fxq:990208")
    chk(len(MC())==m0+1 and ev("()=>window.__DB.dce_demande['fx-q8'].reveil.ok") is True and "tâche réveillée" in P["t"],"réessai : nouvel appel réel au déclencheur, réveil confirmé")
    hq=ev("()=>window.__DB.dce_demande['fx-q8'].historique");chk(hq and hq[-1]["etat"]=="pret","l'ancienne demande (« prêt » non vérifié) est conservée dans l'historique, pas écrasée")
    # ===== dossier non autorisé : confirmation, liste blanche fusionnée =====
    P=sel("p:fxq:990203");w0=len(W());pg.click('[data-mpv7-file="fx-q3"]');pg.wait_for_timeout(300)
    cf=ev("()=>(document.querySelector('.mpv-conf')||{innerText:''}).innerText");chk("autorisés" in cf and len(W())==w0,"dossier non autorisé : confirmation explicite avant toute écriture")
    pg.click('[data-mpv-confok]');pg.wait_for_timeout(800);C=ev("()=>window.__DB.dce.config")
    chk("fx-q3" in C["file"]["dossiers"] and C["file"]["actif"] is True and C["file"]["trigger"]=="trig_FICTIF01" and all(x in C["file"]["dossiers"] for x in AUT) and C["drive"]["actif"] is True
        and ev("()=>window.__DB.dce_demande['fx-q3'].etat")=="demandee","autorisation : dossier ajouté à la liste (fusion : actif, tâche, autres dossiers et Drive conservés), puis demande écrite")
    # ===== doublon : même consultation via un autre dossier =====
    ev(LIVE);P=sel("p:fxq:990209");chk(P["st"]=="file" and not P["file"],"consultation déjà demandée via le dossier SAKDAT : état « En attente », aucun nouveau dépôt")
    # ===== concurrence : la tâche prend la demande entre l'affichage et le clic =====
    sel("p:fxq:990201");ev("()=>{window.__DB.dce_demande['fx-q1'].etat='ouverture';}");w0=len(W())
    ev("()=>{S.dceDem['fx-q1'].etat='echec';render();}");pg.wait_for_timeout(150);pg.click('[data-mpv7-file="fx-q1"]');pg.wait_for_timeout(700)
    chk(not [x for x in W()[w0:] if x[1].startswith("dce_demande/")] and ev("()=>window.__DB.dce_demande['fx-q1'].etat")=="ouverture" and ev("()=>document.querySelector('[data-mpv7-msg]').dataset.mpv7Msg")=="err",
        "concurrence : la base est relue avant d'écrire ; une récupération en cours n'est jamais écrasée")
    ev(LIVE)
    # ===== échec d'enregistrement =====
    ev("()=>{window.__failSet=true;}");sel("p:fxq:990206");m0=len(MC());pg.click('[data-mpv7-now="fx-q6"]');pg.wait_for_timeout(700);ev("()=>{window.__failSet=false;}")
    chk(ev("()=>window.__DB.dce_demande['fx-q6'].etat")=="echec" and len(MC())==m0 and ev("()=>document.querySelector('[data-mpv7-msg]').dataset.mpv7Msg")=="err","enregistrement refusé : rien mis en file, aucun réveil, état de la base affiché")
    # ===== intervention : CAPTCHA puis remise en file avec historique ; CG : acceptation humaine =====
    P=sel("p:fxq:990206");chk(P["st"]=="interv" and "vérification humaine" in P["t"] and "Prenez la main" in P["t"] and P["file"] and "<b>x</b>" not in P["h"] and "&lt;b&gt;" in P["h"],"CAPTCHA : « Intervention requise », prise en main proposée, remise en file possible, motif échappé")
    pg.click('[data-mpv7-file="fx-q6"]');pg.wait_for_timeout(700);d6=ev("()=>window.__DB.dce_demande['fx-q6']")
    chk(d6["etat"]=="demandee" and d6["historique"][-1]["erreur"]["code"]=="controle","remise en file : nouvelle demande, l'échec précédent conservé dans l'historique")
    ev(LIVE);P=sel("p:fxq:990205")
    chk(P["st"]=="interv" and "Intervention requise" in P["t"] and not ev("()=>window.__xss") and "&lt;script&gt;" in P["h"] and not P["file"] and not P["now"],"CG lues : « Intervention requise », texte échappé (aucun script), boutons de file désactivés")
    m0=len(MC());pg.click('[data-mpv7-valider="fx-q5"]');pg.wait_for_timeout(700);d5=ev("()=>window.__DB.dce_demande['fx-q5']")
    chk(d5["etat"]=="cg_validees" and d5["validation"]["empreinte"]==CG["empreinte"] and d5["validation"]["phrase"].startswith("J'accepte") and MC()[m0:][0][1]=="fire_trigger","acceptation humaine des CG : validation écrite (phrase + empreinte), tâche réveillée")
    # ===== en cours, reçu =====
    P=sel("p:fxq:990204");chk(P["st"]=="cours" and "Vous pouvez fermer EAIOS" in P["t"] and not P["file"] and not P["now"],"récupération en cours : progression serveur, boutons désactivés")
    ev("()=>{MPV6.ds.sel='p:fxq:990207';render();}");pg.wait_for_timeout(200);P=ev(PAN)
    chk(P["st"]=="pret" and "4 fichiers vérifiés" in P["t"] and "Drive privé" in P["t"] and not P["file"],"reçu : seulement avec stockage vérifié (fichiers, empreinte, date de vérification)")
    # ===== lecture seule =====
    ev("()=>{S.readOnly=true;render();}");P=sel("p:fxq:990201");w0=len(W())
    chk(P["vis"] and not P["file"] and not P["now"] and "Lecture seule" in P["t"],"lecture seule : boutons visibles mais désactivés, motif affiché");ev("()=>{S.readOnly=false;render();}")
    # ===== URL : liste blanche =====
    ok=ev("()=>[dcePmmpUrl({portail:{ref:'1\"><script>',org:'x'}}),dcePmmpUrl({portail:{ref:'123',org:'ab c'}}),dcePmmpUrl({portail:{ref:'123',org:'abc'}})]")
    chk(ok[0] is None and ok[1] is None and ok[2].startswith("https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce"),"lien PMMP : identifiants filtrés, hôte officiel seulement")
    # ===== ancienne demande interne (dossiers réels) =====
    old=ev("()=>{const G=mpvDceGroupes(Date.now());const g=G.O.find(g=>g.dce.ancien);return g?g.k:null}")
    if old:P=sel(old);chk(P["st"]=="afaire" and "Ancienne demande interne" in P["t"],"ancienne « demande interne » sans tâche : affichée « À demander », jamais comme une récupération")
    # ===== panneau Consultations : accès à la file =====
    ev(B11);x=ev("()=>{const dm=mpvDosMap();const e=mpvBase().R.find(e=>!e.x._ferme&&(dm[e.x.r+'/'+e.x.o]||[]).length&&mpvDce(dm[e.x.r+'/'+e.x.o]).k==='afaire');return e?e.k:null}")
    if x:
        ev("k=>{MPV.tab='cons';MPN.outil='veille';MPV.outil='veille';MPV.sel=k;render();}",x);pg.wait_for_timeout(300)
        chk(ev("()=>!!document.querySelector('[data-mpv7-godce]')&&!document.querySelector('[data-mpv-demander]')"),"Consultations : l'ancienne demande interne est remplacée par « Récupérer le DCE (file DCE) »")
        pg.click('[data-mpv7-godce]');pg.wait_for_timeout(400);chk(ev("()=>MPV.tab")=="dce","… qui ouvre l'onglet DCE sur la même consultation")
    reel=[w for w in W() if w[1].startswith("ao/") and w[1][3:] in REEL];chk(not reel,"aucune écriture sur les dossiers réels copiés")
    chk(not errs,f"aucune erreur JavaScript {errs[:3]}");ctx.close()
    ctx,pg,errs=demarrer(b,390,844);ev=lambda js,*a:pg.evaluate(js,*a);ev(B11);P=sel("p:fxq:990201")
    pg.click('[data-mpv6-row] button');pg.wait_for_timeout(300);laychk(ev(LAY),"mobile 390 px");pg.screenshot(path=os.path.join(OUT,"cartes_mobile.png"),full_page=True);ov=ev("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
    chk(ov<=0 and not errs,f"mobile 390 px : sans débordement ({ov})");ctx.close();b.close()
open(os.path.join(OUT,"resultat.txt"),"w",encoding="utf-8").write("\n".join(R))
print(sum(r.startswith("OK") for r in R),"/",len(R))
