/* ================= B2.1 · Décision d'Ahmed par société (b21d-1) =================
   Une carte par société candidate : chaque société a son propre dossier (ao/<base>~<société>, FIN-ISO-001) ; la carte ne lit que les
   pièces, l'état et les prix de CE dossier. Pièces : liste construite depuis les pièces du RC (b21Check) et les preuves existantes
   (coffre, pièces cachetées vérifiées) ; « Prêt » seulement sur preuve vérifiée. Ni chiffrage ni pièces après attribution (b21d-6). Décision : modèle existant
   a.decision {verdict, le, qui, motif} ; jamais de Go automatique ni de présélection ; une décision remplacée est conservée
   (a.decisionHist) et tracée au journal ; la société d'un dossier n'est jamais changée ici. L'avis et la recommandation de
   l'Analyste restent dans la note d'analyse. Consultation clôturée : décision affichée en lecture, aucune nouvelle soumission. */
const B21D={v:"b21d-9",motif:{},conf:null,ajout:null,ui:{id:null,open:null,f:"tout"},cat:{}};
const B21D_ST={prep:["b21d-neu","À préparer"],prep2:["b21d-neu","À préparer après Go · requis avant dépôt"],aprod:["b21d-amb","À produire si attribué"],pret:["b21d-ok","Prêt"],verif:["b21d-amb","À vérifier"],joindre:["b21d-ko","À joindre"],compl:["b21d-amb","À compléter"],nonexige:["b21d-neu","Non exigé"],attrib:["b21d-neu","Si attribué"]};
const B21D_COFFRE=["qc","refs","fis","cnss","rc","pouvoirs"],B21D_FIN=["bpu","sdp"];   /* l'acte d'engagement se prépare dans les pièces (B3.2) */
function b21dSibs(id,a){let L=[];try{L=b31Sibs(id,a);}catch(e){L=[{id,soc:a.soc,statut:a.statut}];}return L.map(s=>({oid:s.id,sid:s.soc,a:S.ao[s.id]})).filter(x=>x.a&&x.sid);}
function b21dRcId(oid,a){return[oid,a.base].filter(Boolean).find(x=>S.rc[x]&&Array.isArray(S.rc[x].pieces)&&S.rc[x].pieces.length)||oid;}
function b21dLim(a){if(!a.lim)return null;const m=String(a.heure||"").match(/(\d{1,2})\s*[hH:]\s*(\d{2})?/),d=new Date(a.lim+"T"+(m?String(m[1]).padStart(2,"0")+":"+(m[2]||"00"):"23:59")+":00");return isNaN(d)?null:d;}
const b21dClos=a=>{const d=b21dLim(a);return!!d&&d<new Date()&&!["Déposé","Attribué","Non retenu"].includes(a.statut);};
/* statut d'une pièce : « Prêt » uniquement sur preuve vérifiée */
function b21dPiece(row,p,oa,sid){const std=p&&p.std,st=row.st,dp=oa.dcePieces||{},F=oa.fichiers||{};
  /* b21d-6 : offre financière (enveloppe 2) = exigence du RC à préparer en Préparation ; aucun état de chiffrage dans la Décision */
  if(row.g==="Financier")return{k:"prep",ctrl:"Exigence du RC, à préparer en Préparation (pièces du dossier)"};
  if(std==="cpsrc"){const ok=["cps","rc"].every(k=>dp[k]&&dp[k].cachete&&dp[k].cachete.soc===sid&&dp[k].cachete.statut==="VÉRIFIÉ");
    if(ok)return{k:"pret",ctrl:"CPS et RC paraphés et cachetés au nom de "+socCourt(sid)+" : statut VÉRIFIÉ"};}
  if(std==="refs"&&F.refs&&F.refs.soc===sid&&F.refs.statut==="VÉRIFIÉ")return{k:"pret",ctrl:"Attestations de référence jointes au nom de "+socCourt(sid)+" : statut VÉRIFIÉ"};
  if(st==="nonexige")return{k:"nonexige"};if(st==="attrib")return{k:"attrib"};
  if(st==="dispo")return{k:B21D_COFFRE.includes(std)?"pret":"verif"};
  if(st==="manquant"||st==="bloquant")return{k:"joindre"};if(st==="remplir")return{k:"compl"};return{k:"verif"};}
function b21dAller(oid,bur,k){if(typeof MPN!=="undefined"&&MPN.dos&&typeof mpnDosAller==="function"){S.aoId=oid;MPN.dos=Object.assign({},MPN.dos,{id:oid});mpnDosAller(bur,k);}else{S.aoId=oid;S.stepOpen={...(S.stepOpen||{}),[oid]:k};}
  render();window.scrollTo(0,0);if(typeof mpdFocus==="function")mpdFocus("#mpn-h");}
function b21dAction(row,p,K,oid,sid){const std=p&&p.std,lab=K==="pret"?"Ouvrir":K==="joindre"?"Joindre":K==="compl"?(B21D_FIN.includes(std)||std==="memoire"||std==="moyens"||std==="planning"?"Saisir":"Compléter"):"Vérifier";
  if(K==="nonexige"||K==="attrib")return"";
  if(K==="prep")return`<button type="button" class="b21d-act" data-b21d-go="pieces" data-act="${act(()=>b21dAller(oid,"MP-B3.2","pieces"))}">Préparation<small>pièces B3.2</small></button>`;
  if(B21D_COFFRE.includes(std))return`<button type="button" class="b21d-act" data-b21d-go="coffre" data-act="${act(()=>go(()=>{S.soc=sid;S.dept=null;}))}">${lab}<small>coffre ${esc(socCourt(sid))}</small></button>`;
  return`<button type="button" class="b21d-act" data-b21d-go="pieces" data-act="${act(()=>b21dAller(oid,"MP-B3.2","pieces"))}">${lab}<small>pièces B3.2</small></button>`;}
function b21dCarteData(oid,oa,sid){const rcId=b21dRcId(oid,oa),r=S.rc[rcId]||{},P=Array.isArray(r.pieces)?r.pieces:[];let rows=[];try{rows=b21Check(rcId,oa,sid);}catch(e){rows=[];}
  const env={"Administratif":["e1","adm"],"Technique":["e1","tec"],"Technique (offre technique)":["e1","tec"],"Financier":["e2","fin"],"Si attribué":["att","att"]};
  const L=rows.filter(x=>x.pi!=null||x.st==="nonrens").map(x=>{const p=x.pi!=null?P[x.pi]:null,K=p?((env[x.g]||[])[0]==='att'?b21dPieceAtt(x):b21dPiece(x,p,oa,sid)):{k:"verif"},e=env[x.g]||["e1","aut"];
    return{piece:x.piece,ctrl:K.ctrl||x.ctrl,k:K.k,src:x.src,std:p&&p.std,env:e[0],sec:e[1],act:p?()=>b21dAction(x,p,K.k,oid,sid):null};});
  /* b21d-7 : prérequis société (preuves du coffre exigées par le RC) / à préparer après Go (tout le reste avant dépôt) */
  const pre=[],prep=[];L.forEach(x=>{if(x.env==="att")return;if(x.env==="e1"&&B21D_COFFRE.includes(x.std)){const rw=rows.find(r=>r.piece===x.piece&&P[r.pi]&&P[r.pi].std===x.std)||{};const k=x.k==="pret"?"joint":b21dPreK(rw.st);pre.push(Object.assign({},x,{k,vk:B21D_VK[x.std]}));}
    else prep.push(Object.assign({},x,{k:x.k==="nonexige"||x.k==="pret"?x.k:"prep2"}));});
  const prof=b21dProfMiss(sid),nPre=prof.filter(z=>!z.fait).length+pre.filter(z=>z.k!=="joint").length,nPrep=prep.filter(z=>z.k==="prep2").length;
  return{rcId,rows:L,pre,prep,prof,nPre,nPrep,reste:prof.filter(z=>!z.fait).concat(pre.filter(z=>z.k!=="joint")),rcOk:P.length>0,F:(()=>{try{return b21Fraicheur(rcId,oa);}catch(e){return null;}})()};}
function b21dTable(D,sid,att){const sec=att?[["att","att","Pièces exigées de l'attributaire (si le marché est attribué)"]]:[["e1","adm","Enveloppe 1 · Dossier administratif"],["e1","tec","Enveloppe 1 · Dossier technique"],["e1","aut","Enveloppe 1 · Autres pièces du RC"],["e2","fin","Enveloppe 2 · Offre financière (à préparer en Préparation)"]];
  let h=`<div class="b21d-tw"><table class="b21d-tab" aria-label="Pièces de ${esc(socCourt(sid||""))} : pièce, statut, action"><caption class="b21d-sr">Pièces du dossier de ${esc(socCourt(sid||""))} selon le RC</caption><thead><tr><th scope="col">Pièce</th><th scope="col">Statut</th><th scope="col">Action</th></tr></thead><tbody>`;
  sec.forEach(([e,s,t])=>{const R=D.rows.filter(x=>x.env===e&&x.sec===s);if(!R.length)return;h+=`<tr class="b21d-sec"><th colspan="3" scope="colgroup">${esc(t)}</th></tr>`;
    R.forEach(x=>{const S2=B21D_ST[x.k]||B21D_ST.verif;h+=`<tr data-b21d-k="${x.k}"><td><b>${esc(x.piece)}</b>${x.ctrl?`<small>${esc(x.ctrl)}</small>`:""}${x.src?`<small class="b21d-src">Source : ${esc(x.src)}</small>`:""}</td><td><span class="b21d-pill ${S2[0]}">${S2[1]}</span></td><td>${(x.act&&x.act())||`<span class="b21d-na">—</span>`}</td></tr>`;});});
  return h+`</tbody></table></div>`;}
const b21dQui=q=>q?(q===S.role.me?"vous":"Ahmed / gérance"):"auteur non enregistré";   /* même convention que prospQui */
function b21dDecTxt(d){return d?(d.verdict||"?")+(d.le?" · le "+fmtIso(d.le):"")+" · par "+b21dQui(d.qui)+(d.parallele?" (offre séparée)":"")+(d.motif?" · motif : "+d.motif:""):"Aucune décision enregistrée";}
/* ===== b21d-7 : prérequis société (coffre / profil) distincts des pièces à préparer après le Go ===== */
/* Go = participer et démarrer la préparation. Les pièces produites en Préparation (DH, CPS/RC signés, note moyens, AE, BPU,
   récépissé de caution…) ne bloquent jamais le Go : « À préparer après Go · requis avant dépôt » ; les contrôles du dépôt restent.
   Prérequis société : champs du profil requis (règle existante paramMiss du Paramétrage) et preuves du coffre exigées par le RC
   (qualification, références, attestations, pouvoirs), lues par les règles B2.3 existantes. Non renseigné ≠ inexistant : « À vérifier ». */
