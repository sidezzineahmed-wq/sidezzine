/* ================= B2.1 · Décision d'Ahmed par société (b21d-1) =================
   Une carte par société candidate : chaque société a son propre dossier (ao/<base>~<société>, FIN-ISO-001) ; la carte ne lit que les
   pièces, l'état et les prix de CE dossier. Pièces : liste construite depuis les pièces du RC (b21Check) et les preuves existantes
   (coffre, pièces cachetées vérifiées) ; « Prêt » seulement sur preuve vérifiée. Ni chiffrage ni pièces après attribution (b21d-6). Décision : modèle existant
   a.decision {verdict, le, qui, motif} ; jamais de Go automatique ni de présélection ; une décision remplacée est conservée
   (a.decisionHist) et tracée au journal ; la société d'un dossier n'est jamais changée ici. L'avis et la recommandation de
   l'Analyste restent dans la note d'analyse. Consultation clôturée : décision affichée en lecture, aucune nouvelle soumission. */
const B21D={v:"b21d-7",motif:{},conf:null,ajout:null,ui:{id:null,open:null,f:"tout"},cat:{}};
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
function b21dDecider(oid,verdict){const a=S.ao[oid];if(!a)return;if(!editable())return toast(RO_MSG);
  if(b21dClos(a))return toast("Consultation clôturée : la décision reste affichée en lecture, aucune nouvelle soumission.");
  if(["Déposé","Attribué","Non retenu"].includes(a.statut))return toast("Dossier "+a.statut.toLowerCase()+" : décision figée.");
  const motif=String(B21D.motif[oid]||"").trim().slice(0,300);
  if(verdict!=="Go"&&!motif)return toast("Saisissez le motif (obligatoire pour « "+verdict+" »).");
  if(verdict==="Go"){const GB=b21dGoBloc(oid);if(GB.bloc.length)return toast("Go impossible en l'état : "+GB.bloc.map(z=>z.t).join(" ; ")+".");}
  if(a.decision&&a.decision.verdict===verdict&&(a.decision.motif||"")===motif)return toast("Décision inchangée : rien n'est enregistré.");
  const k=oid+"|"+verdict;if(!B21D.conf||B21D.conf.k!==k||Date.now()-B21D.conf.t>6000){B21D.conf={k,t:Date.now()};render();return toast("Confirmez « "+verdict+" » pour "+socCourt(a.soc)+" : appuyez encore une fois. "+(verdict==="Go"?"La préparation de son dossier est lancée ; ":"")+"aucune autre société n'est modifiée.");}
  B21D.conf=null;const me=S.role.me||null,now=new Date().toISOString(),prev=a.decision;
  if(prev)a.decisionHist=(a.decisionHist||[]).concat([Object.assign({},prev,{remplaceLe:now,remplacePar:me})]).slice(-50);
  a.decision={verdict,le:isoToday(),qui:me,motif,soc:a.soc,source:"B2.1 décision par société"};
  a.statut=verdict==="Go"?"En préparation":verdict==="No-Go"?"Abandonné":"À examiner";
  saveAO(oid);logJ(a.ref+" : décision "+verdict+" pour "+socCourt(a.soc)+(prev?" (remplace "+(prev.verdict||"?")+" du "+(prev.le?fmtIso(prev.le):"?")+")":"")+(motif?" — "+motif:""));
  if(verdict==="Go")prepDemarrer(oid,"Go (B2.1)");delete B21D.motif[oid];render();
  toast(verdict==="Go"?"Go enregistré pour "+socCourt(a.soc)+" : la préparation démarre ; les pièces restantes restent à traiter avant dépôt.":verdict==="No-Go"?"No-Go enregistré pour "+socCourt(a.soc)+" : ses pièces sont conservées.":"« À reprendre » enregistré pour "+socCourt(a.soc)+" : retiré de la préparation, pièces conservées, réversible par un nouveau Go.");}
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
B21D.pf={};B21D.wq={};B21D.ouvF={};
const b21dPfStored=(sid,k)=>{const p=((S.docs||{})[sid]||{}).profil||{};return p[k]==null?"":p[k];};
function b21dPfNorm(k,v){v=String(v==null?"":v).trim();return k==="ice"||k==="rib"||k==="capital"?v.replace(/\s+/g,""):v;}
function b21dPfValid(k,v){if(!v)return"Valeur vide : rien n'est enregistré.";if(v.length>200)return"200 caractères au plus.";
  if(k==="mail"&&!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v))return"Adresse électronique invalide.";
  if((k==="tel"||k==="fax")&&!/^\+?[\d\s.\-()]{9,20}$/.test(v))return"Numéro invalide (au moins 9 chiffres).";
  if(k==="ice"&&!/^\d{15}$/.test(v))return"L'ICE compte 15 chiffres.";if(k==="rib"&&!/^\d{24}$/.test(v))return"Le RIB compte 24 chiffres.";
  if(k==="capital"&&!/^\d+$/.test(v))return"Montant en dirhams, chiffres seulement.";return null;}
function b21dPfOuvrir(sid,k){const key=sid+"|"+k;B21D.ouvF[key]=!B21D.ouvF[key];
  if(B21D.ouvF[key]&&!B21D.pf[key]){const cur=k==="gerants"?null:b21dPfStored(sid,k);B21D.pf[key]=k==="gerants"?{v:{nom:"",qualite:"Gérant",signe:"unique"},st:"edit"}:{v:String(profilOf(sid)[k]||""),base:String(cur),saved:null,st:"edit"};}
  render();if(B21D.ouvF[key])b21dFocus('#b21d-pf-'+CSS.escape(sid)+'-'+k+(k==="gerants"?"-nom":""));}
