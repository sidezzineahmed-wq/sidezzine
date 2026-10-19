/* ===================== mpv-5 · B1.1 Veille : fiche complète (résumé + sections repliables) =====================
   Données : catalogue (champs de fiche) et « pmmp_enrichi.complements_fiche » de catalogue_details.json (lecteur de fiche v3 :
   retrait, prix des plans, prospectus / échantillons, contact administratif publié, pièces publiées), statut PAR BLOC :
   lu / non publié / pas encore lu (jamais confondus). Jointure seulement si la référence lue = référence du catalogue.
   Prospectus / échantillons : date et texte publiés, distincts de la date limite de remise des plis. TPE / PME : champ officiel
   tel que publié (rien n'est déduit de l'objet). Pièces : lien vers la page publique PMMP du MÊME identifiant ; aucun fichier
   n'est joint dans EAIOS. Codes et provenance dans « Source de la fiche ». Aucune écriture. */
MPV.v="mpv-5";
const MPV5_PORTAIL="https://www.marchespublics.gov.ma/";
function mpvCf(x){const C=S.enr&&S.enr.complements_fiche,r=C&&(C.par_id||{})["pmmp:"+x.o+":"+x.r];return r&&mpvNref(r.ref)===mpvNref(x.ref)?r:null;}
function mpvCfSt(x,b){const r=mpvCf(x);return r&&r.statuts?r.statuts[b]||"non_lu":"non_lu";}
const mpvNL=t=>`<span class="mpv-mut">${esc(t)}</span>`;
function mpvBloc(x,b,val,vide){const st=mpvCfSt(x,b);
  if(st==="non_publie")return{st,h:mpvNL("Non publié sur la fiche PMMP")};
  if(st!=="lu")return{st,h:mpvNL(x.det?"Pas encore lu (relecture de la fiche par le collecteur à venir)":"Fiche pas encore lue")};
  return{st,h:val!=null&&val!==""?val:mpvNL(vide||"Non indiqué sur PMMP (« - »)")};}
/* champ du catalogue (fiche lue) : null = non indiqué ; fiche non lue = inconnu */
const mpvFc=(x,v,vide)=>!x.det?mpvNL("Fiche pas encore lue"):v!=null&&v!==""?v:mpvNL(vide||"Non indiqué sur PMMP (« - »)");
const mpvParLot=x=>mpvAlloti(x)?"Par lot : voir le détail des lots":null;
/* liens officiels seulement : https://www.marchespublics.gov.ma/index.php, page publique de la liste blanche, MÊME
   refConsultation / orgAcronyme ; sinon (javascript:, autre hôte, autre page, autre ID, espace soumissionnaire) : fiche PMMP */
const MPV5_PAGES=new Set(["entreprise.EntrepriseDemandeTelechargementDce","entreprise.EntrepriseDetailsConsultation"]);
function mpvDocUrl(x,u){
  try{const U=new URL(String(u||""),MPV5_PORTAIL);
    if(U.protocol==="https:"&&U.host==="www.marchespublics.gov.ma"&&U.pathname==="/index.php"&&!U.username&&!U.password&&!U.hash&&MPV5_PAGES.has(U.searchParams.get("page"))&&
       U.searchParams.get("refConsultation")===String(x.r)&&U.searchParams.get("orgAcronyme")===String(x.o)&&[...U.searchParams.keys()].every(k=>["page","refConsultation","orgAcronyme"].includes(k)))return U.href;}catch(e){}
  return pmmpUrl(x);}
