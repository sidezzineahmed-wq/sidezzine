/* ================= B2.1 · Décision d'Ahmed par société (b21d-1) =================
   Une carte par société candidate : chaque société a son propre dossier (ao/<base>~<société>, FIN-ISO-001) ; la carte ne lit que les
   pièces, l'état et les prix de CE dossier. Pièces : liste construite depuis les pièces du RC (b21Check) et les preuves existantes
   (coffre, pièces cachetées vérifiées, chiffrage B3.1) ; « Prêt » seulement sur preuve vérifiée. Décision : modèle existant
   a.decision {verdict, le, qui, motif} ; jamais de Go automatique ni de présélection ; une décision remplacée est conservée
   (a.decisionHist) et tracée au journal ; la société d'un dossier n'est jamais changée ici. L'avis et la recommandation de
   l'Analyste restent dans la note d'analyse. Consultation clôturée : décision affichée en lecture, aucune nouvelle soumission. */
const B21D={v:"b21d-2",motif:{},conf:null};
const B21D_ST={chiffre:["b21d-amb","Chiffré · à valider"],chval:["b21d-ok","Chiffré · validé"],pret:["b21d-ok","Prêt"],verif:["b21d-amb","À vérifier"],joindre:["b21d-ko","À joindre"],compl:["b21d-amb","À compléter"],nonexige:["b21d-neu","Non exigé"],attrib:["b21d-neu","Si attribué"]};
const B21D_COFFRE=["qc","refs","fis","cnss","rc","pouvoirs"],B21D_FIN=["bpu","sdp"];   /* l'acte d'engagement se prépare dans les pièces (B3.2) */
/* b21d-2 : état du chiffrage de LA société, sans aucun montant (FIN-ISO-001) : couverture des PU et validation seulement */
function b21dChiffrage(oid,a){if(!S.bp[oid])return null;try{const ET=b31Etat(oid,a),T=ET.T;return{n:T.n,N:T.n+T.miss,complet:!T.miss&&T.n>0,valide:!!ET.valide,tva:ET.tva.ok,statut:ET.statut.k};}catch(e){return null;}}
function b21dSibs(id,a){let L=[];try{L=b31Sibs(id,a);}catch(e){L=[{id,soc:a.soc,statut:a.statut}];}return L.map(s=>({oid:s.id,sid:s.soc,a:S.ao[s.id]})).filter(x=>x.a&&x.sid);}
function b21dRcId(oid,a){return[oid,a.base].filter(Boolean).find(x=>S.rc[x]&&Array.isArray(S.rc[x].pieces)&&S.rc[x].pieces.length)||oid;}
function b21dLim(a){if(!a.lim)return null;const m=String(a.heure||"").match(/(\d{1,2})\s*[hH:]\s*(\d{2})?/),d=new Date(a.lim+"T"+(m?String(m[1]).padStart(2,"0")+":"+(m[2]||"00"):"23:59")+":00");return isNaN(d)?null:d;}
const b21dClos=a=>{const d=b21dLim(a);return!!d&&d<new Date()&&!["Déposé","Attribué","Non retenu"].includes(a.statut);};
/* statut d'une pièce : « Prêt » uniquement sur preuve vérifiée */
function b21dPiece(row,p,oa,sid,CH){const std=p&&p.std,st=row.st,dp=oa.dcePieces||{},F=oa.fichiers||{};
  if(std==="bpu"&&CH&&CH.n){const cov=CH.n+"/"+CH.N+" PU saisis";
    if(CH.valide)return{k:"chval",ctrl:"Couverture "+cov+" · chiffrage validé (offre figée) ; signature et cachet du bordereau restent à faire"};
    if(CH.complet)return{k:"chiffre",ctrl:"Couverture "+cov+" · chiffrage non validé"+(CH.tva?"":" ; TVA non confirmée")+" ; signature et cachet restent à faire"};
    return{k:"compl",ctrl:"Couverture "+cov+" : "+(CH.N-CH.n)+" PU à saisir"};}
  if(std==="cpsrc"){const ok=["cps","rc"].every(k=>dp[k]&&dp[k].cachete&&dp[k].cachete.soc===sid&&dp[k].cachete.statut==="VÉRIFIÉ");
    if(ok)return{k:"pret",ctrl:"CPS et RC paraphés et cachetés au nom de "+socCourt(sid)+" : statut VÉRIFIÉ"};}
  if(std==="refs"&&F.refs&&F.refs.soc===sid&&F.refs.statut==="VÉRIFIÉ")return{k:"pret",ctrl:"Attestations de référence jointes au nom de "+socCourt(sid)+" : statut VÉRIFIÉ"};
  if(st==="nonexige")return{k:"nonexige"};if(st==="attrib")return{k:"attrib"};
  if(st==="dispo")return{k:B21D_COFFRE.includes(std)?"pret":"verif"};
  if(st==="manquant"||st==="bloquant")return{k:"joindre"};if(st==="remplir")return{k:"compl"};return{k:"verif"};}
