/* ===================== mpv-7 · « DCE à récupérer » branché sur la FILE DCE réelle (dce_demande + tâche DCE existante) =====================
   Pas de nouveau service : la file durable est la collection dce_demande (un document par dossier de la consultation), traitée
   par la tâche existante « EAIOS DCE » (kit_dce : FIFO par date de demande, priorité « immédiat », une seule demande active par
   consultation organisme+numéro, bail épinglé contre les passages concurrents, CG validées par un humain, archive vérifiée puis
   rangée dans le Drive privé et relue avant « prêt »).
   - « Mettre en file » : écrit la demande (FIFO), la tâche la prend à son prochain passage horaire.
   - « Récupérer maintenant » : même demande marquée immédiate + réveil de la tâche tout de suite (fire_trigger, connecteur
     Claude Code Remote déjà déclaré par EAIOS) ; l'onglet peut être fermé, l'état vient de la base (live dce_demande).
   - États : À demander · En attente (position réelle dans la file) · Récupération en cours · Intervention requise (CG à accepter,
     CAPTCHA, formulaire non reconnu…) · Reçu (fichiers réellement rangés et vérifiés) · Échec (cause).
   - Aucune société : la tâche saisit l'identité de l'exploitant EAIOS exigée par le formulaire PMMP, jamais une société.
   - Aucun ajout manuel ni dépôt de ZIP dans cette vue ; anciens fichiers et anciennes demandes conservés (historique). */
MPV.v="mpv-7";
const MPV7={msg:{}};
const MPV7_INTERV=["controle","cg_modifiees","validation","formulaire"];
const MPV7_LIBERR={controle:"le portail demande une vérification humaine (page de contrôle ou CAPTCHA)",cg_modifiees:"les conditions générales ont changé : nouvelle acceptation requise",
  validation:"acceptation des conditions absente ou expirée",formulaire:"formulaire du portail non reconnu de façon sûre",association:"page ou référence inattendue sur le portail : rien n'a été téléchargé",
  reseau:"aucune réponse du portail",delai_telechargement:"le téléchargement n'a pas abouti à temps",telechargement:"transfert interrompu",stockage:"archive non rangée (stockage)",
  interrompu:"passage interrompu",cg_extraction:"conditions générales illisibles de façon sûre",cg_algo:"conditions lues avec une ancienne méthode : nouvelle demande requise",confiance:"connexion sécurisée non vérifiée : arrêt"};
function mpv7Dem(ids){let b=null;(ids||[]).forEach(id=>{const D=(S.dceDem||{})[id];if(D&&(!b||String(D.demande_le||"")>String(b.D.demande_le||"")))b={id,D};});return b;}
function mpv7Recu(D){const r=D&&D.etat==="pret"&&D.resultat;if(!r)return false;if(r.stockage==="drive")return!!(r.verifie_le&&+r.fichiers>0&&r.zip_sha256);return r.deja_importe===true||(Array.isArray(r.cles)&&r.cles.length>0);}
/* état DCE d'une consultation : fichiers réellement joints au dossier, sinon la demande de la file ; une ancienne « demande interne » sans tâche n'est pas une file */
{const _mpvDce7=mpvDce;mpvDce=function(ids){const b=_mpvDce7(ids);if(b.k==="pret"||b.k==="partiel")return b;const Q=mpv7Dem(ids);
  if(Q){const D=Q.D,e=D.etat,o={id:Q.id,E:b.E,D};
    if(e==="demandee"||e==="cg_validees")return{...o,k:"file",t:e==="demandee"&&D.immediat?"Démarrage demandé":"En attente",c:"or"};
    if(e==="ouverture"||e==="telechargement")return{...o,k:"cours",t:"Récupération en cours",c:"bl"};
    if(e==="attente_validation_CG")return{...o,k:"interv",t:"Intervention requise",c:"ro"};
    if(e==="pret"&&mpv7Recu(D))return{...o,k:"pret",t:"Reçu",c:"bl"};
    if(e==="echec"){const iv=MPV7_INTERV.includes((D.erreur||{}).code);return{...o,k:iv?"interv":"echec",t:iv?"Intervention requise":"Échec",c:"ro"};}}
  if(b.k==="encours"&&!(b.E&&b.E.run))return{...b,k:"afaire",t:"À demander",c:"or",ancien:true};
  if(b.k==="echec")return{...b,t:"Échec",c:"ro"};
  if(b.k==="afaire"||b.k==="nd")return{...b,k:"afaire",t:"À demander",c:"or"};
  return b;};}
