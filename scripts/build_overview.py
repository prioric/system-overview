#!/usr/bin/env python3
"""Draw the system overview page of one company from its overview.json.

    python build_overview.py {company}
    python build_overview.py {company} --out {file}

Reads {company}/overview.json and the chapters in {company}/chapters/, and writes
{company}/system_overview.html: one HTML file with inline CSS and a short inline script,
no fonts to download and no web request.

Every card has a fixed place. The lines run in fixed lanes: from a card's inner edge, through
the gutter beside a column, onto a ring of lanes around the middle box. The builder tries every
order of lanes and both ways round the ring, and keeps the routing with the fewest crossings.

Python 3 and its standard library only.
"""
import argparse
import hashlib
import html
import itertools
import json
import sys
from pathlib import Path

W, H = 1760, 1200

# The panels: x, y, width, height.
PANELS = {
    "around": (0, 0, 300, H),
    "owns": (356, 0, 1048, 350),
    "money": (356, 850, 1048, 350),
    "says": (1460, 0, 300, H),
}
GROUP_OF = {
    "market": "around", "customers": "around", "competitors": "around",
    "assets": "owns", "capabilities": "owns", "limits": "owns",
    "invests": "money", "cuts": "money", "hires": "money",
    "story": "says", "signal": "says",
}
CARD_KEYS = list(GROUP_OF)
# The side each card's lines leave from: the side that faces the middle.
FACE = {"around": "right", "owns": "bottom", "money": "top", "says": "left"}

# The open area between the panels, and the middle box inside it.
OPEN = (356, 350, 1404, 850)
LANE_INSET, LANE_GAP = 20, 16
MIDDLE = (432, 426, 1328, 774)
GUTTER_LEFT = [314, 328, 342]
GUTTER_RIGHT = [1446, 1432, 1418]
ANCHOR_STEP = 22

COLORS = {
    "around": ("#0E6E6B", "#E2F0EF"),
    "owns": ("#2A5A95", "#E3EBF5"),
    "money": ("#9A5400", "#F5EADB"),
    "says": ("#9B3355", "#F4E3E9"),
}
INK, GRAY, PAGE = "#1F2328", "#5B6168", "#FAFAF7"
ACCENT = "#C2410C"

DEFAULT_LABELS = {
    "around": "Around it",
    "owns": "What it owns and what binds it",
    "money": "Where its money goes",
    "says": "What it says",
    "market": "Market", "customers": "Customers", "competitors": "Competitors",
    "assets": "Assets", "capabilities": "Capabilities", "limits": "Limits",
    "invests": "Invests", "cuts": "Cuts", "hires": "Hires",
    "story": "Story", "signal": "Signal",
    "decision": "The decision",
    "who": "Who decides",
    "by_when": "By when",
    "options": "Options",
    "who_pays": "Who pays",
    "cost": "Cost",
    "if_nobody": "If nobody decides",
    "pulls": "Where the facts pull against each other",
    "sources": "Sources",
    "evidence_date": "Evidence current as of",
    "status": "Status",
    "zoom_hint": "Ctrl and the mouse wheel zoom. Drag to move.",
    "fit_fault": "Text does not fit in:",
    "line_fault": "A line crosses a card:",
    "draft_note": "A draft written by a language model from public sources. A person checks every figure and claim against its source before this page reaches anyone.",
}


# ---------- layout ----------

def card_rects():
    """Each card's rectangle (x1, y1, x2, y2) on the stage."""
    rects = {}
    pad, gap, head = 12, 12, 52
    # Left and right columns: the group's pill on top, the cards below.
    for group, keys in (("around", ["market", "customers", "competitors"]), ("says", ["story", "signal"])):
        x, y, w, h = PANELS[group]
        n = len(keys)
        ch = (h - head - pad - gap * (n - 1)) / n
        for i, k in enumerate(keys):
            y1 = y + head + i * (ch + gap)
            rects[k] = (x + pad, y1, x + w - pad, y1 + ch)
    # Top row: pill on top, cards below. Bottom row: cards on top, pill below, so cards face the middle.
    for group, keys, top in (("owns", ["assets", "capabilities", "limits"], True),
                             ("money", ["invests", "cuts", "hires"], False)):
        x, y, w, h = PANELS[group]
        cw = (w - 2 * pad - gap * 2) / 3
        y1 = y + head if top else y + pad
        y2 = y + h - pad if top else y + h - head
        for i, k in enumerate(keys):
            x1 = x + pad + i * (cw + gap)
            rects[k] = (x1, y1, x1 + cw, y2)
    return rects


