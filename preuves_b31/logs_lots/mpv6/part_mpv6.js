/* ===================== mpv-6 · B1.1 : « Mes consultations suivies » et « DCE à récupérer » (suivi au niveau du GROUPE) =====================
   Règle métier : on suit une consultation pour le groupe ; aucune société n'est choisie avant l'étape Décision (B2.1).
   - Une consultation suivie = l'identifiant officiel PMMP (organisme + numéro), regroupant tous ses dossiers (dossier de base et
     dossiers séparés déjà créés par société) ; jamais la référence seule.
   - Nouveau suivi : dossier « À examiner » SANS société (champ suivi.niveau = "groupe") ; ancien comportement « ALWAAD par défaut » retiré.
     Les dossiers existants ne sont ni réécrits ni migrés : leurs sociétés, choix et décisions restent tels quels ; une société posée
     d'office par l'ancien suivi (dossier de base, aucune décision, note « Société proposée par défaut ») n'est plus présélectionnée.
   - Choix des sociétés : uniquement à l'étape Décision (création du dossier séparé de la société à la confirmation, flux existant).
   - DCE : « reçu » seulement avec des fichiers réellement joints au dossier ; une demande interne n'est jamais un DCE reçu ;
     inventaire PMMP affiché seulement s'il a été réellement lu (sinon inconnu). Aucun téléchargement ni formulaire externe. */
MPV.v="mpv-6";
const MPV6={ss:{q:"",etat:"tout",dce:"",sort:"lim",page:1,sel:null,mob:"list"},ds:{q:"",f:"tout",sort:"lim",page:1,sel:null,mob:"list",ech:false},tq:0,all:[],by:new Map()};
/* société posée d'office par l'ancien suivi : pas un choix (dossier de base, aucune décision) */
function mpv6SocAuto(a){return!!(a&&a.soc&&!a.base&&a.veille&&!a.decision&&!(a.decisionHist||[]).length&&/Société proposée par défaut/.test(String(a.note||"")));}
function mpv6SocDossier(a){return a&&!mpv6SocAuto(a)?a.soc||null:null;}
const mpv6Px=p=>({r:String(p.ref),o:String(p.org||"")});
/* dossiers d'une même consultation : dossier de base d'abord */
mpvDosMap=function(){const m={};Object.entries(S.ao||{}).forEach(([id,a])=>{if(a&&a.portail&&a.portail.ref){const k=a.portail.ref+"/"+(a.portail.org||"");(m[k]=m[k]||[]).push(id);}});
  Object.values(m).forEach(L=>L.sort((x,y)=>(!!S.ao[x].base-!!S.ao[y].base)||(x.indexOf("~")>=0)-(y.indexOf("~")>=0)||x.localeCompare(y)));return m;};
function mpv6B(){if(!S.cat)return null;try{return mpvBase();}catch(e){return null;}}
function mpv6Groups(now){const B=mpv6B(),G=new Map();
  Object.entries(S.ao||{}).forEach(([id,a])=>{if(!a||!(a.portail||a.veille))return;const p=a.portail&&a.portail.ref?a.portail:null,k=p?"p:"+(p.org||"")+":"+p.ref:"b:"+(a.base||id);const g=G.get(k)||{k,ids:[]};g.ids.push(id);G.set(k,g);});
  const L=[];G.forEach(g=>{g.ids.sort((x,y)=>(!!S.ao[x].base-!!S.ao[y].base)||(x.indexOf("~")>=0)-(y.indexOf("~")>=0)||x.localeCompare(y));g.id=g.ids[0];const a=g.a=S.ao[g.id],p=a.portail;
    g.px=p&&p.ref?mpv6Px(p):null;g.x=g.px&&B?(B.by.get(g.px.o+":"+g.px.r)||{}).x||null:null;   /* B.by : entrée {x,sc,k} du catalogue */
    const lim=g.x?g.x.lim:a.lim,h=g.x?g.x.h:mpvH(a.heure);g.limS=lim||"";g.h=h||"";g.lim=limEtat({lim,h},now);g.ouv=!g.lim.passe;
    g.actif=g.ids.some(id=>["À examiner","En préparation"].includes((S.ao[id]||{}).statut));g.dce=mpvDce(g.ids);g.nDec=g.ids.filter(id=>(S.ao[id]||{}).decision).length;
    g.ref=(g.x&&g.x.ref)||a.ref||g.id;g.obj=(g.x&&g.x.obj)||a.obj||"";g.mo=String((g.x&&g.x.mo)||a.mo||"").replace(/\s+/g," ").trim();
    g.cree=String((a.suivi&&a.suivi.le)||(a.veille&&a.veille.detecte_le)||a.cree||"");L.push(g);});
  MPV6.all=L;MPV6.by=new Map(L.map(g=>[g.k,g]));return L;}
const mpv6T=g=>g.lim.inst!=null?g.lim.inst:g.limS?Date.parse(g.limS+"T23:59:00Z"):Infinity;
/* file « DCE à récupérer » : consultation ouverte, au moins un dossier actif, DCE non reçu ; le reste (échues, sans suite) hors compteur */
mpvDceGroupes=function(now){const L=mpv6Groups(now),N=L.filter(g=>g.dce.k!=="pret"),O=N.filter(g=>g.ouv&&g.actif).sort((p,q)=>mpv6T(p)-mpv6T(q)),E=N.filter(g=>!(g.ouv&&g.actif)).sort((p,q)=>mpv6T(q)-mpv6T(p));
  MPV.nSuiv6=L.length;return{O,E,L};};
