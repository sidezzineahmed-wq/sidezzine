import hashlib,sys
src=open("avant/index.html",encoding="utf-8").read()
assert hashlib.sha256(src.encode()).hexdigest()=="522c6b0ecb9c7cf130bac7e7686fc99212fbf37d5f31d8f63f3132fc2806e55b","base inattendue"
mod=open("b21_module.js",encoding="utf-8").read()
anc="\nrender();\n(async()=>{try{\n  const db="
assert src.count(anc)==1
assert "</script" not in mod.lower()
out=src.replace(anc,"\n"+mod.rstrip()+"\n"+anc,1)
# b31-1 : le chargeur bpx conserve aussi les verrous de ligne et l'origine des PU (B3.1) ; aucun autre champ ne change
LBPX='S.bpx[d.id]={p:v.p||{},q:v.q||{},k:v.k,sd:v.sd||{},soc:v.soc,meta:v.meta,t:v.t};'
assert out.count(LBPX)==1
out=out.replace(LBPX,'S.bpx[d.id]={p:v.p||{},q:v.q||{},k:v.k,sd:v.sd||{},soc:v.soc,meta:v.meta,t:v.t,lock:v.lock||{},srcL:v.srcL||{},tva:v.tva||null};')

# b31-6b : parcours express — même résumé de prix que les cartes (TVA documentée, aucun taux supposé)
LEXP='step(T.miss?"vous":"ok",T.miss?"À vous : fixer "+T.miss+" prix sur "+b.nb+" lignes (étape 4).":"Bordereau chiffré : "+dh(T.ttc)+" TTC.");'
assert out.count(LEXP)==1
out=out.replace(LEXP,'step(T.miss?"vous":"ok",T.miss?"À vous : fixer "+T.miss+" prix sur "+b.nb+" lignes (étape 4).":"Bordereau chiffré : "+(b31ResumeTTC(id,a)||dh(T.ttc)+" TTC")+".");')

# b21d-3 : bureau B2.1, mode « Décision d'Ahmed » : la note d'analyse n'est plus calculée ni rendue dans cette vue (elle reste entière dans le mode
# « Note d'analyse ») ; titre unique « Décision d'Ahmed » ; la section humaine n'a plus de titre doublé
LN='else if(D.bur==="MP-B2.1"){const n=st("note").body?st("note").body():"",dd=st("dec"),Pd=STEP_PILL[dd.st]||["p-dash",""];'
assert out.count(LN)==1
out=out.replace(LN,'else if(D.bur==="MP-B2.1"){const dd=st("dec"),Pd=STEP_PILL[dd.st]||["p-dash",""];')
LH='const hum=`<section class="mpn-humain" aria-labelledby="mpn-dec"><h3 id="mpn-dec">Décision d\'Ahmed</h3><div class="mpn-dres"><span class="pill ${Pd[0]}">${esc(Pd[1])}</span><span>${esc(dd.res||"")}</span></div><p class="hint" style="margin-top:0">Espace humain relié au bureau B2.1 : la décision Go ou No-Go appartient à Ahmed. Aucun employé numérique ni aucun bureau ne décide.</p>${dd.body?dd.body():""}</section>`;'
assert out.count(LH)==1
out=out.replace(LH,'const hum=()=>`<section class="mpn-humain" aria-label="Décision d\'Ahmed" data-mpn-dec-vue="1"><p class="hint" style="margin-top:0">Espace humain relié au bureau B2.1 : la décision Go ou No-Go appartient à Ahmed. Aucun employé numérique ni aucun bureau ne décide.</p>${dd.body?dd.body():""}</section>`;')
LW='w=D.k==="dec"?hum+`<h3 class="mpn-t3">Note d\'analyse</h3>`+n:n+resume;}'
assert out.count(LW)==1
out=out.replace(LW,'w=D.k==="dec"?hum():(st("note").body?st("note").body():"")+resume;}')
LT=':D.bur==="MP-B2.1"&&D.k==="dec"?"Décision d\'Ahmed et note d\'analyse":'
assert out.count(LT)==1
out=out.replace(LT,':D.bur==="MP-B2.1"&&D.k==="dec"?"Décision d\'Ahmed":')
# b21d-4 : création existante d'un dossier séparé (creerSib) avec option sansGo : mêmes contrôles (parCompat : art. 27, déjà membre,
# écartée), même identifiant base~société, mêmes données publiques (sibData, FIN-ISO-001) ; mais aucune décision, statut « À examiner »,
# pas de lancement de préparation, pas de changement du dossier ouvert. Sans option : comportement inchangé (Go d'offre séparée).
for A,B in [
 ('async function creerSib(id,sid){const a=S.ao[id]','async function creerSib(id,sid,o){o=o||{};const a=S.ao[id]'),
 ('if(g&&g.exists){S.aoId=nid;render();return toast("Ce dossier existe déjà : ouvert tel quel.");}',
  'if(g&&g.exists){if(o.sansGo){render();return toast("Le dossier de "+socCourt(sid)+" existe déjà pour cet AO : rien n\'est créé.");}S.aoId=nid;render();return toast("Ce dossier existe déjà : ouvert tel quel.");}'),
 ('statut:"En préparation",cree:isoToday(),decision:{verdict:"Go",le:isoToday(),qui:S.role.me||null,parallele:true}});',
  'cree:isoToday()},o.sansGo?{statut:"À examiner",ajout:{le:isoToday(),qui:S.role.me||null,source:o.source||"B2.1"}}:{statut:"En préparation",decision:{verdict:"Go",le:isoToday(),qui:S.role.me||null,parallele:true}});'),
 ('  S.db.doc("ao/"+nid).set(d).then(()=>{S.ao[nid]=d;logJ(a.ref+" : offre séparée ouverte pour "+socCourt(sid));',
  '  return S.db.doc("ao/"+nid).set(d).then(()=>{S.ao[nid]=d;if(o.sansGo){logJ(a.ref+" : dossier séparé ajouté pour "+socCourt(sid)+" (aucune décision enregistrée)");render();return toast("Dossier séparé créé pour "+socCourt(sid)+" : aucune décision enregistrée ; ses pièces, ses prix et sa signature restent séparés.");}logJ(a.ref+" : offre séparée ouverte pour "+socCourt(sid));'),
]:
  assert out.count(A)==1,A[:60]
  out=out.replace(A,B)
open("page_b21.html","w",encoding="utf-8").write(out)
print(hashlib.sha256(out.encode()).hexdigest(),len(out))