Object.assign(MPV6_DF,{afaire:"afaire",echec:"afaire",nd:"afaire",file:"dem",cours:"dem",interv:"dem",encours:"afaire",envoi:"dem",pret:"recu",partiel:"recu"});
const MPV7_CAT={afaire:"sans",echec:"sans",file:"attente",cours:"cours",interv:"cours"};
/* file réelle : ordre de traitement de la tâche (immédiates d'abord, puis date de demande), dossiers autorisés seulement */
function mpv7File(){const c=dceFileConf(),A=new Set((c&&c.dossiers)||[]);
  return Object.entries(S.dceDem||{}).filter(([id,D])=>D&&A.has(id)&&(D.etat==="demandee"||D.etat==="cg_validees"))
    .sort((x,y)=>((x[1].immediat?0:1)-(y[1].immediat?0:1))||String(x[1].demande_le||"").localeCompare(String(y[1].demande_le||""))||x[0].localeCompare(y[0])).map(([id])=>id);}
function mpv7H(s){const d=s?new Date(s):null;if(!d||isNaN(d))return"date inconnue";const P=casaParts(d);return P.day+"/"+P.month+" à "+P.hour+":"+P.minute;}
function mpv7Qui(p){return p&&S.role&&p===S.role.me?"vous":p?"un membre de l'équipe":"inconnu";}
/* ---- actions réelles ---- */
async function mpv7Enfiler(g,imm){const id=g.id,a=S.ao[id],U=a&&dcePmmpUrl(a);if(!a||!editable())return toast(RO_MSG);
  if(!S.db||!U)return toast("File DCE indisponible : dossier sans lien PMMP ou base absente.");if(imm&&!S.mcp)return toast("Démarrage immédiat indisponible dans cette vue (connecteur Claude Code Remote).");
  const c=dceFileConf();if(!c)return toast("File DCE inactive (configuration dce/config).");
  MPV.conf=null;if((MPV7.msg[id]||{}).st==="envoi")return;MPV7.msg[id]={st:"envoi",imm};render();
  const now=new Date().toISOString().replace(/\.\d+Z$/,"Z");
  try{
    /* relire la demande dans la base juste avant d'écrire : jamais deux demandes actives, jamais écraser un travail en cours */
    const g0=await S.db.doc("dce_demande/"+id).get(),D=g0&&g0.exists?g0.data():null;
    if(D&&["ouverture","telechargement","attente_validation_CG"].includes(D.etat)){MPV7.msg[id]={st:"err",msg:"une récupération est déjà en cours pour ce dossier"};render();return;}
    const autre=mpv7Dem(g.ids.filter(x=>x!==id));if(autre&&["demandee","cg_validees","ouverture","telechargement","attente_validation_CG"].includes(autre.D.etat)){MPV7.msg[id]={st:"err",msg:"cette consultation a déjà une demande active (autre dossier)"};render();return;}
    if(!c.dossiers.includes(id))await S.db.doc("dce/config").update({file:{dossiers:[...c.dossiers,id]}});   /* autorisation explicite (confirmée) de ce dossier pour la tâche */
    if(D&&(D.etat==="demandee"||D.etat==="cg_validees")){if(imm&&!D.immediat)await S.db.doc("dce_demande/"+id).update({immediat:true,maj:now});}
    else{const hist=[...(Array.isArray(D&&D.historique)?D.historique:[]),...(D?[{etat:D.etat,demande_le:D.demande_le||null,maj:D.maj||null,erreur:D.erreur||null,resultat:D.resultat||null}]:[])].slice(-20);
      await S.db.doc("dce_demande/"+id).set({ao_id:id,ref:String(a.portail.ref),org:String(a.portail.org),reference_attendue:String(a.ref||""),etat:"demandee",immediat:!!imm,
        demande_par:String(S.role.me||""),demande_le:now,maj:now,cg:null,validation:null,tache:null,erreur:null,resultat:null,historique:hist});}
    const g1=await S.db.doc("dce_demande/"+id).get(),D1=g1&&g1.exists?g1.data():null;
    if(!D1||!["demandee","cg_validees"].includes(D1.etat)||(imm&&!D1.immediat)){MPV7.msg[id]={st:"err",msg:"demande non confirmée par la base"};render();return;}
    logJ((a.ref||id)+" : DCE "+(imm?"demandé avec démarrage immédiat":"mis en file")+" (file DCE)");
    let rev="";if(imm){rev=await mpv7Reveil(id);}
    MPV7.msg[id]={st:"ok",imm,rev,le:Date.now()};}
  catch(e){MPV7.msg[id]={st:"err",msg:(e&&(e.code||e.message))||"erreur"};}
  render();}