const B21D_PST={joint:["b21d-ok","Joint · en validité"],averif:["b21d-amb","À vérifier"],nonrens:["b21d-amb","Non renseigné · à vérifier"],invalide:["b21d-ko","Échu ou invalide"],
  arens:["b21d-amb","À renseigner · bloque la préparation"],pinv:["b21d-ko","Format invalide"],prof:["b21d-ok","Renseigné"]};
const B21D_VK={qc:"Qualification & classification",refs:"Attestations de bonne exécution",fis:"Attestation fiscale (marchés)",cnss:"Attestation CNSS (marchés)",rc:"RC / Modèle 9",pouvoirs:"PV & pouvoirs de signature"};
/* champs du profil : métadonnées de PF_FIELDS ; libellés « manquants » de la règle existante paramMiss, rattachés à leur clé */
const B21D_PF=(()=>{const F={};try{PF_FIELDS.forEach(([g,L])=>L.forEach(f=>{if(!f[2]||f[2]==="email"||f[2]==="num")F[f[0]]={lab:f[1],t:f[2]||"text"};}));}catch(e){}
  const M={};try{const A=paramMiss({});Object.keys(F).forEach(k=>{const B=paramMiss({[k]:k==="ice"?"123456789012345":k==="rib"?"123456789012345678901234":"x"});const d=A.filter(x=>!B.includes(x));if(d.length===1)M[d[0]]=k;});}catch(e){}
  return{F,M};})();
function b21dProfMiss(sid){const P=profilOf(sid)||{};let L=[];try{L=paramMiss(P);}catch(e){L=[];}const out=[],seen=new Set();
  L.forEach(l=>{if(l==="gérant"){out.push({k:"gerants",lab:"Gérant ou signataire",inv:false});return;}
    const inv=/^(ICE|RIB) à \d+ chiffres$/.test(l),k=inv?(l.startsWith("ICE")?"ice":"rib"):B21D_PF.M[l];if(!k||seen.has(k))return;seen.add(k);out.push({k,lab:(B21D_PF.F[k]||{}).lab||l,inv});});
  Object.keys(B21D.pf||{}).forEach(key=>{const[s2,k]=key.split("|");if(s2===sid&&!seen.has(k)&&k!=="gerants"&&B21D_PF.F[k]){seen.add(k);out.push({k,lab:B21D_PF.F[k].lab,inv:false,fait:true});}});
  if(B21D.pf&&B21D.pf[sid+"|gerants"]&&!out.some(x=>x.k==="gerants"))out.push({k:"gerants",lab:"Gérant ou signataire",inv:false,fait:true});
  return out;}
function b21dPreK(st){return st==="dispo"?"joint":st==="bloquant"?"invalide":st==="manquant"?"nonrens":"averif";}
/* preuves d'éligibilité ou de capacité pour l'AO (critères B2.3 non « attributaire ») pouvant bloquer le Go ; tout autre critère
   « incompatible » (ex. certificat de signature électronique, nécessaire au dépôt) reste une vérification non bloquante */
const B21D_ELIG=["Qualification & classification","Attestations de bonne exécution","Lignes de caution / crédit"];
/* blocage du Go : seulement les règles existantes — preuve d'éligibilité exigée datée échue (compatEval B2.3 « incompatible ») et art. 27
   (même société ou même signataire dans une autre offre active de la même consultation, comme parCompat) */
function b21dGoBloc(oid){const a=S.ao[oid];if(!a)return{bloc:[],verif:[]};const sid=a.soc,bloc=[],verif=[];
  try{const E=compatEval(oid,a,sid);(E.crits||[]).forEach(c=>{if(c.e==="ko"&&!c.attrib&&B21D_ELIG.includes(c.k))bloc.push({t:c.lab+" ("+socCourt(sid)+") : "+c.motif,src:c.src});else if(c.e==="ko")verif.push({t:c.lab+" : "+c.motif+" — à régler avant le dépôt ; ne bloque pas le Go",src:c.src});else if(c.e==="inc")verif.push({t:c.lab+" : "+c.motif,src:c.src});});}catch(e){verif.push({t:"Compatibilité B2.3 non calculable : à vérifier",src:""});}
  try{const sibs=consultSibs(a).filter(([o])=>o!==oid),mine=sibs.flatMap(([o,b])=>aoMembers(b).filter(Boolean).map(m=>({o,b,m})));
    if(mine.some(x=>x.m===sid))bloc.push({t:socCourt(sid)+" figure déjà dans une autre offre active de cette consultation (une seule offre par concurrent)",src:"décret 2-22-431, article « Groupements », § C"});
    const sg=pKey(pfSig({...a,soc:sid},sid));for(const x of mine){const so=pKey(pfSig(x.b,x.m));if(sg&&sg===so){bloc.push({t:"Même signataire que l'offre de "+socCourt(x.m)+" ("+pfSig(x.b,x.m)+")",src:"article 27 du décret 2-22-431"});break;}}}catch(e){}
  return{bloc,verif};}
/* ---- saisie en ligne d'un champ du profil, enregistrée dans le coffre de LA société (societes/<sid>.profil) ---- */
B21D.pf={};B21D.wq={};B21D.ouvF={};B21D.ptr=false;B21D.rq=0;
function b21dRenderSafe(){if(B21D.ptr){B21D.rq=1;return;}render();}
document.addEventListener("pointerdown",()=>{B21D.ptr=true;},true);
document.addEventListener("pointerup",()=>{B21D.ptr=false;if(B21D.rq){B21D.rq=0;setTimeout(render,60);}},true);
document.addEventListener("pointercancel",()=>{B21D.ptr=false;if(B21D.rq){B21D.rq=0;setTimeout(render,60);}},true);
const b21dPfStored=(sid,k)=>{const p=((S.docs||{})[sid]||{}).profil||{};return p[k]==null?"":p[k];};
function b21dPfNorm(k,v){v=String(v==null?"":v).trim();return k==="ice"||k==="rib"||k==="capital"?v.replace(/\s+/g,""):v;}
function b21dPfValid(k,v){if(!v)return"Valeur vide : rien n'est enregistré.";if(v.length>200)return"200 caractères au plus.";
  if(k==="mail"&&!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v))return"Adresse électronique invalide.";
  if((k==="tel"||k==="fax")&&!/^\+?[\d\s.\-()]{9,20}$/.test(v))return"Numéro invalide (au moins 9 chiffres).";
  if(k==="ice"&&!/^\d{15}$/.test(v))return"L'ICE compte 15 chiffres.";if(k==="rib"&&!/^\d{24}$/.test(v))return"Le RIB compte 24 chiffres.";
  if(k==="capital"&&!/^\d+$/.test(v))return"Montant en dirhams, chiffres seulement.";return null;}
function b21dPfEtat(F){return F.st==="saving"?"Enregistrement…":F.st==="ok"?"Enregistré ✓":F.st==="err"?"Échec de l'enregistrement : "+(F.msg||"erreur")+". Votre saisie est conservée.":F.st==="conflit"?"Modifiée ailleurs entre-temps : valeur enregistrée « "+F.cur+" ». Votre saisie est conservée.":F.st==="invalid"?F.msg:F.st==="lecture"?"Lecture seule : aucune modification possible.":"Enregistrement automatique à la sortie du champ ou après une pause.";}
function b21dPfSave(sid,k,force){const key=sid+"|"+k,F=B21D.pf[key];if(!F)return;clearTimeout(F.t);
  if(!editable()){F.st="lecture";return b21dRenderSafe();}
  if(k==="gerants"){const g=F.v;if(!String(g.nom||"").trim()){F.st="invalid";F.msg="Indiquez le nom du gérant ou du signataire.";return b21dRenderSafe();}}
  else{const v=b21dPfNorm(k,F.v),er=b21dPfValid(k,v);if(er){F.st="invalid";F.msg=er;return b21dRenderSafe();}if(v===F.saved&&!force)return;}
  if(!S.db){F.st="err";F.msg="base indisponible";return b21dRenderSafe();}
  F.st="saving";b21dPfPaint(key);const val=k==="gerants"?[{nom:String(F.v.nom).trim(),qualite:String(F.v.qualite||"").trim(),signe:F.v.signe||"unique"}]:b21dPfNorm(k,F.v);
  B21D.wq[sid]=(B21D.wq[sid]||Promise.resolve()).then(async()=>{const ref=S.db.doc("societes/"+sid),g=await ref.get(),pr=g&&g.exists?((g.data()||{}).profil||{}):{};
      if(!force){if(k==="gerants"){if((pr.gerants||[]).some(x=>x&&x.nom)){F.st="conflit";F.cur=(pr.gerants||[]).map(x=>x.nom).filter(Boolean).join(", ");return;}}
        else{const cur=pr[k]==null?"":String(pr[k]);if(cur!==String(F.base==null?"":F.base)&&cur!==val){F.st="conflit";F.cur=cur;return;}}}
      const maj=new Date().toISOString(),patch={profil:{[k]:val,maj}};if(g&&g.exists)await ref.update(patch);else await ref.set(patch);
      const d=D0(sid);d.profil={...(d.profil||{}),[k]:val,maj};try{socApply(sid);}catch(e){}
      if(k!=="gerants"){F.base=val;F.saved=val;}F.dirty=false;F.st="ok";F.cur=null;logJ((socCourt(sid)||sid)+" : profil mis à jour depuis la décision B2.1 ("+(k==="gerants"?"signataire":(B21D_PF.F[k]||{}).lab||k)+")");})
    .catch(e=>{F.st="err";F.msg=(e&&e.code)||"erreur";}).finally(()=>b21dRenderSafe());}
/* aller à la pièce précise du coffre de la société (rubrique dépliée, pièce mise en vue) */
function b21dCoffrePiece(sid,k){const i=SOC.findIndex(z=>z.sid===sid);let ci=-1;try{ci=VAULT.findIndex(([c,ps])=>ps.some(p=>p.k===k));}catch(e){}
  go(()=>{S.cur=i<0?0:i;S.soc=null;S.dept="coffre";S.cview="soc";S.filter="all";S.aoId=null;if(ci>=0)S.open["c"+ci]=true;});
  setTimeout(()=>{const e=[...document.querySelectorAll(".piece .nm")].find(n=>n.textContent.trim()===k);if(e){const r=e.closest(".piece");r.scrollIntoView({block:"center"});r.classList.add("b21d-cible");const b=r.querySelector("button,label");if(b&&b.focus)b.focus({preventScroll:true});}},60);}
