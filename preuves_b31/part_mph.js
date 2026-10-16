/* ===================== mph-1 · Accueil du département Marchés publics (maquette approuvée) =====================
   Affichage et navigation seulement : aucune écriture, aucune création, aucun changement de statut ni de décision.
   Chiffres calculés depuis les données chargées (S.ao, profils et coffres des sociétés, RC lus), avec les règles des pages
   destinations : décision B2.1 (b21d-11 « À compléter / vérifier » : b21dEval), statuts existants, étapes aoSteps.
   Périmètre « ouvert » : dossier société (a.soc) au statut « À examiner » ou « En préparation » dont la date limite
   (heure de Casablanca) n'est pas dépassée ; date inconnue : gardé et signalé. Déposé / Attribué / Non retenu / Abandonné : hors urgence.
   Les routes réutilisent MPN (mpnBureau, mpnAller, mpnDosOuvrir) et les 14 bureaux MPD_BUR sans les modifier. */
const MPH={v:"mph-1",soc:"",q:"",svc:"MP-S2",prio:null,ck:null,cache:null};
const MPH_TZ="Africa/Casablanca";
const MPH_SVC={"MP-S1":"Veille & qualification","MP-S2":"Analyse & conformité","MP-S3":"Préparation des offres","MP-S4":"Dépôt & résultats","MP-S5":"Pilotage & référentiel"};
const MPH_SBUT={"MP-S1":"Repérer et qualifier les marchés publiés.","MP-S2":"Analyser le DCE, vérifier les exigences, décider de participer.","MP-S3":"Chiffrer, assembler et contrôler chaque offre.","MP-S4":"Déposer à temps et suivre chaque résultat.","MP-S5":"Suivre le portefeuille, les capacités et les textes."};
const MPH_BDESC={"MP-B1.1":"Annonces et DCE à récupérer","MP-B2.1":"Note d'analyse et décision","MP-B2.2":"Lecture du RC et du CPS","MP-B2.3":"Éligibilité pour cet appel d'offres","MP-B2.4":"Acheteurs et concurrence",
 "MP-B3.1":"Prix ligne par ligne","MP-B3.2":"Assembler le dossier d'offre","MP-B3.3":"Contrôle des pièces","MP-B3.4":"Devis fournisseurs et sous-traitants",
 "MP-B4.1":"Signature et dépôt","MP-B4.2":"Résultats et retours d'expérience","MP-B5.1":"Portefeuille et agenda","MP-B5.2":"Capacités des sociétés","MP-B5.3":"Textes officiels"};
