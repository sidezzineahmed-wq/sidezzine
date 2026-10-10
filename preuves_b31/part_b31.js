/* ================= B3.1 · Chiffrage (b31-1) =================
   Vue du bureau B3.1 pour UN dossier = UNE société (dossiers frères « id~société » pour les offres séparées, FIN-ISO-001).
   Calculs : méthode canonique existante (cts, ligneC, BP_TVA, bpTot) — Σ(qté × PU arrondi au centime) → HT → TVA → TTC.
   Stockage : PU, quantités, sous-détails et verrous dans bpx/<id> (existant, bpSave) ; validation = prixValide + offre figée
   immuable (offreValider, existant) ; scénarios et statut « à reprendre » dans chiffrage/<id> (historique ajouté, jamais effacé) ;
   brouillons enregistrés = documents immuables chiffrage_versions/<id>~v<n> (création refusée si la version existe).
   Aucune donnée d'une autre société n'est lue pour chiffrer (les onglets n'affichent que nom et statut).
   Contrôle art. 44 du décret n° 2-22-431 (édition TGR 2023, art. 44 B, p. 70) : comparaison en centimes, seuils stricts ;
   régimes études (art. 144), gardiennage / nettoyage / espaces verts (art. 43 II.1.a) ou inconnus : « à vérifier ».
   b31-4 : objectif en % aussi sur un bordereau vide ou partiel (bases justifiées puis ajustement), voir plus bas.
   b31-5 : seuils de l'art. 44 B BLOQUANTS pour l'application de l'objectif en % et pour la validation du chiffrage (garde dans les
   gestionnaires, pas seulement dans l'interface) ; études et régimes inconnus : « à vérifier », aucun seuil inventé. */
const B31={v:"b31-5",propIA:{},propBusy:null,propErr:{},mode:{},recherche:{},sansPrix:{},n:{},ouv:{},prev:{},pct:{},ch:{},vers:{},etat:{},ia:{},iaBusy:null,dlg:null,simH:{},pdf:{}};
const B31_DECRET={url:"https://www.tgr.gov.ma/wps/wcm/connect/1f3081fc-2d01-41de-8339-9a2c7de0480f/DECRET%2B2-22-431%2BFR.pdf?MOD=AJPERES",
  ref:"Décret n° 2-22-431 du 8 mars 2023, art. 44 (édition TGR 2023, p. 69-70)",sha:"d08109b9cee1364870c99659dbe58a3aef3556ab2d87209426dc97a314e07c78"};
const B31_SCEN=[["prudent","Prudent"],["equilibre","Équilibré"],["competitif","Compétitif"]];
/* ---------- arithmétique exacte (centimes entiers) ---------- */
const b31C=v=>v===""||v==null||isNaN(+v)?null:cts(v);
const b31Dh=c=>c==null?"—":fmtN(c/100)+" DH";
function b31PctNorm(t){return String(t==null?"":t).trim().replace(/[−–]/g,"-").replace(/\s|%/g,"").replace(",",".");}
/* b31-4 : toute valeur numérique (hausse, baisse, décimale à deux chiffres, zéro) ; refus si non numérique ou si la cible TTC serait ≤ 0 */
function b31ParsePct(t){const s=b31PctNorm(t);if(!/^[+-]?\d+(\.\d{1,2})?$/.test(s))return null;const v=+s;return isFinite(v)&&v>-100?v+0:null;}
function b31PctErr(t){const s=b31PctNorm(t);if(s==="")return null;if(!/^[+-]?\d+(\.\d{1,2})?$/.test(s))return"Pourcentage non reconnu : saisissez un nombre (ex. −10, +5, 7,5 ou 0 ; deux décimales au plus).";
  if(+s<=-100)return"Objectif refusé : "+String(s).replace(".",",")+" % donne une cible TTC nulle ou négative (il faut un pourcentage supérieur à −100 %).";return null;}
const b31PctTxt=p=>(p>0?"+":p<0?"−":"")+String(Math.abs(p)).replace(".",",")+" %";
const b31PartTxt=p=>String(Math.round((100+p)*100)/100).replace(".",",")+" % de l'estimation";
function b31Cible(estC,p){const pH=Math.round(p*100);return Math.round(estC*(10000+pH)/10000);}
/* totaux canoniques à partir d'une table de PU (même algorithme que bpTot / offreCalc) */
function b31Tot(id,P){const b=S.bp[id];if(!b)return null;let ht=0,tv=0,n=0,miss=0,zero=0;
  b.lots.forEach((L,l)=>{let hc=0;L.lignes.forEach((x,i)=>{const k=l+"-"+i,p=P[k],qq=bpQ(id,l,i,x);if(p!==undefined&&p!==""&&p!=null&&qq!=null){hc+=ligneC(qq,p);n++;if(+p===0)zero++;}else miss++;});
    ht+=hc;tv+=Math.floor((hc*BP_TVA+50)/100);});
  return{htC:ht,tvaC:tv,ttcC:ht+tv,n,miss,zero};}
function b31Lignes(id){const b=S.bp[id];if(!b)return[];const R=[];b.lots.forEach((L,l)=>L.lignes.forEach((x,i)=>R.push({k:l+"-"+i,l,i,x,lot:L.lot||null,qq:bpQ(id,l,i,x)})));return R;}
/* ---------- données du dossier ---------- */
function b31Est(a){const ex=a.exig||{},v=ex.estimation||a.est||null,S2=ex.sources||{};return{c:v?cts(v):null,src:v?(S2.estimation||ex.estimationSource||"Portail PMMP (fiche de la consultation)"):null,base:"TTC"};}
function b31Tva(id,a){const ex=a.exig||{},b=S.bp[id]||{},d=ex.tva!=null&&ex.tva!==""?+ex.tva:b.tva!=null&&b.tva!==""?+b.tva:null;
  if(d==null)return{taux:BP_TVA,ok:false,txt:"TVA "+BP_TVA+" % : taux de calcul EAIOS par défaut, à confirmer dans le CPS / le bordereau"};
  return d===BP_TVA?{taux:BP_TVA,ok:true,txt:"TVA "+BP_TVA+" % (taux relevé dans le dossier)"}:{taux:BP_TVA,ok:false,bloque:true,txt:"TVA relevée "+String(d).replace(".",",")+" % ≠ taux de calcul "+BP_TVA+" % : à corriger avant toute validation"};}
