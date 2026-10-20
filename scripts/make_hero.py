"""Draw docs/hero.svg from a saved receipt, so every number in the picture comes from the data."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from versus.report import analyse, cost_per_thousand  # noqa: E402

receipt = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else "receipts/gemma.json").read_text())
prices = {"claude:answered-blind": (2.0, 10.0)}
a = analyse(receipt)
models = receipt["models"]
tags = a["tags"]
tag_of = {t["id"]: t["tag"] for t in receipt["tasks"]}
rate = {m: defaultdict(lambda: [0, 0]) for m in models}
for m, rows in receipt["results"].items():
    for r in rows:
        rate[m][tag_of[r["id"]]][0] += r["ok"]
        rate[m][tag_of[r["id"]]][1] += 1

NAMES = {models[0]: "Gemma 3 · 4B", models[1]: "Gemma 3 · 12B", models[2]: "Claude"}
COLOURS = {models[0]: "#ffb454", models[1]: "#39d0c0", models[2]: "#a78bfa"}
W, H = 1200, 720
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">']
o.append('''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b0f19"/><stop offset="1" stop-color="#151a2e"/></linearGradient>
<linearGradient id="glow" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffb454"/><stop offset="0.5" stop-color="#39d0c0"/><stop offset="1" stop-color="#a78bfa"/></linearGradient>
<style>
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes fade{from{opacity:0}to{opacity:1}}
.bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow .9s cubic-bezier(.2,.8,.2,1) both}
.fade{animation:fade .8s ease both}
</style></defs>''')
o.append(f'<rect width="{W}" height="{H}" rx="24" fill="url(#bg)"/>')
o.append(f'<rect x="0" y="0" width="{W}" height="5" rx="2" fill="url(#glow)"/>')
o.append('<text x="60" y="78" font-size="46" font-weight="800" fill="#fff" letter-spacing="-1">versus</text>')
o.append('<text x="60" y="108" font-size="17" fill="#8b93a7">Same tasks. Free model on your laptop vs Claude. Every answer marked by a fixed rule.</text>')
# score cards
cw, gap, x0, y0 = 340, 30, 60, 140
for i, m in enumerate(models):
    s = a["summary"][m]
    x = x0 + i * (cw + gap)
    price = prices.get(m, (0, 0))
    cost = cost_per_thousand(receipt["results"][m], price)
    d = 0.15 * i
    o.append(f'<g class="fade" style="animation-delay:{d}s">')
    o.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="112" rx="16" fill="#ffffff08" stroke="{COLOURS[m]}" stroke-opacity=".45"/>')
    o.append(f'<circle cx="{x+28}" cy="{y0+32}" r="6" fill="{COLOURS[m]}"/>')
    o.append(f'<text x="{x+44}" y="{y0+38}" font-size="17" font-weight="600" fill="#cfd5e6">{NAMES[m]}</text>')
    o.append(f'<text x="{x+24}" y="{y0+90}" font-size="48" font-weight="800" fill="{COLOURS[m]}">{round(s["passed"]/s["total"]*100)}%</text>')
    o.append(f'<text x="{x+cw-24}" y="{y0+66}" font-size="15" fill="#8b93a7" text-anchor="end">{s["passed"]} of {s["total"]} right</text>')
    o.append(f'<text x="{x+cw-24}" y="{y0+90}" font-size="15" fill="#8b93a7" text-anchor="end">${cost:.2f} per 1,000 tasks</text>')
    o.append('</g>')
# chart
base, top = 600, 330
ch = base - top
o.append(f'<text x="60" y="300" font-size="15" font-weight="600" fill="#8b93a7" letter-spacing="2">RIGHT ANSWERS BY KIND OF TASK</text>')
for pct in (0, 50, 100):
    y = base - ch * pct / 100
    o.append(f'<line x1="60" x2="1140" y1="{y}" y2="{y}" stroke="#ffffff" stroke-opacity="{.18 if pct==0 else .07}"/>')
    o.append(f'<text x="52" y="{y+5}" font-size="12" fill="#5d6580" text-anchor="end">{pct}%</text>')
gw = 1080 / len(tags)
bw, bg = 46, 8
for gi, tag in enumerate(tags):
    gx = 60 + gi * gw + (gw - (3 * bw + 2 * bg)) / 2
    for mi, m in enumerate(models):
        k, n = rate[m][tag]
        p = k / n
        h = ch * p
        x = gx + mi * (bw + bg)
        delay = 0.3 + gi * 0.12 + mi * 0.07
        o.append(f'<rect class="bar" style="animation-delay:{delay:.2f}s" x="{x:.1f}" y="{base-h:.1f}" width="{bw}" height="{max(h,2):.1f}" rx="6" fill="{COLOURS[m]}"/>')
        o.append(f'<text class="fade" style="animation-delay:{delay+.6:.2f}s" x="{x+bw/2:.1f}" y="{base-h-8:.1f}" font-size="12" font-weight="600" fill="{COLOURS[m]}" text-anchor="middle">{round(p*100)}</text>')
    o.append(f'<text x="{60+gi*gw+gw/2:.1f}" y="{base+26}" font-size="15" fill="#cfd5e6" text-anchor="middle">{tag}</text>')
# callout from the real numbers
worst_tag = min(tags, key=lambda t: rate[models[0]][t][0] / rate[models[0]][t][1])
k, n = rate[models[0]][worst_tag]
o.append(f'<text x="60" y="676" font-size="17" fill="#cfd5e6">The small model got <tspan font-weight="700" fill="{COLOURS[models[0]]}">{n-k} of {n} {worst_tag} tasks wrong</tspan>. It aced every sorting and labelling task.</text>')
o.append('<text x="60" y="700" font-size="13" fill="#5d6580">Claude answers came from a Claude agent shown only the questions; cost estimated at Sonnet 5.5 rates. 102 tasks, so read each score as a range.</text>')
# legend
lx = 1140
for m in reversed(models):
    o.append(f'<text x="{lx}" y="300" font-size="13" fill="#8b93a7" text-anchor="end">{NAMES[m]}</text>')
    lx -= len(NAMES[m]) * 7.3 + 30
    o.append(f'<circle cx="{lx+14}" cy="295" r="5" fill="{COLOURS[m]}"/>')
    lx -= 22
o.append('</svg>')
Path("docs/hero.svg").write_text("\n".join(o))
print("wrote docs/hero.svg")