/* b21d-6 : pièces exigées de l'attributaire → vue Résultat (B4.2) du même dossier et de sa société ; section conditionnelle :
   rien n'est supposé attribué, aucun résultat n'est modifié, rien n'est lancé ni écrit */
function b21dPieceAtt(row){return row.st==="dispo"?{k:"pret",ctrl:row.ctrl}:{k:"aprod",ctrl:row.ctrl};}
function vApresAttribB21(id,a){b21dCss();const sid=a.soc;if(!sid)return"";const D=b21dCarteData(id,a,sid),A=D.rows.filter(x=>x.env==="att"),nm=socCourt(sid);
  const k=a.statut==="Attribué"?"attribue":a.statut==="Non retenu"?"nonretenu":"conditionnel";
  let h=`<section class="b21d b21d-res" data-b21d-apres="${k}" data-b21d-res-soc="${esc(sid)}" aria-labelledby="b21d-apt-${esc(id)}"><h3 id="b21d-apt-${esc(id)}">Après attribution · pièces exigées de l'attributaire (${esc(nm)})</h3>`;
  h+=`<p class="b21d-intro" data-b21d-cond="1">${k==="attribue"?`Marché attribué à ${esc(nm)} : pièces à produire au titre de l'attribution, selon le RC.`:k==="nonretenu"?`Sans objet : l'offre de ${esc(nm)} n'a pas été retenue. Liste conservée pour mémoire.`:`Conditionnel : à produire seulement si le marché est attribué à ${esc(nm)}. Aucun résultat n'est supposé et aucun travail n'est lancé.`}</p>`;
  if(!D.rcOk)h+=`<p class="b21d-warn">Pièces du RC non relevées pour ce dossier : liste indisponible (aucune pièce supposée).</p>`;
  else if(!A.length)h+=`<p class="b21d-src">Le RC lu ne mentionne aucune pièce exigée de l'attributaire.</p>`;
  else h+=(k==="nonretenu"?`<details class="b21d-note"><summary>Pièces exigées de l'attributaire (${A.length})</summary>${b21dTable(D,sid,true)}</details>`:b21dTable(D,sid,true));
  h+=`<p class="b21d-src">Sources : pièces du RC lues (${esc(D.rcId)}) et coffre de ${esc(nm)} (attestations fiscale et CNSS, RC / modèle 9 propres à la société). Ce dossier seulement ; affichage sans écriture.</p>`;
  return h+`</section>`;}
/* b21d-4 : toutes les sociétés actuelles du groupe (SOC, liste dynamique). Sans dossier pour cet AO : carte compacte avec la compatibilité
   informative du moteur B2.3 (compatEval, jamais supposée compatible) et l'ajout par la création existante du dossier séparé
   (creerSib, option sansGo : contrôles parCompat art. 27 / déjà membre / écartée, sibData FIN-ISO-001, aucune décision, aucun Go). */
const B21D_CMP={"Possible":[1,"b21d-ok","Compatible"],"À vérifier":[2,"b21d-amb","À vérifier"],"Écartée":[3,"b21d-ko","Incompatible en l'état"]};
function b21dCompat(id,a,sid){try{const v=compatEval(id,a,sid);if(!v||!B21D_CMP[v.v])throw 0;return v;}catch(e){return{sid,v:"À vérifier",n:null,contre:["Compatibilité B2.3 non calculable pour cette société : rien n'est supposé"],err:1};}}
function b21dPasse(a){const d=b21dLim(a);return!!d&&d<new Date();}
function b21dFocus(sel){setTimeout(()=>{const b=document.querySelector(sel);if(b)b.focus({preventScroll:true});},0);}
/* ===================== b21d-8 · Décision B2.1 : liste des sociétés + panneau société (maquette validée) =====================
   Toutes les sociétés du groupe sont évaluées depuis leur propre profil, coffre et compatEval (B2.3), avec ou sans dossier.
   Sélectionner, chercher, filtrer : affichage seulement (B21D.ui), rien n'est créé ni écrit. Les informations manquantes se
   saisissent sous la pièce qui les utilise (correspondance tirée des générateurs existants pfMissing : DH, AE, plan de charge) ;
   enregistrement automatique b21d-7 dans le profil de LA société. Décision : choix explicite + « Confirmer la décision ». */
const B21D_DV={Go:"Participer","No-Go":"Ne pas participer","À reprendre":"À réexaminer"},B21D_DVK={participer:"Go",nepas:"No-Go",reex:"À reprendre"};
const B21D_GEN={dsh:"dh",ae:"ae",pc:"pc"};
/* libellés de pfMissing → clé du profil (champs saisissables) ; montants, lot, rabais : chiffrage (Préparation B3), jamais ici */
const B21D_FLD={"signataire":"gerants","téléphone":"tel","e-mail":"mail","RIB":"rib","RIB (24 chiffres attendus)":"rib","localité de la banque":"banque","Capital":"capital","CNSS":"cnss","RC":"rc","Patente":"patente","ICE":"ice","Siège":"siege"};
const B21D_FLAB={gerants:"Signataire (gérant)",tel:"Téléphone",mail:"E-mail",rib:"RIB (24 chiffres)",banque:"Banque / agence",capital:"Capital (DH)",cnss:"N° CNSS",rc:"N° RC",patente:"Taxe professionnelle",ice:"ICE (15 chiffres)",siege:"Siège social"};
const B21D_FIC={tel:"☎",mail:"✉",rib:"🏦",banque:"🏦",gerants:"✍",capital:"§",cnss:"§",rc:"§",patente:"§",ice:"§",siege:"⌂"};
const b21dFin=t=>/montant|n° de lot|rabais/i.test(t);
B21D.docF={};B21D.dec=null;
function b21dUi8(id,a){if(B21D.ui.id!==id){B21D.ui={id,sel:a.soc,f:"toutes",q:"",mob:"list"};B21D.dec=null;B21D.conf=null;}const u=B21D.ui;if(!u.f)u.f="toutes";if(u.q==null)u.q="";if(!u.sel)u.sel=a.soc;if(!u.mob)u.mob="list";return u;}
/* éligibilité pour cet AO : règles B2.3 existantes (preuves d'éligibilité non « attributaire ») et art. 27 / déjà membre */
function b21dElig(id,a,sid,X){const oid=X?X.oid:id,ac=X?X.a:a,non=[],ver=[],ok=[];let E=null;try{E=compatEval(oid,ac,sid);}catch(e){}
  if(!E)ver.push({t:"Compatibilité B2.3 non calculable pour cette société : rien n'est supposé",src:""});
  else{(E.crits||[]).forEach(c=>{if(c.attrib||!B21D_ELIG.includes(c.k))return;const r={t:c.lab+" : "+c.motif,src:c.src,vk:c.k,lab:c.lab};if(c.e==="ko")non.push(r);else if(c.e==="inc")ver.push(r);else ok.push(r);});
    if(E.inconnues&&E.inconnues.length)ver.push({t:"Exigences du marché inconnues : "+E.inconnues.join(", "),src:"Exigences lues du RC (B2.2)",b23:1,lab:"Exigences du marché"});}
  try{if(X){b21dGoBloc(X.oid).bloc.filter(z=>/décret|article/i.test(z.src||"")).forEach(z=>non.push({t:z.t,src:z.src}));}
    else{const pc=parCompat(id,a,sid);if((pc.st==="non"||pc.st==="deja")&&/article|décret/i.test(pc.why||""))non.push({t:pc.why,src:"décret 2-22-431"});}}catch(e){}
  return{k:non.length?"non":ver.length?"averif":"ok",non,ver,ok,E};}
/* documents à produire (RC) et informations nécessaires, par document ; proofs = preuves du coffre exigées par le RC */
function b21dDocs(id,a,sid,X){const oid=X?X.oid:id,ac=X?X.a:a,D=b21dCarteData(oid,ac,sid);let f0={};try{f0={...pfDefaults(ac,sid),...((ac.pieces||{})[sid]||{})};}catch(e){}
  const docs=(D.prep||[]).map((z,i)=>{const gen=B21D_GEN[z.std],o={i,piece:z.piece,std:z.std,src:z.src,fields:[],autres:[],fin:false,kind:"ready",note:""};
    if(z.k==="nonexige"){o.kind="nonexige";return o;}
    if(gen){let m=[];try{m=pfMissing(gen,ac,sid,f0).filter(x=>x!=="date");}catch(e){o.kind="verif";o.note="Contrôle des informations indisponible : vérification requise";return o;}
      m.forEach(l=>{if(b21dFin(l)){o.fin=true;return;}const k=B21D_FLD[l];if(k){if(!o.fields.some(f=>f.k===k))o.fields.push({k,lab:B21D_FLAB[k]||l,inv:/24 chiffres/.test(l)});}else o.autres.push(l);});
      o.kind=o.fields.length||o.autres.length?"miss":"ready";if(o.fin)o.note="Montants : préparés et chiffrés en Préparation (B3), pas dans la décision";}
    else if(z.std==="cpsrc"){if(z.k==="pret")o.note="Paraphés et cachetés au nom de "+socCourt(sid)+" (VÉRIFIÉ)";else if(!f0.sig){o.fields.push({k:"gerants",lab:B21D_FLAB.gerants});o.kind="miss";}else o.note="À parapher et signer par "+f0.sig;}
    else if(z.std==="caution")o.note="Récépissé à obtenir de la banque après la décision ; ligne de caution : voir l'éligibilité";
    else if(z.std==="bpu"||z.std==="sdp"){o.kind="b3";o.note="Chiffré en Préparation (B3)";}
    else if(z.std==="memoire"||z.std==="moyens"||z.std==="planning"){o.kind="verif";o.note="Moyens humains et matériels réels : non structurés dans EAIOS (le générateur laisse des repères [à compléter]) ; vérification requise";o.vk="Organigramme & effectifs";}
    else{o.kind="verif";o.note="Informations nécessaires non déterminées automatiquement pour cette pièce : vérification requise";}
    const kd=sid+"|"+z.std;B21D.docF[kd]=Array.from(new Set([...(B21D.docF[kd]||[]),...o.fields.map(f=>f.k)]));
    (B21D.docF[kd]||[]).forEach(k=>{if(!o.fields.some(f=>f.k===k)&&B21D.pf[sid+"|"+k])o.fields.push({k,lab:B21D_FLAB[k]||k,fait:true});});
    return o;});
  const proofs=(D.pre||[]);return{D,docs,proofs,rcOk:D.rcOk,rcId:D.rcId};}