def ring(lane):
    i = LANE_INSET + LANE_GAP * lane
    return (OPEN[0] + i, OPEN[1] + i, OPEN[2] - i, OPEN[3] - i)


def ring_pos(r, p):
    """The distance along the ring, clockwise from its top-left corner, of point p on it."""
    x1, y1, x2, y2 = r
    x, y = p
    w, h = x2 - x1, y2 - y1
    if y == y1:
        return x - x1
    if x == x2:
        return w + (y - y1)
    if y == y2:
        return w + h + (x2 - x)
    return 2 * w + h + (y2 - y)


def ring_point(r, t):
    x1, y1, x2, y2 = r
    w, h = x2 - x1, y2 - y1
    t %= 2 * (w + h)
    if t <= w:
        return (x1 + t, y1)
    if t <= w + h:
        return (x2, y1 + t - w)
    if t <= 2 * w + h:
        return (x2 - (t - w - h), y2)
    return (x1, y2 - (t - 2 * w - h))


def ring_walk(r, a, b, clockwise):
    """The points from a to b along the ring, corners included."""
    x1, y1, x2, y2 = r
    w, h = x2 - x1, y2 - y1
    per = 2 * (w + h)
    corners = [0, w, w + h, 2 * w + h]
    ta, tb = ring_pos(r, a), ring_pos(r, b)
    pts = [a]
    if clockwise:
        d = (tb - ta) % per
        for c in sorted(corners, key=lambda c: (c - ta) % per):
            if 0 < (c - ta) % per < d:
                pts.append(ring_point(r, c))
    else:
        d = (ta - tb) % per
        for c in sorted(corners, key=lambda c: (ta - c) % per):
            if 0 < (ta - c) % per < d:
                pts.append(ring_point(r, c))
    pts.append(b)
    return pts


def leg(key, lane, slot, rects):
    """The points from a card's edge to its entry point on the ring, card end first."""
    group = GROUP_OF[key]
    x1, y1, x2, y2 = rects[key]
    rx1, ry1, rx2, ry2 = ring(lane)
    off = slot * ANCHOR_STEP
    face = FACE[group]
    if face == "bottom":
        x = (x1 + x2) / 2 + off
        return [(x, y2), (x, ry1)]
    if face == "top":
        x = (x1 + x2) / 2 + off
        return [(x, y1), (x, ry2)]
    y = (y1 + y2) / 2 + off
    if face == "right":
        edge, gx, rx = x2, GUTTER_LEFT[lane], rx1
    else:
        edge, gx, rx = x1, GUTTER_RIGHT[lane], rx2
    if ry1 <= y <= ry2:
        return [(edge, y), (rx, y)]
    yy = ry1 if y < ry1 else ry2
    return [(edge, y), (gx, y), (gx, yy), (rx, yy)]


def simplify(pts):
    out = []
    for p in pts:
        p = (round(p[0], 1), round(p[1], 1))
        if out and p == out[-1]:
            continue
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            if (a[0] == b[0] == p[0]) or (a[1] == b[1] == p[1]):
                out[-1] = p
                continue
        out.append(p)
    return out


def route(pull, lane, slots, rects, clockwise):
    a = leg(pull["from"], lane, slots[0], rects)
    b = leg(pull["to"], lane, slots[1], rects)
    middle = ring_walk(ring(lane), a[-1], b[-1], clockwise)
    return simplify(a + middle[1:] + list(reversed(b))[1:])


def segments(pts):
    return list(zip(pts, pts[1:]))


def seg_crosses_rect(s, r, margin=0.5):
    """True when a straight horizontal or vertical segment enters the inside of a rectangle."""
    (ax, ay), (bx, by) = s
    x1, y1, x2, y2 = r[0] + margin, r[1] + margin, r[2] - margin, r[3] - margin
    if ay == by:
        lo, hi = sorted((ax, bx))
        return y1 < ay < y2 and lo < x2 and hi > x1
    lo, hi = sorted((ay, by))
    return x1 < ax < x2 and lo < y2 and hi > y1