function b31Regime(a){const cat=String(a.categorie||"").toLowerCase(),obj=String(a.obj||""),cr=String((a.exig||{}).criteres||"");
  if(/gardiennage|nettoyage|espaces?\s+verts?/i.test(obj)||/taux de majoration/i.test(cr))return{k:"special",lab:"Régime particulier (gardiennage, nettoyage, espaces verts : taux de majoration, art. 43 II.1.a)",art:"art. 43 II.1.a"};
  if(/(^|[^a-zà-ÿ])[ée]tudes?([^a-zà-ÿ]|$)|ma[iî]trise d['’]\s?[œo]e?uvre|assistance technique/i.test(obj)||/note technico-financi/i.test(cr))return{k:"etudes",lab:"Prestations d'études (art. 144 : évaluation technico-financière)",art:"art. 144"};
  if(cat.startsWith("travaux"))return{k:"travaux",lab:"Marché de travaux",bas:20};
  if(cat.startsWith("fourniture"))return{k:"fournitures",lab:"Marché de fournitures",bas:25};
  if(cat.startsWith("service"))return{k:"services",lab:"Marché de services (autres que les études)",bas:25};
  return{k:"inconnu",lab:"Catégorie du marché inconnue"};}
/* art. 44 B : excessive si > +20 % ; anormalement basse si < −20 % (travaux) ou < −25 % (fournitures, services hors études). Égalité = dans les bornes. */
function b31Art44(R,oC,eC){const out={regime:R,eC,oC};
  if(eC==null||eC<=0)return Object.assign(out,{k:"verifier",t:"Estimation du maître d'ouvrage inconnue : contrôle de l'art. 44 impossible"});
  if(oC!=null)out.ecart=(oC-eC)/eC*100;
  if(!R.bas)return Object.assign(out,{k:"verifier",t:R.lab+" : seuils de l'art. 44 B non appliqués automatiquement — à vérifier ("+(R.art||"régime inconnu")+" et RC)"});
  if(oC==null)return Object.assign(out,{k:"incomplet",t:"Offre incomplète : contrôle de l'art. 44 en attente des prix manquants"});
  out.minC=Math.ceil(eC*(100-R.bas)/100);out.maxC=Math.floor(eC*120/100);
  if(oC*100<eC*(100-R.bas))return Object.assign(out,{k:"bas",t:"Offre anormalement basse au sens de l'art. 44 B-2 : inférieure de plus de "+R.bas+" % à l'estimation"});
  if(oC*100>eC*120)return Object.assign(out,{k:"excessif",t:"Offre excessive au sens de l'art. 44 B-1 : supérieure de plus de 20 % à l'estimation"});
  return Object.assign(out,{k:"bornes",t:"Dans les bornes de l'art. 44 B (contrôle arithmétique ; ce n'est pas une conformité de l'offre)"});}
const b31EcartTxt=e=>e==null?"—":(e>0?"+":e<0?"−":"")+(Math.abs(Math.abs(e)-20)<0.01||Math.abs(Math.abs(e)-25)<0.01?Math.abs(e).toFixed(4):Math.abs(e).toFixed(2)).replace(".",",")+" %";
/* coût : sous-détail de la société (déboursé sec × frais de chantier, frais généraux, aléas ; bénéfice exclu) */
function b31CoutU(id,k){const sd=sdOf(id,k),ds=sdDS(sd);if(!ds)return null;const K=sdK(id),f=[K.fc,K.fg,K.al].reduce((m,v)=>m*(1+(+v||0)/100),1);
  return{ds,frais:Math.round(ds*(f-1)*100)/100,cu:Math.round(ds*f*100)/100,parts:SD_T.map(([t,l])=>[t,l,sdPart(sd,t)])};}
function b31Cout(id){const L=b31Lignes(id),X=bpX(id);let cC=0,pC=0,k=0;L.forEach(r=>{const c=b31CoutU(id,r.k),p=X.p[r.k];if(!c||r.qq==null)return;k++;cC+=ligneC(r.qq,c.cu);if(p!==undefined&&p!=="")pC+=ligneC(r.qq,p);});
  return{k,N:L.length,coutC:cC,prixC:pC};}
/* ---------- état complet du chiffrage (pur : aucune écriture) ---------- */
function b31Etat(id,a){const X=bpX(id),T=b31Tot(id,X.p||{}),E=b31Est(a),R=b31Regime(a),tva=b31Tva(id,a),complet=!!T&&!T.miss&&T.n>0;
  const A44=b31Art44(R,complet?T.ttcC:null,E.c),C=S.bp[id]?b31Cout(id):{k:0,N:0,coutC:0,prixC:0};
  const srcL=X.srcL||{},nIA=Object.values(srcL).filter(s=>s&&s.m==="ia").length,lock=X.lock||{},nLock=Object.keys(lock).filter(k=>lock[k]).length;
  let iso=[];try{iso=isoCheck(id,a);}catch(e){iso=["contrôle d'isolation indisponible : "+(e&&e.message||e)];}
  const cf=(()=>{try{return offreConflit(id,a);}catch(e){return[];}})(),O=(()=>{try{return offreCourante(id,a);}catch(e){return null;}})(),pv=a.prixValide&&(!a.prixValide.soc||a.prixValide.soc===a.soc)?a.prixValide:null;
  const div=[];
  if(cf.length)div.push(OFR_CONFLIT+" ("+cf.map(o=>"v"+o.version+" "+o.status).join(", ")+")");
  if(pv&&O&&cts(pv.ttc)!==cts(O.total_ttc))div.push("Décision de prix validée ("+dh(pv.ttc)+" TTC) ≠ offre figée v"+O.version+" ("+dh(+O.total_ttc)+" TTC)");
  if(pv&&T&&complet&&cts(pv.ttc)!==T.ttcC)div.push("Bordereau actuel ("+b31Dh(T.ttcC)+" TTC) ≠ décision de prix validée ("+dh(pv.ttc)+" TTC)");
  const anc=offresOf(id,a.soc).filter(o=>OFR_ACT.includes(o.status)&&(!O||o.offer_id!==O.offer_id));if(!cf.length&&anc.length)div.push(anc.length+" autre(s) version(s) figée(s) active(s)");
  if(a.prixEtat)div.push("Notes de traçabilité du prix (réparation FIN-ISO-001, ZIP généré hors EAIOS)");
  const doc=B31.ch[id]&&B31.ch[id].doc&&B31.ch[id].doc.soc===a.soc?B31.ch[id].doc:null;
  const valide=(()=>{try{return prixFait(id,a,bpTot(id));}catch(e){return false;}})();
  const statut=valide?{k:"valide",t:"Chiffrage validé · offre v"+(O?O.version:"?")+" figée"}:doc&&doc.statut&&doc.statut.k==="a_reprendre"?{k:"reprendre",t:"À reprendre"+(doc.statut.motif?" : "+doc.statut.motif:"")}:{k:"brouillon",t:"Brouillon · chiffrage non validé"+(pv?" (une validation antérieure diverge : voir l'historique)":"")};
  return{X,T,E,R,tva,complet,A44,C,nIA,nLock,iso,cf,O,pv,div,doc,statut,valide};}
/* ---------- objectif en pourcentage (b31-4) ----------
   Cible = estimation MO TTC × (1 + p/100), p positif, négatif, décimal ou nul ; refus si non numérique ou cible ≤ 0.
   Base complète (toutes les lignes ont un PU) : ajustement proportionnel inchangé.
   Bordereau vide ou partiel : chaque ligne non verrouillée reçoit une BASE de prix justifiée — PU déjà saisi, référence interne
   de LA MÊME société (ses autres chiffrages, même désignation et même unité), proposition du Chiffreur rattachée à la société,
   ou proposition IA ligne par ligne (Claude, hypothèses à vérifier) — puis toutes les bases sont ajustées ensemble à la cible.
   Jamais de prix d'une autre société (FIN-ISO-001), jamais de répartition égale arbitraire, jamais de quantité inventée.
   Proposition et aperçu n'écrivent rien ; seul « Appliquer » écrit, sur les lignes non verrouillées, et le chiffrage reste un brouillon.
   L'aperçu porte une empreinte (pourcentage, société, estimation, PU, quantités, verrous, lignes, proposition) : toute
   modification avant « Appliquer » l'invalide. */
function b31Refs(id,a){const soc=a&&a.soc,M={};if(!soc)return M;
  Object.entries(S.bpx||{}).forEach(([oid,X])=>{const b2=S.bp[oid],o=S.ao[oid];if(oid===id||!X||!b2||!o||X.soc!==soc||o.soc!==soc||!Array.isArray(b2.lots))return;
    b2.lots.forEach((L,l)=>(L.lignes||[]).forEach((x,i)=>{const p=(X.p||{})[l+"-"+i],d=norm(x.d||"");if(!d||p===undefined||p===""||p==null||!(+p>0))return;
      const key=d+"|"+norm(x.u||"");(M[key]=M[key]||[]).push({pu:+p,ref:o.ref||oid,oid,t:+X.t||0});}));});
  Object.values(M).forEach(v=>v.sort((u,w)=>w.t-u.t));return M;}
function b31PropSig(id,a){return sha256Str((a.soc||"")+"|"+b31Lignes(id).map(r=>r.k+":"+norm(r.x.d||"")+":"+norm(r.x.u||"")).join(";"));}
function b31PropIA(id,a){const P=B31.propIA[id];return P&&P.soc===a.soc&&P.sig===b31PropSig(id,a)?P:null;}
const b31Conf=c=>{c=norm(String(c||"")).toLowerCase();return["haute","moyenne","basse"].includes(c)?c:"non indiquée";};
/* base de prix de chaque ligne (lecture seule) */
function b31Bases(id,a){const X=bpX(id),lock=X.lock||{},R=b31Refs(id,a),P=propOwn(id,a)?S.bpprop[id]:null,PL=(P&&P.lignes)||{},IA=b31PropIA(id,a);
  return b31Lignes(id).map(r=>{const k=r.k,v=X.p[k],vu=v===undefined||v===""||v==null,z=!vu&&+v===0,has=!vu&&+v>0;
    if(lock[k])return{r,lock:true,pu:has?+v:z?0:null};
    if(has)return{r,pu:+v,m:"existant",lab:"PU déjà saisi dans ce chiffrage ("+socCourt(a.soc)+")",conf:null,just:"Prix de la société conservé comme base, ajusté proportionnellement."};
    const rf=R[norm(r.x.d||"")+"|"+norm(r.x.u||"")];
    if(rf&&rf.length)return{r,pu:rf[0].pu,m:"ref",lab:"Référence interne de "+socCourt(a.soc)+" : dossier "+rf[0].ref+(rf.length>1?" (+"+(rf.length-1)+" autre(s))":""),conf:"moyenne",
      just:"Même désignation et même unité dans un autre chiffrage de la même société ; conditions et date différentes : à vérifier."};
    const c=PL[k];if(c&&+c.pu>0)return{r,pu:+c.pu,m:"chiffreur",lab:"Proposition du Chiffreur EAIOS rattachée à "+socCourt(a.soc),conf:"basse",
      just:c.j?String(c.j):"Déboursé hypothétique × coefficient (base "+(((P||{}).meta||{}).baseCout||"HYPOTHÈSE")+")."};
    const g=IA&&IA.L[k];if(g&&g.pu>0)return{r,pu:g.pu,m:"ia",lab:"Proposition IA (Claude) — hypothèse à vérifier",conf:g.conf,just:[g.just,g.inclut?"Inclut : "+g.inclut:""].filter(Boolean).join(" · ")||"Aucune justification fournie."};
    return{r,pu:null,zero:z,iaNull:!!(g&&!(g.pu>0)),iaWhy:g?g.just:null};});}
function b31BaseStat(B){const o={existant:0,ref:0,chiffreur:0,ia:0,sans:0,lock:0,qnull:0};B.forEach(z=>{if(z.r.qq==null)o.qnull++;if(z.lock)o.lock++;else if(z.pu==null)o.sans++;else o[z.m]++;});return o;}
/* empreinte de l'aperçu : tout changement de pourcentage, société, estimation, PU, quantités, verrous, lignes ou proposition l'invalide */
function b31PrevSig(id,a,p){const X=bpX(id),IA=b31PropIA(id,a);
  return sha256Str(canonJSON({p:+p,soc:a.soc||null,est:b31Est(a).c,reg:b31Regime(a).k,tva:b31Tva(id,a).txt,pu:X.p||{},q:X.q||{},lock:X.lock||{},ia:IA?IA.le:null,
    l:b31Lignes(id).map(r=>[r.k,r.qq==null?null:+r.qq,r.x.d||"",r.x.u||""]),b:b31Bases(id,a).map(z=>[z.r.k,z.pu==null?null:z.pu,z.m||""])}));}
/* b31-5 · garde de l'art. 44 B (décret n° 2-22-431) : bornes inclusives ; strictement au-delà = bloqué. Contrôle la cible demandée ET
   le TTC réellement obtenu après arrondis, recalculés sur l'estimation, la catégorie et la TVA ACTUELLES. Aucune tolérance, aucun PU corrigé. */
function b31Hors44Txt(l,A){const bas=A.k==="bas",borne=bas?A.minC:A.maxC,dep=bas?borne-A.oC:A.oC-borne;
  return l+" "+b31Dh(A.oC)+" TTC : "+(bas?"offre anormalement basse (art. 44 B-2)":"offre excessive (art. 44 B-1)")+" — seuil "+(bas?"−"+A.regime.bas:"+20")+" % de l'estimation "+b31Dh(A.eC)+", borne "+b31Dh(borne)+" TTC ; écart "+b31EcartTxt(A.ecart)+", dépassement de "+b31Dh(dep)+".";}
function b31Garde44(id,a,cibleC,ttcC){const E=b31Est(a),R=b31Regime(a),tva=b31Tva(id,a),G={bloque:false,raisons:[],verifier:null,regime:R.k};
  if(tva.bloque){G.bloque=true;G.raisons.push(tva.txt+".");}
  if(E.c==null){G.bloque=true;G.raisons.push("Estimation du maître d'ouvrage inconnue : bornes de l'art. 44 B incalculables.");return G;}
  if(!R.bas){G.verifier=R.lab+" : aucun seuil de l'art. 44 B appliqué automatiquement (aucun seuil inventé) — à vérifier ("+(R.art||"régime inconnu")+" et RC).";return G;}
  [["Cible demandée",cibleC],["TTC obtenu après arrondis",ttcC]].forEach(([l,c])=>{if(c==null)return;const A=b31Art44(R,c,E.c);if(A.k==="bas"||A.k==="excessif"){G.bloque=true;G.raisons.push(b31Hors44Txt(l,A));}});
  return G;}
function b31Previsu(id,a,p){const ET=b31Etat(id,a),X=ET.X,L=b31Lignes(id);
  if(typeof p!=="number"||!isFinite(p)||p<=-100)return{ok:false,why:"Pourcentage invalide : la cible TTC doit rester strictement positive (pourcentage supérieur à −100 %).",manque:[]};
  if(ET.E.c==null)return{ok:false,why:"Estimation du maître d'ouvrage inconnue : l'objectif en pourcentage n'a pas de base. Renseignez l'estimation (source) dans les exigences.",manque:[]};
  if(!L.length)return{ok:false,why:"Bordereau sans ligne : rien à chiffrer.",manque:[]};
  const qn=L.filter(r=>r.qq==null);
  if(qn.length)return{ok:false,k:"quantite",why:qn.length+" ligne(s) sans quantité lisible : EAIOS n'invente aucune quantité. Saisissez-les d'après le DCE (colonne Qté du bordereau), puis prévisualisez.",manque:qn.map(r=>r.x.n||r.k)};
  const B=b31Bases(id,a),lk=B.filter(z=>z.lock),lib=B.filter(z=>!z.lock);
  const lkS=lk.filter(z=>!(z.pu>0));if(lkS.length)return{ok:false,k:"verrou",why:lkS.length+" ligne(s) verrouillée(s) sans PU ou à zéro : une ligne verrouillée garde son prix ; saisissez-le ou déverrouillez-la.",manque:lkS.map(z=>z.r.x.n||z.r.k)};
  if(!lib.length)return{ok:false,why:"Toutes les lignes sont verrouillées : rien à ajuster.",manque:[]};
  const sans=lib.filter(z=>z.pu==null);
  if(sans.length){const nz=sans.filter(z=>z.zero).length,ni=sans.filter(z=>z.iaNull).length;
    return{ok:false,k:"base",why:"Base de prix incomplète : "+sans.length+" ligne(s) non verrouillée(s) sans base"+(nz?" (dont "+nz+" PU à zéro)":"")+" — ni PU saisi, ni référence interne de "+socCourt(a.soc)+", ni proposition"+(ni?" ("+ni+" sans estimation de l'IA)":"")+". EAIOS ne fait aucune répartition arbitraire : générez la proposition IA (justifiée ligne par ligne) ou saisissez ces PU, puis prévisualisez.",
      manque:sans.map(z=>z.r.x.n||z.r.k),need:sans.length};}
  const cibleC=b31Cible(ET.E.c,p),cibleHtC=Math.round(cibleC*100/(100+BP_TVA));let lockC=0,baseC=0;
  lk.forEach(z=>{lockC+=ligneC(z.r.qq,z.pu);});lib.forEach(z=>{baseC+=ligneC(z.r.qq,z.pu);});
  if(cibleHtC-lockC<=0)return{ok:false,k:"inatteignable",why:"Objectif inatteignable : les "+lk.length+" ligne(s) verrouillée(s) totalisent déjà "+b31Dh(lockC)+" HT, pour une cible de "+b31Dh(cibleHtC)+" HT ("+b31Dh(cibleC)+" TTC). Déverrouillez des lignes ou changez le pourcentage.",manque:[],cibleC,cibleHtC,lockC};
  if(!(baseC>0))return{ok:false,why:"Base des lignes non verrouillées nulle : aucun ajustement possible.",manque:[]};
  const f=(cibleHtC-lockC)/baseC,P={...X.p},rows=[];
  lib.forEach(z=>{const k=z.r.k,v=X.p[k],n=Math.round(z.pu*f*100+1e-7)/100;rows.push({k,n:z.r.x.n||"",d:z.r.x.d||"",u:z.r.x.u||"",qq:z.r.qq,avant:v===undefined||v===""||v==null?null:+v,base:z.pu,apres:n,m:z.m,lab:z.lab,conf:z.conf,just:z.just});P[k]=n;});
  const zr=rows.filter(r=>!(r.apres>0));if(zr.length)return{ok:false,why:zr.length+" PU arrondi(s) à 0,00 DH avec ce pourcentage : objectif irréaliste pour ces lignes ; changez le pourcentage ou saisissez-les.",manque:zr.map(r=>r.n||r.k)};
  const T2=b31Tot(id,P),st=b31BaseStat(B),g44=b31Garde44(id,a,cibleC,T2.ttcC);
  return{ok:true,p,f,cibleC,cibleHtC,lockC,P,rows,T:T2,resteC:T2.ttcC-cibleC,lockN:lk.length,A44:b31Art44(ET.R,T2.ttcC,ET.E.c),tva:ET.tva,
    g44,nProp:st.ref+st.chiffreur+st.ia,nIA:st.ia,nRef:st.ref,nCh:st.chiffreur,nEx:st.existant,soc:a.soc,sig:b31PrevSig(id,a,p)};}
function b31Appliquer(id,a){const pr=B31.prev[id];if(!pr||!pr.ok)return;if(!editable())return toast(RO_MSG);
  /* b31-2 : verrous relus AU MOMENT d'appliquer (une ligne verrouillée après l'aperçu n'est jamais écrasée) */
  const X=bpX(id),now=new Date().toISOString(),Lk=X.lock||{},rows=pr.rows.filter(r=>!Lk[r.k]),nv=pr.rows.length-rows.length;
  if(nv){delete B31.prev[id];render();return toast(nv+" ligne(s) verrouillée(s) depuis l'aperçu : rien n'est appliqué. Refaites l'aperçu.");}
  /* b31-4 : société, pourcentage, données ou proposition modifiés depuis l'aperçu → rien n'est appliqué */
  if(pr.soc!==a.soc){delete B31.prev[id];render();return toast("Société du dossier changée depuis l'aperçu : rien n'est appliqué. Refaites l'aperçu.");}
  const v=B31.pct[id]==null||B31.pct[id]===""?pr.p:b31ParsePct(B31.pct[id]);
  if(v!==pr.p){delete B31.prev[id];render();return toast("Pourcentage modifié depuis l'aperçu : rien n'est appliqué. Refaites l'aperçu.");}
  const re=b31Previsu(id,a,pr.p);
  if(!re.ok||re.sig!==pr.sig||canonJSON(re.rows.map(r=>[r.k,r.apres]))!==canonJSON(pr.rows.map(r=>[r.k,r.apres]))){delete B31.prev[id];render();return toast("Les données du bordereau ont changé depuis l'aperçu (prix, quantités, verrous ou proposition) : rien n'est appliqué. Refaites l'aperçu.");}
  /* b31-5 : seuils de l'art. 44 B recalculés sur les données ACTUELLES juste avant toute écriture (cible et TTC obtenu) */
  const G=b31Garde44(id,a,re.cibleC,re.T.ttcC);if(G.bloque){B31.prev[id]=re;render();return toast("Application bloquée, rien n'est écrit : "+G.raisons.join(" "));}
  X.srcL=X.srcL||{};rows.forEach(r=>{X.p[r.k]=r.apres;X.srcL[r.k]=Object.assign({m:"pct",p:pr.p,le:now,base:r.m},r.m!=="existant"?{baseLab:String(r.lab||"").slice(0,160),conf:r.conf||null,just:String(r.just||"").slice(0,300)}:{});});
  X._src="B3.1 objectif "+b31PctTxt(pr.p)+" ("+b31PartTxt(pr.p)+")"+(pr.nProp?" — "+pr.nProp+" PU de base proposés (hypothèses à vérifier)":"");
  if(pr.nProp)X._base="HYPOTHÈSE — proposition (IA, références internes ou Chiffreur) à vérifier";
  bpSave(id);delete X._base;
  logJ(a.ref+" : B3.1 objectif "+b31PctTxt(pr.p)+" appliqué à "+rows.length+" ligne(s) non verrouillée(s) de "+socCourt(a.soc)+(pr.nProp?" ("+pr.nProp+" PU de base proposés)":""));
  delete B31.prev[id];render();toast("Objectif appliqué à "+rows.length+" ligne(s) ; lignes verrouillées inchangées. Rien n'est validé : le chiffrage reste un brouillon.");}
/* proposition IA des bases manquantes : lecture seule, rien n'est écrit (ni bordereau, ni chiffrage, ni journal) */
function b31PropMsg(e){const c=e&&e.code;return c==="not_granted"||c==="sampling_disabled"?"Claude refusé ou indisponible pour ce compte":c==="rate_limited"?"trop de demandes, réessayez plus tard":c==="cancelled"?"demande annulée":c==="invalid_json"?"réponse illisible":(c||(e&&e.message)||"erreur");}
async function b31ProposerIA(id,a){if(!editable())return toast(RO_MSG);if(B31.propBusy)return;
  if(!S.sample){B31.propErr[id]={k:"indispo",t:"Proposition IA indisponible dans cette vue : la capacité « sample » (Claude) n'est pas accordée pour ce lecteur. Aucune proposition n'est produite ni simulée : saisissez les PU manquants à la main."};render();return;}
  const B=b31Bases(id,a),need=B.filter(z=>!z.lock&&z.pu==null&&z.r.qq!=null);
  if(!need.length){delete B31.propErr[id];render();return toast("Toutes les lignes non verrouillées ont déjà une base de prix.");}
  B31.propBusy=id;delete B31.propErr[id];render();
  const ET=b31Etat(id,a),E=ET.E,p=b31ParsePct(B31.pct[id]),ex=a.exig||{},R=b31Refs(id,a);
  const refs=Object.entries(R).slice(0,40).map(([k,v])=>JSON.stringify({designation:k.split("|")[0].slice(0,140),unite:k.split("|")[1]||"",pu_ht:v[0].pu,dossier:v[0].ref}));
  const ex2=B.filter(z=>z.m==="existant").slice(0,40).map(z=>JSON.stringify({designation:String(z.r.x.d||"").slice(0,140),unite:z.r.x.u||"",quantite:z.r.qq,pu_ht:z.pu}));
  const ctx=`Tu prépares, pour une PME marocaine du BTP (société : ${socCourt(a.soc)}), une PROPOSITION de prix unitaires HT en dirhams marocains (DH) pour le bordereau d'un marché public. Ces prix serviront de STRUCTURE : EAIOS les ajustera ensuite proportionnellement pour atteindre un total cible ; ils doivent donc être cohérents entre eux selon la nature, l'unité et la quantité de chaque ouvrage.
Marché : « ${String(a.obj||"").slice(0,300)} » · catégorie : ${a.categorie||"inconnue"} · lieu : ${(a.lieux||[]).join(", ")||"non précisé"}${ex.delai?" · délai : "+String(ex.delai).slice(0,160):""}${E.c!=null?" · estimation du maître d'ouvrage : "+fmtN(E.c/100)+" DH TTC (TVA "+BP_TVA+" % à confirmer)":""}${p!=null&&E.c!=null?" · objectif : "+fmtN(b31Cible(E.c,p)/100)+" DH TTC":""}.
Tu n'as accès à AUCUNE base de prix, mercuriale ni internet : ce sont des hypothèses. N'utilise jamais les prix d'une autre entreprise.${refs.length?"\nRéférences internes de la MÊME société (ses chiffrages antérieurs, indicatifs) :\n"+refs.join("\n"):""}${ex2.length?"\nPrix déjà saisis dans ce chiffrage par la même société :\n"+ex2.join("\n"):""}
Pour CHAQUE ligne ci-dessous : pu (nombre > 0, DH HT par unité) ou null si impossible, ce que le prix inclut, une justification courte (nature, unité, quantité, hypothèse de fourniture et de rendement) et ta confiance (haute|moyenne|basse).
Réponds uniquement par un objet JSON : {"lignes":[{"k":"clé","pu":nombre ou null,"inclut":"…","justification":"…","confiance":"haute|moyenne|basse"}]}
LIGNES :
`;
  const o={},keys=new Set(need.map(z=>z.r.k));
  try{for(let i=0;i<need.length;i+=40){const part=need.slice(i,i+40);
      const res=await S.sample.json(ctx+part.map(z=>JSON.stringify({k:z.r.k,n:z.r.x.n||"",designation:String(z.r.x.d||"").slice(0,300),unite:z.r.x.u||"",quantite:z.r.qq,section:z.r.x.s||""})).join("\n"),{modelTier:"default",cache:false});
      if(!res||!Array.isArray(res.lignes))throw{code:"invalid_json"};
      res.lignes.forEach(z=>{if(!z||!keys.has(z.k))return;const pu=+z.pu;o[z.k]={pu:z.pu==null||!isFinite(pu)||!(pu>0)?null:Math.round(pu*100)/100,inclut:String(z.inclut||"").slice(0,300),just:String(z.justification||z.hypotheses||"").slice(0,400),conf:b31Conf(z.confiance)};});}
    const n=Object.values(o).filter(z=>z.pu>0).length,nn=need.length-n;
    B31.propIA[id]={soc:a.soc,sig:b31PropSig(id,a),le:new Date().toISOString(),modele:"Claude (capacité sample de la page)",L:o,n,nn};delete B31.prev[id];
    if(nn)B31.propErr[id]={k:"partiel",t:"Proposition IA partielle : "+nn+" ligne(s) sans estimation de Claude ; saisissez leur PU à la main avant de prévisualiser."};
    toast(n+" PU proposé(s) par Claude, justifiés ligne par ligne : hypothèses à vérifier. Rien n'est écrit.");}
  catch(e){B31.propErr[id]={k:"echec",t:"Proposition IA interrompue ("+b31PropMsg(e)+") : aucune nouvelle proposition conservée, rien n'est écrit. Réessayez ou saisissez les PU à la main."};}
  finally{B31.propBusy=null;render();}}
/* ---------- persistance : chiffrage/<id> (scénarios, statut) et versions immuables ---------- */
async function b31Charger(id){if(!S.db||B31.ch[id])return;B31.ch[id]={etat:"loading"};
  try{const g=await S.db.doc("chiffrage/"+id).get();B31.ch[id]={etat:"ok",doc:g&&g.exists?g.data():null};}catch(e){B31.ch[id]={etat:"err",err:String(e&&(e.code||e.message)||e)};}
  try{const s=await S.db.collection("chiffrage_versions").where("ao_id","==",id).get();B31.vers[id]=(s.docs||[]).filter(d=>d.exists).map(d=>Object.assign({doc_id:d.id},d.data())).filter(v=>v.ao_id===id).sort((x,y)=>y.version-x.version);}catch(e){B31.vers[id]=[];}
  softRender();}
async function b31SaveDoc(id,a,patch,action){if(!S.db||!editable())throw new Error(RO_MSG);const ref=S.db.doc("chiffrage/"+id),g=await ref.get(),cur=g&&g.exists?g.data():{};
  if(cur.soc&&cur.soc!==a.soc)throw new Error("document de chiffrage rattaché à "+socCourt(cur.soc)+" : refus (FIN-ISO-001)");
  const le=new Date().toISOString(),par=S.role.me||null,n=Object.assign({},cur,patch,{ao_id:id,soc:a.soc,maj:le,historique:(cur.historique||[]).concat([{le,par,action}]).slice(-300)});
  await ref.set(JSON.parse(JSON.stringify(n)));B31.ch[id]={etat:"ok",doc:n};logJ(a.ref+" : B3.1 "+action+" ("+socCourt(a.soc)+")");return n;}
async function b31Version(id,a,label){if(!S.db||!editable())throw new Error(RO_MSG);const ET=b31Etat(id,a),X=ET.X,L=B31.vers[id]||[],v=L.reduce((m,x)=>Math.max(m,x.version||0),0)+1,did=id+"~v"+v,ref=S.db.doc("chiffrage_versions/"+did);
  const ex=await ref.get();if(ex&&ex.exists)throw new Error("la version "+v+" existe déjà : un brouillon enregistré n'est jamais réécrit");
  const d={ao_id:id,soc:a.soc,version:v,label:String(label||"Brouillon").slice(0,120),created_at:new Date().toISOString(),created_by:S.role.me||null,mode:B31.mode[id]||"manuel",
    pu:JSON.parse(JSON.stringify(X.p||{})),lock:JSON.parse(JSON.stringify(X.lock||{})),srcL:JSON.parse(JSON.stringify(X.srcL||{})),
    totaux:ET.T?{ht:s2c(ET.T.htC),tva:s2c(ET.T.tvaC),ttc:s2c(ET.T.ttcC),pu_saisis:ET.T.n,pu_manquants:ET.T.miss}:null,estimation_ttc:ET.E.c==null?null:s2c(ET.E.c),art44:{etat:ET.A44.k,regime:ET.R.k},statut:"BROUILLON"};
  d.hash=sha256Str(canonJSON(d));await ref.set(d);B31.vers[id]=[Object.assign({doc_id:did},d)].concat(L);logJ(a.ref+" : B3.1 brouillon v"+v+" enregistré ("+socCourt(a.soc)+", TTC "+(d.totaux?d.totaux.ttc:"incomplet")+")");return d;}
async function b31Restaurer(id,a,v){if(!editable())return toast(RO_MSG);if(v.soc!==a.soc)return toast("Version d'une autre société : refusée (FIN-ISO-001).");
  if(!confirmTwice("b31rest"+v.doc_id))return toast("Touchez encore une fois pour recharger les PU de la version "+v.version+" dans le brouillon (la version reste intacte).");
  /* b31-2 : les lignes verrouillées du brouillon actif gardent leur PU, leur verrou et leur source */
  const X=bpX(id),L0=Object.assign({},X.lock||{}),P0=Object.assign({},X.p||{}),S0=Object.assign({},X.srcL||{}),K=Object.keys(L0).filter(k=>L0[k]);
  X.p=JSON.parse(JSON.stringify(v.pu||{}));X.lock=JSON.parse(JSON.stringify(v.lock||{}));X.srcL=JSON.parse(JSON.stringify(v.srcL||{}));
  K.forEach(k=>{if(k in P0)X.p[k]=P0[k];else delete X.p[k];X.lock[k]=L0[k];if(k in S0)X.srcL[k]=S0[k];else delete X.srcL[k];});
  X._src="B3.1 brouillon v"+v.version+" rechargé";bpSave(id);logJ(a.ref+" : B3.1 brouillon v"+v.version+" rechargé ("+socCourt(a.soc)+")"+(K.length?", "+K.length+" ligne(s) verrouillée(s) conservée(s)":""));B31.dlg=null;render();
  if(K.length)toast(K.length+" ligne(s) verrouillée(s) conservée(s) telles quelles.");}
/* b31-2 · historique CONSULTATIF : les écrans hérités (offres figées, traces de prix, ancienne proposition, simulateur, devis) y sont
   affichés pour leurs preuves ; toute action d'écriture est neutralisée (bouton remplacé par un libellé, gestionnaire retiré,
   champs désactivés). Restent actifs : aperçus et téléchargements (data-doc, data-dl, exports) et le dépliage de l'affichage. */
const B31_HIST_OK=[/^\(\)=>\s*(propExport|bpExport)\(/,/^\(\)=>\{S\.(propOpen|bpOpen|bpLot|simOpen|varOpen|dvOpen)(\[[^\]]*\])?=[^;]*;render\(\);?\}$/];
function b31Consult(h){if(!h)return h;const t=document.createElement("template");t.innerHTML=h;
  t.content.querySelectorAll("[data-act]").forEach(el=>{const k=el.dataset.act,fn=ACTS[k],src=String(fn||"").replace(/\s+/g," ").trim();
    if(fn&&B31_HIST_OK.some(r=>r.test(src)))return;delete ACTS[k];el.removeAttribute("data-act");
    if(el.tagName==="BUTTON"||el.tagName==="A"){const s=document.createElement("span");s.className="b31-ro";s.dataset.b31Ro="1";
      s.textContent=(el.textContent||"Action").trim()+" — désactivé dans l'historique (lecture seule) : chiffrez dans le bureau B3.1";el.replaceWith(s);}});
  t.content.querySelectorAll("[data-upk]").forEach(el=>{delete UPS[el.dataset.upk];el.removeAttribute("data-upk");});
  t.content.querySelectorAll("input,select,textarea").forEach(el=>{el.disabled=true;el.setAttribute("disabled","");["sim","bp","sd","b31","irf"].forEach(d=>el.removeAttribute("data-"+d));});
  return t.innerHTML;}
/* ---------- validation du chiffrage (distincte du Go / No-Go d'Ahmed) ---------- */
function b31Bloquants(id,a,ET){const B=[];if(!ET.T)B.push("bordereau absent");else{if(ET.T.miss)B.push(ET.T.miss+" PU manquant(s)");if(ET.T.zero)B.push(ET.T.zero+" PU à zéro");}
  if(ET.tva.bloque)B.push(ET.tva.txt);if(ET.iso.length)B.push("FIN-ISO-001 : "+ET.iso[0]);if(ET.cf.length)B.push(OFR_CONFLIT);
  /* b31-5 : une offre hors des bornes applicables de l'art. 44 B n'est jamais validée (aucun contournement par la validation) */
  if(ET.A44.k==="bas"||ET.A44.k==="excessif")B.push(b31Hors44Txt("Offre",ET.A44)+" Validation bloquée : revoyez les prix");return B;}
function b31Valider(id,a){if(!editable())return toast(RO_MSG);const ET=b31Etat(id,a),B=b31Bloquants(id,a,ET);if(B.length)return toast("Validation impossible : "+B.join(" ; ")+".");
  if(!confirmTwice("b31val"+id))return toast("Valider le chiffrage de "+socCourt(a.soc)+" ("+b31Dh(ET.T.ttcC)+" TTC) : touchez encore une fois. Ce n'est pas la décision Go / No-Go et rien n'est déposé sur le portail.");
  const T=bpTot(id),E=ET.E,moi=E.c?Math.round((1-ET.T.ttcC/E.c)*10000)/100:null;
  a.prixValide={mode:"b31",moi,ttc:T.ttc,ht:T.ht,le:new Date().toISOString(),qui:S.role.me||null,soc:a.soc,source:"B3.1 Chiffrage ("+(B31.mode[id]||"manuel")+")",statut:STATUT_PRIX,
    baseCout:ET.C.k&&ET.C.k===ET.C.N?"SOUS-DÉTAIL SOCIÉTÉ (déboursé + frais)":"INCONNUE",coutReel:"INCONNU",decision:(moi==null?"estimation inconnue":b31PctTxt(-moi)+" par rapport à l'estimation TTC")+" — résultat du BPU",art44:{etat:ET.A44.k,regime:ET.R.k,source:B31_DECRET.ref}};
  saveAO(id);const o=offreValider(id,a);if(B31.ch[id]&&B31.ch[id].doc)b31SaveDoc(id,a,{statut:{k:"valide",le:new Date().toISOString(),qui:S.role.me||null,offre:o?o.offer_id:null}},"chiffrage validé").catch(()=>{});
  logJ(a.ref+" : B3.1 chiffrage de "+socCourt(a.soc)+" validé, "+fmtN(T.ttc)+" DH TTC"+(o?" (offre v"+o.version+")":""));render();toast("Chiffrage validé et figé"+(o?" (offre v"+o.version+")":"")+". La décision Go / No-Go et le dépôt restent humains.");}
async function b31Reprendre(id,a){if(!editable())return toast(RO_MSG);const m=(prompt("Motif « à reprendre » (visible dans l'historique) :","")||"").trim();if(!m)return;
  try{await b31SaveDoc(id,a,{statut:{k:"a_reprendre",motif:m.slice(0,300),le:new Date().toISOString(),qui:S.role.me||null}},"marqué « à reprendre »");render();toast("Chiffrage marqué « à reprendre ». Aucune offre n'est modifiée.");}catch(e){toast("Impossible : "+(e&&e.message||e));}}
/* ---------- proposition IA ---------- */
function b31SugChiffreur(id,a){const P=propOwn(id,a)?S.bpprop[id]:null;if(!P||!P.lignes)return null;const M=P.meta||{};
  return{src:"Proposition du Chiffreur EAIOS"+(M.source?" — "+M.source:""),le:P.le||M.le||null,base:M.baseCout||"HYPOTHÈSE",statut:M.statut||"",L:P.lignes};}
async function b31DemanderClaude(id,a){if(!S.sample)return toast("Claude n'est pas disponible dans cette vue : aucune suggestion produite.");if(B31.iaBusy)return;
  const X=bpX(id),L=b31Lignes(id).filter(r=>X.p[r.k]===undefined||X.p[r.k]===""||X.p[r.k]==null).slice(0,40);if(!L.length)return toast("Toutes les lignes ont déjà un PU.");
  B31.iaBusy=id;render();
  const prompt=`Tu aides une PME marocaine du BTP à préparer le chiffrage d'un marché public (${a.categorie||"catégorie inconnue"}) : « ${String(a.obj||"").slice(0,300)} », lieu : ${(a.lieux||[]).join(", ")||"non précisé"}.
Pour chaque ligne du bordereau ci-dessous, propose un prix unitaire HT en dirhams marocains (DH) RÉALISTE, sans connaître les prix des concurrents.
Tu n'as accès à aucune base de prix ni à internet : indique honnêtement que c'est une estimation, ce que le prix inclut (fourniture, pose, transport…), tes hypothèses et ta confiance (haute|moyenne|basse). Si tu ne peux pas estimer une ligne, mets pu à null.
Réponds uniquement par un objet JSON : {"lignes":[{"k":"clé","pu":nombre ou null,"inclut":"…","hypotheses":"…","confiance":"haute|moyenne|basse"}]}
LIGNES :
${L.map(r=>JSON.stringify({k:r.k,n:r.x.n||"",designation:String(r.x.d||"").slice(0,300),unite:r.x.u||"",quantite:r.qq,section:r.x.s||""})).join("\n")}`;
  try{const res=await S.sample.json(prompt,{modelTier:"default",cache:false}),le=new Date().toISOString(),o={};
    (res&&Array.isArray(res.lignes)?res.lignes:[]).forEach(z=>{if(!z||!L.some(r=>r.k===z.k))return;const pu=+z.pu;o[z.k]={pu:z.pu==null||!(pu>0)?null:Math.round(pu*100)/100,inclut:String(z.inclut||"").slice(0,300),hyp:String(z.hypotheses||"").slice(0,300),conf:String(z.confiance||"").slice(0,12),src:"Claude — estimation du modèle, sans base de prix ni internet (non vérifiée)",le};});
    B31.ia[id]={le,soc:a.soc,L:o};if(S.db&&editable())b31SaveDoc(id,a,{ia:{le,soc:a.soc,modele:"Claude (capacité sample)",lignes:o}},"suggestions Claude reçues ("+Object.keys(o).length+" ligne(s))").catch(()=>{});
    toast(Object.keys(o).length+" suggestion(s) reçue(s) : à accepter ligne par ligne.");}
  catch(e){toast("Claude n'a pas répondu ("+(e&&(e.code||e.message)||"erreur")+") : aucune suggestion.");}finally{B31.iaBusy=null;render();}}
function b31Accepter(id,a,k,pu,src,le){if(!editable())return toast(RO_MSG);const X=bpX(id);if((X.lock||{})[k])return toast("Ligne verrouillée : déverrouillez-la d'abord.");
  X.p[k]=pu;X.srcL=X.srcL||{};X.srcL[k]={m:"ia",src,le,accepte:new Date().toISOString(),par:S.role.me||null};X._src="B3.1 suggestion acceptée par ligne";bpSave(id);render();}
/* ---------- rendu ---------- */
const B31_IC={calc:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M16 11h0M8 15h2M12 15h2M8 18h2M12 18h2M16 15v3"/>',doc:'<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',bar:'<path d="M6 20V12M12 20V5M18 20v-6"/>',
  pen:'<path d="M4 20l4-1 11-11-3-3L5 16z"/><path d="M14 6l3 3"/>',spark:'<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  scale:'<path d="M12 3v18M7 21h10M5 7h14"/><path d="M5 7 2 13h6L5 7zM19 7l-3 6h6l-3-6z"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',build:'<path d="M4 21V4h11v17M15 9h5v12M2 21h20M7 8h2M11 8h2M7 12h2M11 12h2M7 16h2M11 16h2"/>',
  search:'<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',lock:'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',unlock:'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.7-1.5"/>',
  chev:'<path d="M6 9l6 6 6-6"/>',shield:'<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/>',warn:'<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>',ok:'<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
  save:'<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7V4M8 20v-6h8v6"/>',undo:'<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',send:'<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',pct:'<path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>',
  link:'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',x:'<path d="M6 6l12 12M18 6 6 18"/>',dl:'<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>'};
const b31Ic=(k,c)=>`<svg class="b31-ic${c?" "+c:""}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${B31_IC[k]||""}</svg>`;
function b31Sibs(id,a){const k=a.portail?String(a.portail.ref)+"|"+a.portail.org:null,base=a.base||id,ord=SOC.map(z=>z.sid);
  const L=Object.entries(S.ao).filter(([oid,b])=>b&&(oid===id||(k&&b.portail&&String(b.portail.ref)+"|"+b.portail.org===k)||oid===base||b.base===base));
  return L.map(([oid,b])=>({id:oid,soc:b.soc,statut:b.statut})).sort((x,y)=>(ord.indexOf(x.soc)+1||99)-(ord.indexOf(y.soc)+1||99));}
function b31Kpi(ic,lab,val,sub,cls){return`<div class="b31-kpi${cls?" "+cls:""}"><span class="b31-kic">${b31Ic(ic)}</span><div><span class="b31-kl">${esc(lab)}</span><b class="b31-kv">${val}</b>${sub?`<span class="b31-ks">${sub}</span>`:""}</div></div>`;}
function b31Pill(k,t){const c={bornes:"b31-ok",valide:"b31-ok",bas:"b31-ko",excessif:"b31-ko",reprendre:"b31-ko",verifier:"b31-todo",incomplet:"b31-todo",brouillon:"b31-neu"}[k]||"b31-neu";return`<span class="b31-pill ${c}">${esc(t)}</span>`;}
function b31Aller(id,sid){const L=b31Sibs(id,S.ao[id]),o=L.find(x=>x.soc===sid);if(!o)return;S.aoId=o.id;S.stepOpen={...(S.stepOpen||{}),[o.id]:"prix"};if(typeof MPN!=="undefined"&&MPN.dos){MPN.dos=Object.assign({},MPN.dos,{id:o.id});if(typeof mpnDosAller==="function")mpnDosAller("MP-B3.1","prix");}render();window.scrollTo(0,0);if(typeof mpdFocus==="function")mpdFocus("#mpn-h");}
function vB31(id,a){b31Css();b31Charger(id);const ET=b31Etat(id,a),ed=editable(),b=S.bp[id],mode=B31.mode[id]||"manuel",X=ET.X,E=ET.E,T=ET.T;
  const sibs=b31Sibs(id,a);
  let h=`<div class="b31" data-b31="${esc(id)}" data-b31-soc="${esc(a.soc||"")}">`;
  h+=`<header class="b31-head"><div class="b31-ht"><h2 class="b31-h1" id="mpn-h" tabindex="-1">Chiffrage</h2><p class="b31-sub">B3.1 · Préparation des offres <span class="b31-chip">${esc(B31.v)}</span></p></div>
    <div class="b31-dos">${b31Ic("doc")}<div><b>${esc(a.ref||id)} · ${esc(String(a.obj||"").slice(0,90))}${String(a.obj||"").length>90?"…":""}</b><span>${esc(a.mo||"")} · ${esc(a.categorie||"catégorie inconnue")}${a.lim?" · limite "+fmtIso(a.lim)+(a.heure?" "+a.heure:""):""}</span></div></div></header>`;
  h+=`<nav class="b31-tabs" aria-label="Sociétés"><div class="b31-tl" role="tablist">${sibs.map(s=>`<button type="button" role="tab" aria-selected="${s.id===id}" data-b31-tab="${esc(s.soc||"")}" data-act="${act(()=>b31Aller(id,s.soc))}">${b31Ic("build")}${esc(socCourt(s.soc))}${s.id===id?"":`<small>${esc(s.statut||"")}</small>`}</button>`).join("")}</div><span class="b31-tn">Chiffrage propre à la société sélectionnée : aucun prix d'une autre société n'est lu ni affiché.</span></nav>`;
  if(!b)return h+`<div class="b31-card b31-vide">${b31Ic("doc")}<div><b>Bordereau non extrait du DCE</b><p>${a.dceDemande||(a.fichiers||{}).dce?"Le DCE est demandé ou joint : le bordereau apparaîtra après sa lecture (bureau B1.1 / B2.1).":"Aucun DCE : le chiffrage commence après la récupération et la lecture du DCE."} Aucun montant n'est simulé sans bordereau.</p></div></div></div>`;
  const ecC=ET.complet&&E.c?ET.T.ttcC-E.c:null;
  h+=`<div class="b31-kpis" data-b31-kpis="1">${b31Kpi("calc","Estimation MO · TTC",E.c==null?"Non renseignée":b31Dh(E.c),E.c==null?"à relever dans le DCE":esc("Source : "+E.src))}
    ${b31Kpi("doc","Offre "+(ET.valide?"validée":"en cours")+" · TTC",ET.complet?b31Dh(T.ttcC):"Incomplète",ET.complet?esc(T.n+"/"+(T.n+T.miss)+" PU · "+(ET.statut.k==="valide"?"figée":"brouillon")):esc(T.miss+" PU manquant(s) sur "+(T.n+T.miss)+" — aucun total partiel présenté comme offre"),ET.complet?"":"b31-kinc")}
    ${b31Kpi("bar","Écart à l'estimation",ecC==null?"—":b31EcartTxt(ET.A44.ecart),ecC==null?(E.c==null?"estimation inconnue":"offre incomplète"):esc((ecC>0?"+":ecC<0?"−":"")+fmtN(Math.abs(ecC)/100)+" DH · même base TTC / TTC"),ET.A44.k==="bas"||ET.A44.k==="excessif"?"b31-kko":"")}</div>`;
  const M=[["manuel","pen","Saisie manuelle","Saisir et ajuster vos prix"],["ia","spark","Proposition IA","Suggestions par ligne, à accepter"],["pct","target","Objectif en %","Viser un % de l'estimation"]];
  const sc=ET.doc&&ET.doc.actif?(B31_SCEN.find(z=>z[0]===ET.doc.actif)||[0,""])[1]:"";
  h+=`<div class="b31-modes"><div class="b31-mg" role="radiogroup" aria-label="Mode de chiffrage">${M.map(([k,ic,t,s])=>`<button type="button" role="radio" aria-checked="${mode===k}" class="b31-mode" data-b31-mode="${k}" data-act="${act(()=>{B31.mode[id]=k;render();})}">${b31Ic(ic)}<span><b>${t}${k==="ia"?` <em class="b31-pill b31-todo">À vérifier</em>`:""}</b><small>${s}</small></span></button>`).join("")}</div>
    <div class="b31-mx"><button type="button" class="b31-lnk" data-b31-scen="1" data-act="${act(()=>{B31.dlg={id,k:"scen"};render();})}">${b31Ic("doc")}${sc?"Scénario "+esc(sc):"Scénarios"} · ${esc(ET.statut.k==="valide"?"Validé":ET.statut.k==="reprendre"?"À reprendre":"Brouillon")}</button><button type="button" class="b31-lnk" data-b31-vers="1" data-act="${act(()=>{B31.dlg={id,k:"vers"};render();})}">${b31Ic("save")}Brouillons${(B31.vers[id]||[]).length?` <em class="b31-cnt">${(B31.vers[id]||[]).length}</em>`:""}</button><button type="button" class="b31-lnk" data-b31-hist="1" data-act="${act(()=>{B31.dlg={id,k:"hist"};render();})}">${b31Ic("clock")}Historique${ET.div.length?` <em class="b31-cnt">${ET.div.length}</em>`:""}</button></div></div>`;
  if(ET.div.length)h+=`<div class="b31-div" role="note" data-b31-div="${ET.div.length}">${b31Ic("warn")}<span><b>${ET.div.length} divergence(s) conservée(s) dans l'historique</b> — ${esc(ET.div[0])}${ET.div.length>1?" ; …":""}. Le chiffrage actif ci-dessous reste au premier plan ; rien n'est effacé.</span><button type="button" class="b31-lnk" data-act="${act(()=>{B31.dlg={id,k:"hist"};render();})}">Ouvrir l'historique</button></div>`;
  h+=b31Regle(id,a,ET);
  h+=`<div class="b31-grid"><section class="b31-card b31-bpu" aria-labelledby="b31-bt">${b31Table(id,a,ET,mode)}</section><aside class="b31-side" aria-label="Récapitulatif et contrôles">${mode==="pct"?b31SimCard(id,a,ET):""}${mode==="ia"?b31IaCard(id,a,ET):""}<div id="b31-recap">${b31Recap(id,a,ET)}</div>${b31Controles(id,a,ET)}</aside></div>`;
  h+=b31Barre(id,a,ET);
  if(B31.dlg&&B31.dlg.id===id)h+=b31Dialog(id,a,ET);
  if(S.sd&&S.sd.id===id)h+=sdSheet().replace('<div class="fspanel">','<div class="fspanel b31-sdp">');
  return h+`</div>`;}
function b31Regle(id,a,ET){const ex=a.exig||{},cr=ex.criteres,src=(ex.sources||{}).criteres,o=B31.ouv[id+"|regle"],res=S.res&&S.res[id],pvP=res&&res.pv&&res.pv.lots&&res.pv.lots.length===1?res.pv.lots[0]:null;
  let pref="non calculé";const offs=pvP?(pvP.offres||[]).filter(x=>x.montant>0&&x.statut!=="écarté"):[];
  if(offs.length&&ET.E.c){const m=offs.reduce((s,x)=>s+x.montant,0)/offs.length,P=(ET.E.c/100+m)/2;pref=fmtN(P)+" DH (réel : procès-verbal publié, "+offs.length+" offre(s))";}
  let d=`<div class="b31-rb"><p><b>Règle lue dans le RC</b> ${cr?esc(cr):b21NR?b21NR("non relevée : à lire dans le règlement de consultation"):"non relevée"}</p>${src?`<p class="b31-src">Source : ${esc(src)}</p>`:`<p class="b31-src">Source non indiquée : à vérifier sur le RC.</p>`}
    <p><b>Régime retenu pour le contrôle :</b> ${esc(ET.R.lab)}${ET.R.bas?` — offre excessive si supérieure de plus de 20 % à l'estimation ; anormalement basse si inférieure de plus de ${ET.R.bas} % (art. 44 B). Une égalité au seuil n'est pas un dépassement.`:" — seuils de l'art. 44 B non appliqués automatiquement : à vérifier."}</p>
    <p><b>Prix de référence (art. 44 A)</b> : P = (E + moyenne des offres retenues) ÷ 2 ; l'offre retenue est la plus proche de P par défaut. Il ne se calcule qu'avec les offres réelles des concurrents (procès-verbal). Le RC ne déroge pas au décret.</p>
    <p class="b31-src">${b31Ic("link")}<a href="${esc(B31_DECRET.url)}" target="_blank" rel="noopener">${esc(B31_DECRET.ref)}</a> · fichier officiel TGR, empreinte ${esc(B31_DECRET.sha.slice(0,12))}…</p>${b31SimP(id,a,ET)}</div>`;
  return`<details class="b31-card b31-regle" data-b31-regle="1"${o?" open":""}><summary>${b31Ic("chev","b31-cv")}${b31Ic("scale")}<span><b>Règle d'attribution</b> · ${cr?`<em class="b31-or">lue dans le RC — à vérifier</em>`:`<em class="b31-ko-t">non relevée — à vérifier dans le RC</em>`}<small>${esc(ET.R.lab)} · ${esc(ET.A44.k==="verifier"?"contrôle art. 44 à vérifier":"seuils art. 44 B appliqués")}</small></span><span class="b31-rr">${b31Ic("clock")}Prix de référence : <b>${esc(pref.split(" (")[0])}</b></span></summary>${d}</details>`;}
function b31SimP(id,a,ET){const s=B31.simH[id]||"",E=ET.E.c;let r="";
  const v=s.split(/[;\n]+/).map(x=>b31C(String(x).replace(/\s/g,"").replace(",","."))).filter(x=>x!=null&&x>0);
  if(v.length&&E&&ET.complet){const all=v.concat([ET.T.ttcC]),R=ET.R;const ok=all.filter(o=>!R.bas||(o*100>=E*(100-R.bas)&&o*100<=E*120));const m=ok.reduce((t,x)=>t+x,0)/ok.length,P=Math.round((E+m)/2);
    const sous=ok.filter(o=>o<=P).sort((x,y)=>y-x),best=sous.length?sous[0]:ok.slice().sort((x,y)=>x-y)[0];const moi=ok.includes(ET.T.ttcC);
    r=`<p class="b31-hyp">SIMULATION HYPOTHÉTIQUE (offres saisies par vous, non réelles) : P = ${b31Dh(P)} ; ${moi?(best===ET.T.ttcC?"votre offre serait la plus proche par défaut de P avec ces seules hypothèses":"votre offre ne serait pas la plus proche de P avec ces hypothèses"):"votre offre serait écartée (art. 44 B) avec ces hypothèses"}. Aucune simulation ne garantit le résultat.</p>`;}
  return`<div class="b31-simp"><label for="b31-simh-${esc(id)}">Simulation hypothétique du prix de référence — offres concurrentes supposées (TTC, séparées par « ; »)</label><input id="b31-simh-${esc(id)}" data-b31-simh="${esc(id)}" class="b31-in" value="${esc(s)}" placeholder="ex. 2500000 ; 2650000" autocomplete="off">${r||`<p class="b31-src">${ET.complet?"Saisissez des offres supposées pour une simulation, clairement hypothétique.":"Simulation possible quand l'offre est complète."}</p>`}</div>`;}
function b31Table(id,a,ET,mode){const b=S.bp[id],X=ET.X,L=b31Lignes(id),lock=X.lock||{},srcL=X.srcL||{},ed=editable(),pr=mode==="pct"?B31.prev[id]:null,prev=pr&&pr.ok?Object.fromEntries(pr.rows.map(r=>[r.k,r.apres])):null;
  const qs=norm(B31.recherche[id]||""),sp=!!B31.sansPrix[id],ia=mode==="ia"?b31SugChiffreur(id,a):null,cl=mode==="ia"?(B31.ia[id]||(ET.doc&&ET.doc.ia&&ET.doc.ia.soc===a.soc?{le:ET.doc.ia.le,L:ET.doc.ia.lignes||{}}:null)):null;
  const F=L.filter(r=>(!qs||norm((r.x.n||"")+" "+(r.x.d||"")+" "+(r.x.s||"")).includes(qs))&&(!sp||X.p[r.k]===undefined||X.p[r.k]===""||X.p[r.k]==null)),N=B31.n[id]||60;
  let h=`<header class="b31-bh"><div>${b31Ic("doc","b31-big")}<div><h3 id="b31-bt">Bordereau des prix</h3><span>${L.length} ligne(s)${b.lots.length>1?" · "+b.lots.length+" lots":""}${b.cadre?" · marché-cadre":""} · quantités issues du DCE${a.base&&a.base!==id&&S.bp[a.base]===b?" (bordereau de la consultation, partagé en lecture avec le dossier d'origine ; prix propres à "+esc(socCourt(a.soc))+")":""}${b.source?" · "+esc(String(b.source).slice(0,60)):""}</span></div></div>
    <div class="b31-tools"><label class="b31-srch">${b31Ic("search")}<input type="search" data-b31-q="${esc(id)}" value="${esc(B31.recherche[id]||"")}" placeholder="Rechercher une ligne…" aria-label="Rechercher une ligne du bordereau"></label>
    <button type="button" class="b31-btn b31-sm" aria-pressed="${sp}" data-act="${act(()=>{B31.sansPrix[id]=!sp;render();})}">Sans prix (${ET.T.miss})</button>${S.downloads?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>bpExport(id,a,"doc"))}">${b31Ic("dl")}Bordereau Word</button><button type="button" class="b31-btn b31-sm" data-act="${act(()=>bpExport(id,a,"xls"))}">Excel</button>`:""}</div></header>`;
  if(b.alertes&&b.alertes.length)h+=`<p class="b31-al">${b31Ic("warn")}${b.alertes.length} alerte(s) de lecture du bordereau : ${esc(String(b.alertes[0]).slice(0,160))}${b.alertes.length>1?" …":""}</p>`;
  let rows="",sec=null,n=0;
  F.slice(0,N).forEach(r=>{const x=r.x,k=r.k,p=X.p[k],has=p!==undefined&&p!==""&&p!=null,tot=has&&r.qq!=null?ligneC(r.qq,p):null,lk=!!lock[k],s=srcL[k],cu=b31CoutU(id,k),ouv=B31.ouv[id+"|"+k];
    const secT=(r.lot&&b.lots.length>1?r.lot.split(" - ")[0]+" · ":"")+(x.s||"");if(secT!==sec){sec=secT;if(sec)rows+=`<tr class="b31-sec"><th colspan="7" scope="colgroup">${esc(sec)}</th></tr>`;}
    const sug=ia&&ia.L[k]?{pu:ia.L[k].pu,src:ia.src,le:ia.le,inc:"fourniture "+fmtN(ia.L[k].f||0)+" + main-d'œuvre et matériel "+fmtN(ia.L[k].m||0)+" DH (déboursé hypothétique) × coefficient",hyp:ia.L[k].j||"",base:ia.base}:cl&&cl.L[k]&&cl.L[k].pu!=null?{pu:cl.L[k].pu,src:cl.L[k].src,le:cl.L[k].le||cl.le,inc:cl.L[k].inclut,hyp:cl.L[k].hyp,conf:cl.L[k].conf}:null;
    rows+=`<tr class="b31-r${has?"":" b31-nop"}${lk?" b31-lk":""}" data-b31-k="${esc(k)}"><td class="b31-n">${esc(x.n||"")}</td><td class="b31-d"><span class="b31-dt">${esc(x.d||"")}</span>${s?`<small class="b31-sl">${esc(s.m==="ia"?"Suggestion acceptée ("+String(s.src||"").split(" — ")[0]+")":s.m==="pct"?"Objectif "+b31PctTxt(s.p):"Saisie manuelle")}</small>`:""}${sug&&ed?`<div class="b31-sug"><span>${b31Ic("spark")}<b>${sug.pu==null?"Pas d'estimation":fmtN(sug.pu)+" DH"}</b> · ${esc(sug.src)}${sug.le?" · "+esc(fmtDT(sug.le)):""}${sug.conf?" · confiance "+esc(sug.conf):""}${sug.base?" · base "+esc(sug.base):""}</span>${sug.inc?`<small>Inclut : ${esc(sug.inc)}</small>`:""}${sug.hyp?`<small>Hypothèses : ${esc(sug.hyp)}</small>`:""}${sug.pu!=null&&!lk&&+p!==+sug.pu?`<button type="button" class="b31-btn b31-xs" data-b31-acc="${esc(k)}" data-act="${act(()=>b31Accepter(id,a,k,sug.pu,sug.src,sug.le))}">Accepter pour cette ligne</button>`:sug.pu!=null&&+p===+sug.pu?`<em class="b31-pill b31-ok">Acceptée</em>`:""}</div>`:""}</td>
      <td class="b31-u">${esc(x.u||"")}</td><td class="b31-q">${r.qq==null?`<span class="b31-ko-t">illisible</span>`:esc(fmtQ(r.qq))}</td>
      <td class="b31-p"><input type="number" inputmode="decimal" step="0.01" min="0" id="bpi${esc(k)}" data-bp="${esc(k)}" value="${esc(has?p:"")}" placeholder="PU HT" aria-label="Prix unitaire HT, ligne ${esc(x.n||k)}" ${ed&&!lk&&mode!=="pct"?"":"disabled"}>${prev&&prev[k]!=null?`<small class="b31-pv">→ ${fmtN(prev[k])}</small>`:""}</td>
      <td class="b31-t" id="bpt${esc(k)}">${tot!=null?fmtN(tot/100):`<span class="b31-ko-t">—</span>`}</td>
      <td class="b31-a">${ed?`<button type="button" class="b31-ib" aria-pressed="${lk}" aria-label="${lk?"Déverrouiller":"Verrouiller"} la ligne ${esc(x.n||k)}" title="${lk?"Ligne verrouillée : l'objectif en % ne la modifie pas":"Verrouiller la ligne"}" data-b31-lock="${esc(k)}" data-act="${act(()=>{const Y=bpX(id);Y.lock=Y.lock||{};if(Y.lock[k])delete Y.lock[k];else Y.lock[k]=true;bpSave(id);delete B31.prev[id];render();})}">${b31Ic(lk?"lock":"unlock")}</button>`:""}<button type="button" class="b31-sdb${cu?" on":""}" aria-expanded="${!!ouv}" data-b31-sd="${esc(k)}" data-act="${act(()=>{B31.ouv[id+"|"+k]=!ouv;render();})}">${b31Ic("chev")}Sous-détail</button></td></tr>`;
    if(ouv)rows+=`<tr class="b31-sdr"><td></td><td colspan="6">${b31SdInline(id,k,p,cu,ed)}</td></tr>`;n++;});
  h+=`<div class="b31-tw"><table class="b31-tab"><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"></colgroup><thead><tr><th>N°</th><th>Désignation</th><th>Unité</th><th>Qté</th><th>PU HT (DH)</th><th>PT HT (DH)</th><th><span class="b31-sr">Actions</span></th></tr></thead><tbody>${rows||`<tr><td colspan="7" class="b31-none">Aucune ligne ne correspond.</td></tr>`}</tbody></table></div>`;
  if(F.length>N)h+=`<button type="button" class="b31-more" data-b31-more="1" data-act="${act(()=>{B31.n[id]=N+60;render();})}">Afficher 60 lignes de plus (${F.length-N} restantes sur ${F.length})</button>`;
  const T=ET.T;h+=`<div class="b31-arr">${b31Ic("doc")}<div>${ET.complet?`<b>Arrêté à : ${esc(enLettres(T.ttcC/100))} toutes taxes comprises.</b>`:`<b>Arrêté non disponible :</b> ${T.miss} PU manquant(s). Aucun montant en lettres n'est produit pour une offre incomplète.`}<span>Écart calculé sur la même base TTC (estimation TTC / offre TTC).</span></div></div>`;
  return h;}
function b31SdInline(id,k,p,cu,ed){const open=act(()=>{S.sd={id,key:k};render();});
  if(!cu)return`<div class="b31-sdi"><p>Aucun sous-détail pour ce prix : coût inconnu (jamais compté à zéro).</p>${ed?`<button type="button" class="b31-btn b31-sm" data-act="${open}">Saisir le sous-détail</button>`:""}</div>`;
  const has=p!==undefined&&p!==""&&p!=null,mg=has?Math.round((+p-cu.cu)*100)/100:null;
  const tile=(ic,l,v)=>`<div class="b31-tile"><span>${esc(l)}</span><b>${fmtN(v)} DH</b></div>`;
  return`<div class="b31-sdi"><h4>Sous-détail du prix unitaire</h4><div class="b31-tiles">${cu.parts.map(([t,l,v])=>tile(t,l,v)).join("")}${tile("f","Frais (chantier, généraux, aléas)",cu.frais)}<div class="b31-tile b31-tc"><span>Coût unitaire</span><b>${fmtN(cu.cu)} DH</b></div><div class="b31-tile b31-tc"><span>Marge unitaire</span><b>${mg==null?"—":fmtN(mg)+" DH"}</b></div></div>
    <p class="b31-src">Origine : sous-détail saisi pour cette société (déboursé sec × frais ; le bénéfice du coefficient K n'est pas compté dans le coût). ${ed?`<button type="button" class="b31-lnk" data-act="${open}">Modifier dans le panneau</button>`:""}</p></div>`;}
function b31Recap(id,a,ET){const T=ET.T,C=ET.C,inc=!ET.complet;
  const row=(l,v,c)=>`<div class="b31-rr${c?" "+c:""}"><span>${l}</span><b>${v}</b></div>`;
  let h=`<section class="b31-card b31-rec" aria-labelledby="b31-rt"><h3 id="b31-rt">${b31Ic("calc")}Récapitulatif</h3>`;
  h+=row("Total HT",inc?`<span class="b31-ko-t">incomplet</span>`:b31Dh(T.htC))+row(esc(ET.tva.txt.split(" : ")[0].replace(" (taux relevé dans le dossier)","")),inc?"—":b31Dh(T.tvaC))+row("Total TTC",inc?`<span class="b31-ko-t">incomplet (${T.miss} PU)</span>`:b31Dh(T.ttcC),"b31-ttc");
  if(inc)h+=`<p class="b31-src">Somme des seules lignes chiffrées : ${b31Dh(T.htC)} HT — ce n'est pas une offre.</p>`;
  const cov=C.k+"/"+C.N+" ligne(s) avec sous-détail";
  if(C.k&&C.k===C.N&&!inc){const mC=T.htC-C.coutC;h+=row("Coût estimé HT",b31Dh(C.coutC))+row("Marge estimée HT",b31Dh(mC))+row("Taux de marge sur vente",(mC/T.htC*100).toFixed(1).replace(".",",")+" %");h+=`<p class="b31-src">Taux = (prix HT − coût HT) ÷ prix HT. Coût = sous-détails de la société (${cov}).</p>`;}
  else h+=row("Coût estimé HT",`<span class="b31-ko-t">incomplet</span>`)+`<p class="b31-src">${b31Ic("warn")}Coûts incomplets (${cov}) : marge globale non calculée.${C.k&&C.prixC?" Sur les seules lignes couvertes : marge "+((C.prixC-C.coutC)/C.prixC*100).toFixed(1).replace(".",",")+" % du prix HT de ces lignes.":""}</p>`;
  h+=`<p class="b31-src">${b31Ic("warn")}${esc(ET.tva.txt)}.</p>`;
  return h+`</section>`;}
function b31Controles(id,a,ET){const L=[],T=ET.T,it=(niv,t,fn)=>L.push({niv,t,fn});
  if(T.miss)it("ko",T.miss+" PU manquant(s) : offre incomplète",()=>{B31.sansPrix[id]=true;B31.mode[id]="manuel";render();});
  if(T.zero)it("ko",T.zero+" PU à zéro : à justifier ou corriger",null);
  it(ET.A44.k==="bornes"?"ok":ET.A44.k==="bas"||ET.A44.k==="excessif"?"ko":"warn",ET.A44.t+(ET.A44.minC!=null?" — bornes : "+b31Dh(ET.A44.minC)+" à "+b31Dh(ET.A44.maxC)+" TTC":""),()=>{B31.ouv[id+"|regle"]=true;render();});
  if(ET.E.c==null)it("ko","Estimation du maître d'ouvrage inconnue : écart non calculable",null);
  if(!ET.tva.ok)it(ET.tva.bloque?"ko":"warn",ET.tva.txt,null);
  if(ET.C.k<ET.C.N)it("warn","Coûts incomplets : "+ET.C.k+"/"+ET.C.N+" sous-détail(s)",null);
  if(ET.nIA)it("warn",ET.nIA+" prix issus d'une suggestion acceptée : sources à confirmer",()=>{B31.mode[id]="ia";render();});
  ET.iso.forEach(t=>it("ko","FIN-ISO-001 : "+t,null));
  if(ET.div.length)it("warn",ET.div.length+" divergence(s) dans l'historique (versions figées, décision antérieure)",()=>{B31.dlg={id,k:"hist"};render();});
  if(!L.some(x=>x.niv!=="ok"))it("ok","Aucun point bloquant relevé",null);
  it("ok","Aucun prix appliqué sans action d'une personne (ligne, objectif ou acceptation)",null);
  return`<section class="b31-card b31-ctl" aria-labelledby="b31-ct"><h3 id="b31-ct">${b31Ic("shield")}Contrôles avant validation</h3><ul>${L.map(x=>`<li class="b31-c-${x.niv}">${x.fn?`<button type="button" data-act="${act(x.fn)}">`:"<div>"}${b31Ic(x.niv==="ok"?"ok":"warn")}<span>${esc(x.t)}</span>${x.fn?b31Ic("chev","b31-go")+"</button>":"</div>"}</li>`).join("")}</ul></section>`;}
function b31SimCard(id,a,ET){const v=B31.pct[id]==null?"":B31.pct[id],p=b31ParsePct(v),er=b31PctErr(v),pr=B31.prev[id],ed=editable();
  let h=`<section class="b31-card b31-sim" aria-labelledby="b31-st"><h3 id="b31-st">${b31Ic("pct")}Objectif en pourcentage</h3><label class="b31-pl">Écart voulu par rapport à l'estimation MO TTC : hausse (+) ou baisse (−), ex. −10, +5, 7,5 ou 0<input class="b31-in" data-b31-pct="${esc(id)}" value="${esc(v)}" inputmode="decimal" autocomplete="off" placeholder="saisi par vous"></label>`;
  if(er)h+=`<p class="b31-ko-t" data-b31-pcterr="1">${esc(er)}</p>`;
  if(p!=null&&ET.E.c!=null){const c=b31Cible(ET.E.c,p),A=b31Art44(ET.R,c,ET.E.c);h+=`<p class="b31-eq"><b>${esc(b31PctTxt(p))} = ${esc(b31PartTxt(p))}</b> · cible ${b31Dh(c)} TTC</p><p>${b31Pill(A.k,A.k==="bornes"?"Dans les bornes art. 44 B":A.k==="bas"?"Anormalement basse (art. 44 B)":A.k==="excessif"?"Excessive (art. 44 B)":"Art. 44 à vérifier")}</p>`;}
  if(p!=null&&ET.E.c==null)h+=`<p class="b31-ko-t">Estimation inconnue : aucune cible calculable.</p>`;
  /* base de prix : d'où vient la structure de chaque ligne (aucune répartition égale arbitraire) */
  const B=b31Bases(id,a),st=b31BaseStat(B),IA=b31PropIA(id,a),pe=B31.propErr[id],busy=B31.propBusy===id;
  const part=[[st.existant,"PU saisi(s)"],[st.ref,"référence(s) interne(s) "+socCourt(a.soc)],[st.chiffreur,"proposition(s) du Chiffreur"],[st.ia,"proposition(s) IA"],[st.lock,"verrouillée(s)"],[st.sans,"sans base"]].filter(x=>x[0]);
  h+=`<div class="b31-base" data-b31-base="${st.sans?"incomplete":"complete"}"><p><b>Base de prix · ${B.length} ligne(s)</b> : ${esc(part.map(x=>x[0]+" "+x[1]).join(" · ")||"aucune")}${st.qnull?` · <span class="b31-ko-t">${st.qnull} quantité(s) illisible(s)</span>`:""}</p>`;
  if(st.sans&&ed)h+=S.sample?`<button type="button" class="b31-btn" data-b31-propia="1" ${busy||B31.propBusy?"disabled":""} data-act="${act(()=>b31ProposerIA(id,a))}">${b31Ic("spark")}${busy?"Claude prépare la proposition…":"Générer la proposition IA ("+st.sans+" ligne"+(st.sans>1?"s":"")+" sans base)"}</button><p class="b31-src">Claude propose un PU justifié par ligne (désignation, unité, quantité, CPS lu, références internes de ${esc(socCourt(a.soc))}). Rien n'est écrit : la proposition sert seulement à l'aperçu.</p>`
    :`<p class="b31-need" data-b31-iaindispo="1">${b31Ic("warn")}<span><b>Proposition IA indisponible dans cette vue</b> (capacité « sample » non accordée) : saisissez les ${st.sans} PU manquant(s) en mode manuel. Aucune répartition arbitraire n'est faite.</span></p>`;
  if(pe)h+=`<p class="b31-need" data-b31-properr="${esc(pe.k)}">${b31Ic("warn")}<span>${esc(pe.t)}</span></p>`;
  if(IA)h+=`<p class="b31-src" data-b31-propia-ok="1">Proposition IA du ${esc(fmtDT(IA.le))} pour ${esc(socCourt(a.soc))} : ${IA.n} PU proposé(s)${IA.nn?", "+IA.nn+" sans estimation":""} · en mémoire de cette page seulement, non enregistrée.</p>`;
  h+=`</div>`;
  h+=`<div class="b31-row">${ed?`<button type="button" class="b31-btn" data-b31-prev="1" ${p==null?"disabled":""} data-act="${act(()=>{B31.prev[id]=b31Previsu(id,a,p);render();})}">Prévisualiser</button>`:""}${ed&&p!=null?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{B31.dlg={id,k:"scen",pct:p};render();})}">Enregistrer comme scénario…</button>`:""}</div>`;
  if(pr&&!pr.ok)h+=`<div class="b31-need" data-b31-need="${esc(pr.k||"1")}">${b31Ic("warn")}<span>${esc(pr.why)}${pr.manque&&pr.manque.length?`<small class="b31-src">Ligne(s) N° ${esc(pr.manque.slice(0,15).join(", "))}${pr.manque.length>15?" … (+"+(pr.manque.length-15)+")":""}</small>`:""}</span></div>`;
  if(pr&&pr.ok){const stale=pr.soc!==a.soc||pr.sig!==b31PrevSig(id,a,pr.p),prop=pr.rows.filter(r=>r.m!=="existant");
    h+=`<div class="b31-prv" data-b31-prv="1"${stale?' data-b31-stale="1"':""}><p><b>Aperçu ${esc(b31PctTxt(pr.p))}</b> : ${pr.rows.length} ligne(s) ajustée(s) × ${String(Math.round(pr.f*10000)/10000).replace(".",",")}, ${pr.lockN} verrouillée(s) inchangée(s).</p>
      <p data-b31-cible="1">TTC cible ${b31Dh(pr.cibleC)} · TTC obtenu ${b31Dh(pr.T.ttcC)} · écart d'arrondi ${pr.resteC>0?"+":""}${fmtN(pr.resteC/100)} DH, laissé tel quel (aucune ligne forcée).</p><p class="b31-src">${esc(pr.tva.txt)}.${pr.lockN?" Lignes verrouillées : "+b31Dh(pr.lockC)+" HT conservés.":""}</p><p>${b31Pill(pr.A44.k,pr.A44.t)}</p>${pr.g44&&pr.g44.verifier?`<p class="b31-src" data-b31-verif44="1">${esc(pr.g44.verifier)}</p>`:""}`;
    if(prop.length)h+=`<div class="b31-hyp" data-b31-hyp="1"><b>Proposition IA / hypothèses à vérifier</b> : ${prop.length} PU de base proposé(s) (${[pr.nRef?pr.nRef+" référence(s) interne(s)":"",pr.nCh?pr.nCh+" Chiffreur":"",pr.nIA?pr.nIA+" IA":""].filter(Boolean).join(", ")}), puis ajustés à la cible. Aucune mercuriale ni base de prix de marché n'est branchée ; aucun prix d'une autre société n'est utilisé.</div>
      <details class="b31-just" data-b31-just="1"><summary>Justification de chaque PU proposé (${prop.length})</summary><ul class="b31-ul">${prop.map(r=>`<li data-b31-jk="${esc(r.k)}"><b>N° ${esc(r.n||r.k)}</b> ${esc(String(r.d).slice(0,90))}${String(r.d).length>90?"…":""} (${esc(r.u)}, qté ${esc(fmtQ(r.qq))}) : base ${fmtN(r.base)} → <b>${fmtN(r.apres)} DH</b> · ${esc(r.lab)} · confiance ${esc(r.conf||"non indiquée")}<small class="b31-src">${esc(r.just||"")}</small></li>`).join("")}</ul></details>`;
    h+=stale?`<p class="b31-need" data-b31-perime="1">${b31Ic("warn")}<span>Aperçu périmé : les données, la société, les verrous ou la proposition ont changé depuis. Refaites l'aperçu avant d'appliquer.</span></p><div class="b31-row"><button type="button" class="b31-btn" data-act="${act(()=>{B31.prev[id]=b31Previsu(id,a,pr.p);render();})}">Refaire l'aperçu</button></div></div>`
      :pr.g44&&pr.g44.bloque?`<div class="b31-need b31-blk" data-b31-bloque44="1" role="alert">${b31Ic("warn")}<span><b>Application bloquée — hors des bornes de l'art. 44 B (décret n° 2-22-431)</b>${pr.g44.raisons.map(t=>`<small class="b31-src">${esc(t)}</small>`).join("")}<small class="b31-src">Aperçu conservé pour simulation seulement : rien n'est écrit. Changez le pourcentage ou les prix pour revenir dans les bornes (bornes incluses).</small></span></div><div class="b31-row"><button type="button" class="b31-btn b31-gold" data-b31-appl="bloque" disabled aria-disabled="true" title="${esc(pr.g44.raisons.join(" "))}">Appliquer (bloqué : art. 44 B)</button><button type="button" class="b31-btn b31-sm" data-act="${act(()=>{delete B31.prev[id];render();})}">Annuler l'aperçu</button></div></div>`
      :`<div class="b31-row"><button type="button" class="b31-btn b31-gold" data-b31-appl="1" data-act="${wact(()=>b31Appliquer(id,a))}">Appliquer aux lignes non verrouillées</button><button type="button" class="b31-btn b31-sm" data-act="${act(()=>{delete B31.prev[id];render();})}">Annuler l'aperçu</button></div><p class="b31-src">Rien n'est validé en appliquant : le chiffrage reste un brouillon (ni validation, ni Go / No-Go, ni signature, ni dépôt).</p></div>`;}
  return h+`</section>`;}
