"""mpv-6c : correctif MINIMAL appliqué sur le script EAIOS publié (rebase : jamais une ancienne version reprise en bloc).
1. Premier chargement du catalogue : jamais différé parce qu'un champ de saisie a le focus (reproduit : focus dans la recherche
   = « Chargement du catalogue… » jusqu'à la sortie du champ) ; le report reste pour remplacer une liste DÉJÀ affichée.
2. « DCE à récupérer » / « Mes consultations suivies » : tant que le catalogue ou les données de fiches chargent, « Chargement… » ;
   en cas d'échec, « indisponible » explicite ; « absente du catalogue » seulement catalogue chargé.
Usage : python3 build6c.py <eaios.js publié> <sortie>"""
import hashlib,sys
src,dst=sys.argv[1],sys.argv[2]
out=open(src,encoding="utf-8").read()
R=[
 ('if(catSaisieEnCours()&&sha!==S.catSha){S.catAttente=L;softRender();return"differe";}',
  'if(S.cat&&catSaisieEnCours()&&sha!==S.catSha){S.catAttente=L;softRender();return"differe";}'),
 ('''function mpv6Inv(g){const x=g.x;
  if(!x)return`<p class="mpv-mut" data-mpv6-inv="inconnu">Inventaire PMMP : inconnu (consultation absente du catalogue de cette version).</p>`;''',
  '''function mpv6Inv(g){const x=g.x;
  if(!S.cat)return S.catState==="absent"?`<p class="mpv-w" data-mpv6-inv="erreur">Inventaire PMMP indisponible : le catalogue n'a pas pu être chargé${S.catRelu&&S.catRelu.motif?" ("+esc(S.catRelu.motif)+")":""}. Rouvrez EAIOS pour réessayer.</p>`:`<p class="mpv-mut" data-mpv6-inv="chargement" role="status">Chargement de l'inventaire PMMP…</p>`;
  if(!x)return`<p class="mpv-mut" data-mpv6-inv="inconnu">Inventaire PMMP : inconnu (consultation absente du catalogue de cette version).</p>`;
  if(!S.enr)return S.enrState==="chargement"?`<p class="mpv-mut" data-mpv6-inv="chargement" role="status">Chargement de l'inventaire PMMP…</p>`:`<p class="mpv-mut" data-mpv6-inv="indisponible">Inventaire PMMP indisponible dans cette version (données des fiches non publiées).</p>`;'''),
 ('${S.cat?"Absente du catalogue de cette version : informations du dossier.":"Catalogue non chargé : informations du dossier."}',
  '${S.cat?"Absente du catalogue de cette version : informations du dossier.":S.catState==="absent"?"Catalogue indisponible : informations du dossier.":"Chargement du catalogue : informations du dossier en attendant."}'),
 ('if(!g.x)h+=`<p class="mpv-mut" data-mpv6-horscat="1">','if(!g.x)h+=`<p class="mpv-mut" data-mpv6-horscat="${S.cat?"absente":S.catState==="absent"?"erreur":"chargement"}">'),
 # file et liste : dates des dossiers tant que le catalogue n'est pas là (annoncé)
 ('let h=`<div class="mpv6" data-mpv6="suiv">','let h=`<div class="mpv6" data-mpv6="suiv">${mpv6CatNote()}'),
 ('let h=`<div class="mpv6" data-mpv6="dce">','let h=`<div class="mpv6" data-mpv6="dce">${mpv6CatNote()}'),
 ('function mpv6Wait(){','function mpv6CatNote(){return S.cat?"":`<p class="mpv-mut" data-mpv6-catwait="${S.catState==="absent"?"erreur":"chargement"}" role="status">${S.catState==="absent"?"Catalogue indisponible : dates des dossiers, inventaires PMMP non disponibles.":"Chargement du catalogue : compteurs et dates provisoires (dates des dossiers), recalculés dès que le catalogue est chargé ; inventaires PMMP à venir."}</p>`;}\nfunction mpv6Wait(){'),
]
for A,B in R:
  assert out.count(A)==1,A[:80]
  out=out.replace(A,B,1)
open(dst,"w",encoding="utf-8").write(out)
print(hashlib.sha256(out.encode()).hexdigest(),len(out))
