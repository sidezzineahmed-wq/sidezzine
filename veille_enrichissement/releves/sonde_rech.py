"""Recherche officielle filtrée par classification (lecture publique, client du kit, 3 s mini)."""
import sys,os,json,re
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","..","coffre_bc24","stock","kit"))
os.environ.setdefault("REQUESTS_CA_BUNDLE","/root/.ccr/ca-bundle.crt")
from veille.client import ClientPMMP
from veille.pmmp_listing import CollecteListing,total_et_pages,P_RECH
J=[];c=ClientPMMP(delai_min=3.0,journal=J.append);L=CollecteListing(c);D=os.path.dirname(__file__)
L.ouvrir();out={}
for cl in sys.argv[1:]:
    f={"type_rechercheEntite":"exact"} if cl!="-" else {}
    h,d=L.rechercher(classification=None if cl=="-" else cl,fenetre=f)
    open(f"{D}/rech_{cl}.html","w").write(h);out[cl]=total_et_pages(h);print(cl,out[cl])
print(json.dumps(J))
