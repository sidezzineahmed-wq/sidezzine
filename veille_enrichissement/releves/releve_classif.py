"""Relevé officiel borné : identifiants (orgCons, refCons) des résultats filtrés Etat/CL/EEP. Lecture publique, 3 s mini."""
import sys,os,json,re,datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","..","coffre_bc24","stock","kit"))
os.environ.setdefault("REQUESTS_CA_BUNDLE","/root/.ccr/ca-bundle.crt")
from veille.client import ClientPMMP
from veille.pmmp_listing import CollecteListing,total_et_pages,lignes
J=[];c=ClientPMMP(delai_min=3.0,journal=J.append);L=CollecteListing(c);D=os.path.dirname(__file__)
L.ouvrir();out={"debut":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),"url":L.url,"fenetre":L.fenetre,"classes":{}}
ids=lambda h:[(re.search(r'\$orgCons"[^>]*value="([^"]*)"',r).group(1),re.search(r'\$refCons"[^>]*value="(\d+)"',r).group(1)) for r in lignes(h)]
for cl in sys.argv[1:]:
    h,_=L.rechercher(classification=cl,fenetre={"type_rechercheEntite":"exact"});t0=total_et_pages(h)
    res={"total":t0["total"]}
    if cl!="1":
        h=L.taille_500(h);t=total_et_pages(h);I=ids(h)
        for n in range(2,(t["pages"] or 1)+1):
            h=L.page(h,n);I+=ids(h)
        res.update({"pages_500":t["pages"],"ids":sorted(set(I)),"n_ids":len(set(I))})
    out["classes"][cl]=res;print(cl,{k:v for k,v in res.items() if k!="ids"})
out["fin"]=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds");out["requetes"]=J
json.dump(out,open(f"{D}/releve_classif.json","w"),ensure_ascii=False,indent=1)