function b31IaCard(id,a,ET){const C=b31SugChiffreur(id,a),cl=B31.ia[id]||(ET.doc&&ET.doc.ia&&ET.doc.ia.soc===a.soc?ET.doc.ia:null);
  let h=`<section class="b31-card b31-ia" aria-labelledby="b31-it"><h3 id="b31-it">${b31Ic("spark")}Proposition IA</h3>`;
  h+=C?`<p><b>Proposition du Chiffreur</b> (${esc(C.le?fmtDT(C.le):"date non enregistrée")}) : suggestions affichées sous chaque ligne, base de coûts ${esc(C.base)}. ${C.statut?"Statut : "+esc(C.statut)+".":""}</p>`:`<p>Aucune proposition du Chiffreur rattachée à ${esc(socCourt(a.soc))} pour ce dossier.</p>`;
  h+=S.sample?`<p><b>Claude</b> (capacité de la page) : estimations par ligne, sans base de prix ni internet — à vérifier avant acceptation.${cl?" Dernières suggestions : "+esc(fmtDT(cl.le))+".":""}</p><button type="button" class="b31-btn" data-b31-claude="1" ${B31.iaBusy?"disabled":""} data-act="${wact(()=>b31DemanderClaude(id,a))}">${B31.iaBusy===id?"Claude prépare les suggestions…":"Demander à Claude (lignes sans PU, 40 au plus)"}</button>`
    :`<p class="b31-need">${b31Ic("warn")}<span><b>Claude n'est pas disponible dans cette vue</b> : la capacité « sample » de la page n'est pas accordée (ou a été refusée) pour ce lecteur. Aucune suggestion IA n'est produite ni simulée.</span></p>`;
  h+=`<p class="b31-src">Aucune source de prix de marché (devis, mercuriale) n'est branchée ici : les devis fournisseurs restent au bureau B3.4. Chaque suggestion s'accepte ligne par ligne ; rien n'est appliqué automatiquement.</p>`;
  return h+`</section>`;}
