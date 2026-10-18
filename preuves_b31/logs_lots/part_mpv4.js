/* ===================== mpv-4 · B1.1 Veille : détail PAR LOT (popup PMMP « Détail des lots ») =====================
   Données : « pmmp_enrichi.lots » de catalogue_details.json (ingestion horaire du collecteur ; même garde catalogue_sha256).
   Jointure seulement si la référence de la fiche lue = référence du catalogue ; sinon le détail par lot est inconnu.
   Règle de filtre : les critères PAR LOT (estimation, caution, TPE/PME, qualification, agrément, visite) sont évalués sur un
   MÊME lot : une annonce correspond si UN de ses lots satisfait TOUS ces critères (OU dans un critère, ET entre critères).
   Exemple : estimation 1–5 M ET réservé TPE ne retient pas une annonce dont le lot 1 vaut 3 M (non réservé) et le lot 2 est réservé
   à 0,5 M. Les critères globaux (lieu, catégorie, dates, procédure, mode, domaines…) s'appliquent à l'annonce.
   Consultation non allotie : l'annonce est son propre « lot ». Allotie sans popup lu : tous les critères par lot sont inconnus ;
   popup partiel (moins de lots que « N Lots ») : les lots lus comptent, le reste est inconnu. Inconnu ≠ non indiqué : seule
   « Inclure aussi les fiches non renseignées » retient l'inconnu, signalé à part. Aucune somme ni valeur globale déduite.
   Comptes = annonces dédupliquées (une annonce à 3 lots correspondants compte 1). Aucune écriture. */
MPV.v="mpv-4";
const MPV_LK=["mts","cau","tp","qual","qh","ag","vis"];
const mpvLotsAll=()=>(S.enr&&S.enr.lots)||null;
const mpvAlloti=x=>!!(x.lots||x.allot);
function mpvLotsRec(x){const L=mpvLotsAll(),r=L&&(L.par_id||{})["pmmp:"+x.o+":"+x.r];return r&&mpvNref(r.ref)===mpvNref(x.ref)&&(r.lots||[]).length?r:null;}
function mpvLotSt(x){if(!mpvAlloti(x))return"non_alloti";const r=mpvLotsRec(x);if(r)return r.statut==="lu"?"lu":"partiel";const L=mpvLotsAll();if(L&&(L.inaccessibles||{})["pmmp:"+x.o+":"+x.r])return"inaccessible";return"non_lu";}
/* unités d'évaluation (mémoïsées par annonce et version des données) */
let mpvUC=new WeakMap(),mpvUV=null;
function mpvUnits(x){const L=mpvLotsAll();if(mpvUV!==L){mpvUC=new WeakMap();mpvUV=L;}let U=mpvUC.get(x);if(U)return U;
  if(!mpvAlloti(x))U=[{_u:1,_lot:null,det:x.det,est:x.est,cau:x.cau,tp:x.tp,q:x.q||[],ag:x.ag,vis:x.vis}];
  else{const r=mpvLotsRec(x);U=r?r.lots.map(l=>({_u:1,_lot:l.num,det:true,est:l.est==null?null:l.est,cau:l.cau==null?null:l.cau,tp:l.tp==null?null:l.tp,q:l.q||[],ag:(l.ag||[]).length?l.ag.join(" ; "):null,vis:l.vis||null})):[];
    if(!r||r.statut!=="lu")U.push({_u:1,_lot:null,_inc:1,det:false,est:null,cau:null,tp:null,q:[],ag:null,vis:null});}
  mpvUC.set(x,U);return U;}
