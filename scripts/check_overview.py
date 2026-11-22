#!/usr/bin/env python3
"""Check a system overview: the data file overview.json and the page system_overview.html.

    python check_overview.py {company}           check overview.json, and the page when it exists
    python check_overview.py {company} --final   also refuse a status that still says draft

The checks:
  1. overview.json has every part, in the right form and within the length limits.
  2. Each pull quotes one Evidence line from the chapter of each of its two cards.
  3. Every number sits in a sourced Evidence line of the right chapter. A year alone is exempt.
  4. The page was built from the current overview.json and the current chapters.
  5. The page loads nothing from anywhere: no link, no source file, no request from its script.
  6. No line crosses a card or the middle box, no two lines share a stretch, every number sits clear
     of the other lines, and the lines cross each other at most three times.

Python 3 and its standard library only. Prints one line per fault and exits 2 when there is any.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_overview as bo  # noqa: E402

CHAPTERS = {
    "market": ["01", "10"], "customers": ["02"], "competitors": ["03"],
    "assets": ["04"], "capabilities": ["05"], "limits": ["06", "07"],
    "invests": ["08"], "cuts": ["08"], "hires": ["08"],
    "story": ["09"], "signal": ["09"],
}
LIMITS = {"headline": 110, "body": 300, "source": 80}
SOURCE = re.compile(r"\[[^\]]*\b(?:19|20)\d\d\b[^\]]*\]")
NUMBER = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)*")
YEAR = re.compile(r"^(?:19|20)\d\d$")
SCORE = re.compile(r"\b(out of (?:5|10)|world[- ]class|best[- ]in[- ]class|strengths|weaknesses|SWOT)\b", re.I)
ADVICE = re.compile(r"\b(should|ought to|recommend(?:s|ed|ation)?|we suggest|it is advisable)\b", re.I)
REQUEST = [
    (re.compile(r"https?:", re.I), "an http address"),
    (re.compile(r"""["'(\s=]//[\w-]"""), "an address that starts with //"),
    (re.compile(r"\b(?:src|srcset)\s*=", re.I), "a src attribute"),
    (re.compile(r"""\bhref\s*=\s*["']?(?!#)""", re.I), "a link"),
    (re.compile(r"url\s*\(", re.I), "a CSS url()"),
    (re.compile(r"@import", re.I), "a CSS @import"),
    (re.compile(r"<\s*(?:link|iframe|object|embed|base|img|video|audio|source)\b", re.I), "a tag that loads a file"),
    (re.compile(r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts)\b"), "a script request"),
    (re.compile(r"\bimport\s*\("), "a script import"),
    (re.compile(r"new\s+Image\b"), "a script image load"),
]


def norm_number(n):
    """'5,323' and '5323' are one number; '3.8' stays '3.8'; a comma decimal '3,8' becomes '3.8'."""
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", n):
        return n.replace(",", "")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", n):
        return n.replace(".", "").replace(",", ".")
    if re.fullmatch(r"\d+,\d{1,2}", n):
        return n.replace(",", ".")
    return n


def numbers(text):
    return {norm_number(n) for n in NUMBER.findall(text or "") if not YEAR.match(n)}


def sentences(text):
    text = re.sub(r"\s+", " ", (text or "").strip())
    text = re.sub(r"\[INFERRED\]|\[ESTIMATE\]", "", text)
    return [s for s in re.split(r"(?:(?<=[.!?])|(?<=[.!?][\"”’']))\s+(?=[A-ZÀ-ɏ\"“(])", text) if s.strip()]