/* réveil réel de la tâche (fire_trigger) ; résultat écrit dans la demande : visible après rechargement, réessayable */
async function mpv7Reveil(id){const rev=await dceFileReveiller(id),le=new Date().toISOString().replace(/\.\d+Z$/,"Z");
  try{await S.db.doc("dce_demande/"+id).update({reveil:{le,ok:!rev,motif:rev||null}});}catch(e){}return rev;}
async function mpv7Relancer(g){const id=g.id;if(!editable()||!S.mcp)return toast(RO_MSG);if((MPV7.msg[id]||{}).st==="envoi")return;MPV7.msg[id]={st:"envoi",imm:true};render();
  const rev=await mpv7Reveil(id);MPV7.msg[id]={st:"ok",imm:true,rev,le:Date.now()};render();}
function mpv7Lancer(g,imm){const c=dceFileConf();if(c&&!c.dossiers.includes(g.id)){MPV.conf={t:"q7",id:g.id,imm};render();mpdFocus("[data-mpv-confok]");return;}mpv7Enfiler(g,imm);}
/* ---- inventaire PMMP : noms et tailles (non cliquables) ---- */
function mpv7Inv(g){const x=g.x;
  if(!S.cat)return S.catState==="absent"?`<p class="mpv-w" data-mpv6-inv="erreur">Inventaire PMMP indisponible : le catalogue n'a pas pu être chargé. Rouvrez EAIOS pour réessayer.</p>`:`<p class="mpv-mut" data-mpv6-inv="chargement" role="status">Chargement de l'inventaire PMMP…</p>`;
  if(!x)return`<p class="mpv-mut" data-mpv6-inv="inconnu">Inventaire PMMP : inconnu (consultation absente du catalogue de cette version).</p>`;
  if(!S.enr)return S.enrState==="chargement"?`<p class="mpv-mut" data-mpv6-inv="chargement" role="status">Chargement de l'inventaire PMMP…</p>`:`<p class="mpv-mut" data-mpv6-inv="indisponible">Inventaire PMMP indisponible dans cette version (données des fiches non publiées).</p>`;
  const st=mpvCfSt(x,"docs"),r=mpvCf(x);
  if(st!=="lu"||!r)return`<p class="mpv-mut" data-mpv6-inv="inconnu">Inventaire PMMP : inconnu — la liste des pièces publiées n'a pas encore été relevée pour cette consultation.</p>`;
  const D=r.docs||[],lu=r.docs_lu_le?` <small class="mpv-mut">relevé le ${esc(mpvDt(r.docs_lu_le))}</small>`:"";
  if(!D.length)return`<p class="mpv-mut" data-mpv6-inv="vide">Inventaire PMMP : aucune pièce publiée (constaté sur la fiche PMMP).${lu}</p>`;
  return`<div data-mpv6-inv="lu"><p class="mpv-mut">Pièces publiées sur PMMP (${D.length})${lu}</p><ul class="mpv6-inv mpv7-inv">${D.map(d=>`<li data-mpv6-doc="${esc(d.type)}"><span>${mpvI("file")}${esc(MPV5_DOC[d.type]||d.libelle||"Document")}</span>${d.taille?`<small class="mpv-mut">${esc(d.taille)}</small>`:""}</li>`).join("")}</ul></div>`;}
