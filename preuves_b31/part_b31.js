/* ================= B3.1 · Chiffrage (b31-1) =================
   Vue du bureau B3.1 pour UN dossier = UNE société (dossiers frères « id~société » pour les offres séparées, FIN-ISO-001).
   Calculs : méthode canonique existante (cts, ligneC, bpTot ; TVA documentée du dossier depuis b31-6) — Σ(qté × PU arrondi au centime) → HT → TVA → TTC.
   Stockage : PU, quantités, sous-détails et verrous dans bpx/<id> (existant, bpSave) ; validation = prixValide + offre figée
   immuable (offreValider, existant) ; scénarios et statut « à reprendre » dans chiffrage/<id> (historique ajouté, jamais effacé) ;
   brouillons enregistrés = documents immuables chiffrage_versions/<id>~v<n> (création refusée si la version existe).
   Aucune donnée d'une autre société n'est lue pour chiffrer (les onglets n'affichent que nom et statut).
   Contrôle art. 44 du décret n° 2-22-431 (édition TGR 2023, art. 44 B, p. 70) : comparaison en centimes, seuils stricts ;
   régimes études (art. 144), gardiennage / nettoyage / espaces verts (art. 43 II.1.a) ou inconnus : « à vérifier ».
   b31-4 : objectif en % aussi sur un bordereau vide ou partiel (bases justifiées puis ajustement), voir plus bas.
   b31-5 : seuils de l'art. 44 B BLOQUANTS pour l'application de l'objectif en % et pour la validation du chiffrage (garde dans les
   gestionnaires, pas seulement dans l'interface) ; études et régimes inconnus : « à vérifier », aucun seuil inventé.
   b31-6 : (1) TVA documentée par dossier-société (taux, état confirmé / hypothèse, document et page ; taux par ligne si DCE mixte) :
   aucun taux par défaut dans B3.1, TVA et TTC non calculés tant qu'aucun taux n'est saisi ou relevé, confirmation exigée avant validation ;
   (2) provenance durable de chaque PU appliqué (srcL v:6) ; (3) événements de prix immuables chiffrage_evenements/<id>~e<n>, écrits
   AVANT le bordereau ; (4) sous-détail B3.1 propre à la société (matériaux, main-d'œuvre, matériel, transport, sources de devis,
   frais), déboursé sec / coût de revient / vente / marge ; (5) comparaison des scénarios sans écriture. */
const B31={v:"b31-6d",sdBase:{},ev:{},evErr:{},ecr:{},saisie:{},sd:null,sdIA:{},sdBusy:null,sdErr:{},tvaEd:{},cmp:{},provOuv:{},propIA:{},propBusy:null,propErr:{},mode:{},recherche:{},sansPrix:{},n:{},ouv:{},prev:{},pct:{},ch:{},vers:{},etat:{},ia:{},iaBusy:null,dlg:null,simH:{},pdf:{}};
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
/* totaux canoniques à partir d'une table de PU (même algorithme que bpTot / offreCalc) ; b31-6 : TVA par lot ET par taux documenté
   (un seul taux = calcul identique à l'existant) ; taux inconnu → TVA et TTC null, jamais un taux par défaut */
function b31Tot(id,P,M){const b=S.bp[id];if(!b)return null;M=M||b31TvaM(id,S.ao[id]||{});let ht=0,tv=0,n=0,miss=0,zero=0,ok=!!M.calc;const par={};
  b.lots.forEach((L,l)=>{const G={};L.lignes.forEach((x,i)=>{const k=l+"-"+i,p=P[k],qq=bpQ(id,l,i,x);if(p!==undefined&&p!==""&&p!=null&&qq!=null){const c=ligneC(qq,p),r=M.rate(k);ht+=c;n++;if(+p===0)zero++;if(r==null)ok=false;else G[r]=(G[r]||0)+c;}else miss++;});
    Object.entries(G).forEach(([r,hc])=>{const t=Math.floor((hc*+r+50)/100),z=par[r]=par[r]||{htC:0,tvaC:0};tv+=t;z.htC+=hc;z.tvaC+=t;});});
  return{htC:ht,tvaC:ok?tv:null,ttcC:ok?ht+tv:null,n,miss,zero,parTaux:par,tvaOk:ok};}
function b31Lignes(id){const b=S.bp[id];if(!b)return[];const R=[];b.lots.forEach((L,l)=>L.lignes.forEach((x,i)=>R.push({k:l+"-"+i,l,i,x,lot:L.lot||null,qq:bpQ(id,l,i,x)})));return R;}
/* ---------- données du dossier ---------- */
function b31Est(a){const ex=a.exig||{},v=ex.estimation||a.est||null,S2=ex.sources||{};return{c:v?cts(v):null,src:v?(S2.estimation||ex.estimationSource||"Portail PMMP (fiche de la consultation)"):null,base:"TTC"};}
/* b31-6 · TVA documentée du dossier-société (bpx/<id>.tva) : {taux, etat confirme|hypothese, src:{doc,page}, mixte, lignes:{k:taux}, par, le}.
   À défaut, taux relevé automatiquement dans le DCE (exigences) = « à confirmer ». Sinon : non renseignée, aucun taux inventé. */
const B31_TVA_ETAT={confirme:"confirmée",hypothese:"hypothèse non confirmée",dce:"relevée dans le DCE, à confirmer",absent:"non renseignée"};
function b31TauxOk(v){const s=String(v==null?"":v).trim().replace(",",".").replace(/\s|%/g,"");if(!/^\d{1,3}(\.\d{1,2})?$/.test(s))return null;const n=+s;return n>=0&&n<=100?n:null;}
const b31TxPct=t=>String(t).replace(".",",")+" %";
function b31TvaM(id,a,X){X=X||bpX(id);a=a||{};const D=X.tva&&typeof X.tva==="object"?X.tva:null,ex=a.exig||{},dce=ex.tva!=null&&ex.tva!==""&&isFinite(+ex.tva)?+ex.tva:null,dSrc=(ex.sources||{}).tva||null;
  let etat="absent",taux=null,src=null,par=null,le=null;
  if(D&&(D.taux!=null||D.mixte)){etat=D.etat==="confirme"?"confirme":"hypothese";taux=D.taux==null||D.taux===""?null:+D.taux;src=D.src||null;par=D.par||null;le=D.le||null;}
  else if(dce!=null){etat="dce";taux=dce;src={doc:dSrc||"DCE (lecture automatique EAIOS, page non indiquée)",page:null};}
  const lignes=D&&D.mixte&&D.lignes?D.lignes:{},rate=k=>lignes[k]!=null&&lignes[k]!==""?+lignes[k]:taux,L=b31Lignes(id);
  const sans=L.filter(r=>rate(r.k)==null).map(r=>r.x.n||r.k),calc=L.length?!sans.length:taux!=null;
  const set=[...new Set(L.map(r=>rate(r.k)).filter(v=>v!=null))].sort((x,y)=>y-x);
  const conflit=D&&dce!=null&&!D.mixte&&taux!=null&&dce!==taux?"TVA relevée dans le DCE "+b31TxPct(dce)+" ≠ taux saisi "+b31TxPct(taux)+" : à corriger avant toute validation":null;
  const srcT=src&&src.doc?src.doc+(src.page?", p. "+src.page:", page non indiquée"):"source non indiquée";
  const lab=set.length>1?"TVA mixte ("+set.map(b31TxPct).join(", ")+")":set.length?"TVA "+b31TxPct(set[0]):taux!=null?"TVA "+b31TxPct(taux):"TVA";
  let txt=etat==="absent"?"TVA non renseignée : aucun taux relevé dans le DCE ni saisi pour "+socCourt(a.soc)+" — TVA et TTC non calculés (aucun taux inventé)"
    :lab+" "+B31_TVA_ETAT[etat]+" · source : "+srcT+(par||le?" · saisie"+(par?" par "+par:"")+(le?" le "+fmtDT(le):""):"");
  if(etat!=="absent"&&!calc)txt+=" · "+sans.length+" ligne(s) sans taux : TVA et TTC non calculés";
  if(conflit)txt=conflit;
  return{etat,taux,lignes,mixte:!!(D&&D.mixte),rate,calc,sans,set,src,srcT,par,le,conflit,lab,txt,dce,ok:etat==="confirme"&&calc&&!conflit,bloque:!!conflit,D};}
function b31Tva(id,a){return b31TvaM(id,a);}
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
/* coût (b31-6) : sous-détail de LA société, par unité d'ouvrage — matériaux, main-d'œuvre, matériel, transport (quantité × prix de la
   ressource, source : devis daté, référence interne, hypothèse ou proposition IA acceptée).
   Déboursé sec DS = Σ ressources ; coût de revient CR = DS × (1 + frais de chantier) × (1 + frais généraux) × (1 + aléas), bénéfice EXCLU ;
   prix de vente théorique = CR × (1 + bénéfice). Une ressource sans quantité ou sans prix rend le coût de la ligne INCONNU (jamais 0). */
const B31_SDT=[["mat","Matériaux et fournitures","Ciment, acier, agglos…"],["mo","Main-d'œuvre","Chef d'équipe, maçon, manœuvre…"],["mt","Matériel","Bétonnière, engin, location…"],["tr","Transport","Camion, rotation, distance…"]];
if(!SD_T.some(z=>z[0]==="tr"))SD_T.push(["tr","Transport","Camion, rotation, distance…"]);/* le calcul existant (sdDS) compte aussi le transport */
const B31_SRC={devis:"Devis fournisseur",interne:"Référence interne",hypothese:"Hypothèse",ia:"Proposition IA acceptée (hypothèse)"};
const b31Num=v=>v===""||v==null||!isFinite(+v)?null:+v;
function b31SdCalc(id,k,a){const sd=sdOf(id,k);if(!sd)return null;const Xk=bpX(id).k,K=sdK(id),parts=[],inc=[],etr=[],sans=[];let ds=0,nr=0,nh=0;
  B31_SDT.forEach(([t,l])=>{let s0=0;(sd[t]||[]).forEach((r,j)=>{if(!r)return;const q0=b31Num(r.q),p0=b31Num(r.pu);if(!String(r.d||"").trim()&&q0==null&&p0==null)return;nr++;
    if(r.soc&&a&&r.soc!==a.soc){etr.push(l+" : "+(r.d||"ligne "+(j+1)));return;}
    if(q0==null||p0==null||q0<0||p0<0){inc.push(l+" : "+(r.d||"ligne "+(j+1))+(q0==null?" (quantité inconnue)":"")+(p0==null?" (prix inconnu)":""));return;}
    if(r.st==="hypothese"||r.st==="ia"||!r.st)nh++;if(!r.st)sans.push(l+" : "+(r.d||"ligne "+(j+1)));s0+=q0*p0;});
    parts.push([t,l,Math.round(s0*100)/100]);ds+=s0;});
  ds=Math.round(ds*100)/100;const complet=nr>0&&!inc.length&&!etr.length&&ds>0,fc=+K.fc||0,fg=+K.fg||0,al=+K.al||0,ben=+K.ben||0;
  const cFc=ds*fc/100,cFg=(ds+cFc)*fg/100,cAl=(ds+cFc+cFg)*al/100,cr=Math.round((ds+cFc+cFg+cAl)*100)/100,pv=Math.round(cr*(1+ben/100)*100)/100;
  return{ds,parts,complet,inc,etr,sans,nr,nh,K,kDefaut:!Xk,fc:Math.round(cFc*100)/100,fg:Math.round(cFg*100)/100,al:Math.round(cAl*100)/100,cr,frais:Math.round((cr-ds)*100)/100,ben:Math.round((pv-cr)*100)/100,pv};}
function b31CoutU(id,k,a){const c=b31SdCalc(id,k,a||S.ao[id]);if(!c||!c.complet)return null;return Object.assign(c,{cu:c.cr});}
const b31CoutVide=()=>({k:0,N:0,coutC:0,dsC:0,prixC:0,venteC:0,complet:false,kDefaut:true,perte:[],etr:0,inc:0,hyp:0});
/* coûts du bordereau pour une table de PU (par défaut : PU actuels) ; marge seulement si TOUTES les lignes ont un coût connu */
function b31Cout(id,a,P){a=a||S.ao[id]||{};const L=b31Lignes(id),X=bpX(id);P=P||X.p||{};const o=b31CoutVide();o.N=L.length;o.kDefaut=!X.k;
  L.forEach(r=>{const c=b31SdCalc(id,r.k,a),p=P[r.k],has=p!==undefined&&p!==""&&p!=null;if(c){if(c.etr.length)o.etr+=c.etr.length;if(c.inc.length)o.inc++;if(c.nh)o.hyp++;}
    if(!c||!c.complet||r.qq==null)return;o.k++;const cC=ligneC(r.qq,c.cr);o.coutC+=cC;o.dsC+=ligneC(r.qq,c.ds);if(has){const v=ligneC(r.qq,p);o.prixC+=v;if(+p<c.cr)o.perte.push(r.x.n||r.k);}});
  L.forEach(r=>{const p=P[r.k];if(p!==undefined&&p!==""&&p!=null&&r.qq!=null)o.venteC+=ligneC(r.qq,p);});
  o.complet=o.N>0&&o.k===o.N;return o;}