function b21dAller(oid,bur,k){if(typeof MPN!=="undefined"&&MPN.dos&&typeof mpnDosAller==="function"){S.aoId=oid;MPN.dos=Object.assign({},MPN.dos,{id:oid});mpnDosAller(bur,k);}else{S.aoId=oid;S.stepOpen={...(S.stepOpen||{}),[oid]:k};}
  render();window.scrollTo(0,0);if(typeof mpdFocus==="function")mpdFocus("#mpn-h");}
function b21dAction(row,p,K,oid,sid){const std=p&&p.std,lab=K==="pret"||K==="chiffre"||K==="chval"?"Ouvrir":K==="joindre"?"Joindre":K==="compl"?(B21D_FIN.includes(std)||std==="memoire"||std==="moyens"||std==="planning"?"Saisir":"Compléter"):"Vérifier";
  if(K==="nonexige"||K==="attrib")return"";
  if(B21D_COFFRE.includes(std))return`<button type="button" class="b21d-act" data-b21d-go="coffre" data-act="${act(()=>go(()=>{S.soc=sid;S.dept=null;}))}">${lab}<small>coffre ${esc(socCourt(sid))}</small></button>`;
  if(B21D_FIN.includes(std))return`<button type="button" class="b21d-act" data-b21d-go="prix" data-act="${act(()=>b21dAller(oid,"MP-B3.1","prix"))}">${lab}<small>chiffrage B3.1</small></button>`;
  return`<button type="button" class="b21d-act" data-b21d-go="pieces" data-act="${act(()=>b21dAller(oid,"MP-B3.2","pieces"))}">${lab}<small>pièces B3.2</small></button>`;}
function b21dCarteData(oid,oa,sid){const rcId=b21dRcId(oid,oa),r=S.rc[rcId]||{},P=Array.isArray(r.pieces)?r.pieces:[];let rows=[];try{rows=b21Check(rcId,oa,sid);}catch(e){rows=[];}
  const env={"Administratif":["e1","adm"],"Technique":["e1","tec"],"Technique (offre technique)":["e1","tec"],"Financier":["e2","fin"],"Si attribué":["att","att"]};
  const CH=b21dChiffrage(oid,oa);
  const L=rows.filter(x=>x.pi!=null||x.st==="nonrens").map(x=>{const p=x.pi!=null?P[x.pi]:null,K=p?b21dPiece(x,p,oa,sid,CH):{k:"verif"},e=env[x.g]||["e1","aut"];
    return{piece:x.piece,ctrl:K.ctrl||x.ctrl,k:K.k,src:x.src,std:p&&p.std,env:e[0],sec:e[1],act:p?b21dAction(x,p,K.k,oid,sid):""};});
  return{rcId,CH,rows:L,reste:L.filter(x=>!["pret","nonexige","attrib"].includes(x.k)),rcOk:P.length>0,F:(()=>{try{return b21Fraicheur(rcId,oa);}catch(e){return null;}})()};}