/* moteur : critère d'unité inchangé (fonctions mpv-2) ; une annonce = ∃ unité satisfaisant tous les critères par lot actifs */
const _mpvF4=mpvF,_mpvUNK4={...MPV_UNK},_FAC4={mts:FACETS.mts,tp:FACETS.tp,cau:FACETS.cau,qual:FACETS.qual,ag:FACETS.ag,vis:FACETS.vis};
const mpvLotOn=d=>MPV_LK.filter(k=>MPV_ON[k](d));
function mpvUnitOk(u,d,ks,strict){let unk=false;for(const k of ks){if(_mpvF4(k,u,d))continue;const g=MPV_G[k];if(k!==strict&&g&&(d.inc||[]).includes(g)&&_mpvUNK4[k](u)){unk=true;continue;}return null;}return{unk};}
function mpvLotHits(x,d,strict){const ks=mpvLotOn(d);if(strict&&!ks.includes(strict))ks.push(strict);const H=[];mpvUnits(x).forEach(u=>{const r=mpvUnitOk(u,d,ks,strict);if(r)H.push({u,unk:r.unk});});return H;}
mpvF=function(k,x,d){if(!MPV_LK.includes(k)||x._u)return _mpvF4(k,x,d);return mpvLotHits(x,d,k).length>0;};  /* k réellement satisfait sur le lot ; autres critères par lot : même lot (inconnus admis seulement si inclus) */
["mts","tp","cau","qual","ag","vis"].forEach(k=>{FACETS[k]=(x,f)=>x._u||!x.r?_FAC4[k](x,f):(k==="mts"?!(f.mts.length||f.estMin||f.estMax):!f[k])||mpvF(k,x,f);});
MPV_LK.forEach(k=>{MPV_UNK[k]=x=>x._u?_mpvUNK4[k](x):mpvUnits(x).some(u=>_mpvUNK4[k](u));});
/* r = {ok, unk, lots} : lots = numéros des lots correspondants (annonce allotie, critère par lot actif) */
mpvMatch=function(e,d,skip){if(!mpvAxes(e,d,skip)||(skip!=="q"&&!mpvQ(e.x,d)))return{ok:false};let unk=false;const lk=[];
  for(const k in MPV_ON){if(k===skip||!MPV_ON[k](d))continue;if(MPV_LK.includes(k)){lk.push(k);continue;}if(_mpvF4(k,e.x,d))continue;const g=MPV_G[k];if(g&&d.inc.includes(g)&&_mpvUNK4[k](e.x)){unk=true;continue;}return{ok:false};}
  if(!lk.length)return{ok:true,unk};
  const H=[];mpvUnits(e.x).forEach(u=>{const r=mpvUnitOk(u,d,lk,null);if(r)H.push({u,unk:r.unk});});if(!H.length)return{ok:false};
  const sure=H.filter(h=>!h.unk);return{ok:true,unk:unk||!sure.length,lots:mpvAlloti(e.x)?sure.filter(h=>h.u._lot!=null).map(h=>h.u._lot):null,lotsInc:H.some(h=>h.unk)};};
/* comptes de la qualification (système/secteur/classe) : lignes des SEULS lots qui satisfont les autres critères par lot */
const _mpvDrawer4=mpvDrawer;
mpvDrawer=function(B){const d=MPV.dr,ks=mpvLotOn(d).filter(k=>k!=="qh"),sw=[];
  B.R.forEach(e=>{const x=e.x;if(!mpvAlloti(x)||!mpvLotsRec(x))return;const q=[];mpvUnits(x).forEach(u=>{if(u._lot!=null&&(!ks.length||mpvUnitOk(u,d,ks,null)))q.push(...u.q);});sw.push([x,x.q]);x.q=q;});
  let h;try{h=_mpvDrawer4(B);}finally{sw.forEach(([x,q])=>{x.q=q;});}
  const L=mpvLotsAll();
  h=h.replace(/(<section id="mpv-s-cond"[\s\S]*?<\/div>)/,`$1<p class="mpv-mut" data-mpv-lotrule="1">Consultations alloties : estimation, caution, TPE / PME, qualification, agrément et visite sont lus <b>par lot</b> sur PMMP. Ces critères sont vérifiés sur un <b>même lot</b> (ex. estimation et réservation TPE du même lot) ; les critères généraux (lieu, catégorie, dates…) portent sur l'annonce.</p>`);
  if(L){const c=L.couverture||{};h=h.replace(/(<section id="mpv-s-dispo"[\s\S]*?<ul class="mpv-dl2">)/,`$1<li data-mpv-cov="lots"><b>Détail par lot</b> : ${c.lues||0} consultation${(c.lues||0)>1?"s":""} alloties lues entièrement (${c.lots||0} lots)${c.partielles?` · ${c.partielles} lue${c.partielles>1?"s":""} partiellement`:""}${c.inaccessibles?` · ${c.inaccessibles} popup${c.inaccessibles>1?"s":""} inaccessible${c.inaccessibles>1?"s":""}`:""} · pas encore lues : ${c.non_lues||0}, sur ${c.alloties||0} alloties.</li>`);}
  return h;};