/* marge : base explicite = prix de vente HT ; null tant que le coût n'est pas connu pour toutes les lignes ou qu'un PU manque */
function b31Marge(C,T){if(!C||!C.complet||!T||T.miss||!T.n)return null;const m=T.htC-C.coutC;return{mC:m,pct:T.htC?m/T.htC*100:null,perte:m<0};}
/* ---------- état complet du chiffrage (pur : aucune écriture) ---------- */
function b31Etat(id,a){const X=bpX(id),tva=b31TvaM(id,a,X),T=b31Tot(id,X.p||{},tva),E=b31Est(a),R=b31Regime(a),prixComplet=!!T&&!T.miss&&T.n>0,complet=prixComplet&&T.ttcC!=null;
  let A44=b31Art44(R,complet?T.ttcC:null,E.c);if(prixComplet&&!complet&&A44.k==="incomplet")A44=Object.assign({},A44,{t:"TVA non renseignée ou incomplète : TTC et contrôle de l'art. 44 non calculés"});
  const C=S.bp[id]?b31Cout(id,a):b31CoutVide();
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
  return{X,T,E,R,tva,complet,prixComplet,A44,C,nIA,nLock,iso,cf,O,pv,div,doc,statut,valide};}
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
  return sha256Str(canonJSON({p:+p,soc:a.soc||null,est:b31Est(a).c,reg:b31Regime(a).k,tva:(M=>({e:M.etat,t:M.taux,l:M.lignes,c:M.conflit,x:M.txt}))(b31TvaM(id,a,X)),k:X.k||null,pu:X.p||{},q:X.q||{},lock:X.lock||{},ia:IA?IA.le:null,
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
  /* b31-6 : la cible TTC ne se convertit en HT qu'avec un taux de TVA documenté (aucun taux par défaut) */
  if(!ET.tva.calc)return{ok:false,k:"tva",why:(ET.tva.etat==="absent"?"Taux de TVA non renseigné pour "+socCourt(a.soc)+" : la cible TTC ne peut pas être convertie en HT. Saisissez le taux et sa source (document, page) dans la carte « TVA du dossier » ; aucun taux n'est supposé.":"Taux de TVA manquant pour "+ET.tva.sans.length+" ligne(s) (DCE à taux mixtes) : complétez-les dans la carte « TVA du dossier »."),manque:ET.tva.sans||[]};
  /* un seul taux : conversion TTC → HT au taux documenté (algorithme b31-4 inchangé) ; taux mixtes : facteur sur les TTC de chaque ligne */
  const M=ET.tva,uni=M.set.length===1?M.set[0]:null,cibleC=b31Cible(ET.E.c,p),cibleHtC=uni!=null?Math.round(cibleC*100/(100+uni)):null;let lockC=0,baseC=0,lockT=0,baseT=0;
  lk.forEach(z=>{const c=ligneC(z.r.qq,z.pu);lockC+=c;lockT+=c*(100+M.rate(z.r.k))/100;});lib.forEach(z=>{const c=ligneC(z.r.qq,z.pu);baseC+=c;baseT+=c*(100+M.rate(z.r.k))/100;});
  if(uni!=null?cibleHtC-lockC<=0:cibleC-lockT<=0)return{ok:false,k:"inatteignable",why:"Objectif inatteignable : les "+lk.length+" ligne(s) verrouillée(s) totalisent déjà "+b31Dh(lockC)+" HT, pour une cible de "+(cibleHtC!=null?b31Dh(cibleHtC)+" HT (":"(")+b31Dh(cibleC)+" TTC). Déverrouillez des lignes ou changez le pourcentage.",manque:[],cibleC,cibleHtC,lockC};
  if(!(baseC>0))return{ok:false,why:"Base des lignes non verrouillées nulle : aucun ajustement possible.",manque:[]};
  const f=uni!=null?(cibleHtC-lockC)/baseC:(cibleC-lockT)/baseT,P={...X.p},rows=[];
  lib.forEach(z=>{const k=z.r.k,v=X.p[k],n=Math.round(z.pu*f*100+1e-7)/100;rows.push({k,n:z.r.x.n||"",d:z.r.x.d||"",u:z.r.x.u||"",qq:z.r.qq,avant:v===undefined||v===""||v==null?null:+v,base:z.pu,apres:n,m:z.m,lab:z.lab,conf:z.conf,just:z.just});P[k]=n;});
  const zr=rows.filter(r=>!(r.apres>0));if(zr.length)return{ok:false,why:zr.length+" PU arrondi(s) à 0,00 DH avec ce pourcentage : objectif irréaliste pour ces lignes ; changez le pourcentage ou saisissez-les.",manque:zr.map(r=>r.n||r.k)};
  const T2=b31Tot(id,P,M),st=b31BaseStat(B),g44=b31Garde44(id,a,cibleC,T2.ttcC);
  return{ok:true,p,f,cibleC,cibleHtC,lockC,P,rows,T:T2,resteC:T2.ttcC-cibleC,lockN:lk.length,A44:b31Art44(ET.R,T2.ttcC,ET.E.c),tva:ET.tva,
    g44,nProp:st.ref+st.chiffreur+st.ia,nIA:st.ia,nRef:st.ref,nCh:st.chiffreur,nEx:st.existant,soc:a.soc,sig:b31PrevSig(id,a,p)};}
/* b31-6 · métriques d'un aperçu (pures) : TTC, HT, TVA, coût connu et marge seulement si le coût de TOUTES les lignes est connu */
function b31Metr(id,a,pr){const C=b31Cout(id,a,pr.P),Mg=b31Marge(C,pr.T),E=b31Est(a).c,A=pr.A44;
  return{pct:pr.p,cible_ttc:s2c(pr.cibleC),ttc:s2c(pr.T.ttcC),ht:s2c(pr.T.htC),tva:s2c(pr.T.tvaC),ecart_arrondi:(pr.resteC<0?"-":"")+s2c(Math.abs(pr.resteC)),
    cout_couverture:C.k+"/"+C.N,cout_revient_ht:C.complet?s2c(C.coutC):null,marge_ht:Mg?(Mg.mC<0?"-":"")+s2c(Math.abs(Mg.mC)):null,marge_pct_vente:Mg&&Mg.pct!=null?Math.round(Mg.pct*100)/100:null,
    art44:A.k,borne_min:A.minC!=null?s2c(A.minC):null,borne_max:A.maxC!=null?s2c(A.maxC):null,bloque44:!!(pr.g44&&pr.g44.bloque),verrouillees:pr.lockN,
    bases:{existant:pr.nEx,ref:pr.nRef,chiffreur:pr.nCh,ia:pr.nIA},frais:(K=>({fc:+K.fc||0,fg:+K.fg||0,al:+K.al||0,ben:+K.ben||0,defaut:!bpX(id).k}))(sdK(id)),tva:pr.tva.txt,estimation_ttc:E==null?null:s2c(E)};}
/* ---------- b31-6 · historique automatique des prix ----------
   Toute application de prix (objectif %, acceptation IA, report du sous-détail, saisie manuelle effective, rechargement d'un brouillon,
   taux de TVA) crée D'ABORD un événement immuable chiffrage_evenements/<id>~e<n> (création refusée s'il existe), propre à la société,
   avec avant / après par ligne, provenance, totaux HT / TVA / TTC, auteur, date et contexte ; le bordereau bpx/<id> n'est écrit
   qu'ensuite. Échec de l'historique → aucun prix écrit. Échec du bordereau → état local restauré et événement « échec » ajouté ;
   l'historique affiche alors l'événement comme non appliqué. Aucun événement n'est reconstitué pour les prix antérieurs. */
const b31Sig=P=>sha256Str(canonJSON(P||{}));
const b31TotJ=T=>T?{ht:s2c(T.htC),tva:T.tvaC==null?null:s2c(T.tvaC),ttc:T.ttcC==null?null:s2c(T.ttcC),pu_saisis:T.n,pu_manquants:T.miss}:null;
const B31_MSRC={existant:"PU déjà saisi (même société)",ref:"Référence interne (même société)",chiffreur:"Proposition du Chiffreur",ia:"Proposition IA (Claude)",manuel:"Saisie manuelle",sd:"Sous-détail de la société",version:"Brouillon enregistré"};
async function b31ChargerEv(id){if(!S.db)return;
  try{const s0=await S.db.collection("chiffrage_evenements").where("ao_id","==",id).get();B31.ev[id]=(s0.docs||[]).filter(d=>d.exists).map(d=>Object.assign({doc_id:d.id},d.data())).filter(e=>e.ao_id===id).sort((x,y)=>(y.seq||0)-(x.seq||0));delete B31.evErr[id];}
  catch(e){B31.evErr[id]=String(e&&(e.code||e.message)||e);B31.ev[id]=B31.ev[id]||[];}}
const b31EvSoc=(id,a)=>(B31.ev[id]||[]).filter(e=>e.soc===a.soc);
async function b31EvNouveau(id,a){await b31ChargerEv(id);if(B31.evErr[id])throw new Error("historique illisible ("+B31.evErr[id]+") : rien n'est écrit");
  const L=B31.ev[id]||[],n=L.reduce((m,e)=>Math.max(m,e.seq||0),0)+1,did=id+"~e"+n,ref=S.db.doc("chiffrage_evenements/"+did),g=await ref.get();
  if(g&&g.exists)throw new Error("l'événement e"+n+" existe déjà (écriture concurrente) : rien n'est écrit ; rechargez la page");return{L,n,did,ref};}
/* o : {type, label, lignes:[{k, apres, prov}], tva (nouvel objet TVA, facultatif), lock (facultatif), contexte, base} */
async function b31Ecrire(id,a,o){if(!S.db||!editable())throw new Error(RO_MSG);const X=bpX(id);
  if(X.soc&&X.soc!==a.soc)throw new Error("bordereau rattaché à "+socCourt(X.soc)+" : refus (FIN-ISO-001)");
  if(B31.ecr[id])throw new Error("une écriture de prix est déjà en cours pour ce dossier");B31.ecr[id]=true;
  try{await (chain["bpx"+id]||Promise.resolve());
    /* version : le bordereau enregistré doit être celui affiché (sinon modification ailleurs : rien n'est écrit) */
    const rb=await S.db.doc("bpx/"+id).get(),R0=rb&&rb.exists?rb.data():null;
    if(R0?canonJSON(R0.p||{})!==canonJSON(X.p||{})||canonJSON(R0.tva||null)!==canonJSON(X.tva||null)||(R0.soc&&R0.soc!==a.soc):Object.keys(X.p||{}).length||X.tva)
      throw new Error("le bordereau enregistré diffère de celui affiché (modification ailleurs ou non enregistrée) : rien n'est écrit ; rechargez la page");
    const{L,n,did,ref}=await b31EvNouveau(id,a),now=new Date().toISOString(),me=S.role.me||null;
    const P1=JSON.parse(JSON.stringify(X.p||{})),tva1=o.tva!==undefined?o.tva:(X.tva||null);(o.lignes||[]).forEach(z=>{if(z.apres==null||z.apres==="")delete P1[z.k];else P1[z.k]=z.apres;});
    const M0=b31TvaM(id,a,X),M1=b31TvaM(id,a,Object.assign({},X,{tva:tva1})),T0=b31Tot(id,X.p||{},M0),T1=b31Tot(id,P1,M1),byK=Object.fromEntries(b31Lignes(id).map(r=>[r.k,r]));
    const ev={ao_id:id,soc:a.soc,seq:n,type:o.type,label:String(o.label||"").slice(0,240),le:now,par:me,
      lignes:(o.lignes||[]).map(z=>{const r=byK[z.k],av=(X.p||{})[z.k];if(z.prov)z.prov.evt="e"+n;return{k:z.k,n:r?String(r.x.n||""):"",d:r?String(r.x.d||"").slice(0,140):"",u:r?String(r.x.u||""):"",q:r&&r.qq!=null?String(r.qq):null,
        avant:av===undefined||av===""||av==null?null:+av,apres:z.apres==null||z.apres===""?null:+z.apres,prov:z.prov||null};}),
      tva_avant:{etat:M0.etat,txt:M0.txt},tva_apres:{etat:M1.etat,txt:M1.txt},totaux_avant:b31TotJ(T0),totaux_apres:b31TotJ(T1),
      avant_sig:b31Sig(X.p),apres_sig:b31Sig(P1),precedent:L[0]?L[0].doc_id:null,contexte:o.contexte||null,cible:"bpx/"+id};
    ev.hash=sha256Str(canonJSON(ev));
    try{await ref.set(JSON.parse(JSON.stringify(ev)));}catch(e){throw new Error("historique non enregistré ("+(e&&(e.code||e.message)||"erreur")+") : aucun prix n'est écrit");}
    const sv={p:X.p,srcL:X.srcL,tva:X.tva,lock:X.lock};
    X.p=P1;X.srcL=Object.assign({},X.srcL||{});(o.lignes||[]).forEach(z=>{if(z.prov)X.srcL[z.k]=z.prov;else delete X.srcL[z.k];});if(o.tva!==undefined)X.tva=tva1;if(o.lock)X.lock=o.lock;
    const d=JSON.parse(JSON.stringify(X));d.t=Date.now();d.soc=a.soc;d.meta={soc:a.soc,qui:me,le:now,source:"B3.1 "+(o.label||o.type)+" · événement e"+n,statut:Object.keys(d.p||{}).length?"À VALIDER":"INCONNU",baseCout:o.base||"INCONNUE",evenement:did};delete d._src;delete d._base;
    /* b31-6b : un sous-détail modifié mais non enregistré n'est jamais écrit en passant par une autre action */
    const SB=B31.sdBase[id];if(SB&&o.type!=="cout"&&o.type!=="sous_detail"){d.sd=JSON.parse(JSON.stringify(SB.sd));if(SB.k)d.k=JSON.parse(JSON.stringify(SB.k));else delete d.k;}
    try{await S.db.doc("bpx/"+id).set(d);X.t=d.t;X.soc=a.soc;X.meta=d.meta;}
    catch(e){Object.assign(X,sv);const c=String(e&&(e.code||e.message)||"erreur"),ech={ao_id:id,soc:a.soc,seq:n+1,type:"echec_ecriture",ref:did,label:"Écriture du bordereau refusée ("+c+") : événement e"+n+" NON appliqué",le:new Date().toISOString(),par:me};
      ech.hash=sha256Str(canonJSON(ech));try{await S.db.doc("chiffrage_evenements/"+id+"~e"+(n+1)).set(ech);}catch(e2){}await b31ChargerEv(id);
      throw new Error("prix non enregistrés ("+c+") : rien n'est appliqué ; l'événement e"+n+" est affiché comme non appliqué");}
    B31.ev[id]=[Object.assign({doc_id:did},ev)].concat(L);logJ(a.ref+" : B3.1 "+(o.label||o.type)+" ("+socCourt(a.soc)+", événement e"+n+")");return ev;}
  finally{delete B31.ecr[id];}}
/* événement sans changement de prix (comparaison de scénarios figée) */
async function b31EvSeul(id,a,type,label,contexte){if(!S.db||!editable())throw new Error(RO_MSG);const{L,n,did,ref}=await b31EvNouveau(id,a),X=bpX(id),T=b31Tot(id,X.p||{});
  const ev={ao_id:id,soc:a.soc,seq:n,type,label:String(label).slice(0,240),le:new Date().toISOString(),par:S.role.me||null,lignes:[],totaux_avant:b31TotJ(T),totaux_apres:b31TotJ(T),avant_sig:b31Sig(X.p),apres_sig:b31Sig(X.p),precedent:L[0]?L[0].doc_id:null,contexte};
  ev.hash=sha256Str(canonJSON(ev));await ref.set(JSON.parse(JSON.stringify(ev)));B31.ev[id]=[Object.assign({doc_id:did},ev)].concat(L);return ev;}
/* statut d'un événement, déduit des faits enregistrés (jamais supposé) */
function b31EvStatut(e,L,X){if(e.type==="echec_ecriture"||e.type==="comparaison")return null;if(L.some(z=>z.type==="echec_ecriture"&&z.ref===e.doc_id))return{k:"ko",t:"non appliqué : écriture du bordereau refusée"};
  if(L.some(z=>z.seq>e.seq&&z.type!=="echec_ecriture"&&z.type!=="comparaison"&&z.avant_sig===e.apres_sig)||b31Sig(X.p)===e.apres_sig)return{k:"ok",t:"appliqué"};
  return{k:"todo",t:"bordereau actuel différent de l'état « après » (écriture non constatée ou modifiée hors B3.1)"};}
/* provenance d'un PU : v:6 = documentée par b31-6 ; sinon ancienne, affichée telle quelle, jamais complétée */
function b31Prov(s,has){if(!s)return has?{court:"Provenance non documentée (PU antérieur à b31-6)",doc:false,det:[]}:null;
  const m=s.m;if(s.v!==6){const t=m==="pct"?"Objectif "+(s.p!=null?b31PctTxt(s.p):"")+" (ancien : PU de base"+(s.baseLab?" « "+s.baseLab+" »":"")+" et auteur non enregistrés)":m==="ia"?"Suggestion acceptée (ancienne : "+String(s.src||"source").split(" — ")[0]+(s.le?", "+fmtDT(s.le):"")+")":m==="manuel"?"Saisie manuelle (ancienne, non documentée)":"Origine ancienne non documentée";
    return{court:t,doc:false,det:[]};}
  const f=v=>v==null||v===""?"—":fmtN(v)+" DH",det=[["Source",(B31_MSRC[s.methode||m]||s.source||m)+(s.source_lab?" — "+s.source_lab:"")],["PU avant application",f(s.pu_avant)],["PU de base (avant coefficient)",f(s.pu_base)],["PU proposé",f(s.propose)],["PU appliqué",f(s.applique)]];
  if(s.coef_pct!=null)det.push(["Coefficient",b31PctTxt(s.coef_pct)+(s.facteur!=null?" (facteur × "+String(s.facteur).replace(".",",")+")":"")]);
  if(s.justification)det.push(["Justification",s.justification]);if(s.hypotheses)det.push(["Hypothèses",s.hypotheses]);if(s.confiance)det.push(["Confiance",s.confiance]);
  det.push(["Appliqué par",(s.par||"auteur non identifié")+" le "+fmtDT(s.le)]);if(s.evt)det.push(["Événement",s.evt]);if(s.scenario)det.push(["Scénario",s.scenario]);
  const court=m==="pct"?"Objectif "+b31PctTxt(s.p)+" · base "+f(s.pu_base)+" ("+(B31_MSRC[s.methode]||s.methode)+") → "+f(s.applique):m==="ia"?"Proposition acceptée · "+f(s.applique)+" ("+(s.source_lab||"IA")+")":m==="sd"?"Report du sous-détail · "+f(s.applique):m==="rest"?"Rechargé du brouillon "+(s.version||"")+" · "+f(s.applique):"Saisie manuelle · "+f(s.applique);
  return{court:court+" · "+(s.par||"auteur non identifié")+", "+fmtDT(s.le),doc:true,det};}
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
  /* b31-6 : provenance complète par ligne + événement immuable écrit AVANT le bordereau */
  const me=S.role.me||null,lignes=rows.map(r=>({k:r.k,apres:r.apres,prov:Object.assign({v:6,m:"pct",p:pr.p,le:now,par:me,base:r.m,methode:r.m,pu_avant:r.avant,pu_base:r.base,propose:r.m!=="existant"?r.base:null,applique:r.apres,coef_pct:pr.p,facteur:Math.round(pr.f*1e6)/1e6,
      source_lab:String(r.lab||"").slice(0,200),justification:String(r.just||"").slice(0,400),confiance:r.m==="existant"?null:(r.conf||"non indiquée"),hypotheses:r.m==="existant"?null:"PU de base proposé, à vérifier ; ajusté proportionnellement à la cible",scenario:pr.scen||null},
      r.m!=="existant"?{baseLab:String(r.lab||"").slice(0,160),conf:r.conf||null,just:String(r.just||"").slice(0,300)}:{})}));
  B31.prev[id]=Object.assign(re,{scen:pr.scen||null,enCours:true});render();
  return b31Ecrire(id,a,{type:"objectif",label:"Objectif "+b31PctTxt(pr.p)+" ("+b31PartTxt(pr.p)+") appliqué à "+rows.length+" ligne(s)"+(pr.scen?" · scénario "+pr.scen:""),lignes,
      contexte:Object.assign(b31Metr(id,a,re),{scenario:pr.scen||null,lignes_verrouillees_inchangees:re.lockN,pu_de_base_proposes:re.nProp}),base:pr.nProp?"HYPOTHÈSE — proposition (IA, références internes ou Chiffreur) à vérifier":undefined})
    .then(()=>{delete B31.prev[id];render();toast("Objectif appliqué à "+rows.length+" ligne(s) et tracé dans l'historique ; lignes verrouillées inchangées. Rien n'est validé : le chiffrage reste un brouillon.");})
    .catch(e=>{if(B31.prev[id])delete B31.prev[id].enCours;render();toast("Rien n'est appliqué : "+(e&&e.message||e));});}
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
Marché : « ${String(a.obj||"").slice(0,300)} » · catégorie : ${a.categorie||"inconnue"} · lieu : ${(a.lieux||[]).join(", ")||"non précisé"}${ex.delai?" · délai : "+String(ex.delai).slice(0,160):""}${E.c!=null?" · estimation du maître d'ouvrage : "+fmtN(E.c/100)+" DH TTC ("+ET.tva.txt+")":""}${p!=null&&E.c!=null?" · objectif : "+fmtN(b31Cible(E.c,p)/100)+" DH TTC":""}.
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
  await b31ChargerEv(id);softRender();}
async function b31SaveDoc(id,a,patch,action){if(!S.db||!editable())throw new Error(RO_MSG);const ref=S.db.doc("chiffrage/"+id),g=await ref.get(),cur=g&&g.exists?g.data():{};
  if(cur.soc&&cur.soc!==a.soc)throw new Error("document de chiffrage rattaché à "+socCourt(cur.soc)+" : refus (FIN-ISO-001)");
  const le=new Date().toISOString(),par=S.role.me||null,n=Object.assign({},cur,patch,{ao_id:id,soc:a.soc,maj:le,historique:(cur.historique||[]).concat([{le,par,action}]).slice(-300)});
  await ref.set(JSON.parse(JSON.stringify(n)));B31.ch[id]={etat:"ok",doc:n};logJ(a.ref+" : B3.1 "+action+" ("+socCourt(a.soc)+")");return n;}
async function b31Version(id,a,label){if(!S.db||!editable())throw new Error(RO_MSG);const ET=b31Etat(id,a),X=ET.X,L=B31.vers[id]||[],v=L.reduce((m,x)=>Math.max(m,x.version||0),0)+1,did=id+"~v"+v,ref=S.db.doc("chiffrage_versions/"+did);
  const ex=await ref.get();if(ex&&ex.exists)throw new Error("la version "+v+" existe déjà : un brouillon enregistré n'est jamais réécrit");
  const d={ao_id:id,soc:a.soc,version:v,label:String(label||"Brouillon").slice(0,120),created_at:new Date().toISOString(),created_by:S.role.me||null,mode:B31.mode[id]||"manuel",
    pu:JSON.parse(JSON.stringify(X.p||{})),lock:JSON.parse(JSON.stringify(X.lock||{})),srcL:JSON.parse(JSON.stringify(X.srcL||{})),
    totaux:b31TotJ(ET.T),estimation_ttc:ET.E.c==null?null:s2c(ET.E.c),art44:{etat:ET.A44.k,regime:ET.R.k},statut:"BROUILLON",
    tva:{etat:ET.tva.etat,taux:ET.tva.taux,lignes:ET.tva.lignes,txt:ET.tva.txt,doc:JSON.parse(JSON.stringify(X.tva||null))},
    couts:{couverture:ET.C.k+"/"+ET.C.N,deb_sec_ht:ET.C.complet?s2c(ET.C.dsC):null,cout_revient_ht:ET.C.complet?s2c(ET.C.coutC):null,marge:(Mg=>Mg?{ht:(Mg.mC<0?"-":"")+s2c(Math.abs(Mg.mC)),pct_vente:Math.round(Mg.pct*100)/100}:null)(b31Marge(ET.C,ET.T)),frais:JSON.parse(JSON.stringify(sdK(id))),frais_defaut:!X.k},
    scenarios:b31Comparer(id,a).filter(z=>!z.vide).map(z=>Object.assign({scenario:z.l},z.m||{pct:z.pct,erreur:z.pr.why})),dernier_evenement:(b31EvSoc(id,a)[0]||{}).doc_id||null};
  d.hash=sha256Str(canonJSON(d));await ref.set(d);B31.vers[id]=[Object.assign({doc_id:did},d)].concat(L);logJ(a.ref+" : B3.1 brouillon v"+v+" enregistré ("+socCourt(a.soc)+", TTC "+(d.totaux?d.totaux.ttc:"incomplet")+")");return d;}
async function b31Restaurer(id,a,v){if(!editable())return toast(RO_MSG);if(v.soc!==a.soc)return toast("Version d'une autre société : refusée (FIN-ISO-001).");
  if(!confirmTwice("b31rest"+v.doc_id))return toast("Touchez encore une fois pour recharger les PU de la version "+v.version+" dans le brouillon (la version reste intacte).");
  /* b31-2 : les lignes verrouillées du brouillon actif gardent leur PU, leur verrou et leur source ; b31-6 : événement « rechargement » d'abord */
  const X=bpX(id),L0=Object.assign({},X.lock||{}),P0=Object.assign({},X.p||{}),K=Object.keys(L0).filter(k=>L0[k]),VP=v.pu||{},VS=v.srcL||{},now=new Date().toISOString(),me=S.role.me||null;
  const lock=JSON.parse(JSON.stringify(v.lock||{}));K.forEach(k=>{lock[k]=L0[k];});const lignes=[];
  new Set(Object.keys(P0).concat(Object.keys(VP))).forEach(k=>{if(L0[k])return;const n0=P0[k]===undefined||P0[k]===""||P0[k]==null?null:+P0[k],n1=VP[k]===undefined||VP[k]===""||VP[k]==null?null:+VP[k];if(n0===n1)return;
    lignes.push({k,apres:n1,prov:n1==null?null:{v:6,m:"rest",le:now,par:me,methode:"version",version:"v"+v.version,pu_avant:n0,pu_base:null,propose:null,applique:n1,source_lab:"Brouillon v"+v.version+" enregistré le "+fmtDT(v.created_at),
      justification:VS[k]?"Origine dans le brouillon : "+(b31Prov(VS[k],true)||{court:""}).court:null}});});
  try{await b31Ecrire(id,a,{type:"restauration",label:"Brouillon v"+v.version+" rechargé ("+lignes.length+" PU modifié(s))"+(K.length?", "+K.length+" ligne(s) verrouillée(s) conservée(s)":""),lignes,lock,contexte:{version:v.version,hash:v.hash||null}});}
  catch(e){return toast("Rien n'est rechargé : "+(e&&e.message||e));}
  B31.dlg=null;render();if(K.length)toast(K.length+" ligne(s) verrouillée(s) conservée(s) telles quelles.");}
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
  if(ET.tva.bloque)B.push(ET.tva.txt);else if(!ET.tva.ok)B.push("TVA non confirmée ("+ET.tva.txt+") : confirmez le taux avec sa source (document et page) avant validation");
  if(B31.ecr[id])B.push("écriture de prix en cours");if(Object.keys(B31.saisie[id]||{}).length)B.push("saisie(s) de PU non enregistrée(s)");if(ET.C.etr)B.push("FIN-ISO-001 : ressource(s) de sous-détail d'une autre société");
  if(ET.iso.length)B.push("FIN-ISO-001 : "+ET.iso[0]);if(ET.cf.length)B.push(OFR_CONFLIT);
  /* b31-5 : une offre hors des bornes applicables de l'art. 44 B n'est jamais validée (aucun contournement par la validation) */
  if(ET.A44.k==="bas"||ET.A44.k==="excessif")B.push(b31Hors44Txt("Offre",ET.A44)+" Validation bloquée : revoyez les prix");return B;}