function mpv6Date(g){if(!g.limS)return{d:"Date limite inconnue",r:"À vérifier sur PMMP",u:false};const ds=fmtIso(g.limS)+(g.h?" · "+g.h:" · heure non précisée");
  if(g.lim.passe)return{d:ds,r:"Clôturée",u:false,c:true};const now=Date.now();
  if(g.h&&g.lim.inst!=null&&g.lim.inst-now<48*36e5){const n=Math.max(1,Math.ceil((g.lim.inst-now)/36e5));return{d:ds,r:n<=1?"Dans moins d'1 h":"Dans "+n+" h",u:true};}
  const d=g.lim.d;return{d:ds,r:d===0?"Aujourd'hui":d===1?"Demain":d==null?"":"Dans "+d+" jours",u:d!=null&&d<=1};}
const mpv6Etat=g=>g.ouv?`<span class="mpv6-etat ouv" data-mpv6-etat="ouv">Ouverte</span>`:`<span class="mpv6-etat clos" data-mpv6-etat="clos">Clôturée</span>`;
const MPV6_DF={afaire:"afaire",echec:"afaire",nd:"afaire",encours:"dem",envoi:"dem",pret:"recu",partiel:"recu"};
function mpv6Q(g,q){const Q=mpvTk(q||"");if(!Q.length)return true;const T=[...mpvTk(g.ref),...mpvTk(g.obj),...mpvTk(g.mo)],raw=String(q).trim();
  if(/[\/\-]/.test(raw)&&/\d/.test(raw))return mpvSeq(mpvTk(g.ref),Q);return Q.every(w=>/^\d+$/.test(w)?T.includes(w):T.some(t=>t.startsWith(w)));}
function mpv6Sort(L,k){const A=L.filter(g=>g.ouv),C=L.filter(g=>!g.ouv);
  if(k==="rec")return L.slice().sort((p,q)=>q.cree.localeCompare(p.cree)||mpv6T(p)-mpv6T(q));
  if(k==="limd")return[...A.sort((p,q)=>mpv6T(q)-mpv6T(p)),...C.sort((p,q)=>mpv6T(p)-mpv6T(q))];
  return[...A.sort((p,q)=>mpv6T(p)-mpv6T(q)),...C.sort((p,q)=>mpv6T(q)-mpv6T(p))];}
function mpv6Sel(s,k){MPV6[s].sel=k;MPV6[s].mob="panel";MPV.conf=null;render();const l=document.querySelector(".mpv-lst"),nar=l&&getComputedStyle(l).display==="none";mpdFocus(nar?(s==="ss"?"#mpv6-ph":"#mpv6-dph"):'[data-mpv6-sel="'+s+":"+k+'"]');}
function mpv6Row(s,g,on){const D=mpv6Date(g),dc=g.dce;
  return`<li class="mpv-row mpv6-row${on?" on":""}" data-mpv6-row="${esc(g.k)}"><button type="button" class="mpv-rb mpv6-rb" aria-current="${on?"true":"false"}" data-mpv6-sel="${esc(s+":"+g.k)}" data-act="${act(()=>mpv6Sel(s,g.k))}">
    <span class="mpv-ref">${esc(g.ref)}</span><span class="mpv-ob2"><b>${esc(g.obj||"Objet non indiqué")}</b><small>${esc(g.mo||"Acheteur non indiqué")}</small></span>
    <span class="mpv-dt"><span>${esc(D.d)}</span>${D.r?`<span class="mpv-rel${D.u?" u":""}${D.c?" c":""}">${esc(D.r)}</span>`:""}</span>
    <span class="mpv6-st">${mpv6Etat(g)}<span class="mpv-dce mpv-c-${dc.c}" data-mpv-dce="${esc(dc.k)}">${esc(dc.t)}</span></span></button></li>`;}
function mpv6Pages(s,n){const st=MPV6[s],per=10,pages=Math.max(1,Math.ceil(n/per));st.page=Math.min(Math.max(1,st.page),pages);
  if(pages<2)return{i0:(st.page-1)*per,per,h:""};const W=[];for(let p=Math.max(1,st.page-2);p<=Math.min(pages,st.page+2);p++)W.push(p);const go=p=>act(()=>{st.page=p;render();mpdFocus(s==="ss"?"#mpv6-lt":"#mpv6-dlt");});
  return{i0:(st.page-1)*per,per,h:`<nav class="mpv-pg" aria-label="Pages de résultats"><button type="button" data-mpv6-page="prev" ${st.page<=1?"disabled":""} data-act="${go(st.page-1)}">‹ Précédent</button>${W.map(p=>`<button type="button" data-mpv6-page="${p}" ${p===st.page?'aria-current="page"':""} data-act="${go(p)}">${p}</button>`).join("")}${W[W.length-1]<pages?`<span>…</span><button type="button" data-mpv6-page="${pages}" data-act="${go(pages)}">${pages}</button>`:""}<button type="button" data-mpv6-page="next" ${st.page>=pages?"disabled":""} data-act="${go(st.page+1)}">Suivant ›</button></nav>`};}