/* liste : lots correspondants */
const _mpvRow4=mpvRow;
mpvRow=function(e,dm,sel){let h=_mpvRow4(e,dm,sel);const x=e.x;if(!mpvAlloti(x))return h;const f=S.vf,ks=mpvLotOn(f),st=mpvLotSt(x);let t="";
  if(ks.length){const r=mpvMatch(e,f,null);if(r.ok)t=r.lots&&r.lots.length?(r.lots.length>1?"Lots ":"Lot ")+r.lots.join(", ")+" correspondant"+(r.lots.length>1?"s":"")+(r.lotsInc?" · autres lots inconnus":""):"Lots non renseignés (inclus à part)";}
  else t=st==="lu"?mpvLotsRec(x).lots.length+" lots détaillés":st==="partiel"?"Lots lus en partie":"Détail par lot non lu";
  return t?h.replace(/(<span class="mpv-ob2"><b>[\s\S]*?<\/b><small>[\s\S]*?)(<\/small>)/,(z,a,b)=>a+` · <span class="mpv-lotm" data-mpv-lotm="${esc((mpvMatch(e,f,null).lots||[]).join(","))}">${esc(t)}</span>`+b):h;};
/* fiche : estimation/caution/qualification par lot et détail de chaque lot, avec provenance */
function mpvMt(v,lab){return v==null?null:v===0?"0 sur PMMP (non exploitable)":dh(v)+(lab?" "+lab:"");}
function mpvNiTxt(l,k){return(l.ni||[]).includes(k)?"Non indiqué sur PMMP (« - »)":(l.na||[]).includes(k)?"Bloc non affiché par PMMP":"Non lu";}
function mpvLotHtml(l,on){const v=(k,val)=>val!=null&&val!==""?esc(val):`<span class="mpv-mut">${esc(mpvNiTxt(l,k))}</span>`;
  const q=(l.q||[]).length?`<ul class="mpv-lq">${l.q.map(z=>`<li>${esc(mpvSys(z.m))} · ${esc(mpvSect(z.m,z.s,z.sl))}${z.q?" · "+esc(z.q+(z.ql?" "+z.ql:"")):""} · ${esc(mpvCls(z.c))}</li>`).join("")}</ul>`:v("q",null);
  return`<li class="mpv-lot${on?" on":""}" data-mpv-lot="${esc(l.num||"")}"${on?' aria-current="true"':""}><b>Lot ${esc(l.num||"?")}${on?" · correspond aux filtres":""}</b>${l.intitule?` <span>${esc(l.intitule)}</span>`:""}
   <dl class="mpv-kv"><dt>Estimation</dt><dd data-mpv-lest="${l.est==null?"":l.est}">${l.est!=null?esc(mpvMt(l.est,"TTC"))+(l.est_libelle?` <small class="mpv-mut">${esc(l.est_libelle)}</small>`:""):v("est",null)}</dd>
   <dt>Caution provisoire</dt><dd>${l.cau!=null?esc(l.cau===0?"0 DH selon PMMP, à vérifier dans le DCE":dh(l.cau)):v("cau",null)}</dd>
   <dt>Réservé TPE / PME</dt><dd data-mpv-ltp="${l.tp==null?"":l.tp}">${l.tp==null?v("tp",null):l.tp?"Oui":"Non"}</dd><dt>Qualification</dt><dd>${q}</dd>
   <dt>Agréments</dt><dd>${(l.ag||[]).length?esc(l.ag.join(" ; ")):v("ag",null)}</dd><dt>Visite des lieux</dt><dd>${v("vis",l.vis)}</dd>
   <dt>Réunion</dt><dd>${v("reu",l.reu)}</dd><dt>Échantillons / prospectus</dt><dd>${v("proto",l.proto)}</dd><dt>Variante</dt><dd>${l.var==null?v("var",null):l.var?"Oui":"Non"}</dd>${l.env?`<dt>Environnement</dt><dd>${esc(l.env)}</dd>`:""}${l.cat?`<dt>Catégorie</dt><dd>${esc(l.cat)}</dd>`:""}</dl></li>`;}