const mpvMail=e=>/^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}$/.test(String(e||""));
const MPV5_DOC={dce:"Dossier de consultation (DCE)",reglement:"Règlement de consultation",complement:"Complément",avis:"Avis publié"};
function mpvSec(id,title,state,body){return`<details class="mpv-fs" data-mpv-fs="${id}"${(MPV.fsOpen||{})[id]?" open":""}><summary>${mpvI("chev","mpv-car")}<b>${esc(title)}</b>${state?`<small>${state}</small>`:""}</summary><div>${body}</div></details>`;}
const mpvKv=rows=>`<dl class="mpv-kv mpv-kv5">${rows.filter(Boolean).map(([k,v,a])=>`<dt>${esc(k)}</dt><dd${a||""}>${v}</dd>`).join("")}</dl>`;
function mpvFiche5(x,D){const r=mpvCf(x),al=mpvAlloti(x),pl=mpvParLot(x);
  /* Conditions */
  const tp=!x.det?mpvNL("Fiche pas encore lue"):x.tp===true?"Oui":x.tp===false?`Non <small class="mpv-mut">champ officiel PMMP (l'objet est affiché tel que publié)</small>`:mpvNL(pl||"Non indiqué sur PMMP");
  const dom=x.det?((x.dom||[]).length?`<ul class="mpv-l5">${x.dom.map(d=>`<li>${esc(d)}</li>`).join("")}</ul>`:mpvNL("Non indiqué sur PMMP")):mpvNL("Fiche pas encore lue");
  const ech=(()=>{const st=mpvCfSt(x,"echantillons");
    if(st==="lu"&&(r.ech_date||r.ech_txt))return`${r.ech_date?`<b data-mpv-echd="${esc(r.ech_date)}">Date limite des prospectus / échantillons : ${esc(fmtIso(r.ech_date.slice(0,10)))} à ${esc(r.ech_date.slice(11,16))}</b>`:""}${r.ech_txt?`<span class="mpv-src5" data-mpv-echt="1">Texte publié : « ${esc(r.ech_txt)} »</span>`:""}<small class="mpv-mut">Distinct de la date limite de remise des plis (${esc(D.d)}).</small>`;
    if(st==="lu")return mpvNL(pl||"Non indiqué sur PMMP (« - »)");
    if(x.det&&x.proto)return`${esc(x.proto)} <small class="mpv-mut">texte publié (lecture précédente du collecteur)</small>`;
    return mpvBloc(x,"echantillons",null).h;})();
  const pp=mpvBloc(x,"prix_plans",r&&r.prix_plans!=null?(r.prix_plans===0?"0,00 DH (publié sur PMMP)":esc(dh(r.prix_plans))):null).h;
  const cond=mpvKv([["Catégorie",x.cat?esc(x.cat):mpvNL("Non indiquée")],["Réservé TPE / PME",tp,` data-mpv-tp5="${x.tp==null?"":x.tp}"`],["Domaines d'activité",dom],
    ["Agréments",mpvFc(x,x.ag?esc(x.ag):null,pl||undefined)],["Réunion",mpvFc(x,x.reu?esc(x.reu):null,pl||undefined)],
    ["Prospectus, notices, échantillons",ech,` data-mpv-ech="${mpvCfSt(x,"echantillons")}"`],["Variante",!x.det?mpvNL("Fiche pas encore lue"):x.var===true?"Oui":x.var===false?"Non":mpvNL(pl||"Non indiqué sur PMMP")],["Prix d'acquisition des plans",pp]]);
  /* Dépôt et ouverture */
  const dep=mpvKv([["Date limite de remise des plis",`${esc(D.d)}`],["Retrait du dossier",mpvBloc(x,"retrait",r&&r.ret?esc(r.ret):null).h,` data-mpv-ret="${mpvCfSt(x,"retrait")}"`],
    ["Dépôt des offres",mpvFc(x,x.dep?esc(x.dep):null)],["Ouverture des plis",mpvFc(x,x.ouv?esc(x.ouv):null)]]);
  /* Documents publiés */
  const dst=mpvCfSt(x,"docs"),docs=dst==="lu"?((r.docs||[]).length?`<ul class="mpv-l5 mpv-docs">${r.docs.map(d=>`<li data-mpv-doc="${esc(d.type)}"><span>${esc(MPV5_DOC[d.type]||d.libelle||"Document")}${d.taille?` <small class="mpv-mut">${esc(d.taille)}</small>`:""}</span><a class="mpv-lk" href="${esc(mpvDocUrl(x,d.url))}" target="_blank" rel="noopener">Ouvrir sur PMMP${mpvI("ext","mpv-ie")}<span class="mpv-sr"> (nouvel onglet)</span></a></li>`).join("")}</ul><p class="mpv-mut">Liens vers le portail PMMP pour cette consultation : le document n'est pas joint dans EAIOS ; le téléchargement se fait sur PMMP.</p>`:mpvNL("Aucune pièce publiée sur la fiche PMMP"))
    :mpvBloc(x,"docs",null).h+`<p class="mpv-mut">Les pièces publiées se consultent sur la <a class="mpv-lk" data-mpv-docpmmp="1" href="${esc(pmmpUrl(x))}" target="_blank" rel="noopener">fiche PMMP de la consultation${mpvI("ext","mpv-ie")}<span class="mpv-sr"> (nouvel onglet)</span></a>.</p>`;
  /* Contact administratif publié */
  const cst=mpvCfSt(x,"contact"),c=r&&r.contact;
  const ct=cst==="lu"&&c?(c.nom||c.email||c.tel||c.fax?mpvKv([["Nom / service",c.nom?esc(c.nom):mpvNL("Non indiqué")],["E-mail",c.email?(mpvMail(c.email)?`<a class="mpv-lk" href="mailto:${esc(c.email)}">${esc(c.email)}</a>`:esc(c.email)):mpvNL("Non indiqué")],["Téléphone",c.tel?esc(c.tel):mpvNL("Non indiqué")],["Télécopieur",c.fax?esc(c.fax):mpvNL("Non indiqué")]])+`<p class="mpv-mut" data-mpv-csrc="${(r.sources_blocs||{}).contact==="etat_de_page"?"etat_de_page":"page"}">Coordonnées professionnelles publiées dans le bloc administratif de la fiche PMMP${(r.sources_blocs||{}).contact==="etat_de_page"?`, relevées dans la page de la fiche reçue le ${esc(mpvDt(r.lu_le))} (état de page de cette lecture)`:` (lue le ${esc(mpvDt(r.lu_le))})`}.</p>`:mpvNL("Bloc publié sans coordonnées (« - »)"))
    :mpvBloc(x,"contact",null).h;
  /* Source et provenance */
  const pc=S.enr&&x.proc&&((S.enr.procedures||{}).codes||{})[x.proc];
  const src=mpvKv([["Type d'annonce",r&&r.type_annonce?esc(r.type_annonce):mpvNL("Non lu")],["Identifiant PMMP",`${esc(x.o)} / ${esc(x.r)}`],
    pc?["Code procédure PMMP",`${esc(pc)} <small class="mpv-mut">(liste « Mode de passation » du formulaire PMMP, dont les valeurs sont les procédures)</small>`,` data-mpv-pcode="${esc(pc)}"`]:null,
    ["Lecture des compléments",r?`fiche PMMP lue le ${esc(mpvDt(r.lu_le))}${r.reanalyse_le?` · ré-analysée hors ligne le ${esc(mpvDt(r.reanalyse_le))} (lecteur v${esc(String(r.version_parseur||"?"))}, même page lue)`:""}`:mpvNL("Compléments de fiche pas encore lus"),` data-mpv-cflu="${r?esc(r.lu_le):""}"`],
    ["Fiche PMMP",`<a class="mpv-lk" href="${esc(pmmpUrl(x))}" target="_blank" rel="noopener">Voir sur PMMP${mpvI("ext","mpv-ie")}<span class="mpv-sr"> (nouvel onglet)</span></a>`]]);
  const n=(t,st)=>st==="lu"?"":st==="non_publie"?"non publié":"pas encore lu";
  return`<div class="mpv-fiche5" data-mpv-fiche5="${r?"cf":"base"}">`+mpvSec("cond","Conditions de participation","",cond)+mpvSec("dep","Retrait, dépôt et ouverture","",dep)+
    mpvSec("docs","Documents publiés sur PMMP",dst==="lu"?((r.docs||[]).length+" pièce"+((r.docs||[]).length>1?"s":"")):n("",dst),`<div data-mpv-docs="${dst}">${docs}</div>`)+
    mpvSec("contact","Contact administratif",n("",cst),`<div data-mpv-contact="${cst}">${ct}</div>`)+mpvSec("src","Source de la fiche","",src)+`</div>`;}
