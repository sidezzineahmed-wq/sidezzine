"""Recette mpv-2 · B1.1 Veille : barre de filtres + tiroir « Tous les filtres ». Banc qa_b21dec (base simulée, écritures tracées
dans __writes) + copie locale EN LECTURE du catalogue live (srv/). Les attentes sont recalculées indépendamment en JS de test."""
import os,json,re
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50"
NL="()=>+document.getElementById('mpv-lt').innerText.split(' ')[0]"
LST="()=>[...document.querySelectorAll('[data-mpv-row]')].map(r=>r.dataset.mpvRow)"
# moteur indépendant (tokens normalisés : accents, casse, ponctuation)
IND=r"""(o)=>{const tk=s=>String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
 const fm=followedMap(),Q=tk(o.q||''),m=o.qmode||'all',seq=(T,Q)=>{for(let i=0;i+Q.length<=T.length;i++)if(Q.every((w,j)=>T[i+j]===w))return true;return false;};
 const refm=/[\/\-]/.test(o.q||'')&&/\d/.test(o.q||'');
 return MPV.base.R.filter(e=>{const x=e.x;
  if((o.etat||'ouv')==='ouv'&&x._ferme)return false;if(o.etat==='clos'&&!x._ferme)return false;
  if(o.pert&&(e.sc.block||e.sc.s<60))return false;if(o.suivi){const f=!!fm[x.r+'/'+x.o];if(f!==(o.suivi==='oui'))return false;}
  if(Q.length){const R=tk(x.ref),F=[R,tk(x.obj),tk(x.mo),...(x.lx||[]).flatMap(p=>[tk(p),tk(nice(p))])],A=F.flat(),t=w=>/^\d+$/.test(w)?A.includes(w):A.some(z=>z.startsWith(w));
    if(m==='ref'||(m==='all'&&refm)){if(!seq(R,Q))return false;}else if(m==='phrase'){if(!F.some(T=>seq(T,Q)))return false;}else if(m==='any'){if(!Q.some(t))return false;}else if(!Q.every(t))return false;}
  return o.extra?o.extra(x):true;}).length;}"""