/* ---- suivi serveur de la demande ---- */
function mpv7Suivi(g,dc){const D=dc.D,id=dc.id||g.id,F=mpv7File();
  if(!D){if(dc.ancien){const E=dc.E||{};return`<p class="mpv-mut" data-mpv7-ancien="1">Ancienne demande interne du ${esc(dceQuand(E.dem))} : elle n'est pas dans la file DCE et n'a jamais été traitée.</p>`;}return"";}
  const e=D.etat,pos=F.indexOf(id);let h=`<div class="mpv7-suivi" data-mpv7-etat="${esc(e)}" role="status">`;
  if(e==="demandee"||e==="cg_validees"){const occ=Object.entries(S.dceDem||{}).find(([k,x])=>k!==id&&x&&["ouverture","telechargement"].includes(x.etat)&&x.tache&&new Date(x.tache.jusqu)>new Date()),rv=D.reveil;
    h+=`<p><b>${pos>=0?"Position "+(pos+1)+" sur "+F.length+" dans la file":"En file (hors liste autorisée de la tâche)"}</b>${e==="cg_validees"?" · conditions acceptées, téléchargement au prochain passage de la tâche":""}</p>`;
    if(D.immediat)h+=rv&&rv.ok===false?`<p class="mpv-w" data-mpv7-reveil="echec">Démarrage demandé, mais le réveil de la tâche a échoué le ${esc(mpv7H(rv.le))} (${esc(rv.motif||"erreur")}) : la demande attend le prochain passage horaire.${editable()&&S.mcp?` <button type="button" class="mpv-lk" data-mpv7-relancer="${esc(id)}" data-act="${act(()=>mpv7Relancer({id}))}">Réessayer le démarrage</button>`:""}</p>`
      :rv&&rv.ok?`<p data-mpv7-reveil="ok">Démarrage demandé : tâche réveillée le ${esc(mpv7H(rv.le))}. <b>La récupération n'a pas encore commencé</b> : elle commence quand la tâche prend la demande.</p>`
      :`<p data-mpv7-reveil="inconnu">Démarrage demandé ; réveil de la tâche non confirmé : la demande sera prise au plus tard au prochain passage horaire.</p>`;
    if(occ)h+=`<p class="mpv-mut" data-mpv7-occupee="1">La tâche traite en ce moment une autre demande ; la vôtre suit dans l'ordre de la file.</p>`;
    h+=`<p class="mpv-mut">Demandée le ${esc(mpv7H(D.demande_le))} par ${esc(mpv7Qui(D.demande_par))}. La tâche DCE prend une demande par passage, dans l'ordre de la file, à chaque passage horaire${D.immediat?" et à son réveil":""} ; aucun autre déclenchement n'est nécessaire.</p>`;}
  else if(e==="ouverture"||e==="telechargement")h+=`<p><b>${e==="ouverture"?"La tâche lit la page du DCE sur le portail":"La tâche télécharge et vérifie l'archive"}</b></p><p class="mpv-mut">Prise en charge le ${esc(mpv7H(D.maj))}${D.tache&&D.tache.jusqu?" · limite "+esc(mpv7H(D.tache.jusqu)):""}. Vous pouvez fermer EAIOS : l'état se met à jour depuis la base.</p>`;
  else if(e==="attente_validation_CG"&&D.cg)h+=`<p><b>Intervention requise : acceptez les conditions générales du portail pour ce téléchargement</b></p><blockquote>${esc(D.cg.texte||"")}</blockquote>${dceCgBloc(D.cg)}${editable()?`<button type="button" class="mpv-bp" data-mpv7-valider="${esc(id)}" ${(S.dceFileEnvoi||{})[id]?"disabled":""} data-act="${act(()=>dceFileValider(id))}">${esc(DCE_SRV_PHRASE)}</button>`:""}<p class="mpv-mut">La tâche ne les accepte jamais à votre place ; votre acceptation vaut pour ce seul téléchargement et la réveille aussitôt.</p>`;
  else if(e==="echec"){const er=D.erreur||{},iv=MPV7_INTERV.includes(er.code);h+=`<p><b>${iv?"Intervention requise":"Échec"} : ${esc(MPV7_LIBERR[er.code]||er.motif||"cause non précisée")}</b></p><p class="mpv-mut">${er.motif?esc(er.motif)+" · ":""}le ${esc(mpv7H(er.le||D.maj))}. Rien n'a été modifié dans le dossier ; aucune nouvelle tentative automatique.${iv&&er.code==="controle"?" Prenez la main sur PMMP, puis remettez en file.":""}</p>`;}
  else if(e==="pret"){const r=D.resultat||{};h+=mpv7Recu(D)?`<p><b>Reçu</b> le ${esc(mpv7H(r.verifie_le||r.le))} · ${r.stockage==="drive"?esc(String(r.fichiers))+" fichiers vérifiés (empreintes SHA-256), rangés dans le Drive privé":r.deja_importe?"même contenu déjà rangé, aucun doublon":esc(String((r.cles||[]).length))+" fichiers rangés au dossier"}</p><p class="mpv-mut">Empreinte de l'archive : <code>${esc(String(r.zip_sha256||"").slice(0,16))}…</code></p>`:`<p class="mpv-w">Résultat incomplet : non compté comme reçu.</p>`;}
  else h+=`<p class="mpv-mut">${esc(DCE_FILE_LIB[e]||e)}</p>`;
  return h+`</div>`;}
