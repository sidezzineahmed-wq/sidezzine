"""Sonde bornée : rappels PRADO officiels de la recherche avancée PMMP (lecture publique, 3 s entre requêtes)."""
import sys,os,json,re,time,datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","..","coffre_bc24","stock","kit"))
from veille.client import ClientPMMP
from veille.html_outils import formulaire
os.environ.setdefault("REQUESTS_CA_BUNDLE","/root/.ccr/ca-bundle.crt")
J=[];c=ClientPMMP(delai_min=3.0,journal=J.append)
D=os.path.dirname(__file__)
P="ctl0$CONTENU_PAGE$AdvancedSearch$"
r=c.get({"page":"entreprise.EntrepriseAdvancedSearch","searchAnnCons":""});h=r.content.decode("utf-8","replace");url=r.url
open(f"{D}/form.html","w").write(h)
for cl in sys.argv[1:] or ("1",):
    d=formulaire(h);d[P+"type_rechercheEntite"]="exact";d[P+"classification"]=cl
    d["PRADO_CALLBACK_TARGET"]=P+"classification";d["PRADO_CALLBACK_PARAMETER"]="null"
    r=c.s.post(url,data=d,timeout=90,headers={"X-Requested-With":"XMLHttpRequest"});c._dernier=time.monotonic()
    open(f"{D}/cb_class_{cl}.txt","w").write("HEADERS "+json.dumps(dict(r.headers))+"\n\n"+r.content.decode("utf-8","replace"))
    print(cl,r.status_code,len(r.content),{k:v[:200] for k,v in r.headers.items() if "PRADO" in k.upper()})
print(json.dumps(J))