function b31Valider(id,a){if(!editable())return toast(RO_MSG);const ET=b31Etat(id,a),B=b31Bloquants(id,a,ET);if(B.length)return toast("Validation impossible : "+B.join(" ; ")+".");
  if(!confirmTwice("b31val"+id))return toast("Valider le chiffrage de "+socCourt(a.soc)+" ("+b31Dh(ET.T.ttcC)+" TTC) : touchez encore une fois. Ce n'est pas la décision Go / No-Go et rien n'est déposé sur le portail.");
  const T=bpTot(id),E=ET.E,moi=E.c?Math.round((1-ET.T.ttcC/E.c)*10000)/100:null;
  a.prixValide={mode:"b31",moi,ttc:T.ttc,ht:T.ht,le:new Date().toISOString(),qui:S.role.me||null,soc:a.soc,source:"B3.1 Chiffrage ("+(B31.mode[id]||"manuel")+")",statut:STATUT_PRIX,
    baseCout:ET.C.complet?"SOUS-DÉTAIL SOCIÉTÉ (déboursé sec + frais, bénéfice exclu)":"INCONNUE",coutReel:"INCONNU",tva:{etat:ET.tva.etat,taux:ET.tva.taux,lignes:ET.tva.lignes,source:ET.tva.srcT,txt:ET.tva.txt},decision:(moi==null?"estimation inconnue":b31PctTxt(-moi)+" par rapport à l'estimation TTC")+" — résultat du BPU",art44:{etat:ET.A44.k,regime:ET.R.k,source:B31_DECRET.ref}};
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
function b31Accepter(id,a,k,pu,src,le,info){if(!editable())return toast(RO_MSG);const X=bpX(id);if((X.lock||{})[k])return toast("Ligne verrouillée : déverrouillez-la d'abord.");
  const v=b31Num(pu);if(v==null||v<0)return toast("Proposition sans prix exploitable : rien n'est appliqué.");info=info||{};
  const now=new Date().toISOString(),av=X.p[k],prov={v:6,m:"ia",src,le:now,par:S.role.me||null,accepte:now,methode:/chiffreur/i.test(String(src))?"chiffreur":"ia",propose_le:le||null,pu_avant:av===undefined||av===""||av==null?null:+av,
    pu_base:null,propose:v,applique:Math.round(v*100)/100,source_lab:String(src||"").slice(0,200),justification:String(info.inc?"Inclut : "+info.inc:"").slice(0,400)||null,hypotheses:String(info.hyp||"").slice(0,400)||null,confiance:info.conf?b31Conf(info.conf):"non indiquée"};
  return b31Ecrire(id,a,{type:"ia",label:"Proposition acceptée pour la ligne "+k+" ("+String(src||"").split(" — ")[0]+")",lignes:[{k,apres:prov.applique,prov}],contexte:{source:String(src||"").slice(0,200),propose_le:le||null}})
    .then(()=>{render();toast("Proposition acceptée et tracée dans l'historique (ligne "+k+").");}).catch(e=>{render();toast("Rien n'est appliqué : "+(e&&e.message||e));});}
/* b31-6 · saisie manuelle : la valeur tapée reste en attente (non enregistrée) ; à la validation du champ (Entrée ou sortie),
   une modification EFFECTIVE crée l'événement puis écrit le bordereau ; valeur identique = rien n'est écrit */
function b31PuNorm(v){const s0=String(v==null?"":v).trim().replace(",",".");if(s0==="")return"";if(!/^\d+(\.\d{1,2})?$/.test(s0))return null;return +s0;}
async function b31Manuel(id,a,k,val){if(!editable())return toast(RO_MSG);const X=bpX(id),sa=B31.saisie[id]||{};
  if((X.lock||{})[k]){delete sa[k];render();return toast("Ligne verrouillée : rien n'est écrit.");}
  const v=b31PuNorm(val);if(v===null){render();return toast("PU non reconnu (nombre positif, deux décimales au plus) : rien n'est écrit.");}
  const av=X.p[k],avN=av===undefined||av===""||av==null?"":+av;if(v===avN){delete sa[k];b31MajLive();return;}
  const now=new Date().toISOString(),prov=v===""?null:{v:6,m:"manuel",le:now,par:S.role.me||null,methode:"manuel",pu_avant:avN===""?null:avN,pu_base:null,propose:null,applique:v,source_lab:"Saisie manuelle dans le bureau B3.1"};
  try{await b31Ecrire(id,a,{type:"manuel",label:"Saisie manuelle ligne "+k+" : "+(avN===""?"vide":fmtN(avN))+" → "+(v===""?"vide":fmtN(v)),lignes:[{k,apres:v,prov}]});delete sa[k];delete B31.prev[id];render();}
  catch(e){delete sa[k];render();toast("Saisie non enregistrée, rien n'est écrit : "+(e&&e.message||e));}}
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
    ${b31Kpi("doc","Offre "+(ET.valide?"validée":"en cours")+" · TTC",ET.complet?b31Dh(T.ttcC):ET.prixComplet?"TTC non calculé":"Incomplète",ET.complet?esc(T.n+"/"+(T.n+T.miss)+" PU · "+(ET.statut.k==="valide"?"figée":"brouillon")+" · "+ET.tva.lab+" "+B31_TVA_ETAT[ET.tva.etat]):ET.prixComplet?esc(T.n+" PU · "+b31Dh(T.htC)+" HT · "+ET.tva.lab+" "+B31_TVA_ETAT[ET.tva.etat]+(ET.tva.calc?"":" : TTC non calculé")):esc(T.miss+" PU manquant(s) sur "+(T.n+T.miss)+" — aucun total partiel présenté comme offre"),ET.complet?"":"b31-kinc")}
    ${b31Kpi("bar","Écart à l'estimation",ecC==null?"—":b31EcartTxt(ET.A44.ecart),ecC==null?(E.c==null?"estimation inconnue":"offre incomplète"):esc((ecC>0?"+":ecC<0?"−":"")+fmtN(Math.abs(ecC)/100)+" DH · même base TTC / TTC"),ET.A44.k==="bas"||ET.A44.k==="excessif"?"b31-kko":"")}</div>`;
  const M=[["manuel","pen","Saisie manuelle","Saisir et ajuster vos prix"],["ia","spark","Proposition IA","Suggestions par ligne, à accepter"],["pct","target","Objectif en %","Viser un % de l'estimation"]];
  const sc=ET.doc&&ET.doc.actif?(B31_SCEN.find(z=>z[0]===ET.doc.actif)||[0,""])[1]:"";
  h+=`<div class="b31-modes"><div class="b31-mg" role="radiogroup" aria-label="Mode de chiffrage">${M.map(([k,ic,t,s])=>`<button type="button" role="radio" aria-checked="${mode===k}" class="b31-mode" data-b31-mode="${k}" data-act="${act(()=>{B31.mode[id]=k;render();})}">${b31Ic(ic)}<span><b>${t}${k==="ia"?` <em class="b31-pill b31-todo">À vérifier</em>`:""}</b><small>${s}</small></span></button>`).join("")}</div>
    <div class="b31-mx"><button type="button" class="b31-lnk" data-b31-scen="1" data-act="${act(()=>{B31.dlg={id,k:"scen"};render();})}">${b31Ic("doc")}${sc?"Scénario "+esc(sc):"Scénarios"} · ${esc(ET.statut.k==="valide"?"Validé":ET.statut.k==="reprendre"?"À reprendre":"Brouillon")}</button><button type="button" class="b31-lnk" data-b31-vers="1" data-act="${act(()=>{B31.dlg={id,k:"vers"};render();})}">${b31Ic("save")}Brouillons${(B31.vers[id]||[]).length?` <em class="b31-cnt">${(B31.vers[id]||[]).length}</em>`:""}</button><button type="button" class="b31-lnk" data-b31-hist="1" data-act="${act(()=>{B31.dlg={id,k:"hist"};render();})}">${b31Ic("clock")}Historique${ET.div.length?` <em class="b31-cnt">${ET.div.length}</em>`:""}</button></div></div>`;
  if(ET.div.length)h+=`<div class="b31-div" role="note" data-b31-div="${ET.div.length}">${b31Ic("warn")}<span><b>${ET.div.length} divergence(s) conservée(s) dans l'historique</b> — ${esc(ET.div[0])}${ET.div.length>1?" ; …":""}. Le chiffrage actif ci-dessous reste au premier plan ; rien n'est effacé.</span><button type="button" class="b31-lnk" data-act="${act(()=>{B31.dlg={id,k:"hist"};render();})}">Ouvrir l'historique</button></div>`;
  h+=b31Regle(id,a,ET);
  h+=`<div class="b31-grid"><section class="b31-card b31-bpu" aria-labelledby="b31-bt">${b31Table(id,a,ET,mode)}</section><aside class="b31-side" aria-label="Récapitulatif et contrôles">${mode==="pct"?b31SimCard(id,a,ET):""}${mode==="ia"?b31IaCard(id,a,ET):""}${b31TvaCard(id,a,ET)}<div id="b31-recap">${b31Recap(id,a,ET)}</div>${b31Controles(id,a,ET)}</aside></div>`;
  h+=b31Barre(id,a,ET);
  if(B31.dlg&&B31.dlg.id===id)h+=b31Dialog(id,a,ET);
  if(B31.sd&&B31.sd.id===id)h+=b31SdPanel(id,a);
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
    <button type="button" class="b31-btn b31-sm" aria-pressed="${sp}" data-act="${act(()=>{B31.sansPrix[id]=!sp;render();})}">Sans prix (${ET.T.miss})</button>${S.downloads?`<button type="button" class="b31-btn b31-sm" data-b31-exp="doc" data-act="${act(()=>b31Export(id,a,"doc"))}">${b31Ic("dl")}Bordereau Word</button><button type="button" class="b31-btn b31-sm" data-b31-exp="xls" data-act="${act(()=>b31Export(id,a,"xls"))}">Excel</button>`:""}</div></header>`;
  if(b.alertes&&b.alertes.length)h+=`<p class="b31-al">${b31Ic("warn")}${b.alertes.length} alerte(s) de lecture du bordereau : ${esc(String(b.alertes[0]).slice(0,160))}${b.alertes.length>1?" …":""}</p>`;
  let rows="",sec=null,n=0;
  const SA=B31.saisie[id]||{};
  F.slice(0,N).forEach(r=>{const x=r.x,k=r.k,p=X.p[k],has=p!==undefined&&p!==""&&p!=null,tot=has&&r.qq!=null?ligneC(r.qq,p):null,lk=!!lock[k],s=srcL[k],cu=b31CoutU(id,k,a),ouv=B31.ouv[id+"|"+k],pv=b31Prov(s,has),po=B31.provOuv[id+"|"+k],en=Object.prototype.hasOwnProperty.call(SA,k);
    const secT=(r.lot&&b.lots.length>1?r.lot.split(" - ")[0]+" · ":"")+(x.s||"");if(secT!==sec){sec=secT;if(sec)rows+=`<tr class="b31-sec"><th colspan="7" scope="colgroup">${esc(sec)}</th></tr>`;}
    const sug=ia&&ia.L[k]?{pu:ia.L[k].pu,src:ia.src,le:ia.le,inc:"fourniture "+fmtN(ia.L[k].f||0)+" + main-d'œuvre et matériel "+fmtN(ia.L[k].m||0)+" DH (déboursé hypothétique) × coefficient",hyp:ia.L[k].j||"",base:ia.base}:cl&&cl.L[k]&&cl.L[k].pu!=null?{pu:cl.L[k].pu,src:cl.L[k].src,le:cl.L[k].le||cl.le,inc:cl.L[k].inclut,hyp:cl.L[k].hyp,conf:cl.L[k].conf}:null;
    rows+=`<tr class="b31-r${has?"":" b31-nop"}${lk?" b31-lk":""}" data-b31-k="${esc(k)}"><td class="b31-n">${esc(x.n||"")}</td><td class="b31-d"><span class="b31-dt">${esc(x.d||"")}</span>${pv?`<small class="b31-sl${pv.doc?"":" b31-nd"}" data-b31-prov="${pv.doc?"doc":"ancien"}">${esc(pv.court)}${pv.doc?` <button type="button" class="b31-lnk" aria-expanded="${!!po}" data-b31-provb="${esc(k)}" data-act="${act(()=>{B31.provOuv[id+"|"+k]=!po;render();})}">Provenance</button>`:""}</small>${po&&pv.doc?`<dl class="b31-provd" data-b31-provd="${esc(k)}">${pv.det.map(([t,v])=>`<dt>${esc(t)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>`:""}`:""}${en?`<small class="b31-pend" data-b31-pend="${esc(k)}">Saisie non enregistrée : validez (Entrée) ou quittez le champ pour l'enregistrer et la tracer.</small>`:""}${sug&&ed?`<div class="b31-sug"><span>${b31Ic("spark")}<b>${sug.pu==null?"Pas d'estimation":fmtN(sug.pu)+" DH"}</b> · ${esc(sug.src)}${sug.le?" · "+esc(fmtDT(sug.le)):""}${sug.conf?" · confiance "+esc(sug.conf):""}${sug.base?" · base "+esc(sug.base):""}</span>${sug.inc?`<small>Inclut : ${esc(sug.inc)}</small>`:""}${sug.hyp?`<small>Hypothèses : ${esc(sug.hyp)}</small>`:""}${sug.pu!=null&&!lk&&+p!==+sug.pu?`<button type="button" class="b31-btn b31-xs" data-b31-acc="${esc(k)}" data-act="${act(()=>b31Accepter(id,a,k,sug.pu,sug.src,sug.le,{inc:sug.inc,hyp:sug.hyp,conf:sug.conf}))}">Accepter pour cette ligne</button>`:sug.pu!=null&&+p===+sug.pu?`<em class="b31-pill b31-ok">Acceptée</em>`:""}</div>`:""}</td>
      <td class="b31-u">${esc(x.u||"")}</td><td class="b31-q">${r.qq==null?`<span class="b31-ko-t">illisible</span>`:esc(fmtQ(r.qq))}</td>
      <td class="b31-p"><input type="number" inputmode="decimal" step="0.01" min="0" id="bpi${esc(k)}" data-bp="${esc(k)}" value="${esc(en?SA[k]:has?p:"")}" placeholder="PU HT" aria-label="Prix unitaire HT, ligne ${esc(x.n||k)}" ${ed&&!lk&&mode!=="pct"?"":"disabled"}>${prev&&prev[k]!=null?`<small class="b31-pv">→ ${fmtN(prev[k])}</small>`:""}</td>
      <td class="b31-t" id="bpt${esc(k)}">${tot!=null?fmtN(tot/100):`<span class="b31-ko-t">—</span>`}</td>
      <td class="b31-a"><div class="b31-acts">${ed?`<button type="button" class="b31-ib" aria-pressed="${lk}" aria-label="${lk?"Déverrouiller":"Verrouiller"} la ligne ${esc(x.n||k)}" title="${lk?"Ligne verrouillée : l'objectif en % ne la modifie pas":"Verrouiller la ligne"}" data-b31-lock="${esc(k)}" data-act="${act(()=>{if(B31.ecr[id])return toast("Écriture de prix en cours : réessayez dans un instant.");if(B31.sdBase[id])return toast("Sous-détail modifié non enregistré : enregistrez-le ou annulez ses modifications avant de changer un verrou.");const Y=bpX(id);Y.lock=Y.lock||{};if(Y.lock[k])delete Y.lock[k];else Y.lock[k]=true;bpSave(id);delete B31.prev[id];render();})}">${b31Ic(lk?"lock":"unlock")}</button>`:""}<button type="button" class="b31-sdb${cu?" on":""}" aria-expanded="${!!ouv}" data-b31-sd="${esc(k)}" data-act="${act(()=>{B31.ouv[id+"|"+k]=!ouv;render();})}">${b31Ic("chev")}Sous-détail</button></div></td></tr>`;
    if(ouv)rows+=`<tr class="b31-sdr"><td></td><td colspan="6">${b31SdInline(id,k,p,cu,ed)}</td></tr>`;n++;});
  h+=`<div class="b31-tw"><table class="b31-tab"><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"></colgroup><thead><tr><th>N°</th><th>Désignation</th><th>Unité</th><th>Qté</th><th>PU HT (DH)</th><th>PT HT (DH)</th><th><span class="b31-sr">Actions</span></th></tr></thead><tbody>${rows||`<tr><td colspan="7" class="b31-none">Aucune ligne ne correspond.</td></tr>`}</tbody></table></div>`;
  if(F.length>N)h+=`<button type="button" class="b31-more" data-b31-more="1" data-act="${act(()=>{B31.n[id]=N+60;render();})}">Afficher 60 lignes de plus (${F.length-N} restantes sur ${F.length})</button>`;
  const T=ET.T;h+=`<div class="b31-arr">${b31Ic("doc")}<div>${ET.complet?`<b>Arrêté à : ${esc(enLettres(T.ttcC/100))} toutes taxes comprises.</b>`:ET.prixComplet?`<b>Arrêté non disponible :</b> TVA non renseignée ou incomplète, TTC non calculé (aucun taux supposé).`:`<b>Arrêté non disponible :</b> ${T.miss} PU manquant(s). Aucun montant en lettres n'est produit pour une offre incomplète.`}<span>Écart calculé sur la même base TTC (estimation TTC / offre TTC).</span></div></div>`;
  return h;}
function b31SdInline(id,k,p,cu,ed){const open=act(()=>{B31.sd={id,k};render();}),a=S.ao[id],c=b31SdCalc(id,k,a);
  if(!c)return`<div class="b31-sdi"><p>Aucun sous-détail pour ce prix : coût inconnu (jamais compté à zéro).</p>${ed?`<button type="button" class="b31-btn b31-sm" data-b31-sdopen="${esc(k)}" data-act="${open}">Saisir le sous-détail</button>`:""}</div>`;
  if(!cu)return`<div class="b31-sdi"><p class="b31-ko-t">Sous-détail incomplet : coût inconnu (${esc((c.inc.concat(c.etr)).slice(0,2).join(" ; ")||"aucune ressource chiffrée")}).</p>${ed?`<button type="button" class="b31-btn b31-sm" data-b31-sdopen="${esc(k)}" data-act="${open}">Compléter le sous-détail</button>`:""}</div>`;
  const has=p!==undefined&&p!==""&&p!=null,mg=has?Math.round((+p-cu.cr)*100)/100:null;
  const tile=(l,v,cl)=>`<div class="b31-tile${cl?" "+cl:""}"><span>${esc(l)}</span><b>${v}</b></div>`;
  return`<div class="b31-sdi"><h4>Sous-détail du prix unitaire · ${esc(socCourt(a.soc))}</h4><div class="b31-tiles">${cu.parts.filter(z=>z[2]).map(([t,l,v])=>tile(l,fmtN(v)+" DH")).join("")}${tile("Déboursé sec",fmtN(cu.ds)+" DH")}${tile("Frais (chantier, généraux, aléas)",fmtN(cu.frais)+" DH")}${tile("Coût de revient (hors bénéfice)",fmtN(cu.cr)+" DH","b31-tc")}${tile("Prix de vente théorique",fmtN(cu.pv)+" DH")}${tile("Marge unitaire / PU appliqué",mg==null?"—":(mg<0?"−":"")+fmtN(Math.abs(mg))+" DH"+(+p>0?" · "+(mg/+p*100).toFixed(1).replace(".",",")+" %":""),mg!=null&&mg<0?"b31-tc b31-kko":"b31-tc")}</div>
    <p class="b31-src">Sous-détail propre à ${esc(socCourt(a.soc))} ; coût de revient = déboursé sec + frais de chantier, frais généraux et aléas (bénéfice exclu) ; marge en % du PU de vente HT.${cu.nh?" "+cu.nh+" ressource(s) en hypothèse.":""}${cu.kDefaut?" Taux de frais : valeurs de départ (hypothèses).":""} ${ed?`<button type="button" class="b31-lnk" data-b31-sdopen="${esc(k)}" data-act="${open}">Ouvrir le sous-détail</button>`:""}</p></div>`;}
function b31Recap(id,a,ET){const T=ET.T,C=ET.C,inc=!ET.prixComplet,M=ET.tva,SA=Object.keys(B31.saisie[id]||{}).length;
  const row=(l,v,c)=>`<div class="b31-rr${c?" "+c:""}"><span>${l}</span><b>${v}</b></div>`;
  let h=`<section class="b31-card b31-rec" aria-labelledby="b31-rt"><h3 id="b31-rt">${b31Ic("calc")}Récapitulatif</h3>`;
  h+=row("Total HT",inc?`<span class="b31-ko-t">incomplet</span>`:b31Dh(T.htC));
  const PT=Object.entries(T.parTaux||{}).sort((u,w)=>w[0]-u[0]);
  if(inc)h+=row(esc(M.lab),"—");else if(T.tvaC==null)h+=row(esc(M.lab),`<span class="b31-ko-t">non calculée</span>`);
  else if(PT.length>1)PT.forEach(([r,z])=>{h+=row("TVA "+esc(b31TxPct(r))+" <small>sur "+fmtN(z.htC/100)+" HT</small>",b31Dh(z.tvaC));});else h+=row(esc(M.lab),b31Dh(T.tvaC));
  h+=row("Total TTC",inc?`<span class="b31-ko-t">incomplet (${T.miss} PU)</span>`:T.ttcC==null?`<span class="b31-ko-t">non calculé (TVA)</span>`:b31Dh(T.ttcC),"b31-ttc");
  if(inc)h+=`<p class="b31-src">Somme des seules lignes chiffrées : ${b31Dh(T.htC)} HT — ce n'est pas une offre.</p>`;
  if(SA)h+=`<p class="b31-pend" data-b31-pendn="${SA}">${SA} saisie(s) en attente, non enregistrée(s) : les totaux ci-dessus portent sur les prix enregistrés.</p>`;
  const cov=C.k+"/"+C.N+" ligne(s) avec coût connu",Mg=b31Marge(C,T);
  if(Mg){h+=row("Déboursé sec HT",b31Dh(C.dsC))+row("Coût de revient HT <small>(hors bénéfice)</small>",b31Dh(C.coutC))+row("Vente HT",b31Dh(T.htC))+row("Marge HT",(Mg.mC<0?"−":"")+b31Dh(Math.abs(Mg.mC)),Mg.perte?"b31-kko":"")+row("Taux de marge <small>(base : vente HT)</small>",Mg.pct.toFixed(1).replace(".",",")+" %",Mg.perte?"b31-kko":"");
    h+=`<p class="b31-src" data-b31-marge="1">Marge = vente HT − coût de revient HT ; taux = marge ÷ vente HT. Coût = sous-détails de ${esc(socCourt(a.soc))} (${cov})${C.kDefaut?" ; taux de frais : valeurs de départ (hypothèses)":""}${C.hyp?" ; "+C.hyp+" ligne(s) avec ressources en hypothèse":""}.</p>`;
    if(Mg.perte||C.perte.length)h+=`<p class="b31-ko-t" data-b31-perte="1">${Mg.perte?"Offre à perte : la vente HT est inférieure au coût de revient. ":""}${C.perte.length?C.perte.length+" ligne(s) vendue(s) sous leur coût de revient (N° "+esc(C.perte.slice(0,8).join(", "))+(C.perte.length>8?" …":"")+").":""}</p>`;}
  else h+=row("Coût de revient HT",`<span class="b31-ko-t">incomplet</span>`)+`<p class="b31-src" data-b31-marge="0">${b31Ic("warn")}Coûts incomplets (${cov}) : coût inconnu pour ${C.N-C.k} ligne(s), marge globale non calculée.${C.k&&C.prixC?" Sur les seules lignes couvertes : vente "+b31Dh(C.prixC)+" HT, coût de revient "+b31Dh(C.coutC)+" HT.":""}</p>`;
  h+=`<p class="b31-src">${b31Ic("warn")}${esc(M.txt)}.</p>`;
  return h+`</section>`;}
function b31Controles(id,a,ET){const L=[],T=ET.T,it=(niv,t,fn)=>L.push({niv,t,fn});
  if(T.miss)it("ko",T.miss+" PU manquant(s) : offre incomplète",()=>{B31.sansPrix[id]=true;B31.mode[id]="manuel";render();});
  if(T.zero)it("ko",T.zero+" PU à zéro : à justifier ou corriger",null);
  it(ET.A44.k==="bornes"?"ok":ET.A44.k==="bas"||ET.A44.k==="excessif"?"ko":"warn",ET.A44.t+(ET.A44.minC!=null?" — bornes : "+b31Dh(ET.A44.minC)+" à "+b31Dh(ET.A44.maxC)+" TTC":""),()=>{B31.ouv[id+"|regle"]=true;render();});
  if(ET.E.c==null)it("ko","Estimation du maître d'ouvrage inconnue : écart non calculable",null);
  if(!ET.tva.ok)it(ET.tva.bloque||ET.tva.etat==="absent"?"ko":"warn",ET.tva.txt+(ET.tva.bloque?"":" — confirmation requise avant validation"),()=>{B31.ouv[id+"|tva"]=true;render();});
  if(ET.C.k<ET.C.N)it("warn","Coûts incomplets : "+ET.C.k+"/"+ET.C.N+" ligne(s) avec coût connu ; marge non calculée",null);
  else{const Mg=b31Marge(ET.C,ET.T);if(Mg&&Mg.perte)it("ko","Offre à perte : marge "+b31Dh(Mg.mC)+" HT",null);}
  if(ET.C.perte.length)it("warn",ET.C.perte.length+" ligne(s) vendue(s) sous leur coût de revient",null);
  if(ET.C.etr)it("ko","FIN-ISO-001 : "+ET.C.etr+" ressource(s) de sous-détail rattachée(s) à une autre société, exclue(s) du coût",null);
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
  h+=`<div class="b31-row">${ed?`<button type="button" class="b31-btn" data-b31-prev="1" ${p==null?"disabled":""} data-act="${act(()=>{B31.prev[id]=b31Previsu(id,a,p);render();})}">Prévisualiser</button>`:""}${ed&&p!=null?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{B31.dlg={id,k:"scen",pct:p};render();})}">Enregistrer comme scénario…</button>`:""}<button type="button" class="b31-btn b31-sm" data-b31-cmpo="1" data-act="${act(()=>{B31.dlg={id,k:"cmp"};render();})}">${b31Ic("bar")}Comparer les scénarios</button></div>`;
  if(pr&&!pr.ok)h+=`<div class="b31-need" data-b31-need="${esc(pr.k||"1")}">${b31Ic("warn")}<span>${esc(pr.why)}${pr.manque&&pr.manque.length?`<small class="b31-src">Ligne(s) N° ${esc(pr.manque.slice(0,15).join(", "))}${pr.manque.length>15?" … (+"+(pr.manque.length-15)+")":""}</small>`:""}</span></div>`;
  if(pr&&pr.ok){const stale=pr.soc!==a.soc||pr.sig!==b31PrevSig(id,a,pr.p),prop=pr.rows.filter(r=>r.m!=="existant");
    h+=`<div class="b31-prv" data-b31-prv="1"${stale?' data-b31-stale="1"':""}><p><b>Aperçu ${esc(b31PctTxt(pr.p))}${pr.scen?" · scénario « "+esc(pr.scen)+" »":""}</b> : ${pr.rows.length} ligne(s) ajustée(s) × ${String(Math.round(pr.f*10000)/10000).replace(".",",")}, ${pr.lockN} verrouillée(s) inchangée(s).</p>
      <p data-b31-cible="1">TTC cible ${b31Dh(pr.cibleC)} · TTC obtenu ${b31Dh(pr.T.ttcC)} · écart d'arrondi ${pr.resteC>0?"+":""}${fmtN(pr.resteC/100)} DH, laissé tel quel (aucune ligne forcée).</p><p class="b31-src">${esc(pr.tva.txt)}.${pr.lockN?" Lignes verrouillées : "+b31Dh(pr.lockC)+" HT conservés.":""}</p><p>${b31Pill(pr.A44.k,pr.A44.t)}</p>${pr.g44&&pr.g44.verifier?`<p class="b31-src" data-b31-verif44="1">${esc(pr.g44.verifier)}</p>`:""}`;
    if(prop.length)h+=`<div class="b31-hyp" data-b31-hyp="1"><b>Proposition IA / hypothèses à vérifier</b> : ${prop.length} PU de base proposé(s) (${[pr.nRef?pr.nRef+" référence(s) interne(s)":"",pr.nCh?pr.nCh+" Chiffreur":"",pr.nIA?pr.nIA+" IA":""].filter(Boolean).join(", ")}), puis ajustés à la cible. Aucune mercuriale ni base de prix de marché n'est branchée ; aucun prix d'une autre société n'est utilisé.</div>
      <details class="b31-just" data-b31-just="1"><summary>Justification de chaque PU proposé (${prop.length})</summary><ul class="b31-ul">${prop.map(r=>`<li data-b31-jk="${esc(r.k)}"><b>N° ${esc(r.n||r.k)}</b> ${esc(String(r.d).slice(0,90))}${String(r.d).length>90?"…":""} (${esc(r.u)}, qté ${esc(fmtQ(r.qq))}) : base ${fmtN(r.base)} → <b>${fmtN(r.apres)} DH</b> · ${esc(r.lab)} · confiance ${esc(r.conf||"non indiquée")}<small class="b31-src">${esc(r.just||"")}</small></li>`).join("")}</ul></details>`;
    h+=stale?`<p class="b31-need" data-b31-perime="1">${b31Ic("warn")}<span>Aperçu périmé : les données, la société, les verrous ou la proposition ont changé depuis. Refaites l'aperçu avant d'appliquer.</span></p><div class="b31-row"><button type="button" class="b31-btn" data-act="${act(()=>{B31.prev[id]=b31Previsu(id,a,pr.p);render();})}">Refaire l'aperçu</button></div></div>`
      :pr.g44&&pr.g44.bloque?`<div class="b31-need b31-blk" data-b31-bloque44="1" role="alert">${b31Ic("warn")}<span><b>Application bloquée — hors des bornes de l'art. 44 B (décret n° 2-22-431)</b>${pr.g44.raisons.map(t=>`<small class="b31-src">${esc(t)}</small>`).join("")}<small class="b31-src">Aperçu conservé pour simulation seulement : rien n'est écrit. Changez le pourcentage ou les prix pour revenir dans les bornes (bornes incluses).</small></span></div><div class="b31-row"><button type="button" class="b31-btn b31-gold" data-b31-appl="bloque" disabled aria-disabled="true" title="${esc(pr.g44.raisons.join(" "))}">Appliquer (bloqué : art. 44 B)</button><button type="button" class="b31-btn b31-sm" data-act="${act(()=>{delete B31.prev[id];render();})}">Annuler l'aperçu</button></div></div>`
      :pr.enCours?`<div class="b31-row"><button type="button" class="b31-btn b31-gold" data-b31-appl="encours" disabled aria-disabled="true">Application en cours : historique puis bordereau…</button></div></div>`
      :`<div class="b31-row"><button type="button" class="b31-btn b31-gold" data-b31-appl="1" data-act="${wact(()=>b31Appliquer(id,a))}">Appliquer aux lignes non verrouillées</button><button type="button" class="b31-btn b31-sm" data-act="${act(()=>{delete B31.prev[id];render();})}">Annuler l'aperçu</button></div><p class="b31-src">Rien n'est validé en appliquant : le chiffrage reste un brouillon (ni validation, ni Go / No-Go, ni signature, ni dépôt). L'application est tracée dans l'historique (avant / après, provenance) avant l'écriture des prix.</p></div>`;
    if(!stale&&!pr.enCours){const Mt=b31Metr(id,a,pr);h=h.replace(/<\/div>$/,"")+`<p class="b31-src" data-b31-prvm="1">Coût connu ${esc(Mt.cout_couverture)} ligne(s) · ${Mt.marge_ht==null?"marge non calculée (coûts incomplets)":"marge "+(+Mt.marge_ht<0?"−":"")+fmtN(Math.abs(+Mt.marge_ht))+" DH HT ("+String(Mt.marge_pct_vente).replace(".",",")+" % de la vente HT)"} · HT ${fmtN(+Mt.ht)} · TVA ${fmtN(+Mt.tva)}.</p></div>`;}}
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
    <button type="button" class="b31-btn" data-b31-pdf="1" data-act="${act(()=>b31Pdf(id))}" ${B31.pdfBusy?"disabled":""}>${b31Ic("doc")}${B31.pdfBusy?"PDF en préparation…":"Aperçu PDF du bordereau"}</button>
    ${ed?`<button type="button" class="b31-btn" data-b31-rep="1" data-act="${act(()=>b31Reprendre(id,a))}">${b31Ic("undo")}À reprendre</button><button type="button" class="b31-btn b31-gold" data-b31-val="1" ${B.length?`aria-disabled="true" title="${esc(B.join(" ; "))}"`:""} data-act="${act(()=>b31Valider(id,a))}">${b31Ic("send")}Valider le chiffrage</button>`:""}</div>
    <p class="b31-bn">Valider le chiffrage fige l'offre de ${esc(socCourt(a.soc))} ; ce n'est ni la décision Go / No-Go d'Ahmed, ni une soumission sur le portail (aucun dépôt automatique).</p></div>`;}
function b31Dialog(id,a,ET){const D=B31.dlg,ferme=act(()=>{B31.dlg=null;render();});let t="",c="";
  if(D.k==="hist"){t="Historique du chiffrage · "+socCourt(a.soc);const V=B31.vers[id]||[];
    c+=b31EvHtml(id,a);
    c+=`<h4>Divergences conservées (${ET.div.length})</h4>${ET.div.length?`<ul class="b31-ul">${ET.div.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:`<p>Aucune divergence relevée.</p>`}`;
    c+=`<h4>Brouillons B3.1 enregistrés (${V.length}, immuables)</h4>${V.length?`<ul class="b31-ul">${V.map(v=>`<li><b>v${v.version}</b> · ${esc(v.label||"")} · ${esc(fmtDT(v.created_at))} · TTC ${esc(v.totaux&&v.totaux.ttc!=null?fmtN(+v.totaux.ttc):"incomplet")} · art. 44 ${esc((v.art44||{}).etat||"?")} · empreinte ${esc(String(v.hash||"").slice(0,10))}…</li>`).join("")}</ul><p class="b31-src">Pour recharger un brouillon dans le chiffrage actif : bouton « Brouillons » du bureau (lignes verrouillées conservées).</p>`:`<p>Aucun brouillon enregistré.</p>`}`;
    const hs=(ET.doc&&ET.doc.historique)||[];if(hs.length)c+=`<h4>Actions tracées (${hs.length})</h4><ul class="b31-ul">${hs.slice().reverse().slice(0,30).map(x=>`<li>${esc(fmtDT(x.le))} · ${esc(x.action)}</li>`).join("")}</ul>`;
    c+=`<p class="b31-src" data-b31-consult="1">Historique en lecture seule : textes sources, aperçus et téléchargements restent disponibles ; les anciennes actions d'écriture (appliquer au bordereau, retenir une version, simuler, lire des devis…) sont désactivées ici. Les prix se modifient dans le bureau B3.1, ligne par ligne et en respectant les verrous.</p>`;
    let anc="";try{anc=b31Consult(vOffres(id,a)+vPrixTrace(id,a));}catch(e){anc=`<p>Indisponible : ${esc(e.message||e)}</p>`;}
    c+=`<h4>Offres figées et décisions de prix antérieures (preuves inchangées)</h4>${anc||"<p>Aucune.</p>"}`;
    let prop="";try{prop=b31Consult(vPropChiffreur(id,a));}catch(e){}if(prop)c+=`<h4>Ancienne proposition du Chiffreur</h4>${prop}`;
    let sim="";try{sim=b31Consult(vSimu(id,a)+vSourcing(id,a));}catch(e){}c+=`<details class="b31-old"><summary>Outils précédents (simulateur, devis fournisseurs) — consultation</summary>${sim}</details>`;}
  else if(D.k==="vers"){t="Brouillons enregistrés · "+socCourt(a.soc);const V=(B31.vers[id]||[]).filter(v=>v.soc===a.soc);
    c+=`<p>Brouillons de ${esc(socCourt(a.soc))}, immuables. Recharger copie leurs PU dans le chiffrage actif ; les lignes verrouillées du chiffrage actif sont conservées telles quelles ; la version reste intacte. Double confirmation.</p>`;
    c+=V.length?`<ul class="b31-ul">${V.map(v=>`<li data-b31-v="${v.version}"><b>v${v.version}</b> · ${esc(v.label||"")} · ${esc(fmtDT(v.created_at))} · TTC ${esc(v.totaux&&v.totaux.ttc!=null?fmtN(+v.totaux.ttc):"incomplet")} · art. 44 ${esc((v.art44||{}).etat||"?")}${editable()?` <button type="button" class="b31-lnk" data-b31-rest="${v.version}" data-act="${act(()=>b31Restaurer(id,a,v))}">Recharger dans le brouillon</button>`:""}</li>`).join("")}</ul>`:`<p>Aucun brouillon enregistré. Utilisez « Enregistrer le brouillon ».</p>`;}
  else if(D.k==="cmp"){t="Comparaison des scénarios · "+socCourt(a.soc);c+=b31CmpHtml(id,a,ET);}
  else if(D.k==="scen"){t="Scénarios · "+socCourt(a.soc);const SC=(ET.doc&&ET.doc.scenarios)||{};
    c+=`<p>Trois scénarios propres à ${esc(socCourt(a.soc))}, chacun défini par un pourcentage que vous saisissez par rapport à l'estimation TTC. Ils ne sont jamais recopiés vers une autre société.</p>`;
    c+=B31_SCEN.map(([k,l])=>{const s=SC[k]||{},v=D.pct!=null&&D.cible===k?D.pct:s.pct,c2=v!=null&&ET.E.c!=null?b31Cible(ET.E.c,v):null,A=c2!=null?b31Art44(ET.R,c2,ET.E.c):null;
      return`<div class="b31-sc" data-b31-sc="${k}"><b>${l}</b><input class="b31-in" data-b31-scin="${k}" value="${esc(v==null?"":String(v).replace(".",","))}" placeholder="% saisi par vous" aria-label="Pourcentage du scénario ${l}"><span>${v==null?"non défini":esc(b31PctTxt(v)+" = "+b31PartTxt(v))+(c2!=null?" · cible "+b31Dh(c2)+" TTC":"")}</span>${A?b31Pill(A.k,A.k==="bornes"?"art. 44 : bornes":A.k==="verifier"?"art. 44 : à vérifier":"art. 44 : hors bornes"):""}${s.le?`<small>Enregistré le ${esc(fmtDT(s.le))}</small>`:""}
        ${editable()?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{const inp=document.querySelector(`[data-b31-scin="${k}"]`),pv=b31ParsePct(inp&&inp.value);if(pv==null)return toast("Pourcentage non reconnu.");const n={...SC,[k]:{pct:pv,le:new Date().toISOString(),par:S.role.me||null}};b31SaveDoc(id,a,{scenarios:n,actif:k},"scénario "+l+" = "+b31PctTxt(pv)).then(()=>{B31.dlg={id,k:"scen"};render();toast("Scénario "+l+" enregistré pour "+socCourt(a.soc)+".");}).catch(e=>toast("Impossible : "+(e&&e.message||e)));})}">Enregistrer</button>`:""}${v!=null?`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{B31.pct[id]=String(v).replace(".",",");B31.mode[id]="pct";B31.prev[id]=b31Previsu(id,a,v);B31.dlg=null;render();})}">Prévisualiser</button>`:""}</div>`;}).join("");
    c+=`<div class="b31-row"><button type="button" class="b31-btn b31-sm" data-b31-cmpo="2" data-act="${act(()=>{B31.dlg={id,k:"cmp"};render();})}">${b31Ic("bar")}Comparer côte à côte</button></div>`;
    if(D.pct!=null&&!D.cible)c+=`<p class="b31-src">Pourcentage courant ${esc(b31PctTxt(D.pct))} : choisissez le scénario où l'enregistrer.</p>${B31_SCEN.map(([k,l])=>`<button type="button" class="b31-btn b31-sm" data-act="${act(()=>{B31.dlg={id,k:"scen",pct:D.pct,cible:k};render();})}">Placer dans « ${l} »</button>`).join(" ")}`;}
  return`<div class="fsheet b31-dlg" role="dialog" aria-modal="true" aria-label="${esc(t)}"><div class="fsback" data-act="${ferme}"></div><div class="fspanel b31-dp"><div class="fshead"><div><div class="fshtitle">${esc(t)}</div><div class="fshsub">${esc(a.ref||id)} · lecture des preuves conservées, rien n'est effacé</div></div><button type="button" class="fsx" aria-label="Fermer" data-act="${ferme}">${b31Ic("x")}</button></div><div class="fsbody b31" id="fsbody">${c}</div></div></div>`;}
/* ---------- b31-6c · PDF du bordereau fidèle au DCE (pdfmake, document texte vectoriel) ----------
   Structure dérivée du bordereau extrait du DCE DE CE DOSSIER (S.bp : lots, sections dans l'ordre, N°, désignations, unités, quantités) :
   pour chaque section « TOTAL <intitulé sans numéro> », puis Total HT, TVA au taux documenté (une ligne par taux), Total TTC,
   récapitulatif des sections et arrêté en lettres. Seuls les PU / PT de la société du dossier sont remplis ; un prix manquant reste vide
   et aucun total ni arrêté n'est produit. Les contrôles EAIOS sont rejetés dans une annexe interne séparée, après le bordereau.
   Aucun modèle d'arrêté dans le DCE lu → formule française standard. Document de travail interne : aucune signature ni cachet. */
const B31_COLS=["N° Prix","Désignation des Ouvrages","Unité","Quantité","Prix Unitaire (DH)","Prix Total (DH)"];
const b31SecNum=s=>{const m=String(s||"").match(/^\s*(\d+)\s*(?:[.\-–)]|\s)/);return m?+m[1]:null;};
const b31SecNom=s=>String(s||"").replace(/^\s*\d+(?:\.\d+)*\s*[.\-–)]?\s*/,"").replace(/\s+/g," ").trim();
function b31BpModele(id,a){const b=S.bp[id],X=bpX(id),M=b31TvaM(id,a);if(!b)return null;
  const lots=b.lots.map((L,l)=>{const secs=[];let cur=null,ht=0,miss=0;const G={};
    L.lignes.forEach((x,i)=>{const k=l+"-"+i,s=String(x.s||"").replace(/\s+/g," ").trim();if(!cur||cur.titre!==s){cur={titre:s,lignes:[],htC:0,miss:0};secs.push(cur);}
      const p=X.p[k],has=p!==undefined&&p!==""&&p!=null,q=bpQ(id,l,i,x),mc=has&&q!=null?ligneC(q,p):null;
      cur.lignes.push({k,n:String(x.n||""),d:String(x.d||""),u:String(x.u||""),q,pu:has?+p:null,pt:mc,r:M.rate(k)});
      if(mc==null){cur.miss++;miss++;}else{cur.htC+=mc;ht+=mc;const r=M.rate(k);if(r!=null)G[r]=(G[r]||0)+mc;}});
    secs.forEach(s=>{s.total=s.titre?"TOTAL "+b31SecNom(s.titre):null;});
    const nums=secs.map(s=>b31SecNum(s.titre)),seq=secs.length>1&&nums.every((v,j)=>v===j+1),N=secs.length;
    const libHT=seq?"TOTAL ("+(N<=3?nums.join("+"):"1+2+…+"+N)+") HT":"TOTAL HT";
    const tv=Object.entries(G).sort((u,w)=>w[0]-u[0]).map(([r,h])=>({r:+r,htC:h,tvaC:Math.floor((h*+r+50)/100)}));
    const ok=!miss&&M.calc,tvaC=ok?tv.reduce((t,z)=>t+z.tvaC,0):null;
    return{lot:String(L.lot||""),secs,libHT,htC:miss?null:ht,miss,tv,tvaC,ttcC:ok?ht+tvaC:null,mixte:tv.length>1};});
  return{titre:b.titre||"BORDEREAU DES PRIX",cols:b.colonnes&&b.colonnes.length===6?b.colonnes:B31_COLS,lots,M,source:b.source||null,cadre:!!b.cadre};}
const b31ArreteTxt=c=>"Arrêté le présent bordereau à la somme de : "+enLettres(c/100)+" toutes taxes comprises.";
function b31PdfDoc(id,a){const ET=b31Etat(id,a),Mo=b31BpModele(id,a),K=B21_PDF.K,now=new Date(),gen=fmt(now)+" à "+pad(now.getHours())+"h"+pad(now.getMinutes()),T=ET.T;
  const brou=!ET.valide,soc=socCourt(a.soc),c2=c=>c==null?"":fmtN(c/100),R={alignment:"right"},th={fillColor:K.th,bold:true,fontSize:8.5,alignment:"center"};
  const lab=(t,o)=>Object.assign({text:t,colSpan:5,alignment:"right",bold:true},o||{}),em=()=>({}),tvaLab=(z,lot)=>"TVA ("+String(z.r).replace(".",",")+"%)"+(lot.mixte?" sur "+c2(z.htC)+" HT":"");
  const content=[{text:(a.procedure||"Appel d'offres ouvert")+" n° "+(a.ref||id),bold:true,fontSize:11},{text:String(a.mo||""),color:K.ink2,margin:[0,1,0,0]},
    {text:[{text:"Objet : ",bold:true},String(a.obj||"")],margin:[0,3,0,0]},{text:[{text:"Concurrent : ",bold:true},soc],margin:[0,2,0,6]}];
  if(brou)content.push({table:{widths:["*"],body:[[{text:"DOCUMENT DE TRAVAIL INTERNE — chiffrage non validé (brouillon). Ne pas déposer : la pièce de l'offre est établie, signée et cachetée par la gérance ; aucune signature ni cachet n'est apposé ici.",color:K.red,bold:true,fontSize:8.5,margin:[4,3,4,3]}]]},layout:{hLineColor:()=>K.red,vLineColor:()=>K.red},margin:[0,0,0,6]});
  const inc=Mo.lots.reduce((t,L)=>t+L.miss,0);
  if(inc||!ET.tva.calc)content.push({text:(inc?inc+" prix unitaire(s) manquant(s) : cellules laissées vides, totaux et arrêté non produits. ":"")+(!ET.tva.calc?"TVA non renseignée pour ce dossier : TVA et TTC non calculés (aucun taux supposé).":""),color:K.red,fontSize:8.5,margin:[0,0,0,6]});
  Mo.lots.forEach((L,li)=>{if(li)content.push({text:"",pageBreak:"before"});
    if(L.lot)content.push({text:L.lot,bold:true,fontSize:11,margin:[0,2,0,4]});
    content.push({text:Mo.titre,style:"titre"});
    L.secs.forEach((s,si)=>{const body=[Mo.cols.map(c=>Object.assign({text:c},th))];/* cellules neuves par tableau : pdfmake les modifie */if(s.titre)body.push([{text:s.titre,colSpan:6,bold:true,fillColor:K.voile,fontSize:9},em(),em(),em(),em(),em()]);
      s.lignes.forEach(r=>body.push([{text:r.n,fontSize:8.5},{text:r.d,fontSize:8.5},{text:r.u,alignment:"center",fontSize:8.5},Object.assign({text:r.q==null?"illisible":fmtQ(r.q),fontSize:8.5},R),Object.assign({text:r.pu==null?"":fmtN(r.pu),fontSize:8.5},R),Object.assign({text:c2(r.pt),fontSize:8.5},R)]));
      if(s.total)body.push([lab(s.total),em(),em(),em(),em(),Object.assign({text:s.miss?"":c2(s.htC),bold:true},R)]);
      const last=si===L.secs.length-1;
      if(last){body.push([lab(L.libHT),em(),em(),em(),em(),Object.assign({text:c2(L.htC),bold:true},R)]);
        if(Mo.M.calc)L.tv.forEach(z=>body.push([lab(tvaLab(z,L)),em(),em(),em(),em(),Object.assign({text:L.miss?"":c2(z.tvaC),bold:true},R)]));
        else body.push([lab("TVA (taux non renseigné)"),em(),em(),em(),em(),Object.assign({text:"non calculée",italics:true,color:K.red},R)]);
        body.push([lab("TOTAL TTC"),em(),em(),em(),em(),Object.assign({text:L.ttcC==null?"":c2(L.ttcC),bold:true},R)]);}
      content.push({table:{headerRows:s.titre?2:1,keepWithHeaderRows:1,dontBreakRows:true,widths:[34,"*",36,50,66,76],body},layout:{hLineColor:()=>K.line,vLineColor:()=>K.line,paddingTop:()=>3,paddingBottom:()=>3},margin:[0,0,0,8]});});
    /* récapitulatif et arrêté, groupés (jamais isolés de leurs montants) */
    const rb=L.secs.filter(s=>s.total).map(s=>[{text:s.total},Object.assign({text:s.miss?"":c2(s.htC)},R)]);
    rb.push([{text:L.libHT,bold:true},Object.assign({text:c2(L.htC),bold:true},R)]);
    if(Mo.M.calc)L.tv.forEach(z=>rb.push([{text:tvaLab(z,L),bold:true},Object.assign({text:L.miss?"":c2(z.tvaC),bold:true},R)]));else rb.push([{text:"TVA (taux non renseigné)",bold:true},Object.assign({text:"non calculée",italics:true,color:K.red},R)]);
    rb.push([{text:"TOTAL TTC",bold:true},Object.assign({text:L.ttcC==null?"":c2(L.ttcC),bold:true},R)]);
    content.push({unbreakable:true,stack:[{table:{widths:["*",96],body:rb},fontSize:8.5,layout:{hLineColor:()=>K.line,vLineColor:()=>K.line,paddingTop:()=>1.5,paddingBottom:()=>1.5},margin:[90,0,0,6]},
      L.ttcC!=null?{text:b31ArreteTxt(L.ttcC),bold:true,margin:[0,2,0,0]}:{text:"Arrêté non produit : "+(L.miss?L.miss+" prix manquant(s)":"TVA non renseignée")+".",italics:true,color:K.red,margin:[0,2,0,0]},
      {text:Mo.M.txt+".",fontSize:7.5,color:K.muted,margin:[0,4,0,0]}]});});
  /* annexe interne : contrôles EAIOS, hors bordereau */
  const E=ET.E,Mg=b31Marge(ET.C,T),kv=(k,v)=>[{text:k,color:K.ink2},{text:v,bold:true}];
  content.push({text:"Annexe interne EAIOS — contrôles du chiffrage (ne fait pas partie du bordereau)",style:"h",pageBreak:"before"},
    {table:{widths:[190,"*"],body:[kv("Statut",ET.statut.t),kv("Estimation du maître d'ouvrage",E.c==null?"non renseignée":b31Dh(E.c)+" — telle que publiée (source : "+(E.src||"non indiquée")+") ; nature HT / TTC non convertie : EAIOS la compare au TTC de l'offre par convention, à vérifier dans l'avis"),
      kv("Offre",ET.complet?b31Dh(T.htC)+" HT · "+b31Dh(T.tvaC)+" TVA · "+b31Dh(T.ttcC)+" TTC":"incomplète ou TTC non calculé"),kv("Écart offre TTC / estimation",ET.complet&&E.c?b31EcartTxt(ET.A44.ecart):"—"),
      kv("Contrôle art. 44 (décret 2-22-431)",ET.R.lab+" — "+ET.A44.t+(ET.A44.minC!=null?" (bornes "+b31Dh(ET.A44.minC)+" à "+b31Dh(ET.A44.maxC)+")":"")),kv("TVA du dossier",ET.tva.txt),
      kv("Coût et marge",Mg?"coût de revient "+b31Dh(ET.C.coutC)+" HT · marge "+(Mg.mC<0?"−":"")+b31Dh(Math.abs(Mg.mC))+" ("+Mg.pct.toFixed(1).replace(".",",")+" % de la vente HT)":"coûts incomplets ("+ET.C.k+"/"+ET.C.N+" ligne(s)) : marge non calculée"),
      kv("Source du bordereau",(Mo.source||"bordereau extrait du DCE")+" ; structure (sections, ordre, N°, désignations, unités, quantités) reprise telle qu'extraite")]},layout:"lightHorizontalLines"},
    {text:"Source réglementaire : "+B31_DECRET.ref,fontSize:7.5,color:K.muted,margin:[0,6,0,0]});
  return{dd:{pageSize:"A4",pageOrientation:"portrait",pageMargins:[34,58,34,44],defaultStyle:{font:"Roboto",fontSize:9,color:K.ink,lineHeight:1.12},
    styles:{titre:{fontSize:12,bold:true,alignment:"center",margin:[0,4,0,8]},h:{fontSize:12,bold:true,margin:[0,0,0,8]}},
    info:{title:"Bordereau des prix "+(a.ref||id)+" — "+soc+(brou?" (document de travail)":""),author:"EAIOS",subject:"B3.1 · bordereau des prix (document de travail interne)",creator:"EAIOS "+(typeof APP_VERSION!=="undefined"?APP_VERSION:""),producer:"EAIOS "+B31.v+" (pdfmake)"},
    header:()=>({columns:[{text:(a.ref||id)+" · "+soc,color:K.muted},{text:brou?"DOCUMENT DE TRAVAIL INTERNE · BROUILLON":"Document de travail · chiffrage validé (offre figée)",alignment:"right",color:brou?K.red:K.muted,bold:brou}],fontSize:7.5,margin:[34,24,34,0]}),
    footer:(p,n)=>({columns:[{text:"EAIOS · B3.1 · généré le "+gen+" · non destiné au dépôt",color:K.muted},{text:"Page "+p+" / "+n,alignment:"right",width:70}],fontSize:7.5,margin:[34,14,34,0]}),content},gen,Mo};}
async function b31Pdf(id){const a=S.ao[id];if(!a||B31.pdfBusy)return;B31.pdfBusy=true;render();
  try{const pm=await b21PdfLib(),{dd,gen}=b31PdfDoc(id,a);
    const buf=await new Promise((res,rej)=>{try{pm.createPdf(dd).getBuffer(b=>res(b));}catch(e){rej(e);}}),bytes=new Uint8Array(buf),nom="Bordereau_"+safeN(a.ref||id)+"_"+safeN(socCourt(a.soc))+".pdf";
    B31.pdf[id]={bytes,nom,gen};await b31PdfVue(bytes,"Bordereau des prix "+(a.ref||id)+" · "+socCourt(a.soc)+" · "+gen,nom);}
  catch(e){toast("PDF indisponible : "+(e&&(e.message||e.code)||"erreur"));}finally{B31.pdfBusy=false;render();}}
/* lecteur : pages rendues à la densité de l'écran (net), couche de texte pdf.js (sélection, recherche du navigateur), zoom */
const B31_TL_CSS=`.b31v-bar{position:sticky;top:-10px;z-index:3;display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:-10px -10px 12px;padding:8px 10px;background:var(--bg,#F4F1EA);color:var(--ink,#16171A);border-bottom:1px solid var(--line,#E6DFD2);box-shadow:0 2px 6px rgba(0,0,0,.12)}.b31v-bar button{border:1px solid #c9c2b5;background:#fff;color:#16171A;border-radius:6px;padding:4px 10px;font:600 13px system-ui;cursor:pointer}.b31v-bar span{font-size:12.5px;opacity:.8}
.b31v-p{position:relative;margin:0 auto 12px;scroll-margin-top:96px;box-shadow:0 1px 4px rgba(0,0,0,.25);background:#fff}.b31v-p canvas{display:block}.b31v-p .textLayer{position:absolute;inset:0;overflow:hidden;line-height:1;text-align:initial;opacity:1;forced-color-adjust:none;transform-origin:0 0}
.b31v-p .textLayer span,.b31v-p .textLayer br{color:transparent;position:absolute;white-space:pre;cursor:text;transform-origin:0% 0%}.b31v-p .textLayer ::selection{background:rgba(0,90,255,.3)}`;
async function b31PdfVue(bytes,titre,nom){const v=$("#viewer"),bd=dceVue(titre,nom,bytes);if(!document.getElementById("b31v-css")){const st=document.createElement("style");st.id="b31v-css";st.textContent=B31_TL_CSS;document.head.appendChild(st);}
  bd.innerHTML='<p class="hint" style="padding:16px">Ouverture du PDF…</p>';const lib=await ensurePdf(),pdf=await lib.getDocument({data:bytes.slice(),isEvalSupported:false}).promise;if(v.hidden)return;
  const st={z:1,pdf};B31.pdfVue=st;
  const dessin=async()=>{const tok=st.tok={};const fit=Math.max(200,Math.min(bd.clientWidth-24,900)),dpr=Math.min(window.devicePixelRatio||1,3);
    bd.innerHTML=`<div class="b31v-bar" data-b31-pdfbar="1"><button type="button" data-z="-" aria-label="Zoom arrière">−</button><span data-b31-zoom="1">${Math.round(st.z*100)} %</span><button type="button" data-z="+" aria-label="Zoom avant">+</button><button type="button" data-z="1">Largeur</button><span>PDF texte (vectoriel) · ${pdf.numPages} page(s) A4 · texte sélectionnable ; recherche : Ctrl+F · « Télécharger » enregistre exactement ce fichier.</span></div>`;
    bd.querySelectorAll("[data-z]").forEach(btn=>btn.addEventListener("click",()=>{const z=btn.dataset.z;st.z=z==="+"?Math.min(st.z*1.25,4):z==="-"?Math.max(st.z/1.25,0.4):1;dessin();}));
    for(let i=1;i<=pdf.numPages;i++){if(v.hidden||st.tok!==tok)return;const pg=await pdf.getPage(i),s=fit*st.z/pg.getViewport({scale:1}).width,vpC=pg.getViewport({scale:s}),vp=pg.getViewport({scale:s*dpr});
      const box=document.createElement("div");box.className="b31v-p";box.dataset.b31Page=i;{const br=bd.querySelector("[data-b31-pdfbar]");if(br)box.style.scrollMarginTop=(br.offsetHeight+12)+"px";}box.style.width=Math.floor(vpC.width)+"px";box.style.height=Math.floor(vpC.height)+"px";
      const c=document.createElement("canvas");c.width=Math.floor(vp.width);c.height=Math.floor(vp.height);c.style.width=Math.floor(vpC.width)+"px";c.style.height=Math.floor(vpC.height)+"px";box.appendChild(c);
      const tl=document.createElement("div");tl.className="textLayer";tl.style.setProperty("--scale-factor",vpC.scale);box.appendChild(tl);bd.appendChild(box);
      await pg.render({canvasContext:c.getContext("2d"),viewport:vp}).promise;
      try{if(lib.renderTextLayer){const t=lib.renderTextLayer({textContentSource:pg.streamTextContent(),container:tl,viewport:vpC,textDivs:[]});if(t&&t.promise)await t.promise;}}catch(e){tl.dataset.erreur=String(e&&e.message||e);}}};
  await dessin();}
/* ---------- b31-6 · carte « TVA du dossier » ---------- */
function b31TvaEd(id,a){const M=b31TvaM(id,a),D=M.D||{};return B31.tvaEd[id]||(B31.tvaEd[id]={taux:M.taux!=null?String(M.taux).replace(".",","):"",etat:M.etat==="confirme"?"confirme":"hypothese",doc:(D.src&&D.src.doc)||"",page:(D.src&&D.src.page)||"",mixte:!!D.mixte,lignes:Object.assign({},D.lignes||{})});}
function b31TvaCard(id,a,ET){const M=ET.tva,ed=editable(),o=B31.ouv[id+"|tva"]||M.etat==="absent"||M.conflit;
  const pill=M.conflit?b31Pill("bas","Conflit DCE / saisie"):M.ok?b31Pill("bornes","Confirmée"):M.etat==="absent"?b31Pill("bas","Non renseignée"):b31Pill("verifier",M.etat==="dce"?"Relevée, à confirmer":"Hypothèse");
  let h=`<section class="b31-card b31-tva" aria-labelledby="b31-tvt" data-b31-tva="${esc(M.etat)}"><h3 id="b31-tvt">${b31Ic("scale")}TVA du dossier ${pill}</h3><p class="b31-src" data-b31-tvatxt="1">${esc(M.txt)}.</p>`;
  if(M.dce!=null&&M.etat!=="dce")h+=`<p class="b31-src">Taux relevé automatiquement dans le DCE : ${esc(b31TxPct(M.dce))}${(a.exig&&a.exig.sources&&a.exig.sources.tva)?" ("+esc(a.exig.sources.tva)+")":""}.</p>`;
  if(!M.ok)h+=`<p class="b31-need">${b31Ic("warn")}<span>${M.etat==="absent"?"Aucun taux n'est supposé : TVA et TTC restent non calculés.":"Taux non confirmé"} — la validation du chiffrage exige un taux <b>confirmé</b> avec sa source (document et page du CPS / bordereau).</span></p>`;
  if(ed){const F=b31TvaEd(id,a),L=b31Lignes(id);
    h+=`<details class="b31-tvf"${o?" open":""} data-b31-tvf="1"><summary>${M.etat==="absent"?"Saisir le taux de TVA":"Modifier le taux ou sa source"}</summary>
      <div class="b31-tvg"><label>Taux (%)<input class="b31-in" data-b31-tvaf="taux" value="${esc(F.taux)}" inputmode="decimal" placeholder="taux lu dans le DCE" autocomplete="off"></label>
      <label>État<select class="b31-in" data-b31-tvaf="etat"><option value="confirme"${F.etat==="confirme"?" selected":""}>Confirmé (lu dans le DCE)</option><option value="hypothese"${F.etat!=="confirme"?" selected":""}>Hypothèse (à confirmer)</option></select></label>
      <label>Document source<input class="b31-in" data-b31-tvaf="doc" value="${esc(F.doc)}" placeholder="ex. CPS, article des prix" autocomplete="off"></label><label>Page<input class="b31-in" data-b31-tvaf="page" value="${esc(F.page)}" placeholder="ex. 12" autocomplete="off"></label></div>
      <label class="b31-chk"><input type="checkbox" data-b31-tvaf="mixte"${F.mixte?" checked":""}> DCE à taux mixtes : taux propre à certaines lignes</label>`;
    if(F.mixte)h+=`<details class="b31-tvl"><summary>Taux par ligne (${Object.values(F.lignes).filter(v=>v!==""&&v!=null).length} ligne(s) avec taux propre ; les autres prennent le taux ci-dessus)</summary><ul class="b31-ul">${L.map(r=>`<li><label>N° ${esc(r.x.n||r.k)} ${esc(String(r.x.d||"").slice(0,60))}<input class="b31-in b31-xin" data-b31-tval="${esc(r.k)}" value="${esc(F.lignes[r.k]==null?"":String(F.lignes[r.k]).replace(".",","))}" inputmode="decimal" placeholder="${esc(F.taux||"taux")}" aria-label="Taux de TVA de la ligne ${esc(r.x.n||r.k)}"></label></li>`).join("")}</ul></details>`;
    h+=`<div class="b31-row"><button type="button" class="b31-btn b31-sm" data-b31-tvasave="1" data-act="${wact(()=>b31TvaEnregistrer(id,a))}">Enregistrer le taux (tracé dans l'historique)</button></div><p class="b31-src">Un taux « confirmé » exige le document et la page. Le changement de taux est un événement de prix (TTC avant / après).</p></details>`;}
  return h+`</section>`;}
async function b31TvaEnregistrer(id,a){const F=b31TvaEd(id,a),t=F.taux===""?null:b31TauxOk(F.taux),L=b31Lignes(id),lg={};
  if(F.taux!==""&&t==null)return toast("Taux non reconnu (0 à 100, deux décimales au plus) : rien n'est écrit.");
  if(F.mixte)for(const r of L){const v=F.lignes[r.k];if(v==null||v==="")continue;const tv=b31TauxOk(v);if(tv==null)return toast("Taux non reconnu pour la ligne "+(r.x.n||r.k)+" : rien n'est écrit.");lg[r.k]=tv;}
  if(t==null&&!(F.mixte&&Object.keys(lg).length))return toast("Saisissez un taux : rien n'est écrit.");
  const doc=String(F.doc||"").trim().slice(0,160),page=String(F.page||"").trim().slice(0,40);
  if(F.etat==="confirme"&&(!doc||!page))return toast("Un taux confirmé exige le document source ET la page : rien n'est écrit (ou choisissez « Hypothèse »).");
  const n={taux:t,etat:F.etat==="confirme"?"confirme":"hypothese",src:doc||page?{doc:doc||null,page:page||null}:null,mixte:!!F.mixte,lignes:F.mixte?lg:{},par:S.role.me||null,le:new Date().toISOString(),soc:a.soc};
  if(canonJSON(Object.assign({},n,{par:null,le:null}))===canonJSON(Object.assign({},bpX(id).tva||{},{par:null,le:null})))return toast("Taux inchangé : rien n'est écrit.");
  const M1=b31TvaM(id,a,Object.assign({},bpX(id),{tva:n}));
  try{await b31Ecrire(id,a,{type:"tva",label:"TVA : "+M1.lab+" "+B31_TVA_ETAT[M1.etat]+" (source : "+M1.srcT+")",lignes:[],tva:n,contexte:{tva:n}});delete B31.tvaEd[id];delete B31.prev[id];render();toast("Taux de TVA enregistré et tracé dans l'historique.");}
  catch(e){toast("Taux non enregistré, rien n'est écrit : "+(e&&e.message||e));}}
/* ---------- b31-6 · sous-détail du prix propre à la société ---------- */
/* bibliothèque de la SOCIÉTÉ : ses propres sous-détails (tous dossiers de la société) et les seules entrées de la bibliothèque du groupe
   rattachées explicitement à cette société ; les entrées sans société ou d'une autre société ne sont jamais proposées (FIN-ISO-001) */
function b31SdBiblio(a){const soc=a&&a.soc,M={};let horsSoc=0;if(!soc)return{L:[],horsSoc:0};
  Object.entries(S.bpx||{}).forEach(([oid,X])=>{const o=S.ao[oid];if(!X||!o||X.soc!==soc||o.soc!==soc)return;Object.entries(X.sd||{}).forEach(([k,sd])=>{if(!sd)return;B31_SDT.forEach(([t])=>(sd[t]||[]).forEach(r=>{
    if(!r||r.soc&&r.soc!==soc)return;const d=String(r.d||"").trim(),pu=b31Num(r.pu);if(!d||pu==null||!(pu>0))return;const key=t+"|"+norm(d);const z={t,d,u:r.u||"",pu,st:r.st||"",four:r.four||"",date:r.date||"",ref:o.ref||oid};
    if(!M[key]||String(z.date)>String(M[key].date))M[key]=z;}));});});
  sdBiblio().forEach(it=>{if(!it||it.soc!==soc){horsSoc++;return;}const key=it.t+"|"+norm(it.d);if(!M[key])M[key]={t:it.t,d:it.d,u:it.u||"",pu:+it.pu,st:/devis/i.test(String(it.src||""))?"devis":"interne",four:"",date:it.at||"",ref:"bibliothèque "+socCourt(soc)};});
  return{L:Object.values(M).sort((x,y)=>x.d.localeCompare(y.d)),horsSoc};}
function b31SdRowSrc(r){const st=r.st||"";return st?(B31_SRC[st]||st)+(st==="devis"?(r.four?" · "+r.four:" · fournisseur non indiqué")+(r.date?" · "+r.date:" · date non indiquée"):"")+(r.ref?" · "+r.ref:""):"source non indiquée";}
function b31SdPanel(id,a){const k=B31.sd.k,b=S.bp[id];if(!b)return"";const[l,i]=k.split("-").map(Number),x=b.lots[l].lignes[i],X=bpX(id),ed=editable(),lkP=!!(X.lock||{})[k],sd=(X.sd||{})[k]||{},c=b31SdCalc(id,k,a),K=sdK(id),Bi=b31SdBiblio(a),p=X.p[k],has=p!==undefined&&p!==""&&p!=null;
  const ferme=act(()=>{B31.sd=null;render();});let h=`<p class="b31-src">Prix n° ${esc(x.n||k)} · ${esc(x.u||"")} · ${esc(a.ref||id)} · <b>${esc(socCourt(a.soc))}</b></p><p><b>${esc(x.d||"")}</b></p>
    <p class="b31-src">Quantités pour <b>une</b> unité d'ouvrage (1 ${esc(x.u||"unité")}). Ressources propres à ${esc(socCourt(a.soc))} : la bibliothèque proposée ne contient que les références de cette société${Bi.horsSoc?` — ${Bi.horsSoc} référence(s) de la bibliothèque du groupe sans société ou d'une autre société ne sont <b>pas</b> proposées (FIN-ISO-001)`:""}. Une quantité ou un prix vide = coût inconnu.</p>`;
  B31_SDT.forEach(([t,lab,ph])=>{const rows=sd[t]||[],part=c?(c.parts.find(z=>z[0]===t)||[0,0,0])[2]:0;
    h+=`<div class="b31-sdg" data-b31-sdg="${t}"><div class="b31-sdgh"><b>${esc(lab)}</b><span>${fmtN(part)} DH</span></div>`+rows.map((r,j)=>{if(!r)return"";const etr=r.soc&&r.soc!==a.soc;return`<div class="b31-sdrw${etr?" b31-etr":""}">
      <label class="b31-sdd">Désignation<input class="b31-in" list="b31-sdl-${t}" data-b31sd="${t}|${j}|d" value="${esc(r.d||"")}" placeholder="${esc(ph)}" ${ed?"":"disabled"}></label>
      <label>Unité<input class="b31-in" data-b31sd="${t}|${j}|u" value="${esc(r.u||"")}" ${ed?"":"disabled"}></label><label>Qté / unité<input class="b31-in" inputmode="decimal" data-b31sd="${t}|${j}|q" value="${esc(r.q==null?"":r.q)}" ${ed?"":"disabled"}></label>
      <label>Prix ressource HT<input class="b31-in" inputmode="decimal" data-b31sd="${t}|${j}|pu" value="${esc(r.pu==null?"":r.pu)}" ${ed?"":"disabled"}></label>
      <label>Source<select class="b31-in" data-b31sd="${t}|${j}|st" ${ed?"":"disabled"}><option value="">non indiquée</option>${Object.entries(B31_SRC).map(([v,l2])=>`<option value="${v}"${r.st===v?" selected":""}>${esc(l2)}</option>`).join("")}</select></label>
      <label>Fournisseur<input class="b31-in" data-b31sd="${t}|${j}|four" value="${esc(r.four||"")}" placeholder="${r.st==="devis"?"obligatoire pour un devis":"—"}" ${ed?"":"disabled"}></label><label>Date du devis<input class="b31-in" type="date" data-b31sd="${t}|${j}|date" value="${esc(r.date||"")}" ${ed?"":"disabled"}></label>
      ${etr?`<small class="b31-ko-t">Ressource rattachée à ${esc(socCourt(r.soc))} : exclue du calcul (FIN-ISO-001)</small>`:""}<span class="b31-sdx"><span class="b31-sdm">${b31Num(r.q)!=null&&b31Num(r.pu)!=null?"Montant "+fmtN(b31Num(r.q)*b31Num(r.pu))+" DH":"Montant inconnu"}</span>${r.ref?`<small class="b31-src">${esc(r.ref)}</small>`:""}${ed?`<button type="button" class="b31-lnk" aria-label="Supprimer la ressource" data-act="${act(()=>{b31SdAvant(id);X.sd[k][t].splice(j,1);render();})}">${b31Ic("x")}</button>`:""}</span></div>`;}).join("")+
      (ed?`<button type="button" class="b31-btn b31-xs" data-b31-sdadd="${t}" data-act="${act(()=>{b31SdAvant(id);X.sd=X.sd||{};X.sd[k]=X.sd[k]||{mat:[],mo:[],mt:[],tr:[]};(X.sd[k][t]=X.sd[k][t]||[]).push({d:"",u:t==="mo"||t==="mt"?"h":"",q:"",pu:"",st:"",soc:a.soc});render();})}">+ Ajouter</button>`:"")+
      `<datalist id="b31-sdl-${t}">${Bi.L.filter(z=>z.t===t).map(z=>`<option value="${esc(z.d)}">${esc(fmtN(z.pu)+" DH / "+(z.u||"u")+" · "+(B31_SRC[z.st]||"source non indiquée")+(z.date?" · "+z.date:"")+" · "+z.ref)}</option>`).join("")}</datalist></div>`;});
  h+=`<div class="b31-sdg"><div class="b31-sdgh"><b>Frais et bénéfice (taux du dossier, communs à tous ses prix)</b>${c&&c.kDefaut||!X.k?`<em class="b31-pill b31-todo">valeurs de départ : hypothèses</em>`:""}</div><div class="b31-tvg">${[["fc","Frais de chantier"],["fg","Frais généraux"],["al","Aléas"],["ben","Bénéfice"]].map(([kk,l2])=>`<label>${l2} (%)<input class="b31-in" inputmode="decimal" data-b31sdk="${kk}" value="${esc(K[kk])}" ${editable()?"":"disabled"}></label>`).join("")}</div></div>`;
  const IA=B31.sdIA[id+"|"+k],pe=B31.sdErr[id+"|"+k];
  if(editable()&&S.sample)h+=`<div class="b31-row"><button type="button" class="b31-btn b31-sm" data-b31-sdia="1" ${B31.sdBusy?"disabled":""} data-act="${act(()=>b31SdProposerIA(id,a,k))}">${b31Ic("spark")}${B31.sdBusy===id+"|"+k?"Claude prépare le sous-détail…":"Proposer un sous-détail (IA, hypothèse)"}</button></div>`;
  else if(editable())h+=`<p class="b31-src" data-b31-sdiaindispo="1">Proposition IA de sous-détail indisponible dans cette vue (capacité « sample » non accordée).</p>`;
  if(pe)h+=`<p class="b31-need">${b31Ic("warn")}<span>${esc(pe)}</span></p>`;
  if(IA)h+=`<div class="b31-hyp" data-b31-sdprop="1"><b>Proposition IA du ${esc(fmtDT(IA.le))} — hypothèse à vérifier</b> (confiance ${esc(IA.conf)}) : ${IA.rows.length} ressource(s), sans devis, sans fournisseur ni date. ${esc(IA.just||"")}<ul class="b31-ul">${IA.rows.map(r=>`<li>${esc((B31_SDT.find(z=>z[0]===r.t)||[0,r.t])[1])} · ${esc(r.d)} · ${esc(fmtQ(r.q))} ${esc(r.u)} × ${r.pu==null?"prix inconnu":fmtN(r.pu)+" DH"}</li>`).join("")}</ul>${ed?`<button type="button" class="b31-btn b31-xs" data-b31-sdacc="1" data-act="${act(()=>b31SdAccepterIA(id,a,k))}">Accepter comme hypothèse (remplace les ressources de cette ligne)</button>`:""}</div>`;
  h+=`<div class="b31-sdsum" id="b31-sdsum">${b31SdSum(id,k,a)}</div>`;
  h+=`<p class="b31-pend" id="b31-sdpend" data-b31-sdpend="1"${B31.sdBase[id]?"":" hidden"}>Modifications du sous-détail non enregistrées : « Enregistrer le sous-détail » les trace dans l'historique sans changer le PU.</p>`;
  const foot=`<div class="fsfoot b31-sdfoot">${ed?`<button type="button" class="b31-btn" data-b31-sdsave="1" data-act="${wact(()=>b31SdEnregistrer(id,a,k))}">Enregistrer le sous-détail sans changer le PU</button>`+(lkP?`<span class="b31-src">Ligne verrouillée : le PU n'est jamais remplacé ; le coût peut être documenté.</span>`:`<button type="button" class="b31-btn b31-gold" data-b31-sdrep="1" ${c&&c.complet?"":"disabled"} data-act="${wact(()=>b31SdReporter(id,a,k))}">Reporter le prix de vente au bordereau</button>`):""}${ed&&B31.sdBase[id]?`<button type="button" class="b31-btn b31-sm" data-b31-sdannul="1" data-act="${act(()=>{const B=B31.sdBase[id];X.sd=JSON.parse(JSON.stringify(B.sd));if(B.k)X.k=JSON.parse(JSON.stringify(B.k));else delete X.k;delete B31.sdBase[id];render();})}">Annuler les modifications</button>`:""}<button type="button" class="b31-btn" data-act="${ferme}">Fermer</button></div>`;
  return`<div class="fsheet b31-dlg" role="dialog" aria-modal="true" aria-label="Sous-détail du prix"><div class="fsback" data-act="${ferme}"></div><div class="fspanel b31-dp b31-sdp"><div class="fshead"><div><div class="fshtitle">Sous-détail du prix · ${esc(socCourt(a.soc))}</div><div class="fshsub">Déboursé sec → coût de revient (hors bénéfice) → prix de vente</div></div><button type="button" class="fsx" aria-label="Fermer" data-act="${ferme}">${b31Ic("x")}</button></div><div class="fsbody b31" id="fsbody">${h}</div>${foot}</div></div>`;}
function b31SdSum(id,k,a){const c=b31SdCalc(id,k,a),X=bpX(id),p=X.p[k],has=p!==undefined&&p!==""&&p!=null;if(!c)return`<p>Aucune ressource : coût inconnu (jamais compté à zéro).</p>`;
  const row=(l,v,cl)=>`<div class="b31-rr${cl?" "+cl:""}"><span>${esc(l)}</span><b>${v}</b></div>`;let h="";
  if(!c.complet){h+=`<p class="b31-ko-t" data-b31-sdinc="1">Coût inconnu : ${esc((c.inc.concat(c.etr)).slice(0,4).join(" ; ")||"aucune ressource chiffrée")}${c.inc.length+c.etr.length>4?" …":""}.</p>`;return h+row("Déboursé sec (ressources connues seulement)",fmtN(c.ds)+" DH");}
  h+=row("Déboursé sec",fmtN(c.ds)+" DH")+row("Frais de chantier ("+String(c.K.fc).replace(".",",")+" %)",fmtN(c.fc)+" DH")+row("Frais généraux ("+String(c.K.fg).replace(".",",")+" %)",fmtN(c.fg)+" DH")+row("Aléas ("+String(c.K.al).replace(".",",")+" %)",fmtN(c.al)+" DH")
    +row("Coût de revient (hors bénéfice)",fmtN(c.cr)+" DH","b31-ttc")+row("Bénéfice ("+String(c.K.ben).replace(".",",")+" %)",fmtN(c.ben)+" DH")+row("Prix de vente théorique HT",fmtN(c.pv)+" DH","b31-ttc");
  if(has){const m=Math.round((+p-c.cr)*100)/100;h+=row("PU appliqué au bordereau",fmtN(p)+" DH")+row("Marge unitaire (PU − coût de revient)",(m<0?"−":"")+fmtN(Math.abs(m))+" DH · "+(+p>0?(m/+p*100).toFixed(1).replace(".",","):"—")+" % du PU de vente HT",m<0?"b31-kko":"");
    if(m<0)h+=`<p class="b31-ko-t" data-b31-perte="1">Vente à perte sur cette ligne : le PU appliqué est inférieur au coût de revient.</p>`;}
  if(c.nh)h+=`<p class="b31-src">${c.nh} ressource(s) en hypothèse (proposition IA, hypothèse ou source non indiquée)${c.sans.length?" dont "+c.sans.length+" sans source":""}.</p>`;
  if(c.kDefaut)h+=`<p class="b31-src">Taux de frais et de bénéfice : valeurs de départ (hypothèses), non validées pour ce dossier.</p>`;
  return h;}
async function b31SdProposerIA(id,a,k){if(!editable())return toast(RO_MSG);if(B31.sdBusy)return;const key=id+"|"+k;
  if(!S.sample){B31.sdErr[key]="Proposition IA indisponible : capacité « sample » non accordée. Rien n'est produit.";render();return;}
  const r=b31Lignes(id).find(z=>z.k===k);if(!r)return;B31.sdBusy=key;delete B31.sdErr[key];render();
  const Bi=b31SdBiblio(a).L.slice(0,40).map(z=>JSON.stringify({categorie:z.t,designation:z.d.slice(0,100),unite:z.u,pu_ht:z.pu,source:B31_SRC[z.st]||"non indiquée",date:z.date||null}));
  const prompt=`Tu proposes, pour une PME marocaine du BTP (société : ${socCourt(a.soc)}), un SOUS-DÉTAIL HYPOTHÉTIQUE du prix unitaire d'un ouvrage de marché public : ressources nécessaires pour UNE unité d'ouvrage.
Ouvrage : « ${String(r.x.d||"").slice(0,300)} » · unité : ${r.x.u||"?"} · quantité au bordereau : ${r.qq} · marché : « ${String(a.obj||"").slice(0,200)} » · lieu : ${(a.lieux||[]).join(", ")||"non précisé"}.
Catégories : mat (matériaux et fournitures), mo (main-d'œuvre, en heures), mt (matériel), tr (transport). Tu n'as accès à AUCUN devis, mercuriale ni internet : n'invente ni fournisseur, ni date, ni référence de devis. N'utilise jamais les prix d'une autre entreprise.${Bi.length?"\nRéférences internes de la MÊME société (indicatives) :\n"+Bi.join("\n"):""}
Pour chaque ressource : categorie, designation, unite, quantite par unité d'ouvrage, pu (DH HT, ou null si tu ne peux pas l'estimer). Donne une justification courte et ta confiance (haute|moyenne|basse).
Réponds uniquement par un objet JSON : {"ressources":[{"categorie":"mat|mo|mt|tr","designation":"…","unite":"…","quantite":nombre,"pu":nombre ou null}],"justification":"…","confiance":"haute|moyenne|basse"}`;
  try{const res=await S.sample.json(prompt,{modelTier:"default",cache:false});if(!res||!Array.isArray(res.ressources))throw{code:"invalid_json"};
    const rows=res.ressources.filter(z=>z&&["mat","mo","mt","tr"].includes(z.categorie)&&String(z.designation||"").trim()).slice(0,40).map(z=>({t:z.categorie,d:String(z.designation).slice(0,140),u:String(z.unite||"").slice(0,16),q:b31Num(z.quantite)!=null&&+z.quantite>=0?Math.round(+z.quantite*10000)/10000:null,pu:b31Num(z.pu)!=null&&+z.pu>0?Math.round(+z.pu*100)/100:null}));
    if(!rows.length)throw{code:"vide",message:"aucune ressource exploitable"};
    B31.sdIA[key]={le:new Date().toISOString(),soc:a.soc,rows,just:String(res.justification||"").slice(0,400),conf:b31Conf(res.confiance)};toast(rows.length+" ressource(s) proposée(s) : hypothèse à vérifier, rien n'est écrit.");}
  catch(e){B31.sdErr[key]="Proposition IA interrompue ("+b31PropMsg(e)+") : rien n'est écrit.";}finally{B31.sdBusy=null;render();}}
function b31SdAccepterIA(id,a,k){if(!editable())return toast(RO_MSG);const IA=B31.sdIA[id+"|"+k],X=bpX(id);if(!IA||IA.soc!==a.soc)return toast("Proposition absente ou d'une autre société : rien n'est accepté.");
  const sd={mat:[],mo:[],mt:[],tr:[]},le=new Date().toISOString();IA.rows.forEach(r=>sd[r.t].push({d:r.d,u:r.u,q:r.q==null?"":r.q,pu:r.pu==null?"":r.pu,st:"ia",four:"",date:"",ref:"Proposition IA du "+fmtDT(IA.le)+" acceptée par "+(S.role.me||"auteur non identifié")+" le "+fmtDT(le),soc:a.soc}));
  b31SdAvant(id);X.sd=X.sd||{};X.sd[k]=sd;delete B31.sdIA[id+"|"+k];render();toast("Sous-détail accepté comme HYPOTHÈSE (aucun devis, aucun fournisseur ni date), non encore enregistré : vérifiez chaque ressource puis « Enregistrer le sous-détail ». Le PU du bordereau n'est pas modifié.");}
/* b31-6b · les modifications du sous-détail restent en attente (rien n'est écrit en arrière-plan) jusqu'à « Enregistrer le sous-détail »
   (coût seul, PU inchangé) ou « Reporter » (coût + PU) : chacune crée d'abord un événement d'historique avec le coût avant / après */
function b31SdAvant(id){if(!B31.sdBase[id]){const X=bpX(id);B31.sdBase[id]={sd:JSON.parse(JSON.stringify(X.sd||{})),k:X.k?JSON.parse(JSON.stringify(X.k)):null};}}
function b31SdCalcAvec(id,k,a,sd,K){const X=bpX(id),s0=X.sd,k0=X.k;try{X.sd=sd;if(K)X.k=K;else delete X.k;return b31SdCalc(id,k,a);}finally{X.sd=s0;if(k0)X.k=k0;else delete X.k;}}
function b31CoutJ(c){return c?{deb_sec:c.ds,cout_revient:c.complet?c.cr:null,prix_vente_theorique:c.complet?c.pv:null,complet:c.complet,inconnus:c.inc.concat(c.etr).slice(0,10)}:{complet:false,absent:true};}
function b31SdCtx(id,a,k){const X=bpX(id),B=B31.sdBase[id]||{sd:X.sd||{},k:X.k||null},av=b31SdCalcAvec(id,k,a,B.sd,B.k),ap=b31SdCalc(id,k,a),p=X.p[k],has=p!==undefined&&p!==""&&p!=null;
  const Kf=K=>(z=>({fc:+z.fc||0,fg:+z.fg||0,al:+z.al||0,ben:+z.ben||0}))(Object.assign({},SD_K0,K||{}));
  return{ligne:k,cout_avant:b31CoutJ(av),cout_apres:b31CoutJ(ap),pu_actuel:has?+p:null,marge_unitaire:has&&ap&&ap.complet?Math.round((+p-ap.cr)*100)/100:null,
    marge_pct_pu:has&&ap&&ap.complet&&+p>0?Math.round((+p-ap.cr)/+p*10000)/100:null,frais_avant:Kf(B.k),frais_apres:Kf(X.k),frais_defaut:!X.k,
    ressources:JSON.parse(JSON.stringify((X.sd||{})[k]||null))};}
async function b31SdEnregistrer(id,a,k){const X=bpX(id),p0=JSON.stringify(X.p||{}),l0=JSON.stringify(X.lock||{});const ctx=b31SdCtx(id,a,k);
  try{await b31Ecrire(id,a,{type:"cout",label:"Sous-détail ligne "+k+" enregistré (PU inchangé) : coût de revient "+(ctx.cout_apres.cout_revient==null?"inconnu":fmtN(ctx.cout_apres.cout_revient)+" DH")+(ctx.marge_unitaire!=null?", marge "+fmtN(ctx.marge_unitaire)+" DH sur le PU actuel":""),lignes:[],contexte:ctx});
    if(JSON.stringify(X.p||{})!==p0||JSON.stringify(X.lock||{})!==l0)throw new Error("incohérence : PU ou verrous modifiés");delete B31.sdBase[id];render();toast("Sous-détail enregistré et tracé dans l'historique ; PU du bordereau inchangé.");}
  catch(e){render();toast("Sous-détail non enregistré, rien n'est écrit : "+(e&&e.message||e));}}
async function b31SdReporter(id,a,k){const X=bpX(id);if((X.lock||{})[k])return toast("Ligne verrouillée : rien n'est reporté.");const c=b31SdCalc(id,k,a);if(!c||!c.complet)return toast("Sous-détail incomplet : coût inconnu, rien n'est reporté.");
  const av=X.p[k],now=new Date().toISOString(),prov={v:6,m:"sd",le:now,par:S.role.me||null,methode:"sd",pu_avant:av===undefined||av===""||av==null?null:+av,pu_base:c.cr,propose:c.pv,applique:c.pv,coef_pct:null,
    source_lab:"Sous-détail de "+socCourt(a.soc),justification:"Déboursé sec "+fmtN(c.ds)+" DH ; coût de revient "+fmtN(c.cr)+" DH (frais de chantier "+c.K.fc+" %, frais généraux "+c.K.fg+" %, aléas "+c.K.al+" %) ; bénéfice "+c.K.ben+" %",
    hypotheses:c.nh||c.kDefaut?[c.nh?c.nh+" ressource(s) en hypothèse ou sans source":"",c.kDefaut?"taux de frais par défaut non validés":""].filter(Boolean).join(" ; "):null,confiance:c.nh||c.kDefaut?"basse":null};
  try{await b31Ecrire(id,a,{type:"sous_detail",label:"Report du sous-détail ligne "+k+" : "+fmtN(c.pv)+" DH HT",lignes:[{k,apres:c.pv,prov}],contexte:Object.assign(b31SdCtx(id,a,k),{deb_sec:c.ds,cout_revient:c.cr,frais:{fc:c.K.fc,fg:c.K.fg,al:c.K.al,ben:c.K.ben},hypotheses:c.nh,frais_defaut:c.kDefaut}),base:"SOUS-DÉTAIL SOCIÉTÉ"});
    delete B31.sdBase[id];B31.sd=null;render();toast("Prix de vente "+fmtN(c.pv)+" DH HT reporté au bordereau et tracé dans l'historique.");}
  catch(e){toast("Rien n'est reporté : "+(e&&e.message||e));}}
/* ---------- b31-6 · comparaison des scénarios (aperçus non destructifs) ---------- */
function b31Comparer(id,a){const SC=((B31.ch[id]&&B31.ch[id].doc&&B31.ch[id].doc.soc===a.soc?B31.ch[id].doc:{}).scenarios)||{};
  return B31_SCEN.map(([k,l])=>{const s=SC[k];if(!s||s.pct==null)return{k,l,vide:true};const pr=b31Previsu(id,a,+s.pct);return{k,l,pct:+s.pct,le:s.le,pr,m:pr.ok?b31Metr(id,a,pr):null};});}
function b31CmpHtml(id,a,ET){const R=b31Comparer(id,a),ed=editable(),def=R.filter(z=>!z.vide);
  let h=`<p>Comparaison côte à côte des scénarios de ${esc(socCourt(a.soc))}, calculés sur les PU propres à la société (aperçus non destructifs : rien n'est écrit). Les noms ne garantissent aucun résultat ; aucune marge ni niveau de compétitivité n'est inventé.</p>`;
  if(!def.length)return h+`<p>Aucun scénario défini : saisissez un pourcentage pour au moins un scénario (bouton « Scénarios »).</p>`;
  const c=(z,f,fn)=>z.vide?`<td class="b31-na">non défini</td>`:!z.pr.ok?`<td class="b31-na">${f==="pct"?esc(b31PctTxt(z.pct)):f==="cible"&&ET.E.c!=null?b31Dh(b31Cible(ET.E.c,z.pct)):f==="art"?`<span class="b31-ko-t">Aperçu impossible : ${esc(String(z.pr.why).slice(0,160))}</span>`:"—"}</td>`:`<td>${fn(z)}</td>`;
  const lig=[["% demandé","pct",z=>esc(b31PctTxt(z.pct))],["TTC cible","cible",z=>b31Dh(z.pr.cibleC)],["TTC obtenu après arrondis","",z=>b31Dh(z.pr.T.ttcC)+`<small>${z.pr.resteC>0?"+":""}${fmtN(z.pr.resteC/100)} DH</small>`],["Total HT","",z=>b31Dh(z.pr.T.htC)],["TVA","",z=>b31Dh(z.pr.T.tvaC)+`<small>${esc(z.pr.tva.lab)} · ${esc(B31_TVA_ETAT[z.pr.tva.etat])}</small>`],
    ["Coût connu (couverture)","",z=>esc(z.m.cout_couverture)+" ligne(s)"+(z.m.cout_revient_ht!=null?`<small>coût de revient ${fmtN(+z.m.cout_revient_ht)} DH HT</small>`:`<small>coût incomplet</small>`)],
    ["Marge (base : vente HT)","",z=>z.m.marge_ht==null?`<span class="b31-ko-t">non calculée (coûts incomplets)</span>`:`${(+z.m.marge_ht<0?"−":"")+fmtN(Math.abs(+z.m.marge_ht))} DH · ${String(z.m.marge_pct_vente).replace(".",",")} %${+z.m.marge_ht<0?`<small class="b31-ko-t">vente à perte</small>`:""}`],
    ["Art. 44 B","art",z=>b31Pill(z.pr.g44&&z.pr.g44.bloque?"bas":z.pr.A44.k,z.pr.g44&&z.pr.g44.bloque?"Hors bornes : application bloquée":z.pr.A44.k==="bornes"?"Dans les bornes":"À vérifier")+(z.pr.A44.minC!=null?`<small>bornes ${b31Dh(z.pr.A44.minC)} – ${b31Dh(z.pr.A44.maxC)}</small>`:"")],
    ["Lignes verrouillées","",z=>String(z.pr.lockN)],["Bases proposées","",z=>(z.pr.nProp?z.pr.nProp+" ("+[z.pr.nRef?z.pr.nRef+" réf.":"",z.pr.nCh?z.pr.nCh+" Chiffreur":"",z.pr.nIA?z.pr.nIA+" IA":""].filter(Boolean).join(", ")+")":"aucune")]];
  h+=`<div class="b31-tw"><table class="b31-cmp" data-b31-cmp="1"><thead><tr><th scope="col">Indicateur</th>${R.map(z=>`<th scope="col" data-b31-cmpk="${z.k}">${esc(z.l)}</th>`).join("")}</tr></thead><tbody>${lig.map(([lab,f,fn])=>`<tr><th scope="row">${esc(lab)}</th>${R.map(z=>c(z,f,fn)).join("")}</tr>`).join("")}
    <tr><th scope="row">Action</th>${R.map(z=>`<td>${!z.vide&&ed?`<button type="button" class="b31-btn b31-xs" data-b31-cmpprev="${z.k}" data-act="${act(()=>{B31.pct[id]=String(z.pct).replace(".",",");B31.mode[id]="pct";const pr=b31Previsu(id,a,z.pct);if(pr.ok)pr.scen=z.l;B31.prev[id]=pr;B31.dlg=null;render();})}">Prévisualiser ce scénario</button>`:""}</td>`).join("")}</tr></tbody></table></div>`;
  const K=sdK(id);h+=`<p class="b31-src">Taux de frais utilisés pour le coût (${bpX(id).k?"taux du dossier":"valeurs de départ : hypothèses"}) : chantier ${K.fc} %, généraux ${K.fg} %, aléas ${K.al} %, bénéfice ${K.ben} %. Marge = vente HT − coût de revient HT, affichée seulement si le coût de toutes les lignes est connu. Sources et propositions IA : voir l'aperçu de chaque scénario (justification ligne par ligne).</p>`;
  if(ed)h+=`<div class="b31-row"><button type="button" class="b31-btn b31-sm" data-b31-cmpfig="1" data-act="${wact(()=>b31EvSeul(id,a,"comparaison","Comparaison des scénarios figée",{scenarios:R.filter(z=>!z.vide).map(z=>Object.assign({scenario:z.l},z.m||{pct:z.pct,erreur:z.pr.why}))}).then(ev=>{render();toast("Comparaison figée dans l'historique (événement e"+ev.seq+", immuable).");}).catch(e=>toast("Comparaison non enregistrée : "+(e&&e.message||e))))}">Figer cette comparaison dans l'historique</button></div><p class="b31-src">Appliquer un scénario : « Prévisualiser ce scénario », puis « Appliquer » depuis un aperçu à jour (garde de l'art. 44 B recalculée au moment d'écrire).</p>`;
  return h;}
/* ---------- b31-6 · historique des événements de prix ---------- */
function b31EvHtml(id,a){const all=B31.ev[id]||[],L=b31EvSoc(id,a),X=bpX(id),autres=all.length-L.length,nPu=Object.values(X.p||{}).filter(v=>v!==""&&v!=null).length;
  let h=`<h4>Événements de prix (${L.length}, automatiques et immuables)</h4>`;
  if(B31.evErr[id])h+=`<p class="b31-ko-t">Historique illisible : ${esc(B31.evErr[id])}. Aucune écriture de prix n'est possible tant qu'il n'est pas lu.</p>`;
  if(autres)h+=`<p class="b31-ko-t">${autres} événement(s) rattaché(s) à une autre société ignoré(s) (FIN-ISO-001).</p>`;
  if(!L.length)return h+`<p data-b31-ev0="1">Aucun événement de prix enregistré pour ${esc(socCourt(a.soc))}. L'historique automatique commence avec b31-6 ; ${nPu?"les "+nPu+" PU actuels n'ont pas d'historique antérieur et aucun passé n'est reconstitué.":"aucun PU n'est encore saisi."}</p>`;
  const tt=t=>t?(t.ttc!=null?fmtN(+t.ttc)+" TTC":t.ht!=null?fmtN(+t.ht)+" HT (TTC non calculé)":"—"):"—";
  return h+`<ul class="b31-ul b31-evl">${L.map(e=>{const st=b31EvStatut(e,all,X);return`<li data-b31-ev="${esc(e.seq)}"><details><summary><b>e${esc(e.seq)}</b> · ${esc(fmtDT(e.le))} · ${esc(e.par||"auteur non identifié")} · ${esc(e.label||e.type)}${e.type!=="echec_ecriture"&&e.type!=="comparaison"?` · ${esc(tt(e.totaux_avant))} → ${esc(tt(e.totaux_apres))}`:""}${st?" "+b31Pill(st.k==="ok"?"valide":st.k==="ko"?"bas":"verifier",st.t):""}</summary>
    ${(e.lignes||[]).length?`<ul class="b31-ul">${e.lignes.slice(0,80).map(z=>{const P=b31Prov(z.prov,z.apres!=null);return`<li>N° ${esc(z.n||z.k)} ${esc(String(z.d||"").slice(0,70))} : ${z.avant==null?"vide":fmtN(z.avant)} → <b>${z.apres==null?"vide":fmtN(z.apres)}</b>${P?`<small class="b31-src">${esc(P.court)}${P.det.filter(d=>/Justification|Hypothèses|Confiance/.test(d[0])).map(d=>" · "+d[0]+" : "+d[1]).join("")}</small>`:""}</li>`;}).join("")}${e.lignes.length>80?`<li>… (+${e.lignes.length-80})</li>`:""}</ul>`:""}
    ${e.contexte&&e.contexte.cout_apres?`<p class="b31-src" data-b31-evcout="1">Ligne ${esc(e.contexte.ligne)} : coût de revient ${e.contexte.cout_avant&&e.contexte.cout_avant.cout_revient!=null?fmtN(e.contexte.cout_avant.cout_revient)+" DH":"inconnu"} → ${e.contexte.cout_apres.cout_revient!=null?fmtN(e.contexte.cout_apres.cout_revient)+" DH":"inconnu"} · PU ${e.contexte.pu_actuel==null?"non saisi":fmtN(e.contexte.pu_actuel)+" DH"}${e.type==="cout"?" (inchangé)":""}${e.contexte.marge_unitaire!=null?" · marge "+fmtN(e.contexte.marge_unitaire)+" DH ("+String(e.contexte.marge_pct_pu).replace(".",",")+" % du PU)":""}</p>`:""}${e.tva_apres&&e.type==="tva"?`<p class="b31-src">${esc(e.tva_avant?e.tva_avant.txt:"")} → ${esc(e.tva_apres.txt)}</p>`:""}${e.contexte&&e.contexte.scenarios?`<p class="b31-src">${esc(e.contexte.scenarios.map(z=>z.scenario+" "+(z.pct!=null?b31PctTxt(z.pct):"")+" : TTC "+(z.ttc||"—")+", marge "+(z.marge_ht!=null?z.marge_ht+" ("+z.marge_pct_vente+" %)":"non calculée")+", art. 44 "+(z.art44||"—")).join(" ; "))}</p>`:""}
    <p class="b31-src">Empreinte ${esc(String(e.hash||"").slice(0,12))}…${e.precedent?" · précédent "+esc(String(e.precedent).split("~").pop()):""}</p></details></li>`;}).join("")}</ul>`;}
/* ---------- b31-6 · export Word / Excel du bordereau avec la TVA documentée (jamais un taux par défaut) ---------- */
async function b31Export(id,a,fmt){const b=S.bp[id],X=bpX(id),M=b31TvaM(id,a);if(!S.downloads||!b)return;
  const cad=b.cadre,th=`<tr><th>N° prix</th><th>Désignation des prestations</th><th>Unité</th><th>${cad?"Qté min":"Quantité"}</th>${cad?"<th>Qté max</th>":""}<th>Prix unitaire HT (DH)</th><th>${cad?"Total min HT":"Prix total HT (DH)"}</th>${cad?"<th>Total max HT</th>":""}</tr>`;
  const num=v=>fmt==="xls"?(v===""||v==null?"":String(Math.round(+v*100)/100)):pu2(v),c2=c=>c==null?"":fmt==="xls"?s2c(c):fmtN(c/100);let h="";
  b.lots.forEach((L,l)=>{let sec=null,rows="",hc=0,hx=0,miss=0,tvOk=M.calc;const G={},GX={};
    L.lignes.forEach((x,i)=>{const k=l+"-"+i,p=X.p[k],q=bpQ(id,l,i,x),has=p!==undefined&&p!==""&&p!=null,r=M.rate(k);if((x.s||"")!==sec){sec=x.s||"";if(sec)rows+=`<tr><td></td><td colspan="${cad?7:5}"><b>${esc(sec)}</b></td></tr>`;}
      const mc=has&&q!=null?ligneC(q,p):null,mx=has&&x.qmax?ligneC(x.qmax,p):null;if(mc==null)miss++;else{hc+=mc;if(r==null)tvOk=false;else G[r]=(G[r]||0)+mc;}if(mx!=null){hx+=mx;if(r!=null)GX[r]=(GX[r]||0)+mx;}
      rows+=`<tr><td>${esc(x.n||"")}</td><td>${esc(x.d)}${M.mixte&&r!=null?` <i>(TVA ${esc(b31TxPct(r))})</i>`:""}</td><td>${esc(x.u||"")}</td><td class="r">${q==null?"":num(q)}</td>${cad?`<td class="r">${num(x.qmax)}</td>`:""}<td class="r">${has?num(p):""}</td><td class="r">${mc==null?"":c2(mc)}</td>${cad?`<td class="r">${mx==null?"":c2(mx)}</td>`:""}</tr>`;});
    const sp=cad?6:5,tr=(lab,v,v2)=>`<tr><td colspan="${sp}" class="r"><b>${esc(lab)}</b></td><td class="r"><b>${v}</b></td>${cad?`<td class="r"><b>${v2}</b></td>`:""}</tr>`,tg=g=>Object.entries(g).sort((u,w)=>w[0]-u[0]);
    let tv=0,tvx=0,tvR="";if(tvOk)tg(G).forEach(([r,hcc])=>{const t=Math.floor((hcc*+r+50)/100),tx=Math.floor(((GX[r]||0)*+r+50)/100);tv+=t;tvx+=tx;tvR+=tr("TVA "+b31TxPct(r)+(Object.keys(G).length>1?" (sur "+fmtN(hcc/100)+" HT)":""),c2(t),c2(tx));});
    else tvR=tr("TVA : "+(M.etat==="absent"?"taux non renseigné":"taux incomplet")+" — non calculée","","");
    h+=`${L.lot?`<h3>${esc(L.lot)}</h3>`:""}<table>${th}${rows}${tr("Total HT",c2(hc),c2(hx))}${tvR}${tr("Total TTC",tvOk?c2(hc+tv):"non calculé",tvOk?c2(hx+tvx):"")}</table>
     ${tvOk&&!miss&&hc>0?`<p>Arrêté le présent bordereau des prix - détail estimatif${L.lot?" ("+esc(L.lot.split(" - ")[0])+")":""} à la somme de : <b>${esc(enLettres((cad&&hx?hx+tvx:hc+tv)/100))}</b> toutes taxes comprises.</p>`:`<p><i>Montant en lettres non produit : ${miss?miss+" prix manquant(s)":"TVA non calculée"}.</i></p>`}`;});
  const s0=SOCBY[a.soc]||{},note=`<p style="font-size:9pt">${esc(M.txt)}.</p>`;
  const html=`<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="utf-8"><style>body{font-family:"Times New Roman",serif;font-size:11pt}table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border:1px solid #000;padding:3px 5px;vertical-align:top}th{background:#e8e8e8}.r{text-align:right;white-space:nowrap}h2{text-align:center;font-size:14pt}@page{size:A4;margin:1.5cm}</style></head><body>
   <p>${esc(a.procedure||"Appel d'offres")} n° ${esc(a.ref||"")} · ${esc(a.mo||"")}</p><p><b>Objet :</b> ${esc(a.obj||"")}</p><h2>Bordereau des prix - détail estimatif</h2>${h}${M.ok?"":note}
   <p style="text-align:right;margin-top:18px">${(()=>{const f=pfGet(a,a.soc);return`Fait à ${esc(f.faitA||"……………")}, le ${esc(fmtIso(f.date||isoToday()))}<br>${esc(s0.court||"")}${f.sig?"<br>"+esc(f.sig)+", "+esc(f.qual||"Gérant"):""}`;})()}<br>Signature et cachet du concurrent</p></body></html>`;
  const base="Bordereau_"+String(a.ref||id).replace(/[^A-Za-z0-9]+/g,"-");B31.dernierExport={id,fmt,html};
  S.livrCtx={id,k:"bpu:"+fmt,t:fmt==="xls"?"Bordereau des prix (Excel)":"Bordereau des prix et détail estimatif",emp:"chiffreur",sign:fmt!=="xls",nopdf:fmt==="xls"};
  try{if(fmt==="xls")await S.downloads.save({filename:base+".xls",data:new Blob(["﻿"+html],{type:"application/vnd.ms-excel"})});else{const W=await withCachet(a.soc,html,html,[]);await S.downloads.save({filename:base+".doc",data:new Blob([W.data],{type:"application/msword"}),preview:W.preview});}toast(fmt==="xls"?"Fichier Excel prêt.":"Fichier Word prêt : à signer et cacheter par la gérance.");}
  catch(e){if(!e||e.code!=="declined")toast("Enregistrement impossible : "+(e&&e.code||"erreur"));}}
/* ---------- b31-6 · totaux et offre figée de l'application avec la TVA documentée ----------
   bpTot : taux du dossier quand ils sont connus (identique à l'existant pour un taux unique) ; sinon comportement existant, marqué tvaDefaut.
   offreBpu : chaque ligne de l'offre figée porte son taux ; offreCalc : TVA par taux (offres figées antérieures, sans taux : calcul d'origine). */
{const _bpTotB31=bpTot;bpTot=function(id){const a=S.ao[id],b=S.bp[id];let M=null;try{M=a&&b?b31TvaM(id,a):null;}catch(e){M=null;}if(!M||!M.calc){const T=_bpTotB31(id);return T?Object.assign(T,{tvaDefaut:true}):T;}
  const X=bpX(id),tg=g=>Object.entries(g).reduce((t,[r,h])=>t+Math.floor((h*+r+50)/100),0);
  const lots=b.lots.map((L,l)=>{let hc=0,hxc=0,n=0,miss=0;const G={},GX={};L.lignes.forEach((x,i)=>{const k=l+"-"+i,p=X.p[k],q=bpQ(id,l,i,x);
    if(p!==undefined&&p!==""&&q!=null){const c=ligneC(q,p),r=M.rate(k);hc+=c;G[r]=(G[r]||0)+c;if(x.qmax){const cx=ligneC(x.qmax,p);hxc+=cx;GX[r]=(GX[r]||0)+cx;}n++;}else miss++;});
    const tv=tg(G),tvx=tg(GX);return{ht:hc/100,htx:hxc/100,n,miss,tva:tv/100,ttc:(hc+tv)/100,ttcx:(hxc+tvx)/100};});
  const s0=k=>Math.round(lots.reduce((t,x)=>t+x[k],0)*100)/100;
  return{lots,ht:s0("ht"),ttc:s0("ttc"),htx:s0("htx"),ttcx:s0("ttcx"),n:lots.reduce((t,x)=>t+x.n,0),miss:lots.reduce((t,x)=>t+x.miss,0),tvaEtat:M.etat};};}
{const _offreBpuB31=offreBpu;offreBpu=function(id){const R=_offreBpuB31(id),a=S.ao[id];if(!R||!a)return R;let M=null;try{M=b31TvaM(id,a);}catch(e){}if(!M||!M.calc)return R;return R.map(l=>Object.assign({},l,{tva:String(M.rate(l.k))}));};}
offreCalc=function(bpu){const G={};let ht=0;bpu.forEach(l=>{const c=ligneC(l.q,l.pu),r=l.tva!=null&&l.tva!==""?+l.tva:BP_TVA;ht+=c;G[r]=(G[r]||0)+c;});
  const tva=Object.entries(G).reduce((t,[r,h])=>t+Math.floor((h*+r+50)/100),0);return{total_ht:s2c(ht),tva:s2c(tva),total_ttc:s2c(ht+tva)};};
/* ---------- b31-6 · écouteurs des nouveaux champs (TVA, sous-détail, frais) ---------- */
function b31Ecoute(){const V=document.getElementById("view");let tS=null;
  const H=e=>{const t=e.target,w=t&&t.closest&&t.closest("[data-b31]");if(!w||!t.dataset)return;const id=w.dataset.b31,a=S.ao[id];if(!a)return;
    if(t.dataset.b31Tvaf){const F=b31TvaEd(id,a),f=t.dataset.b31Tvaf;F[f]=t.type==="checkbox"?t.checked:t.value;if(f==="mixte")render();}
    else if(t.dataset.b31Tval){b31TvaEd(id,a).lignes[t.dataset.b31Tval]=t.value;}
    else if((t.dataset.b31sd||t.dataset.b31sdk)&&B31.sd&&B31.sd.id===id&&editable()){const X=bpX(id),k=B31.sd.k;
      b31SdAvant(id);if(t.dataset.b31sdk){const v=b31Num(String(t.value).replace(",","."));X.k=Object.assign({},sdK(id),{[t.dataset.b31sdk]:v==null||v<0?0:v});}
      else{const[g,j,f]=t.dataset.b31sd.split("|"),r=((X.sd||{})[k]||{})[g]&&X.sd[k][g][+j];if(!r)return;
        if(f==="q"||f==="pu"){const v=String(t.value).trim().replace(",",".");r[f]=v===""?"":isFinite(+v)?+v:"";}else r[f]=t.value;r.soc=r.soc||a.soc;
        if(f==="d"&&e.type==="change"&&(r.pu===""||r.pu==null)){const z=b31SdBiblio(a).L.find(z=>z.t===g&&norm(z.d)===norm(r.d));if(z){r.pu=z.pu;if(!r.u)r.u=z.u;r.st=z.st||"interne";r.four=z.four||"";r.date=z.date||"";r.ref="Référence de "+socCourt(a.soc)+" : "+z.ref;render();}}}
      const sm=document.getElementById("b31-sdsum");if(sm)sm.innerHTML=b31SdSum(id,k,a);const pe=document.getElementById("b31-sdpend");if(pe)pe.hidden=false;const rb=document.querySelector("[data-b31-sdrep]");if(rb){const cc=b31SdCalc(id,k,a);rb.disabled=!(cc&&cc.complet);}}};
  V.addEventListener("input",H);V.addEventListener("change",H);}
/* ---------- saisie en direct ---------- */
function b31MajLive(){const w=document.querySelector("[data-b31]");if(!w)return;const id=w.dataset.b31,a=S.ao[id];if(!a)return;const ET=b31Etat(id,a);
  const r=document.getElementById("b31-recap");if(r)r.innerHTML=b31Recap(id,a,ET);}
/* b31-6 : dans le bureau B3.1, la saisie d'un PU n'écrit plus directement (le gestionnaire existant n'est pas appelé) : valeur en attente,
   puis à la validation du champ, événement d'historique et écriture du bordereau (b31Manuel) */
document.addEventListener("input",e=>{const t=e.target,w=t&&t.closest&&t.closest("[data-b31]");if(!w||!t.dataset||!t.dataset.bp)return;e.stopImmediatePropagation();
  const id=w.dataset.b31,k=t.dataset.bp;if(!editable())return;(B31.saisie[id]=B31.saisie[id]||{})[k]=t.value;
  const el=document.getElementById("bpt"+k),[l,i]=k.split("-").map(Number),b=S.bp[id],v=b31PuNorm(t.value);if(el&&b){const x=b.lots[l].lignes[i],qq=bpQ(id,l,i,x);el.innerHTML=v!==null&&v!==""&&qq!=null?fmtN(ligneC(qq,v)/100)+' <small class="b31-pend">non enregistré</small>':'<span class="b31-ko-t">—</span>';}
  delete B31.prev[id];b31MajLive();},true);
document.addEventListener("change",e=>{const t=e.target,w=t&&t.closest&&t.closest("[data-b31]");if(!w||!t.dataset||!t.dataset.bp)return;e.stopImmediatePropagation();
  const id=w.dataset.b31,a=S.ao[id];if(a)b31Manuel(id,a,t.dataset.bp,t.value);},true);
document.getElementById("view").addEventListener("input",e=>{const t=e.target;if(!t||!t.dataset)return;
  if(t.dataset.b31Q){B31.recherche[t.dataset.b31Q]=t.value;B31.n[t.dataset.b31Q]=60;clearTimeout(b31MajLive._q);b31MajLive._q=setTimeout(render,250);}
  else if(t.dataset.b31Pct){B31.pct[t.dataset.b31Pct]=t.value;delete B31.prev[t.dataset.b31Pct];clearTimeout(b31MajLive._p);b31MajLive._p=setTimeout(render,350);}
  else if(t.dataset.b31Simh){B31.simH[t.dataset.b31Simh]=t.value;clearTimeout(b31MajLive._s);b31MajLive._s=setTimeout(render,400);}});
b31Ecoute();
document.getElementById("view").addEventListener("toggle",e=>{const t=e.target;if(t&&t.matches&&t.matches("details[data-b31-regle]")){const w=t.closest("[data-b31]");if(w)B31.ouv[w.dataset.b31+"|regle"]=t.open;}},true);
/* ---------- raccordement : étape « Prix » → B3.1 ; vue pleine largeur dans le bureau B3.1 ---------- */
/* b31-6b : résumé du prix des listes (cartes de bureau, parcours express) recalculé avec la TVA documentée du dossier ;
   taux absent → HT et « TTC non calculé — TVA à renseigner » ; hypothèse / relevé DCE nommés ; montant validé antérieur nommé historique */
function b31ResumeTTC(id,a){let M,T;try{M=b31TvaM(id,a);T=b31Tot(id,bpX(id).p||{},M);}catch(e){return null;}if(!T)return null;
  if(T.ttcC==null)return b31Dh(T.htC)+" HT · TTC non calculé — "+(M.etat==="absent"?"TVA à renseigner":"TVA à compléter ("+M.sans.length+" ligne(s) sans taux)");
  return b31Dh(T.ttcC)+" TTC"+(M.etat==="confirme"?(M.set.length>1?" ("+M.lab+" confirmée)":""):" — "+M.lab+" "+B31_TVA_ETAT[M.etat]);}
{const _aoStepsB31=aoSteps;aoSteps=function(id,a){const L=_aoStepsB31(id,a),n=L.find(s=>s.k==="prix");if(n)n.body=()=>vB31(id,a);
  try{const b=S.bp[id],T=b?bpTot(id):null;if(n&&T&&!T.miss&&typeof n.res==="string"){const v=" : "+dh(T.ttc)+" TTC",M=b31TvaM(id,a),r=b31ResumeTTC(id,a);
    if(r&&n.res.endsWith("Bordereau chiffré, à valider"+v))n.res=n.res.slice(0,-v.length)+" : "+r;
    else if(r&&/Validé à [^:]*$/.test(n.res.slice(0,-v.length))&&n.res.endsWith(v)&&!M.ok)n.res+=" — montant historique de l'offre figée, pas un TTC actuel ("+(M.etat==="absent"?"TVA non renseignée":M.lab+" "+B31_TVA_ETAT[M.etat])+")";}}catch(e){}
  return L;};}
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
.b31-tab col.c1{width:46px}.b31-tab col.c3{width:52px}.b31-tab col.c4{width:74px}.b31-tab col.c5{width:112px}.b31-tab col.c6{width:116px}.b31-tab col.c7{width:128px}
.b31-tab th{font-size:11.5px;font-weight:600;color:var(--b21-muted);text-align:left;padding:8px 8px;border-bottom:1px solid var(--b21-line);background:var(--b21-ivoire);position:sticky;top:0;z-index:1}
.b31-tab thead th:nth-child(n+4){text-align:right}
.b31-tab td{padding:7px 8px;border-bottom:1px solid var(--b21-line2);vertical-align:top;font-size:13px}
.b31-n{color:var(--b21-muted);font-size:12px}.b31-d{overflow-wrap:anywhere}.b31-dt{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;line-height:1.4}
.b31-q,.b31-t{text-align:right;white-space:nowrap}.b31-t{font-weight:600}
.b31-p{text-align:right}.b31-p input{width:100%;text-align:right;border:1px solid var(--b21-line);border-radius:6px;padding:5px 7px;font:600 13px/1.2 var(--body,inherit);background:var(--b21-card);color:var(--b21-ink);font-variant-numeric:tabular-nums}
.b31-p input:disabled{background:var(--b21-nabg);color:var(--b21-ink)}.b31-nop .b31-p input{border-color:#E2B4AC;background:var(--b21-kobg)}
.b31-pv{display:block;color:var(--b21-or-p);font-weight:600;font-size:12px;margin-top:2px}
.b31-a{text-align:right}.b31-acts{display:flex;flex-wrap:wrap;justify-content:flex-end;align-items:center;gap:2px;min-width:0}.b31-sdb{white-space:nowrap}
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
.b31-pend{display:block;color:var(--b21-or-p);font-size:11px;font-weight:600;margin-top:2px}.b31-t .b31-pend{display:inline;font-weight:400}.b31-sl.b31-nd{font-style:italic}.b31-sl .b31-lnk{font-size:11px;padding:0 2px;margin-left:4px}
.b31-provd{display:block;margin:6px 0 2px;padding:6px 8px;border:1px solid var(--b21-line);border-radius:8px;background:var(--b21-card);font-size:11.5px;line-height:1.45}.b31-provd dt{display:inline;color:var(--b21-muted)}.b31-provd dt::after{content:" : "}.b31-provd dd{display:inline;margin:0;overflow-wrap:anywhere}.b31-provd dd::after{content:"";display:block}
.b31-tva h3 .b31-pill{margin-left:6px}.b31-tva p{font-size:12.5px;margin:4px 0}.b31-tvf summary,.b31-tvl summary{cursor:pointer;font-weight:600;color:var(--b21-or-p);margin:8px 0 4px;font-size:12.5px}
.b31-tvg{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,120px),1fr));gap:8px}.b31-tvg label,.b31-tvl label{display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:var(--b21-muted)}.b31-tvl label{flex-direction:row;align-items:center;justify-content:space-between;gap:8px}.b31-xin{width:76px;flex:0 0 76px}
.b31-chk{display:flex;gap:6px;align-items:center;font-size:12.5px;margin-top:8px}
.b31-cmp{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums;min-width:520px}.b31-cmp th,.b31-cmp td{border-bottom:1px solid var(--b21-line2);padding:6px 8px;text-align:left;vertical-align:top}.b31-cmp thead th{background:var(--b21-ivoire);font-size:12px}.b31-cmp tbody th{color:var(--b21-muted);font-weight:600;font-size:12px;width:24%}.b31-cmp small{display:block;color:var(--b21-muted);font-size:11px}.b31-na{color:var(--b21-muted);font-style:italic}
.b31-sdg{border:1px solid var(--b21-line);border-radius:10px;padding:8px 10px;margin:10px 0}.b31-sdgh{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:6px;font-size:13px}
.b31-sdrw{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px 8px;align-items:end;padding:8px 0;border-top:1px dashed var(--b21-line2)}.b31-sdrw .b31-sdd{grid-column:span 2}.b31-sdx{grid-column:1 / -1;display:flex;justify-content:flex-end;align-items:center;gap:8px}.b31-sdrw label{display:flex;flex-direction:column;gap:2px;font-size:11px;color:var(--b21-muted);min-width:0}.b31-sdrw .b31-in{width:100%;min-width:0}.b31-sdrw>small{grid-column:1 / -1}
.b31-sdm{font-weight:600;font-size:12.5px;white-space:nowrap}.b31-sdfoot{flex-wrap:wrap;gap:8px}.b31-etr{background:var(--b21-kobg)}
.b31-sdsum .b31-rr{display:flex;justify-content:space-between;gap:10px;padding:5px 0;border-bottom:1px solid var(--b21-line2);font-size:13px}.b31-sdsum .b31-ttc{font-weight:700;color:var(--b21-or-p)}.b31-kko b,.b31-rr.b31-kko b{color:var(--red,#A63D32)}
.b31-evl>li{list-style:none;margin-left:-18px;border-bottom:1px solid var(--b21-line2);padding:4px 0}.b31-evl summary{cursor:pointer}.b31-evl small{display:block}
@container b31 (max-width:560px){.b31-sdrw{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.b31-sdrw .b31-sdd{grid-column:1 / -1}}
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
  .b31-tab td.b31-q,.b31-tab td.b31-u{text-align:left}.b31-tab td.b31-a{grid-column:1 / -1;text-align:left}.b31-tab .b31-acts{justify-content:flex-start}
  .b31-tab tr.b31-sec,.b31-tab tr.b31-sdr{display:block}.b31-tab tr.b31-sec th{display:block}.b31-tab tr.b31-sdr td:first-child{display:none}.b31-tab tr.b31-sdr td{padding:8px 12px}
  .b31-sc{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.b31-sc>span{grid-column:1 / -1}
  .b31-ba{width:100%}.b31-ba .b31-btn{flex:1 1 140px}.b31-h1{font-size:24px}}
@media (max-width:640px){.b31-full .mpn-dnav{flex-direction:column;align-items:stretch}.b31-full .mpn-dnav ul{max-width:100%}}`;
function b31Css(){if(document.getElementById("b31-css"))return;const s=document.createElement("style");s.id="b31-css";s.textContent=B31_CSS;document.head.appendChild(s);}