function b21dTable(D,sid){const sec=[["e1","adm","Enveloppe 1 · Dossier administratif"],["e1","tec","Enveloppe 1 · Dossier technique"],["e1","aut","Enveloppe 1 · Autres pièces du RC"],["e2","fin","Enveloppe 2 · Offre financière"],["att","att","Après attribution (si le marché est attribué)"]];
  let h=`<div class="b21d-tw"><table class="b21d-tab" aria-label="Pièces de ${esc(socCourt(sid||""))} : pièce, statut, action"><caption class="b21d-sr">Pièces du dossier de ${esc(socCourt(sid||""))} selon le RC</caption><thead><tr><th scope="col">Pièce</th><th scope="col">Statut</th><th scope="col">Action</th></tr></thead><tbody>`;
  sec.forEach(([e,s,t])=>{const R=D.rows.filter(x=>x.env===e&&x.sec===s);if(!R.length)return;h+=`<tr class="b21d-sec"><th colspan="3" scope="colgroup">${esc(t)}</th></tr>`;
    R.forEach(x=>{const S2=B21D_ST[x.k]||B21D_ST.verif;h+=`<tr data-b21d-k="${x.k}"><td><b>${esc(x.piece)}</b>${x.ctrl?`<small>${esc(x.ctrl)}</small>`:""}${x.src?`<small class="b21d-src">Source : ${esc(x.src)}</small>`:""}</td><td><span class="b21d-pill ${S2[0]}">${S2[1]}</span></td><td>${x.act||`<span class="b21d-na">—</span>`}</td></tr>`;});});
  return h+`</tbody></table></div>`;}
const b21dQui=q=>q?(q===S.role.me?"vous":"Ahmed / gérance"):"auteur non enregistré";   /* même convention que prospQui */
function b21dDecTxt(d){return d?(d.verdict||"?")+(d.le?" · le "+fmtIso(d.le):"")+" · par "+b21dQui(d.qui)+(d.parallele?" (offre séparée)":"")+(d.motif?" · motif : "+d.motif:""):"Aucune décision enregistrée";}
function b21dDecider(oid,verdict){const a=S.ao[oid];if(!a)return;if(!editable())return toast(RO_MSG);
  if(b21dClos(a))return toast("Consultation clôturée : la décision reste affichée en lecture, aucune nouvelle soumission.");
  if(["Déposé","Attribué","Non retenu"].includes(a.statut))return toast("Dossier "+a.statut.toLowerCase()+" : décision figée.");
  const motif=String(B21D.motif[oid]||"").trim().slice(0,300);
  if(verdict!=="Go"&&!motif)return toast("Saisissez le motif (obligatoire pour « "+verdict+" »).");
  if(a.decision&&a.decision.verdict===verdict&&(a.decision.motif||"")===motif)return toast("Décision inchangée : rien n'est enregistré.");
  const k=oid+"|"+verdict;if(!B21D.conf||B21D.conf.k!==k||Date.now()-B21D.conf.t>6000){B21D.conf={k,t:Date.now()};render();return toast("Confirmez « "+verdict+" » pour "+socCourt(a.soc)+" : appuyez encore une fois. "+(verdict==="Go"?"La préparation de son dossier est lancée ; ":"")+"aucune autre société n'est modifiée.");}
  B21D.conf=null;const me=S.role.me||null,now=new Date().toISOString(),prev=a.decision;
  if(prev)a.decisionHist=(a.decisionHist||[]).concat([Object.assign({},prev,{remplaceLe:now,remplacePar:me})]).slice(-50);
  a.decision={verdict,le:isoToday(),qui:me,motif,soc:a.soc,source:"B2.1 décision par société"};
  a.statut=verdict==="Go"?"En préparation":verdict==="No-Go"?"Abandonné":"À examiner";
  saveAO(oid);logJ(a.ref+" : décision "+verdict+" pour "+socCourt(a.soc)+(prev?" (remplace "+(prev.verdict||"?")+" du "+(prev.le?fmtIso(prev.le):"?")+")":"")+(motif?" — "+motif:""));
  if(verdict==="Go")prepDemarrer(oid,"Go (B2.1)");delete B21D.motif[oid];render();
  toast(verdict==="Go"?"Go enregistré pour "+socCourt(a.soc)+" : la préparation démarre ; les pièces restantes restent à traiter avant dépôt.":verdict==="No-Go"?"No-Go enregistré pour "+socCourt(a.soc)+" : ses pièces sont conservées.":"« À reprendre » enregistré pour "+socCourt(a.soc)+" : retiré de la préparation, pièces conservées, réversible par un nouveau Go.");}