document.getElementById("view").addEventListener("toggle",e=>{const t=e.target;if(t&&t.dataset&&t.dataset.mpvFs){MPV.fsOpen=MPV.fsOpen||{};MPV.fsOpen[t.dataset.mpvFs]=t.open;}},true);
const _mpvPanel5=mpvPanel;
mpvPanel=function(B,dm,inList){let h=_mpvPanel5(B,dm,inList);const e=MPV.sel&&B&&B.by.get(MPV.sel);if(!e)return h;const x=e.x;
  h=h.replace(/<dt>Code procédure PMMP<\/dt><dd data-mpv-pcode="[^"]*">[\s\S]*?<\/dd>/,"");  /* code interne : dans « Source de la fiche » */
  const f=mpvFiche5(x,mpvDate(x));
  return h.replace(/(<\/dl>)/,"$1"+f);};
const MPV5_CSS=`.mpv-fiche5{margin:10px 0 4px;display:grid;gap:6px}.mpv-fs{border:1px solid var(--mpv-line,#d8dde6);border-radius:8px;background:var(--surface,transparent)}.mpv-fs>summary{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:9px 10px;cursor:pointer;list-style:none;min-height:44px;box-sizing:border-box}.mpv-fs>summary::-webkit-details-marker{display:none}.mpv-fs>summary small{color:var(--mpv-mut);font-size:12px;margin-left:auto}.mpv-fs[open]>summary .mpv-car{transform:rotate(90deg)}.mpv-fs>div{padding:0 10px 10px}.mpv-fs .mpv-kv{margin-top:0}.mpv-l5{margin:0;padding-left:18px}.mpv-docs{list-style:none;padding:0;display:grid;gap:6px}.mpv-docs li{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;justify-content:space-between}.mpv-src5{display:block;margin-top:4px;font-size:13px}.mpv-kv5 dd>b{display:block;font-weight:600}.mpv-kv5 dd small.mpv-mut{display:block}
@media (max-width:640px){.mpv-pan .mpv-kv,.mpv-lot .mpv-kv{grid-template-columns:minmax(0,1fr)!important;gap:0}.mpv-pan .mpv-kv dt{font-weight:600;color:var(--mpv-mut);margin-top:8px;font-size:12.5px}.mpv-pan .mpv-kv dt:first-child{margin-top:0}.mpv-pan .mpv-kv dd{margin:1px 0 0}}`;
const _mpvPage5=mpvPage;
mpvPage=function(){if(!document.getElementById("mpv5-css")){const s=document.createElement("style");s.id="mpv5-css";s.textContent=MPV5_CSS;document.head.appendChild(s);}return _mpvPage5();};