def INDX(o,extra):  # extra : corps JS d'un prédicat sur x
    return ev("o=>{const f="+IND+";o.extra=new Function('x',o.ex);return f(o);}",{**o,"ex":extra})
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);pg.wait_for_function(WAIT,timeout=30000);ev=lambda js,*a:pg.evaluate(js,*a);W=lambda:ev("()=>window.__writes.slice()");AK=lambda:ev("()=>Object.keys(S.ao).length")
    def SQ(t,mode=None):
        if mode:pg.select_option("#mpv-qm",mode);pg.wait_for_timeout(250)
        pg.fill("#mpv-q",t);pg.press("#mpv-q","Enter");pg.wait_for_timeout(450)
    def VF(**k):
        ev("k=>{S.vf={...JSON.parse(JSON.stringify(VF0)),sort:S.vf.sort,...k};vfSave();MPV.page=1;render();}",k);pg.wait_for_timeout(250)
    def OPEN(sel="#mpv-tf"):
        pg.click(sel);pg.wait_for_timeout(350)
    def DO(key,v):  # coche une option du tiroir
        pg.click(f'[data-mpv-o="{key}:{v}"]');pg.wait_for_timeout(250)
    APPLY=lambda:(pg.click("#mpv-dwok"),pg.wait_for_timeout(350))
    w0=len(W());k0=AK();ev(B11);pg.wait_for_timeout(700);ev("()=>{localStorage.removeItem('eaios.vf');S.vf=vfLoad();mpvMigr(S.vf);vfSave();render();}")
    # ===== A. barre : 3 lignes =====
    BAR=ev("""()=>{const r=s=>!!document.querySelector(s);return{r1:r('.mpv-r1 #mpv-q')&&r('.mpv-r1 #mpv-qm')&&r('.mpv-r1 #mpv-go'),qm:[...document.querySelectorAll('#mpv-qm option')].map(o=>o.textContent),
      qf:[...document.querySelectorAll('.mpv-r2 .mpv-qfl>span')].map(s=>s.textContent),tf:document.getElementById('mpv-tf').innerText.trim(),ax:[...document.querySelectorAll('.mpv-r3 [data-mpv-ax]')].map(b=>b.dataset.mpvAx),
      pert:r('.mpv-r3 #mpv-pert'),sort:r('.mpv-r3 #mpv-sort'),scope:r('[data-mpv-scope]'),old:r('#v_q')||r('[data-fpill]'),txt:document.querySelector('.mpv').innerText}}""")
    chk(BAR["r1"] and BAR["qm"]==["Tous les mots","Au moins un mot","Expression exacte","Référence exacte"] and BAR["qf"]==["Lieu d'exécution","Catégorie & domaine","Date limite","Acheteur public"] and BAR["tf"]=="Tous les filtres"
        and BAR["ax"]==["etat:ouv","etat:clos","etat:tout","suivi:","suivi:oui","suivi:non"] and BAR["pert"] and BAR["sort"] and not BAR["scope"] and not BAR["old"],"barre : ligne 1 recherche + 4 modes + Rechercher ; ligne 2 Lieu / Catégorie / Date limite / Acheteur + « Tous les filtres » (aucun critère) ; ligne 3 État × Suivi × Pertinentes + tri ; ancien périmètre exclusif retiré")
    chk(not re.search(r"MAQUETTE|Demande enregistrée avec succès|26/10/20|Approchée ET",BAR["txt"]) and "Filtres appliqués" in BAR["txt"],"aucun contenu de maquette (badge MAQUETTE, date d'exemple, « Approchée ET »)")
    # ===== B. recherche : 4 modes + régression 75/CL =====
    for q,m in (("travaux laayoune","all"),("travaux laayoune","any"),("fourniture de bureau","phrase"),("Laâyoune","all"),("FOURNITURE, bureau!","all")):
        SQ(q,m);e=ev(IND,{"q":q,"qmode":m});n=ev(NL)
        chk(n==e and n>0 and ev("()=>[S.vf.q,S.vf.qmode]")==[q.strip(),m],f"mode {m} « {q} » : {n} résultat(s) = recalcul indépendant (ET / OU / contigu ; accents, casse, ponctuation ignorés)")
    SQ("75/CL/2026","ref");e75=ev(IND,{"q":"75/CL/2026","qmode":"ref"});refs=ev("()=>[...document.querySelectorAll('[data-mpv-row] .mpv-ref')].map(r=>r.innerText)")
    chk(ev(NL)==e75 and e75>=1 and all(re.search(r"(^|[^0-9A-Za-z])75\s*/\s*CL\s*/\s*2026([^0-9A-Za-z]|$)",r,re.I) for r in refs),f"Référence exacte « 75/CL/2026 » : {e75} résultat(s), segments entiers {refs}")
    SQ("75/CL/2026","all");chk(ev(NL)==e75 and "segments exacts de la référence" in pg.inner_text(".mpv-hint"),"Tous les mots + saisie de type référence : même résultat, mode réellement appliqué annoncé")
    SQ("175/CL/2026","ref");chk(ev(NL)==ev(IND,{"q":"175/CL/2026","qmode":"ref"}) and not any(re.search(r"(^|[^0-9])75/CL/2026",r) and not "175/CL/2026" in r for r in ev("()=>[...document.querySelectorAll('[data-mpv-row] .mpv-ref')].map(r=>r.innerText)")),"« 175/CL/2026 » ≠ « 75/CL/2026 »")
    hid=ev("()=>{const e=MPV.base.R.find(e=>!e.x._ferme&&e.x.r&&!String(e.x.ref||'').includes(e.x.r)&&!(e.x.obj||'').includes(e.x.r)&&!(e.x.mo||'').includes(e.x.r));return e?e.x.r:null}")
    SQ(hid,"any");chk(ev(NL)==ev(IND,{"q":hid,"qmode":"any"}),f"numéro PMMP interne non affiché ({hid}) : aucune correspondance cachée (ni UUID ni URL)")
    pg.fill("#mpv-q","brouillon non validé");pg.wait_for_timeout(200);chk(ev("()=>S.vf.q")==hid,"saisie sans Entrée ni « Rechercher » : rien n'est appliqué")
    pg.click("#mpv-go");pg.wait_for_timeout(400);chk(ev("()=>[S.vf.q,document.activeElement.id]")==["brouillon non validé","mpv-q"],"bouton « Rechercher » : applique, focus conservé dans le champ")
    SQ("","all")
    # ===== C. axes indépendants : 18 combinaisons =====
    ev("()=>{const ks=MPV.base.R.filter(e=>e.x._ferme).slice(0,2).map(e=>e.x);ks.forEach((x,i)=>{S.ao['qa-fclos'+i]={portail:{ref:x.r,org:x.o},statut:'À examiner',lim:x.lim};});}")
    bad=[]
    for et in ("ouv","clos","tout"):
        for su in ("","oui","non"):
            for pe in (False,True):
                VF(etat=et,suivi=su,pert=pe);n=ev(NL) if ev("()=>!!document.getElementById('mpv-lt')") else None;e=ev(IND,{"etat":et,"suivi":su,"pert":pe})
                if n!=e:bad.append((et,su,pe,n,e))
    chk(not bad,f"État × Suivi × Pertinentes : 18 combinaisons = recalcul indépendant {bad[:3]}")
    VF();pg.click("#mpv-ax-suivi-oui");pg.wait_for_timeout(250);pg.click("#mpv-ax-etat-clos");pg.wait_for_timeout(250);pg.check("#mpv-pert");pg.wait_for_timeout(250);pg.click("#mpv-ax-etat-tout");pg.wait_for_timeout(250)
    chk(ev("()=>[S.vf.etat,S.vf.suivi,S.vf.pert,document.getElementById('mpv-ax-etat-tout').getAttribute('aria-checked'),document.getElementById('mpv-ax-suivi-oui').getAttribute('aria-checked')]")==["tout","oui",True,"true","true"] and ev("()=>document.getElementById('mpv-tf').dataset.mpvTf")=="0","axes cliqués : aucun n'efface l'autre (aria-checked) ; ils ne comptent pas comme filtres ; le tri non plus")
    VF()
    # ===== D. tiroir : ouverture depuis un filtre rapide, sections, focus =====
    OPEN('[data-mpv-qf="loc"]')
    D=ev("""()=>({dlg:!!document.querySelector('.mpv-dwp[role=dialog][aria-modal=true]'),n:document.querySelectorAll('.mpv-dw').length,dw:MPV.dw,foc:document.activeElement.dataset.mpvDnav,
      nav:[...document.querySelectorAll('[data-mpv-dnav]')].map(b=>b.innerText.trim()),foot:[...document.querySelectorAll('.mpv-dwf button')].map(b=>b.innerText.trim()),sticky:getComputedStyle(document.querySelector('.mpv-dwf')).position})""")
    chk(D["dlg"] and D["n"]==1 and D["dw"]=="loc" and D["foc"]=="loc" and D["nav"]==["Recherche","Acheteur & procédure","Localisation","Catégories & domaines","Dates","Montants","Conditions PMMP","Suivi & DCE","Disponibilité des données"]
        and D["foot"]==["Réinitialiser","Annuler","Appliquer les filtres"],f"« Lieu d'exécution » ouvre UN tiroir (dialogue modal) sur Localisation, focus dans la navigation ; 9 sections ; pied Réinitialiser / Annuler / Appliquer {D['foot']}")
    reg=ev("()=>Object.keys(S.cat.regions).find(r=>MPV.base.R.some(e=>!e.x._ferme&&e.x._regs.includes(r)&&e.x._regs.length===1))")
    DO("regs",reg);chk(ev("()=>S.vf.regs.length")==0 and ev("()=>MPV.dr.regs")==[reg],"choix dans le tiroir : brouillon seulement, rien appliqué")
    pg.keyboard.press("Escape");pg.wait_for_timeout(300)
    chk(ev("()=>[!!document.querySelector('.mpv-dw'),S.vf.regs.length,document.activeElement.dataset.mpvQf]")==[False,0,"loc"],"Échap : brouillon abandonné, focus rendu au filtre rapide d'origine")
    OPEN('[data-mpv-qf="loc"]');DO("regs",reg);pg.click("#mpv-dwa");pg.wait_for_timeout(300)
    chk(ev("()=>[!!document.querySelector('.mpv-dw'),S.vf.regs.length,document.activeElement.dataset.mpvQf]")==[False,0,"loc"],"Annuler : idem")
    OPEN('[data-mpv-qf="loc"]');DO("regs",reg);dn=ev("()=>+document.querySelector('[data-mpv-dwn]').dataset.mpvDwn");APPLY()
    eR=INDX({},f"return x._regs.includes({json.dumps(reg)})")
    BX=ev("""()=>({n:+document.getElementById('mpv-lt').innerText.split(' ')[0],qf:document.querySelector('[data-mpv-qf=loc]').innerText.trim(),tf:document.getElementById('mpv-tf').innerText.trim(),
      ch:[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.dataset.vfx),foc:document.activeElement.dataset.mpvQf,pg:MPV.page})""")
    chk(BX["n"]==eR==dn and BX["qf"]==reg and BX["tf"]=="Tous les filtres · 1" and BX["ch"]==["regs:"+reg] and BX["foc"]=="loc" and BX["pg"]==1,f"Appliquer : liste = compte annoncé dans le pied ({dn}) = recalcul ({eR}) ; filtre rapide, « Tous les filtres · 1 » et puce synchronisés ; page 1 ; focus rendu")
    # province (arborescence lieu)
    OPEN('[data-mpv-qf="loc"]');pg.click(f'[data-mpv-o="regs:{reg}"] ~ .mpv-oexp, [id^="mpvo-regs-"][data-mpv-o="regs:{reg}"]+.mpv-oexp');pg.wait_for_timeout(250)
    prov=ev("r=>{const ps=S.cat.regions[r].map(p=>p[0]);return ps.find(p=>MPV.base.R.some(e=>!e.x._ferme&&(e.x.lx||[]).includes(p)))}",reg)
    lab=ev("r=>document.querySelector('[data-mpv-o=\"regs:'+r+'\"]').parentElement.querySelector('.mpv-oexp').getAttribute('aria-label')",reg)
    DO("provs",prov);APPLY();eP=INDX({},f"return x._regs.includes({json.dumps(reg)})&&(x.lx||[]).includes({json.dumps(prov)})")
    chk(ev(NL)==eP and lab==f"Masquer les provinces de {reg}" and len(ev("()=>[...document.querySelectorAll('.mpv-r4 .mpv-x')]"))==2,f"Localisation : région → provinces ({prov}) : {eP} résultat(s) ; libellé « provinces » seulement pour les lieux")
    pg.click(f'.mpv-r4 [data-vfx="provs:{prov}"]');pg.wait_for_timeout(300)
    chk(ev("()=>[S.vf.provs.length,S.vf.regs.length,document.activeElement.id]")==[0,1,"mpv-fx-tout"] and ev(NL)==eR,"puce retirée seule (province), la région reste ; focus sur « Tout effacer »")
    pg.click("#mpv-fx-tout");pg.wait_for_timeout(300);chk(ev("()=>[S.vf.regs.length,document.getElementById('mpv-tf').dataset.mpvTf,document.activeElement.id]")==[0,"0","mpv-tf"],"« Tout effacer » : tous les critères retirés, focus sur « Tous les filtres »")
    # ===== E. catégories & domaines (3 niveaux) =====
    OPEN('[data-mpv-qf="cat"]');CT=pg.inner_text("#mpv-s-cat")
    d1=ev("()=>{const s=new Set();MPV.base.R.forEach(e=>(e.x._doms||[]).forEach(z=>{if(z.split(' / ').length===3)s.add(z)}));return [...s].find(z=>MPV.base.R.some(e=>!e.x._ferme&&(e.x._doms||[]).includes(z)))}")
    top,mid=d1.split(" / ")[0],d1.rsplit(" / ",1)[0]
    lab=ev("t=>document.querySelector('[data-mpv-o=\"doms:'+t+'\"]').parentElement.querySelector('.mpv-oexp').getAttribute('aria-label')",top)
    pg.click(f'[data-mpv-o="doms:{top}"]+.mpv-oexp');pg.wait_for_timeout(250);pg.click(f'[data-mpv-o="doms:{mid}"]+.mpv-oexp');pg.wait_for_timeout(250)
    vis3=ev("z=>!!document.querySelector('[data-mpv-o=\"doms:'+z+'\"]')",d1);DO("doms",d1);DO("doms",mid);DO("cats","Travaux");APPLY()
    eD=INDX({},f"return x.cat==='Travaux'&&(x._doms||[]).some(z=>[{json.dumps(d1)},{json.dumps(mid)}].includes(z))")
    chk(lab.startswith("Afficher les sous-domaines de") and "provinces" not in CT and vis3 and ev(NL)==eD and "Catégorie principale" in CT,f"Catégories : principale distincte des domaines ; « Afficher les sous-domaines » (jamais « provinces ») ; 3 niveaux ; multisélection : {eD} résultat(s)")
    VF()
    # ===== F. acheteur / entité / procédure / référence =====
    OPEN('[data-mpv-qf="ach"]');mo=ev("()=>document.querySelector('[data-mpv-o^=\"mos:\"]').dataset.mpvO.slice(4)");n_mo=ev("()=>+document.querySelector('[data-mpv-o^=\"mos:\"] .mpv-on').innerText")
    pg.fill("#mpv-ls-mos",mo[:12]);pg.wait_for_timeout(500);chk(ev("m=>!!document.querySelector('[data-mpv-o=\"mos:'+m+'\"]')",mo),"recherche dans la liste des acheteurs")
    DO("mos",mo);APPLY();eM=INDX({},f"return x._mo==={json.dumps(mo)}");chk(ev(NL)==eM==n_mo,f"Acheteur public « {mo[:40]} » : {eM} = compte affiché dans le tiroir")
    DS=ev("()=>{const a=document.querySelector('[data-mpv-dis=mode]'),b=document.querySelector('[data-mpv-dis=type]');return null}")
    OPEN('[data-mpv-qf="ach"]');DS=ev("()=>({dis:[...document.querySelectorAll('[data-mpv-dis]')].map(d=>d.dataset.mpvDis),enr:!!document.querySelector('[data-mpv-enr]'),opts:document.querySelectorAll('[data-mpv-o^=\"tach:\"],[data-mpv-o^=\"mpass:\"]').length,txt:document.getElementById('mpv-s-ach').innerText})")
    chk(DS["dis"]==[] and DS["enr"] and DS["opts"]>=4 and "Non transmis au catalogue" not in DS["txt"] and "Type d'acheteur" not in DS["txt"],"mpv-3 : mode de passation et classification Etat / CL / EEP actifs (données PMMP jointes), plus de bloc « non disponible »")
    pg.click("#mpv-dwa");pg.wait_for_timeout(200);VF()
    pr=ev("()=>MPV.base.R.find(e=>!e.x._ferme&&e.x.proc).x.proc");VF(procs=[pr]);chk(ev(NL)==INDX({},f"return x.proc==={json.dumps(pr)}"),f"Procédure « {pr} »")
    VF(ref="75/CL/2026");chk(ev(NL)==e75,"filtre Référence exacte (tiroir) = même moteur que le mode Référence exacte")
    # ===== G. qualification reliée, libellés sans null =====
    VF();OPEN();pg.click("#mpv-dn-cond");pg.wait_for_timeout(250);pg.click("#mpv-acc-qual");pg.wait_for_timeout(300);QT=pg.inner_text("#mpv-s-cond")
    chk(not re.search(r"\bnull\b|undefined",QT) and "Secteur non renseigné (Laboratoires)" in QT and "Système" in QT and "Qualification exigée par l'annonce (pas celle d'une société)" in QT,"Conditions : aucun « null » ; « Secteur non renseigné (Laboratoires) » explicite ; qualification de l'annonce ≠ de la société")
    chk(("Classe illisible" in QT) == ev("()=>MPV.base.R.some(e=>!e.x._ferme&&(e.x.q||[]).some(q=>q.c&&!/^\\d+$/.test(q.c)&&q.c!=='S'))") and not re.search(r"Classe [A-Z]{2,}",QT),"classe source illisible signalée comme telle (jamais transformée en lettre inventée)")
    DO("qsys","Laboratoires");sk="Laboratoires|null";DO("sects",sk);
    cl=ev("()=>{const b=[...document.querySelectorAll('[data-mpv-o^=\"qcls:Laboratoires|\"]')];return b.length?b[0].dataset.mpvO.slice(5):null}")
    DO("qcls",cl);APPLY()
    c_=cl.split("|")[1];eQ=INDX({},f"return (x.q||[]).some(q=>(q.m||'')==='Laboratoires'&&q.s==null&&(q.c||'')==={json.dumps(c_)})")
    eLoose=INDX({},f"const Q=x.q||[];return Q.some(q=>q.m==='Laboratoires'&&q.s==null)&&Q.some(q=>q.m==='Laboratoires'&&(q.c||'')==={json.dumps(c_)})")
    chk(ev(NL)==eQ and eQ<=eLoose and not re.search(r"null",pg.inner_text(".mpv-r4")),f"système → secteur non renseigné → classe {c_} reliés sur une même ligne : {eQ} (non relié : {eLoose}) ; puces sans « null »")
    chk(ev("()=>S.vf.qcls.every(k=>k.startsWith('Laboratoires|'))") and "comparaison de classes entre systèmes" in QT,"classes par système, aucune comparaison inter-systèmes")
    # ===== H. inconnus on/off et comptes =====
    VF(tp="oui");a=ev(NL);eT=INDX({},"return x.tp===true");uT=INDX({},"return x.tp==null")
    OPEN();pg.click("#mpv-dn-cond");pg.wait_for_timeout(200);pg.click("#mpv-acc-tp");pg.wait_for_timeout(250)
    nu=ev("()=>+document.querySelector('[data-mpv-inc=tp] [data-mpv-nu]').dataset.mpvNu");dis0=ev("()=>document.getElementById('mpv-inc-tp').disabled")
    pg.click("#mpv-inc-tp");pg.wait_for_timeout(250);dn=ev("()=>+document.querySelector('[data-mpv-dwn]').dataset.mpvDwn");APPLY()
    L=ev("()=>[+document.getElementById('mpv-lt').innerText.split(' ')[0],(document.querySelector('[data-mpv-nu-list]')||{dataset:{}}).dataset.mpvNuList,[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.innerText)]")
    chk(a==eT and nu==uT and not dis0 and L[0]==dn==eT+uT and L[1]==str(uT) and any("fiches non renseignées : TPE/PME" in c for c in L[2]),f"TPE/PME : {eT} réservées ; + {uT} non renseignées incluses sur demande, comptées et signalées à part (liste, puce) ; jamais confondues avec « Non »")
    VF(tp="non");chk(ev(NL)==INDX({},"return x.tp===false"),"« Non réservées » n'inclut pas les fiches inconnues")
    VF();OPEN();pg.click("#mpv-dn-cond");pg.wait_for_timeout(200);pg.click("#mpv-acc-tp");pg.wait_for_timeout(250)
    chk(ev("()=>document.getElementById('mpv-inc-tp').disabled") and "s'applique quand un choix est fait" in ev("()=>document.querySelector('[data-mpv-inc=tp]').textContent"),"inclusion désactivée tant qu'aucun choix n'est fait (pas de critère fantôme)");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    VF(ag="sans");eA=INDX({},"return x.det&&!x.ag");VF(ag="sans",inc=["ag"]);eA2=INDX({},"return !x.det||!x.ag")
    chk(eA<eA2 and ev(NL)==eA2,f"Agrément « non indiqué » : {eA} fiches lues seulement ; fiches non lues ajoutées seulement sur demande ({eA2})")
    VF(estMin="1");eM1=INDX({},"return x.est>=1e6");VF(estMin="1",inc=["mts"]);eM2=INDX({},"return x.est>=1e6||x.est==null")
    chk(ev(NL)==eM2 and eM1<eM2,f"Estimation ≥ 1 M DH : {eM1} ; + estimations inconnues sur demande : {eM2} (inconnu ≠ 0)")
    VF(doms=[d1]);eD1=ev(NL);VF(doms=[d1],inc=["doms"]);chk(ev(NL)==eD1+INDX({},"return !(x._doms||[]).length"),"domaine inconnu inclus sur demande, compté")
    # ===== I. montants, caution 0, par lots, dates =====
    VF(estMin="1",estMax="5");chk(ev(NL)==INDX({},"return x.est>=1e6&&x.est<=5e6"),"Estimation TTC min / max")
    VF(estMin="5",estMax="1");OPEN();pg.click("#mpv-dn-mts");pg.wait_for_timeout(200);chk("minimum est supérieur au maximum" in pg.inner_text("#mpv-s-mts"),"min > max signalé");pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    VF(mts=["np"]);chk(ev(NL)==INDX({},"return x.det&&!x.est"),"estimation « non publiée ou 0 » distincte d'inconnue")
    VF(cau="zero");z0=ev(NL);chk(z0==INDX({},"return x.cau===0"),f"caution 0 DH selon PMMP : {z0} (jamais déduite d'une fiche non lue)")
    VF(cau="np");chk(ev(NL)==INDX({},"return x.det&&x.cau==null"),"caution non indiquée (fiche lue) ≠ inconnue")
    VF(lots="oui");chk(ev(NL)==INDX({},"return !!x.lots"),"allotissement")
    VF(pub="7");CD=ev("()=>casaJour(Date.now())");eP7=INDX({},"const U=s=>{const[a,b,c]=s.split('-').map(Number);return Date.UTC(a,b-1,c)};return !!x.pub&&(U('"+CD+"')-U(x.pub))/864e5<=7")
    chk(ev(NL)==eP7,f"mise en ligne depuis 7 jours, jour de Casablanca ({CD}) : {eP7}")
    d0=ev("()=>casaJour(Date.now()-3*864e5)");VF(pubFrom=d0);ePF=INDX({},f"return !!x.pub&&x.pub>='{d0}'");VF(limTo=d0,etat="tout");eLT=INDX({"etat":"tout"},f"return !!x.lim&&x.lim<='{d0}'")
    chk(ev(NL)==eLT and ev("()=>S.vf.pubFrom")=="","date limite et date de mise en ligne : filtres distincts")
    VF(pubFrom=d0);chk(ev(NL)==ePF and any("Mise en ligne du" in c for c in ev("()=>[...document.querySelectorAll('.mpv-r4 .mpv-x')].map(x=>x.innerText)")),f"mise en ligne depuis le {d0} : {ePF}, puce dédiée")
    VF(lim="7");chk(ev(NL)==INDX({},"return x._d!=null&&x._d<=7"),"date limite sous 7 jours")
    # ===== J. réinitialiser, recherches enregistrées (seule écriture explicite), migration =====
    VF(regs=[reg],tp="oui",etat="clos",pert=True);OPEN();pg.click("#mpv-dwr");pg.wait_for_timeout(250)
    chk(ev("()=>[S.vf.regs.length,MPV.dr.regs.length,MPV.dr.tp,MPV.dr.etat]")==[1,0,"","ouv"],"Réinitialiser : brouillon seulement, rien appliqué avant « Appliquer »")
    pg.click("#mpv-dwa");pg.wait_for_timeout(200)
    nw=len(W());VF(regs=[reg],qmode="phrase",q="fourniture de bureau");OPEN();pg.fill("#mpv-svn","QA fixture région");pg.wait_for_timeout(100);pg.click("#mpv-svb");pg.wait_for_timeout(500)
    ws=[w for w in W()[nw:]];sv=ev("()=>S.saved.find(r=>r.nom==='QA fixture région')")
    chk(ws==[["set","veille/recherches"]] and sv and sv["vf"]["regs"]==[reg] and sv["vf"]["qmode"]=="phrase" and "sort" not in sv["vf"],f"« Enregistrer cette recherche » : action explicite, une écriture (veille/recherches, base simulée) {ws}")
    pg.click("#mpv-dwa");pg.wait_for_timeout(200);VF();OPEN();i=ev("()=>S.saved.findIndex(r=>r.nom==='QA fixture région')");pg.click(f"#mpv-sv-{i}");pg.wait_for_timeout(250)
    chk(ev("()=>[S.vf.regs.length,MPV.dr.regs.length,MPV.dr.qmode]")==[0,1,"phrase"],"recherche enregistrée chargée dans le brouillon seulement");APPLY()
    chk(ev("()=>[S.vf.regs.length,S.vf.q]")==[1,"fourniture de bureau"] and len(W())==nw+1,"appliquée explicitement, sans nouvelle écriture")
    MG=ev("""()=>{localStorage.setItem('eaios.vf',JSON.stringify({q:'abc',exact:true,view:'pour',classe:'3',clss:['Etat'],regs:['X'],sort:'score'}));const v=vfLoad();const w=mpvMigr(v);S.vf=v;MPV.migr=w;vfSave();render();
      return{w,v:[v.q,v.qmode,v.pert,v.classe,v.clss.length,v.regs,v.sort,v.etat,v.inc.length],ban:(document.querySelector('[data-mpv-migr]')||{}).innerText||''}}""")
    chk(MG["v"]==["abc","phrase",True,"",0,["X"],"score","ouv",0] and len(MG["w"])==2 and "classes au-dessus de 3" in MG["ban"],f"migration : expression exacte → mode, « pour le groupe » → case Pertinentes, filtres conservés ; classe globale et type d'acheteur retirés AVEC avertissement {MG['v']}")
    sv2=ev("()=>{const v={...VF0,...{q:'x',classe:'4'}};return [mpvMigr(v).length,v.classe]}");chk(sv2==[1,""],"migration appliquée aussi aux recherches enregistrées anciennes")
    ev("()=>{MPV.migr=[];}");VF()
    # ===== K. pagination et sélection =====
    VF();pg.click('[data-mpv-page="2"]');pg.wait_for_timeout(300);sel=ev("()=>document.querySelectorAll('[data-mpv-row]')[3].dataset.mpvRow");ev("k=>{MPV.sel=k;render();}",sel)
    pg.select_option("#mpv-qm","any");pg.wait_for_timeout(300);chk(ev("()=>MPV.page")==2,"changement de mode sans texte : critères identiques, page conservée")
    VF(regs=[reg]);chk(ev("()=>[MPV.page,MPV.sel]")==[1,sel],"critères changés → page 1 ; fiche sélectionnée conservée")
    chk(ev("()=>document.querySelectorAll('[data-mpv-row]').length")<=10 and ev("()=>document.querySelectorAll('.mpv [data-mpv-o]').length")==0,"10 lignes au plus dans le DOM ; options du tiroir absentes tant qu'il est fermé")
    # ===== L. piège de focus, Échap, superposition =====
    VF();OPEN();pg.focus("#mpv-dwok");pg.keyboard.press("Tab");pg.wait_for_timeout(100);f1=ev("()=>document.activeElement.closest('.mpv-dwp')?document.activeElement.id||document.activeElement.dataset.mpvDnav||'in':'OUT'")
    pg.keyboard.press("Shift+Tab");pg.wait_for_timeout(100);f2=ev("()=>document.activeElement.id||document.activeElement.outerHTML.slice(0,90)")
    chk(f1!="OUT" and f2=="mpv-dwok" and ev("()=>[...document.querySelectorAll('[role=dialog]')].filter(d=>d.getClientRects().length).length")==1,f"piège de focus : Tab après « Appliquer » revient au début du tiroir ({f1}), Maj+Tab y retourne ({f2}) ; un seul dialogue")
    pg.keyboard.press("Escape");pg.wait_for_timeout(200);chk(ev("()=>[!!document.querySelector('.mpv-dw'),document.activeElement.id]")==[False,"mpv-tf"],"Échap ferme sans appliquer, focus sur « Tous les filtres »")
    # ===== M. aucune écriture métier =====
    ev("()=>{delete S.ao['qa-fclos0'];delete S.ao['qa-fclos1'];}")
    chk(len([w for w in W()[w0:] if w[1]!="veille/recherches"])==0 and AK()==k0,"recherche, filtres, tiroir, pages, sélection : aucune écriture métier, aucun dossier créé (seule la recherche enregistrée, explicitement)")
    chk(not errs,f"aucune erreur JavaScript {errs[:2]}")
    ctx.close()
    # ===== N. responsive clair / sombre, tiroir ouvert =====
    for w,sch in ((390,"light"),(615,"dark"),(768,"light"),(1440,"dark")):
        c=b.new_context(viewport={"width":w,"height":860},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function(WAIT,timeout=30000);q.wait_for_timeout(500);q.evaluate(B11);q.wait_for_timeout(600)
        q.evaluate("()=>{S.vf={...JSON.parse(JSON.stringify(VF0)),tp:'oui',inc:['tp'],regs:[Object.keys(S.cat.regions)[0]]};vfSave();render();}");q.wait_for_timeout(300)
        o1=q.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth");q.screenshot(path=f"{OUT}/mpv2_barre_{w}_{sch}.png")
        q.click("#mpv-tf");q.wait_for_timeout(400);q.click("#mpv-dn-cond");q.wait_for_timeout(200)
        M=q.evaluate("""()=>{const p=document.querySelector('.mpv-dwp').getBoundingClientRect(),f=document.querySelector('.mpv-dwf').getBoundingClientRect(),c=document.getElementById('mpv-dwc');
          const bg=getComputedStyle(document.querySelector('.mpv-dwp')).backgroundColor;return{pw:Math.round(p.width),fb:Math.round(f.bottom),vh:innerHeight,ov:c.scrollWidth-c.clientWidth,bg,
          ok:document.getElementById('mpv-dwok').getBoundingClientRect().bottom<=innerHeight}}""")
        q.screenshot(path=f"{OUT}/mpv2_tiroir_{w}_{sch}.png")
        dark=sch=="dark";bgd=sum(int(z) for z in re.findall(r"\d+",M["bg"])[:3])<200
        chk(o1==0 and M["ov"]<=0 and M["ok"] and M["fb"]<=M["vh"] and (M["pw"]==w if w<=760 else M["pw"]<w) and bgd==dark and not e,f"{w} px {'sombre' if dark else 'clair'} : barre sans débordement ; tiroir {'plein écran' if w<=760 else 'latéral'} ({M['pw']} px), pied « Appliquer » visible, fond {'sombre' if dark else 'clair'} {M}")
        c.close()
    b.close()
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