/* ---- panneau ---- */
mpv6DcePanel=function(g,where){if(!g)return`<aside class="mpv-pan" aria-labelledby="mpv6-dph"><p class="mpv-kick" id="mpv6-dph" tabindex="-1">DCE de la consultation</p><p class="mpv-mut">Sélectionnez une consultation dans la liste.</p></aside>`;
  const D0=mpv6Date(g),dc=g.dce,ed=editable(),a=S.ao[g.id]||g.a,U=dcePmmpUrl(a),F=mpv6Fichiers(g),M=MPV7.msg[g.id]||{},cf=dceFileConf(),st=dc.k;
  let h=`<aside class="mpv-pan" aria-labelledby="mpv6-dph" data-mpv6-dpanel="${esc(g.k)}">${mpv6Back("ds",g.k)}<p class="mpv-kick">DCE de la consultation</p>${where?`<p class="mpv-hl" data-mpv6-hors="${esc(where)}">${esc(where)}</p>`:""}
    <h2 class="mpv-ph" id="mpv6-dph" tabindex="-1">${esc(g.ref)}</h2><p class="mpv-pobj">${esc(g.obj||"Objet non indiqué")}</p><p class="mpv-mut">${esc(g.mo||"Acheteur non indiqué")}</p>
    <dl class="mpv-kv"><dt>Date limite</dt><dd>${esc(D0.d)}${D0.r?`<small class="mpv-rel${D0.u?" u":""}${D0.c?" c":""}">${esc(D0.r)}</small>`:""}</dd><dt>Statut du DCE</dt><dd><span class="mpv-dce mpv-c-${dc.c}" data-mpv6-dst="${esc(st)}">${esc(dc.t)}</span></dd></dl>`;
  h+=mpv7Suivi(g,dc);
  h+=`<h3 class="mpv-h3">Inventaire PMMP</h3>${mpv7Inv(g)}${U?`<a class="mpv-lk" href="${esc(U)}" target="_blank" rel="noopener noreferrer" data-mpv7-pmmp="1">Accéder au DCE sur PMMP${mpvI("ext","mpv-ie")}<span class="mpv-sr"> (nouvel onglet)</span></a>`:`<p class="mpv-mut">Pas de lien PMMP pour ce dossier.</p>`}`;
  if(F.length)h+=`<h3 class="mpv-h3">Fichiers joints au dossier</h3><ul class="mpv6-inv" data-mpv6-joints="${F.length}">${F.slice(0,8).map(n=>`<li><span>${mpvI("file")}${esc(n)}</span></li>`).join("")}${F.length>8?`<li>+ ${F.length-8} autre(s)</li>`:""}</ul>`;
  /* actions : deux boutons toujours visibles, désactivés avec leur raison */
  const actif=["file","cours","interv"].includes(st)&&!(st==="interv"&&dc.D&&dc.D.etat==="echec"),recu=st==="pret"||st==="partiel";
  const pourquoi=!ed?"Lecture seule":!cf?"File DCE inactive":!U?"Dossier sans lien PMMP":!g.ouv?"Consultation clôturée":recu?"DCE déjà reçu":st==="cours"?"Récupération en cours":st==="interv"&&actif?"Intervention requise ci-dessus":"";
  const okQ=!pourquoi&&!actif,okN=!pourquoi&&S.mcp&&(!actif||(st==="file"&&!(dc.D||{}).immediat)),envoi=M.st==="envoi";
  if(MPV.conf&&MPV.conf.t==="q7"&&MPV.conf.id===g.id&&ed)h+=mpvConfirm(`Ce dossier n'est pas encore dans la liste des dossiers autorisés pour la tâche DCE. L'autoriser et ${MPV.conf.imm?"lancer la récupération maintenant":"le mettre en file"} ? La tâche télécharge sur le portail public avec l'identité de l'exploitant EAIOS, jamais au nom d'une société, et s'arrête pour que vous acceptiez les conditions générales.`,"Autoriser et continuer",()=>mpv7Enfiler(g,MPV.conf.imm));
  else h+=`<div class="mpv7-acts"><button type="button" class="mpv-bs2" data-mpv7-file="${esc(g.id)}" ${okQ&&!envoi?"":"disabled"} data-act="${act(()=>mpv7Lancer(g,false))}">Mettre en file</button><button type="button" class="mpv-bp" data-mpv7-now="${esc(g.id)}" ${okN&&!envoi?"":"disabled"} data-act="${act(()=>mpv7Lancer(g,true))}">${mpvI("dl")}Récupérer maintenant</button></div>
    ${pourquoi?`<p class="mpv-mut" data-mpv7-pourquoi="1">${esc(pourquoi)}${st==="file"&&!pourquoi?"":""}.</p>`:st==="file"?`<p class="mpv-mut" data-mpv7-pourquoi="1">Déjà en file${(dc.D||{}).immediat?" avec démarrage immédiat demandé":" : « Récupérer maintenant » la fait passer en tête et réveille la tâche"}.</p>`:!S.mcp?`<p class="mpv-mut" data-mpv7-pourquoi="1">« Récupérer maintenant » indisponible dans cette vue (connecteur Claude Code Remote) : « Mettre en file » reste possible.</p>`:""}`;
  if(envoi)h+=`<p class="mpv-mut" role="status" data-mpv7-msg="envoi">Enregistrement de la demande…</p>`;
  else if(M.st==="ok")h+=`<p class="mpv-ok" role="status" data-mpv7-msg="ok">${M.imm?(M.rev?`Demande enregistrée et confirmée par la base ; réveil de la tâche impossible (${esc(M.rev)}) : réessayable ci-dessus, sinon prochain passage horaire.`:"Demande enregistrée et confirmée par la base ; tâche DCE réveillée : démarrage demandé, en attente de prise en charge."):"Mise en file confirmée par la base : la tâche la prendra à son tour, au plus tard à son prochain passage horaire."}</p>`;
  else if(M.st==="err")h+=`<p class="mpv-w" role="alert" data-mpv7-msg="err">Rien n'a été mis en file (${esc(M.msg||"erreur")}) : l'état affiché est celui de la base.</p>`;
  h+=`<button type="button" class="mpv-lk" data-mpv6-dossier="${esc(g.id)}" data-act="${act(()=>mpvOuvrir(g.id,recu?"dce":null))}">Ouvrir le dossier</button>`;
  h+=`<p class="mpv-note">${mpvI("info")}La tâche DCE télécharge sur le portail public avec l'identité de l'exploitant EAIOS exigée par le formulaire (nom, prénom, e-mail), jamais au nom d'une société ; elle s'arrête pour que vous acceptiez les conditions générales. « Reçu » seulement quand l'archive est vérifiée et rangée.</p>`;
  return h+`</aside>`;};