function b31Barre(id,a,ET){const ed=editable(),B=b31Bloquants(id,a,ET);
  return`<div class="b31-bar" data-b31-statut="${esc(ET.statut.k)}"><div class="b31-bs">${b31Ic("doc")}<span><b>${esc(ET.statut.t.split(" · ")[0].split(" (")[0])}</b>${ET.statut.t.includes(" · ")?" · "+esc(ET.statut.t.split(" · ").slice(1).join(" · ")):ET.statut.t.includes(" (")?" "+esc(ET.statut.t.slice(ET.statut.t.indexOf(" ("))):""}</span></div>
    <div class="b31-ba">${ed?`<button type="button" class="b31-btn" data-b31-save="1" data-act="${act(()=>b31Version(id,a,"Brouillon "+(B31.mode[id]||"manuel")).then(v=>{toast("Brouillon v"+v.version+" enregistré (immuable).");render();}).catch(e=>toast("Enregistrement impossible : "+(e&&e.message||e))))}">${b31Ic("save")}Enregistrer le brouillon</button>`:""}
    <button type="button" class="b31-btn" data-b31-pdf="1" data-act="${act(()=>b31Pdf(id))}" ${B31.pdfBusy?"disabled":""}>${b31Ic("doc")}${B31.pdfBusy?"PDF en préparation…":"Aperçu PDF"}</button>
    ${ed?`<button type="button" class="b31-btn" data-b31-rep="1" data-act="${act(()=>b31Reprendre(id,a))}">${b31Ic("undo")}À reprendre</button><button type="button" class="b31-btn b31-gold" data-b31-val="1" ${B.length?`aria-disabled="true" title="${esc(B.join(" ; "))}"`:""} data-act="${act(()=>b31Valider(id,a))}">${b31Ic("send")}Valider le chiffrage</button>`:""}</div>
    <p class="b31-bn">Valider le chiffrage fige l'offre de ${esc(socCourt(a.soc))} ; ce n'est ni la décision Go / No-Go d'Ahmed, ni une soumission sur le portail (aucun dépôt automatique).</p></div>`;}