const mpv6Opt=(s,f,L)=>`<select id="mpv6-${s}-${f}" data-mpv6-f="${s}.${f}">${L.map(([v,l])=>`<option value="${v}"${MPV6[s][f]===v?" selected":""}>${esc(l)}</option>`).join("")}</select>`;
const mpv6Search=(s,ph)=>`<div class="mpv-q">${mpvI("search","mpv-qi")}<label class="mpv-sr" for="mpv6-${s}-q">${esc(ph)}</label><input id="mpv6-${s}-q" type="search" autocomplete="off" placeholder="${esc(ph)}" data-mpv6-q="${s}" value="${esc(MPV6[s].q)}"></div>`;
function mpv6Wait(){return`<p class="mpv-vide" data-mpv-etat="${esc(S.aoState||"")}">${S.aoState==="err"?"Dossiers indisponibles : liste non calculée.":"Chargement des dossiers…"}</p>`;}
const mpv6Back=(s,k)=>`<button type="button" class="mpv-back" data-mpv-back="1" data-act="${act(()=>{MPV6[s].mob="list";render();mpdFocus('[data-mpv6-sel="'+s+":"+k+'"]');})}">← Retour à la liste</button>`;
function mpv6Url(g,u){const x=g.x||g.px;return x?(u?mpvDocUrl(x,u):pmmpUrl(x)):null;}
/* ---------- Mes consultations suivies ---------- */
function mpv6SuivPanel(g,inList){if(!g)return`<aside class="mpv-pan" aria-labelledby="mpv6-ph"><p class="mpv-kick" id="mpv6-ph" tabindex="-1">Consultation suivie</p><p class="mpv-mut">Sélectionnez une consultation dans la liste.</p></aside>`;
  const D=mpv6Date(g),dc=g.dce,u=mpv6Url(g);
  let h=`<aside class="mpv-pan" aria-labelledby="mpv6-ph" data-mpv6-panel="${esc(g.k)}">${mpv6Back("ss",g.k)}<p class="mpv-kick">Consultation suivie</p>${inList?"":`<p class="mpv-hl" data-mpv-hors="1">Hors des résultats affichés : la sélection est conservée.</p>`}
    <h2 class="mpv-ph" id="mpv6-ph" tabindex="-1">${esc(g.ref)}</h2><p class="mpv-pobj">${esc(g.obj||"Objet non indiqué")}</p><p class="mpv-mut">${esc(g.mo||"Acheteur non indiqué")}</p>
    <p class="mpv6-badges">${g.ouv?`<span class="mpv6-etat ouv" data-mpv6-petat="ouv">Consultation ouverte</span>`:`<span class="mpv6-etat clos" data-mpv6-petat="clos">Consultation clôturée</span>`}</p>
    <dl class="mpv-kv"><dt>Remise des plis</dt><dd>${esc(D.d)}${D.r?`<small class="mpv-rel${D.u?" u":""}${D.c?" c":""}">${esc(D.r)}</small>`:""}</dd>${g.x&&g.a.lim&&g.a.lim!==g.limS?`<dt>Date du dossier</dt><dd data-mpv6-datedos="1">${esc(fmtIso(g.a.lim))} · <small class="mpv-mut">antérieure : la date PMMP ci-dessus est la plus récente</small></dd>`:""}<dt>DCE</dt><dd><span class="mpv-dce mpv-c-${dc.c}" data-mpv6-pdce="${esc(dc.k)}">${esc(dc.t)}</span></dd>
    <dt>Décision</dt><dd data-mpv6-ndec="${g.nDec}">${g.nDec?g.nDec+" décision"+(g.nDec>1?"s":"")+" enregistrée"+(g.nDec>1?"s":"")+" (étape Décision)":"Aucune décision enregistrée"}</dd></dl>
    <p class="mpv6-socn" data-mpv6-socnote="1">${mpvI("info")}<span><b>Choix des sociétés : à l'étape Décision.</b> Le suivi concerne le groupe ; aucune société n'est désignée en suivant.</span></p>`;
  if(!g.x)h+=`<p class="mpv-mut" data-mpv6-horscat="1">${S.cat?"Absente du catalogue de cette version : informations du dossier.":"Catalogue non chargé : informations du dossier."}</p>`;
  h+=`<div class="mpv-acts"><button type="button" class="mpv-bp" data-mpv6-dossier="${esc(g.id)}" data-act="${act(()=>mpvOuvrir(g.id,null))}">${mpvI("open")}Ouvrir le dossier</button>
    <button type="button" class="mpv-bs2" data-mpv6-godce="${esc(g.k)}" data-act="${act(()=>{MPV6.ds.sel=g.k;MPV6.ds.mob="panel";MPV.tab="dce";MPN.outil="f:dce";MPV.outil="f:dce";MPV.conf=null;render();window.scrollTo(0,0);mpdFocus("#mpv6-dph");})}">${mpvI("dl")}Accéder à la récupération du DCE</button>
    ${u?`<a class="mpv-lk" href="${esc(u)}" target="_blank" rel="noopener" data-mpv6-pmmp="1">Voir sur PMMP${mpvI("ext","mpv-ie")}<span class="mpv-sr"> (nouvel onglet)</span></a>`:`<p class="mpv-mut">Pas de lien PMMP pour ce dossier.</p>`}</div>`;
  return h+`</aside>`;}
