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
open("page_b21.html","w",encoding="utf-8").write(out)
print(hashlib.sha256(out.encode()).hexdigest(),len(out))