function b31Dialog(id,a,ET){const D=B31.dlg,ferme=act(()=>{B31.dlg=null;render();});let t="",c="";
  if(D.k==="hist"){t="Historique du chiffrage · "+socCourt(a.soc);const V=B31.vers[id]||[];
    c+=`<h4>Divergences conservées (${ET.div.length})</h4>${ET.div.length?`<ul class="b31-ul">${ET.div.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:`<p>Aucune divergence relevée.</p>`}`;
    c+=`<h4>Brouillons B3.1 enregistrés (${V.length}, immuables)</h4>${V.length?`<ul class="b31-ul">${V.map(v=>`<li><b>v${v.version}</b> · ${esc(v.label||"")} · ${esc(fmtDT(v.created_at))} · TTC ${esc(v.totaux?fmtN(+v.totaux.ttc):"incomplet")} · art. 44 ${esc((v.art44||{}).etat||"?")} · empreinte ${esc(String(v.hash||"").slice(0,10))}…</li>`).join("")}</ul><p class="b31-src">Pour recharger un brouillon dans le chiffrage actif : bouton « Brouillons » du bureau (lignes verrouillées conservées).</p>`:`<p>Aucun brouillon enregistré.</p>`}`;
    const hs=(ET.doc&&ET.doc.historique)||[];if(hs.length)c+=`<h4>Actions tracées (${hs.length})</h4><ul class="b31-ul">${hs.slice().reverse().slice(0,30).map(x=>`<li>${esc(fmtDT(x.le))} · ${esc(x.action)}</li>`).join("")}</ul>`;
    c+=`<p class="b31-src" data-b31-consult="1">Historique en lecture seule : textes sources, aperçus et téléchargements restent disponibles ; les anciennes actions d'écriture (appliquer au bordereau, retenir une version, simuler, lire des devis…) sont désactivées ici. Les prix se modifient dans le bureau B3.1, ligne par ligne et en respectant les verrous.</p>`;
    let anc="";try{anc=b31Consult(vOffres(id,a)+vPrixTrace(id,a));}catch(e){anc=`<p>Indisponible : ${esc(e.message||e)}</p>`;}
    c+=`<h4>Offres figées et décisions de prix antérieures (preuves inchangées)</h4>${anc||"<p>Aucune.</p>"}`;
    let prop="";try{prop=b31Consult(vPropChiffreur(id,a));}catch(e){}if(prop)c+=`<h4>Ancienne proposition du Chiffreur</h4>${prop}`;
    let sim="";try{sim=b31Consult(vSimu(id,a)+vSourcing(id,a));}catch(e){}c+=`<details class="b31-old"><summary>Outils précédents (simulateur, devis fournisseurs) — consultation</summary>${sim}</details>`;}
  else if(D.k==="vers"){t="Brouillons enregistrés · "+socCourt(a.soc);const V=(B31.vers[id]||[]).filter(v=>v.soc===a.soc);
    c+=`<p>Brouillons de ${esc(socCourt(a.soc))}, immuables. Recharger copie leurs PU dans le chiffrage actif ; les lignes verrouillées du chiffrage actif sont conservées telles quelles ; la version reste intacte. Double confirmation.</p>`;
    c+=V.length?`<ul class="b31-ul">${V.map(v=>`<li data-b31-v="${v.version}"><b>v${v.version}</b> · ${esc(v.label||"")} · ${esc(fmtDT(v.created_at))} · TTC ${esc(v.totaux?fmtN(+v.totaux.ttc):"incomplet")} · art. 44 ${esc((v.art44||{}).etat||"?")}${editable()?` <button type="button" class="b31-lnk" data-b31-rest="${v.version}" data-act="${act(()=>b31Restaurer(id,a,v))}">Recharger dans le brouillon</button>`:""}</li>`).join("")}</ul>`:`<p>Aucun brouillon enregistré. Utilisez « Enregistrer le brouillon ».</p>`;}
  else if(D.k==="scen"){t="Scénarios · "+socCourt(a.soc);const SC=(ET.doc&&ET.doc.scenarios)||{};
    c+=`<p>Trois scénarios propres à ${esc(socCourt(a.soc))}, chacun défini par un pourcentage que vous saisissez par rapport à l'estimation TTC. Ils ne sont jamais recopiés vers une autre société.</p>`;
    c+=B31_SCEN.map(([k,l])=>{const s=SC[k]||{},v=D.pct!=null&&D.cible===k?D.pct:s.pct,c2=v!=null&&ET.E.c!=null?b31Cible(ET.E.c,v):null,A=c2!=null?b31Art44(ET.R,c2,ET.E.c):null;
      return`<div class="b31-sc" data-b31-sc="${k}"><b>${l}</b><input class="b31-in" data-b31-scin="${k}" value="${esc(v==null?"":String(v).replace(".",","))}" placeholder="% saisi par vous" aria-label="Pourcentage du scénario ${l}"><span>${v==null?"non défini":esc(b31PctTxt(v)+" = "+b31PartTxt(v))+(c2!=null?" · cible "+b31Dh(c2)+" TTC":"")}</span>${A?b31Pill(A.k,A.k==="bornes"?"art. 44 : bornes":A.k==="verifier"?"art. 44 : à vérifier":"art. 44 : hors bornes"):""}${s.le?`<small>Enregistré le ${esc(fmtDT(s.le))}</small>`:""}
        ${editable()?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{const inp=document.querySelector(`[data-b31-scin="${k}"]`),pv=b31ParsePct(inp&&inp.value);if(pv==null)return toast("Pourcentage non reconnu.");const n={...SC,[k]:{pct:pv,le:new Date().toISOString(),par:S.role.me||null}};b31SaveDoc(id,a,{scenarios:n,actif:k},"scénario "+l+" = "+b31PctTxt(pv)).then(()=>{B31.dlg={id,k:"scen"};render();toast("Scénario "+l+" enregistré pour "+socCourt(a.soc)+".");}).catch(e=>toast("Impossible : "+(e&&e.message||e)));})}">Enregistrer</button>`:""}${v!=null?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{B31.pct[id]=String(v).replace(".",",");B31.mode[id]="pct";B31.prev[id]=b31Previsu(id,a,v);B31.dlg=null;render();})}">Prévisualiser</button>`:""}</div>`;}).join("");
    if(D.pct!=null&&!D.cible)c+=`<p class="b31-src">Pourcentage courant ${esc(b31PctTxt(D.pct))} : choisissez le scénario où l'enregistrer.</p>${B31_SCEN.map(([k,l])=>`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{B31.dlg={id,k:"scen",pct:D.pct,cible:k};render();})}">Placer dans « ${l} »</button>`).join(" ")}`;}
  return`<div class="fsheet b31-dlg" role="dialog" aria-modal="true" aria-label="${esc(t)}"><div class="fsback" data-act="${ferme}"></div><div class="fspanel b31-dp"><div class="fshead"><div><div class="fshtitle">${esc(t)}</div><div class="fshsub">${esc(a.ref||id)} · lecture des preuves conservées, rien n'est effacé</div></div><button type="button" class="fsx" aria-label="Fermer" data-act="${ferme}">${b31Ic("x")}</button></div><div class="fsbody b31" id="fsbody">${c}</div></div></div>`;}