mpvSuivTab=function(B){if(S.aoState!=="ok")return mpv6Wait();const st=MPV6.ss,L=MPV6.all;   /* calculé par mpvDceGroupes au début de mpvPage */
  const nO=L.filter(g=>g.ouv).length,nC=L.length-nO;
  const F=L.filter(g=>(st.etat==="tout"||(st.etat==="ouv"?g.ouv:!g.ouv))&&(!st.dce||MPV6_DF[g.dce.k]===st.dce)&&mpv6Q(g,st.q)),list=mpv6Sort(F,st.sort),n=list.length;
  const P=mpv6Pages("ss",n),rows=list.slice(P.i0,P.i0+P.per);if(!st.sel||!MPV6.by.get(st.sel))st.sel=rows[0]?rows[0].k:null;const inList=list.some(g=>g.k===st.sel);
  let h=`<div class="mpv6" data-mpv6="suiv"><p class="mpv6-sum" data-mpv6-sum="${L.length}|${nO}|${nC}"><b>${L.length}</b> consultation${L.length>1?"s":""} suivie${L.length>1?"s":""} par le groupe · ${nO} ouverte${nO>1?"s":""} · ${nC} clôturée${nC>1?"s":""}</p>
    <div class="mpv6-fb">${mpv6Search("ss","Référence, objet ou acheteur")}<label class="mpv6-sel"><span>État</span>${mpv6Opt("ss","etat",[["tout","Toutes"],["ouv","Ouvertes"],["clos","Clôturées"]])}</label>
    <label class="mpv6-sel"><span>DCE</span>${mpv6Opt("ss","dce",[["","Tous"],["afaire","À récupérer"],["dem","Demande interne enregistrée"],["recu","Reçu (fichiers joints)"]])}</label>
    <label class="mpv6-sel"><span>Trier</span>${mpv6Opt("ss","sort",[["lim","Échéance la plus proche"],["limd","Échéance la plus lointaine"],["rec","Suivies récemment"]])}</label></div>`;
  h+=`<div class="mpv-grid" data-mob="${esc(st.mob)}"><section class="mpv-lst" aria-labelledby="mpv6-lt"><div class="mpv-lh"><h2 id="mpv6-lt" tabindex="-1">${n} consultation${n>1?"s":""} <small>${st.etat==="ouv"?"ouvertes":st.etat==="clos"?"clôturées":"suivies"}</small></h2><span class="mpv-mut" data-mpv6-rng="${n?P.i0+1:0}-${P.i0+rows.length}/${n}">${n?(P.i0+1)+" – "+(P.i0+rows.length)+" sur "+n:"0 résultat"}</span></div>`;
  h+=n?`<ul class="mpv-rows">${rows.map(g=>mpv6Row("ss",g,g.k===st.sel)).join("")}</ul>`:`<p class="mpv-vide" data-mpv-vide="1">${L.length?"Aucune consultation suivie ne correspond : changez la recherche ou les filtres.":"Aucune consultation suivie. Suivez-en une depuis l'onglet « Consultations »."}</p>`;
  h+=P.h+`<p class="mpv-note">${mpvI("info")}Une consultation compte une fois, même si plusieurs dossiers existent déjà pour elle. Les dossiers ne sont jamais supprimés.</p></section>${mpv6SuivPanel(MPV6.by.get(st.sel),inList)}</div></div>`;
  return h;};
/* ---------- DCE à récupérer ---------- */
function mpv6Fichiers(g){const seen=new Set(),F=[];g.ids.forEach(id=>{const a=S.ao[id];[...dceFichiers(a),...dceOriginaux(a)].forEach(f=>{const key=f.id||f.k;if(seen.has(key))return;seen.add(key);F.push(f.nom||f.k);});});return F;}
function mpv6Inv(g){const x=g.x;
  if(!x)return`<p class="mpv-mut" data-mpv6-inv="inconnu">Inventaire PMMP : inconnu (consultation absente du catalogue de cette version).</p>`;
  const st=mpvCfSt(x,"docs"),r=mpvCf(x);
  if(st!=="lu"||!r)return`<p class="mpv-mut" data-mpv6-inv="inconnu">Inventaire PMMP : inconnu — la liste des pièces publiées n'a pas encore été relevée pour cette consultation.</p>`;
  const D=r.docs||[],lu=r.docs_lu_le?` <small class="mpv-mut">relevé le ${esc(mpvDt(r.docs_lu_le))}</small>`:"";
  if(!D.length)return`<p class="mpv-mut" data-mpv6-inv="vide">Inventaire PMMP : aucune pièce publiée (constaté sur la fiche PMMP${r.docs_preuve==="bloc_aucune_piece"?", mention officielle « aucune pièce »":""}).${lu}</p>`;
  return`<div data-mpv6-inv="lu"><p class="mpv-mut">Pièces publiées sur PMMP (${D.length})${lu}</p><ul class="mpv6-inv">${D.map(d=>`<li data-mpv6-doc="${esc(d.type)}"><span>${esc(MPV5_DOC[d.type]||d.libelle||"Document")}${d.taille?` <small class="mpv-mut">${esc(d.taille)}</small>`:""}</span><a class="mpv-lk" href="${esc(mpvDocUrl(x,d.url))}" target="_blank" rel="noopener">Ouvrir sur PMMP${mpvI("ext","mpv-ie")}<span class="mpv-sr"> (nouvel onglet)</span></a></li>`).join("")}</ul></div>`;}