function b21dPfEtat(F){return F.st==="saving"?"Enregistrement…":F.st==="ok"?"Enregistré ✓":F.st==="err"?"Échec de l'enregistrement : "+(F.msg||"erreur")+". Votre saisie est conservée.":F.st==="conflit"?"Modifiée ailleurs entre-temps : valeur enregistrée « "+F.cur+" ». Votre saisie est conservée.":F.st==="invalid"?F.msg:F.st==="lecture"?"Lecture seule : aucune modification possible.":"Enregistrement automatique à la sortie du champ ou après une pause.";}
function b21dPfSave(sid,k,force){const key=sid+"|"+k,F=B21D.pf[key];if(!F)return;clearTimeout(F.t);
  if(!editable()){F.st="lecture";return render();}
  if(k==="gerants"){const g=F.v;if(!String(g.nom||"").trim()){F.st="invalid";F.msg="Indiquez le nom du gérant ou du signataire.";return render();}}
  else{const v=b21dPfNorm(k,F.v),er=b21dPfValid(k,v);if(er){F.st="invalid";F.msg=er;return render();}if(v===F.saved&&!force)return;}
  if(!S.db){F.st="err";F.msg="base indisponible";return render();}
  F.st="saving";b21dPfPaint(key);const val=k==="gerants"?[{nom:String(F.v.nom).trim(),qualite:String(F.v.qualite||"").trim(),signe:F.v.signe||"unique"}]:b21dPfNorm(k,F.v);
  B21D.wq[sid]=(B21D.wq[sid]||Promise.resolve()).then(async()=>{const ref=S.db.doc("societes/"+sid),g=await ref.get(),pr=g&&g.exists?((g.data()||{}).profil||{}):{};
      if(!force){if(k==="gerants"){if((pr.gerants||[]).some(x=>x&&x.nom)){F.st="conflit";F.cur=(pr.gerants||[]).map(x=>x.nom).filter(Boolean).join(", ");return;}}
        else{const cur=pr[k]==null?"":String(pr[k]);if(cur!==String(F.base==null?"":F.base)&&cur!==val){F.st="conflit";F.cur=cur;return;}}}
      const maj=new Date().toISOString(),patch={profil:{[k]:val,maj}};if(g&&g.exists)await ref.update(patch);else await ref.set(patch);
      const d=D0(sid);d.profil={...(d.profil||{}),[k]:val,maj};try{socApply(sid);}catch(e){}
      if(k!=="gerants"){F.base=val;F.saved=val;}F.st="ok";F.cur=null;logJ((socCourt(sid)||sid)+" : profil mis à jour depuis la décision B2.1 ("+(k==="gerants"?"signataire":(B21D_PF.F[k]||{}).lab||k)+")");})
    .catch(e=>{F.st="err";F.msg=(e&&e.code)||"erreur";}).finally(()=>render());}
function b21dPfPaint(key){const F=B21D.pf[key],n=document.querySelector('[data-b21d-pff="'+CSS.escape(key)+'"] [data-b21d-pfst]');if(!F||!n)return;n.dataset.b21dPfst=F.st;n.innerHTML=`<span class="b21d-pill b21d-neu">Enregistrement…</span> `+esc(b21dPfEtat(F));}
function b21dPfForm(sid,x){const key=sid+"|"+x.k,F=B21D.pf[key]||{st:"edit",v:""},ed=editable(),idb="b21d-pf-"+sid+"-"+x.k,etat=b21dPfEtat(F);
  const cls=F.st==="ok"?"b21d-ok":F.st==="err"||F.st==="conflit"||F.st==="invalid"?"b21d-ko":"b21d-neu";
  let h=`<div class="b21d-pff" data-b21d-pff="${esc(key)}">`;
  if(x.k==="gerants")h+=`<div class="b21d-pfg"><label>Nom et prénom<input id="${esc(idb)}-nom" data-b21d-pfg="${esc(key)}|nom" value="${esc(F.v.nom||"")}" ${ed?"":"disabled"} autocomplete="off"></label><label>Qualité<input id="${esc(idb)}-qualite" data-b21d-pfg="${esc(key)}|qualite" value="${esc(F.v.qualite||"")}" ${ed?"":"disabled"}></label><label>Signature<select id="${esc(idb)}-signe" data-b21d-pfg="${esc(key)}|signe" ${ed?"":"disabled"}>${[["unique","Seul"],["séparée","Séparée"],["conjointe","Conjointe"]].map(([v,l])=>`<option value="${v}" ${F.v.signe===v?"selected":""}>${l}</option>`).join("")}</select></label></div>`;
  else{const t=(B21D_PF.F[x.k]||{}).t;h+=`<label class="b21d-pfl">${esc(x.lab)}<input id="${esc(idb)}" data-b21d-pf="${esc(key)}" type="${t==="email"?"email":"text"}" inputmode="${x.k==="tel"||x.k==="fax"?"tel":x.k==="ice"||x.k==="rib"||x.k==="capital"?"numeric":"text"}" value="${esc(F.v)}" ${ed?"":"disabled"} autocomplete="off"></label>`;}
  h+=`<p class="b21d-pfs" role="status" aria-live="polite" data-b21d-pfst="${esc(F.st)}"><span class="b21d-pill ${cls}">${esc(F.st==="ok"?"Enregistré ✓":F.st==="saving"?"Enregistrement…":F.st==="err"?"Échec":F.st==="conflit"?"Conflit":F.st==="invalid"?"À corriger":"Brouillon")}</span> ${esc(etat)}</p>`;
  if(ed&&(F.st==="err"))h+=`<button type="button" class="b21d-btn" data-b21d-pfretry="${esc(key)}" data-act="${act(()=>b21dPfSave(sid,x.k))}">Réessayer</button>`;
  if(ed&&F.st==="conflit")h+=`<div class="b21d-ma"><button type="button" class="b21d-btn" data-b21d-pfforce="${esc(key)}" data-act="${act(()=>b21dPfSave(sid,x.k,true))}">Remplacer par ma saisie</button><button type="button" class="b21d-btn" data-b21d-pfkeep="${esc(key)}" data-act="${act(()=>{delete B21D.pf[key];B21D.ouvF[key]=false;render();})}">Garder la valeur enregistrée</button></div>`;
  if(ed&&x.k==="gerants"&&F.st!=="ok")h+=`<button type="button" class="b21d-btn" data-b21d-pfsave="${esc(key)}" data-act="${act(()=>b21dPfSave(sid,"gerants"))}">Enregistrer le signataire</button>`;
  return h+`<p class="b21d-src">Enregistré dans le profil de ${esc(socCourt(sid))} (coffre de la société), visible dans le Paramétrage et la Préparation. Aucune autre société n'est modifiée.</p></div>`;}