/* ---------- PDF vectoriel du récapitulatif (pdfmake, déjà utilisé par B2.1) : document de travail, pas une pièce de dépôt ---------- */
async function b31Pdf(id){const a=S.ao[id];if(!a||B31.pdfBusy)return;B31.pdfBusy=true;render();
  try{const ET=b31Etat(id,a),pm=await b21PdfLib(),K=B21_PDF.K,now=new Date(),gen=fmt(now)+" à "+pad(now.getHours())+"h"+pad(now.getMinutes()),X=ET.X,T=ET.T;
    const L=b31Lignes(id),body=[[{text:"N°",style:"th"},{text:"Désignation",style:"th"},{text:"Unité",style:"th"},{text:"Qté",style:"th",alignment:"right"},{text:"PU HT",style:"th",alignment:"right"},{text:"PT HT",style:"th",alignment:"right"}]];
    L.forEach(r=>{const p=X.p[r.k],has=p!==undefined&&p!==""&&p!=null;body.push([{text:String(r.x.n||""),color:K.muted},String(r.x.d||""),String(r.x.u||""),{text:r.qq==null?"illisible":fmtQ(r.qq),alignment:"right"},{text:has?fmtN(p):"manquant",alignment:"right",color:has?K.ink:K.red},{text:has&&r.qq!=null?fmtN(ligneC(r.qq,p)/100):"—",alignment:"right"}]);});
    const kv=(k,v)=>[{text:k,color:K.ink2},{text:v,bold:true,alignment:"right"}];
    const dd={pageSize:"A4",pageOrientation:"landscape",pageMargins:[40,50,40,46],defaultStyle:{font:"Roboto",fontSize:9.5,color:K.ink},styles:{th:{bold:true,fillColor:K.th,fontSize:9},h:{fontSize:13,bold:true,margin:[0,10,0,4]}},
      info:{title:"Chiffrage "+(a.ref||id)+" — "+socCourt(a.soc),author:"EAIOS",subject:"B3.1 Chiffrage · document de travail",creator:"EAIOS "+(typeof APP_VERSION!=="undefined"?APP_VERSION:""),producer:"EAIOS "+B31.v+" (pdfmake)"},
      footer:(p,n)=>({columns:[{text:"EAIOS · B3.1 Chiffrage · "+(a.ref||id)+" · "+socCourt(a.soc)+" · généré le "+gen+" · document de travail interne, non destiné au dépôt",color:K.muted},{text:"Page "+p+" / "+n,alignment:"right",width:70}],fontSize:8,margin:[40,14,40,0]}),
      content:[{text:"Chiffrage · "+(a.ref||id),fontSize:18,bold:true},{text:String(a.obj||""),margin:[0,2,0,2]},{text:socCourt(a.soc)+" · "+(a.mo||"")+" · statut : "+ET.statut.t,color:K.ink2,margin:[0,0,0,8]},
        {columns:[{width:"*",table:{widths:["*","auto"],body:[kv("Estimation MO TTC",ET.E.c==null?"non renseignée":b31Dh(ET.E.c)),kv("Offre TTC",ET.complet?b31Dh(T.ttcC):"incomplète ("+T.miss+" PU manquants)"),kv("Écart (TTC / TTC)",ET.complet&&ET.E.c?b31EcartTxt(ET.A44.ecart):"—")]},layout:"lightHorizontalLines"},
          {width:"*",table:{widths:["*","auto"],body:[kv("Total HT",ET.complet?b31Dh(T.htC):"incomplet"),kv(ET.tva.txt.split(" : ")[0].replace(" (taux relevé dans le dossier)",""),ET.complet?b31Dh(T.tvaC):"—"),kv("Total TTC",ET.complet?b31Dh(T.ttcC):"incomplet")]},layout:"lightHorizontalLines"}],columnGap:18},
        ET.complet?{text:"Arrêté à : "+enLettres(T.ttcC/100)+" toutes taxes comprises.",italics:true,margin:[0,6,0,0]}:{text:"Montant en lettres non produit : offre incomplète.",italics:true,color:K.red,margin:[0,6,0,0]},
        {text:"Contrôle art. 44 (décret 2-22-431)",style:"h"},{text:ET.R.lab+" — "+ET.A44.t+(ET.A44.minC!=null?" (bornes "+b31Dh(ET.A44.minC)+" à "+b31Dh(ET.A44.maxC)+" TTC)":""),margin:[0,0,0,2]},{text:"Source : "+B31_DECRET.ref+" — "+B31_DECRET.url,color:K.muted,fontSize:8},
        {text:"Coût et marge",style:"h"},{text:ET.C.k&&ET.C.k===ET.C.N&&ET.complet?"Coût HT "+b31Dh(ET.C.coutC)+" · marge "+b31Dh(T.htC-ET.C.coutC)+" · taux de marge sur vente "+((T.htC-ET.C.coutC)/T.htC*100).toFixed(1).replace(".",",")+" % (marge ÷ prix HT)":"Coûts incomplets : "+ET.C.k+"/"+ET.C.N+" ligne(s) avec sous-détail ; marge globale non calculée."},
        {text:ET.tva.txt,color:K.ink2,margin:[0,2,0,0]},
        {text:"Bordereau des prix ("+L.length+" lignes)",style:"h",pageBreak:"before"},{table:{headerRows:1,widths:[34,"*",44,60,72,82],body},layout:"lightHorizontalLines"}]};
    const buf=await new Promise((res,rej)=>{try{pm.createPdf(dd).getBuffer(b=>res(b));}catch(e){rej(e);}}),bytes=new Uint8Array(buf),nom="Chiffrage_"+safeN(a.ref||id)+"_"+safeN(socCourt(a.soc))+".pdf";
    B31.pdf[id]={bytes,nom,gen};
    const v=$("#viewer"),bd=dceVue("Chiffrage "+(a.ref||id)+" · "+socCourt(a.soc)+" · "+gen,nom,bytes);bd.innerHTML='<p class="hint" style="padding:16px">Ouverture du PDF…</p>';
    const lib=await ensurePdf(),pdf=await lib.getDocument({data:bytes.slice(),isEvalSupported:false}).promise;if(v.hidden)return;
    bd.innerHTML=`<p class="hint" style="margin:0 0 8px">PDF vectoriel · ${pdf.numPages} page(s) · « Enregistrer » sauvegarde exactement ce fichier.</p>`;const w=Math.max(200,Math.min(bd.clientWidth-20,1000));
    for(let i=1;i<=pdf.numPages;i++){if(v.hidden)return;const pg=await pdf.getPage(i),s=w/pg.getViewport({scale:1}).width,vp=pg.getViewport({scale:s}),c=document.createElement("canvas");c.width=Math.floor(vp.width);c.height=Math.floor(vp.height);c.className="dce-ap-page";bd.appendChild(c);await pg.render({canvasContext:c.getContext("2d"),viewport:vp}).promise;}}
  catch(e){toast("PDF indisponible : "+(e&&(e.message||e.code)||"erreur"));}finally{B31.pdfBusy=false;render();}}