def seg_cross_point(s, t):
    """The point where a horizontal and a vertical segment cross, or None."""
    (ax, ay), (bx, by) = s
    (cx, cy), (dx, dy) = t
    if (ay == by) == (cy == dy):
        return None
    if ay != by:
        (ax, ay), (bx, by), (cx, cy), (dx, dy) = (cx, cy), (dx, dy), (ax, ay), (bx, by)
    x, y = cx, ay
    if min(ax, bx) < x < max(ax, bx) and min(cy, dy) < y < max(cy, dy):
        return (x, y)
    return None


def seg_overlap(s, t):
    """True when two segments lie on one line and share a stretch."""
    (ax, ay), (bx, by) = s
    (cx, cy), (dx, dy) = t
    if ay == by == cy == dy:
        return min(max(ax, bx), max(cx, dx)) - max(min(ax, bx), min(cx, dx)) > 0.5
    if ax == bx == cx == dx:
        return min(max(ay, by), max(cy, dy)) - max(min(ay, by), min(cy, dy)) > 0.5
    return False


def point_seg_dist(p, s):
    (ax, ay), (bx, by) = s
    x, y = p
    if ay == by:
        cx = min(max(x, min(ax, bx)), max(ax, bx))
        return ((x - cx) ** 2 + (y - ay) ** 2) ** 0.5
    cy = min(max(y, min(ay, by)), max(ay, by))
    return ((x - ax) ** 2 + (y - cy) ** 2) ** 0.5


def crossings(paths):
    pts = []
    for i, j in itertools.combinations(range(len(paths)), 2):
        for s in segments(paths[i]):
            for t in segments(paths[j]):
                c = seg_cross_point(s, t)
                if c:
                    pts.append(c)
    return pts


def place_dot(i, paths):
    """The point for line i's number: the middle of its longest clear stretch."""
    own = segments(paths[i])
    others = [s for j, p in enumerate(paths) if j != i for s in segments(p)]
    cands = []
    for s in own:
        (ax, ay), (bx, by) = s
        length = abs(ax - bx) + abs(ay - by)
        for f in (0.5, 0.35, 0.65, 0.2, 0.8):
            p = (ax + (bx - ax) * f, ay + (by - ay) * f)
            clear = min([point_seg_dist(p, t) for t in others] or [999])
            if clear >= 14:
                cands.append((-length, abs(f - 0.5), p))
    if not cands:
        return None
    return min(cands)[2]


def layout(data):
    """Cards, lines and dots for one overview. Returns a dict the page and the check both use."""
    rects = card_rects()
    pulls = data.get("pulls", [])
    n = len(pulls)
    # Slots spread two lines that touch the same card along its edge.
    use = {}
    slots = []
    for p in pulls:
        s = []
        for k in (p.get("from"), p.get("to")):
            use[k] = use.get(k, 0) + 1
            s.append(use[k])
        slots.append(s)
    # Centre the slots: one line leaves the middle of the edge, two leave half a step either side.
    for p_i, p in enumerate(pulls):
        for side, k in enumerate((p.get("from"), p.get("to"))):
            slots[p_i][side] = slots[p_i][side] - 1 - (use.get(k, 1) - 1) / 2
    best = None
    if all(p.get("from") in rects and p.get("to") in rects for p in pulls):
        for lanes in itertools.permutations(range(3), n):
            for ways in itertools.product((True, False), repeat=n):
                paths = [route(p, lanes[i], slots[i], rects, ways[i]) for i, p in enumerate(pulls)]
                cross = len(crossings(paths))
                length = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for path in paths for a, b in segments(path))
                score = (cross, length)
                if best is None or score < best[0]:
                    best = (score, paths, lanes)
    paths = best[1] if best else []
    dots = [place_dot(i, paths) for i in range(len(paths))]
    return {"rects": rects, "middle": MIDDLE, "paths": paths, "dots": dots,
            "crossings": crossings(paths), "stage": (W, H)}