/* aller à la pièce précise du coffre de la société (rubrique dépliée, pièce mise en vue) */
function b21dCoffrePiece(sid,k){const i=SOC.findIndex(z=>z.sid===sid);let ci=-1;try{ci=VAULT.findIndex(([c,ps])=>ps.some(p=>p.k===k));}catch(e){}
  go(()=>{S.cur=i<0?0:i;S.soc=null;S.dept="coffre";S.cview="soc";S.filter="all";S.aoId=null;if(ci>=0)S.open["c"+ci]=true;});
  setTimeout(()=>{const e=[...document.querySelectorAll(".piece .nm")].find(n=>n.textContent.trim()===k);if(e){const r=e.closest(".piece");r.scrollIntoView({block:"center"});r.classList.add("b21d-cible");const b=r.querySelector("button,label");if(b&&b.focus)b.focus({preventScroll:true});}},60);}
function b21dPanneau(x,clos){const a=x.a,d=a.decision,ed=editable()&&!clos&&!["Déposé","Attribué","Non retenu"].includes(a.statut),H=(a.decisionHist||[]).slice().reverse();
  const cls=!d?"b21d-neu":d.verdict==="Go"?"b21d-ok":d.verdict==="No-Go"?"b21d-ko":"b21d-amb";
  let h=`<aside class="b21d-dec" aria-label="Votre décision pour ${esc(socCourt(x.sid))}"><h4>Votre décision</h4><p><span class="b21d-pill ${cls} b21d-big" data-b21d-verdict="${esc(d?d.verdict:"aucune")}">${esc(d?d.verdict:"Aucune décision")}</span></p><p class="b21d-src">${esc(b21dDecTxt(d))}</p>`;
  if(ed){const v=B21D.motif[x.oid]||"",c=B21D.conf&&B21D.conf.k.startsWith(x.oid+"|")?B21D.conf.k.split("|")[1]:null;
    const GB=b21dGoBloc(x.oid),gb=GB.bloc.length>0;
    h+=`<div class="b21d-btns" role="group" aria-label="Décision">${["Go","No-Go","À reprendre"].map(V=>V==="Go"&&gb?`<button type="button" class="b21d-db" disabled aria-describedby="b21d-gb-${esc(x.oid)}" data-b21d-dec="Go">Go</button>`:`<button type="button" class="b21d-db${c===V?" b21d-arm":""}" aria-pressed="${!!(d&&d.verdict===V)}" data-b21d-dec="${esc(V)}" data-act="${act(()=>b21dDecider(x.oid,V))}">${c===V?"Confirmer « "+V+" »":V}</button>`).join("")}</div>`;
    {const PM=b21dProfMiss(x.sid).filter(z=>!z.fait);if(PM.length)h+=`<div class="b21d-pm" data-b21d-prepbloc="${PM.length}"><b>Préparation bloquée (pas le Go)</b> : profil de ${esc(socCourt(x.sid))} à compléter — ${esc(PM.map(z=>z.lab+(z.inv?" (format invalide)":"")).join(", "))}. Corrigeable dans « Prérequis société » ; ce n'est pas une non-éligibilité.</div>`;}
    if(gb)h+=`<div class="b21d-gb" id="b21d-gb-${esc(x.oid)}" data-b21d-gobloc="${GB.bloc.length}"><b>Go impossible en l'état (éligibilité)</b><ul>${GB.bloc.map(z=>`<li>${esc(z.t)}${z.src?`<small>Source : ${esc(z.src)}</small>`:""}</li>`).join("")}</ul></div>`;
    if(GB.verif.length)h+=`<details class="b21d-gv" data-b21d-goverif="${GB.verif.length}"><summary>Vérifications d'éligibilité requises (${GB.verif.length})</summary><p class="b21d-src">Non renseigné n'est pas inexistant : ces points sont à établir (coffre, RC) ; ils ne bloquent pas le Go.</p><ul>${GB.verif.map(z=>`<li>${esc(z.t)}${z.src?`<small>Source : ${esc(z.src)}</small>`:""}</li>`).join("")}</ul></details>`;
    h+=`
      <label class="b21d-lab">Motif <small>(obligatoire pour No-Go et À reprendre)</small><textarea rows="2" data-b21d-motif="${esc(x.oid)}" placeholder="Motif de votre décision">${esc(v)}</textarea></label>
      <p class="b21d-src">Go = participer et démarrer la préparation, pas un dossier complet : les pièces à préparer après le Go restent signalées et les contrôles avant dépôt s'appliquent. Aucun Go n'est proposé ni présélectionné.</p>`;}
  else h+=`<p class="b21d-src">${clos?"Consultation clôturée : décision en lecture seule, aucune nouvelle soumission.":!editable()?"Lecture seule.":"Dossier "+esc(a.statut)+" : décision figée."}</p>`;
  if(H.length)h+=`<details class="b21d-hist"><summary>Historique des décisions (${H.length})</summary><ul>${H.map(z=>`<li>${esc(b21dDecTxt(z))}<small>remplacée le ${esc(fmtDT(z.remplaceLe))} par ${esc(b21dQui(z.remplacePar))}</small></li>`).join("")}</ul></details>`;
  return h+`</aside>`;}