/* ---------- saisie en direct ---------- */
function b31MajLive(){const w=document.querySelector("[data-b31]");if(!w)return;const id=w.dataset.b31,a=S.ao[id];if(!a)return;const ET=b31Etat(id,a);
  const r=document.getElementById("b31-recap");if(r)r.innerHTML=b31Recap(id,a,ET);}
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(!t||!t.dataset)return;
  if(t.dataset.bp&&document.querySelector("[data-b31]")&&S.aoId){const X=bpX(S.aoId);X.srcL=X.srcL||{};X.srcL[t.dataset.bp]={m:"manuel",le:new Date().toISOString()};if(t.value==="")delete X.srcL[t.dataset.bp];
    const el=document.getElementById("bpt"+t.dataset.bp),[l,i]=t.dataset.bp.split("-").map(Number),b=S.bp[S.aoId];if(el&&b){const x=b.lots[l].lignes[i],qq=bpQ(S.aoId,l,i,x);el.innerHTML=t.value!==""&&qq!=null?fmtN(ligneC(qq,t.value)/100):'<span class="b31-ko-t">—</span>';}
    delete B31.prev[S.aoId];b31MajLive();}
  else if(t.dataset.b31Q){B31.recherche[t.dataset.b31Q]=t.value;B31.n[t.dataset.b31Q]=60;clearTimeout(b31MajLive._q);b31MajLive._q=setTimeout(render,250);}
  else if(t.dataset.b31Pct){B31.pct[t.dataset.b31Pct]=t.value;delete B31.prev[t.dataset.b31Pct];clearTimeout(b31MajLive._p);b31MajLive._p=setTimeout(render,350);}
  else if(t.dataset.b31Simh){B31.simH[t.dataset.b31Simh]=t.value;clearTimeout(b31MajLive._s);b31MajLive._s=setTimeout(render,400);}});
document.getElementById("view").addEventListener("change",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.bp&&document.querySelector("[data-b31]"))render();});
document.getElementById("view").addEventListener("toggle",e=>{const t=e.target;if(t&&t.matches&&t.matches("details[data-b31-regle]")){const w=t.closest("[data-b31]");if(w)B31.ouv[w.dataset.b31+"|regle"]=t.open;}},true);
/* ---------- raccordement : étape « Prix » → B3.1 ; vue pleine largeur dans le bureau B3.1 ---------- */
{const _aoStepsB31=aoSteps;aoSteps=function(id,a){const L=_aoStepsB31(id,a),n=L.find(s=>s.k==="prix");if(n)n.body=()=>vB31(id,a);return L;};}
function b31Plein(id){return typeof MPN!=="undefined"&&!!MPN.dos&&MPN.dos.id===id&&MPN.dos.bur==="MP-B3.1"&&MPN.dos.k==="prix"&&!MPN.dos.global&&S.aoId===id;}
{const _mpnDossierB31=mpnDossier;mpnDossier=function(d){let h=_mpnDossierB31(d);
  try{const id=S.aoId;if(!id||!b31Plein(id))return h;
    const t=h.replace('<div class="mpn" data-mpn-dossier-vue=','<div class="mpn b31-full" data-mpn-dossier-vue=')
      .replace(/<div class="mpd-kick">[^<]*<\/div><h2 class="mpn-h" id="mpn-h" tabindex="-1">[^<]*<\/h2><div class="mpn-dres"><span class="pill [^"]*">[^<]*<\/span><span>[^<]*<\/span><\/div>/,"");
    return t.indexOf('id="mpn-h"')!==t.lastIndexOf('id="mpn-h"')||t.indexOf("b31-full")<0?h:t;}catch(e){return h;}};}