/* ---- onglet ---- */
mpvDceTab=function(G){if(S.aoState!=="ok")return mpv6Wait();const st=MPV6.ds,O=G.O||[],Ech=G.E||[],cat=g=>MPV7_CAT[g.dce.k]||"sans";
  const C={tout:O.length,sans:O.filter(g=>cat(g)==="sans").length,attente:O.filter(g=>cat(g)==="attente").length,cours:O.filter(g=>cat(g)==="cours").length};
  const FL=[["tout","Tous"],["sans","Sans demande"],["attente","En attente"],["cours","En cours"]];if(!FL.some(([k])=>k===st.f))st.f="tout";
  let list=O.filter(g=>(st.f==="tout"||cat(g)===st.f)&&mpv6Q(g,st.q));if(st.sort==="limd")list=list.slice().reverse();const n=list.length,P=mpv6Pages("ds",n),rows=list.slice(P.i0,P.i0+P.per);
  if(!st.sel||!MPV6.by.get(st.sel))st.sel=rows[0]?rows[0].k:null;const sg=MPV6.by.get(st.sel),inQ=sg&&O.includes(sg),inList=sg&&list.includes(sg);
  const where=!sg||inList?"":inQ?"Hors des résultats affichés : la sélection est conservée.":sg.dce.k==="pret"?"DCE reçu : hors de la file.":Ech.includes(sg)?"Échue ou sans suite : hors compteur.":"Hors de la file.";
  const F=mpv7File();
  let h=`<div class="mpv6" data-mpv6="dce">${typeof mpv6CatNote==="function"?mpv6CatNote():""}<div class="mpv6-cnt" role="group" aria-label="Filtrer">${FL.map(([k,l])=>`<button type="button" class="mpv-chip" aria-pressed="${st.f===k}" data-mpv6-cf="${k}" data-mpv6-cn="${C[k]}" data-act="${act(()=>{st.f=k;st.page=1;render();mpdFocus('[data-mpv6-cf="'+k+'"]');})}">${esc(l)} <b>${C[k]}</b></button>`).join("")}<span class="mpv-mut" data-mpv7-file="${F.length}">File de la tâche DCE : ${F.length} demande${F.length>1?"s":""} en attente</span></div>
    <div class="mpv6-fb">${mpv6Search("ds","Référence, objet ou acheteur")}<label class="mpv6-sel"><span>Trier</span>${mpv6Opt("ds","sort",[["lim","Échéance la plus proche"],["limd","Échéance la plus lointaine"]])}</label></div>`;
  h+=`<div class="mpv-grid" data-mob="${esc(st.mob)}"><section class="mpv-lst" aria-labelledby="mpv6-dlt"><div class="mpv-lh"><h2 id="mpv6-dlt" tabindex="-1" data-mpv6-dn="${O.length}">${O.length} DCE à récupérer <small>consultations suivies ouvertes, DCE non reçu</small></h2><span class="mpv-mut" data-mpv6-rng="${n?P.i0+1:0}-${P.i0+rows.length}/${n}">${n?(P.i0+1)+" – "+(P.i0+rows.length)+" sur "+n:"0 résultat"}</span></div>`;
  h+=n?`<ul class="mpv-rows">${rows.map(g=>mpv6Row("ds",g,g.k===st.sel)).join("")}</ul>`:`<p class="mpv-vide" data-mpv-vide="1">${O.length?"Aucune consultation ne correspond : changez la recherche ou le filtre.":"Aucun DCE à récupérer pour les consultations suivies ouvertes."}</p>`;
  h+=P.h+`<details class="mpv-hs mpv6-ech" data-mpv6-ech="${Ech.length}"${st.ech?" open":""}><summary>Échues ou sans suite, DCE non reçu (${Ech.length}) · hors compteur${mpvI("chev","mpv-car")}</summary><div>${Ech.length?`<ul class="mpv-rows">${Ech.map(g=>mpv6Row("ds",g,g.k===st.sel)).join("")}</ul>`:`<p class="mpv-mut">Aucune.</p>`}<p class="mpv-mut">Rien n'est supprimé : ces dossiers restent consultables.</p></div></details>`;
  return h+`</section>${mpv6DcePanel(sg,where)}</div></div>`;};
{const _pg7=mpvPage;mpvPage=function(){if(!document.getElementById("mpv7-css")){const s=document.createElement("style");s.id="mpv7-css";s.textContent=`.mpv7-acts{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.mpv7-acts button:disabled{opacity:.5;cursor:not-allowed}
.mpv7-suivi{border:1px solid var(--mpv-line);border-left:3px solid var(--mpv-orf);border-radius:6px;background:var(--mpv-ivo);padding:8px 10px;margin:6px 0;font-size:13.5px}.mpv7-suivi p{margin:0 0 4px}.mpv7-suivi blockquote{margin:6px 0;max-height:140px;overflow:auto;font-size:12.5px;border-left:2px solid var(--mpv-line);padding-left:8px}
ul.mpv7-inv li{justify-content:space-between}.mpv6-cnt>span.mpv-mut{align-self:center;margin-left:auto}@media (max-width:640px){.mpv7-acts{grid-template-columns:1fr}}`;document.head.appendChild(s);}return _pg7();};}
/* panneau « Consultations » : l'ancienne « demande interne » (sans tâche) est remplacée par l'accès à la file DCE réelle */
{const _p7=mpvPanel;mpvPanel=function(B,dm,inList){let h=_p7(B,dm,inList);const e=MPV.sel&&B&&B.by.get(MPV.sel);if(!e)return h;const ids=dm[e.x.r+"/"+e.x.o]||[];if(!ids.length)return h;
  const k="p:"+e.x.o+":"+e.x.r,go=act(()=>{MPV6.ds.sel=k;MPV6.ds.mob="panel";MPV.tab="dce";MPN.outil="f:dce";MPV.outil="f:dce";MPV.conf=null;render();window.scrollTo(0,0);mpdFocus("#mpv6-dph");});
  return h.replace(/<button type="button" class="mpv-bp" data-mpv-demander="[^"]*" data-act="[^"]*">[\s\S]*?<\/button>/,`<button type="button" class="mpv-bp" data-mpv7-godce="${esc(k)}" data-act="${go}">${mpvI("dl")}Récupérer le DCE (file DCE)</button>`)
    .replace(/<button type="button" class="mpv-bp" data-mpv-odce="[^"]*" data-act="[^"]*">[\s\S]*?Suivre la récupération du DCE<\/button>/,`<button type="button" class="mpv-bp" data-mpv7-godce="${esc(k)}" data-act="${go}">${mpvI("open")}Suivre la récupération du DCE</button>`);};}