def geometry_faults(lay):
    """Every fault of the drawn lines: crossing a card or the middle box, sharing a stretch, a dot on
    another line, a point off the stage, too many crossings."""
    faults = []
    rects, paths = lay["rects"], lay["paths"]
    for i, path in enumerate(paths):
        n = i + 1
        for s in segments(path):
            for k, r in rects.items():
                if seg_crosses_rect(s, r):
                    faults.append(f"line {n} crosses the card '{k}'")
            if seg_crosses_rect(s, lay["middle"]):
                faults.append(f"line {n} crosses the middle box")
        for x, y in path:
            if not (0 <= x <= W and 0 <= y <= H):
                faults.append(f"line {n} leaves the stage at ({x}, {y})")
    for i, j in itertools.combinations(range(len(paths)), 2):
        for s in segments(paths[i]):
            for t in segments(paths[j]):
                if seg_overlap(s, t):
                    faults.append(f"lines {i + 1} and {j + 1} share a stretch")
    for i, d in enumerate(lay["dots"]):
        if d is None:
            faults.append(f"line {i + 1} has no clear stretch for its number")
            continue
        for j, p in enumerate(paths):
            if j != i and min(point_seg_dist(d, s) for s in segments(p)) < 12:
                faults.append(f"the number of line {i + 1} sits on line {j + 1}")
    if len(lay["crossings"]) > 3:
        faults.append(f"the lines cross {len(lay['crossings'])} times; at most 3 are allowed")
    return sorted(set(faults))


# ---------- page ----------

def esc(s):
    return html.escape(str(s or ""), quote=True)


def file_hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def build_hashes(company):
    company = Path(company)
    h = {"overview.json": file_hash(company / "overview.json")}
    for p in sorted((company / "chapters").glob("*.md")):
        h["chapters/" + p.name] = file_hash(p)
    return h


def path_d(pts, r=8):
    """An SVG path with rounded corners."""
    if len(pts) < 2:
        return ""
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i - 1], pts[i], pts[i + 1]
        l1 = abs(bx - ax) + abs(by - ay)
        l2 = abs(cx - bx) + abs(cy - by)
        rr = min(r, l1 / 2, l2 / 2)
        ux, uy = ((bx - ax) / l1, (by - ay) / l1) if l1 else (0, 0)
        vx, vy = ((cx - bx) / l2, (cy - by) / l2) if l2 else (0, 0)
        d.append(f"L{bx - ux * rr:.1f},{by - uy * rr:.1f}")
        d.append(f"Q{bx:.1f},{by:.1f} {bx + vx * rr:.1f},{by + vy * rr:.1f}")
    d.append(f"L{pts[-1][0]:.1f},{pts[-1][1]:.1f}")
    return " ".join(d)


