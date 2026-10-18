/* ===================== mpv-3 · B1.1 Veille : Mode de passation + classification PMMP Etat / CL / EEP =====================
   Données : clé « pmmp_enrichi » de catalogue_details.json, produite à chaque passage horaire par l'ingestion du collecteur
   (ingestion/enrichi_pmmp.py) ; même garde de cohérence que les autres fichiers (catalogue_sha256).
   - Classification : classification PMMP de l'ENTITÉ PUBLIQUE (liste officielle « Etat/CL/EEP » du formulaire de recherche,
     relevée par entité ; contrôlée par la recherche filtrée). Une annonce hérite de son entité (orgAcronyme) ; entité absente = inconnue.
   - Mode de passation : élément modePassation de la fiche PMMP (« Sur offre de prix », « Au rabais / majoration »…), lu et daté
     par annonce ; distinct de la procédure ; jointure seulement si la référence lue = référence du catalogue ; sinon inconnu.
   Même moteur que les autres facettes (mpvMatch) : ET entre critères, OU dans un critère, inconnus exclus sauf
   « Inclure aussi les fiches non renseignées ». Aucune écriture. */
MPV.v="mpv-3";S.enr=null;S.enrState="chargement";
Object.assign(VF0,{tach:[],mpass:[]});MPV_IG.push("tach","mpass");
["tach","mpass"].forEach(k=>{if(!Array.isArray(S.vf[k]))S.vf[k]=[];});S.vf.inc=(S.vf.inc||[]).filter(k=>MPV_IG.includes(k));
function mpvEnrLire(){const d=S.catDetails&&S.catDetails.pmmp_enrichi;S.enr=d&&d.classification&&d.mode_passation&&d.procedures?d:null;S.enrState=S.enr?"ok":S.catState==="ok"?"absent":"chargement";}
const _catAppliquer3=catAppliquer;catAppliquer=function(L){_catAppliquer3(L);mpvEnrLire();softRender();};mpvEnrLire();
const mpvNref=s=>String(s||"").replace(/\s+/g," ").trim().toUpperCase();
function mpvTachE(x){const e=S.enr&&S.enr.classification.par_entite[x.o];return e&&e.code?e:null;}
const mpvTach=x=>{const e=mpvTachE(x);return e?e.code:null;};
function mpvMp(x){const r=S.enr&&S.enr.mode_passation.par_id["pmmp:"+x.o+":"+x.r];return r&&r.v&&mpvNref(r.ref)===mpvNref(x.ref)?r:null;}
function mpvMpSt(x){const M=S.enr&&S.enr.mode_passation,k="pmmp:"+x.o+":"+x.r;if(!M)return"";const a=(M.absents||{})[k];if(a&&mpvNref(a.ref)===mpvNref(x.ref))return"absent";if((M.inaccessibles||{})[k])return"inaccessible";return"non_lu";}
function mpvMpTxt(x){const M=S.enr.mode_passation,k="pmmp:"+x.o+":"+x.r,st=mpvMpSt(x);if(st==="absent")return"Non renseigné : champ vide sur la fiche PMMP (lue le "+mpvDt(M.absents[k].lu_le)+")";if(st==="inaccessible"){const i=M.inaccessibles[k];return"Non renseigné : fiche PMMP inaccessible après "+(i.tentatives||"?")+" essais"+(i.dernier_echec?" (dernier le "+mpvDt(i.dernier_echec)+")":"");}return"Non renseigné : fiche PMMP pas encore lue (ou référence modifiée depuis la lecture)";}
function mpvCovTxt(c){const n=v=>v==null?"?":v;return`Connu pour ${c.connues} consultations sur ${c.annonces} (${c.pct} %), chacune avec sa date de lecture`+(c.champ_absent!=null?` ; fiche lue sans mode : ${n(c.champ_absent)} ; fiche inaccessible : ${n(c.inaccessibles)} ; pas encore lue : ${n(c.non_lues)}`:" ; les autres : fiche non lue")+". Aucune valeur n'est déduite.";}
const MPV_TACH=[["1","Etat"],["2","Collectivité locale"],["3","Etablissement public"]];
FACETS.tach=(x,f)=>!(f.tach||[]).length||!S.enr||f.tach.includes(mpvTach(x));
FACETS.mpass=(x,f)=>{if(!(f.mpass||[]).length||!S.enr)return true;const m=mpvMp(x);return!!m&&f.mpass.includes(m.v);};
Object.assign(MPV_G,{tach:"tach",mpass:"mpass"});
Object.assign(MPV_UNK,{tach:x=>mpvTach(x)==null,mpass:x=>!mpvMp(x)});
Object.assign(MPV_ON,{tach:d=>!!(S.enr&&(d.tach||[]).length),mpass:d=>!!(S.enr&&(d.mpass||[]).length)});
/* puces */
const _mpvActive2=mpvActive;
mpvActive=function(d){const o=_mpvActive2(d).filter(([k])=>k!=="inc:tach"&&k!=="inc:mpass"),off=S.enr?"":" (non appliqué : données indisponibles)";
  (d.tach||[]).forEach(c=>o.push(["tach:"+c,"Classification PMMP : "+((MPV_TACH.find(z=>z[0]===c)||[,c])[1])+off]));
  (d.mpass||[]).forEach(v=>o.push(["mpass:"+v,"Mode de passation : "+v+off]));
  (d.inc||[]).forEach(g=>{if(g==="tach")o.push(["inc:tach","+ fiches non renseignées : classification"]);if(g==="mpass")o.push(["inc:mpass","+ fiches non renseignées : mode de passation"]);});
  return o;};