/* ---------- styles B3.1 (palette EAIOS ivoire / or / charbon, mode sombre ; mise en page 72 / 28 par requête de conteneur) ---------- */
const B31_TOK=`--b21-card:var(--surface,#18212D);--b21-ivoire:rgba(195,160,106,.07);--b21-line:var(--line,#2B3542);--b21-line2:rgba(255,255,255,.06);--b21-voile:rgba(195,160,106,.12);--b21-or-p:var(--ea-or-clair,#DCC193);--b21-gold:#9C7837;--b21-noir:#F3EEE4;--b21-okbg:rgba(31,122,77,.18);--b21-todobg:rgba(195,160,106,.16);--b21-kobg:rgba(166,61,50,.2);--b21-nabg:rgba(255,255,255,.07)`;
const B31_CSS=`.b31{--b21-card:#FFFFFF;--b21-ivoire:#FBF7EF;--b21-line:#E6DFD2;--b21-line2:#EFEAE0;--b21-or:var(--ea-or,#C3A06A);--b21-or-p:var(--ea-or-profond,#7A5C2F);--b21-gold:#94702F;--b21-noir:var(--ea-noir,#0E0F11);--b21-voile:#F6EFE2;--b21-ink:var(--ink,#16171A);--b21-muted:var(--muted,#6B6E75);
  --b21-okbg:#E9F4EE;--b21-todobg:#FBF1DE;--b21-kobg:#FBEAE7;--b21-nabg:#F1F0EC;color:var(--b21-ink);font-size:13.5px;display:flex;flex-direction:column;gap:12px;container:b31/inline-size;min-width:0}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .b31{${B31_TOK}}}
:root[data-theme="dark"] .b31{${B31_TOK}}
.b31 *{box-sizing:border-box}
.b31-ic{width:18px;height:18px;flex:0 0 auto;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;vertical-align:-4px}
.b31-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px 24px}
.b31-h1{outline:none;margin:0;font-family:var(--display,inherit);font-size:28px;font-weight:600;line-height:1.1;text-transform:none;color:var(--b21-ink)}
.b31-sub{margin:3px 0 0;font-size:14px;color:var(--b21-muted)}
.b31-chip{display:inline-block;border:1px solid var(--b21-line);background:var(--b21-ivoire);border-radius:6px;padding:0 6px;font-size:11px;line-height:17px;color:var(--b21-muted);vertical-align:1px}
.b31-dos{display:flex;gap:10px;align-items:center;border:1px solid var(--b21-line);background:var(--b21-card);border-radius:10px;padding:8px 14px;max-width:min(100%,620px);color:var(--b21-or-p)}
.b31-dos div{display:flex;flex-direction:column;min-width:0}.b31-dos b{color:var(--b21-ink);font-size:13.5px;overflow-wrap:anywhere}.b31-dos span{font-size:12px;color:var(--b21-muted)}
.b31-tabs{display:flex;flex-wrap:wrap;align-items:center;gap:6px 16px;border-bottom:1px solid var(--b21-line)}
.b31-tl{display:flex;gap:2px;overflow-x:auto;max-width:100%;scrollbar-width:thin}
.b31-tl button{display:inline-flex;align-items:center;gap:7px;background:none;border:none;border-bottom:2px solid transparent;padding:9px 14px 8px;font:600 13.5px/1.2 var(--body,inherit);color:var(--b21-muted);cursor:pointer;white-space:nowrap}
.b31-tl button[aria-selected="true"]{color:var(--b21-ink);border-bottom-color:var(--b21-or)}.b31-tl button small{font-weight:400;font-size:11px}
.b31-tn{font-size:12px;color:var(--b21-muted);margin-left:auto;padding:4px 0}
.b31-kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.b31-kpi{display:flex;gap:12px;align-items:center;background:var(--b21-card);border:1px solid var(--b21-line);border-radius:12px;padding:12px 16px;min-width:0}
.b31-kpi>div{display:flex;flex-direction:column;min-width:0}
.b31-kic{width:40px;height:40px;border-radius:50%;background:var(--b21-ivoire);border:1px solid var(--b21-line);display:inline-flex;align-items:center;justify-content:center;color:var(--b21-or-p);flex:0 0 auto}.b31-kic .b31-ic{width:20px;height:20px}
.b31-kl{font-size:12px;color:var(--b21-muted)}.b31-kv{font-size:20px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.25;overflow-wrap:anywhere}.b31-ks{font-size:11.5px;color:var(--b21-muted);overflow-wrap:anywhere}
.b31-kinc .b31-kv,.b31-kko .b31-kv{color:var(--red,#A63D32)}
.b31-modes{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}
.b31-mg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;flex:1 1 560px;min-width:0}
.b31-mode{display:flex;gap:10px;align-items:center;text-align:left;background:var(--b21-card);border:1px solid var(--b21-line);border-radius:10px;padding:9px 12px;cursor:pointer;color:var(--b21-or-p);font:inherit;min-width:0}
.b31-mode span{display:flex;flex-direction:column;min-width:0}.b31-mode b{color:var(--b21-ink);font-size:13.5px}.b31-mode small{color:var(--b21-muted);font-size:11.5px}
.b31-mode[aria-checked="true"]{border-color:var(--b21-or);box-shadow:inset 0 0 0 1px var(--b21-or);background:var(--b21-ivoire)}
.b31-mx{display:flex;gap:8px;flex-wrap:wrap;align-items:stretch}
.b31-lnk{display:inline-flex;align-items:center;gap:6px;background:none;border:1px solid var(--b21-line);border-radius:10px;padding:8px 12px;font:600 13px/1.2 var(--body,inherit);color:var(--b21-ink);cursor:pointer}
.b31-lnk:hover,.b31-mode:hover,.b31-btn:hover{border-color:var(--b21-or)}
.b31 button:focus-visible,.b31 input:focus-visible,.b31 summary:focus-visible,.b31 a:focus-visible{outline:2px solid var(--b21-or);outline-offset:2px}
.b31-cnt{font-style:normal;background:var(--b21-todobg);color:var(--b21-or-p);border-radius:999px;padding:0 7px;font-size:11.5px}
.b31-div{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;background:var(--b21-todobg);border:1px solid #EBD7AE;border-radius:10px;padding:8px 12px;font-size:12.5px;color:var(--b21-or-p)}
.b31-div>span{flex:1 1 360px;min-width:0;overflow-wrap:anywhere}.b31-div b{color:var(--b21-ink)}.b31-div .b31-lnk{padding:5px 10px;font-size:12px}
.b31-card{background:var(--b21-card);border:1px solid var(--b21-line);border-radius:12px;padding:14px 16px;min-width:0;box-shadow:0 1px 2px rgba(20,16,8,.04)}
.b31-card h3{margin:0 0 10px;font-family:var(--display,inherit);font-size:16px;font-weight:600;text-transform:none;letter-spacing:0;display:flex;align-items:center;gap:8px;color:var(--b21-ink)}
.b31-card h3 .b31-ic{color:var(--b21-or-p)}
.b31-regle{padding:0}.b31-regle>summary{list-style:none;display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;padding:10px 16px;cursor:pointer;color:var(--b21-or-p)}
.b31-regle>summary::-webkit-details-marker{display:none}.b31-regle>summary>span{display:flex;flex-wrap:wrap;gap:2px 8px;align-items:baseline;min-width:0;color:var(--b21-ink)}
.b31-regle>summary small{flex-basis:100%;font-size:11.5px;color:var(--b21-muted)}.b31-regle[open] .b31-cv{transform:rotate(180deg)}
.b31-or{font-style:normal;color:var(--b21-or-p)}.b31-ko-t{color:var(--red,#A63D32);font-style:normal}
.b31-rr{margin-left:auto;display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--b21-muted)}.b31-rr b{color:var(--b21-ink)}
.b31-rb{padding:0 16px 14px;border-top:1px solid var(--b21-line2);font-size:13px;line-height:1.5}.b31-rb p{margin:8px 0}
.b31-src{font-size:11.5px;color:var(--b21-muted);line-height:1.45;margin:6px 0 0;overflow-wrap:anywhere}.b31-src a{color:var(--b21-or-p)}
.b31-simp{border:1px dashed var(--b21-line);border-radius:10px;padding:10px 12px;margin-top:8px}.b31-simp label{display:block;font-size:12px;font-weight:600;margin-bottom:6px}
.b31-hyp{background:var(--b21-todobg);border-radius:8px;padding:8px 10px;font-size:12.5px}
.b31-in{width:100%;max-width:100%;border:1px solid var(--b21-line);border-radius:8px;padding:8px 10px;font:14px/1.3 var(--body,inherit);background:var(--b21-card);color:var(--b21-ink)}
.b31-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;align-items:start}
@container b31 (min-width:1000px){.b31-grid{grid-template-columns:minmax(0,72fr) minmax(300px,28fr)}.b31-side{position:sticky;top:12px}}
.b31-side{display:flex;flex-direction:column;gap:12px;min-width:0}
.b31-bpu{padding:0;overflow:hidden}
.b31-bh{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px 16px;padding:12px 16px;border-bottom:1px solid var(--b21-line2)}
.b31-bh>div:first-child{display:flex;gap:10px;align-items:center;min-width:0;color:var(--b21-or-p)}.b31-bh h3{margin:0}.b31-bh span{font-size:12px;color:var(--b21-muted)}.b31-big{width:22px;height:22px}
.b31-tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.b31-srch{display:flex;align-items:center;gap:6px;border:1px solid var(--b21-line);border-radius:8px;padding:0 10px;background:var(--b21-card);color:var(--b21-muted);min-width:0;flex:1 1 220px}
.b31-srch input{border:none;outline:none;background:none;padding:7px 0;font:13.5px var(--body,inherit);color:var(--b21-ink);min-width:0;width:100%}
.b31-btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:1px solid var(--b21-line);background:var(--b21-card);color:var(--b21-ink);border-radius:8px;padding:8px 14px;font:600 13.5px/1.2 var(--body,inherit);cursor:pointer;text-align:center}
.b31-btn[disabled]{opacity:.55;cursor:not-allowed}.b31-btn[aria-disabled="true"]{opacity:.6}.b31-btn[aria-pressed="true"]{background:var(--b21-ivoire);border-color:var(--b21-or)}
.b31-sm{padding:6px 10px;font-size:12.5px}.b31-xs{padding:3px 8px;font-size:12px}
.b31-gold{background:var(--b21-gold);border-color:var(--b21-gold);color:#fff}.b31-gold:hover{filter:brightness(1.06)}
.b31-al{display:flex;gap:8px;align-items:flex-start;margin:0;padding:8px 16px;font-size:12.5px;background:var(--b21-todobg);color:var(--b21-or-p)}
.b31-tw{max-width:100%;overflow-x:auto}
.b31-tab{width:100%;border-collapse:collapse;table-layout:fixed;font-variant-numeric:tabular-nums}
.b31-tab col.c1{width:46px}.b31-tab col.c3{width:52px}.b31-tab col.c4{width:74px}.b31-tab col.c5{width:112px}.b31-tab col.c6{width:116px}.b31-tab col.c7{width:112px}
.b31-tab th{font-size:11.5px;font-weight:600;color:var(--b21-muted);text-align:left;padding:8px 8px;border-bottom:1px solid var(--b21-line);background:var(--b21-ivoire);position:sticky;top:0;z-index:1}
.b31-tab thead th:nth-child(n+4){text-align:right}
.b31-tab td{padding:7px 8px;border-bottom:1px solid var(--b21-line2);vertical-align:top;font-size:13px}
.b31-n{color:var(--b21-muted);font-size:12px}.b31-d{overflow-wrap:anywhere}.b31-dt{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;line-height:1.4}
.b31-q,.b31-t{text-align:right;white-space:nowrap}.b31-t{font-weight:600}
.b31-p{text-align:right}.b31-p input{width:100%;text-align:right;border:1px solid var(--b21-line);border-radius:6px;padding:5px 7px;font:600 13px/1.2 var(--body,inherit);background:var(--b21-card);color:var(--b21-ink);font-variant-numeric:tabular-nums}
.b31-p input:disabled{background:var(--b21-nabg);color:var(--b21-ink)}.b31-nop .b31-p input{border-color:#E2B4AC;background:var(--b21-kobg)}
.b31-pv{display:block;color:var(--b21-or-p);font-weight:600;font-size:12px;margin-top:2px}
.b31-a{text-align:right;white-space:nowrap}
.b31-ib{background:none;border:1px solid transparent;border-radius:6px;padding:3px;color:var(--b21-muted);cursor:pointer;vertical-align:middle}.b31-ib[aria-pressed="true"]{color:var(--b21-or-p);border-color:var(--b21-or);background:var(--b21-ivoire)}
.b31-sdb{display:inline-flex;align-items:center;gap:2px;background:none;border:none;color:var(--b21-muted);font:600 11.5px var(--body,inherit);cursor:pointer;padding:3px 4px}.b31-sdb.on{color:var(--b21-or-p)}.b31-sdb[aria-expanded="true"] .b31-ic{transform:rotate(180deg)}.b31-sdb .b31-ic{width:14px;height:14px}
.b31-lk td{background:var(--b21-ivoire)}
.b31-sec th{position:static;background:var(--b21-voile);color:var(--b21-ink);font-size:12px;text-align:left!important;padding:6px 10px}
.b31-sl{display:block;color:var(--b21-muted);font-size:11px;margin-top:2px}
.b31-sug{margin-top:6px;border:1px dashed var(--b21-or);border-radius:8px;padding:6px 8px;font-size:12px;display:flex;flex-direction:column;gap:3px;background:var(--b21-ivoire)}.b31-sug small{color:var(--b21-muted)}.b31-sug .b31-btn,.b31-sug .b31-pill{align-self:flex-start}
.b31-sdr td{background:var(--b21-ivoire)}
.b31-sdi h4{margin:2px 0 8px;font-size:13px}.b31-sdi p{margin:4px 0;font-size:12.5px}
.b31-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr));gap:8px}
.b31-tile{border:1px solid var(--b21-line);border-radius:8px;padding:7px 10px;background:var(--b21-card);display:flex;flex-direction:column;gap:2px}.b31-tile span{font-size:11.5px;color:var(--b21-muted)}.b31-tile b{font-size:14px}
.b31-tc{border-color:var(--b21-or)}
.b31-none{text-align:center;color:var(--b21-muted);padding:18px!important}
.b31-more{display:block;width:100%;border:none;border-top:1px solid var(--b21-line2);background:var(--b21-ivoire);padding:10px;font:600 13px var(--body,inherit);color:var(--b21-or-p);cursor:pointer}
.b31-arr{display:flex;gap:10px;align-items:flex-start;padding:12px 16px;border-top:1px solid var(--b21-line);color:var(--b21-or-p)}.b31-arr div{display:flex;flex-direction:column;gap:2px;min-width:0}.b31-arr b{color:var(--b21-ink);font-size:13px;overflow-wrap:anywhere}.b31-arr span{font-size:11.5px;color:var(--b21-muted)}
.b31-rec .b31-rr{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--b21-line2);margin:0;color:var(--b21-ink);font-size:13px}
.b31-rec .b31-rr b{font-variant-numeric:tabular-nums;text-align:right}
.b31-rec .b31-ttc{background:var(--b21-ivoire);border:1px solid var(--b21-or);border-radius:8px;padding:8px 10px;margin:6px 0;font-size:14.5px}
.b31-ctl ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
.b31-ctl li>button,.b31-ctl li>div{display:flex;gap:8px;align-items:flex-start;width:100%;text-align:left;background:none;border:none;padding:6px 4px;font:13px/1.4 var(--body,inherit);color:var(--b21-ink);border-radius:6px}
.b31-ctl li>button{cursor:pointer}.b31-ctl li>button:hover{background:var(--b21-ivoire)}.b31-ctl span{flex:1;min-width:0;overflow-wrap:anywhere}.b31-go{transform:rotate(-90deg);color:var(--b21-muted)}
.b31-c-ok .b31-ic{color:var(--green,#1F7A4D)}.b31-c-warn .b31-ic{color:var(--b21-or-p)}.b31-c-ko .b31-ic{color:var(--red,#A63D32)}
.b31-pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:11.5px;font-weight:600;font-style:normal;line-height:18px;vertical-align:1px}
.b31-ok{background:var(--b21-okbg);color:var(--green,#1F7A4D)}.b31-ko{background:var(--b21-kobg);color:var(--red,#A63D32)}.b31-todo{background:var(--b21-todobg);color:var(--b21-or-p)}.b31-neu{background:var(--b21-nabg);color:var(--b21-muted)}
.b31-sim .b31-pl{display:flex;flex-direction:column;gap:6px;font-size:12.5px;color:var(--b21-muted)}
.b31-eq{margin:10px 0 4px;font-size:13.5px}.b31-eq b{color:var(--b21-or-p)}
.b31-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.b31-need{display:flex;gap:8px;align-items:flex-start;background:var(--b21-todobg);border-radius:8px;padding:8px 10px;margin-top:10px;font-size:12.5px;color:var(--b21-or-p)}.b31-need span{color:var(--b21-ink)}
.b31-prv{margin-top:10px;border:1px solid var(--b21-or);border-radius:10px;padding:8px 10px;font-size:12.5px;background:var(--b21-ivoire)}.b31-prv p{margin:4px 0}
.b31-ia p{font-size:12.5px;line-height:1.5;margin:6px 0}
.b31-base{margin-top:10px;border-top:1px solid var(--b21-line2);padding-top:8px;font-size:12.5px}.b31-base p{margin:4px 0}.b31-base .b31-btn{margin-top:4px}
.b31-prv .b31-hyp{margin:6px 0}.b31-blk{border:1px solid var(--red,#A63D32)}.b31-blk small{display:block;margin-top:4px}.b31-just summary{cursor:pointer;font-weight:600;color:var(--b21-or-p);margin:6px 0}.b31-just li small{display:block}
.b31-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;background:var(--b21-card);border:1px solid var(--b21-line);border-radius:12px;padding:10px 14px;box-shadow:0 -2px 10px rgba(20,16,8,.06)}
@media (min-width:900px){.b31-bar{position:sticky;bottom:8px;z-index:3}}
.b31-bs{display:flex;gap:8px;align-items:center;color:var(--b21-or-p);font-size:13px;min-width:0;flex:1 1 260px}.b31-bs span{color:var(--b21-ink);overflow-wrap:anywhere}
.b31-ba{display:flex;flex-wrap:wrap;gap:8px}
.b31-bn{flex-basis:100%;margin:0;font-size:11.5px;color:var(--b21-muted)}
.b31-vide{display:flex;gap:12px;align-items:flex-start;color:var(--b21-or-p)}.b31-vide b{color:var(--b21-ink)}.b31-vide p{margin:4px 0 0;color:var(--b21-ink);font-size:13px}
.b31-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.b31-sc{display:grid;grid-template-columns:110px minmax(120px,160px) minmax(0,1fr) auto auto auto;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid var(--b21-line2)}.b31-sc small{grid-column:1 / -1;color:var(--b21-muted)}
.b31-ul{margin:4px 0 10px;padding-left:18px;font-size:13px;line-height:1.5}.b31-ul li{margin:3px 0;overflow-wrap:anywhere}
.b31-dlg .b31-dp{max-width:min(980px,100vw);width:min(980px,100vw)}.b31-dlg .fsbody h4{margin:14px 0 4px;font-size:14px}
.b31-old summary{cursor:pointer;font-weight:600;margin:12px 0 6px}
.b31-ro{display:inline-block;margin:4px 8px 4px 0;padding:3px 8px;border:1px dashed var(--b21-line,#E6DFD2);border-radius:6px;font-size:12px;color:var(--b21-muted,#6B6E75);font-style:italic}
.b31-sdp{max-width:min(860px,100vw)!important;width:min(860px,100vw)}
@media (min-width:900px){main.wide:has(.b31-full){max-width:1680px!important}}
.b31-full .aolay{grid-template-columns:minmax(0,1fr)!important}
.b31-full .mpn-dos{display:none}
.b31-full .mpn-dnav{margin-top:10px;display:flex;align-items:center;gap:10px}.b31-full .mpn-dnav h2{margin:0;font-size:11px;white-space:nowrap}
.b31-full .mpn-dnav ul{flex-wrap:nowrap;overflow-x:auto;gap:6px;scrollbar-width:thin;padding-bottom:2px}
.b31-full .mpn-dnav button{flex-direction:row;align-items:center;gap:6px;min-width:0;max-width:none;padding:4px 10px;border-radius:999px;white-space:nowrap;font-size:12px}
.b31-full .mpn-dnav button b{font-size:12px;font-weight:600}.b31-full .mpn-dnav button .pill{font-size:10.5px;padding:0 6px}
@container b31 (max-width:760px){.b31-kpis{grid-template-columns:minmax(0,1fr)}.b31-mg{grid-template-columns:minmax(0,1fr)}.b31-mx>*{flex:1 1 auto;justify-content:center}.b31-tn{margin-left:0}.b31-rr{margin-left:0}
  .b31-tw{overflow:visible}.b31-tab,.b31-tab tbody,.b31-tab tr,.b31-tab td{display:block;width:auto}.b31-tab thead,.b31-tab colgroup{display:none}
  .b31-tab tr.b31-r{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:4px 10px;padding:10px 12px;border-bottom:1px solid var(--b21-line)}
  .b31-tab tr.b31-r td{border:none;padding:0}.b31-tab td.b31-d{grid-column:1 / -1;order:-1}.b31-tab td.b31-n{grid-column:1 / -1;order:-2}
  .b31-tab td.b31-u::before{content:"Unité : "}.b31-tab td.b31-q::before{content:"Qté : "}.b31-tab td.b31-t::before{content:"PT HT : "}
  .b31-tab td.b31-u::before,.b31-tab td.b31-q::before,.b31-tab td.b31-t::before{color:var(--b21-muted);font-weight:400;font-size:11.5px}
  .b31-tab td.b31-q,.b31-tab td.b31-u{text-align:left}.b31-tab td.b31-a{grid-column:1 / -1;text-align:left}
  .b31-tab tr.b31-sec,.b31-tab tr.b31-sdr{display:block}.b31-tab tr.b31-sec th{display:block}.b31-tab tr.b31-sdr td:first-child{display:none}.b31-tab tr.b31-sdr td{padding:8px 12px}
  .b31-sc{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.b31-sc>span{grid-column:1 / -1}
  .b31-ba{width:100%}.b31-ba .b31-btn{flex:1 1 140px}.b31-h1{font-size:24px}}
@media (max-width:640px){.b31-full .mpn-dnav{flex-direction:column;align-items:stretch}.b31-full .mpn-dnav ul{max-width:100%}}`;
function b31Css(){if(document.getElementById("b31-css"))return;const s=document.createElement("style");s.id="b31-css";s.textContent=B31_CSS;document.head.appendChild(s);}