function b21dPanneau(x,clos){const a=x.a,d=a.decision,ed=editable()&&!clos&&!["Déposé","Attribué","Non retenu"].includes(a.statut),H=(a.decisionHist||[]).slice().reverse();
  const cls=!d?"b21d-neu":d.verdict==="Go"?"b21d-ok":d.verdict==="No-Go"?"b21d-ko":"b21d-amb";
  let h=`<aside class="b21d-dec" aria-label="Votre décision pour ${esc(socCourt(x.sid))}"><h4>Votre décision</h4><p><span class="b21d-pill ${cls} b21d-big" data-b21d-verdict="${esc(d?d.verdict:"aucune")}">${esc(d?d.verdict:"Aucune décision")}</span></p><p class="b21d-src">${esc(b21dDecTxt(d))}</p>`;
  if(ed){const v=B21D.motif[x.oid]||"",c=B21D.conf&&B21D.conf.k.startsWith(x.oid+"|")?B21D.conf.k.split("|")[1]:null;
    h+=`<div class="b21d-btns" role="group" aria-label="Décision">${["Go","No-Go","À reprendre"].map(V=>`<button type="button" class="b21d-db${c===V?" b21d-arm":""}" aria-pressed="${!!(d&&d.verdict===V)}" data-b21d-dec="${esc(V)}" data-act="${act(()=>b21dDecider(x.oid,V))}">${c===V?"Confirmer « "+V+" »":V}</button>`).join("")}</div>
      <label class="b21d-lab">Motif <small>(obligatoire pour No-Go et À reprendre)</small><textarea rows="2" data-b21d-motif="${esc(x.oid)}" placeholder="Motif de votre décision">${esc(v)}</textarea></label>
      <p class="b21d-src">Le Go lance la préparation même si des pièces restent à compléter : elles restent signalées et les contrôles avant dépôt s'appliquent. Aucun Go n'est proposé ni présélectionné.</p>`;}
  else h+=`<p class="b21d-src">${clos?"Consultation clôturée : décision en lecture seule, aucune nouvelle soumission.":!editable()?"Lecture seule.":"Dossier "+esc(a.statut)+" : décision figée."}</p>`;
  if(H.length)h+=`<details class="b21d-hist"><summary>Historique des décisions (${H.length})</summary><ul>${H.map(z=>`<li>${esc(b21dDecTxt(z))}<small>remplacée le ${esc(fmtDT(z.remplaceLe))} par ${esc(b21dQui(z.remplacePar))}</small></li>`).join("")}</ul></details>`;
  return h+`</aside>`;}
function b21dCarte(x,clos){const D=b21dCarteData(x.oid,x.a,x.sid),a=x.a,CH=D.CH;
  /* aucun montant (HT, TVA, TTC) dans cette vue multi-sociétés : couverture et validation seulement (FIN-ISO-001) */
  const fin=CH?`<p class="b21d-fin" data-b21d-fin="1"><b>Chiffrage de ${esc(socCourt(x.sid))}</b> : ${esc(CH.n+"/"+CH.N)} PU saisis · ${CH.valide?"validé (offre figée)":CH.statut==="reprendre"?"à reprendre":"non validé"}${CH.tva?"":" · TVA non confirmée"} <button type="button" class="b21d-lnk" data-act="${act(()=>b21dAller(x.oid,"MP-B3.1","prix"))}">Ouvrir le chiffrage</button></p>`:`<p class="b21d-fin" data-b21d-fin="0">Bordereau non extrait pour ce dossier.</p>`;
  const FR=D.F?{ajour:["b21d-ok","Lecture à jour"],perimee:["b21d-ko","Note à actualiser"],inconnue:["b21d-amb","Fraîcheur non vérifiée"],absente:["b21d-amb","Aucune lecture"]}[D.F.k]:null;
  let h=`<article class="b21d-card" id="b21d-${esc(x.oid)}" data-b21d-soc="${esc(x.sid)}" data-b21d-oid="${esc(x.oid)}"><header class="b21d-ch"><div><h3>${esc(socCourt(x.sid))}</h3><p class="b21d-src">Dossier séparé · ${esc(a.statut||"")} · ${esc(a.ref||x.oid)}</p></div>
    <div class="b21d-cm"><span class="b21d-pill ${D.reste.length?"b21d-amb":"b21d-ok"}" data-b21d-reste="${D.reste.length}">${D.reste.length?D.reste.length+" point(s) restant(s)":"Aucun point restant relevé"}</span>${FR?`<span class="b21d-pill ${FR[0]}" title="${esc(D.F.txt)}">${FR[1]}</span>`:""}</div></header>
    <div class="b21d-body"><div class="b21d-main">`;
  h+=D.rcOk?b21dTable(D,x.sid):`<p class="b21d-warn">Pièces du RC non relevées pour ce dossier : liste indisponible (aucune pièce supposée). <button type="button" class="b21d-lnk" data-act="${act(()=>b21dAller(x.oid,"MP-B2.2","note"))}">Ouvrir la lecture RC / CPS</button></p>`;
  h+=fin+`<p class="b21d-src">Sources : pièces du RC lues (${esc(D.rcId)}), coffre et pièces de ${esc(socCourt(x.sid))}, chiffrage B3.1 de ce dossier. ${D.F?esc(D.F.txt):""}</p></div>${b21dPanneau(x,clos)}</div></article>`;
  return h;}