def section(text, name):
    m = re.search(r"^##\s+" + re.escape(name) + r"\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def evidence_lines(company, prefixes):
    """The Evidence lines that end on a dated source, from the chapters whose names start with these prefixes."""
    lines = []
    for p in sorted((Path(company) / "chapters").glob("*.md")):
        if p.name[:2] in prefixes:
            text = p.read_text(encoding="utf-8")
            ev = section(text, "Evidence") or text
            lines += [l for l in ev.splitlines() if SOURCE.search(l)]
    return lines


def plain(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", re.sub(r"\*\*", "", s)).strip().lower()


def check_numbers(where, text, bank, faults):
    have = set()
    for l in bank:
        have |= numbers(SOURCE.sub(lambda m: "", l)) | numbers(l)
    for n in sorted(numbers(text)):
        if n not in have:
            faults.append(f"{where}: the number {n} sits in no sourced Evidence line of its chapters")


def need(where, value, faults, limit=None):
    if not isinstance(value, str) or not value.strip():
        faults.append(f"{where}: missing")
        return False
    if limit and len(value) > limit:
        faults.append(f"{where}: {len(value)} characters, the limit is {limit}")
    return True


def check_data(company, data, final):
    faults = []
    chapters = Path(company) / "chapters"
    if not chapters.is_dir() or len(list(chapters.glob("*.md"))) < 10:
        faults.append(f"{chapters}: the ten chapters are missing; run the system analysis first")
        return faults
    all_lines = evidence_lines(company, {f"{i:02d}" for i in range(1, 11)})

    for key in ("company", "title", "evidence_date", "sources", "status"):
        need(key, data.get(key), faults, 160 if key == "title" else None)
    if data.get("title") and len(sentences(data["title"])) != 1:
        faults.append("title: must be one sentence")
    status = str(data.get("status", ""))
    if status and not (status.lower().startswith("draft") or status.lower().startswith("checked by")):
        faults.append("status: must start with 'draft' or 'checked by {name} on {date}'")
    if final and bo.is_draft(status):
        faults.append("status: still draft; a person must check the page and change the status first")

    stats = data.get("stats") or []
    if not isinstance(stats, list) or len(stats) > 2:
        faults.append("stats: zero to two figures")
        stats = []
    for i, s in enumerate(stats):
        need(f"stats {i + 1} figure", s.get("figure"), faults, 16)
        need(f"stats {i + 1} label", s.get("label"), faults, 50)
        check_numbers(f"stats {i + 1}", s.get("figure", "") + " " + s.get("label", ""), all_lines, faults)

    cards = data.get("cards") or {}
    for key in bo.CARD_KEYS:
        c = cards.get(key)
        if not isinstance(c, dict):
            faults.append(f"cards.{key}: missing")
            continue
        for part, limit in LIMITS.items():
            need(f"cards.{key}.{part}", c.get(part), faults, limit)
        if c.get("headline") and len(sentences(c["headline"])) != 1:
            faults.append(f"cards.{key}.headline: must be one sentence")
        if c.get("body") and not 1 <= len(sentences(c["body"])) <= 3:
            faults.append(f"cards.{key}.body: one to three sentences, found {len(sentences(c['body']))}")
        text = f"{c.get('headline', '')} {c.get('body', '')}"
        check_numbers(f"cards.{key}", text, evidence_lines(company, set(CHAPTERS[key])), faults)
    for key in cards:
        if key not in bo.CARD_KEYS:
            faults.append(f"cards.{key}: not a card; the cards are {', '.join(bo.CARD_KEYS)}")

    pulls = data.get("pulls") or []
    if not 2 <= len(pulls) <= 3:
        faults.append(f"pulls: two or three, found {len(pulls)}")
    titles = set()
    for i, p in enumerate(pulls):
        w = f"pulls {i + 1}"
        need(f"{w} title", p.get("title"), faults, 40)
        need(f"{w} sentence", p.get("sentence"), faults, 300)
        need(f"{w} who_pays", p.get("who_pays"), faults, 200)
        t = plain(p.get("title", ""))
        if t in titles:
            faults.append(f"{w}: the title repeats another pull's title")
        titles.add(t)
        a, b = p.get("from"), p.get("to")
        for side in (a, b):
            if side not in bo.CARD_KEYS:
                faults.append(f"{w}: '{side}' is not a card")
        if a == b:
            faults.append(f"{w}: from and to must be two different cards")
        bank = []
        for side, fact in ((a, "from_fact"), (b, "to_fact")):
            if side not in bo.CARD_KEYS:
                continue
            lines = evidence_lines(company, set(CHAPTERS[side]))
            bank += lines
            q = p.get(fact)
            if need(f"{w} {fact}", q, faults, 200):
                if not any(plain(q) in plain(l) for l in lines):
                    faults.append(f"{w} {fact}: the quote is not in a sourced Evidence line of the "
                                  f"'{side}' chapter: \"{q}\"")
        check_numbers(w, f"{p.get('sentence', '')} {p.get('who_pays', '')}", bank, faults)

    dec = data.get("decision") or {}
    need("decision.who", dec.get("who"), faults, 80)
    need("decision.what", dec.get("what"), faults, 160)
    need("decision.by_when", dec.get("by_when"), faults, 60)
    need("decision.if_nobody", dec.get("if_nobody"), faults, 300)
    opts = dec.get("options") or []
    if not 2 <= len(opts) <= 3:
        faults.append(f"decision.options: two or three, found {len(opts)}")
    for i, o in enumerate(opts):
        need(f"decision option {i + 1} option", o.get("option"), faults, 80)
        need(f"decision option {i + 1} cost", o.get("cost"), faults, 200)
        need(f"decision option {i + 1} who_pays", o.get("who_pays"), faults, 40)
    dec_text = " ".join([str(dec.get(k, "")) for k in ("who", "what", "by_when", "if_nobody")] +
                        [str(o.get(k, "")) for o in opts for k in ("option", "cost", "who_pays")])
    check_numbers("decision", dec_text, all_lines, faults)

    whole = json.dumps(data, ensure_ascii=False)
    for m in SCORE.finditer(whole):
        faults.append(f"the data file scores the company: '{m.group(0)}'")
    for m in ADVICE.finditer(whole):
        faults.append(f"the data file gives advice: '{m.group(0)}'")
    return faults


def check_page(company, data):
    faults = []
    page = Path(company) / "system_overview.html"
    if not page.exists():
        return faults, False
    text = page.read_text(encoding="utf-8")
    m = re.search(r"<!-- build: (\{.*?\}) -->", text)
    if not m:
        faults.append("page: no build record; build it again")
    else:
        if json.loads(m.group(1)) != bo.build_hashes(company):
            faults.append("page: built from an older overview.json or older chapters; build it again")
    for rx, what in REQUEST:
        for hit in rx.finditer(text):
            line = text.count("\n", 0, hit.start()) + 1
            faults.append(f"page line {line}: {what} ('{hit.group(0).strip()}'); the page must load nothing")
    faults += ["page: " + f for f in bo.geometry_faults(bo.layout(data))]
    return faults, True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("company")
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    company = Path(a.company)
    src = company / "overview.json"
    if not src.exists():
        print(f"FAULT {src}: missing")
        sys.exit(2)
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAULT {src}: not valid JSON ({e})")
        sys.exit(2)
    faults = check_data(company, data, a.final)
    page_faults, has_page = check_page(company, data)
    faults += page_faults
    for f in faults:
        print("FAULT " + f)
    if not faults:
        print(f"ok: overview.json{' and system_overview.html' if has_page else ''} pass every check"
              f"{'' if has_page else '; the page is not built yet'}")
    sys.exit(2 if faults else 0)


if __name__ == "__main__":
    main()