function b21dEval(id,a,sid,X){const el=b21dElig(id,a,sid,X),dc=b21dDocs(id,a,sid,X),miss=new Set();dc.docs.forEach(d=>d.fields.filter(f=>!f.fait).forEach(f=>miss.add(f.k)));
  const nAutres=dc.docs.reduce((n,d)=>n+d.autres.length,0),nVer=dc.docs.filter(d=>d.kind==="verif").length,info=miss.size+nAutres;
  const B=[];if(el.k==="non")B.push(["non","Non éligible","b21d-ko"]);if(info)B.push(["comp","Informations à compléter","b21d-amb"]);if(el.k==="averif")B.push(["verif","Éligibilité à vérifier","b21d-amb"]);if(nVer)B.push(["verif","Documents à vérifier","b21d-amb"]);
  const pret=el.k==="ok"&&!info&&!nVer&&dc.rcOk;if(pret)B.push(["pret","Prête à préparer","b21d-ok"]);
  const pend=Object.entries(B21D.pf).some(([k,F])=>k.startsWith(sid+"|")&&F&&(F.st==="err"||F.st==="conflit"||F.st==="saving"||F.st==="invalid"||(F.st==="edit"&&F.dirty)));
  return{sid,X,el,dc,miss,info,nVer,B,pret,pend};}
const B21D_F8=[["toutes","Toutes",()=>true],["pretes","Prêtes",e=>e.pret],["comp","À compléter",e=>e.info>0],["verif","À vérifier",e=>e.el.k==="averif"||e.nVer>0],["non","Non éligible",e=>e.el.k==="non"]];
const B21D_SHORT={"Non éligible":"Non éligible","Informations à compléter":"À compléter","Éligibilité à vérifier":"À vérifier","Documents à vérifier":"À vérifier","Prête à préparer":"Prête à préparer"};
/* ---- sélection, filtre, recherche : état d'affichage seulement ---- */
function b21dSel(sid){const u=B21D.ui;if(u.sel!==sid)B21D.dec=null;u.sel=sid;u.mob="panel";render();b21dFocus('#b21d-ph');}
function b21dFil(f){B21D.ui.f=f;render();b21dFocus('[data-b21d-f="'+f+'"]');}
/* ---- champ saisissable sous la pièce (enregistrement automatique b21d-7, état partagé par société et champ) ---- */
function b21dPfEnsure(sid,k){const key=sid+"|"+k;if(!B21D.pf[key])B21D.pf[key]=k==="gerants"?{v:{nom:"",qualite:"Gérant",signe:"unique"},st:"edit"}:{v:String((profilOf(sid)||{})[k]||""),base:String(b21dPfStored(sid,k)),saved:null,st:"edit"};return B21D.pf[key];}
function b21dChip(F){const st=F?F.st:"vide";const M={vide:["b21d-neu","À saisir"],edit:["b21d-neu","Brouillon"],saving:["b21d-neu","Enregistrement…"],ok:["b21d-ok","Enregistré ✓"],err:["b21d-ko","Échec"],conflit:["b21d-ko","Conflit"],invalid:["b21d-ko","À corriger"],lecture:["b21d-neu","Lecture seule"]}[st]||["b21d-neu","Brouillon"];return M;}
function b21dFieldRow(sid,f,di){const key=sid+"|"+f.k,F=B21D.pf[key],ed=editable(),idb="b21d-pf-"+sid+"-"+f.k+"-"+di,C=b21dChip(F&&(F.st!=="edit"||F.dirty)?F:null);
  let h=`<div class="b21d-fr" data-b21d-fr="${esc(key)}" data-b21d-fdoc="${di}"><span class="b21d-fi" aria-hidden="true">${B21D_FIC[f.k]||"•"}</span>`;
  if(f.k==="gerants"){const v=F&&typeof F.v==="object"?F.v:{nom:"",qualite:"Gérant",signe:"unique"};
    h+=`<span class="b21d-fl">${esc(f.lab)}</span><div class="b21d-fg"><input id="${esc(idb)}-nom" aria-label="Nom et prénom du signataire" placeholder="Nom et prénom" data-b21d-pfg="${esc(key)}|nom" value="${esc(v.nom||"")}" ${ed?"":"disabled"} autocomplete="off"><input id="${esc(idb)}-qualite" aria-label="Qualité" placeholder="Qualité" data-b21d-pfg="${esc(key)}|qualite" value="${esc(v.qualite||"")}" ${ed?"":"disabled"}><select id="${esc(idb)}-signe" aria-label="Signature" data-b21d-pfg="${esc(key)}|signe" ${ed?"":"disabled"}>${[["unique","Seul"],["séparée","Séparée"],["conjointe","Conjointe"]].map(([x,l])=>`<option value="${x}" ${v.signe===x?"selected":""}>${l}</option>`).join("")}</select></div>`;
    h+=`<span class="b21d-fs"><span class="b21d-pill ${C[0]}" data-b21d-pfst="${esc(F?F.st:"vide")}" data-b21d-pfkey="${esc(key)}">${C[1]}</span>${ed&&(!F||F.st!=="ok")?`<button type="button" class="b21d-sb" data-b21d-pfsave="${esc(key)}" data-act="${act(()=>{b21dPfEnsure(sid,"gerants");b21dPfSave(sid,"gerants");})}">Enregistrer</button>`:""}</span>`;}
  else{const val=F?F.v:String((profilOf(sid)||{})[f.k]||""),t=(B21D_PF.F[f.k]||{}).t;
    h+=`<label class="b21d-fl" for="${esc(idb)}">${esc(f.lab)}</label><input id="${esc(idb)}" data-b21d-pf="${esc(key)}" type="${t==="email"?"email":"text"}" inputmode="${f.k==="tel"?"tel":f.k==="ice"||f.k==="rib"||f.k==="capital"?"numeric":"text"}" value="${esc(val)}" placeholder="Saisir" ${ed?"":"disabled"} autocomplete="off">
      <span class="b21d-fs"><span class="b21d-pill ${C[0]}" data-b21d-pfst="${esc(F?F.st:"vide")}" data-b21d-pfkey="${esc(key)}">${C[1]}</span>${ed&&F&&F.st==="err"?`<button type="button" class="b21d-sb" data-b21d-pfretry="${esc(key)}" data-act="${act(()=>b21dPfSave(sid,f.k))}">Réessayer</button>`:""}</span>`;}
  if(F&&(F.st==="err"||F.st==="conflit"||F.st==="invalid"))h+=`<p class="b21d-fm" role="status">${esc(b21dPfEtat(F))}</p>`;
  if(ed&&F&&F.st==="conflit")h+=`<div class="b21d-fm"><button type="button" class="b21d-sb" data-b21d-pfforce="${esc(key)}" data-act="${act(()=>b21dPfSave(sid,f.k,true))}">Remplacer par ma saisie</button> <button type="button" class="b21d-sb" data-b21d-pfkeep="${esc(key)}" data-act="${act(()=>{delete B21D.pf[key];render();})}">Garder la valeur enregistrée</button></div>`;
  return h+`</div>`;}
function b21dPfPaint(key){const F=B21D.pf[key];if(!F)return;document.querySelectorAll('[data-b21d-pfkey="'+CSS.escape(key)+'"]').forEach(n=>{const C=b21dChip(F);n.dataset.b21dPfst=F.st;n.className="b21d-pill "+C[0];n.textContent=C[1];});}
/* ---- décision : choix explicite, motif, confirmation ; enregistrement avec les contrôles actuels ---- */
function b21dEnreg(oid,verdict,motif){const a=S.ao[oid];if(!a)return false;const me=S.role.me||null,now=new Date().toISOString(),prev=a.decision;
  if(prev)a.decisionHist=(a.decisionHist||[]).concat([Object.assign({},prev,{remplaceLe:now,remplacePar:me})]).slice(-50);
  a.decision={verdict,le:isoToday(),qui:me,motif,soc:a.soc,source:"B2.1 décision par société"};
  a.statut=verdict==="Go"?"En préparation":verdict==="No-Go"?"Abandonné":"À examiner";
  saveAO(oid);logJ(a.ref+" : décision « "+(B21D_DV[verdict]||verdict)+" » pour "+socCourt(a.soc)+(prev?" (remplace « "+(B21D_DV[prev.verdict]||prev.verdict||"?")+" » du "+(prev.le?fmtIso(prev.le):"?")+")":"")+(motif?" — "+motif:""));
  if(verdict==="Go")prepDemarrer(oid,"Participer (B2.1)");return true;}
async function b21dConfirmer(id,sid){const a=S.ao[id],D=B21D.dec;if(!a)return;if(!D||D.sid!==sid||!D.v)return toast("Choisissez d'abord : Participer, Ne pas participer ou À réexaminer.");
  if(!editable())return toast(RO_MSG);if(b21dPasse(a))return toast("Consultation clôturée : décisions en lecture seule.");
  const X=b21dSibs(id,a).find(x=>x.sid===sid),V=B21D_DVK[D.v],motif=String(B21D.motif["s:"+sid]||"").trim().slice(0,300);
  if(V!=="Go"&&!motif)return toast("Motif obligatoire pour « "+B21D_DV[V]+" ».");
  if(X&&["Déposé","Attribué","Non retenu"].includes(X.a.statut))return toast("Dossier "+X.a.statut.toLowerCase()+" : décision figée.");
  if(V==="Go"){const el=b21dElig(id,a,sid,X);if(el.k==="non")return toast("Participation impossible en l'état : "+el.non.map(z=>z.t).join(" ; ")+".");}
  if(!X){/* société sans dossier : création à la confirmation seulement (creerSib sans Go) ; hors offre pour une non-participation */
    if(B21D.ajout)return toast("Création en cours, patientez.");B21D.ajout=sid;render();
    try{await creerSib(id,sid,{sansGo:true,horsOffre:V!=="Go",source:"B2.1 décision · "+B21D_DV[V]});}finally{B21D.ajout=null;}
    const nid=(a.base||id)+"~"+sid;if(!S.ao[nid]){render();return toast("Dossier non créé : aucune décision enregistrée.");}
    b21dEnreg(nid,V,motif);}
  else{if(X.a.decision&&X.a.decision.verdict===V&&(X.a.decision.motif||"")===motif)return toast("Décision inchangée : rien n'est enregistré.");b21dEnreg(X.oid,V,motif);}
  B21D.dec=null;delete B21D.motif["s:"+sid];render();toast("Décision « "+B21D_DV[V]+" » enregistrée pour "+socCourt(sid)+".");}
