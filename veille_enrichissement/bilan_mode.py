"""Bilan brut du mode de passation sur un catalogue + catalogue_details publiés (pmmp_enrichi) ; par source et statut."""
import json,sys,re,collections,datetime
d=sys.argv[1];n=lambda s:re.sub(r"\s+"," ",s or "").strip().upper()
cat=json.load(open(f"{d}/catalogue.json"))["items"];M=json.load(open(f"{d}/catalogue_details.json"))["pmmp_enrichi"]["mode_passation"]
val=collections.Counter();src=collections.Counter();st=collections.Counter();irr=[]
for x in cat:
    k=f"pmmp:{x['o']}:{x['r']}";v=M["par_id"].get(k)
    if v and n(v.get("ref"))==n(x["ref"]):val[v["v"]]+=1;src[v["source"]]+=1;st["connu"]+=1
    elif k in M.get("absents",{}):st["champ_absent"]+=1;irr.append((k,"champ_absent",M["absents"][k].get("lu_le")))
    elif k in M.get("inaccessibles",{}):st["inaccessible"]+=1;i=M["inaccessibles"][k];irr.append((k,"inaccessible",i.get("tentatives"),i.get("raison")))
    elif v:st["reference_discordante"]+=1;irr.append((k,"reference_discordante",v.get("ref"),x["ref"]))
    else:st["non_lu"]+=1
print(json.dumps({"annonces":len(cat),"statuts":dict(st),"valeurs":dict(val),"sources":dict(src),"pct":round(100*st["connu"]/len(cat),2),"irreductibles":irr[:50],"n_irreductibles":len(irr)},ensure_ascii=False,indent=1))
