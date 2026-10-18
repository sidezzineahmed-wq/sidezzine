"""Cibles = annonces du catalogue live sans mode connu (pmmp_enrichi live, fiches du coffre, cache local), union des cibles précédentes."""
import json,glob,re,sys
live_dir,fiches_p,prec_p,sortie=sys.argv[1:5]
n=lambda s:re.sub(r"\s+"," ",s or "").strip().upper()
cat=json.load(open(f"{live_dir}/catalogue.json"))["items"];e=json.load(open(f"{live_dir}/catalogue_details.json"))["pmmp_enrichi"]["mode_passation"]
F=json.load(open(fiches_p));cache={}
for p in glob.glob("pmmp/complement/cache/*.json"):
    r=json.load(open(p));cache[r["id"]]=r
prec=json.load(open(prec_p))
cib=dict(prec);nouv=0
for x in cat:
    k=f"pmmp:{x['o']}:{x['r']}";ref=x["ref"]
    v=e["par_id"].get(k);f=(F.get(k) or {}).get("champs") or {};c=cache.get(k)
    connu=(v and n(v.get("ref"))==n(ref)) or (f.get("mode_passation") and n(f.get("ref"))==n(ref)) or (c and c.get("mode_passation") and n(c.get("ref"))==n(ref))
    if not connu and k not in cib:cib[k]={"ref":ref,"lim":x.get("lim"),"h":x.get("h")};nouv+=1
    elif k in cib:cib[k]["ref"]=ref
json.dump(cib,open(sortie,"w"),ensure_ascii=False)
rest=[k for k in cib if not glob.glob(f"pmmp/complement/cache/{k.split(':')[1]}_{k.split(':')[2]}.json")]
print({"cibles":len(cib),"nouvelles_ajoutees":nouv,"restant_a_lire":len(rest)})