/* tiroir : Acheteur & procédure */
function mpvDt(s){if(!s)return"date inconnue";const P=casaParts(new Date(s));return P.day+"/"+P.month+"/"+P.year+" à "+P.hour+"h"+P.minute;}
function mpvEnrBlocs(B){const d=MPV.dr,E=S.enr;
  if(!E)return`<div class="mpv-dis" data-mpv-dis="enr"><b>Mode de passation · Classification Etat / CL / EEP</b><span>${S.enrState==="chargement"?"Chargement des données PMMP…":"Données PMMP d'enrichissement indisponibles dans cette version : filtres désactivés (rien n'est déduit)."}</span></div>`;
  const bt=mpvBaseFor(B,d,"tach"),ct=mpvCnt(bt,x=>{const c=mpvTach(x);return c?[c]:[];}),bm=mpvBaseFor(B,d,"mpass"),cm=mpvCnt(bm,x=>{const m=mpvMp(x);return m?[m.v]:[];});
  const vals=[...new Set([...Object.keys(E.mode_passation.couverture.valeurs||{}),...cm.keys()])].sort((a,b)=>(cm.get(b)||0)-(cm.get(a)||0)||a.localeCompare(b));
  const C=E.classification,M=E.mode_passation,src=C.source||{};
  return`<div class="mpv-two mpv-enr" data-mpv-enr="1"><div><h4>Mode de passation <span class="mpv-tag">Fiche PMMP</span></h4><div class="mpv-ol">${vals.map(v=>mpvOpt("mpass",v,v,cm.get(v)||0,(d.mpass||[]).includes(v))).join("")}</div>${mpvInc("mpass",bm,"mpass","mode de passation")}
     <p class="mpv-mut">Champ de la fiche PMMP affiché après la procédure (ex. « Appel d'offres ouvert | Sur offre de prix ») ; distinct de la procédure. ${mpvCovTxt(M.couverture)}</p></div>
   <div><h4>Classification Etat / CL / EEP <span class="mpv-tag">Liste officielle PMMP</span></h4><div class="mpv-ol">${MPV_TACH.map(([c,l])=>mpvOpt("tach",c,l,ct.get(c)||0,(d.tach||[]).includes(c))).join("")}</div>${mpvInc("tach",bt,"tach","classification")}
     <p class="mpv-mut">Classification PMMP de l'entité publique de rattachement (liste « Etat/CL/EEP » du portail, relevée le ${esc(mpvDt(src.fin))}) ; une annonce hérite de son entité. Ex. : les acheteurs rattachés au Ministère de l'Intérieur sont « Etat » selon PMMP. Rien n'est déduit du nom de l'acheteur.</p></div></div>`;}