CSS = """
*{box-sizing:border-box}
html,body{margin:0;background:%(page)s;color:%(ink)s;font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header{display:flex;flex-wrap:wrap;gap:16px 32px;align-items:flex-end;justify-content:space-between;padding:20px 24px 12px}
header h1{font-size:26px;line-height:1.25;margin:0;max-width:1100px;font-weight:700}
header .co{font-size:14px;color:%(gray)s;margin:0 0 6px;text-transform:uppercase;letter-spacing:.06em}
.stats{display:flex;gap:28px}
.stat b{display:block;font-size:28px;line-height:1.1}
.stat span{font-size:13px;color:%(gray)s}
.bar{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding:0 24px 10px;font-size:13px;color:%(gray)s}
.bar .status{color:#9A1B1B;font-weight:600}
.bar .status.ok{color:#1E6B34}
.bar button{font:inherit;font-size:15px;min-width:34px;height:30px;border:1px solid #C9CCD1;background:#fff;border-radius:6px;cursor:pointer}
#fit{display:none;margin:0 24px 10px;padding:8px 12px;border:2px solid #B42318;color:#B42318;background:#FFF4F2;font-size:14px}
#wrap{position:relative;overflow:hidden;margin:0 12px;cursor:grab}
#stage{position:absolute;left:0;top:0;width:%(w)dpx;height:%(h)dpx;transform-origin:0 0}
.panel{position:absolute;border-radius:14px}
.pill{position:absolute;left:12px;height:30px;line-height:28px;padding:0 14px;border-radius:15px;background:#fff;border:2px solid;font-size:15px;font-weight:700;color:%(ink)s;white-space:nowrap}
.card{position:absolute;background:#fff;border-radius:10px;padding:12px 14px;overflow:hidden;display:flex;flex-direction:column;gap:6px;border:1px solid rgba(0,0,0,.06)}
.card .nm{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.07em}
.card .hl{font-size:18px;line-height:1.3;font-weight:700}
.card .bd{font-size:15px;line-height:1.42}
.card .src{font-size:12.5px;line-height:1.35;color:%(gray)s;margin-top:auto}
.card.s1 .hl{font-size:16px}.card.s1 .bd{font-size:13.5px}
.card.s2 .hl{font-size:14.5px}.card.s2 .bd{font-size:12.5px}.card.s2 .src{font-size:12px}
.over{outline:3px solid #B42318;outline-offset:2px}
#middle{position:absolute;background:#fff;border:2px solid %(accent)s;border-radius:14px;padding:20px 26px;overflow:hidden;display:flex;flex-direction:column;gap:8px}
#middle .eb{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:%(accent)s}
#middle .what{font-size:24px;line-height:1.25;font-weight:700}
#middle .meta{font-size:15px;color:%(gray)s}
#middle ul{margin:2px 0 0;padding-left:20px;font-size:16px;line-height:1.38}
#middle li{margin:2px 0}
#middle .pl{border-top:1px solid #E3E5E8;padding-top:8px;font-size:15px;line-height:1.5}
#middle .pl>span{display:inline-block;margin-right:18px}
#middle.s1 .what{font-size:20px}#middle.s1 ul{font-size:14.5px}
#middle.s2 .what{font-size:17px}#middle.s2 ul,#middle.s2 .pl{font-size:13px}
.num{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:10px;background:%(accent)s;color:#fff;font-size:12px;font-weight:700;margin-right:6px;vertical-align:1px}
svg{position:absolute;left:0;top:0;pointer-events:none}
main{max-width:980px;padding:20px 24px 48px}
main h2{font-size:20px;margin:28px 0 8px}
main h3{font-size:17px;margin:18px 0 4px}
main p,main li{font-size:16px;line-height:1.55}
main .small{font-size:13px;color:%(gray)s}
@media print{#wrap{overflow:visible}.bar button{display:none}}
"""

SCRIPT = r"""
(function(){
var W=%(w)d,H=%(h)d,wrap=document.getElementById('wrap'),stage=document.getElementById('stage');
var zoom=1,base=1,panX=0,panY=0;
function apply(){var s=base*zoom;stage.style.transform='translate('+panX+'px,'+panY+'px) scale('+s+')';wrap.style.height=Math.round(H*base)+'px';}
function fit(){base=Math.max(0.2,(wrap.clientWidth)/W);zoom=1;panX=0;panY=0;apply();}
window.addEventListener('resize',fit);
document.getElementById('zin').onclick=function(){zoom=Math.min(4,zoom*1.25);apply();};
document.getElementById('zout').onclick=function(){zoom=Math.max(1,zoom/1.25);if(zoom==1){panX=0;panY=0;}apply();};
document.getElementById('zfit').onclick=fit;
wrap.addEventListener('wheel',function(e){if(!e.ctrlKey)return;e.preventDefault();zoom=Math.min(4,Math.max(1,zoom*(e.deltaY<0?1.1:1/1.1)));if(zoom==1){panX=0;panY=0;}apply();},{passive:false});
var drag=null;
wrap.addEventListener('mousedown',function(e){drag=[e.clientX-panX,e.clientY-panY];});
window.addEventListener('mouseup',function(){drag=null;});
window.addEventListener('mousemove',function(e){if(!drag||zoom==1)return;panX=e.clientX-drag[0];panY=e.clientY-drag[1];apply();});
fit();
// The fit report: lower the type of a box that runs over, then mark it.
var bad=[];
function over(el){return el.scrollHeight>el.clientHeight+1;}
var boxes=document.querySelectorAll('.card,#middle');
for(var i=0;i<boxes.length;i++){var b=boxes[i];
  if(over(b)){b.classList.add('s1');}
  if(over(b)){b.classList.remove('s1');b.classList.add('s2');}
  if(over(b)){b.classList.add('over');bad.push(b.getAttribute('data-name'));}}
// The line report: sample each line and test every point against every card and the middle box.
var cross=[];
var rects=[];for(i=0;i<boxes.length;i++){var e=boxes[i];rects.push([e.getAttribute('data-name'),e.offsetLeft,e.offsetTop,e.offsetLeft+e.offsetWidth,e.offsetTop+e.offsetHeight]);}
var lines=document.querySelectorAll('svg path.ln');
for(i=0;i<lines.length;i++){var L=lines[i],len=L.getTotalLength();
  for(var t=6;t<len-6;t+=4){var p=L.getPointAtLength(t);
    for(var k=0;k<rects.length;k++){var r=rects[k];if(p.x>r[1]+1&&p.x<r[3]-1&&p.y>r[2]+1&&p.y<r[4]-1){cross.push((i+1)+' / '+r[0]);t=len;break;}}}}
var msg=[];
if(bad.length)msg.push(%(fit_fault)s+' '+bad.join(', '));
if(cross.length)msg.push(%(line_fault)s+' '+cross.join(', '));
document.body.setAttribute('data-fit',msg.length?'fault':'ok');
document.body.setAttribute('data-fit-report',msg.join(' | '));
if(msg.length){var f=document.getElementById('fit');f.textContent=msg.join(' · ');f.style.display='block';}
})();
"""