function mpv6DcePanel(g,where){if(!g)return`<aside class="mpv-pan" aria-labelledby="mpv6-dph"><p class="mpv-kick" id="mpv6-dph" tabindex="-1">DCE de la consultation</p><p class="mpv-mut">Sélectionnez une consultation dans la liste.</p></aside>`;
  const D=mpv6Date(g),dc=g.dce,ed=editable(),did=dc.id||g.id,a=S.ao[did]||g.a,E=dc.E||null,F=mpv6Fichiers(g),recu=dc.k==="pret"||dc.k==="partiel";
  const r=g.x?mpvCf(g.x):null,ddoc=r&&mpvCfSt(g.x,"docs")==="lu"?(r.docs||[]).find(d=>d.type==="dce"&&d.url):null,u=mpv6Url(g,ddoc?ddoc.url:null);
  let h=`<aside class="mpv-pan" aria-labelledby="mpv6-dph" data-mpv6-dpanel="${esc(g.k)}">${mpv6Back("ds",g.k)}<p class="mpv-kick">DCE de la consultation</p>${where?`<p class="mpv-hl" data-mpv6-hors="${esc(where)}">${esc(where)}</p>`:""}
    <h2 class="mpv-ph" id="mpv6-dph" tabindex="-1">${esc(g.ref)}</h2><p class="mpv-pobj">${esc(g.obj||"Objet non indiqué")}</p><p class="mpv-mut">${esc(g.mo||"Acheteur non indiqué")}</p>
    <dl class="mpv-kv"><dt>Date limite</dt><dd>${esc(D.d)}${D.r?`<small class="mpv-rel${D.u?" u":""}${D.c?" c":""}">${esc(D.r)}</small>`:""}</dd><dt>Statut du DCE</dt><dd><span class="mpv-dce mpv-c-${dc.c}" data-mpv6-dst="${esc(dc.k)}">${esc(dc.t)}</span></dd>
    ${E&&E.dem&&!recu?`<dt>Demande interne</dt><dd data-mpv6-dem="1">Enregistrée le ${esc(dceQuand(E.dem))} · ce n'est pas un DCE reçu</dd>`:""}</dl>`;
  h+=`<h3 class="mpv-h3">Inventaire PMMP</h3>${mpv6Inv(g)}`;
  h+=`<h3 class="mpv-h3">Fichiers joints au dossier</h3>${F.length?`<ul class="mpv6-inv" data-mpv6-joints="${F.length}">${F.slice(0,8).map(n=>`<li><span>${mpvI("file")}${esc(n)}</span></li>`).join("")}${F.length>8?`<li>+ ${F.length-8} autre(s)</li>`:""}</ul>${dc.k==="partiel"?`<p class="mpv-w">DCE partiel : parties manquantes d'après les noms de fichiers.</p>`:""}`:`<p class="mpv-mut" data-mpv6-joints="0">Aucun fichier joint : le DCE n'est pas reçu.</p>`}`;
  const conf=MPV.conf&&MPV.conf.t==="dem6"&&MPV.conf.id===did&&ed;
  if(conf)h+=mpvConfirm(`Enregistrer une demande interne de récupération du DCE pour ${esc(g.ref)} ? <b>Une demande interne n'est pas un DCE reçu</b> : le statut ne passe à « reçu » qu'avec des fichiers joints au dossier.`,"Confirmer la demande",()=>mpvDemander(did));
  else{h+=`<div class="mpv-acts">`;
    if(u)h+=`<a class="mpv-bs2 mpv6-a" href="${esc(u)}" target="_blank" rel="noopener" data-mpv6-docs="${ddoc?"dce":"fiche"}">${mpvI("ext")}Ouvrir les documents sur PMMP<span class="mpv-sr"> (nouvel onglet)</span></a>`;
    /* joindre : dépôt du ZIP existant (dceIngerer : archive vérifiée, PDF rangés, originaux conservés, registre dcef) sur le dossier de la consultation */
    if(recu)h+=`<button type="button" class="mpv-bp" data-mpv6-ouvdce="${esc(dc.id||g.id)}" data-act="${act(()=>mpvOuvrir(dc.id||g.id,"dce"))}">${mpvI("open")}Ouvrir le DCE joint</button>`;
    else if(ed)h+=`<div class="mpv6-join" data-mpv6-joindre="${esc(g.id)}"><p class="mpv6-jt">Joindre le DCE au dossier</p>${vDceDepot(g.id,S.ao[g.id])}</div>`;
    else h+=`<button type="button" class="mpv-bs2" data-mpv6-ouvdce="${esc(g.id)}" data-act="${act(()=>mpvOuvrir(g.id,"dce"))}">${mpvI("open")}Ouvrir le DCE du dossier</button>`;
    if(ed&&!recu&&(dc.k==="afaire"||dc.k==="echec"||dc.k==="nd")&&a&&a.portail&&g.ouv)h+=`<button type="button" class="mpv-bs2" data-mpv6-demande="${esc(did)}" data-act="${act(()=>{MPV.conf={t:"dem6",id:did};render();mpdFocus("[data-mpv-confok]");})}">${dc.k==="echec"?"Nouvelle demande interne":"Enregistrer une demande interne"}</button>`;
    h+=`<button type="button" class="mpv-lk" data-mpv6-dossier="${esc(g.id)}" data-act="${act(()=>mpvOuvrir(g.id,null))}">Ouvrir le dossier de la consultation</button></div>`;}
  const Dm=MPV.dem[did];
  if(Dm&&Dm.st==="ok")h+=`<p class="mpv-ok" role="status" data-mpv-dem="ok">Demande interne enregistrée et confirmée par la base. Le DCE n'est pas encore reçu.</p>`;
  if(Dm&&Dm.st==="err")h+=`<p class="mpv-w" role="alert" data-mpv-dem="err">Demande non confirmée (${esc(Dm.msg||"erreur")}) : l'état affiché est celui de la base.</p>`;
  h+=`<p class="mpv-note">${mpvI("info")}EAIOS ne télécharge rien et ne remplit aucun formulaire PMMP : téléchargez le DCE sur PMMP, puis joignez-le au dossier. « Reçu » seulement avec des fichiers joints.</p>`;
  if(!ed)h+=`<p class="mpv-mut">Lecture seule : demande et ajout de fichiers réservés aux personnes autorisées à modifier.</p>`;
  return h+`</aside>`;}