function b21dDecSec(id,a,e){const sid=e.sid,X=e.X,d=X&&X.a.decision,ed=editable(),passe=b21dPasse(a),fig=X&&["Déposé","Attribué","Non retenu"].includes(X.a.statut),peut=ed&&!passe&&!fig,D=B21D.dec&&B21D.dec.sid===sid?B21D.dec:null,H=X?(X.a.decisionHist||[]).slice().reverse():[];
  let h=`<section class="b21d-ds" aria-labelledby="b21d-dt" data-b21d-decsec="${esc(sid)}"><div class="b21d-dh"><div><h3 id="b21d-dt">Votre décision</h3><p class="b21d-src" data-b21d-decact="${esc(d?d.verdict:"aucune")}">${d?`<b>${esc(B21D_DV[d.verdict]||d.verdict)}</b> · le ${esc(d.le?fmtIso(d.le):"?")} · par ${esc(b21dQui(d.qui))}${d.motif?" · motif : "+esc(d.motif):""}`:"Aucune décision enregistrée."}</p></div>`;
  if(peut)h+=`<button type="button" class="b21d-pd" aria-expanded="${!!D}" aria-controls="b21d-dform" data-b21d-prendre="1" data-act="${act(()=>{B21D.dec=B21D.dec&&B21D.dec.sid===sid?null:{sid,v:null};render();b21dFocus('#b21d-dform [role=radio]');})}">${d?"Modifier la décision":"Prendre une décision"} <span aria-hidden="true">${D?"▴":"▾"}</span></button>`;
  h+=`</div>`;
  if(!peut)h+=`<p class="b21d-src" data-b21d-declock="1">${passe?"Consultation clôturée : décision en lecture seule, aucune nouvelle soumission.":!ed?"Lecture seule.":"Dossier "+esc(X.a.statut)+" : décision figée."}</p>`;
  if(peut&&D){const sansDos=!X;h+=`<div class="b21d-df" id="b21d-dform"><div class="b21d-dc"><div role="radiogroup" aria-label="Décision pour ${esc(socCourt(sid))}" class="b21d-dcs">${[["participer","Participer","b21d-cp"],["nepas","Ne pas participer","b21d-cn"],["reex","À réexaminer","b21d-cr"]].map(([k,l,c])=>{const dis=false;return`<button type="button" role="radio" aria-checked="${D.v===k}" class="b21d-ch8 ${c}" data-b21d-choix="${k}" ${dis?"disabled":""} data-act="${act(()=>{if(dis)return;B21D.dec={sid,v:k};render();b21dFocus('[data-b21d-choix="'+k+'"]');})}">${l}</button>`;}).join("")}</div>
      <p class="b21d-src">${sansDos?"Aucun dossier pour cet AO : à la confirmation seulement, le dossier séparé de "+esc(socCourt(sid))+" est d'abord créé (aucune donnée financière d'un autre dossier), puis la décision est enregistrée. « Ne pas participer » et « À réexaminer » ne lancent aucune préparation.":"Votre décision sera enregistrée et visible dans le suivi du dossier."} Les documents à préparer ne bloquent pas « Participer ».</p></div>
      <div class="b21d-dm"><label class="b21d-lab" for="b21d-motif-${esc(sid)}">Motif / commentaire <small>(obligatoire pour Ne pas participer et À réexaminer)</small></label><textarea id="b21d-motif-${esc(sid)}" rows="3" data-b21d-motif="s:${esc(sid)}" placeholder="Saisir un commentaire…">${esc(B21D.motif["s:"+sid]||"")}</textarea>
      <button type="button" class="b21d-cf" data-b21d-confirmer="1" ${D.v&&!B21D.ajout?"":"disabled"} data-act="${act(()=>b21dConfirmer(id,sid))}">${B21D.ajout===sid?"Création du dossier…":"Confirmer la décision"}</button></div></div>`;
    if(D.v==="participer"&&e.el.k==="non")h+=`<p class="b21d-warn" data-b21d-gobloc="${e.el.non.length}"><b>Participation impossible en l'état :</b> ${esc(e.el.non.map(z=>z.t+(z.src?" (source : "+z.src+")":"")).join(" ; "))}</p>`;}
  if(H.length)h+=`<details class="b21d-hist"><summary>Historique des décisions (${H.length})</summary><ul>${H.map(z=>`<li>${esc(B21D_DV[z.verdict]||z.verdict||"?")} · ${esc(z.le?fmtIso(z.le):"?")} · ${esc(b21dQui(z.qui))}${z.motif?" · "+esc(z.motif):""}<small>remplacée le ${esc(fmtDT(z.remplaceLe))} par ${esc(b21dQui(z.remplacePar))}</small></li>`).join("")}</ul></details>`;
  return h+`</section>`;}
/* ---- panneau d'une société ---- */
function b21dPanel(id,a,e){const sid=e.sid,X=e.X,nm=socCourt(sid),el=e.el,ELP={ok:["b21d-ok","Prouvée"],averif:["b21d-amb","À vérifier"],non:["b21d-ko","Non éligible"]}[el.k];
  let h=`<section class="b21d-p" aria-labelledby="b21d-ph" data-b21d-panel="${esc(sid)}"><button type="button" class="b21d-back" data-b21d-back="1" data-act="${act(()=>{B21D.ui.mob="list";render();b21dFocus('[data-b21d-item="'+sid+'"]');})}">← Sociétés</button>
    <header class="b21d-pt"><span class="b21d-pic" aria-hidden="true">▦</span><div><h3 id="b21d-ph" tabindex="-1">${esc(nm)}</h3><p class="b21d-src" data-b21d-psub="1">${e.B.length?esc(e.B.map(b=>b[1]).join(" · ")):"Aucun point relevé"}${X?" · dossier "+esc(X.a.statut||""):" · aucun dossier pour cet AO"}</p></div>
    <button type="button" class="b21d-lnk b21d-oc" data-b21d-coffre="${esc(sid)}" data-act="${act(()=>{const i=SOC.findIndex(z=>z.sid===sid);go(()=>{S.cur=i<0?0:i;S.soc=null;S.dept="coffre";S.cview="soc";S.aoId=null;});})}">Ouvrir le coffre ↗</button></header>`;
  const R=el.k==="non"?el.non:el.ver,r0=R[0],vk=(r0&&r0.vk)||null;
  h+=`<div class="b21d-eb b21d-eb-${el.k}" data-b21d-elig="${el.k}"><span class="b21d-ei" aria-hidden="true">⛨</span><div><p class="b21d-et"><b>Éligibilité pour cet AO</b> · <span class="b21d-pill ${ELP[0]}">${ELP[1]}</span></p><p class="b21d-src">${el.k==="ok"?"Preuves d'éligibilité exigées présentes et en validité (contenu non vérifié automatiquement).":esc(R[0]?R[0].t:"")+(R.length>1?" · + "+(R.length-1)+" autre"+(R.length>2?"s":"")+" point"+(R.length>2?"s":""):"")}${r0&&r0.src?" · Source : "+esc(r0.src):""}</p></div>`;
  if(r0)h+=`<button type="button" class="b21d-lnk" data-b21d-everif="1" data-act="${act(()=>vk&&VAULT.some(([c,ps])=>ps.some(p=>p.k===vk))?b21dCoffrePiece(sid,vk):b21dAller(X?X.oid:id,"MP-B2.3","note"))}">${vk?"Vérifier : "+esc(r0.lab||vk):"Voir les exigences (B2.3)"} →</button>`;
  h+=`</div>`;
  const P=e.dc.proofs;if(P.length||R.length>1)h+=`<details class="b21d-pv" data-b21d-proofs="${P.length}"><summary>Preuves d'éligibilité du coffre (${P.length}) et raisons détaillées</summary><ul>${R.map(z=>`<li>${esc(z.t)}${z.src?`<small>Source : ${esc(z.src)}</small>`:""}</li>`).join("")}${P.map(z=>{const S2=B21D_PST[z.k]||B21D_PST.averif;return`<li data-b21d-pk="${z.k}" data-b21d-std="${esc(z.std)}"><b>${esc(z.piece)}</b> <span class="b21d-pill ${S2[0]}">${S2[1]}</span> <button type="button" class="b21d-lnk" data-b21d-go="coffre" data-act="${act(()=>b21dCoffrePiece(sid,z.vk))}">${z.k==="nonrens"?"Joindre au coffre":z.k==="invalide"?"Mettre à jour":z.k==="joint"?"Ouvrir":"Vérifier"}</button>${z.src?`<small>Source : ${esc(z.src)}</small>`:""}</li>`;}).join("")}</ul></details>`;
  h+=`<div class="b21d-dd"><h4>Documents et informations nécessaires</h4><p class="b21d-src">Compléter les informations demandées pour préparer l'offre de ${esc(nm)}.</p>`;
  if(!e.dc.rcOk)h+=`<p class="b21d-warn">Pièces du RC non relevées pour ce dossier : liste indisponible (aucune pièce supposée).</p>`;
  e.dc.docs.forEach(d=>{const todo=d.fields.filter(f=>!f.fait).length+d.autres.length,open=d.fields.length||d.autres.length;
    if(d.kind==="nonexige")return;
    if(d.kind==="ready"&&!open){h+=`<div class="b21d-dl" data-b21d-doc="${esc(d.std||"")}" data-b21d-dk="ready"><span class="b21d-dic" aria-hidden="true">▤</span><b>${esc(d.piece)}</b><span class="b21d-pill b21d-ok">Prête à préparer</span>${d.note?`<small>${esc(d.note)}</small>`:""}</div>`;return;}
    if(d.kind==="b3"){h+=`<div class="b21d-dl" data-b21d-doc="${esc(d.std||"")}" data-b21d-dk="b3"><span class="b21d-dic" aria-hidden="true">▤</span><b>${esc(d.piece)}</b><span class="b21d-pill b21d-neu">Préparation (B3)</span><small>${esc(d.note)}</small></div>`;return;}
    if(d.kind==="verif"){h+=`<div class="b21d-dl" data-b21d-doc="${esc(d.std||"")}" data-b21d-dk="verif"><span class="b21d-dic" aria-hidden="true">▤</span><b>${esc(d.piece)}</b><span class="b21d-pill b21d-amb">Vérification requise</span><small>${esc(d.note)}</small>${d.vk?`<button type="button" class="b21d-lnk" data-act="${act(()=>b21dCoffrePiece(sid,d.vk))}">Voir le coffre</button>`:""}</div>`;return;}
    h+=`<article class="b21d-dcard" data-b21d-doc="${esc(d.std||"")}" data-b21d-dk="${todo?"miss":"done"}"><div class="b21d-dch"><span class="b21d-dic" aria-hidden="true">▤</span><div><p><b>${esc(d.piece)}</b> <span class="b21d-pill ${todo?"b21d-amb":"b21d-ok"}">${todo?"Informations à compléter":"Prête à préparer"}</span></p><p class="b21d-src">${todo?"Informations manquantes pour la génération :":"Informations complétées"}${d.src?" · Source : "+esc(d.src):""}</p></div><p class="b21d-gn">ⓘ Ce document sera généré après validation de votre décision.</p></div>`;
    h+=`<div class="b21d-frs">${d.fields.map(f=>b21dFieldRow(sid,f,d.i)).join("")}${d.autres.map(t=>`<div class="b21d-fr" data-b21d-autre="1"><span class="b21d-fi" aria-hidden="true">•</span><span class="b21d-fl">${esc(t)}</span><span class="b21d-src">À compléter dans les chantiers de la société (pas de saisie ici)</span></div>`).join("")}</div>`;
    if(d.fields.length)h+=`<p class="b21d-src b21d-sv">ⓘ Sauvegarde automatique dans le coffre de ${esc(nm)}.${d.note?" "+esc(d.note):""}</p>`;
    h+=`</article>`;});
  h+=`<p class="b21d-fn8">ⓘ Informations complètes ne signifie pas offre prête au dépôt : signatures, cachets et contrôles avant dépôt restent à faire.</p></div>`;
  h+=b21dDecSec(id,a,e);
  return h+`</section>`;}