def card_html(key, card, rect, labels):
    group = GROUP_OF[key]
    color = COLORS[group][0]
    x1, y1, x2, y2 = rect
    return (f'<div class="card" data-name="{esc(labels[key])}" style="left:{x1:.0f}px;top:{y1:.0f}px;'
            f'width:{x2 - x1:.0f}px;height:{y2 - y1:.0f}px">'
            f'<div class="nm" style="color:{color}">{esc(labels[key])}</div>'
            f'<div class="hl">{esc(card.get("headline"))}</div>'
            f'<div class="bd">{esc(card.get("body"))}</div>'
            f'<div class="src">{esc(card.get("source"))}</div></div>')


def is_draft(status):
    return str(status or "").strip().lower().startswith("draft")


def build(company, out=None):
    company = Path(company)
    data = json.loads((company / "overview.json").read_text(encoding="utf-8"))
    labels = dict(DEFAULT_LABELS)
    labels.update(data.get("labels") or {})
    accent = data.get("accent") or ACCENT
    lay = layout(data)
    hashes = build_hashes(company)

    parts = []
    for group, (x, y, w, h) in PANELS.items():
        color, wash = COLORS[group]
        if group == "money":
            pill_top = h - 42
        else:
            pill_top = 12
        parts.append(f'<div class="panel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{wash}">'
                     f'<div class="pill" style="top:{pill_top}px;border-color:{color}">{esc(labels[group])}</div></div>')
    cards = data.get("cards", {})
    for key in CARD_KEYS:
        parts.append(card_html(key, cards.get(key, {}), lay["rects"][key], labels))

    dec = data.get("decision", {})
    opts = "".join(f'<li><b>{esc(o.get("option"))}</b> · {esc(labels["who_pays"])}: {esc(o.get("who_pays"))}</li>'
                   for o in dec.get("options", []))
    pulls = data.get("pulls", [])
    pl = "".join(f'<span><span class="num">{i + 1}</span>{esc(p.get("title"))}</span>' for i, p in enumerate(pulls))
    mx1, my1, mx2, my2 = MIDDLE
    parts.append(f'<div id="middle" data-name="{esc(labels["decision"])}" style="left:{mx1}px;top:{my1}px;'
                 f'width:{mx2 - mx1}px;height:{my2 - my1}px">'
                 f'<div class="eb">{esc(labels["decision"])}</div>'
                 f'<div class="what">{esc(dec.get("what"))}</div>'
                 f'<div class="meta">{esc(labels["who"])}: <b>{esc(dec.get("who"))}</b> · '
                 f'{esc(labels["by_when"])}: <b>{esc(dec.get("by_when"))}</b></div>'
                 f'<ul>{opts}</ul><div class="pl">{pl}</div></div>')

    svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true">']
    for i, path in enumerate(lay["paths"]):
        svg.append(f'<path class="ln" d="{path_d(path)}" fill="none" stroke="#fff" stroke-width="7" '
                   f'stroke-linejoin="round"/>')
        svg.append(f'<path class="ln" d="{path_d(path)}" fill="none" stroke="{accent}" stroke-width="3" '
                   f'stroke-linejoin="round"/>')
        for (x, y) in (path[0], path[-1]):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{accent}"/>')
    for i, d in enumerate(lay["dots"]):
        if d:
            svg.append(f'<circle cx="{d[0]:.1f}" cy="{d[1]:.1f}" r="14" fill="{accent}" stroke="#fff" stroke-width="3"/>'
                       f'<text x="{d[0]:.1f}" y="{d[1] + 5.5:.1f}" text-anchor="middle" font-size="16" '
                       f'font-weight="700" fill="#fff">{i + 1}</text>')
    svg.append("</svg>")

    stats = "".join(f'<div class="stat"><b>{esc(s.get("figure"))}</b><span>{esc(s.get("label"))}</span></div>'
                    for s in (data.get("stats") or [])[:2])
    status = data.get("status", "draft, not checked by a person")
    status_cls = "status" if is_draft(status) else "status ok"

    det = [f'<h2>{esc(labels["pulls"])}</h2>']
    for i, p in enumerate(pulls):
        det.append(f'<h3><span class="num">{i + 1}</span>{esc(p.get("title"))}</h3>'
                   f'<p>{esc(p.get("sentence"))}</p>'
                   f'<p><b>{esc(labels["who_pays"])}:</b> {esc(p.get("who_pays"))}</p>')
    det.append(f'<h2>{esc(labels["decision"])}</h2><p><b>{esc(dec.get("what"))}</b></p>'
               f'<p>{esc(labels["who"])}: {esc(dec.get("who"))}. {esc(labels["by_when"])}: {esc(dec.get("by_when"))}.</p><ul>')
    for o in dec.get("options", []):
        det.append(f'<li><b>{esc(o.get("option"))}</b> {esc(labels["cost"])}: {esc(o.get("cost"))} '
                   f'{esc(labels["who_pays"])}: {esc(o.get("who_pays"))}.</li>')
    det.append(f'</ul><p><b>{esc(labels["if_nobody"])}:</b> {esc(dec.get("if_nobody"))}</p>')
    det.append(f'<h2>{esc(labels["sources"])}</h2><p>{esc(data.get("sources"))}</p>'
               f'<p class="small">{esc(labels["evidence_date"])}: {esc(data.get("evidence_date"))}. '
               f'{esc(labels["status"])}: {esc(status)}.</p><p class="small">{esc(labels["draft_note"])}</p>')

    lang = esc(data.get("language", "en"))
    title = esc(data.get("title"))
    css = CSS % {"page": PAGE, "ink": INK, "gray": GRAY, "w": W, "h": H, "accent": accent}
    script = SCRIPT % {"w": W, "h": H, "fit_fault": json.dumps(labels["fit_fault"]),
                       "line_fault": json.dumps(labels["line_fault"])}
    page = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data.get("company"))} · {title}</title>
