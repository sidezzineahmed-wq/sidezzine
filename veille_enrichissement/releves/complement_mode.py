"""Complément borné du « Mode de passation » (élément modePassation de la fiche publique PMMP).
Lecture publique sans compte ; client du kit (>= 4 s + gigue, arrêt sur 401/403) ; contacts tronqués AVANT analyse.
Reprise : un fichier cache/<org>_<ref>.json par fiche lue (rien n'est relu s'il existe). Ne conserve QUE
mode_passation, proc, ref (contrôle de jointure), lu_le, sha256 du HTML tronqué. N'écrit nulle part ailleurs."""
import sys,os,json,hashlib,datetime,argparse
K=os.path.join(os.path.dirname(__file__),"..","..","coffre_bc24","stock","kit");sys.path.insert(0,K)
os.environ.setdefault("REQUESTS_CA_BUNDLE","/root/.ccr/ca-bundle.crt")
from veille.client import ClientPMMP,ArretCollecte,texte
from veille.pmmp_fiche import PARAMS,lire_fiche,tronquer_contact,fiche_valide
ap=argparse.ArgumentParser();ap.add_argument("--catalogue");ap.add_argument("--fiches-coffre");ap.add_argument("--max",type=int,default=500);ap.add_argument("--aujourdhui");a=ap.parse_args()
D=os.path.join(os.path.dirname(__file__),"cache");now=lambda:datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
F=json.load(open(a.fiches_coffre));C=json.load(open(a.catalogue))["items"]
conn=lambda o,r:os.path.exists(os.path.join(D,f"{o}_{r}.json"))
cand=[x for x in C if (x.get("lim") or "9")>=a.aujourdhui and not ((F.get(f"pmmp:{x['o']}:{x['r']}") or {}).get("champs") or {}).get("mode_passation") and not conn(x["o"],x["r"])]
cand.sort(key=lambda x:(x.get("lim") or "9",x.get("h") or "",x["o"],x["r"]))
J=[];c=ClientPMMP(delai_min=4.0,journal=J.append);ok=err=0
print(json.dumps({"candidats":len(cand),"max":a.max,"debut":now()}),flush=True)
for x in cand[:a.max]:
    try:
        r=c.get(PARAMS(x["r"],x["o"]));h,coupe=tronquer_contact(texte(r));f=lire_fiche(h,masquer=True)
        if not fiche_valide(f):err+=1;continue
        rec={"id":f"pmmp:{x['o']}:{x['r']}","lu_le":now(),"url":r.url[:300],"mode_passation":f.get("mode_passation"),"proc":f.get("proc"),"ref":f.get("ref"),
             "ref_catalogue":x.get("ref"),"contact_coupe":coupe,"sha256_html_tronque":hashlib.sha256(h.encode()).hexdigest()}
        json.dump(rec,open(os.path.join(D,f"{x['o']}_{x['r']}.json"),"w"),ensure_ascii=False);ok+=1
        if ok%25==0:print(json.dumps({"lues":ok,"echecs":err,"t":now()}),flush=True)
    except ArretCollecte as e:
        print(json.dumps({"ARRET":str(e)}),flush=True);break
    except Exception as e:
        err+=1;print(json.dumps({"echec":x["o"]+":"+x["r"],"e":repr(e)[:160]}),flush=True)
print(json.dumps({"fin":now(),"lues":ok,"echecs":err,"requetes":c.nb_requetes}),flush=True)
json.dump(J,open(os.path.join(os.path.dirname(__file__),f"journal_{now().replace(':','')}.json"),"w"))