function vDecisionB21(id,a){b21dCss();const u=b21dUi8(id,a),X=b21dSibs(id,a),lim=b21dLim(a),passe=b21dPasse(a);
  const ids=[];SOC.forEach(z=>{if(z&&z.sid&&!ids.includes(z.sid))ids.push(z.sid);});X.forEach(x=>{if(!ids.includes(x.sid))ids.push(x.sid);});
  const E=ids.map(sid=>b21dEval(id,a,sid,X.find(x=>x.sid===sid)||null));if(!E.some(e=>e.sid===u.sel))u.sel=(E[0]||{}).sid;
  const F8=B21D_F8.find(z=>z[0]===u.f)||B21D_F8[0],q=norm(u.q||"").toLowerCase(),L=E.filter(e=>F8[2](e)&&(!q||norm(socCourt(e.sid)).toLowerCase().includes(q)));
  let h=`<div class="b21d b21d8" data-b21d="${esc(id)}" data-b21d-mob="${esc(u.mob)}"><header class="b21d-top"><div><p class="b21d-sub8">Choisir une société, vérifier les prérequis, décider.</p></div>
    <div class="b21d-ao"><div><b>AO — ${esc(a.ref||id)}</b><span class="b21d-src">${esc(String(a.obj||"").slice(0,90))}</span></div><div class="b21d-cm">${lim?`<span class="b21d-pill ${passe?"b21d-ko":"b21d-neu"}" data-b21d-clos="${passe}">${passe?"Consultation clôturée le ":"Date limite : "}${esc(fmtIso(a.lim))}${a.heure?" "+esc(a.heure):""}</span>`:`<span class="b21d-pill b21d-amb">Date limite non renseignée</span>`}<button type="button" class="b21d-btn" data-b21d-maj="1" data-act="${act(()=>{try{delete B21.cache;}catch(e){}render();toast("État et documents relus ; aucune décision modifiée.");})}">Actualiser</button></div></div>
    <nav class="b21d-tabs" aria-label="Ce dossier"><button type="button" aria-current="page" data-b21d-tab="dec">Décision</button><button type="button" data-b21d-tab="note" data-b21d-voirnote="1" data-act="${act(()=>b21Aller(id,"note"))}">Note d'analyse</button><button type="button" data-b21d-tab="prep" data-act="${act(()=>b21dAller(id,"MP-B3.2","pieces"))}">Préparation</button><button type="button" data-b21d-tab="res" data-act="${act(()=>b21dAller(id,"MP-B4.2","res"))}">Résultat</button></nav></header>`;
  h+=`<div class="b21d-grid"><aside class="b21d-l" aria-labelledby="b21d-lt"><div class="b21d-lh"><h3 id="b21d-lt">Sociétés du groupe</h3><span class="b21d-src" data-b21d-total="${E.length}">${E.length} société${E.length>1?"s":""}</span></div>
    <label class="b21d-sr" for="b21d-q">Rechercher une société</label><input id="b21d-q" class="b21d-q" type="search" placeholder="Rechercher une société" data-b21d-q="1" value="${esc(u.q||"")}" autocomplete="off">
    <div class="b21d-filt" role="group" aria-label="Filtrer les sociétés">${B21D_F8.map(([k,l,fn])=>{const n=E.filter(fn).length;return`<button type="button" class="b21d-fb b21d-fb-${k}" aria-pressed="${u.f===k}" data-b21d-f="${k}" data-b21d-fn="${n}" data-act="${act(()=>b21dFil(k))}">${l} <span class="b21d-fn">${n}</span></button>`;}).join("")}</div>
    <p class="b21d-sr" role="status" aria-live="polite" data-b21d-fstat="${esc(u.f)}">Filtre « ${esc(F8[1])} » : ${L.length} société${L.length>1?"s":""} sur ${E.length}.</p>`;
  h+=L.length?`<ul class="b21d-ll">${L.map(e=>{const d=e.X&&e.X.a.decision,bs=[...new Map(e.B.map(b=>[B21D_SHORT[b[1]]||b[1],b])).entries()];return`<li><button type="button" class="b21d-it" aria-current="${u.sel===e.sid}" data-b21d-item="${esc(e.sid)}" data-act="${act(()=>b21dSel(e.sid))}"><span class="b21d-pic" aria-hidden="true">▦</span><span class="b21d-in">${esc(socCourt(e.sid))}</span><span class="b21d-ib">${bs.map(([t,b])=>`<span class="b21d-pill ${b[2]}" data-b21d-badge="${esc(b[0])}">${esc(t)}</span>`).join("")}${d?`<span class="b21d-pill b21d-neu" data-b21d-idec="${esc(d.verdict)}">${esc(B21D_DV[d.verdict]||d.verdict)}</span>`:""}${e.pend?`<span class="b21d-pill b21d-ko" data-b21d-pend="1">Saisie non enregistrée</span>`:""}</span><span aria-hidden="true" class="b21d-chev">›</span></button></li>`;}).join("")}</ul>`:`<p class="b21d-vide" data-b21d-vide="1">Aucune société dans « ${esc(F8[1])} »${q?" pour « "+esc(u.q)+" »":""}. <button type="button" class="b21d-lnk" data-act="${act(()=>{B21D.ui.f="toutes";B21D.ui.q="";render();})}">Tout afficher</button></p>`;
  h+=`</aside>`;
  const sel=E.find(e=>e.sid===u.sel);h+=sel?b21dPanel(id,a,sel):`<section class="b21d-p"><p class="b21d-src">Aucune société.</p></section>`;
  h+=`</div>`;
  let st="";try{const o=aoDecision(id,a),i=o.indexOf('<div class="grp">Statut du dossier</div>');st=i>=0?o.slice(i):"";}catch(e){}
  if(st)h+=`<details class="b21d-note"><summary>Statut administratif du dossier ${esc(socCourt(a.soc))} (existant)</summary>${st}</details>`;
  return h+`</div>`;}
/* vue pleine largeur dans le bureau B2.1 (décision à droite sur ordinateur) : même mécanisme que B3.1 */
function b21dPlein(id){return typeof MPN!=="undefined"&&!!MPN.dos&&MPN.dos.id===id&&MPN.dos.bur==="MP-B2.1"&&MPN.dos.k==="dec"&&!MPN.dos.global&&S.aoId===id;}
{const _mpnDossierB21D=mpnDossier;mpnDossier=function(d){const h=_mpnDossierB21D(d);try{const id=S.aoId;if(!id||!b21dPlein(id)||h.indexOf("b31-full")>=0)return h;b31Css();
  const t=h.replace('<div class="mpn" data-mpn-dossier-vue=','<div class="mpn b31-full b21d-full" data-mpn-dossier-vue=');return t.indexOf("b21d-full")<0?h:t;}catch(e){return h;}};}
{const _aoStepsB21D=aoSteps;aoSteps=function(id,a){const L=_aoStepsB21D(id,a),n=L.find(s=>s.k==="dec");if(n)n.body=()=>vDecisionB21(id,a);
  const r=L.find(s=>s.k==="res");if(r&&r.body){const b0=r.body;r.body=()=>{let x="";try{x=vApresAttribB21(id,a);}catch(e){x="";}return b0()+x;};}return L;};}
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(!t||!t.dataset)return;if(t.dataset.b21dMotif!=null)B21D.motif[t.dataset.b21dMotif]=t.value;
  if(t.dataset.b21dQ!=null){B21D.ui.q=t.value;render();return;}
  if(t.dataset.b21dPf){const key=t.dataset.b21dPf,[sid,k]=key.split("|"),F=b21dPfEnsure(sid,k);F.v=t.value;F.dirty=true;if(F.st!=="saving")F.st="edit";clearTimeout(F.t);F.t=setTimeout(()=>{if(document.activeElement!==t||b21dPfNorm(k,F.v)!==F.saved)b21dPfSave(sid,k);},1500);
    document.querySelectorAll('[data-b21d-pf="'+CSS.escape(key)+'"]').forEach(o=>{if(o!==t)o.value=t.value;});}
  if(t.dataset.b21dPfg){const[sid,k,f]=t.dataset.b21dPfg.split("|"),F=b21dPfEnsure(sid,k);F.v[f]=t.value;F.dirty=true;}});
