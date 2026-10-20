"""mpv-7 : « DCE à récupérer » branché sur la file DCE réelle. Appliqué sur le script EAIOS PUBLIÉ (relu juste avant) :
insertion de part_mpv7.js avant le démarrage + libellés du filtre DCE de « Mes consultations suivies ». Usage : build7.py <publié> <sortie>"""
import hashlib,sys,os
ICI=os.path.dirname(os.path.abspath(__file__))
src,dst=sys.argv[1],sys.argv[2]
out=open(src,encoding="utf-8").read();mod=open(os.path.join(ICI,"part_mpv7.js"),encoding="utf-8").read()
assert "</script" not in mod.lower() and "MPV7" not in out and "mpv6DcePanel" in out
ANC="\nrender();\n(async()=>{try{\n  const db="
assert out.count(ANC)==1
out=out.replace(ANC,"\n"+mod.rstrip()+"\n"+ANC,1)
R=[('[["","Tous"],["afaire","À récupérer"],["dem","Demande interne enregistrée"],["recu","Reçu (fichiers joints)"]]','[["","Tous"],["afaire","À demander"],["dem","En file ou en cours"],["recu","Reçu"]]')]
for A,B in R:
  assert out.count(A)==1,A[:60]
  out=out.replace(A,B,1)
open(dst,"w",encoding="utf-8").write(out)
print(hashlib.sha256(out.encode()).hexdigest(),len(out))