function b21dDetDossier(e,clos){const x=e.x,D=e.D,a=x.a;
  /* b21d-6 : périmètre avant dépôt seulement ; ni chiffrage (B3.1 / Préparation) ni pièces après attribution (Résultat B4.2) */
  const FR=D.F?{ajour:["b21d-ok","Lecture à jour"],perimee:["b21d-ko","Note à actualiser"],inconnue:["b21d-amb","Fraîcheur non vérifiée"],absente:["b21d-amb","Aucune lecture"]}[D.F.k]:null;
  let h=`<header class="b21d-ch"><p class="b21d-src">Dossier séparé · ${esc(a.statut||"")} · ${esc(a.ref||x.oid)}</p>${FR?`<span class="b21d-pill ${FR[0]}" title="${esc(D.F.txt)}">${FR[1]}</span>`:""}</header><div class="b21d-body"><div class="b21d-main">`;
  h+=b21dPrereqTable(D,x)+(D.rcOk?b21dPrepTable(D,x):`<p class="b21d-warn">Pièces du RC non relevées pour ce dossier : liste indisponible (aucune pièce supposée). <button type="button" class="b21d-lnk" data-act="${act(()=>b21dAller(x.oid,"MP-B2.2","note"))}">Ouvrir la lecture RC / CPS</button></p>`);
  const nAtt=D.rows.filter(z=>z.env==="att").length;
  h+=`<p class="b21d-src" data-b21d-perim="1">Prérequis société : données et preuves propres à ${esc(socCourt(x.sid))} sans lesquelles l'équipe ne peut pas préparer correctement. Les pièces « À préparer après Go » sont produites en Préparation et restent exigées avant le dépôt (contrôles du dépôt inchangés)${nAtt?` ; les ${nAtt} pièce${nAtt>1?"s":""} exigée${nAtt>1?"s":""} de l'attributaire sont dans la vue <button type="button" class="b21d-lnk" data-b21d-vres="1" data-act="${act(()=>b21dAller(x.oid,"MP-B4.2","res"))}">Résultat (B4.2)</button>`:""}.</p>`;
  h+=b21dCompatDet(e.c,x.oid)+`<p class="b21d-src">Sources : pièces du RC lues (${esc(D.rcId)}), coffre et pièces de ${esc(socCourt(x.sid))}. ${D.F?esc(D.F.txt):""}</p></div>${b21dPanneau(x,clos)}</div>`;
  return h;}
