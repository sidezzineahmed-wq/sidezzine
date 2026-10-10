"""Base simulée B3.1 : copie locale des données réelles (lecture) + dossiers FICTIFS « fx-* » pour les tests d'écriture."""
import json,glob,os
D=json.load(open("srv/mockdb.json"))
for col in ("bpx","bpprop","offres"):
    D[col]={}
    for f in glob.glob(f"../reel/{col}/*.json"):
        d=json.load(open(f));d.pop("doc_id",None);D[col][os.path.basename(f)[:-5].replace("@","~")]=d
for f in glob.glob("../reel2/bp/*.json"):
    d=json.load(open(f));d.pop("doc_id",None);D["bp"][os.path.basename(f)[:-5]]=d
P0={"org":"fx","ref":"FX-0001","url":""}
def ao(ref,cat,obj,est,soc="sakdat",**k):
    a={"ref":ref,"categorie":cat,"obj":obj,"est":est,"soc":soc,"statut":"En préparation","mo":"MAÎTRE D'OUVRAGE FICTIF","lim":"2026-12-15","portail":dict(P0,ref=ref),"exig":{"estimation":est,"estimationSource":"FICTIF (test)"},"decision":{"verdict":"Go","le":"2026-10-01","qui":"u_qa","soc":soc}}
    a.update(k);return a
D["ao"]["fx-trv"]=ao("FX/TRV","Travaux","Travaux fictifs de test",5000)
D["ao"]["fx-trv~siditrav"]=ao("FX/TRV","Travaux","Travaux fictifs de test",5000,soc="siditrav",base="fx-trv")
D["ao"]["fx-big"]=ao("FX/BIG","Travaux","Grand bordereau fictif (400 lignes)",9000000)
D["ao"]["fx-etu"]=ao("FX/ETU","Services","Études techniques fictives",100000)
D["ao"]["fx-fou"]=ao("FX/FOU","Fournitures","Fournitures fictives",100000)
D["ao"]["fx-inc"]=ao("FX/INC","","Objet fictif sans catégorie",None);D["ao"]["fx-inc"]["exig"]={}
L3=[{"n":"1","d":"Ligne fictive A","u":"U","q":3,"s":"A. Section fictive"},{"n":"2","d":"Ligne fictive B","u":"m²","q":12.5,"s":"A. Section fictive"},{"n":"3","d":"Ligne fictive C","u":"ml","q":7,"s":"B. Autre section"}]
D["bp"]["fx-trv"]={"lots":[{"lignes":L3}],"cadre":False,"alertes":[]}
for k in ("fx-etu","fx-fou","fx-inc"):D["bp"][k]={"lots":[{"lignes":L3}],"cadre":False,"alertes":[]}
D["bp"]["fx-big"]={"lots":[{"lignes":[{"n":f"{i//40+1}.{i%40+1}","d":f"Ouvrage fictif n° {i+1} — désignation longue de test pour vérifier le retour à la ligne sans étirer les colonnes du bordereau, y compris toutes sujétions","u":["U","m²","m³","ml","ENS"][i%5],"q":(i%17)+1.5,"s":f"{i//40+1}. SECTION FICTIVE {i//40+1}"} for i in range(400)]}],"cadre":False,"alertes":[]}
D["bpx"]["fx-trv"]={"p":{"0-0":1234.56,"0-1":10.01,"0-2":0.07},"q":{},"soc":"sakdat"}
D["bpx"]["fx-big"]={"p":{f"0-{i}":round(50+i*3.17,2) for i in range(400) if i%9},"q":{},"soc":"sakdat"}
for k in ("fx-etu","fx-fou","fx-inc"):D["bpx"][k]={"p":{"0-0":1000,"0-1":100,"0-2":10},"q":{},"soc":"sakdat"}
# b31-6 : TVA documentée des dossiers FICTIFS (B3.1 ne suppose plus aucun taux) ; les dossiers réels restent sans TVA saisie
def tva_fx(D):
    for k,a in D["ao"].items():
        if not k.startswith("fx-"):continue
        x=D["bpx"].setdefault(k,{"p":{},"q":{},"soc":a.get("soc")})
        x.setdefault("tva",{"taux":20,"etat":"confirme","src":{"doc":"CPS FICTIF (test), article TVA","page":"1"},"mixte":False,"lignes":{},"par":"u_qa","le":"2026-10-01T00:00:00.000Z","soc":a.get("soc")})
tva_fx(D)
json.dump(D,open("srv/mockdb_b31.json","w"),ensure_ascii=False)
print({k:len(v) for k,v in D.items()})
