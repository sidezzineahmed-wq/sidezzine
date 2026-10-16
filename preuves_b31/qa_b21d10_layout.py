"""b21d-10b : mise en page des lignes d'information sous une pièce (références, renvoi RIB, RIB résolu, saisie RIB) à 390/615/768/1440,
clair et sombre. Banc fictif de qa_b21dec (base simulée) ; le seul état ajouté (RIB résolu) l'est en mémoire de la page de test."""
import os
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
MES="""()=>{const out=[];document.querySelectorAll('[data-b21d-panel] [data-b21d-fr],[data-b21d-panel] [data-b21d-autre]').forEach(r=>{const R=r.getBoundingClientRect(),c=r.closest('[data-b21d-doc]').dataset.b21dDoc;
  const kind=r.dataset.b21dAutre?'autre':r.dataset.b21dFref?'renvoi':r.dataset.b21dFres?'resolu':'saisie';
  const parts=[...r.children].filter(x=>!x.classList.contains('b21d-fi')&&getComputedStyle(x).display!=='none').map(x=>{const b=x.getBoundingClientRect();return{c:x.className,w:Math.round(b.width),h:Math.round(b.height),r:Math.round(b.right-R.right),l:Math.round(b.left-R.left)};});
  out.push({doc:c,kind,k:r.dataset.b21dFr||'autre',h:Math.round(R.height),w:Math.round(R.width),parts});});return out;}"""
res=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for (w,h,sch) in ((390,844,"light"),(615,900,"light"),(615,900,"dark"),(768,1000,"light"),(1440,900,"light"),(1440,900,"dark")):
        tag=f"{w}{'_sombre' if sch=='dark' else ''}"
        c=b.new_context(viewport={"width":w,"height":h},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function("()=>typeof S!=='undefined'&&S.aoState==='ok'&&Object.keys(S.ao).length>50",timeout=20000);q.wait_for_timeout(800);dec(q,"fx-dec")
        q.click('[data-b21d-item="alwaad-ataib"]');q.wait_for_timeout(300)
        for d in ("dsh","moyens","ae"):q.evaluate("d=>{B21D.ui.dOpen['alwaad-ataib|'+d]=true;}",d)
        q.evaluate("()=>{D0('alwaad-ataib').references=[];render();}");   # comme ALWAAD réel : aucune référence saisie (mémoire de la page de test)q.wait_for_timeout(300)
        A=q.evaluate(MES)
        # RIB résolu (état simulé en mémoire : profil lu + confirmation de la base), pour mesurer la ligne « Renseigné dans le coffre ✓ »
        q.evaluate("()=>{const s='alwaad-ataib',v='123456789012345678901234';const d=D0(s);d.profil={...(d.profil||{}),rib:v};B21D.pf[s+'|rib']={v,saved:v,base:v,st:'ok',dirty:false};B21D.docF[s+'|dsh']=[...new Set([...(B21D.docF[s+'|dsh']||[]),'rib'])];if(document.activeElement)document.activeElement.blur();render();}")
        q.wait_for_timeout(300);B=q.evaluate(MES)
        ov=q.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        q.locator('[data-b21d-doc="moyens"]').screenshot(path=f"{OUT}/moyens_{tag}.png");q.locator('[data-b21d-doc="dsh"]').screenshot(path=f"{OUT}/dh_rib_{tag}.png")
        kinds={x["kind"] for x in A+B}
        def bad(x):
            if x["kind"]=="saisie":return x["h"]>160 or any(pp["r"]>1 or pp["l"]<-1 for pp in x["parts"])
            return x["h"]>200 or any(pp["r"]>1 or pp["l"]<-1 or (pp["w"]<120 and "b21d-fs" not in pp["c"]) for pp in x["parts"])
        B_=[x for x in A+B if bad(x)]
        chk(not B_ and {"autre","renvoi","resolu","saisie"}<=kinds and ov<=1 and not e,f"{tag} : lignes références / renvoi RIB / RIB résolu / saisie lisibles (texte ≥120px de large, hauteur bornée, rien hors de la ligne), aucun débordement {[(x['kind'],x['h'],[(pp['c'],pp['w'],pp['h']) for pp in x['parts']]) for x in (B_ or [y for y in A+B if y['kind']=='autre'])][:3]}")
        res.append((tag,[(x["kind"],x["h"],x["w"]) for x in A+B if x["kind"]!="saisie" or x["k"].endswith("rib")]))
        c.close()
    b.close()
for r in res:print(r)
print(f"{sum(1 for x in R if x.startswith('OK'))} / {len(R)}")