document.getElementById("view").addEventListener("change",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.b21dPfg){const[sid,k,f]=t.dataset.b21dPfg.split("|"),F=b21dPfEnsure(sid,k);F.v[f]=t.value;F.dirty=true;}});
document.getElementById("view").addEventListener("focusout",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.b21dPf){const[sid,k]=t.dataset.b21dPf.split("|"),F=B21D.pf[t.dataset.b21dPf];if(F&&F.dirty&&F.st!=="saving"&&F.st!=="ok"&&F.st!=="conflit")b21dPfSave(sid,k);}});
const B21D_TOK=`--d-bg:#151B23;--d-card:#1B232E;--d-line:#2E3946;--d-ink:#EEE9DF;--d-mut:#A7ADB6;--d-okb:rgba(31,122,77,.22);--d-ok:#7FD1A6;--d-ambb:rgba(195,160,106,.2);--d-amb:#E3C48F;--d-kob:rgba(166,61,50,.25);--d-ko:#F0A49A;--d-neub:rgba(255,255,255,.08);--d-sec:rgba(195,160,106,.1)`;
const B21D_CSS=`.b21d{--d-bg:#FBF8F2;--d-card:#FFFFFF;--d-line:#E6DFD2;--d-ink:#16171A;--d-mut:#6B6E75;--d-okb:#E9F4EE;--d-ok:#1F7A4D;--d-ambb:#FBF1DE;--d-amb:#8A551C;--d-kob:#FBEAE7;--d-ko:#A63D32;--d-neub:#F1F0EC;--d-sec:#F6EFE2;
  background:var(--d-bg);color:var(--d-ink);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:12px;font-size:13.5px;container:b21d/inline-size}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .b21d{${B21D_TOK}}}:root[data-theme="dark"] .b21d{${B21D_TOK}}
.b21d *{box-sizing:border-box}.b21d h2,.b21d h3,.b21d h4{margin:0}.b21d-h1{font-size:22px;font-weight:600;letter-spacing:.01em}
.b21d-top{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;align-items:flex-start}.b21d-cm{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.b21d-ref{margin:0;font-size:13px}.b21d-src{color:var(--d-mut);font-size:12px;margin:4px 0 0;line-height:1.45;overflow-wrap:anywhere}.b21d-intro{margin:0;color:var(--d-mut)}
.b21d-card,.b21d-ret,.b21d-note{background:var(--d-card);border:1px solid var(--d-line);border-radius:12px}.b21d-card{padding:14px}.b21d-ret{padding:14px}.b21d-note{padding:10px 14px}.b21d-note summary{cursor:pointer;font-weight:600}
.b21d-ch{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;margin-bottom:10px}.b21d-ch h3{font-size:17px}
.b21d-body{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:14px;align-items:start}@container b21d (max-width:820px){.b21d-body{grid-template-columns:minmax(0,1fr)}}
.b21d-pill{display:inline-block;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:600;line-height:18px;white-space:nowrap}.b21d-big{font-size:14px;padding:4px 12px}
.b21d-ok{background:var(--d-okb);color:var(--d-ok)}.b21d-amb{background:var(--d-ambb);color:var(--d-amb)}.b21d-ko{background:var(--d-kob);color:var(--d-ko)}.b21d-neu{background:var(--d-neub);color:var(--d-mut)}
.b21d-tw{overflow-x:auto}.b21d-tab{width:100%;border-collapse:collapse;font-size:13px}.b21d-tab th,.b21d-tab td{text-align:left;padding:8px;border-bottom:1px solid var(--d-line);vertical-align:top}
.b21d-tab thead th{font-size:11.5px;color:var(--d-mut);font-weight:600}.b21d-tab td small{display:block;color:var(--d-mut);font-size:11.5px;margin-top:2px;overflow-wrap:anywhere}.b21d-sec th{background:var(--d-sec);font-size:12px;color:var(--d-amb)}
.b21d-tab td:nth-child(2){width:110px}.b21d-tab td:nth-child(3){width:130px}
.b21d-act,.b21d-btn,.b21d-db{display:inline-flex;flex-direction:column;align-items:flex-start;border:1px solid var(--d-line);background:var(--d-card);color:var(--d-ink);border-radius:8px;padding:5px 10px;font-family:inherit;font-weight:600;font-size:12.5px;line-height:1.25;cursor:pointer}
.b21d-act small{font-weight:400;color:var(--d-mut);font-size:11px}.b21d-btn{flex-direction:row}.b21d-lnk{background:none;border:none;color:var(--d-amb);font-family:inherit;font-weight:600;font-size:12.5px;cursor:pointer;padding:0 2px;text-decoration:underline}
.b21d-na{color:var(--d-mut)}.b21d-warn{background:var(--d-ambb);color:var(--d-ink);border-radius:8px;padding:8px 10px;margin:0}.b21d-fin{margin:10px 0 0;padding:8px 10px;background:var(--d-sec);border-radius:8px;font-size:12.5px}
.b21d-dec{border:1px solid var(--d-line);border-radius:10px;padding:12px;background:var(--d-bg);display:flex;flex-direction:column;gap:8px}.b21d-dec h4{font-size:14px}.b21d-dec p{margin:0}
.b21d-btns{display:flex;flex-wrap:wrap;gap:6px}.b21d-db{flex-direction:row;padding:7px 12px}.b21d-db[aria-pressed="true"]{border-color:var(--d-ok);background:var(--d-okb);color:var(--d-ok)}.b21d-arm{border-color:var(--d-amb)!important;background:var(--d-ambb)!important;color:var(--d-amb)!important}
.b21d-lab{display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:600}.b21d-lab small{font-weight:400;color:var(--d-mut)}.b21d-lab textarea{width:100%;border:1px solid var(--d-line);border-radius:8px;padding:6px 8px;font-family:inherit;font-size:13px;background:var(--d-card);color:var(--d-ink);resize:vertical}
.b21d-hist summary{cursor:pointer;font-size:12px;color:var(--d-amb)}.b21d-hist ul{margin:6px 0 0;padding-left:16px;font-size:12px}.b21d-hist small{display:block;color:var(--d-mut)}
.b21d-ret h3{font-size:15px;margin-bottom:8px}.b21d-rl{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}.b21d-rl li{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;padding:8px 10px;border:1px solid var(--d-line);border-radius:8px}.b21d-rl small{display:block;color:var(--d-mut);font-size:12px}
.b21d-rla{display:flex;gap:6px;align-items:center}.b21d-add{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.b21d-add p{flex-basis:100%;margin:0;font-size:12.5px}
.b21d-hs{display:flex;flex-direction:column;gap:8px}.b21d-hs h3{font-size:15px}.b21d-hs>.b21d-src{margin:0}.b21d-hg{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.b21d-mini{background:var(--d-card);border:1px dashed var(--d-line);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:8px;min-width:0}.b21d-mh{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px;align-items:center}.b21d-mh h3{font-size:15px}.b21d-mc{margin:0;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.b21d-mc .b21d-src{margin:0}
.b21d-mot{margin:0;padding-left:16px;font-size:12px;color:var(--d-ink)}.b21d-mot li{margin:2px 0;overflow-wrap:anywhere}.b21d-ma{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:auto}.b21d-ma .b21d-src{margin:0;flex:1 1 100%}.b21d-btn[disabled]{opacity:.55;cursor:not-allowed}
.b21d-socs{display:flex;flex-direction:column;gap:10px}.b21d-socs>h3{font-size:15px}.b21d-resume{margin:0;font-weight:600}.b21d-fst{margin:0}
.b21d-filt{display:flex;flex-wrap:wrap;gap:6px}.b21d-fb{border:1px solid var(--d-line);background:var(--d-card);color:var(--d-ink);border-radius:999px;padding:6px 12px;min-height:36px;font-family:inherit;font-size:13px;font-weight:600;cursor:pointer}.b21d-fb .b21d-fn{font-weight:500;color:var(--d-mut);margin-left:2px}.b21d-fb[aria-pressed="true"]{background:var(--d-ink);color:var(--d-bg);border-color:var(--d-ink)}.b21d-fb[aria-pressed="true"] .b21d-fn{color:inherit;opacity:.8}
.b21d-list{display:flex;flex-direction:column;gap:10px}.b21d-sum{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"nm tog" "ch ch";gap:8px 12px;align-items:center}.b21d-sum h3{grid-area:nm;font-size:16px;overflow-wrap:anywhere}.b21d-tog{grid-area:tog;min-height:38px;justify-content:center}.b21d-chips{grid-area:ch;display:flex;flex-wrap:wrap;gap:6px}
.b21d-card.b21d-mini{border-style:dashed}.b21d-det{margin-top:12px;padding-top:12px;border-top:1px solid var(--d-line);display:flex;flex-direction:column;gap:10px}.b21d-det[hidden]{display:none}.b21d-det>.b21d-ch{margin:0}.b21d-cd{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.b21d-vide{margin:0;padding:12px;border:1px dashed var(--d-line);border-radius:10px;color:var(--d-mut)}
@container b21d (max-width:420px){.b21d-sum{grid-template-columns:minmax(0,1fr);grid-template-areas:"nm" "ch" "tog"}.b21d-tog{width:100%}.b21d-chips .b21d-pill{white-space:normal}}
.b21d-res{margin-top:16px}.b21d-res h3{font-size:15px}
.b21d-sct{display:flex;flex-direction:column;gap:6px;margin-top:4px}.b21d-sct h4{font-size:14px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}.b21d-sct>.b21d-src{margin:0}
.b21d-pff{display:flex;flex-direction:column;gap:6px;padding:8px;border:1px solid var(--d-line);border-radius:8px;background:var(--d-bg)}.b21d-pfl,.b21d-pfg label{display:flex;flex-direction:column;gap:3px;font-size:12px;font-weight:600}.b21d-pff input,.b21d-pff select{width:100%;max-width:420px;border:1px solid var(--d-line);border-radius:8px;padding:7px 9px;font-family:inherit;font-size:14px;background:var(--d-card);color:var(--d-ink)}
.b21d-pfg{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}.b21d-pfs{margin:0;font-size:12.5px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.b21d-pfrow td{background:var(--d-sec)}
.b21d-gv summary{cursor:pointer;font-size:12px;color:var(--d-amb)}.b21d-gv ul{margin:6px 0 0;padding-left:16px;font-size:12px}.b21d-gv small{display:block;color:var(--d-mut)}
.b21d-pm{border:1px solid var(--d-amb);background:var(--d-ambb);border-radius:8px;padding:8px 10px;font-size:12.5px}
.b21d-gb{border:1px solid var(--d-ko);background:var(--d-kob);border-radius:8px;padding:8px 10px;font-size:12.5px}.b21d-gb ul{margin:4px 0 0;padding-left:16px}.b21d-gb small{display:block;color:var(--d-mut)}.b21d-db[disabled]{opacity:.5;cursor:not-allowed}
.b21d8{--d-acc:#A85F1C;--d-accb:#FBEFDF;--d-ok2:#2E7D4F;gap:14px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .b21d8{--d-acc:#E3A55C;--d-accb:rgba(227,165,92,.16);--d-ok2:#7FD1A6}}:root[data-theme="dark"] .b21d8{--d-acc:#E3A55C;--d-accb:rgba(227,165,92,.16);--d-ok2:#7FD1A6}
.b21d8 .b21d-top{align-items:center}.b21d-sub8{margin:0;color:var(--d-mut);font-size:14px}.b21d-ao{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;border:1px solid var(--d-line);background:var(--d-card);border-radius:12px;padding:10px 14px;flex:1 1 320px}.b21d-ao>div:first-child{display:flex;flex-direction:column;min-width:0}.b21d-ao .b21d-src{margin:0}
.b21d-tabs{display:flex;flex-wrap:wrap;gap:4px;border:1px solid var(--d-line);background:var(--d-card);border-radius:12px;padding:4px 8px}.b21d-tabs button{border:0;background:none;font-family:inherit;font-size:14px;font-weight:500;color:var(--d-ink);padding:8px 12px;cursor:pointer;border-bottom:2px solid transparent}.b21d-tabs button[aria-current="page"]{color:var(--d-acc);font-weight:700;border-bottom-color:var(--d-acc)}
.b21d-grid{display:grid;grid-template-columns:minmax(260px,330px) minmax(0,1fr);gap:16px;align-items:start}
.b21d-l,.b21d-p{background:var(--d-card);border:1px solid var(--d-line);border-radius:14px;padding:14px;min-width:0}.b21d-lh{display:flex;justify-content:space-between;align-items:baseline;gap:8px}.b21d-lh h3{font-size:18px}
.b21d-q{width:100%;margin:10px 0;border:1px solid var(--d-line);border-radius:10px;padding:9px 12px;font-family:inherit;font-size:14px;background:var(--d-card);color:var(--d-ink)}
.b21d8 .b21d-fb{border-color:transparent;background:var(--d-neub)}.b21d8 .b21d-fb-comp,.b21d8 .b21d-fb-verif{background:var(--d-ambb);color:var(--d-amb)}.b21d8 .b21d-fb-non{background:var(--d-kob);color:var(--d-ko)}.b21d8 .b21d-fb[aria-pressed="true"]{background:var(--d-acc);color:var(--d-bg)}
.b21d-ll{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:8px}.b21d-it{width:100%;display:grid;grid-template-columns:auto minmax(0,1fr) auto auto;gap:10px;align-items:center;text-align:left;border:1px solid var(--d-line);background:var(--d-card);color:var(--d-ink);border-radius:10px;padding:10px 12px;font-family:inherit;cursor:pointer}
.b21d-it[aria-current="true"]{border-color:var(--d-acc);background:var(--d-accb);box-shadow:0 0 0 1px var(--d-acc)}.b21d-in{font-weight:700;font-size:14px;overflow-wrap:anywhere}.b21d-ib{display:flex;flex-direction:column;align-items:flex-end;gap:3px}.b21d-chev{color:var(--d-mut);font-size:18px}.b21d-pic{color:var(--d-acc);font-size:18px}
.b21d-p{display:flex;flex-direction:column;gap:12px}.b21d-back{display:none}.b21d-pt{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center}.b21d-pt h3{font-size:22px;letter-spacing:.01em}.b21d-pt .b21d-src{margin:2px 0 0;font-size:13px}.b21d-oc{font-size:14px}.b21d-pt .b21d-pic{font-size:26px;width:44px;height:44px;display:grid;place-items:center;border-radius:10px;background:var(--d-sec)}
.b21d-eb{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:10px;align-items:center;border:1px solid var(--d-line);border-radius:12px;padding:10px 14px;background:var(--d-sec)}.b21d-eb-non{background:var(--d-kob);border-color:var(--d-ko)}.b21d-eb-ok{background:var(--d-okb)}.b21d-et{margin:0}.b21d-eb .b21d-src{margin:2px 0 0}.b21d-ei{font-size:22px;color:var(--d-acc)}
.b21d-pv summary{cursor:pointer;font-size:12.5px;color:var(--d-amb)}.b21d-pv ul{margin:6px 0 0;padding-left:16px;font-size:12.5px;display:flex;flex-direction:column;gap:4px}.b21d-pv small{display:block;color:var(--d-mut)}
.b21d-dd{display:flex;flex-direction:column;gap:8px}.b21d-dd h4{font-size:17px}.b21d-dd>.b21d-src{margin:0}
.b21d-dl{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:4px 10px;align-items:center;border:1px solid var(--d-line);border-radius:10px;padding:9px 12px}.b21d-dl small{grid-column:2 / -1;color:var(--d-mut);font-size:12px}.b21d-dl .b21d-lnk{grid-column:2 / -1;justify-self:start}.b21d-dic{color:var(--d-acc);font-size:18px}
.b21d-dcard{border:1px solid var(--d-line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:8px}.b21d-dch{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:10px;align-items:start}.b21d-dch p{margin:0}.b21d-gn{font-size:12px;color:var(--d-mut);max-width:260px}
.b21d-frs{border:1px solid var(--d-line);border-radius:10px;overflow:hidden}.b21d-fr{display:grid;grid-template-columns:24px minmax(110px,170px) minmax(0,1fr) auto;gap:8px 10px;align-items:center;padding:7px 10px;border-top:1px solid var(--d-line)}.b21d-fr:first-child{border-top:0}
.b21d-fr input,.b21d-fr select{width:100%;border:1px solid var(--d-line);border-radius:8px;padding:7px 9px;font-family:inherit;font-size:14px;background:var(--d-card);color:var(--d-ink);min-width:0}.b21d-fl{font-size:13px;font-weight:600}.b21d-fi{color:var(--d-mut);text-align:center}.b21d-fs{display:flex;gap:6px;align-items:center;justify-content:flex-end}
.b21d-fg{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr) minmax(0,1fr);gap:6px}.b21d-fm{grid-column:2 / -1;margin:0;font-size:12px;color:var(--d-ko)}.b21d-sb{border:1px solid var(--d-acc);color:var(--d-acc);background:var(--d-card);border-radius:8px;padding:5px 10px;font-family:inherit;font-weight:600;font-size:12.5px;cursor:pointer}
.b21d-sv{margin:0}.b21d-fn8{margin:0;font-size:12.5px;color:var(--d-mut);background:var(--d-sec);border-radius:8px;padding:8px 10px}
.b21d-ds{border-top:1px solid var(--d-line);padding-top:12px;display:flex;flex-direction:column;gap:10px}.b21d-dh{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;align-items:flex-start}.b21d-dh h3{font-size:18px}.b21d-dh .b21d-src{margin:2px 0 0}
.b21d-pd{border:1px solid var(--d-acc);color:var(--d-acc);background:var(--d-card);border-radius:10px;padding:8px 14px;font-family:inherit;font-weight:700;font-size:14px;cursor:pointer}
.b21d-df{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:14px}.b21d-dcs{display:flex;flex-wrap:wrap;gap:8px}.b21d-ch8{flex:1 1 140px;border:1.5px solid var(--d-line);background:var(--d-card);color:var(--d-ink);border-radius:10px;padding:12px;font-family:inherit;font-weight:700;font-size:14px;cursor:pointer}
.b21d-cp{border-color:var(--d-ok2);color:var(--d-ok2)}.b21d-cp[aria-checked="true"]{background:var(--d-ok2);color:var(--d-bg)}.b21d-cn{border-color:var(--d-ko);color:var(--d-ko)}.b21d-cn[aria-checked="true"]{background:var(--d-ko);color:var(--d-bg)}.b21d-cr{border-color:var(--d-acc);color:var(--d-acc)}.b21d-cr[aria-checked="true"]{background:var(--d-acc);color:var(--d-bg)}.b21d-ch8[disabled]{opacity:.45;cursor:not-allowed}
.b21d-dm{display:flex;flex-direction:column;gap:6px}.b21d-dm textarea{width:100%;border:1px solid var(--d-line);border-radius:8px;padding:8px;font-family:inherit;font-size:13px;background:var(--d-card);color:var(--d-ink)}.b21d-cf{align-self:flex-end;background:var(--d-acc);color:var(--d-bg);border:0;border-radius:10px;padding:10px 16px;font-family:inherit;font-weight:700;font-size:14px;cursor:pointer}.b21d-cf[disabled]{opacity:.5;cursor:not-allowed}
@container b21d (max-width:820px){.b21d-df{grid-template-columns:minmax(0,1fr)}.b21d-dch{grid-template-columns:auto minmax(0,1fr)}.b21d-gn{grid-column:1 / -1;max-width:none}}
@container b21d (max-width:760px){.b21d-grid{grid-template-columns:minmax(0,1fr)}.b21d8[data-b21d-mob="list"] .b21d-p{display:none}.b21d8[data-b21d-mob="panel"] .b21d-l{display:none}.b21d-back{display:inline-block;align-self:flex-start;border:0;background:none;color:var(--d-acc);font-family:inherit;font-weight:700;font-size:14px;padding:4px 0;cursor:pointer}
  .b21d-pt{grid-template-columns:auto minmax(0,1fr)}.b21d-oc{grid-column:1 / -1;justify-self:start}.b21d-eb{grid-template-columns:auto minmax(0,1fr)}.b21d-eb .b21d-lnk{grid-column:1 / -1;justify-self:start}
  .b21d-fr{grid-template-columns:20px minmax(0,1fr) auto}.b21d-fr input,.b21d-fr .b21d-fg{grid-column:1 / -1}.b21d-fs{grid-column:3;grid-row:1}.b21d-fg{grid-template-columns:minmax(0,1fr)}.b21d-dl{grid-template-columns:auto minmax(0,1fr)}.b21d-dl .b21d-pill{grid-column:2;justify-self:start}.b21d-dch p .b21d-pill{display:inline-block;margin-top:2px}.b21d-tabs button{padding:6px 8px;font-size:13px}}
.b21d-noteb{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.b21d-noteb .b21d-src{margin:0;flex:1 1 260px}
.b21d-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@container b21d (max-width:560px){.b21d-tab th,.b21d-tab td{padding:6px 4px}.b21d-tab td:nth-child(2){width:84px}.b21d-tab td:nth-child(3){width:86px}.b21d-tab .b21d-pill{white-space:normal;font-size:11px;padding:2px 7px}.b21d-tab .b21d-act{padding:4px 6px;max-width:100%}.b21d-tab .b21d-act small{display:none}.b21d-tab{table-layout:fixed}.b21d-tab th:nth-child(2),.b21d-tab td:nth-child(2){width:84px}.b21d-tab th:nth-child(3),.b21d-tab td:nth-child(3){width:78px}.b21d-tab td{overflow-wrap:anywhere}.b21d-tab th:nth-child(3),.b21d-tab td:nth-child(3){width:96px}.b21d-tab td:nth-child(3) .b21d-act{overflow-wrap:normal;word-break:keep-all;font-size:11.5px;padding:4px 6px}}`;
function b21dCss(){if(document.getElementById("b21d-css"))return;const s=document.createElement("style");s.id="b21d-css";s.textContent=B21D_CSS;document.head.appendChild(s);}