const MPH_P={doc:'<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',up:'<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v4h16v-4"/>',
 bino:'<circle cx="6.5" cy="15.5" r="3.5"/><circle cx="17.5" cy="15.5" r="3.5"/><path d="M10 15h4M5 12l2-7h3l1 7M19 12l-2-7h-3l-1 7"/>',pen:'<path d="M4 20l4-1L19 8l-3-3L5 16z"/><path d="M14 7l3 3"/>',
 bars:'<path d="M5 20v-6M10 20V9M15 20V12M20 20V5"/>',scale:'<path d="M12 4v16M7 20h10M5 7h14"/><path d="M5 7l-3 6a3 3 0 006 0zM19 7l-3 6a3 3 0 006 0z"/>',
 people:'<circle cx="8.5" cy="8" r="3"/><circle cx="16.5" cy="8" r="3"/><path d="M3 19c0-3 2.5-5 5.5-5s5.5 2 5.5 5M13 14.5c1-.4 2.2-.5 3.5-.5 3 0 5 2 5 5"/>',chart:'<path d="M4 20h16M4 20V4"/><path d="M7 15l4-4 3 3 5-6"/><path d="M15 8h4v4"/>',
 calc:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h2M12 12h2M16 12v5M8 16h2M12 16h2"/>',folder:'<path d="M3 7h6l2 2h10v10H3z"/>',check:'<path d="M9 6h11M9 12h11M9 18h11"/><path d="M3 6l1.5 1.5L7 5M3 12l1.5 1.5L7 11M3 18l1.5 1.5L7 17"/>',
 truck:'<path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',flag:'<path d="M5 21V4h11l-2 4 2 4H5"/>',cal:'<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
 gauge:'<path d="M4 16a8 8 0 1116 0"/><path d="M12 16l4-5"/>',book:'<path d="M5 4h9a3 3 0 013 3v13H8a3 3 0 01-3-3z"/><path d="M5 17a3 3 0 013-3h9"/>',lock:'<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
 search:'<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',arrow:'<path d="M5 12h14M13 6l6 6-6 6"/>',team:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 19c0-3 2.7-5 6-5s6 2 6 5M15 14.5c3 0 6 1.5 6 4.5"/>'};
const MPH_SICO={"MP-S1":"bino","MP-S2":"doc","MP-S3":"pen","MP-S4":"up","MP-S5":"bars"};
const MPH_BICO={"MP-B1.1":"bino","MP-B2.1":"scale","MP-B2.2":"doc","MP-B2.3":"people","MP-B2.4":"chart","MP-B3.1":"calc","MP-B3.2":"folder","MP-B3.3":"check","MP-B3.4":"truck","MP-B4.1":"up","MP-B4.2":"flag","MP-B5.1":"cal","MP-B5.2":"gauge","MP-B5.3":"book"};
const mphI=(k,c)=>`<svg class="${c||"mph-i"}" viewBox="0 0 24 24" aria-hidden="true">${MPH_P[k]||""}</svg>`;
/* ---- dates : heure de Casablanca (Intl), jamais l'heure du poste ---- */
function mphParts(d){try{const p=new Intl.DateTimeFormat("en-US",{timeZone:MPH_TZ,hourCycle:"h23",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit"}).formatToParts(d),g=t=>+(p.find(x=>x.type===t)||{}).value;
  return{y:g("year"),m:g("month"),d:g("day"),h:g("hour")%24,mi:g("minute"),s:g("second")};}catch(e){return{y:d.getFullYear(),m:d.getMonth()+1,d:d.getDate(),h:d.getHours(),mi:d.getMinutes(),s:d.getSeconds()};}}
function mphOff(t){const p=mphParts(new Date(t));return(Date.UTC(p.y,p.m-1,p.d,p.h,p.mi,p.s)-Math.floor(t/1000)*1000)/60000;}
function mphCasa(y,m,d,h,mi){const g=Date.UTC(y,m-1,d,h,mi);let t=g-mphOff(g)*60000;t=g-mphOff(t)*60000;return new Date(t);}
function mphLim(a){const L=String((a&&a.lim)||"");if(!/^\d{4}-\d{2}-\d{2}/.test(L))return{k:"inc"};
  const[y,m,d]=L.slice(0,10).split("-").map(Number),x=String(a.heure||"").match(/(\d{1,2})\s*[hH:]\s*(\d{2})?/),hh=x&&+x[1]<24?+x[1]:null,mm=x?+(x[2]||0):0;
  /* heure connue : cet instant exact ; heure inconnue : la date reste ouverte jusqu'à la fin du jour (signalé « heure non précisée ») */
  const fin=hh!=null?mphCasa(y,m,d,hh,mm):new Date(mphCasa(y,m,d+1,0,0).getTime()-1);
  return{k:"ok",y,m,d,hh,mm,heure:hh!=null,fin,t:fin.getTime()};}
const mphP2=n=>String(n).padStart(2,"0");
function mphDateTxt(L){return L.k!=="ok"?"Date limite inconnue":mphP2(L.d)+"/"+mphP2(L.m)+"/"+L.y+(L.heure?" à "+mphP2(L.hh)+":"+mphP2(L.mm):"");}
function mphRel(L,now){if(L.k!=="ok")return{t:"À vérifier",u:false};const ms=L.t-now;if(ms<0)return{t:"Échue",u:true};
  const P=mphParts(new Date(now)),j=Math.round((Date.UTC(L.y,L.m-1,L.d)-Date.UTC(P.y,P.m-1,P.d))/864e5);
  if(L.heure&&ms<48*36e5){const h=Math.max(1,Math.ceil(ms/36e5));return{t:h<=1&&ms<36e5?"Dans moins d'1 h":"Dans "+h+" h",u:true};}
  const t=j<=0?"Aujourd'hui":j===1?"Demain":"Dans "+j+" jours";return{t:t+(L.heure?"":" (heure non précisée)"),u:j<=1};}
/* ---- périmètre et calculs ---- */
function mphSig(){const m=Math.floor(Date.now()/6e4);let s=S.aoState+"|"+S.dbState+"|"+m+"|"+Object.keys(S.rc||{}).length+"|"+Object.keys(S.jur||{}).length;
  Object.entries(S.ao||{}).forEach(([id,a])=>{if(a)s+="|"+id+":"+a.statut+":"+a.soc+":"+a.lim+":"+a.heure+":"+(a.decision?a.decision.verdict+a.decision.le:"")+":"+(a.noteMoyens?1:0)+":"+Object.keys(a.fichiers||{}).length;});
  (SOC||[]).forEach(z=>{const d=(S.docs||{})[z.sid]||{};s+="|"+z.sid+":"+((d.profil||{}).maj||"")+":"+JSON.stringify(d.coffre||{}).length+":"+Object.keys(d.fichiers||{}).length+":"+(d.references||[]).length+":"+JSON.stringify(d.meta||{}).length;});
  Object.entries((typeof B21D!=="undefined"&&B21D.pf)||{}).forEach(([k,F])=>{s+="|"+k+":"+(F&&F.st);});return s;}
function mphOuverts(now){const seen=new Set(),L=[],ech=[];
  Object.entries(S.ao||{}).forEach(([id,a])=>{if(!a||!a.soc||!["À examiner","En préparation"].includes(a.statut))return;const lim=mphLim(a);
    if(lim.k==="ok"&&lim.t<now){ech.push({id,a,lim});return;}const k=(a.base||id)+"|"+a.soc;if(seen.has(k))return;seen.add(k);L.push({id,a,lim});});
  return{L,ech};}
/* données société manquantes d'un dossier : exactement les cartes de « À compléter / vérifier » (b21d-11) */
function mphInfo(id,a){const base=a.base&&S.ao[a.base]?a.base:id,A=S.ao[base],X={oid:id,sid:a.soc,a};let e;
  try{e=b21dEval(base,A,a.soc,X);}catch(err){return{k:"err",keys:new Map()};}
  if(!e.dc.rcOk)return{k:"inc",keys:new Map()};const K=new Map();
  e.dc.docs.forEach(d=>{if(!(d.kind==="miss"||d.kind==="redac"||d.kind==="ready"))return;d.fields.filter(f=>!f.fait).forEach(f=>K.set("f:"+f.k,f.lab));d.autres.forEach(x=>K.set(x.vk?"v:"+x.vk:"t:"+x.t,x.vk||x.t));});
  e.dc.proofs.filter(z=>z.k!=="joint").forEach(z=>K.set(z.vk?"v:"+z.vk:"p:"+z.std,z.vk||z.piece));
  return{k:"ok",keys:K};}
function mphStep(id,a){let ST=[];try{ST=aoSteps(id,a);}catch(e){}const s=ST.find(x=>x.st!=="fait"&&x.st!=="attente");return s||null;}
function mphCalc(){const ck=mphSig();if(MPH.cache&&MPH.ck===ck)return MPH.cache;
  const now=Date.now(),{L,ech}=mphOuverts(now);L.forEach(x=>{x.info=mphInfo(x.id,x.a);});
  MPH.cache={now,L,ech};MPH.ck=ck;return MPH.cache;}
function mphVuePour(C){const f=x=>!MPH.soc||x.a.soc===MPH.soc,L=C.L.filter(f),ech=C.ech.filter(f);
  const dec=L.filter(x=>x.a.statut==="À examiner"&&(!x.a.decision||x.a.decision.verdict==="À reprendre"));
  const dep=L.filter(x=>x.a.statut==="En préparation");
  const soc=new Map(),inc=[];L.forEach(x=>{if(x.info.k!=="ok"){inc.push(x);return;}if(!x.info.keys.size)return;const o=soc.get(x.a.soc)||{sid:x.a.soc,keys:new Map(),dos:[]};x.info.keys.forEach((v,k)=>o.keys.set(k,v));o.dos.push(x);soc.set(x.a.soc,o);});
  const S2=[...soc.values()].sort((p,q)=>q.keys.size-p.keys.size||socCourt(p.sid).localeCompare(socCourt(q.sid)));
  const nInfo=S2.reduce((n,o)=>n+o.keys.size,0);
  const rank=x=>dec.includes(x)?0:x.info.keys.size?1:2;
  const R=L.slice().sort((p,q)=>(p.lim.k==="ok"?p.lim.t:Infinity)-(q.lim.k==="ok"?q.lim.t:Infinity)||rank(p)-rank(q)||String(p.a.ref).localeCompare(String(q.a.ref)));
  return{L,ech,dec,dep,S2,nInfo,inc,R,rank};}
/* ---- navigation : routes existantes ---- */
function mphOuvrir(id,k){const back={vue:MPN.vue==="prio"?"prio":"dept",svc:null,bur:null,outil:null,trans:null,prev:null};
  MPN.dos=null;if(k&&MPN_ETAPE_BUR[k]){MPN.vue="bur";MPN.bur=MPN_ETAPE_BUR[k];MPN.svc=mpnB(MPN.bur).svc;MPN.ouvert=k==="dec"?"dec":null;}else MPN.vue="dept";
  S.aoId=id;render();if(MPN.dos)MPN.dos.retour=back;window.scrollTo(0,0);mpdFocus("#mpn-h");}
function mphPrio(k){MPH.prio=k;MPN.vue="prio";MPN.prev=null;S.aoId=null;render();window.scrollTo(0,0);mpdFocus("#mpn-h");}
function mphAccueil(){mpnAller({});S.aoId=null;render();window.scrollTo(0,0);mpdFocus("#mpn-h");}
/* action d'une ligne : décision → B2.1 décision ; données manquantes → « À compléter / vérifier » (B2.1) ; sinon étape en cours */
function mphAction(V,x){const st=mphStep(x.id,x.a);
  if(V.dec.includes(x))return{etape:"Décision",cls:"dec",faire:"Décider de la participation",lab:"Examiner",k:"dec"};
  if(x.info.k==="ok"&&x.info.keys.size){const n=x.info.keys.size;return{etape:"Préparation",cls:"prep",faire:"Compléter "+n+" information"+(n>1?"s":"")+" société",lab:"Compléter",k:"dec"};}
  if(st&&st.k==="depot")return{etape:"Dépôt",cls:"dep",faire:"Contrôler et signer",lab:"Ouvrir",k:"depot"};
  if(st&&st.k==="prix")return{etape:"Prix",cls:"prep",faire:"Fixer et valider les prix",lab:"Ouvrir",k:"prix"};
  if(st&&st.k==="pieces")return{etape:"Préparation",cls:"prep",faire:st.res||"Préparer les pièces",lab:"Ouvrir",k:"pieces"};
  return{etape:st?MPN_ETAPE[st.k]||"Dossier":"Dossier",cls:"prep",faire:st?st.res||st.t:"À vérifier dans le dossier",lab:"Ouvrir",k:st?st.k:null};}
/* ---- rendu ---- */
function mphEtat(){if(S.aoState==="ok")return null;if(S.aoState==="err")return{k:"err",t:"Connexion aux dossiers interrompue ("+((S.dbErr||{}).ao||"réseau")+") : chiffres non calculés."};
  if(S.dbState==="absent"&&!S.db)return{k:"err",t:"Base de dossiers indisponible dans cette vue : chiffres non calculés."};return{k:"load",t:"Chargement des dossiers…"};}
function mphHead(){const so=(SOC||[]).filter(z=>z&&z.sid);
  return`<header class="mph-top"><nav class="mph-fil" aria-label="Fil d'Ariane"><ol><li><button type="button" class="mph-lk0" data-mph-deps="1" data-act="${act(()=>go(()=>{S.tab="departements";S.dept=null;S.soc=null;S.aoId=null;S.chId=null;S.form=null;}))}">Départements</button></li><li aria-current="page">Marchés publics</li></ol></nav>
  <div class="mph-srch" role="search"><label class="mph-sr" for="mph-q">Rechercher un AO, un bureau, une société</label>${mphI("search","mph-si")}<input id="mph-q" type="search" data-mph-q="1" autocomplete="off" placeholder="Rechercher un AO, un bureau, une société…" value="${esc(MPH.q)}" aria-describedby="mph-qn"></div></header>
  <div class="mph-hd"><div><h1 class="mph-h1" id="mpn-h" tabindex="-1">Marchés publics</h1><p class="mph-sub">Pilotez vos appels d'offres, de la veille au résultat.</p></div>
  <div class="mph-hr"><button type="button" class="mph-lk" data-mph-equipe="1" data-act="${mpnGo(()=>mpnAller({vue:"trans",trans:"equipe"}))}">${mphI("team")}Équipe numérique</button>
  <label class="mph-sr" for="mph-soc">Filtrer par société</label><select id="mph-soc" class="mph-sel" data-mph-soc="1"><option value="">Toutes les sociétés</option>${so.map(z=>`<option value="${esc(z.sid)}"${MPH.soc===z.sid?" selected":""}>${esc(z.court||z.sid)}</option>`).join("")}</select></div></div>`;}
function mphRecherche(){const q=MPH.q.trim().toLowerCase();if(q.length<2)return`<p class="mph-sr" id="mph-qn" aria-live="polite"></p>`;
  const has=t=>String(t||"").toLowerCase().includes(q);
  const D=Object.entries(S.ao||{}).filter(([id,a])=>a&&(!MPH.soc||a.soc===MPH.soc)&&(has(a.ref)||has(a.obj)||has(a.mo)||has(socCourt(a.soc)))).sort((x,y)=>["À examiner","En préparation"].includes(y[1].statut)-["À examiner","En préparation"].includes(x[1].statut)).slice(0,6);
  const B=MPD_BUR.filter(b=>has(b.code)||has(b.nom)||has(MPH_BDESC[b.id])),So=(SOC||[]).filter(z=>has(z.court)||has(z.sid)||has(z.raison)).slice(0,6),n=D.length+B.length+So.length;
  let h=`<section class="mph-res" aria-labelledby="mph-rt"><h2 id="mph-rt" class="mph-rt">Résultats pour « ${esc(MPH.q.trim())} »</h2><p class="mph-sr" id="mph-qn" aria-live="polite">${n} résultat${n>1?"s":""}</p>`;
  if(!n)return h+`<p class="mph-vide">Aucun AO, bureau ni société ne correspond${MPH.soc?" (filtre société actif)":""}.</p></section>`;
  if(D.length)h+=`<h3>AO</h3><ul>${D.map(([id,a])=>`<li><button type="button" data-mph-rao="${esc(id)}" data-act="${act(()=>mphOuvrir(id,null))}"><b>AO ${esc(a.ref||"")}</b><span>${esc(a.obj||"")}</span><small>${esc(socCourt(a.soc))} · ${esc(a.statut||"")}</small></button></li>`).join("")}</ul>`;
  if(B.length)h+=`<h3>Bureaux</h3><ul>${B.map(b=>`<li><button type="button" data-mph-rbur="${b.id}" data-act="${mpnGo(()=>mpnBureau(b.id))}"><b>${esc(b.code)} · ${esc(b.nom)}</b><span>${esc(MPH_BDESC[b.id]||"")}</span></button></li>`).join("")}</ul>`;
  if(So.length)h+=`<h3>Sociétés</h3><ul>${So.map(z=>`<li><button type="button" data-mph-rsoc="${esc(z.sid)}" data-act="${act(()=>{MPH.soc=z.sid;MPH.q="";render();mpdFocus("#mph-soc");})}"><b>${esc(z.court||z.sid)}</b><span>Filtrer l'accueil sur cette société</span></button></li>`).join("")}</ul>`;
  return h+`</section>`;}
function mphCartes(V,E){const card=(k,ico,tone,n,lab,sub,cta,extra)=>`<article class="mph-pc" data-mph-card="${k}" data-mph-n="${n==null?"":n}"><span class="mph-pci mph-${tone}">${mphI(ico)}</span><div class="mph-pcb"><p class="mph-pn">${n==null?"—":n}</p><p class="mph-pl">${esc(lab)}</p><p class="mph-ps">${sub}</p>${extra||""}</div>${cta||""}</article>`;
  if(E)return`<div class="mph-pcs">${["Décisions à prendre","Informations société manquantes","Dépôts à finaliser"].map((l,i)=>card(["dec","info","depot"][i],["doc","doc","up"][i],i?"am":"ro",null,l,esc(E.t),E.k==="err"&&typeof aoReload==="function"?`<button type="button" class="mph-cta" data-act="${act(aoReload)}">Recharger</button>`:"")).join("")}</div>`;
  const cta=(k,l,n)=>`<button type="button" class="mph-cta" data-mph-go="${k}" data-act="${act(()=>mphPrio(k))}">${l}<span class="mph-sr"> : ${n} ${k==="info"?"données":"dossiers"}</span>${mphI("arrow","mph-ai")}</button>`;
  const nI=V.nInfo,inc=V.inc.length,ns=V.S2.length;
  return`<div class="mph-pcs">${card("dec","doc","ro",V.dec.length,V.dec.length>1?"Décisions à prendre":"Décision à prendre",V.dec.length?"Dossiers ouverts sans décision enregistrée":"Aucun dossier ouvert en attente de décision",cta("dec","Examiner",V.dec.length))}
  ${card("info","doc","am",nI,nI>1?"Informations société manquantes":"Information société manquante",(nI?"Données uniques à compléter ou vérifier, "+ns+" société"+(ns>1?"s":""):inc?"Aucun manque identifié dans les dossiers évalués":"Aucun manque identifié")+(inc?` · <span class="mph-av" data-mph-inc="${inc}">? ${inc} dossier${inc>1?"s":""} non évalué${inc>1?"s":""} (RC non relevé)</span>`:""),cta("info","Compléter",nI))}
  ${card("depot","up","am",V.dep.length,V.dep.length>1?"Dépôts à finaliser":"Dépôt à finaliser",(V.dep.length?"Participation décidée, offre pas encore déposée":"Aucune offre en préparation dans les délais")+(V.ech.filter(x=>x.a.statut==="En préparation").length?` · <span class="mph-av" data-mph-ech="1">${V.ech.filter(x=>x.a.statut==="En préparation").length} échu${V.ech.filter(x=>x.a.statut==="En préparation").length>1?"s":""} sans dépôt (hors compteur)</span>`:""),cta("depot","Préparer",V.dep.length))}</div>`;}
function mphDate(x,now){const r=mphRel(x.lim,now);return`<span class="mph-dl${r.u?" mph-urg":""}">${esc(r.t)}</span><small>${esc(mphDateTxt(x.lim))}</small>`;}
function mphTable(V,rows,now,cap){if(!rows.length)return`<p class="mph-vide" data-mph-vide="1">Aucun dossier ouvert${MPH.soc?" pour "+esc(socCourt(MPH.soc)):""} : rien d'urgent à traiter. Les dossiers déposés ou clôturés restent dans « Mes dossiers ».</p>`;
  return`<div class="mph-tw"><table class="mph-t"><caption class="mph-sr">${esc(cap)}</caption><colgroup><col><col class="c-soc"><col class="c-et"><col class="c-af"><col class="c-dl"><col class="c-ac"></colgroup><thead><tr><th scope="col">Dossier</th><th scope="col">Société</th><th scope="col">Étape</th><th scope="col">À faire</th><th scope="col">Date limite</th><th scope="col"><span class="mph-sr">Action</span><span aria-hidden="true">Action</span></th></tr></thead><tbody>${rows.map(x=>{const A=mphAction(V,x);
    return`<tr data-mph-row="${esc(x.id)}"><td data-l="Dossier"><div><b>AO ${esc(x.a.ref||"")}</b><small class="mph-obj" title="${esc(x.a.obj||"")}">${esc(x.a.obj||"Objet non renseigné")}</small></div></td><td data-l="Société"><div>${esc(socCourt(x.a.soc))}</div></td><td data-l="Étape"><div><span class="mph-et mph-et-${A.cls}"><i aria-hidden="true"></i>${esc(A.etape)}</span></div></td><td data-l="À faire"><div>${esc(A.faire)}${x.info.k==="inc"?`<small class="mph-av">? Exigences du RC non relevées</small>`:""}</div></td><td data-l="Date limite"><div>${mphDate(x,now)}</div></td>
    <td data-l="Action"><button type="button" class="mph-act" data-mph-open="${esc(x.id)}" data-mph-k="${esc(A.k||"")}" data-act="${act(()=>mphOuvrir(x.id,A.k))}">${esc(A.lab)}<span class="mph-sr"> AO ${esc(x.a.ref||"")}, ${esc(socCourt(x.a.soc))}</span>${mphI("arrow","mph-ai")}</button></td></tr>`;}).join("")}</tbody></table></div>`;}
function mphServices(){const s=MPD_SVC.find(x=>x.id===MPH.svc)||MPD_SVC[1],B=MPD_BUR.filter(b=>b.svc===s.id);
  return`<section class="mph-sec" aria-labelledby="mph-st"><div class="mph-sh"><h2 id="mph-st">Services et bureaux</h2><span class="mph-mut">${MPD_SVC.length} services · ${MPD_BUR.length} bureaux</span></div>
  <div class="mph-tabs" role="tablist" aria-label="Services du département">${MPD_SVC.map(x=>`<button type="button" role="tab" id="mph-tab-${x.code}" aria-selected="${x.id===s.id}" aria-controls="mph-tp" tabindex="${x.id===s.id?0:-1}" data-mph-svc="${x.id}" data-act="${act(()=>{MPH.svc=x.id;render();mpdFocus('[data-mph-svc="'+x.id+'"]');})}">${mphI(MPH_SICO[x.id])}<span><b>${esc(x.code)}</b><small>${esc(MPH_SVC[x.id])}</small></span></button>`).join("")}</div>
  <div class="mph-tp" id="mph-tp" role="tabpanel" aria-labelledby="mph-tab-${s.code}"><h3>${esc(s.code)} · ${esc(MPH_SVC[s.id])}</h3><p class="mph-mut">${esc(MPH_SBUT[s.id])}</p>
  <div class="mph-bg">${B.map(b=>`<button type="button" class="mph-bc" data-mph-bur="${b.id}" data-act="${mpnGo(()=>mpnBureau(b.id))}"><span class="mph-bci">${mphI(MPH_BICO[b.id])}</span><span class="mph-bct"><b><span class="mph-code">${esc(b.code)}</span>${esc(b.nom)}</b><small>${esc(MPH_BDESC[b.id]||"")}</small></span><span class="mph-chev" aria-hidden="true">›</span></button>`).join("")}</div></div></section>`;}
function mphAcces(){const L=[["dossiers","Mes dossiers","folder",()=>mpnAller({vue:"trans",trans:"dossiers"})],["agenda","Agenda","cal",()=>mpnAller({vue:"trans",trans:"agenda"})],["textes","Textes & règles","doc",()=>mpnAller({vue:"trans",trans:"textes"})],["equipe","Équipe numérique","team",()=>mpnAller({vue:"trans",trans:"equipe"})]];
  return`<nav class="mph-qa" aria-labelledby="mph-qt"><h2 id="mph-qt">Accès rapides</h2><ul>${L.slice(0,2).map(([k,l,i,f])=>`<li><button type="button" data-mph-acces="${k}" data-act="${mpnGo(f)}">${mphI(i)}${esc(l)}</button></li>`).join("")}<li><button type="button" data-mph-acces="coffre" data-dept="coffre">${mphI("lock")}Coffre des sociétés</button></li>${L.slice(2).map(([k,l,i,f])=>`<li><button type="button" data-mph-acces="${k}" data-act="${mpnGo(f)}">${mphI(i)}${esc(l)}</button></li>`).join("")}</ul></nav>`;}
function mphHome(){const E=mphEtat(),now=Date.now();let V=null;if(!E){try{V=mphVuePour(mphCalc());}catch(e){console.error(e);}}
  const E2=E||(V?null:{k:"err",t:"Calcul impossible pour le moment : chiffres non affichés."});
  let h=mphHead()+mphRecherche();
  h+=`<section class="mph-sec" aria-labelledby="mph-pt"><div class="mph-sh"><h2 id="mph-pt">Vos priorités</h2>${MPH.soc?`<span class="mph-mut" data-mph-filtre="${esc(MPH.soc)}">Filtre : ${esc(socCourt(MPH.soc))}</span>`:""}</div>${mphCartes(V,E2)}</section>`;
  h+=`<section class="mph-sec" aria-labelledby="mph-dt"><div class="mph-sh"><h2 id="mph-dt">Dossiers prioritaires</h2>${V&&V.R.length?`<button type="button" class="mph-lk" data-mph-tous="1" data-act="${act(()=>mphPrio("tous"))}">Voir tous les dossiers (${V.R.length})${mphI("arrow","mph-ai")}</button>`:""}</div>${E2?`<p class="mph-vide" data-mph-etat="${E2.k}">${esc(E2.t)}</p>`:mphTable(V,V.R.slice(0,5),now,"Dossiers prioritaires, échéance la plus proche d'abord")}</section>`;
  h+=mphServices()+mphAcces();
  return`<div class="mph" data-mph="${MPH.v}">${h}</div>`;}
function mphListe(){const E=mphEtat(),now=Date.now(),k=MPH.prio;let V=null;if(!E){try{V=mphVuePour(mphCalc());}catch(e){}}
  const T={dec:"Décisions à prendre",info:"Informations société manquantes",depot:"Dépôts à finaliser",tous:"Tous les dossiers ouverts"}[k]||"Dossiers";
  let h=`<p class="mph-back"><button type="button" class="smallbtn" data-mph-retour="1" data-act="${act(mphAccueil)}">← Marchés publics</button></p><div class="mph-hd"><div><h1 class="mph-h1" id="mpn-h" tabindex="-1">${esc(T)}</h1><p class="mph-sub">${MPH.soc?"Société : "+esc(socCourt(MPH.soc))+" · ":""}${k==="info"?"Données uniques par société (une donnée commune à plusieurs pièces ou dossiers compte une fois).":"Dossiers ouverts, échéance la plus proche d'abord."}</p></div></div>`;
  if(E||!V)return`<div class="mph" data-mph-liste="${esc(k)}">${h}<p class="mph-vide">${esc((E||{t:"Calcul impossible."}).t)}</p></div>`;
  if(k==="info"){h+=`<p class="mph-cnt" data-mph-lc="${V.nInfo}">${V.nInfo} donnée${V.nInfo>1?"s":""} · ${V.S2.length} société${V.S2.length>1?"s":""}</p>`;
    if(!V.S2.length)h+=`<p class="mph-vide" data-mph-vide="1">Aucune donnée société manquante identifiée dans les dossiers ouverts évalués.</p>`;
    h+=V.S2.map(o=>{const d0=o.dos.slice().sort((p,q)=>(p.lim.k==="ok"?p.lim.t:Infinity)-(q.lim.k==="ok"?q.lim.t:Infinity))[0];
      return`<article class="mph-lc" data-mph-lsoc="${esc(o.sid)}" data-mph-ln="${o.keys.size}"><div><h2>${esc(socCourt(o.sid))} <span class="mph-pill mph-am">✎ ${o.keys.size} donnée${o.keys.size>1?"s":""}</span></h2><p class="mph-mut">${[...o.keys.values()].map(esc).join(" · ")}</p><p class="mph-mut">Dossiers concernés : ${o.dos.map(x=>"AO "+esc(x.a.ref||"")).join(", ")}</p></div>
      <button type="button" class="mph-act" data-mph-open="${esc(d0.id)}" data-mph-k="dec" data-act="${act(()=>mphOuvrir(d0.id,"dec"))}">Compléter<span class="mph-sr"> pour ${esc(socCourt(o.sid))} (AO ${esc(d0.a.ref||"")})</span>${mphI("arrow","mph-ai")}</button></article>`;}).join("");
    if(V.inc.length)h+=`<section class="mph-inc" data-mph-linc="${V.inc.length}"><h2>? Non évalués (hors compteur)</h2><p class="mph-mut">Exigences du RC non relevées : impossible de dire ce qui manque, rien n'est supposé complet.</p>${mphTable(V,V.inc,now,"Dossiers non évalués")}</section>`;
    return`<div class="mph" data-mph-liste="info">${h}</div>`;}
  const rows=k==="dec"?V.R.filter(x=>V.dec.includes(x)):k==="depot"?V.R.filter(x=>V.dep.includes(x)):V.R;
  h+=`<p class="mph-cnt" data-mph-lc="${rows.length}">${rows.length} dossier${rows.length>1?"s":""}</p>`+mphTable(V,rows,now,T);
  if(k==="depot"){const e=V.ech.filter(x=>x.a.statut==="En préparation");if(e.length)h+=`<section class="mph-inc" data-mph-lech="${e.length}"><h2>Échus sans dépôt (hors compteur)</h2><p class="mph-mut">Date limite dépassée : consultation en lecture seule, aucune nouvelle soumission.</p><ul>${e.map(x=>`<li>AO ${esc(x.a.ref||"")} · ${esc(socCourt(x.a.soc))} · ${esc(mphDateTxt(x.lim))}</li>`).join("")}</ul></section>`;}
  return`<div class="mph" data-mph-liste="${esc(k)}">${h}</div>`;}
/* intégration : l'accueil (vue « dept ») et les listes (vue « prio ») ; tout le reste (services, bureaux, outils, dossiers) inchangé */
(()=>{const v0=vMP;vMP=function(){if(S.aoId)return v0();
  if(MPN.last!=="ao"&&!MPN.viaMenu){mpnAller({});MPN.sideOuvert=null;MPN.dos=null;}MPN.viaMenu=false;
  if(MPN.dos)mpnFermeDossier();
  if(MPN.demande!=null){const k=MPN.demande;MPN.demande=null;mpnDemande(k);}
  mphCss();if(MPN.vue==="dept")return mphHome();if(MPN.vue==="prio"&&MPH.prio)return mphListe();if(MPN.vue==="prio")mpnAller({});
  if(MPN.vue==="dept")return mphHome();MPN.viaMenu=true;return v0();};})();
/* barre latérale : « Départements » marqué comme rubrique parente quand on est dans Marchés publics (aucune autre modification du shell) */
(()=>{const s0=sideHtml;sideHtml=function(){const h=s0();return S.dept==="ao"&&!S.soc?h.replace('data-side-tab="departements">','data-side-tab="departements" aria-current="true" class="mph-anc">'):h;};})();
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.mphQ){MPH.q=t.value;render();}});
document.getElementById("view").addEventListener("change",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.mphSoc!=null){MPH.soc=t.value;render();mpdFocus("#mph-soc");}});
document.getElementById("view").addEventListener("keydown",e=>{const t=e.target;if(!t||!t.dataset)return;
  if(t.dataset.mphQ&&e.key==="Escape"&&MPH.q){MPH.q="";render();mpdFocus("#mph-q");return;}
  if(t.dataset.mphSvc&&["ArrowRight","ArrowLeft","Home","End"].includes(e.key)){e.preventDefault();const i=MPD_SVC.findIndex(x=>x.id===t.dataset.mphSvc),n=MPD_SVC.length,j=e.key==="Home"?0:e.key==="End"?n-1:(i+(e.key==="ArrowRight"?1:-1)+n)%n;MPH.svc=MPD_SVC[j].id;render();mpdFocus('[data-mph-svc="'+MPH.svc+'"]');}});