mpvDceTab=function(G){if(S.aoState!=="ok")return mpv6Wait();const st=MPV6.ds,O=G.O||[],Ech=G.E||[];
  const C={tout:O.length,sans:O.filter(g=>MPV6_DF[g.dce.k]==="afaire").length,dem:O.filter(g=>MPV6_DF[g.dce.k]==="dem").length,partiel:O.filter(g=>g.dce.k==="partiel").length,sept:O.filter(g=>g.lim.d!=null&&g.lim.d<=7).length};
  const FL=[["tout","Toutes"],["sans","Sans demande"],["dem","Demande interne enregistrée"],["partiel","DCE partiel"],["sept","Clôturent sous 7 jours"]].filter(([k])=>k!=="partiel"||C.partiel);
  if(!FL.some(([k])=>k===st.f))st.f="tout";
  const fx={tout:()=>true,sans:g=>MPV6_DF[g.dce.k]==="afaire",dem:g=>MPV6_DF[g.dce.k]==="dem",partiel:g=>g.dce.k==="partiel",sept:g=>g.lim.d!=null&&g.lim.d<=7}[st.f];
  let list=O.filter(g=>fx(g)&&mpv6Q(g,st.q));if(st.sort==="limd")list=list.slice().reverse();const n=list.length,P=mpv6Pages("ds",n),rows=list.slice(P.i0,P.i0+P.per);
  if(!st.sel||!MPV6.by.get(st.sel))st.sel=rows[0]?rows[0].k:null;const sg=MPV6.by.get(st.sel),inQ=sg&&O.includes(sg),inList=sg&&list.includes(sg);
  const where=!sg||inList?"":inQ?"Hors des résultats affichés : la sélection est conservée.":sg.dce.k==="pret"?"DCE reçu : hors de la file.":Ech.includes(sg)?"Échue ou sans suite : hors compteur.":"Hors de la file.";
  let h=`<div class="mpv6" data-mpv6="dce"><div class="mpv6-cnt" role="group" aria-label="Filtrer la file">${FL.map(([k,l])=>`<button type="button" class="mpv-chip" aria-pressed="${st.f===k}" data-mpv6-cf="${k}" data-mpv6-cn="${C[k]}" data-act="${act(()=>{st.f=k;st.page=1;render();mpdFocus('[data-mpv6-cf="'+k+'"]');})}">${esc(l)} <b>${C[k]}</b></button>`).join("")}</div>
    <div class="mpv6-fb">${mpv6Search("ds","Référence, objet ou acheteur")}<label class="mpv6-sel"><span>Trier</span>${mpv6Opt("ds","sort",[["lim","Échéance la plus proche"],["limd","Échéance la plus lointaine"]])}</label></div>`;
  h+=`<div class="mpv-grid" data-mob="${esc(st.mob)}"><section class="mpv-lst" aria-labelledby="mpv6-dlt"><div class="mpv-lh"><h2 id="mpv6-dlt" tabindex="-1" data-mpv6-dn="${O.length}">${O.length} DCE à récupérer <small>consultations suivies ouvertes, DCE non joint</small></h2><span class="mpv-mut" data-mpv6-rng="${n?P.i0+1:0}-${P.i0+rows.length}/${n}">${n?(P.i0+1)+" – "+(P.i0+rows.length)+" sur "+n:"0 résultat"}</span></div>`;
  h+=n?`<ul class="mpv-rows">${rows.map(g=>mpv6Row("ds",g,g.k===st.sel)).join("")}</ul>`:`<p class="mpv-vide" data-mpv-vide="1">${O.length?"Aucune consultation ne correspond : changez la recherche ou le filtre.":"Aucun DCE à récupérer pour les consultations suivies ouvertes."}</p>`;
  h+=P.h;
  h+=`<details class="mpv-hs mpv6-ech" data-mpv6-ech="${Ech.length}"${st.ech?" open":""}><summary>Échues ou sans suite, DCE non reçu (${Ech.length}) · hors compteur${mpvI("chev","mpv-car")}</summary><div>${Ech.length?`<ul class="mpv-rows">${Ech.map(g=>mpv6Row("ds",g,g.k===st.sel)).join("")}</ul>`:`<p class="mpv-mut">Aucune.</p>`}<p class="mpv-mut">Rien n'est supprimé : ces dossiers restent consultables.</p></div></details>`;
  h+=`</section>${mpv6DcePanel(sg,where)}</div></div>`;
  return h;};
