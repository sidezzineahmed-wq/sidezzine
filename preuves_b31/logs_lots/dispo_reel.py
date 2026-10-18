import os
ICI0=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ICI0,"qa_b21dec.py"),encoding="utf-8").read().split("\nwith sync_playwright() as p:")[0])
WAIT="()=>typeof S!=='undefined'&&S.aoState==='ok'&&S.cat&&Object.keys(S.ao).length>50&&S.enrState==='ok'"
with sync_playwright() as p:
    b=p.chromium.launch();ctx,pg,errs=demarrer(b,1440,1000);pg.wait_for_function(WAIT,timeout=30000)
    pg.evaluate("()=>{S.dept='ao';S.soc=null;S.aoId=null;MPN.last='ao';MPN.dos=null;mpnBureau('MP-B1.1');render();}");pg.wait_for_timeout(600)
    print(pg.evaluate("()=>{const d=document.createElement('div');d.innerHTML=mpvDispoLi(MPV.base.R.filter(e=>!e.x._ferme));return d.innerText}"))
    print(errs[:2]);b.close()
