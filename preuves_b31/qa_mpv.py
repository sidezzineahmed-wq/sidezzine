"""Recette mpv-1/mpv-2 · bureau B1.1 Veille. Banc qa_b21dec (base simulée locale, écritures tracées dans __writes) + copie locale EN LECTURE
du catalogue live (srv/catalogue*.json). Les seules modifications : base simulée, et ajouts en mémoire de la page de test (S.cat, S.ao)."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50"
# recalcul indépendant : clé organisme:numéro ; clôture = horloge de Casablanca comparée à la minute (sans heure : fin du jour)
EXP="""()=>{const P=d=>{const p=new Intl.DateTimeFormat('en-US',{timeZone:'Africa/Casablanca',hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).formatToParts(d),g=t=>+p.find(x=>x.type===t).value;return[g('year'),g('month'),g('day'),g('hour')%24,g('minute')];};
 const n=P(new Date()),nk=((n[0]*100+n[1])*100+n[2])*1e4+n[3]*100+n[4],today=Date.UTC(n[0],n[1]-1,n[2]);const seen=new Set();let ouv=0,pour=0,sept=0,clos=0;
 S.cat.items.forEach(x=>{const k=x.o+':'+x.r;if(seen.has(k))return;seen.add(k);let pas=false,dd=null;const m=String(x.lim||'').match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);
   if(m){const h=String(x.h||'').match(/^(\\d{1,2}):(\\d{2})$/),kk=((+m[1]*100+ +m[2])*100+ +m[3])*1e4+(h?+h[1]*100+ +h[2]:2359);pas=h?kk<=nk:kk<nk;dd=Math.round((Date.UTC(+m[1],m[2]-1,+m[3])-today)/864e5);}
   if(pas){clos++;return;}ouv++;const sc=scoreOf(x);if(!sc.block&&sc.s>=60)pour++;if(dd!=null&&dd<=7)sept++;});
 const G={};Object.entries(S.ao).forEach(([id,a])=>{if(!a||(!a.soc&&!a.portail))return;const k=a.portail&&a.portail.ref?a.portail.ref+'/'+(a.portail.org||''):'b:'+(a.base||id);(G[k]=G[k]||[]).push(id);});
 let dce=0;Object.values(G).forEach(ids=>{if(ids.some(id=>dceEtat(id,S.ao[id]).k==='pret'))return;if(ids.some(id=>{const a=S.ao[id];if(!['À examiner','En préparation'].includes(a.statut))return false;const L=limEtat({lim:a.lim,h:(String(a.heure||'').match(/(\\d{1,2})\\s*[hH:]\\s*(\\d{2})?/)||[]).slice(1).filter(Boolean).length?String(a.heure).replace(/^(\\d{1,2})\\s*[hH:]\\s*(\\d{2})?.*$/,(z,a1,b1)=>a1.padStart(2,'0')+':'+(b1||'00')):''},Date.now());return!L.passe;}))dce++;});
 return{ouv,pour,sept,clos,dce,n:seen.size};}"""
KP="()=>Object.fromEntries([...document.querySelectorAll('[data-mpv-kpi]')].map(c=>[c.dataset.mpvKpi,c.dataset.mpvN]))"
NL="()=>+document.getElementById('mpv-lt').innerText.split(' ')[0]"
def SQ(t):
    pg.fill("#mpv-q",t);pg.press("#mpv-q","Enter");pg.wait_for_timeout(450)
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);pg.wait_for_function(WAIT,timeout=30000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");AK=lambda:ev("()=>Object.keys(S.ao).length")
    w0=len(W());k0=AK();ev(B11);pg.wait_for_timeout(600)
    # ===== A. composition et source =====
    T=pg.inner_text(".mpv")
    chk("Veille des marchés" in T and "Repérer les opportunités et récupérer les DCE à temps." in T and ev("()=>[...document.querySelectorAll('.mpv-fil li')].map(l=>l.innerText.trim()).slice(1)")==["Marchés publics","S1 Veille & qualification","B1.1 Veille"] and not re.search(r"PROPOSITION|DONNÉES D'EXEMPLE|AO EX-|Plateforme de veille",T),"titre, sous-titre, fil Marchés publics / S1 / B1.1 ; aucun contenu de maquette")
    chk(ev("()=>[...document.querySelectorAll('[data-mpv-tab]')].map(t=>[t.innerText.replace(/\s*\(\d+\)$/,''),t.getAttribute('role'),t.getAttribute('aria-selected')])")==[["Consultations","tab","true"],["DCE à récupérer","tab","false"],["Suivies","tab","false"]],"onglets Consultations / DCE à récupérer / Suivies")
    BD=ev("()=>{const d=document.querySelector('details.mpv-band');return{open:d.open,maj:(d.querySelector('[data-mpv-maj]')||{}).innerText||'',fr:(d.querySelector('[data-mpv-frais]')||{dataset:{}}).dataset.mpvFrais,ob:document.querySelector('.mpv-ob').getAttribute('href'),src:d.querySelector('.mpv-src').textContent,ant:!!d.querySelector('[data-mpv-err=anterieurs]'),cur:!!d.querySelector('[data-mpv-err=dernier]'),json:/[{}\\[\\]]/.test(d.querySelector('.mpv-src').textContent)}}")
    ET=json.load(open(os.path.join(SRV,"catalogue_etat.json"),encoding="utf-8"));fin=ET["listing"]["dernier_succes"]["fin"]
    exp_maj=ev("f=>{const P=casaParts(new Date(f));return'Actualisé le '+P.day+'/'+P.month+' à '+P.hour+':'+P.minute}",fin)
    chk(not BD["open"] and BD["maj"].startswith(exp_maj) and "(heure du Maroc)" in BD["maj"] and BD["fr"] in ("ok","vieux","ko","inc") and BD["ob"]=="https://claude.ai/artifact/AUczkckGChVg7tbN1SWuQw",f"bandeau : vraie dernière mise à jour en heure du Maroc ({BD['maj']}), fraîcheur calculée ({BD['fr']}), « Ouvrir la dernière version » réelle ; détail replié")
    chk(BD["ant"] and not BD["cur"] and "essais antérieurs" in BD["src"] and "le dernier essai a réussi" in BD["src"] and "couverture 100" in BD["src"] and "de ces pages de listing" in BD["src"] and "statut inconnu" in BD["src"] and "date de lecture réelle inconnue" in BD["src"] and not BD["json"],"source et couverture : erreurs anciennes ≠ échec du dernier essai ; couverture 100 % limitée aux pages de listing ; absentes = statut inconnu ; détails anciens à date inconnue ; aucune erreur JSON brute")
    # ===== B. indicateurs : recalcul indépendant =====
    X=ev(EXP);K=ev(KP)
    chk(K=={"ouv":str(X["ouv"]),"pour":str(X["pour"]),"sept":str(X["sept"]),"dce":str(X["dce"])},f"4 indicateurs = recalcul indépendant (clé PMMP, Casablanca) {K} ; clôturées {X['clos']} exclues")
    chk(ev(NL)==X["ouv"] and ev("()=>document.querySelectorAll('[data-mpv-row]').length")<=10,f"liste « Toutes les consultations » = consultations ouvertes ({X['ouv']}) ; 10 lignes au plus dans le DOM")
    pg.click('[data-mpv-kpi="pour"]');pg.wait_for_timeout(400);n1=ev(NL)
    pg.click('[data-mpv-kpi="sept"]');pg.wait_for_timeout(400);n2=ev(NL);ch=ev("()=>[...document.querySelectorAll('.mpv-x')].map(x=>x.innerText)")
    pg.click('[data-mpv-kpi="ouv"]');pg.wait_for_timeout(400);n3=ev(NL)
    chk(n1==X["pour"] and n2==X["sept"] and n3==X["ouv"] and any("7 jours" in c for c in ch),f"clic indicateur → liste exactement égale ({n1}, {n2}, {n3}) ; filtre « Clôture sous 7 jours » visible")
    pg.click('[data-mpv-kpi="dce"]');pg.wait_for_timeout(400)
    chk(ev("()=>[MPV.tab,+document.getElementById('mpv-do').innerText.split(' ')[0]]")==["dce",X["dce"]],"clic « DCE à récupérer » → onglet DCE, même nombre")
    DT=ev("()=>({o:document.querySelectorAll('#mpv-do ~ ul [data-mpv-dg], section[aria-labelledby=mpv-do] [data-mpv-dg]').length,e:+document.querySelector('[data-mpv-dech]').dataset.mpvDech})")
    chk(DT["o"]==X["dce"],f"DCE : ouvertes listées ({DT['o']}) ; échues ou clôturées séparées hors compteur ({DT['e']}), rien supprimé")
    pg.click('[data-mpv-tab="cons"]');pg.wait_for_timeout(300)
    # ===== C. dédoublonnage, dates, clôture (ajouts EN MÉMOIRE au catalogue de la page de test) =====
    ev("""()=>{const P=casaParts(Date.now()),j=P.year+'-'+P.month+'-'+P.day,m=new Date(Date.now()-60e3),Q=casaParts(m),hm=Q.hour+':'+Q.minute,src=S.cat.items[0];
      window.__n0=S.cat.items.length;const mk=(r,o,ref,mo,lim,h)=>Object.assign({},src,{r,o,ref,mo,lim,h,obj:'Objet fictif QA '+r,lx:['LAAYOUNE'],det:false,est:null,cau:null,q:[]});
      S.cat.items.push(Object.assign({},src),mk('QA1','qa','QA/1','ACHETEUR QA',j,hm),mk('QA2','qa','QA/2','ACHETEUR QA',j,''),mk('QA3','qa','QA/3','ACHETEUR QA','',''),mk('QA4','qb','QA/3','ACHETEUR QA','2099-01-01','10:00'));catIndex();MPV.bk=null;render();}""")
    X2=ev(EXP);K2=ev(KP)
    chk(int(K2["ouv"])==X["ouv"]+3 and X2["ouv"]==int(K2["ouv"]) and X2["clos"]==X["clos"]+1,f"doublon exact (même organisme:numéro) compté une fois ; même référence + acheteur mais numéros différents comptés séparément ; heure du jour passée (1 min) = clôturée ; date du jour sans heure = ouverte ({K2['ouv']})")
    SQ("fictif QA")
    Q=ev("()=>Object.fromEntries([...document.querySelectorAll('[data-mpv-row]')].map(r=>[r.dataset.mpvRow,r.querySelector('.mpv-dt').innerText.replace(/\\n/g,' | ')]))")
    chk({"qa:QA2","qa:QA3","qb:QA4"}<=set(Q) and "qa:QA1" not in Q and "heure non précisée" in Q["qa:QA2"] and "Aujourd'hui" in Q["qa:QA2"] and "Date limite inconnue" in Q["qa:QA3"] and "À vérifier" in Q["qa:QA3"],f"recherche par référence ; dates : heure non précisée, date inconnue explicite {Q}")
    pg.click('#mpv-ax-etat-clos');pg.wait_for_timeout(400)
    chk(ev("()=>[...document.querySelectorAll('[data-mpv-row]')].map(r=>r.dataset.mpvRow)")==["qa:QA1"] and "Clôturée" in pg.inner_text('[data-mpv-row="qa:QA1"]'),"filtre « Clôturées » : la consultation dont l'heure est passée y est, seulement là")
    pg.click('#mpv-ax-etat-ouv');pg.wait_for_timeout(300)
    ev("()=>{MPV.sel='qa:QA3';render();}");PA=ev("()=>document.querySelector('[data-mpv-panel]').innerText")
    chk("Inconnue (fiche détaillée pas encore lue)" in PA and "Date limite inconnue" in PA and "éligibilité à vérifier en Analyse" in PA and "Composition du DCE à vérifier" in PA,"fiche : estimation / caution / qualification inconnues ≠ 0 ; date inconnue ; pertinence ≠ éligibilité ; composition du DCE à vérifier (aucun inventaire supposé)")
    z=ev("()=>{const e=MPV.base.R.find(e=>e.x.cau===0&&!e.x._ferme);return e?e.k:null}")
    if z:
        ev(f"()=>{{MPV.sel='{z}';render();}}");chk("0 DH selon PMMP, à vérifier dans le DCE" in pg.inner_text("[data-mpv-panel]"),"caution 0 sur PMMP : gardée avec mention « à vérifier dans le DCE »")
    ev("()=>{S.cat.items.splice(window.__n0);catIndex();MPV.bk=null;S.vf.q='';vfSave();MPV.sel=null;render();}");pg.wait_for_timeout(300)
    # ===== D. recherche, filtres, tri, pages, sélection =====
    e0=ev("()=>{const e=MPV.base.R.filter(e=>!e.x._ferme)[123];return{k:e.k,ref:e.x.ref,mo:e.x.mo}}")
    SQ(e0["ref"]);chk(e0["k"] in ev("()=>[...document.querySelectorAll('[data-mpv-row]')].map(r=>r.dataset.mpvRow)") and ev("()=>document.activeElement.id")=="mpv-q","recherche par référence : annonce trouvée, focus conservé")
    SQ("")
    reg=ev("()=>Object.keys(S.cat.regions)[0]")
    ev("r=>{S.vf.regs=[r];vfSave();S.vfOpen=false;render();}",reg);pg.wait_for_timeout(300)
    NR=ev("r=>MPV.base.R.filter(e=>!e.x._ferme&&e.x._regs.includes(r)).length",reg);MR=ev("r=>MPV.base.R.filter(e=>!e.x._ferme&&e.x._regs.includes(r)&&e.x._regs.length>1).length",reg)
    chk(ev(NL)==NR,f"filtre Région « {reg} » : {NR} annonces (dont {MR} multi-régions comptées dans chaque région concernée)")
    ev("()=>{S.vf.regs=[];vfSave();render();}");pg.select_option("#mpv-sort","lim");pg.wait_for_timeout(300)
    TS=ev("()=>[...document.querySelectorAll('[data-mpv-row]')].map(r=>{const e=MPV.base.by.get(r.dataset.mpvRow);return e.x._inst!=null?e.x._inst:Date.parse(e.x.lim+'T23:59:00Z')})")
    pg.select_option("#mpv-sort","score");pg.wait_for_timeout(300);SS=ev("()=>[...document.querySelectorAll('[data-mpv-row]')].map(r=>MPV.base.by.get(r.dataset.mpvRow).sc.s)")
    chk(TS==sorted(TS) and SS==sorted(SS,reverse=True) and ev("()=>document.activeElement.id")=="mpv-sort",f"tri : échéance la plus proche (croissante) puis pertinence (décroissante), sélectionnable au clavier")
    pg.select_option("#mpv-sort","lim");pg.wait_for_timeout(200)
    pg.click('[data-mpv-page="2"]');pg.wait_for_timeout(300);rg=ev("()=>document.querySelector('[data-mpv-rng]').dataset.mpvRng")
    chk(rg.startswith("11-20/") and ev("()=>document.activeElement.id")=="mpv-lt","pagination : page 2 = résultats 11 à 20, focus sur le titre de la liste")
    r3=ev("()=>document.querySelectorAll('[data-mpv-row]')[2].dataset.mpvRow");pg.click(f'[data-mpv-sel="{r3}"]');pg.wait_for_timeout(300)
    chk(ev("k=>[document.querySelector('[data-mpv-panel]').dataset.mpvPanel,document.querySelector('[data-mpv-sel=\"'+k+'\"]').getAttribute('aria-current'),document.activeElement.dataset.mpvSel]",r3)==[r3,"true",r3],"sélection : bonne annonce dans la fiche, ligne marquée, focus conservé sur la ligne (bureau)")
    PM=ev("k=>{const e=MPV.base.by.get(k);return[document.querySelector('[data-mpv-pmmp]').href,'https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation='+encodeURIComponent(e.x.r)+'&orgAcronyme='+encodeURIComponent(e.x.o)]}",r3)
    chk(PM[0]==PM[1],"« Voir sur PMMP » : URL réelle de cette consultation (numéro + organisme)")
    SQ("zzzz-introuvable")
    chk(ev("()=>!!document.querySelector('[data-mpv-hors]')&&!!document.querySelector('[data-mpv-vide]')"),"sélection hors des résultats filtrés : conservée et signalée ; liste vide expliquée")
    SQ("")
    chk(ev("()=>[MPV.page,MPV.sel]")[1]==r3,"retour sans recherche : sélection conservée")
    # ===== D2. recherche B1.1 (mpv-1b) : champs visibles seulement, référence exacte par segments =====
    IND="""(q)=>{const tk=s=>String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);const Q=tk(q);
      const refm=/[\/\-]/.test(q)&&/\d/.test(q);return MPV.base.R.filter(e=>!e.x._ferme).filter(e=>{const x=e.x,R=tk(x.ref),A=[...R,...tk(x.obj),...tk(x.mo),...(x.lx||[]).flatMap(p=>[...tk(p),...tk(nice(p))])];
        if(refm){for(let i=0;i+Q.length<=R.length;i++)if(Q.every((w,j)=>R[i+j]===w))return true;return false;}
        return Q.every(w=>/^\d+$/.test(w)?A.includes(w):A.some(t=>t.startsWith(w)));}).map(e=>e.k).sort();}"""
    LST="()=>{const f=S.vf,o=MPV.base.R.filter(e=>mpvM(e,f,null));return o.map(e=>e.k).sort()}"
    pg.click('#mpv-ax-etat-ouv');pg.wait_for_timeout(200);ev("()=>{S.vf.suivi='';S.vf.pert=false;S.vf.qmode='all';S.vf.lim='';vfSave();render();}")
    SQ("75/CL/2026")
    E75=ev(IND,"75/CL/2026");L75=ev(LST);refs=ev("()=>[...document.querySelectorAll('[data-mpv-row] .mpv-ref')].map(r=>r.innerText)")
    loose=ev("()=>MPV.base.R.filter(e=>!e.x._ferme&&FACETS.q(e.x,{q:'75/CL/2026',exact:false})).length")
    chk(L75==E75 and ev(NL)==len(E75) and all(re.search(r"(^|[^0-9A-Za-z])75\s*/\s*CL\s*/\s*2026([^0-9A-Za-z]|$)",r,re.I) for r in refs) and not any(("SKTRA" in r or "81300" in r or "TNG" in r) for r in refs),f"« 75/CL/2026 » : {len(E75)} résultat(s), seulement des références contenant exactement 75/CL/2026 {refs} (l'ancienne recherche approchée en donnait {loose})")
    SQ("175/CL/2026");chk(ev(LST)==ev(IND,"175/CL/2026"),"« 175/CL/2026 » : segments exacts (75/CL/2026 n'y correspond pas)")
    for qq in ("travaux laayoune","fourniture bureau","Laâyoune"):
        SQ(qq);Lq=ev(LST);Eq=ev(IND,qq)
        chk(Lq==Eq and ev(NL)==len(Eq) and len(Eq)>0,f"« {qq} » : tous les termes (ET) dans référence / objet / acheteur / lieux affichés, accents ignorés : {len(Eq)} résultat(s)")
    hid=ev("()=>{const e=MPV.base.R.find(e=>!e.x._ferme&&e.x.r&&!String(e.x.ref||'').includes(e.x.r)&&!(e.x.obj||'').includes(e.x.r));return e?e.x.r:null}")
    if hid:
        SQ(hid);chk(ev(LST)==ev(IND,hid),f"numéro PMMP interne non affiché ({hid}) : pas de correspondance cachée")
    ev("()=>{S.vf.q='travaux laayoune';vfSave();render();}");pg.click('[data-mpv-qf="cat"]');pg.wait_for_timeout(300)
    VC=ev("()=>{const b=[...document.querySelectorAll('[data-mpv-o^=\"cats:\"]')].find(x=>x.dataset.mpvO==='cats:Travaux');return b?+b.querySelector('.mpv-on').innerText:null}")
    pg.click('#mpv-dwa');pg.wait_for_timeout(200);ET=ev("ks=>ks.filter(k=>MPV.base.by.get(k).x.cat==='Travaux').length",ev(IND,"travaux laayoune"));chk(VC==ET,f"tiroir, Catégorie principale : compteur « Travaux » = résultats de la même recherche en catégorie Travaux ({VC} = {ET})")
    ev("()=>{S.vf.q='';vfSave();render();}");pg.wait_for_timeout(300)
    chk(len(W())==w0 and AK()==k0,"sélection, filtres, recherche, tri, pages, onglets : aucune écriture, aucun dossier créé")
    # ===== E. suivre (confirmation explicite) =====
    nf=ev("()=>{const fm=followedMap();const e=MPV.base.R.find(e=>!e.x._ferme&&!fm[e.x.r+'/'+e.x.o]&&!S.ao['pmmp-'+e.x.r]);return e.k}")
    ev("k=>{MPV.page=1;MPV.sel=k;render();}",nf);pg.wait_for_timeout(200)
    pg.click(f'[data-mpv-panel] [data-mpv-suivre]');pg.wait_for_timeout(200);c1=ev("()=>!!document.querySelector('[data-mpv-confok]')")
    pg.click('[data-mpv-confko]');pg.wait_for_timeout(200)
    chk(c1 and len(W())==w0 and "Ce n'est pas une décision de participer" not in pg.inner_text("[data-mpv-panel]"),"« Suivre » : confirmation explicite (suivre ≠ participer) ; Annuler n'écrit rien")
    pg.click(f'[data-mpv-panel] [data-mpv-suivre]');pg.wait_for_timeout(200);pg.click('[data-mpv-confok]');pg.wait_for_timeout(1500)
    r_=ev("k=>k.split(':')[1]",nf);ws=[w for w in W()[w0:] if w[1].startswith("ao/")]
    chk(ws==[["set","ao/pmmp-"+r_]] and ev("()=>!!document.querySelector('[data-mpv-panel] [data-mpv-dos]')") and ev("()=>document.querySelector('[data-mpv-pdce]').dataset.mpvPdce")=="afaire",f"suivi confirmé : un seul dossier créé (ao/pmmp-{r_}, base simulée), étoile « suivie », DCE « À récupérer » (pas reçu)")
    # ===== F. demander le DCE : confirmation, base confirmée, idempotence, échec + réessai =====
    did="pmmp-"+r_;w1=len(W())
    pg.click('[data-mpv-panel] [data-mpv-demander]');pg.wait_for_timeout(200);chk(len(W())==w1 and "Une demande n'est pas un DCE reçu" in pg.inner_text("[data-mpv-panel]"),"« Demander le DCE » : confirmation explicite, rien d'écrit avant")
    pg.click('[data-mpv-confok]');pg.wait_for_timeout(1200)
    D1=ev("i=>[document.querySelector('[data-mpv-pdce]').dataset.mpvPdce,(document.querySelector('[data-mpv-dem]')||{dataset:{}}).dataset.mpvDem,window.__DB.ao[i].dceDemandeLe?1:0,!!document.querySelector('[data-mpv-panel] [data-mpv-demander]')]",did)
    chk(D1==["encours","ok",1,False] and "Demande enregistrée" in pg.inner_text("[data-mpv-panel]") and ev("()=>document.querySelector('[data-mpv-pdce]').innerText")=="Demande enregistrée",f"demande confirmée par la base : « Demande enregistrée », jamais « DCE reçu » ; plus de bouton (pas de doublon) {D1}")
    ev("i=>{mpvDemander(i);}",did);pg.wait_for_timeout(500);chk(len([w for w in W()[w1:] if w[1]=="ao/"+did])==1,"seconde demande : refusée par le gestionnaire existant (idempotence), aucune nouvelle écriture")
    ev("i=>{S.ao[i].fichiers=Object.assign({},S.ao[i].fichiers,{dce:{id:'x',nom:'DCE-fictif.zip'}});render();}",did);RC=ev("()=>[document.querySelector('[data-mpv-pdce]').dataset.mpvPdce,document.querySelector('.mpv-inv').innerText]")
    ev("i=>{delete S.ao[i].fichiers.dce;render();}",did)
    chk(RC[0]=="pret" and "DCE-fictif.zip" in RC[1],"« DCE reçu » seulement quand un fichier est joint au dossier ; inventaire = fichiers réels")
    # échec : base qui refuse l'écriture (base simulée) → état relu de la base + Réessayer
    nf2=ev("()=>{const fm=followedMap();return MPV.base.R.find(e=>!e.x._ferme&&!fm[e.x.r+'/'+e.x.o]&&!S.ao['pmmp-'+e.x.r]).k}")
    ev("k=>{MPV.sel=k;render();}",nf2);pg.click('[data-mpv-panel] [data-mpv-suivre]');pg.click('[data-mpv-confok]');pg.wait_for_timeout(1500);d2="pmmp-"+nf2.split(":")[1]
    ev("""()=>{const o=S.db.doc.bind(S.db);window.__dbdoc=S.db.doc;S.db.doc=p=>{const r=o(p);if(String(p).startsWith('ao/'))return Object.assign({},r,{set:async d=>{throw{code:'unavailable'};},update:async d=>{throw{code:'unavailable'};}});return r;};}""")
    pg.click('[data-mpv-panel] [data-mpv-demander]');pg.click('[data-mpv-confok]');pg.wait_for_timeout(1500)
    E1=ev("i=>[(document.querySelector('[data-mpv-dem]')||{dataset:{}}).dataset.mpvDem,document.querySelector('[data-mpv-pdce]').dataset.mpvPdce,!!(window.__DB.ao[i]||{}).dceDemandeLe]",d2)
    ev("()=>{S.db.doc=window.__dbdoc;}")
    chk(E1==["err","afaire",False] and "Réessayer" in pg.inner_text("[data-mpv-panel]"),f"échec d'écriture : « non confirmée », état relu de la base (À récupérer), « Réessayer » {E1}")
    pg.click('[data-mpv-panel] [data-mpv-dem] button');pg.wait_for_timeout(200);pg.click('[data-mpv-confok]');pg.wait_for_timeout(1200)
    chk(ev("i=>[(document.querySelector('[data-mpv-dem]')||{dataset:{}}).dataset.mpvDem,!!window.__DB.ao[i].dceDemandeLe]",d2)==["ok",True],"réessai : demande confirmée par la base")
    # ===== G. retour de dossier : filtres, page et sélection conservés =====
    ev("()=>{S.vf.q='';MPV.page=3;vfSave();render();}");pg.wait_for_timeout(200);sel=ev("()=>document.querySelectorAll('[data-mpv-row]')[1].dataset.mpvRow");pg.click(f'[data-mpv-sel="{sel}"]');pg.wait_for_timeout(200)
    ev("i=>mpvOuvrir(i,'dce')",did);pg.wait_for_timeout(600);o1=ev("()=>[S.aoId,document.querySelector('[data-mpn-dossier-vue]').dataset.mpnDossierVue]")
    pg.click('[data-mpn-retour]');pg.wait_for_timeout(600)
    chk(o1==[did,"MP-B1.1|dce"] and ev("()=>[!!document.querySelector('.mpv'),MPV.page,MPV.sel,MPV.tab]")==[True,3,sel,"cons"],"ouvrir le DCE du dossier (B1.1, étape DCE) puis retour : page, sélection et onglet conservés")
    # ===== H. suivies (historique hors catalogue) et lecture seule =====
    pg.click('[data-mpv-tab="suiv"]');pg.wait_for_timeout(400)
    SV=ev("()=>({o:document.querySelectorAll('section[aria-labelledby=mpv-so] [data-mpv-suiv-id]').length,h:+document.querySelector('[data-mpv-hist]').dataset.mpvHist,tot:Object.values(S.ao).filter(a=>a&&(a.portail||a.veille)).length,hc:[...document.querySelectorAll('[data-mpv-suiv-id]')].filter(r=>r.innerText.includes('hors catalogue')).length})")
    chk(SV["o"]+SV["h"]==SV["tot"] and SV["hc"]>=1,f"Suivies : en cours {SV['o']} + historique {SV['h']} = tous les dossiers suivis ({SV['tot']}), dont {SV['hc']} hors catalogue conservés")
    pg.focus('[data-mpv-tab="suiv"]');pg.keyboard.press("ArrowRight");pg.wait_for_timeout(200);chk(ev("()=>[MPV.tab,document.activeElement.dataset.mpvTab]")==["cons","cons"],"clavier : flèches entre les onglets")
    ev("()=>{S.readOnly=true;render();}");RO=ev("()=>({s:document.querySelectorAll('.mpv-star.ro').length,b:document.querySelectorAll('[data-mpv-suivre],[data-mpv-demander]').length})");ev("()=>{S.readOnly=false;render();}")
    chk(RO["s"]>=1 and RO["b"]==0,"lecture seule : ni « Suivre » ni « Demander le DCE » (étoiles inactives)")
    # ===== I. chargement / indisponible =====
    ev("()=>{window.__cat=S.cat;S.cat=null;S.catState='loading';render();}");L1=ev(KP);t1=pg.inner_text(".mpv")
    ev("()=>{S.catState='absent';render();}");t2=pg.inner_text(".mpv");ev("()=>{window.__as=S.aoState;S.aoState='err';render();}");L3=ev(KP)
    ev("()=>{S.cat=window.__cat;S.catState='ok';S.aoState=window.__as;MPV.bk=null;render();}")
    chk(L1["ouv"]=="" and "Chargement du catalogue" in t1 and "Catalogue PMMP indisponible" in t2 and L3["dce"]=="","chargement : « — » et « Chargement du catalogue… » ; catalogue absent : indisponible explicite ; dossiers en erreur : « — » (jamais 0 inventé)")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
    ctx.close()
    # ===== J. responsive + mobile (panneau / retour à la liste) =====
    for (w,h,sch) in ((390,844,"light"),(390,844,"dark"),(615,900,"light"),(768,1000,"dark"),(1440,1000,"light"),(1440,1000,"dark")):
        tag=f"{w}{'_sombre' if sch=='dark' else ''}";c=b.new_context(viewport={"width":w,"height":h},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function(WAIT,timeout=30000);q.wait_for_timeout(600);q.evaluate(B11);q.wait_for_timeout(600)
        M=q.evaluate("()=>{const v=document.querySelector('.mpv'),V=v.getBoundingClientRect();return{ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,out:[...v.querySelectorAll('.mpv-kpi,.mpv-row,.mpv-fp,.mpv-sort,.mpv-chip,.mpv-pan,.mpv-ob,.mpv-band,.mpv-pg button')].filter(x=>{const r=x.getBoundingClientRect();return r.width&&(r.right>V.right+1||r.left<V.left-1)}).length,ink:getComputedStyle(document.querySelector('.mpv-h1')).color,bg:getComputedStyle(document.querySelector('.mpv-kpi')).backgroundColor,pan:getComputedStyle(document.querySelector('.mpv-pan')).display}}")
        q.screenshot(path=f"{OUT}/mpv_{tag}.png",full_page=True);lum=lambda c:sum(int(x) for x in re.findall(r"\d+",c)[:3]);dark=sch=="dark"
        ok=M["ov"]<=1 and M["out"]==0 and not e and ((lum(M["ink"])>lum(M["bg"])) if dark else (lum(M["ink"])<lum(M["bg"])))
        if w<=768:
            r1=q.evaluate("()=>document.querySelector('[data-mpv-row]').dataset.mpvRow");q.click(f'[data-mpv-sel="{r1}"]');q.wait_for_timeout(300)
            P1=q.evaluate("()=>[getComputedStyle(document.querySelector('.mpv-lst')).display,getComputedStyle(document.querySelector('.mpv-pan')).display,document.activeElement.id]")
            q.screenshot(path=f"{OUT}/mpv_{tag}_fiche.png",full_page=True);q.click('[data-mpv-back]');q.wait_for_timeout(300)
            P2=q.evaluate("k=>[getComputedStyle(document.querySelector('.mpv-lst')).display,document.activeElement.dataset.mpvSel]",r1)
            ok=ok and M["pan"]=="none" and P1==["none","flex","mpv-ph"] and P2==["block",r1]
        chk(ok,f"{tag} : aucun débordement, lisible{', liste → fiche (focus titre) → « Retour à la liste » (focus ligne)' if w<=768 else ', liste et fiche côte à côte'} {M}")
        c.close()
    b.close()
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