/* ---------- onglets, indicateurs, suivi ---------- */
mpvTabs=function(){const ok=S.aoState==="ok",T=[["cons","Consultations",MPV.n],["suiv","Mes consultations suivies",ok?MPV.nSuiv6:null],["dce","DCE à récupérer",ok?MPV.nDce:null]];
  return`<div class="mpv-tabs" role="tablist" aria-label="Vues du bureau B1.1">${T.map(([k,l,n])=>`<button type="button" role="tab" id="mpv-tab-${k}" data-mpv-tab="${k}" aria-selected="${MPV.tab===k}" tabindex="${MPV.tab===k?0:-1}" aria-controls="mpv-tp" data-act="${act(()=>{MPV.tab=k;MPN.outil=k==="dce"?"f:dce":"veille";MPV.conf=null;render();mpdFocus('[data-mpv-tab="'+k+'"]');})}">${esc(l)}${n!=null?` <span class="mpv-tn">(${n})</span>`:""}</button>`).join("")}</div>`;};
{const _k6=mpvKpis;mpvKpis=function(B,G){return MPV.tab==="cons"?_k6(B,G):"";};}
/* panneau « Consultations » : flux Suivre sans société, dossiers sans noms de société */
{const _p6=mpvPanel;mpvPanel=function(B,dm,inList){let h=_p6(B,dm,inList);
  h=h.replace(/Suivre crée le dossier « À examiner » de cette consultation dans EAIOS \(société proposée par défaut : ALWAAD ATAIB, à confirmer à la décision\)\. <b>Ce n'est pas une décision de participer<\/b> ; aucun DCE n'est demandé\./,
    "Suivre ajoute cette consultation aux consultations suivies du groupe et crée son dossier « À examiner ». <b>Aucune société n'est choisie</b> : le choix se fait à l'étape Décision. Ce n'est pas une décision de participer ; aucun DCE n'est demandé.");
  h=h.replace(/(Enregistrer une demande de DCE dans le dossier [^<(]*?) \([^()<]*\) \?/,"$1 ?");
  const e=MPV.sel&&B&&B.by.get(MPV.sel),ids=e?dm[e.x.r+"/"+e.x.o]||[]:[];
  if(ids.length)h=h.replace(/<ul class="mpv-dl">[\s\S]*?<\/ul>/,`<p class="mpv-dl6" data-mpv6-suivie="1"><span>Suivie par le groupe · choix des sociétés à l'étape Décision</span><button type="button" class="mpv-lk" data-mpv-dos="${esc(ids[0])}" data-act="${act(()=>mpvOuvrir(ids[0],null))}">Ouvrir le dossier</button></p>`);
  return h;};}
suivre=async function(x){if(!editable())return toast(RO_MSG);const same=d=>!!(d&&d.portail&&String(d.portail.ref)===String(x.r)&&String(d.portail.org||"")===String(x.o||""));
  const deja=(mpvDosMap()[x.r+"/"+x.o]||[])[0];if(deja){render();return toast("Déjà suivie : dossier conservé tel quel, rien n'a été remplacé.");}
  let id="pmmp-"+x.r;if(S.ao[id]&&!same(S.ao[id]))id="pmmp-"+x.o+"-"+x.r;
  /* jamais écraser un dossier existant : relire la base avant de créer (même identifiant officiel = déjà suivie ; autre organisme = autre identifiant) */
  try{let g=await S.db.doc("ao/"+id).get();
    if(g&&g.exists&&!same(g.data())){id="pmmp-"+x.o+"-"+x.r;g=await S.db.doc("ao/"+id).get();}
    if(g&&g.exists){const d=g.data();if(same(d)){S.ao[id]=own(d);render();return toast("Déjà suivie : dossier conservé tel quel, rien n'a été remplacé.");}return toast("Identifiant de dossier déjà pris : rien n'a été enregistré.");}}
  catch(e){return toast("Vérification impossible, rien n'a été enregistré. Réessayez dans un instant.");}
  const ex={};if(x.est){ex.estimation=x.est;ex.estimationSource="Portail PMMP, fiche de la consultation : à confirmer dans le DCE";}
  if(x.cau){ex.cautionMode="montant";ex.caution=x.cau;}
  if(x.det&&x.q&&x.q.length){ex.qualifMode="oui";ex.qualif=x.q.map(q=>`${q.m} ${q.q} ${q.ql}, classe ${q.c}`).join(" ; ");}
  if(x.tp!=null)ex.tpme=x.tp?"oui":"non";
  if(Object.keys(ex).length)ex.sources={portail:"Portail PMMP, fiche de la consultation "+x.r+" ("+x.o+")"};
  const now=new Date().toISOString(),data={ref:x.ref,mo:x.mo,obj:x.obj,lim:x.lim,heure:x.h||"",est:x.est||0,tpme:x.tp===true,statut:"À examiner",checks:{},fichiers:{},cree:isoToday(),
    publie:x.pub||"",procedure:x.proc||"",categorie:x.cat||"",portail:{org:x.o,ref:x.r,url:pmmpUrl(x)},lieux:x.lx||[],lots:!!x.lots,exig:ex,
    veille:{source:"PMMP",profil:"Suivie depuis la veille nationale",detecte_le:now},suivi:{niveau:"groupe",le:now,qui:S.role.me||null,source:"B1.1 Veille"},
    note:"Suivie au niveau du groupe depuis la veille nationale. Exigences issues de la fiche du portail : à confirmer dans le DCE. Choix des sociétés à l'étape Décision."};
  return S.db.doc("ao/"+id).set(data).then(()=>{S.ao[id]=data;logJ("Consultation suivie (groupe) depuis la veille : "+x.ref+" ("+(x.mo||"").slice(0,60)+")");render();toast("Consultation suivie pour le groupe : dossier « À examiner » créé, aucune société choisie.");}).catch(e=>toast("Enregistrement refusé : "+(e&&e.code||"erreur")));};
/* accueil Marchés publics : « Compléter pour <société> » nomme explicitement la société de la carte ; elle reste sélectionnée à la Décision */
{const _mo6=mphOuvrir;mphOuvrir=function(id,k){const a=S.ao[id];if(k==="dec"&&a&&a.soc){B21D.ui={id,sel:a.soc,f:"toutes",q:"",mob:"list",dOpen:{}};B21D.dec=null;B21D.conf=null;}return _mo6(id,k);};}
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(!t||!t.dataset||t.dataset.mpv6Q==null)return;const s=t.dataset.mpv6Q;if(!MPV6[s])return;MPV6[s].q=t.value;MPV6[s].page=1;clearTimeout(MPV6.tq);
  MPV6.tq=setTimeout(()=>{render();const n=document.querySelector('[data-mpv6-q="'+s+'"]');if(n){n.focus();try{n.setSelectionRange(n.value.length,n.value.length);}catch(x){}}},250);});