function b21dPrereqTable(D,x){const sid=x.sid,nm=socCourt(sid),ed=editable();
  let h=`<section class="b21d-sct" data-b21d-prereq="${D.nPre}" aria-labelledby="b21d-pr-${esc(sid)}"><h4 id="b21d-pr-${esc(sid)}">Prérequis société à compléter <span class="b21d-pill ${D.nPre?"b21d-amb":"b21d-ok"}">${D.nPre?D.nPre+" en attente":"aucun en attente"}</span></h4>`;
  h+=`<div class="b21d-tw"><table class="b21d-tab" aria-label="Prérequis de ${esc(nm)} : élément, statut, action"><caption class="b21d-sr">Prérequis société de ${esc(nm)} (profil et coffre)</caption><thead><tr><th scope="col">Élément</th><th scope="col">Statut</th><th scope="col">Action</th></tr></thead><tbody>`;
  if(D.prof.length){h+=`<tr class="b21d-sec"><th colspan="3" scope="colgroup">Profil de la société (champs requis du Paramétrage)</th></tr>`;
    D.prof.forEach(z=>{const key=sid+"|"+z.k,F=B21D.pf[key],o=!!B21D.ouvF[key],k=z.fait||(F&&F.st==="ok")?"prof":z.inv?"pinv":"arens",S2=B21D_PST[k];
      h+=`<tr data-b21d-pk="${k}" data-b21d-pfk="${esc(z.k)}"><td><b>${esc(z.lab)}</b><small>${z.inv?"Valeur enregistrée au mauvais format":k==="prof"?"Renseigné depuis cette vue":"Non renseigné au profil : nécessaire pour préparer les pièces au nom de la société"}</small><small class="b21d-src">Source : Paramétrage des sociétés (profil de ${esc(nm)})</small></td><td><span class="b21d-pill ${S2[0]}">${S2[1]}</span></td>
        <td>${ed?`<button type="button" class="b21d-act" aria-expanded="${o}" aria-controls="b21d-pfr-${esc(sid)}-${esc(z.k)}" data-b21d-saisir="${esc(key)}" data-act="${act(()=>b21dPfOuvrir(sid,z.k))}">${o?"Fermer":k==="prof"?"Modifier":"Saisir"}<small>profil ${esc(nm)}</small></button>`:`<span class="b21d-na">Lecture seule</span>`}</td></tr>`;
      h+=`<tr class="b21d-pfrow" id="b21d-pfr-${esc(sid)}-${esc(z.k)}"${o?"":" hidden"}><td colspan="3">${o?b21dPfForm(sid,z):""}</td></tr>`;});}
  if(D.pre.length){h+=`<tr class="b21d-sec"><th colspan="3" scope="colgroup">Preuves du coffre exigées par le RC</th></tr>`;
    D.pre.forEach(z=>{const S2=B21D_PST[z.k]||B21D_PST.averif,lab=z.k==="nonrens"?"Joindre au coffre":z.k==="invalide"?"Mettre à jour":z.k==="joint"?"Ouvrir":"Vérifier";
      h+=`<tr data-b21d-pk="${z.k}" data-b21d-std="${esc(z.std)}"><td><b>${esc(z.piece)}</b>${z.ctrl?`<small>${esc(z.ctrl)}</small>`:""}${z.k==="joint"?`<small>Justificatif joint et en validité ; son contenu n'est pas vérifié automatiquement</small>`:""}${z.src?`<small class="b21d-src">Source : ${esc(z.src)}</small>`:""}</td><td><span class="b21d-pill ${S2[0]}">${S2[1]}</span></td>
        <td><button type="button" class="b21d-act" data-b21d-go="coffre" data-b21d-vk="${esc(z.vk||"")}" data-act="${act(()=>b21dCoffrePiece(sid,z.vk))}">${lab}<small>coffre ${esc(nm)}</small></button></td></tr>`;});}
  if(!D.prof.length&&!D.pre.length)h+=`<tr><td colspan="3"><span class="b21d-na">Aucun prérequis société relevé pour ce dossier.</span></td></tr>`;
  return h+`</tbody></table></div></section>`;}
function b21dPrepTable(D,x){const sid=x.sid,nm=socCourt(sid),sec=[["e1","adm","Enveloppe 1 · Dossier administratif"],["e1","tec","Enveloppe 1 · Dossier technique"],["e1","aut","Enveloppe 1 · Autres pièces du RC"],["e2","fin","Enveloppe 2 · Offre financière"]];
  let h=`<section class="b21d-sct" data-b21d-aprep-sec="${D.nPrep}" aria-labelledby="b21d-ap-${esc(sid)}"><h4 id="b21d-ap-${esc(sid)}">À préparer après Go · requis avant dépôt <span class="b21d-pill b21d-neu">${D.nPrep} pièce${D.nPrep>1?"s":""}</span></h4><p class="b21d-src">Produites en Préparation après le Go (signatures, cachets, déclarations, mémoire, acte d'engagement, bordereau, récépissé de caution…). Elles ne bloquent pas le Go ; elles restent contrôlées avant le dépôt.</p>`;
  h+=`<div class="b21d-tw"><table class="b21d-tab" aria-label="Pièces de ${esc(nm)} à préparer : pièce, statut, action"><caption class="b21d-sr">Pièces à préparer après le Go pour ${esc(nm)}</caption><thead><tr><th scope="col">Pièce</th><th scope="col">Statut</th><th scope="col">Action</th></tr></thead><tbody>`;
  sec.forEach(([e,s2,t])=>{const R2=D.prep.filter(z=>z.env===e&&z.sec===s2);if(!R2.length)return;h+=`<tr class="b21d-sec"><th colspan="3" scope="colgroup">${esc(t)}</th></tr>`;
    R2.forEach(z=>{const S2=B21D_ST[z.k]||B21D_ST.prep2;h+=`<tr data-b21d-k="${z.k}"><td><b>${esc(z.piece)}</b>${z.ctrl&&z.k!=="prep2"?`<small>${esc(z.ctrl)}</small>`:""}${z.src?`<small class="b21d-src">Source : ${esc(z.src)}</small>`:""}</td><td><span class="b21d-pill ${S2[0]}">${S2[1]}</span></td><td>${z.k==="nonexige"?`<span class="b21d-na">—</span>`:`<button type="button" class="b21d-act" data-b21d-go="pieces" data-act="${act(()=>b21dAller(x.oid,"MP-B3.2","pieces"))}">Préparation<small>pièces B3.2</small></button>`}</td></tr>`;});});
  return h+`</tbody></table></div></section>`;}
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
function b21dHorsAO(id,a,X){const have=new Set(X.map(x=>x.sid)),ed=editable(),passe=b21dPasse(a),fig=["Déposé","Attribué","Non retenu"].includes(a.statut);
  return SOC.filter(z=>z&&z.sid&&!have.has(z.sid)).map((z,i)=>{const c=b21dCompat(id,a,z.sid);let pc;try{pc=parCompat(id,a,z.sid);}catch(e){pc={st:"non",why:"contrôle art. 27 / FIN-ISO-001 indisponible"};}
    const bloc=passe?"consultation clôturée le "+fmtIso(a.lim)+(a.heure?" "+a.heure:"")+", date limite passée.":!ed?"lecture seule.":fig?"dossier "+a.statut.toLowerCase()+".":(pc.st==="non"||pc.st==="deja")?(pc.why||"règles du marché."):null;
    return{sid:z.sid,c,pc,bloc,o:(B21D_CMP[c.v]||B21D_CMP["À vérifier"])[0],i};}).sort((x,y)=>x.o-y.o||x.i-y.i);}
function b21dCompatDet(c,oid){const n=c.n,M=c.contre||[];
  let h=`<div class="b21d-cd"><p class="b21d-mc"><b>Compatibilité RC (informative, B2.3)</b>${n?`<span class="b21d-src" data-b21d-n="${n.ok}/${n.ko}/${n.inc}">${n.ok} justifié${n.ok>1?"s":""} · ${n.ko} incompatible${n.ko>1?"s":""} · ${n.inc} à vérifier</span>`:""}</p>`;
  if(M.length)h+=`<ul class="b21d-mot" data-b21d-motifs="${M.length}">${M.slice(0,3).map(t=>`<li>${esc(t)}</li>`).join("")}${M.length>3?`<li class="b21d-src">… et ${M.length-3} autre${M.length-3>1?"s":""} motif${M.length-3>1?"s":""} (détail dans B2.3)</li>`:""}</ul>`;
  return h+`<button type="button" class="b21d-lnk" data-act="${act(()=>b21dAller(oid,"MP-B2.3","note"))}">Compatibilité détaillée (B2.3)</button></div>`;}
function b21dDetHors(id,y){const arm=!!(B21D.conf&&B21D.conf.k==="add|"+y.sid&&Date.now()-B21D.conf.t<=6000);
  let h=b21dCompatDet(y.c,id);
  if(y.pc.st==="attention"&&!y.bloc)h+=`<p class="b21d-warn" data-b21d-attn="1">${esc(y.pc.why)}</p>`;
  h+=`<div class="b21d-ma">`+(y.bloc?`<button type="button" class="b21d-btn" disabled aria-describedby="b21d-bl-${esc(y.sid)}" data-b21d-ajout="${esc(y.sid)}">Ajouter à cet AO</button><span class="b21d-src" id="b21d-bl-${esc(y.sid)}" data-b21d-bloque="1">Ajout bloqué : ${esc(y.bloc)}</span>`
    :`<button type="button" class="b21d-btn${arm?" b21d-arm":""}" data-b21d-ajout="${esc(y.sid)}" data-act="${act(()=>b21dAjouter(id,y.sid))}">${arm?"Confirmer l'ajout de "+esc(socCourt(y.sid)):"Ajouter à cet AO"}</button><span class="b21d-src">Crée seulement son dossier séparé, sans décision ni Go.</span>`)+`</div>`;
  return h;}
/* b21d-5 : cartes repliées par défaut, une seule ouverte à la fois, filtres. État d'affichage seulement (B21D.ui), propre au dossier
   affiché, jamais enregistré ; ouvrir, fermer ou filtrer n'écrit rien et ne décide rien. Détails rendus seulement pour la carte ouverte. */
const B21D_F=[["tout","Tout"],["ajoutees","Ajoutées"],["compat","Compatibles"],["averif","À vérifier"],["incompat","Incompatibles"]];
const b21dCat=v=>v==="Possible"?"compat":v==="Écartée"?"incompat":"averif";
const b21dDans=(k,f)=>!!k&&(f==="tout"||(f==="ajoutees"?k.aj:k.cat===f));
function b21dUi(id){if(B21D.ui.id!==id){B21D.ui={id,open:null,f:"tout"};B21D.conf=null;}return B21D.ui;}
function b21dFocus(sel){setTimeout(()=>{const b=document.querySelector(sel);if(b)b.focus({preventScroll:true});},0);}
function b21dToggle(sid){const u=B21D.ui;u.open=u.open===sid?null:sid;B21D.conf=null;render();b21dFocus('[data-b21d-tog="'+CSS.escape(sid)+'"]');}
function b21dFiltre(f){const u=B21D.ui;u.f=f;if(u.open&&!b21dDans(B21D.cat[u.open],f))u.open=null;B21D.conf=null;render();b21dFocus('[data-b21d-f="'+f+'"]');}
function b21dMontrer(sid,motif){const u=B21D.ui;u.open=sid;if(!b21dDans(B21D.cat[sid],u.f))u.f="tout";B21D.conf=null;render();
  setTimeout(()=>{const e=document.querySelector('[data-b21d-carte="'+CSS.escape(sid)+'"]');if(!e)return;e.scrollIntoView({behavior:"smooth",block:"start"});const t=(motif&&e.querySelector("[data-b21d-motif]"))||e.querySelector("[data-b21d-tog]");if(t)setTimeout(()=>t.focus({preventScroll:true}),350);},0);}
function b21dCarteR(id,e,clos,open){const sid=e.sid,C=B21D_CMP[e.c.v]||B21D_CMP["À vérifier"],did="b21d-det-"+sid,a=e.x&&e.x.a,d=a&&a.decision,nm=socCourt(sid);
  const r=e.x?e.D.reste.length:null,dcls=!d?"b21d-neu":d.verdict==="Go"?"b21d-ok":d.verdict==="No-Go"?"b21d-ko":"b21d-amb";
  const at=e.x?`id="b21d-${esc(e.x.oid)}" data-b21d-soc="${esc(sid)}" data-b21d-oid="${esc(e.x.oid)}"`:`data-b21d-hors="${esc(sid)}"`;
  let h=`<article class="b21d-card${e.x?"":" b21d-mini"}" ${at} data-b21d-carte="${esc(sid)}" data-b21d-compat="${esc(e.c.v)}" data-b21d-ouvert="${open?1:0}"><div class="b21d-sum">
    <h3 id="b21d-nm-${esc(sid)}">${esc(nm)}</h3><button type="button" class="b21d-btn b21d-tog" aria-expanded="${open}" aria-controls="${did}" data-b21d-tog="${esc(sid)}" data-act="${act(()=>b21dToggle(sid))}">${open?"Masquer les détails":"Afficher les détails"}<span class="b21d-sr"> de ${esc(nm)}</span></button>
    <div class="b21d-chips"><span class="b21d-pill ${e.x?"b21d-ok":"b21d-neu"}" data-b21d-aj="${e.x?1:0}">${e.x?"Ajoutée à cet AO":"Pas encore ajoutée à cet AO"}</span><span class="b21d-pill ${C[1]}" data-b21d-cv="1">Compatibilité RC : ${C[2]}</span>`
    +(e.x?`<span class="b21d-pill ${r?"b21d-amb":"b21d-ok"}" data-b21d-reste="${r}">${r?r+" prérequis société":"Prérequis société : aucun en attente"}</span><span class="b21d-pill b21d-neu" data-b21d-aprep="${e.D.nPrep}">${e.D.nPrep} à préparer après Go</span>${(()=>{const n=b21dGoBloc(e.x.oid).bloc.length;return n?`<span class="b21d-pill b21d-ko" data-b21d-sgobloc="${n}">Go bloqué : ${n} raison${n>1?"s":""}</span>`:"";})()}`:`<span class="b21d-pill b21d-neu" data-b21d-reste="">Aucun dossier</span>`)
    +`<span class="b21d-pill ${dcls}" data-b21d-sdec="${esc(d?d.verdict:"aucune")}">${d?"Décision : "+esc(d.verdict)+(d.le?" · "+esc(fmtIso(d.le)):""):"Non décidée"}</span></div></div>`;
  h+=`<div class="b21d-det" id="${did}" role="region" aria-labelledby="b21d-nm-${esc(sid)}"${open?"":" hidden"}>${open?(e.x?b21dDetDossier(e,clos):b21dDetHors(id,e)):""}</div></article>`;
  return h;}
async function b21dAjouter(id,sid){const a=S.ao[id];if(!a)return;if(!editable())return toast(RO_MSG);
  if(b21dPasse(a))return toast("Consultation clôturée : date limite passée, aucun ajout.");
  if(["Déposé","Attribué","Non retenu"].includes(a.statut))return toast("Dossier "+a.statut.toLowerCase()+" : aucun ajout.");
  if(b21dSibs(id,a).some(x=>x.sid===sid))return toast(socCourt(sid)+" a déjà son dossier pour cet AO : rien n'est créé.");
  let pc;try{pc=parCompat(id,a,sid);}catch(e){return toast("Contrôle art. 27 / FIN-ISO-001 impossible : rien n'est créé.");}
  if(pc.st==="non"||pc.st==="deja")return toast(pc.why||"Ajout bloqué par les règles du marché.");
  const k="add|"+sid;if(!B21D.conf||B21D.conf.k!==k||Date.now()-B21D.conf.t>6000){B21D.conf={k,t:Date.now()};render();return toast("Ajouter "+socCourt(sid)+" à cet AO : son dossier séparé sera créé sans décision (aucun Go)"+(pc.st==="attention"?" ; "+pc.why:"")+". Appuyez encore une fois pour confirmer.");}
  B21D.conf=null;if(B21D.ajout)return toast("Ajout en cours, patientez.");B21D.ajout=sid;
  try{await creerSib(id,sid,{sansGo:true,source:"B2.1 Décision · ajout de société"});}finally{B21D.ajout=null;}}
function vDecisionB21(id,a){b21dCss();const X=b21dSibs(id,a),clos=b21dClos(a),lim=b21dLim(a),ed=editable(),Y=b21dHorsAO(id,a,X),nA=new Set(X.map(x=>x.sid)).size,nT=nA+Y.length;
  let h=`<div class="b21d" data-b21d="${esc(id)}"><header class="b21d-top"><div><p class="b21d-src b21d-ref">${esc(a.ref||id)} · ${esc(String(a.obj||"").slice(0,120))}</p></div>
    <div class="b21d-cm">${lim?`<span class="b21d-pill ${clos?"b21d-ko":"b21d-neu"}" data-b21d-clos="${clos}">${clos?"Consultation clôturée le ":"Date limite : "}${esc(fmtIso(a.lim))}${a.heure?" "+esc(a.heure):""}</span>`:`<span class="b21d-pill b21d-amb">Date limite non renseignée</span>`}<span class="b21d-pill b21d-neu" data-b21d-compte="${nA}/${nT}">${nA} / ${nT} société${nT>1?"s":""} ajoutée${nA>1?"s":""} à cet AO</span><button type="button" class="b21d-btn" data-b21d-maj="1" data-act="${act(()=>{try{delete B21.cache;}catch(e){}render();toast("État et documents relus ; aucune décision modifiée.");})}">Actualiser</button></div></header>`;
  h+=`<p class="b21d-intro">Toutes les sociétés actuelles du groupe. Chaque société ajoutée a son propre dossier, ses pièces et ses prix (FIN-ISO-001). L'état des pièces (administratif) et la compatibilité (informative, B2.3) sont distincts de votre décision commerciale Go / No-Go.</p>`;
  /* b21d-3 : la note d'analyse n'est pas rendue ici ; navigation vers sa propre vue (même dossier, même société) par le routage existant */
  h+=`<div class="b21d-noteb"><button type="button" class="b21d-btn" data-b21d-voirnote="1" data-act="${act(()=>b21Aller(id,"note"))}">Voir la note d'analyse</button><span class="b21d-src">L'avis de l'Analyste, daté et sourcé, et la lecture du DCE sont dans la note d'analyse (bureau B2.1) ; cette vue n'en reprend ni l'avis ni le classement des sociétés.</span></div>`;
  /* b21d-5 : une seule liste, ordre b21d-4 (ajoutées, puis compatibles, à vérifier, incompatibles), filtres et carte ouverte */
  const u=b21dUi(id),E=X.map(x=>({sid:x.sid,x,c:b21dCompat(x.oid,x.a,x.sid),D:b21dCarteData(x.oid,x.a,x.sid)})).concat(Y);
  B21D.cat={};E.forEach(e=>{if(!B21D.cat[e.sid])B21D.cat[e.sid]={aj:!!e.x,cat:b21dCat(e.c.v)};});
  if(u.open&&!E.some(e=>e.sid===u.open&&b21dDans(B21D.cat[e.sid],u.f)))u.open=null;
  const NF=Object.fromEntries(B21D_F.map(([k])=>[k,E.filter(e=>b21dDans(B21D.cat[e.sid],k)).length])),F=E.filter(e=>b21dDans(B21D.cat[e.sid],u.f)),fl=(B21D_F.find(z=>z[0]===u.f)||B21D_F[0])[1];
  h+=`<section class="b21d-socs" aria-labelledby="b21d-st"><h3 id="b21d-st">Sociétés du groupe</h3><p class="b21d-resume" data-b21d-resume="${E.length}/${nA}/${E.length-nA}">${E.length} société${E.length>1?"s":""} · ${nA} ajoutée${nA>1?"s":""} · ${E.length-nA} non ajoutée${E.length-nA>1?"s":""}</p>
    <div class="b21d-filt" role="group" aria-label="Filtrer les sociétés">${B21D_F.map(([k,l])=>`<button type="button" class="b21d-fb" aria-pressed="${u.f===k}" data-b21d-f="${k}" data-b21d-fn="${NF[k]}" data-act="${act(()=>b21dFiltre(k))}">${l} <span class="b21d-fn">${NF[k]}</span></button>`).join("")}</div>
    <p class="b21d-src b21d-fst" role="status" aria-live="polite" data-b21d-fstat="${u.f}">Filtre « ${esc(fl)} » : ${F.length} société${F.length>1?"s":""} affichée${F.length>1?"s":""} sur ${E.length}. La compatibilité est informative (B2.3) et ne vaut pas décision ; Go, No-Go et Ajouter se trouvent dans les détails de chaque carte.</p>`;
  h+=F.length?`<div class="b21d-list">${F.map(e=>b21dCarteR(id,e,clos,u.open===e.sid)).join("")}</div>`:`<p class="b21d-vide" data-b21d-vide="1">Aucune société dans le filtre « ${esc(fl)} » pour cet AO. <button type="button" class="b21d-lnk" data-act="${act(()=>b21dFiltre("tout"))}">Tout afficher</button></p>`;
  h+=`</section>`;
  const G=X.filter(x=>x.a.decision&&x.a.decision.verdict==="Go"&&!["Abandonné","Non retenu","À examiner"].includes(x.a.statut));
  h+=`<section class="b21d-ret" aria-labelledby="b21d-rt"><h3 id="b21d-rt">Entreprises retenues pour la préparation</h3>`;
  h+=G.length?`<ul class="b21d-rl">${G.map(x=>`<li data-b21d-ret="${esc(x.sid)}"><div><b>${esc(socCourt(x.sid))}</b><small>${esc(b21dDecTxt(x.a.decision))} · ${esc(x.a.statut)}</small></div><div class="b21d-rla"><button type="button" class="b21d-btn" data-b21d-modifier="${esc(x.sid)}" data-act="${act(()=>b21dMontrer(x.sid,true))}">Modifier</button>${ed&&!clos?`<button type="button" class="b21d-btn" data-b21d-retirer="${esc(x.sid)}" data-act="${act(()=>{if(!String(B21D.motif[x.oid]||"").trim()){b21dMontrer(x.sid,true);return toast("Retirer = « À reprendre » : saisissez d'abord le motif dans la carte de "+socCourt(x.sid)+".");}b21dDecider(x.oid,"À reprendre");})}">Retirer</button>`:""}</div></li>`).join("")}</ul>`:`<p class="b21d-src">Aucune entreprise avec un Go enregistré.</p>`;
  h+=`</section>`;
  let st="";try{const o=aoDecision(id,a),i=o.indexOf('<div class="grp">Statut du dossier</div>');st=i>=0?o.slice(i):"";}catch(e){}
  if(st)h+=`<details class="b21d-note"><summary>Statut administratif du dossier ${esc(socCourt(a.soc))} (existant)</summary>${st}</details>`;
  return h+`</div>`;}
/* vue pleine largeur dans le bureau B2.1 (décision à droite sur ordinateur) : même mécanisme que B3.1 */
function b21dPlein(id){return typeof MPN!=="undefined"&&!!MPN.dos&&MPN.dos.id===id&&MPN.dos.bur==="MP-B2.1"&&MPN.dos.k==="dec"&&!MPN.dos.global&&S.aoId===id;}
{const _mpnDossierB21D=mpnDossier;mpnDossier=function(d){const h=_mpnDossierB21D(d);try{const id=S.aoId;if(!id||!b21dPlein(id)||h.indexOf("b31-full")>=0)return h;b31Css();
  const t=h.replace('<div class="mpn" data-mpn-dossier-vue=','<div class="mpn b31-full b21d-full" data-mpn-dossier-vue=');return t.indexOf("b21d-full")<0?h:t;}catch(e){return h;}};}
{const _aoStepsB21D=aoSteps;aoSteps=function(id,a){const L=_aoStepsB21D(id,a),n=L.find(s=>s.k==="dec");if(n)n.body=()=>vDecisionB21(id,a);
  const r=L.find(s=>s.k==="res");if(r&&r.body){const b0=r.body;r.body=()=>{let x="";try{x=vApresAttribB21(id,a);}catch(e){x="";}return b0()+x;};}return L;};}
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.b21dMotif!=null)B21D.motif[t.dataset.b21dMotif]=t.value;
  if(t&&t.dataset&&t.dataset.b21dPf){const key=t.dataset.b21dPf,F=B21D.pf[key];if(!F)return;F.v=t.value;F.dirty=true;if(F.st!=="saving"){F.st="edit";}clearTimeout(F.t);const[sid,k]=key.split("|");F.t=setTimeout(()=>{if(document.activeElement!==t||b21dPfNorm(k,F.v)!==F.saved)b21dPfSave(sid,k);},1500);}
  if(t&&t.dataset&&t.dataset.b21dPfg){const[sid,k,f]=t.dataset.b21dPfg.split("|"),F=B21D.pf[sid+"|"+k];if(F&&F.v&&typeof F.v==="object"){F.v[f]=t.value;F.dirty=true;}}});
document.getElementById("view").addEventListener("change",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.b21dPfg){const[sid,k,f]=t.dataset.b21dPfg.split("|"),F=B21D.pf[sid+"|"+k];if(F&&F.v&&typeof F.v==="object")F.v[f]=t.value;}});
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
.b21d-noteb{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.b21d-noteb .b21d-src{margin:0;flex:1 1 260px}
.b21d-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@container b21d (max-width:560px){.b21d-tab th,.b21d-tab td{padding:6px 4px}.b21d-tab td:nth-child(2){width:84px}.b21d-tab td:nth-child(3){width:86px}.b21d-tab .b21d-pill{white-space:normal;font-size:11px;padding:2px 7px}.b21d-tab .b21d-act{padding:4px 6px;max-width:100%}.b21d-tab .b21d-act small{display:none}.b21d-tab{table-layout:fixed}.b21d-tab th:nth-child(2),.b21d-tab td:nth-child(2){width:84px}.b21d-tab th:nth-child(3),.b21d-tab td:nth-child(3){width:78px}.b21d-tab td{overflow-wrap:anywhere}.b21d-tab th:nth-child(3),.b21d-tab td:nth-child(3){width:96px}.b21d-tab td:nth-child(3) .b21d-act{overflow-wrap:normal;word-break:keep-all;font-size:11.5px;padding:4px 6px}}`;
function b21dCss(){if(document.getElementById("b21d-css"))return;const s=document.createElement("style");s.id="b21d-css";s.textContent=B21D_CSS;document.head.appendChild(s);}
