"""mpv-6 : insère part_mpv6.js dans eaios.js publié (avant le démarrage) + correctifs ciblés de l'étape Décision (aucune société présélectionnée
quand le dossier n'a pas de société choisie). Usage : python3 build6.py <eaios.js source> <eaios.js sortie>"""
import hashlib,sys,os
ICI=os.path.dirname(os.path.abspath(__file__))
src,dst=sys.argv[1],sys.argv[2]
out=open(src,encoding="utf-8").read()
mod=open(os.path.join(ICI,"part_mpv6.js"),encoding="utf-8").read()
assert "</script" not in mod.lower() and "MPV6" not in out
ANC="\nrender();\n(async()=>{try{\n  const db="
assert out.count(ANC)==1,"ancre de démarrage"
out=out.replace(ANC,"\n"+mod.rstrip()+"\n"+ANC,1)
R=[
 # Décision B2.1 : la société du dossier n'est présélectionnée que si elle a été choisie (jamais celle posée d'office par l'ancien suivi)
 ('function b21dUi8(id,a){if(B21D.ui.id!==id){B21D.ui={id,sel:a.soc,','function b21dUi8(id,a){if(B21D.ui.id!==id){B21D.ui={id,sel:mpv6SocDossier(a),'),
 ('if(!u.sel)u.sel=a.soc;if(!u.mob)u.mob="list";return u;}','if(!u.sel)u.sel=mpv6SocDossier(a);if(!u.mob)u.mob="list";return u;}'),
 ('const E=ids.map(sid=>b21dEval(id,a,sid,X.find(x=>x.sid===sid)||null));if(!E.some(e=>e.sid===u.sel))u.sel=(E[0]||{}).sid;',
  'const E=ids.map(sid=>b21dEval(id,a,sid,X.find(x=>x.sid===sid)||null));if(u.sel&&!E.some(e=>e.sid===u.sel))u.sel=null;'),
 # onglets B1.1 au clavier : même ordre que l'affichage (Consultations, Mes consultations suivies, DCE à récupérer)
 ('const T=["cons","dce","suiv"],i=T.indexOf(t.dataset.mpvTab)','const T=["cons","suiv","dce"],i=T.indexOf(t.dataset.mpvTab)'),
 ('const sel=E.find(e=>e.sid===u.sel);h+=sel?b21dPanel(id,a,sel):`<section class="b21d-p"><p class="b21d-src">Aucune société.</p></section>`;',
  'const sel=E.find(e=>e.sid===u.sel);h+=sel?b21dPanel(id,a,sel):E.length?`<section class="b21d-p" data-b21d-nosel="1"><p class="b21d-src"><b>Choisissez une société dans la liste.</b> Le choix des sociétés se fait ici, à l\'étape Décision : rien n\'est créé ni enregistré tant qu\'une décision n\'est pas confirmée.</p></section>`:`<section class="b21d-p"><p class="b21d-src">Aucune société.</p></section>`;'),
]
for A,B in R:
  assert out.count(A)==1,A[:70]
  out=out.replace(A,B,1)
open(dst,"w",encoding="utf-8").write(out)
print(hashlib.sha256(out.encode()).hexdigest(),len(out))
