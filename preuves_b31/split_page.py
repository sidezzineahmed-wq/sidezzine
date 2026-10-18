"""Allège index.html : le <style> et le <script> uniques sont publiés comme fichiers annexes du même artefact
(app/eaios.css, app/eaios.js), chargés au même endroit et dans le même ordre (script classique, ni async ni defer).
Motif : le passage horaire doit relire la page ENTIÈRE avant de la republier ; à 1,79 Mo il ne le pouvait plus.
Usage : python3 split_page.py <page.html> <sortie_page.html> <dossier_app>"""
import re,sys,os,hashlib
src,dst,app=sys.argv[1:4]
h=open(src,encoding="utf-8").read()
i=h.index("<style>",h.index("<!DOCTYPE html>"));j=h.index("</style>",i);k=h.index("<script>")
assert i<k and j<k,"le premier <style> doit précéder le script"
st=[h[i+7:j]];sc=re.findall(r"<script>(.*?)</script>",h,re.S)
assert len(sc)==1 and h.count("<script")==h.count("<script>")+h[k:].count("<script") - h[k:].count("<script")
os.makedirs(app,exist_ok=True)
open(os.path.join(app,"eaios.css"),"w",encoding="utf-8").write(st[0])
open(os.path.join(app,"eaios.js"),"w",encoding="utf-8").write(sc[0])
v=lambda t:hashlib.sha256(t.encode()).hexdigest()[:12]
h=h.replace("<style>"+st[0]+"</style>",f'<link rel="stylesheet" href="app/eaios.css?v={v(st[0])}">',1)
h=h.replace("<script>"+sc[0]+"</script>",f'<script src="app/eaios.js?v={v(sc[0])}"></script>',1)
open(dst,"w",encoding="utf-8").write(h)
print(len(h),"octets ; css",len(st[0]),"js",len(sc[0]))