<!-- build: {json.dumps(hashes, sort_keys=True)} -->
<style>{css}</style>
</head>
<body>
<header><div><p class="co">{esc(data.get("company"))}</p><h1>{title}</h1></div><div class="stats">{stats}</div></header>
<div class="bar"><span class="{status_cls}">{esc(labels["status"])}: {esc(status)}</span>
<span>{esc(labels["evidence_date"])}: {esc(data.get("evidence_date"))}</span>
<span style="flex:1"></span><span>{esc(labels["zoom_hint"])}</span>
<button id="zout" aria-label="zoom out">&minus;</button><button id="zin" aria-label="zoom in">+</button><button id="zfit" aria-label="fit">&#9633;</button></div>
<div id="fit"></div>
<div id="wrap"><div id="stage">
{"".join(parts)}
{"".join(svg)}
</div></div>
<main>{"".join(det)}</main>
<script>{script}</script>
</body>
</html>
"""
    out = Path(out) if out else company / "system_overview.html"
    out.write_text(page, encoding="utf-8")
    return out, lay


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("company", help="the company folder that holds overview.json and chapters/")
    ap.add_argument("--out", help="the page to write; default {company}/system_overview.html")
    a = ap.parse_args()
    company = Path(a.company)
    if not (company / "overview.json").exists():
        print(f"no overview.json in {company}")
        sys.exit(2)
    try:
        out, lay = build(company, a.out)
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        print(f"overview.json is not in the expected form ({e}); run check_overview.py first")
        sys.exit(2)
    faults = geometry_faults(lay)
    print(f"wrote {out}")
    for f in faults:
        print("FAULT " + f)
    sys.exit(2 if faults else 0)


if __name__ == "__main__":
    main()