const _mpvPanel4=mpvPanel;
mpvPanel=function(B,dm,inList){let h=_mpvPanel4(B,dm,inList);const e=MPV.sel&&B&&B.by.get(MPV.sel);if(!e)return h;const x=e.x;if(!mpvAlloti(x))return h;
  const r=mpvLotsRec(x),st=mpvLotSt(x),L=mpvLotsAll(),m=mpvLotOn(S.vf).length?mpvMatch(e,S.vf,null):null,on=new Set((m&&m.lots)||[]);
  const ind=r?"Par lot : voir le détail des lots ci-dessous":st==="inaccessible"?"Par lot : popup PMMP inaccessible":"Par lot : détail des lots pas encore lu";
  h=h.replace(/(<dt>Estimation<\/dt><dd>)([^<]*)(<\/dd><dt>Caution provisoire<\/dt><dd>)([^<]*)(<\/dd><dt>Qualification<\/dt><dd>)([^<]*)(<\/dd>)/,(z,a,ve,b,vc,c,vq,d2)=>a+(x.est!=null?ve:esc(ind))+b+(x.cau!=null?vc:esc(ind))+c+((x.q||[]).length?vq:esc(ind))+d2);
  let s=`<section class="mpv-lots" data-mpv-lots="${st}"><h3 class="mpv-h3">Détail par lot</h3>`;
  if(r){const i=(L.inaccessibles||{})["pmmp:"+x.o+":"+x.r];
    s+=`<p class="mpv-mut">Popup PMMP « Détail des lots » lu le ${esc(mpvDt(r.lu_le))} : ${r.lots.length} lot${r.lots.length>1?"s":""}${r.n_annonce!=null?` sur ${r.n_annonce} annoncé${r.n_annonce>1?"s":""}`:""}. Valeurs publiées par lot, sans somme ; estimations TTC telles que publiées.</p>`+
      (r.statut!=="lu"?`<p class="mpv-w" data-mpv-lotpart="1">Lecture partielle : les lots manquants sont inconnus (jamais remplis).</p>`:"")+(m&&m.ok?`<p class="mpv-hl" data-mpv-lotok="${esc([...on].join(","))}">${on.size?`Lot${on.size>1?"s":""} correspondant${on.size>1?"s":""} aux filtres : ${esc([...on].join(", "))}`:"Retenue grâce à « Inclure aussi les fiches non renseignées » (lots inconnus)"}</p>`:"")+
      `<ul class="mpv-lotl">${r.lots.map(l=>mpvLotHtml(l,on.has(l.num))).join("")}</ul>`;void i;}
  else s+=`<p class="mpv-mut" data-mpv-lotnl="1">${st==="inaccessible"?"Popup « Détail des lots » inaccessible après essais bornés : valeurs par lot inconnues.":"Détail des lots pas encore lu par le collecteur : estimation, caution, TPE / PME et conditions par lot inconnues (jamais déduites)."}</p>`;
  s+=`</section>`;
  return h.replace(/(<h3 class="mpv-h3">Pourquoi cette consultation \?<\/h3>)/,s+"$1");};
const MPV4_CSS=`.mpv-lotm{color:var(--accent,#2457c5);font-weight:600}.mpv-lots{margin:12px 0}.mpv-lotl{list-style:none;margin:6px 0 0;padding:0;display:grid;gap:8px}.mpv-lot{border:1px solid var(--line,#d8dde6);border-radius:8px;padding:8px 10px}.mpv-lot.on{border-color:var(--accent,#2457c5);box-shadow:0 0 0 1px var(--accent,#2457c5) inset}.mpv-lot>b{display:block;margin-bottom:4px}.mpv-lq{margin:0;padding-left:16px}.mpv-lot .mpv-kv{margin:0}`;
const _mpvPage4=mpvPage;
mpvPage=function(){if(!document.getElementById("mpv4-css")){const s=document.createElement("style");s.id="mpv4-css";s.textContent=MPV4_CSS;document.head.appendChild(s);}return _mpvPage4();};
/* provenance : fiche inaccessible après essais bornés (pmmp_enrichi.fiches) distincte de « pas encore lue » */
const _vProv4=vProvDetail;
vProvDetail=function(x){const k="pmmp:"+x.o+":"+x.r,fi=!x.det&&S.enr&&S.enr.fiches&&(S.enr.fiches.inaccessibles||{})[k];
  return fi?`<span data-ve-prov="inaccessible">Fiche PMMP inaccessible après ${esc(String(fi.tentatives||"?"))} essais${fi.dernier_echec?" (dernier le "+esc(mpvDt(fi.dernier_echec))+")":""} : informations de fiche inconnues, jamais déduites.</span>`:_vProv4(x);};
