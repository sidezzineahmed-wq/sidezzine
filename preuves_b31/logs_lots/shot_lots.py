import os,json
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
B11="()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}"
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50&&S.enrState==='ok'"
with sync_playwright() as p:
    b=p.chromium.launch()
    for w,sch in ((1440,"light"),(390,"dark")):
        c=b.new_context(viewport={"width":w,"height":1000},color_scheme=sch);c.add_init_script(INIT);q=c.new_page();e=[];q.on("pageerror",lambda x:e.append(str(x)))
        q.goto(URL);q.wait_for_function(WAIT,timeout=30000);q.wait_for_timeout(400);q.evaluate(B11);q.wait_for_timeout(500)
        k=q.evaluate("()=>{S.vf={...JSON.parse(JSON.stringify(VF0)),sort:S.vf.sort,tp:'oui',mts:['lt1']};render();const r=MPV.base.R.find(e=>{const m=mpvMatch(e,S.vf,null);return m.ok&&m.lots&&m.lots.length&&mpvLotsRec(e.x).lots.length>=3});MPV.sel=r.k;MPV.mob='panel';render();return [r.k,mpvMatch(r,S.vf,null).lots]}")
        q.evaluate("()=>document.querySelector('[data-mpv-lots]').scrollIntoView()");q.wait_for_timeout(300)
        q.screenshot(path=f"{OUT}/mpv4_reel_{w}_{sch}.png");print(w,k,e[:1])
        c.close()
    b.close()