const _mpvDrawer2=mpvDrawer;
mpvDrawer=function(B){let h=_mpvDrawer2(B);
  h=h.replace(/<div class="mpv-dis" data-mpv-dis="mode">[\s\S]*?<\/div>\s*<div class="mpv-dis" data-mpv-dis="type">[\s\S]*?<\/div>/,()=>mpvEnrBlocs(B));
  const E=S.enr;if(E){const M=E.mode_passation.couverture,C=E.classification.couverture;
    h=h.replace(/<li><b>Mode de passation<\/b>[\s\S]*?<\/li><li><b>Type d'acheteur<\/b>[\s\S]*?<\/li>/,"");
    h=h.replace(/(<section id="mpv-s-dispo"[\s\S]*?<ul class="mpv-dl2">)/,`$1<li data-mpv-cov="mpass"><b>Mode de passation</b> : ${mpvCovTxt(M)}</li><li data-mpv-cov="tach"><b>Classification Etat / CL / EEP</b> : ${C.annonces-(C.par_code.inconnu||0)} / ${C.annonces} consultations (entités publiques classées par la liste officielle${C.entites_inconnues.length?` ; ${C.entites_inconnues.length} entité(s) inconnue(s)`:""}).</li>`);
  }else h=h.replace(/<li><b>Mode de passation<\/b>[\s\S]*?<\/li>/,`<li><b>Mode de passation</b> et <b>classification Etat / CL / EEP</b> : données d'enrichissement indisponibles dans cette version.</li>`).replace(/<li><b>Type d'acheteur<\/b>[\s\S]*?<\/li>/,"");
  h=h.replace("<h4>Procédure</h4>",`<h4>Procédure <small class="mpv-mut">(liste « Mode de passation » de la recherche PMMP)</small></h4>`);
  return h;};
/* fiche : mode et classification, distincts de la procédure, avec provenance */
const _mpvPanel2=mpvPanel;
mpvPanel=function(B,dm,inList){let h=_mpvPanel2(B,dm,inList);const e=MPV.sel&&B&&B.by.get(MPV.sel);if(!e)return h;const x=e.x,E=S.enr;
  const m=E&&mpvMp(x),t=E&&mpvTachE(x),pc=E&&x.proc&&(E.procedures.codes||{})[x.proc];
  const rows=(pc?`<dt>Code procédure PMMP</dt><dd data-mpv-pcode="${esc(pc)}">${esc(pc)} <small class="mpv-mut">(liste « Mode de passation » du formulaire PMMP, dont les valeurs sont les procédures)</small></dd>`:"")+
    `<dt>Mode de passation <small class="mpv-mut">(fiche PMMP)</small></dt><dd data-mpv-mp="${m?esc(m.v):""}" data-mpv-mpst="${m?"lu":mpvMpSt(x)}">${m?`${esc(m.v)} <small class="mpv-mut">fiche PMMP lue le ${esc(mpvDt(m.lu_le))}${m.source==="complement_eaios"?" (complément EAIOS)":" (collecteur)"}</small>`:`<span class="mpv-mut">${E?mpvMpTxt(x):"Données indisponibles"}</span>`}</dd>`+
    `<dt>Classification de l'entité</dt><dd data-mpv-tach="${t?esc(t.code):""}">${t?`${esc(t.libelle)} <small class="mpv-mut">classification PMMP de l'entité publique « ${esc(t.entite||x.ent||x.o)} », relevée le ${esc(mpvDt(E.classification.source.fin))}</small>`:`<span class="mpv-mut">${E?"Inconnue (entité absente de la liste officielle relevée)":"Données indisponibles"}</span>`}</dd>`;
  return h.replace(/(<dl class="mpv-kv">[\s\S]*?)<\/dl>/,(z,a)=>a+rows+"</dl>");};
const MPV3_CSS=`.mpv-enr{margin-top:12px}.mpv-enr .mpv-mut{font-size:12.5px;margin:6px 0 0}.mpv-kv dd small.mpv-mut{display:block;font-size:12px}`;
const _mpvPage2=mpvPage;
mpvPage=function(){if(!document.getElementById("mpv3-css")){const s=document.createElement("style");s.id="mpv3-css";s.textContent=MPV3_CSS;document.head.appendChild(s);}return _mpvPage2();};