function vDecisionB21(id,a){b21dCss();const X=b21dSibs(id,a),clos=b21dClos(a),lim=b21dLim(a),ed=editable();
  let h=`<div class="b21d" data-b21d="${esc(id)}"><header class="b21d-top"><div><p class="b21d-src b21d-ref">${esc(a.ref||id)} · ${esc(String(a.obj||"").slice(0,120))}</p></div>
    <div class="b21d-cm">${lim?`<span class="b21d-pill ${clos?"b21d-ko":"b21d-neu"}" data-b21d-clos="${clos}">${clos?"Consultation clôturée le ":"Date limite : "}${esc(fmtIso(a.lim))}${a.heure?" "+esc(a.heure):""}</span>`:`<span class="b21d-pill b21d-amb">Date limite non renseignée</span>`}<button type="button" class="b21d-btn" data-b21d-maj="1" data-act="${act(()=>{try{delete B21.cache;}catch(e){}render();toast("État et documents relus ; aucune décision modifiée.");})}">Actualiser</button></div></header>`;
  h+=`<p class="b21d-intro">Une carte par société candidate : chaque société a son propre dossier, ses pièces et ses prix (FIN-ISO-001). L'état des pièces (administratif) est distinct de votre décision commerciale Go / No-Go.</p>`;
  h+=`<details class="b21d-note"><summary>Note d'analyse (avis de l'Analyste, sources)</summary><p>L'avis de l'Analyste, daté et sourcé, et la lecture du DCE sont dans la note d'analyse ; cette zone n'en reprend aucune recommandation. <button type="button" class="b21d-lnk" data-act="${act(()=>b21Aller(id,"note"))}">Ouvrir la note d'analyse</button></p></details>`;
  h+=X.map(x=>b21dCarte(x,clos)).join("");
  const G=X.filter(x=>x.a.decision&&x.a.decision.verdict==="Go"&&!["Abandonné","Non retenu","À examiner"].includes(x.a.statut));
  h+=`<section class="b21d-ret" aria-labelledby="b21d-rt"><h3 id="b21d-rt">Entreprises retenues pour la préparation</h3>`;
  h+=G.length?`<ul class="b21d-rl">${G.map(x=>`<li data-b21d-ret="${esc(x.sid)}"><div><b>${esc(socCourt(x.sid))}</b><small>${esc(b21dDecTxt(x.a.decision))} · ${esc(x.a.statut)}</small></div><div class="b21d-rla"><button type="button" class="b21d-btn" data-act="${act(()=>{const e=document.getElementById("b21d-"+x.oid);if(e){e.scrollIntoView({behavior:"smooth",block:"start"});const t=e.querySelector("[data-b21d-motif]");if(t)setTimeout(()=>t.focus(),400);}})}">Modifier</button>${ed&&!clos?`<button type="button" class="b21d-btn" data-b21d-retirer="${esc(x.sid)}" data-act="${act(()=>{if(!String(B21D.motif[x.oid]||"").trim()){const e=document.getElementById("b21d-"+x.oid);if(e)e.scrollIntoView({block:"start"});return toast("Retirer = « À reprendre » : saisissez d'abord le motif dans la carte de "+socCourt(x.sid)+".");}b21dDecider(x.oid,"À reprendre");})}">Retirer</button>`:""}</div></li>`).join("")}</ul>`:`<p class="b21d-src">Aucune entreprise avec un Go enregistré.</p>`;
  if(ed&&!clos){const have=new Set(X.map(x=>x.sid)),C=SOC.filter(z=>!have.has(z.sid)).map(z=>({sid:z.sid,pc:(()=>{try{return parCompat(id,a,z.sid);}catch(e){return{st:"non",why:"contrôle indisponible"};}})()}));
    const ok=C.filter(c=>c.pc.st==="ok"||c.pc.st==="attention"),no=C.filter(c=>!(c.pc.st==="ok"||c.pc.st==="attention"));
    if(ok.length)h+=`<div class="b21d-add"><p><b>Ajouter une société</b> — crée son dossier séparé selon le modèle existant (contrôles art. 27 et FIN-ISO-001) ; la création vaut Go de cette société, sur votre confirmation.</p>${ok.map(c=>`<button type="button" class="b21d-btn" data-b21d-ajout="${esc(c.sid)}" data-act="${act(()=>{const k="add|"+c.sid;if(!B21D.conf||B21D.conf.k!==k||Date.now()-B21D.conf.t>6000){B21D.conf={k,t:Date.now()};return toast("Ajouter "+socCourt(c.sid)+" : son dossier séparé sera créé avec un Go. Appuyez encore une fois pour confirmer.");}B21D.conf=null;creerSib(id,c.sid);})}">Ajouter ${esc(socCourt(c.sid))}${c.pc.st==="attention"?" (à vérifier : "+esc(c.pc.why)+")":""}</button>`).join(" ")}</div>`;
    if(no.length)h+=`<p class="b21d-src">Non ajoutables : ${esc(no.map(c=>socCourt(c.sid)+" — "+(c.pc.why||"incompatible")).join(" ; "))}.</p>`;}
  else if(clos)h+=`<p class="b21d-src">Consultation clôturée : aucun ajout ni retrait, aucune nouvelle soumission automatique.</p>`;
  h+=`</section>`;
  let st="";try{const o=aoDecision(id,a),i=o.indexOf('<div class="grp">Statut du dossier</div>');st=i>=0?o.slice(i):"";}catch(e){}
  if(st)h+=`<details class="b21d-note"><summary>Statut administratif du dossier ${esc(socCourt(a.soc))} (existant)</summary>${st}</details>`;
  return h+`</div>`;}
