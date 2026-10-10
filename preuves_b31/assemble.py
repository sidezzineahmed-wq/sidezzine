h=open("part_head.js",encoding="utf-8").read()
h=h.replace('const B21={v:"b21-1",open:{},soc:{},bpTout:{}};','const B21={v:"b21-5",open:{},soc:{},bpTout:{},compTout:{},pdf:{},pan:{}};')
assert 'v:"b21-5"' in h
h=h.replace("aucune valeur inventée.","aucune valeur inventée. Composition b21-2 : tableau de bord pleine largeur fidèle à la maquette approuvée\n   (en-tête, synthèse, cartes 01 à 09, compléments), résumés visibles et détails longs repliables à l'intérieur, sans données de maquette. PDF b21-3 : document vectoriel\n   (pdfmake) construit depuis les mêmes données normalisées que l'écran ; aucune capture d'écran.",1)
row='function b21Row(lab,val,src,o){o=o||{};return`<div class="b21-row${o.cls?" "+o.cls:""}"><div class="b21-k">${esc(lab)}</div><div class="b21-v">${val}${src!==undefined?`<div>${b21Src(src)}</div>`:""}</div></div>`;}\n'
parts=[h,row,open("part_data.js").read(),open("part_cards.js").read(),"/* ---- 8 · checklist par société ---- */\n",open("part_check.js").read(),open("part_aller.js").read(),open("part_sec.js").read(),open("part_main.js").read(),open("part_qual.js").read(),open("part_qualv.js").read(),open("part_pdf.js").read(),open("part_tail.js").read(),open("part_b31.js").read(),open("part_b21dec.js").read()]
m="".join(p if p.endswith("\n") else p+"\n" for p in parts)
assert "</script" not in m.lower()
open("b21_module.js","w",encoding="utf-8").write(m)
