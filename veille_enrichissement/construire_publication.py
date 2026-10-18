"""Construit les données publiables : (1) kit_m3/referentiel/mode_passation_complement.json depuis le cache du complément ;
(2) catalogue_details.json = détails EAIOS live relus + pmmp_enrichi recalculé par le kit (même code que le passage horaire).
Usage : python3 construire_publication.py <dossier_eaios_live> <fiches_coffre.json> <sortie_dir>"""
import json,sys,os,subprocess,hashlib
live,fiches,out=sys.argv[1:4];os.makedirs(out,exist_ok=True)
K="kit_m3"
subprocess.run([sys.executable,"/home/user/sidezzine/veille_enrichissement/exporter_complement.py","--dossier","pmmp/complement","--essais","3",
  "--precedent",f"{K}/referentiel/mode_passation_complement.json","--sortie",f"{K}/referentiel/mode_passation_complement.json"],check=True)
sys.path.insert(0,f"{K}/ingestion");import ingestion_catalogue as I;from enrichi_pmmp import enrichir
db=open(f"{live}/catalogue_details.json","rb").read();d=json.loads(db);assert I.octets_json(d)==db
cb=open(f"{live}/catalogue.json","rb").read();cat=json.loads(cb);assert d["catalogue_sha256"]==hashlib.sha256(cb).hexdigest()
e=enrichir(cat["items"],json.load(open(fiches)),json.load(open(I.REFERENTIEL_CLASSIFICATION)),d.get("pmmp_enrichi"),json.load(open(I.COMPLEMENT_MODE)))
d["pmmp_enrichi"]=e;b=I.octets_json(d);open(f"{out}/catalogue_details.json","wb").write(b)
c=e["mode_passation"]["couverture"];print(json.dumps({"octets":len(b),"sha":hashlib.sha256(b).hexdigest()[:16],"mode":{k:v for k,v in c.items() if k!="reference_discordante"},"discord":len(c["reference_discordante"]),"classif":e["classification"]["couverture"]["par_code"]},ensure_ascii=False))