/* vue pleine largeur dans le bureau B2.1 (décision à droite sur ordinateur) : même mécanisme que B3.1 */
function b21dPlein(id){return typeof MPN!=="undefined"&&!!MPN.dos&&MPN.dos.id===id&&MPN.dos.bur==="MP-B2.1"&&MPN.dos.k==="dec"&&!MPN.dos.global&&S.aoId===id;}
{const _mpnDossierB21D=mpnDossier;mpnDossier=function(d){const h=_mpnDossierB21D(d);try{const id=S.aoId;if(!id||!b21dPlein(id)||h.indexOf("b31-full")>=0)return h;b31Css();
  const t=h.replace('<div class="mpn" data-mpn-dossier-vue=','<div class="mpn b31-full b21d-full" data-mpn-dossier-vue=');return t.indexOf("b21d-full")<0?h:t;}catch(e){return h;}};}
{const _aoStepsB21D=aoSteps;aoSteps=function(id,a){const L=_aoStepsB21D(id,a),n=L.find(s=>s.k==="dec");if(n)n.body=()=>vDecisionB21(id,a);return L;};}
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.b21dMotif!=null)B21D.motif[t.dataset.b21dMotif]=t.value;});
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
.b21d-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@container b21d (max-width:560px){.b21d-tab th,.b21d-tab td{padding:6px 4px}.b21d-tab td:nth-child(2){width:84px}.b21d-tab td:nth-child(3){width:86px}.b21d-tab .b21d-pill{white-space:normal;font-size:11px;padding:2px 7px}.b21d-tab .b21d-act{padding:4px 6px;max-width:100%}.b21d-tab .b21d-act small{display:none}.b21d-tab{table-layout:fixed}.b21d-tab th:nth-child(2),.b21d-tab td:nth-child(2){width:84px}.b21d-tab th:nth-child(3),.b21d-tab td:nth-child(3){width:78px}.b21d-tab td{overflow-wrap:anywhere}}`;
function b21dCss(){if(document.getElementById("b21d-css"))return;const s=document.createElement("style");s.id="b21d-css";s.textContent=B21D_CSS;document.head.appendChild(s);}