const MPH_TOK=`--mph-card:var(--surface,#18212D);--mph-line:var(--line,#2B3542);--mph-ink:var(--ink,#E6E8EA);--mph-mut:var(--muted,#9BA4AF);--mph-or:#E3B26A;--mph-or2:#F0C88A;--mph-orb:rgba(227,178,106,.14);--mph-ro:#F09A8C;--mph-rob:rgba(240,154,140,.14);--mph-neu:rgba(255,255,255,.08);--mph-neui:#C9D1DA;--mph-tab:rgba(227,178,106,.1)`;
const MPH_CSS=`.mph{--mph-card:#FFFFFF;--mph-line:#E8E1D5;--mph-ink:var(--ink,#16171A);--mph-mut:var(--muted,#6B6E75);--mph-or:#B07A2A;--mph-or2:#8A5A14;--mph-orb:#FBF0E1;--mph-ro:#B4412F;--mph-rob:#FCE9E5;--mph-neu:#EEF1F4;--mph-neui:#465161;--mph-tab:#FFFDF8;
  color:var(--mph-ink);display:flex;flex-direction:column;gap:22px;container:mph/inline-size;min-width:0;font-size:14px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .mph{${MPH_TOK}}}:root[data-theme="dark"] .mph{${MPH_TOK}}
.mph *{box-sizing:border-box}.mph-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.mph-i{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;flex:0 0 auto}.mph-ai{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.mph-si{position:absolute;left:12px;top:50%;transform:translateY(-50%);width:18px;height:18px;fill:none;stroke:var(--mph-mut);stroke-width:1.8}
.mph button{font-family:inherit}
.mph-top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 20px}.mph-fil ol{list-style:none;margin:0;padding:0;display:flex;gap:8px;font-size:13px;color:var(--mph-mut)}.mph-fil li+li::before{content:"/";margin-right:8px;color:var(--mph-mut)}.mph-fil [aria-current]{color:var(--mph-ink);font-weight:600}
.mph-lk0{border:0;background:none;padding:0;color:var(--mph-mut);cursor:pointer;font-size:13px}.mph-lk0:hover{color:var(--mph-or)}
.mph-srch{position:relative;flex:0 1 520px;min-width:0;width:100%}.mph-srch input{width:100%;border:1px solid var(--mph-line);background:var(--mph-card);color:var(--mph-ink);border-radius:8px;padding:10px 12px 10px 38px;font-size:14px;font-family:inherit}
.mph-hd{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px 20px}.mph-h1{margin:0;font-family:var(--display,inherit);font-size:34px;line-height:1.1;font-weight:600;outline:none;color:var(--mph-ink)}.mph-sub{margin:4px 0 0;color:var(--mph-mut);font-size:15px}
.mph-hr{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px}.mph-lk{display:inline-flex;align-items:center;gap:6px;border:0;background:none;padding:2px 0;color:var(--mph-or);font-weight:600;font-size:14px;cursor:pointer;text-decoration:underline;text-underline-offset:3px}
.mph-sel{border:1px solid var(--mph-line);background:var(--mph-card);color:var(--mph-ink);border-radius:8px;padding:9px 12px;font-size:14px;font-family:inherit;min-width:200px;max-width:100%}
.mph-sec{display:flex;flex-direction:column;gap:12px}.mph-sh{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 14px}.mph-sh h2,.mph-qa h2{margin:0;font-size:20px;font-weight:700;padding-left:12px;border-left:3px solid var(--mph-or);line-height:1.2;color:var(--mph-ink)}.mph-mut{color:var(--mph-mut);font-size:13px;margin:0}
.mph-pcs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.mph-pc{display:grid;grid-template-columns:auto minmax(0,1fr);gap:4px 14px;align-items:start;background:var(--mph-card);border:1px solid var(--mph-line);border-radius:10px;padding:16px}
.mph-pci{width:52px;height:52px;border-radius:50%;display:grid;place-items:center;grid-row:span 2}.mph-pci .mph-i{width:24px;height:24px}.mph-ro{background:var(--mph-rob);color:var(--mph-ro)}.mph-am{background:var(--mph-orb);color:var(--mph-or)}
.mph-pn{margin:0;font-size:30px;font-weight:700;line-height:1}.mph-pl{margin:4px 0 0;font-weight:600}.mph-ps{margin:2px 0 0;font-size:12.5px;color:var(--mph-mut)}.mph-av{color:var(--mph-or2);font-weight:600}
.mph-cta{grid-column:2;justify-self:end;display:inline-flex;align-items:center;gap:6px;border:0;background:none;color:var(--mph-or);font-weight:600;font-size:14px;cursor:pointer;text-decoration:underline;text-underline-offset:3px;padding:4px 0}
.mph-sh h2,.mph-qa h2,.mph-tp h3,.mph-lc h2,.mph-inc h2,.mph-rt{text-transform:none;letter-spacing:normal;font-family:inherit}.mph-t td small.mph-obj{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.mph-t col.c-soc{width:13%}.mph-t col.c-et{width:12%}.mph-t col.c-af{width:19%}.mph-t col.c-dl{width:14%}.mph-t col.c-ac{width:150px}
.mph-tw{background:var(--mph-card);border:1px solid var(--mph-line);border-radius:10px;overflow:hidden}.mph-t{width:100%;border-collapse:collapse}.mph-t th{text-align:left;font-weight:500;font-size:13px;color:var(--mph-mut);padding:10px 14px;border-bottom:1px solid var(--mph-line);background:var(--mph-tab)}
.mph-t td{padding:10px 14px;border-top:1px solid var(--mph-line);vertical-align:middle;font-size:13.5px}.mph-t tr:first-child td{border-top:0}.mph-t td small{display:block;color:var(--mph-mut);font-size:12px;margin-top:2px}.mph-t td b{font-weight:600}
.mph-et{display:inline-flex;align-items:center;gap:7px;border-radius:6px;padding:5px 10px;font-size:13px;white-space:nowrap}.mph-et i{width:8px;height:8px;border-radius:50%;background:currentColor}.mph-et-dec{background:var(--mph-orb);color:var(--mph-or2)}.mph-et-prep,.mph-et-dep{background:var(--mph-neu);color:var(--mph-neui)}
.mph-dl{display:block;font-weight:500}.mph-urg{color:var(--mph-ro);font-weight:600}
.mph-act{display:inline-flex;align-items:center;justify-content:space-between;gap:10px;min-width:118px;border:1px solid var(--mph-or);background:var(--mph-card);color:var(--mph-or2);border-radius:6px;padding:8px 14px;font-weight:600;font-size:13.5px;cursor:pointer}.mph-act:hover{background:var(--mph-orb)}
.mph-vide{margin:0;background:var(--mph-card);border:1px dashed var(--mph-line);border-radius:10px;padding:14px;color:var(--mph-mut)}
.mph-tabs{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}.mph-tabs [role=tab]{display:flex;align-items:center;gap:10px;text-align:left;border:1px solid var(--mph-line);background:var(--mph-card);color:var(--mph-ink);border-radius:8px;padding:12px;cursor:pointer;min-width:0}
.mph-tabs [role=tab] .mph-i{width:24px;height:24px}.mph-tabs [role=tab] span{display:flex;flex-direction:column;min-width:0}.mph-tabs b{font-size:15px}.mph-tabs small{font-size:12.5px;color:var(--mph-mut);overflow-wrap:anywhere}
.mph-tabs [aria-selected=true]{border:2px solid var(--mph-or);background:var(--mph-tab);box-shadow:0 2px 0 var(--mph-or)}.mph-tabs [aria-selected=true] b,.mph-tabs [aria-selected=true] .mph-i{color:var(--mph-or)}.mph-tabs [aria-selected=true] small{color:var(--mph-ink)}
.mph-tp{background:var(--mph-card);border:1px solid var(--mph-line);border-radius:10px;padding:16px}.mph-tp h3{margin:0;font-size:18px;padding-left:12px;border-left:3px solid var(--mph-or)}.mph-tp>.mph-mut{margin:4px 0 12px 15px}
.mph-bg{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.mph-bc{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;text-align:left;border:1px solid var(--mph-line);background:var(--mph-card);color:var(--mph-ink);border-radius:8px;padding:12px 14px;cursor:pointer}.mph-bc:hover{border-color:var(--mph-or)}
.mph-bci{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;background:var(--mph-orb);color:var(--mph-or)}.mph-bci .mph-i{width:22px;height:22px}.mph-bct{display:flex;flex-direction:column;min-width:0}.mph-bct b{font-size:15px;font-weight:600}.mph-bct small{font-size:13px;color:var(--mph-mut)}.mph-code{margin-right:8px}.mph-chev{font-size:22px;color:var(--mph-ink)}
.mph-qa{display:flex;flex-wrap:wrap;align-items:center;gap:10px 24px;background:var(--mph-card);border:1px solid var(--mph-line);border-radius:10px;padding:12px 16px}.mph-qa ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px 22px;flex:1 1 auto;justify-content:space-between}
.mph-qa li button{display:inline-flex;align-items:center;gap:8px;border:0;background:none;color:var(--mph-ink);font-size:14px;cursor:pointer;padding:6px 2px}.mph-qa li button .mph-i{color:var(--mph-or);width:22px;height:22px}.mph-qa li button:hover{color:var(--mph-or)}
.mph-res{background:var(--mph-card);border:1px solid var(--mph-line);border-radius:10px;padding:12px 16px}.mph-rt{margin:0 0 6px;font-size:15px}.mph-res h3{margin:8px 0 4px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mph-mut)}.mph-res ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
.mph-res li button{width:100%;display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;text-align:left;border:0;background:none;color:var(--mph-ink);padding:7px 8px;border-radius:6px;cursor:pointer}.mph-res li button:hover,.mph-res li button:focus-visible{background:var(--mph-orb)}.mph-res span{color:var(--mph-mut);font-size:13px}.mph-res small{color:var(--mph-mut);font-size:12px}
.mph-back{margin:0}.mph-cnt{margin:0;font-weight:600}.mph-lc{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px 16px;background:var(--mph-card);border:1px solid var(--mph-line);border-radius:10px;padding:14px 16px}.mph-lc h2{margin:0;font-size:16px}.mph-lc>div{flex:1 1 300px;min-width:0}.mph-lc .mph-mut{margin-top:4px}
.mph-pill{display:inline-block;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:600}.mph-inc{display:flex;flex-direction:column;gap:8px}.mph-inc h2{margin:0;font-size:16px;color:var(--mph-or2)}
.mph :focus-visible{outline:2px solid var(--mph-or);outline-offset:2px}
#side .mph-anc{box-shadow:inset 3px 0 0 var(--ea-or,#C3A06A)}
@container mph (max-width:900px){.mph-tabs{grid-template-columns:repeat(3,minmax(0,1fr))}}
@container mph (max-width:820px){.mph-pcs{grid-template-columns:minmax(0,1fr)}.mph-pc{grid-template-columns:auto minmax(0,1fr) auto;align-items:center}.mph-pci{grid-row:auto;width:46px;height:46px}.mph-cta{grid-column:3}
  .mph-t thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.mph-t,.mph-t tbody,.mph-t tr,.mph-t td{display:block;width:100%}.mph-t tr{padding:10px 14px;border-top:1px solid var(--mph-line)}.mph-t tr:first-child{border-top:0}
  .mph-t td{border:0;padding:3px 0;display:grid;grid-template-columns:96px minmax(0,1fr);gap:8px}.mph-t td::before{content:attr(data-l);color:var(--mph-mut);font-size:12px}.mph-t td>div{min-width:0}.mph-t td small.mph-obj{-webkit-line-clamp:2}.mph-t td[data-l=Action]{grid-template-columns:minmax(0,1fr);padding-top:8px}.mph-t td[data-l=Action]::before{display:none}.mph-act{width:100%}}
@container mph (max-width:620px){.mph-bg{grid-template-columns:minmax(0,1fr)}.mph-tabs{grid-template-columns:repeat(2,minmax(0,1fr))}.mph-h1{font-size:28px}.mph-sel{min-width:0;width:100%}.mph-hr{width:100%}.mph-pc{grid-template-columns:auto minmax(0,1fr)}.mph-cta{grid-column:1 / -1;justify-self:start}.mph-qa ul{justify-content:flex-start}}`;
function mphCss(){if(document.getElementById("mph-css"))return;const s=document.createElement("style");s.id="mph-css";s.textContent=MPH_CSS;document.head.appendChild(s);}