document.getElementById("view").addEventListener("change",e=>{const t=e.target;if(!t||!t.dataset||t.dataset.mpv6F==null)return;const[s,f]=t.dataset.mpv6F.split(".");if(!MPV6[s])return;MPV6[s][f]=t.value;MPV6[s].page=1;render();mpdFocus('[data-mpv6-f="'+t.dataset.mpv6F+'"]');});
document.addEventListener("toggle",e=>{const t=e.target;if(t&&t.matches&&t.matches("[data-mpv6-ech]"))MPV6.ds.ech=t.open;},true);
const MPV6_CSS=`.mpv6{display:flex;flex-direction:column;gap:10px}.mpv6-sum{margin:0;font-size:13.5px;color:var(--mpv-mut)}.mpv6-sum b{color:var(--mpv-ink)}
.mpv6-fb{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}.mpv6-fb .mpv-q{flex:1 1 280px}
.mpv6-sel{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--mpv-line);background:var(--mpv-card);border-radius:6px;padding:0 10px;font-size:13px;color:var(--mpv-mut);min-height:42px}
.mpv6-sel select{border:0;background:transparent;color:var(--mpv-ink);font:inherit;font-size:14px;padding:8px 0;max-width:220px}
.mpv-lst .mpv6-rb{grid-template-columns:92px minmax(0,1.6fr) 136px 156px}.mpv-lst .mpv6-rb .mpv-ref{grid-column:1;grid-row:1}.mpv-lst .mpv6-rb .mpv-ob2{grid-column:2;grid-row:1}
.mpv-lst .mpv6-rb .mpv-dt{grid-column:3;grid-row:1;border-left:1px solid var(--mpv-line);padding-left:10px;flex-direction:column;align-items:flex-start}.mpv-lst .mpv6-rb .mpv6-st{grid-column:4;grid-row:1}
.mpv6-st{display:flex;flex-direction:column;gap:5px;align-items:flex-start;min-width:0}.mpv6-st .mpv-dce{white-space:normal}
.mpv6-etat{display:inline-block;border-radius:5px;padding:2px 8px;font-size:12.5px;font-weight:600}.mpv6-etat.ouv{background:var(--mpv-blb);color:var(--mpv-bl)}.mpv6-etat.clos{background:var(--mpv-neu);color:var(--mpv-neui)}
.mpv6-badges{margin:4px 0 0}.mpv6-socn{display:flex;gap:8px;align-items:flex-start;background:var(--mpv-ivo);border:1px solid var(--mpv-line);border-left:3px solid var(--mpv-orf);border-radius:6px;padding:8px 10px;font-size:13px;margin:6px 0 0}.mpv6-socn .mpv-i{width:16px;height:16px;flex:0 0 auto;margin-top:1px;color:var(--mpv-or)}
.mpv6-cnt{display:flex;flex-wrap:wrap;gap:8px}.mpv6-cnt .mpv-chip b{margin-left:4px}
ul.mpv6-inv{list-style:none;margin:4px 0;padding:0;display:flex;flex-direction:column;gap:6px;font-size:13.5px}ul.mpv6-inv li{display:flex;justify-content:space-between;align-items:center;gap:6px 10px;flex-wrap:wrap}ul.mpv6-inv li>span{display:inline-flex;gap:6px;align-items:center;min-width:0;overflow-wrap:anywhere}
.mpv6-a{text-decoration:none}.mpv6-join{border:1px solid var(--mpv-line);border-radius:6px;padding:8px 10px;background:var(--mpv-ivo)}.mpv6-jt{margin:0 0 6px;font-weight:700;font-size:14px}.mpv6-join .dce-depot{margin:0}.mpv-dl6{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 10px;align-items:center;font-size:13px;margin:4px 0}
@container mpvl (max-width:700px){.mpv-lst .mpv6-rb{grid-template-columns:minmax(0,1fr) auto}.mpv-lst .mpv6-rb .mpv-ref{grid-column:1;grid-row:1}.mpv-lst .mpv6-rb .mpv6-st{grid-column:2;grid-row:1 / 3;align-items:flex-end}
 .mpv-lst .mpv6-rb .mpv-ob2{grid-column:1;grid-row:2}.mpv-lst .mpv6-rb .mpv-dt{grid-column:1 / -1;grid-row:3;border-left:0;padding-left:0;flex-direction:row;flex-wrap:wrap;align-items:center}}
@media (max-width:640px){.mpv6-sel{flex:1 1 100%;justify-content:space-between}.mpv6-sel select{max-width:none;flex:1;text-align:right}}`;
{const _pg6=mpvPage;mpvPage=function(){if(!document.getElementById("mpv6-css")){const s=document.createElement("style");s.id="mpv6-css";s.textContent=MPV6_CSS;document.head.appendChild(s);}
  if(S.aoState!=="ok")MPV.nSuiv6=null;return _pg6();};}
