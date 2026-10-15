"""Builds journal.html (a printable 5.5x8.5in Guided SOAR journal) from index.html.

Reuses index.html's styles and card builders so the journal always matches the site.
Run:  python3 tools/build_journal.py   (then open journal.html and print, or use tools/journal_pdf.py)

Dwell Skills journal:  BOOK=dwell python3 tools/build_journal.py   -> dwell-journal.html, built from dwell.html.
Same book, but every study is a two-page spread: the Dwell card on the left, its Reflect (Learn + Live) page on the right.
"""
import os, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DWELL = os.environ.get("BOOK", "soar").lower() == "dwell"
src = (ROOT / ("dwell.html" if DWELL else "index.html")).read_text()

head_links = "\n".join(l for l in src.split("\n")[:9] if "fonts.g" in l or "preconnect" in l)
style = src[src.index("<style>") + 7 : src.index("</style>")]
js = src[src.index("<script>", src.index("</style>")) + 8 :]
builders = js[js.index("    // ---------- shared caption builder") : js.index("    document.querySelectorAll('#leaderPage")]

BLANKS = 12   # Guided SOAR: one card per page
STUDIES = 12  # Dwell: one card + Reflect spread per study (32 pages total)

# v1 keeps it simple: cover -> name page -> leader guide. These pages are saved for a later version.
INCLUDE_WHY = False
INCLUDE_RESOURCES = False

# Inside-cover QR code. Set this to your resources page URL and rebuild; until then a placeholder box prints.
COVER_STYLE = "light"   # set COVER_TINT below for a soft single-color pop on the light cover
COVER_TINT = __import__("os").environ.get("COVER_TINT", "")   # "", "teal", "orchid" or "blue"
# "light" prints cleanly on toner printers; "dark" is the original night-grey cover
RESOURCES_URL = "https://dwellmethod.vercel.app/guidedsoar"   # Guided SOAR landing page on the Dwell site
if DWELL:
    RESOURCES_URL = "https://dwellstudy.com"

RESOURCES = [
    ("How to Read the Bible", "BibleProject video series on reading the Bible well: genre, story, poetry, and more.",
     "Scripture &middot; Observation", "https://www.youtube.com/playlist?list=PLH0Szn1yYNedn4FbBMMtOlGN-BPLQ54IH", "YouTube &middot; BibleProject"),
    ("Old Testament Overviews", "A short video for every Old Testament book: its big ideas, structure, and flow.",
     "Scripture", "https://www.youtube.com/playlist?list=PLH0Szn1yYNeeVFodkI9J_WEATHQCwRZ0u", "YouTube &middot; BibleProject"),
    ("New Testament Overviews", "A short video for every New Testament book: who wrote it, why, and how it fits.",
     "Scripture", "https://www.youtube.com/playlist?list=PLH0Szn1yYNecanpQqdixWAm3zHdhY2kPR", "YouTube &middot; BibleProject"),
    ("Bible Hub", "Free commentaries, cross-references, and original-language word studies for any verse.",
     "Observation", "https://biblehub.com", "biblehub.com"),
]

def qr_svg(url):
    import segno, io
    buf = io.BytesIO()
    segno.make(url, error='m').save(buf, kind='svg', scale=1, border=0, xmldecl=False, svgns=True, dark='#111', nl=False)
    import re
    svg = buf.getvalue().decode()
    w = re.search(r'width="(\d+)"', svg).group(1); h = re.search(r'height="(\d+)"', svg).group(1)
    svg = re.sub(r' (width|height)="\d+"', '', svg, count=2)
    if 'viewBox' not in svg:
        svg = svg.replace('<svg ', f'<svg viewBox="0 0 {w} {h}" ', 1)
    return svg.replace('<svg ', '<svg class="qr" preserveAspectRatio="xMidYMid meet" shape-rendering="crispEdges" ', 1)

# very light tints of the wristband colors: (sky top, sky bottom, sun, (far ridge, near ridge), back cover)
TINTS = {
    "teal":   {"sky": ("#ffffff", "#e3f1f1"), "sun": "#cfe6e6", "ridges": ("#a9cfd0", "#74a9ab"), "back": "#e3f1f1"},
    "orchid": {"sky": ("#ffffff", "#f5e6f2"), "sun": "#ecd4e7", "ridges": ("#d7b3cf", "#ad83a6"), "back": "#f5e6f2"},
    "blue":   {"sky": ("#ffffff", "#e7eef5"), "sun": "#d5e1ec", "ridges": ("#b5c8da", "#8aa3bb"), "back": "#e7eef5"},
}
def mountains_svg(light=False, cover_light=False):
    """Sunset-style landscape: the circle sits like a setting sun, half-hidden by hazy ridges
    that get darker toward the front (inspired by a mountain sunset photo)."""
    import random
    W, H = 396, 612
    def ridge(seed, base, peaks, rough, step=(4, 9)):
        rnd = random.Random(seed)
        pts, x = [], -10
        while x <= W + 10:
            y = base
            for (px, ph, pw) in peaks:
                y -= ph * max(0.0, 1 - abs(x - px) / pw) ** 1.3
            y += rnd.uniform(-rough, rough)
            pts.append((x, y)); x += rnd.uniform(*step)
        return pts
    layers = [
        # far ridge: crosses the lower part of the circle and climbs to the right, like the photo
        ("#28292d", ridge(5, 430, [(150, 18, 120), (250, 52, 150), (330, 62, 120)], 1.6)),
        # near ridge: darkest, low rolling hills in front
        ("#1f2023", ridge(9, 505, [(60, 22, 110), (200, 14, 120), (345, 38, 130)], 1.2)),
    ]
    if cover_light:   # mid greys that print evenly and keep the white edge from showing
        far, near = TINTS.get(COVER_TINT, {}).get("ridges", ("#b3b6bd", "#868a92"))
        layers = [(c, pts) for c, (_, pts) in zip((far, near), layers)]
    if light:   # same ranges, pale and lower, for the grey reference pages
        layers = [(c, pts) for c, (_, pts) in zip(("#d9dbe0", "#cfd2d8"), layers)]
    paths = []
    for color, pts in layers:
        d = f"M-10 {H} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts) + f" L{W + 10} {H} Z"
        paths.append(f'<path d="{d}" fill="{color}"/>')
    cls, g = ("ref-mtn", ' transform="translate(0 120)"') if light else ("cover-mtn", "")
    return f'<svg class="{cls}" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true"><g{g}>{"".join(paths)}</g></svg>'

def resources_qr():
    if not RESOURCES_URL:   # nothing on the inside cover until the resources page exists
        return ""
    code = qr_svg(RESOURCES_URL)
    return f'''<div class="ic-res">{code}
    <div class="ic-res-h">Resources</div>
    <div class="ic-res-sub">Scan for more tools for Bible study.</div></div>'''

def resources_page():
    cards = []
    for title, desc, helps, url, src in RESOURCES:
        cards.append(f'''<div class="qr-card">{qr_svg(url)}<div class="qr-body">
      <div class="qr-t">{title}</div><p>{desc}</p>
      <div class="qr-meta"><span class="why-tag">{helps}</span><span class="qr-src">{src}</span></div></div></div>''')
    return "".join(cards)

OT = [
    ("Law", ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]),
    ("History", ["Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
                 "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther"]),
    ("Poetry &amp; Wisdom", ["Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Songs"]),
    ("Major Prophets", ["Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel"]),
    ("Minor Prophets", ["Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum",
                        "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"]),
]
NT = [
    ("Gospels", ["Matthew", "Mark", "Luke", "John"]),
    ("History", ["Acts"]),
    ("Paul&rsquo;s Letters", ["Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
                        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
                        "1 Timothy", "2 Timothy", "Titus", "Philemon"]),
    ("General Letters", ["Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude"]),
    ("Prophecy", ["Revelation"]),
]
assert sum(len(b) for _, b in OT) == 39 and sum(len(b) for _, b in NT) == 27

SHADES = ["g1", "g2", "g3", "g4", "g5"]  # black → white

# chapter counts give each spine a width that hints at how long the book is
CHAPTERS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34, "Joshua": 24, "Judges": 21,
    "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24, "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36,
    "Ezra": 10, "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31, "Ecclesiastes": 12,
    "Song of Songs": 8, "Isaiah": 66, "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14,
    "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephaniah": 3,
    "Haggai": 2, "Zechariah": 14, "Malachi": 4, "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
    "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6, "Ephesians": 6, "Philippians": 4,
    "Colossians": 4, "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3,
    "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5, "2 John": 1, "3 John": 1,
    "Jude": 1, "Revelation": 22,
}

def shelves(groups, split_at):
    flat = [(name, SHADES[i]) for i, (_, books) in enumerate(groups) for name in books]
    rows = [flat[:split_at], flat[split_at:]]
    out = []
    for r, row in enumerate(rows):
        spines = []
        for k, (name, shade) in enumerate(row):
            h = 84 + ((k * 37 + r * 13 + len(name) * 5) % 6) * 3   # gentle, repeatable height variety
            grow = 1 + CHAPTERS[name] ** 0.5 / 3                    # longer books, wider spines
            style = f"height:{h}%;flex-grow:{grow:.2f}"
            spines.append(f'<div class="spine {shade}" style="{style}"><span>{name}</span></div>')
        out.append('<div class="shelf">' + "".join(spines) + "</div>")
    return "".join(out)

def legend(groups):
    return "".join(f'<span class="key"><i class="{SHADES[i]}"></i>{name} <b>{len(b)}</b></span>'
                   for i, (name, b) in enumerate(groups))

# Big-story timeline. Icons are cut from the timeline graphic (assets/timeline/*.png).
# No dates on purpose: many are debated, and the story is the point.
TIMELINE = [
    ("creation", "Creation", "Genesis 1&ndash;2"),
    ("sin", "Sin", "Genesis 3&ndash;11"),
    ("abraham", "Abraham", "Genesis 12&ndash;50 &middot; Job is often set here"),
    ("exodus", "Exodus", "Exodus &middot; Leviticus &middot; Numbers &middot; Deuteronomy"),
    ("land", "Promised Land", "Joshua &middot; Judges &middot; Ruth"),
    ("kings", "Kings", "1&ndash;2 Samuel &middot; 1&ndash;2 Kings &middot; 1&ndash;2 Chronicles &middot; Psalms&ndash;Song of Songs"),
    ("exile", "Exile &amp; Return", "Ezra &middot; Nehemiah &middot; Esther &middot; the Prophets"),
    ("silence", "Silence", "Between the Testaments"),
    ("birth", "Jesus&rsquo; Birth", "Matthew 1&ndash;2 &middot; Luke 1&ndash;2"),
    ("cross", "Life, Death &amp; Resurrection", "Matthew &middot; Mark &middot; Luke &middot; John"),
    ("church", "Church", "Acts &middot; Romans&ndash;Jude"),
    ("return", "Jesus&rsquo; Return", "Revelation"),
    ("restoration", "New Creation", "Revelation 21&ndash;22"),
]

def timeline():
    items = []
    for icon, title, books in TIMELINE:
        small = " small" if icon == "silence" else ""
        items.append(f'<li class="st"><span class="st-ic{small}"><img src="assets/timeline/{icon}.png" alt=""></span>'
                     f'<div><div class="what">{title}</div><div class="books">{books}</div></div></li>')
    return '<ol class="tl2">' + "".join(items) + "</ol>"

# Horizontal timeline that runs across the back spread: the line leaves the left page at the
# gutter and picks up again on the right page, so the story reads as one piece.
SPLIT = next(i for i, t in enumerate(TIMELINE) if t[0] == "birth")
def timeline_half(stops, side):
    W, LBL, PAD = 356, 88, 20                       # content width, label width, inset of end stops
    stops = [t for t in stops if t[0] != "silence"]   # the gap at the gutter says it on its own
    n = len(stops)
    first = PAD if side == "ot" else 60               # NT starts a little in, so the line visibly arrives
    last = W - 50 if side == "ot" else W - PAD
    out = []
    for i, (icon, title, books) in enumerate(stops):
        x = first + i * (last - first) / (n - 1)
        left = min(max(x - LBL / 2, 0), W - LBL)
        align = "left" if left == 0 else "right" if left == W - LBL else "center"
        pos = "up" if i % 2 == 0 else "down"
        small = " small" if icon == "silence" else ""
        out.append(f'<span class="hs-ic{small}" style="left:{x:.1f}pt"><img src="assets/timeline/{icon}.png" alt=""></span>'
                   f'<span class="hs-stem {pos}{small}" style="left:{x:.1f}pt"></span>'
                   f'<div class="hs-lbl {pos}" style="left:{left:.1f}pt;text-align:{align}">'
                   f'<div class="what">{title}</div></div>')
    line = 'left:20pt;right:-20pt' if side == "ot" else 'left:-20pt;right:20pt'
    return f'<div class="tlh {side}"><span class="hs-line" style="{line}"></span>{"".join(out)}</div>'

JOURNAL_CSS = r"""
  @page { size: 5.5in 8.5in; margin: 0; }
  html, body { margin: 0; padding: 0; background: #fff; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .page { width: 396pt; height: 612pt; position: relative; overflow: hidden; page-break-after: always; break-after: page; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
  .page:last-child { page-break-after: auto; break-after: auto; }
  /* page numbers on every inside page (not the front or back cover) so printed sheets are easy to check */
  body { counter-reset: pg; }
  .page { counter-increment: pg; }
  section.page:not(:first-of-type):not(:last-of-type)::after { content: counter(pg); position: absolute; left: 0; right: 0; bottom: 7pt; text-align: center; font-family: 'DM Sans', sans-serif; font-size: 6.5pt; font-weight: 500; color: #8e929b; z-index: 3; }
  .page .mini-card { margin: 0; }
  @media screen { body { background: #9aa0a6; } .page { margin: 16px auto; box-shadow: 0 4px 18px rgba(0,0,0,.25); background: #fff; } }

  /* cover */
  .cover { background: #2e2f33; }
  /* cover reuses the blank card so the circle sits exactly where it does on every template */
  .cover-card .mini-brand, .cover-card .mini-box { visibility: hidden; }
  .cover-card .mini-circle { background: #47494f; border-color: #47494f; }
  .cover-card .mini-label { color: #fff; }
  .cover-card .mini-circle { gap: 9pt; padding: 0; }
  .cover-logo { height: 40pt; width: auto; display: block; }
  .cover-word { font-family: var(--display), sans-serif; font-weight: 600; font-size: 11pt; letter-spacing: 5pt; padding-left: 5pt; color: #fff; line-height: 1; }
  .cover-circle { width: 176pt; height: 176pt; border-radius: 50%; background: #47494f; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 30pt; }
  .cover-circle .lbl { font-family: var(--display), sans-serif; font-weight: 700; font-size: 15pt; color: #fff; letter-spacing: 0.3pt; }
  .back { background: #2e2f33; }
  .cover { background: linear-gradient(180deg, #2a2b2f 0%, #2e2f33 45%, #3a3b40 72%); }
  .cover-mtn { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; }
  .cover .mini-card { position: relative; z-index: 1; }
  .inside-back .ic-res { bottom: 20pt; }
  .inside-back .ic-res .qr { width: 130pt; height: 130pt; }
  .inside-back .ic-res-h { font-size: 20pt; }
  .inside-back .ic-res-sub { font-size: 10pt; }
  /* lined notes pages */
  .notes-page .inner { display: flex; flex-direction: column; }
  .notes-page .rules { flex: 1; margin-top: 8pt; background-image: repeating-linear-gradient(180deg, transparent 0 21.4pt, #c9ccd2 21.4pt 22.2pt); }
  /* light cover variant */
  .cover.cover-light { background: linear-gradient(180deg, #ffffff 0%, #f3f4f6 50%, #e6e8ec 78%); }
  .cover-light .cover-card .mini-circle { background: #d7d9de; border-color: #d7d9de; }
  .back.back-light { background: #e6e8ec; }
  {tint_css}

  /* inside cover */
  .inside-cover { background: #e4e6ea; }
  .ic-circle-wrap { position: relative; flex: 1; }
  .inside-card .mini-brand, .inside-card .mini-box { visibility: hidden; }
  .owner { position: absolute; left: 20pt; right: 20pt; bottom: 20pt; background: #fff; border: 3pt solid #111; border-radius: 12pt; padding: 12pt 16pt 11pt; height: 118pt; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; }
  .owner-h { font-family: var(--display), sans-serif; font-weight: 700; font-size: 11pt; }
  .owner-line { display: flex; align-items: flex-end; gap: 8pt; }
  .owner-line span { font-family: var(--display), sans-serif; font-weight: 600; font-size: 8pt; letter-spacing: 0.5pt; line-height: 1; padding-bottom: 2pt; width: 38pt; text-align: right; }
  .owner-line i { flex: 1; border-bottom: 1.3pt solid #111; }
  .owner-note { font-size: 7pt; color: #4a5568; }

  /* content pages */
  .inner { width: 356pt; height: 572pt; display: flex; flex-direction: column; font-family: 'DM Sans', Arial, sans-serif; color: #111; }
  .ptitle { font-family: var(--display), sans-serif; font-weight: 700; font-size: 20pt; line-height: 1; margin: 2pt 0 2pt; }
  .psub { font-size: 9pt; color: #4a5568; margin: 0 0 10pt; }

  /* why guided soar */
  .why { display: flex; flex-direction: column; gap: 7pt; flex: 1; margin-top: 2pt; min-height: 0; }
  .why-row { flex: 1; display: flex; align-items: center; background: #fff; border: 2.2pt solid #111; border-radius: 10pt; padding: 8pt 12pt 8pt 11pt; }
  .why-row.center { background: #fff; border-width: 3pt; }
  .why-tag { display: inline-block; font-family: var(--display), sans-serif; font-weight: 600; font-size: 7.5pt; letter-spacing: 1.4pt; text-transform: uppercase; color: #111; border: 1.4pt solid #111; border-radius: 99pt; padding: 2pt 8pt 1.6pt; margin-bottom: 5pt; }
  .why-tag.dark { background: #111; color: #fff; }
  .why-row.center { background: #fff; }
  .why-badge { flex: none; width: 26pt; height: 26pt; display: flex; align-items: center; justify-content: center; font-family: var(--display), sans-serif; font-weight: 700; font-size: 22pt; line-height: 1; color: #111; }
  .why-badge.ring { box-sizing: border-box; border: 3pt solid #111; border-radius: 50%; width: 24pt; height: 24pt; margin: 1pt; }
  .why-t { font-family: var(--display), sans-serif; font-weight: 600; font-size: 12.5pt; line-height: 1.15; margin: 0 0 4pt; }
  .why-row p { margin: 0; font-size: 9.5pt; line-height: 1.4; color: #2d3138; }

  /* why we're here (retired) */
  .eyebrow { font-family: var(--display), sans-serif; font-weight: 600; font-size: 8pt; letter-spacing: 2pt; text-transform: uppercase; color: #4a5568; margin-bottom: 3pt; }
  .lede { font-size: 10pt; line-height: 1.45; margin: 8pt 0 14pt; }
  .lede b { font-weight: 700; }
  .sec-h { font-family: var(--display), sans-serif; font-weight: 700; font-size: 12.5pt; margin: 4pt 0 8pt; }
  .win { display: flex; gap: 8pt; border: 2.2pt solid #111; border-radius: 10pt; padding: 10pt 11pt 11pt; margin-bottom: 8pt; }
  .win .num { flex: none; width: 19pt; height: 19pt; border-radius: 50%; background: #111; color: #fff; font-family: var(--display), sans-serif; font-weight: 700; font-size: 9.5pt; display: flex; align-items: center; justify-content: center; }
  .win-t { font-weight: 700; font-size: 9.8pt; line-height: 1.32; margin-bottom: 6pt; }
  .win-p { font-size: 8.8pt; line-height: 1.4; margin: 0 0 6pt; }
  .win-p b { font-weight: 700; }
  .chips { display: flex; flex-wrap: wrap; gap: 3pt; }
  .chips span { font-size: 8.2pt; background: #e4e6ea; border-radius: 99pt; padding: 1.5pt 6pt; }
  .tq-h { font-size: 7.6pt; font-weight: 700; letter-spacing: 0.8pt; text-transform: uppercase; color: #4a5568; margin: 6pt 0 2pt; }
  .tq { margin: 0; padding-left: 12pt; font-size: 9pt; line-height: 1.45; }
  .goals { margin: 0; padding-left: 13pt; font-size: 9.4pt; line-height: 1.42; }
  .goals li { margin-bottom: 4pt; }

  /* reference-page header on cards */
  .ref-head { font-family: 'DM Sans', Arial, sans-serif; color: #111; }
  .ref-head .psub { margin-bottom: 8pt; }

  /* reference pages get a light grey page so they stand apart from journaling pages */
  .ref-page { background: #e4e6ea; }
  .ref-mtn { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 0; }
  .ref-page > .inner, .ref-page > .mini-card, .inside-cover > .owner { position: relative; z-index: 1; }
  .inside-cover > .owner { position: absolute; }
  .ref-page .win, .ref-page .case { background: #fff; }
  ol.tl { background: transparent; }

  /* single QR on the inside cover */
  .ic-res { position: absolute; left: 20pt; right: 20pt; top: 20pt; bottom: 158pt; z-index: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
  .ic-res .qr, .qr-ph { width: 96pt; height: 96pt; background: #fff; padding: 8pt; border-radius: 8pt; box-sizing: content-box; margin-bottom: 10pt; }
  .qr-ph { display: flex; align-items: center; justify-content: center; border: 1.5pt dashed #8e929b; padding: 6.5pt; font-family: 'DM Sans', sans-serif; font-size: 8pt; color: #8e929b; letter-spacing: 0.5pt; text-transform: uppercase; line-height: 1.4; }
  .ic-res-h { font-family: var(--display), sans-serif; font-weight: 700; font-size: 16pt; line-height: 1; }
  .ic-res-sub { font-family: 'DM Sans', sans-serif; font-size: 8.5pt; color: #4a5568; margin-top: 4pt; }

  /* QR resources page */
  .qr-list { flex: 1; display: flex; flex-direction: column; gap: 6pt; margin-top: 6pt; }
  .qr-card { flex: 1; display: flex; align-items: center; gap: 16pt; padding: 4pt 2pt; border-bottom: 1.2pt solid #b9bdc4; }
  .qr-card:last-child { border-bottom: none; }
  .qr-card .qr { width: 74pt; height: 74pt; flex: none; background: #fff; padding: 6pt; border-radius: 6pt; box-sizing: content-box; }
  .qr-t { font-family: var(--display), sans-serif; font-weight: 700; font-size: 13pt; line-height: 1.1; margin-bottom: 4pt; }
  .qr-body p { margin: 0 0 7pt; font-size: 9pt; line-height: 1.4; color: #2d3138; }
  .qr-meta { display: flex; align-items: center; gap: 8pt; flex-wrap: wrap; }
  .qr-meta .why-tag { margin: 0; font-size: 6.6pt; }
  .qr-src { font-size: 7.5pt; color: #4a5568; }

  /* resources card */
  .res-title { font-family: var(--display), sans-serif; font-weight: 700; font-size: 16pt; line-height: 1; padding-top: 4pt; }
  .mini-prompts.res { font-size: 9.6pt; }
  .mini-prompts.res ul { margin-bottom: 4pt; }
  .mini-prompts.res li { margin-bottom: 2.5pt; }
  .res-h { font-family: var(--display), sans-serif; font-weight: 600; font-size: 7.5pt; letter-spacing: 1pt; text-transform: uppercase; color: #111; margin: 0 0 2pt; }

  /* bookshelves */
  .case { border: 3pt solid #111; border-radius: 10pt; padding: 6pt 7pt 0; margin-bottom: 6pt; }
  .case-h { display: flex; justify-content: space-between; align-items: baseline; font-family: var(--display), sans-serif; font-weight: 700; font-size: 11pt; margin: 0 2pt 4pt; }
  .case-h small { font-family: 'DM Sans', sans-serif; font-weight: 500; font-size: 8pt; color: #4a5568; }
  .shelf { height: 102pt; display: flex; align-items: flex-end; gap: 1.2pt; border-bottom: 3.5pt solid #111; margin-bottom: 7pt; padding: 0 1pt; }
  .spine { flex: 1 1 0; min-width: 11pt; position: relative; box-sizing: border-box; border: 1pt solid #111; border-bottom: none; border-radius: 1.5pt 1.5pt 0 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  /* bound-book detail: a pair of bands near the head and foot of every spine */
  .spine::before, .spine::after { content: ''; position: absolute; left: 0; right: 0; height: 2.2pt; border-top: 0.7pt solid currentColor; border-bottom: 0.7pt solid currentColor; opacity: 0.55; }
  .spine::before { top: 6pt; } .spine::after { bottom: 6pt; }
  .spine span { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 6.3pt; font-weight: 600; white-space: nowrap; letter-spacing: 0.1pt; }
  .g1 { background: #111; color: #fff; } .g2 { background: #4a4d55; color: #fff; } .g3 { background: #9a9ea6; color: #111; }
  .g4 { background: #cfd2d7; color: #111; } .g5 { background: #fff; color: #111; }
  .legend { display: flex; flex-wrap: wrap; gap: 3pt 9pt; font-size: 7.5pt; margin: -1pt 2pt 7pt; }
  .key { display: inline-flex; align-items: center; gap: 3pt; white-space: nowrap; }
  .key i { width: 8pt; height: 8pt; border: 0.9pt solid #111; border-radius: 1.5pt; display: inline-block; }
  .key b { color: #4a5568; font-weight: 500; }

  /* horizontal timeline across the back spread */
  .spread .inner { display: flex; flex-direction: column; }
  .spread .shelf { height: 122pt; }
  .tlh { position: relative; flex: none; height: 150pt; margin: 0; }
  .shelf-block { margin-top: auto; }
  .spread .legend { margin-bottom: 0; }
  .hs-line { position: absolute; top: 50%; height: 2pt; margin-top: -1pt; background: #111; }
  .hs-ic { position: absolute; top: 50%; width: 30pt; height: 30pt; margin: -15pt 0 0 -15pt; box-sizing: border-box; border: 1.8pt solid #111; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; z-index: 2; }
  .hs-ic img { width: 21pt; height: 21pt; display: block; }
  .hs-ic.small { width: 18pt; height: 18pt; margin: -9pt 0 0 -9pt; border-width: 2.2pt; }
  .hs-ic.small img { width: 11pt; height: 11pt; }
  .hs-stem { position: absolute; width: 1pt; margin-left: -0.5pt; height: 10pt; background: #111; }
  .hs-stem.up { bottom: calc(50% + 15pt); } .hs-stem.down { top: calc(50% + 15pt); }
  .hs-stem.up.small { bottom: calc(50% + 9pt); height: 16pt; } .hs-stem.down.small { top: calc(50% + 9pt); height: 16pt; }
  .hs-lbl { position: absolute; width: 88pt; }
  .hs-lbl.up { bottom: calc(50% + 28pt); } .hs-lbl.down { top: calc(50% + 28pt); }
  .hs-lbl .what { font-family: var(--display), sans-serif; font-weight: 600; font-size: 10pt; line-height: 1.1; }
  .hs-lbl .books { font-size: 7pt; color: #4a5568; line-height: 1.3; margin-top: 1pt; }

  /* icon timeline */
  .tl2 { list-style: none; margin: 0; padding: 0; position: relative; flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
  .tl2::before { content: ''; position: absolute; left: 16pt; top: 16pt; bottom: 16pt; width: 2pt; margin-left: -1pt; background: #111; }
  .st { display: flex; align-items: center; gap: 11pt; position: relative; }
  .st-ic { flex: none; width: 32pt; height: 32pt; box-sizing: border-box; border: 1.8pt solid #111; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; }
  .st-ic img { width: 23pt; height: 23pt; display: block; }
  .st-ic.small { width: 21pt; height: 21pt; margin: 0 5.5pt; border-width: 2.2pt; }
  .st-ic.small img { width: 13pt; height: 13pt; }
  .st .what { font-family: var(--display), sans-serif; font-weight: 600; font-size: 10.5pt; line-height: 1.1; }
  .st .books { font-size: 7.6pt; color: #4a5568; line-height: 1.3; margin-top: 1pt; }

  /* timeline */
  .tl { list-style: none; margin: 0; padding: 0 0 0 16pt; position: relative; flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
  .tl::before { content: ''; position: absolute; left: 4pt; top: 4pt; bottom: 4pt; width: 2.5pt; background: #111; border-radius: 2pt; }
  .ev { position: relative; }
  .ev::before { content: ''; position: absolute; left: -16pt; top: 2pt; width: 7pt; height: 7pt; border-radius: 50%; background: #fff; border: 2.2pt solid #111; }
  .ev.nt::before { background: #111; }
  .ev .date { font-size: 7.5pt; font-weight: 700; color: #4a5568; letter-spacing: 0.3pt; text-transform: uppercase; }
  .ev .what { font-family: var(--display), sans-serif; font-weight: 600; font-size: 10.5pt; line-height: 1.15; }
  .ev .books { font-size: 7.6pt; color: #4a5568; line-height: 1.25; }
  .tl-note { font-size: 7pt; color: #6b7280; margin-top: 6pt; }
  .divider { display: flex; align-items: center; gap: 6pt; font-size: 7pt; font-weight: 700; letter-spacing: 1pt; text-transform: uppercase; color: #4a5568; margin: 0 0 0 -16pt; }
"""

pages = []
pages.append(f'<section class="page cover{" cover-light" if COVER_STYLE == "light" else ""}" data-card="cover">{mountains_svg(cover_light=COVER_STYLE == "light")}</section>')
pages.append(f'''<section class="page inside-cover" data-card="inside">
  <div class="owner">
    <div class="owner-h">This journal belongs to</div>
    <div class="owner-line"><span>NAME</span><i></i></div>
    <div class="owner-line"><span>PHONE</span><i></i></div>
    <div class="owner-note">If found, please return. It&rsquo;s full of good stuff.</div>
  </div>
</section>''')
pages.append('''<section class="page ref-page"><div class="inner">
  <div class="ptitle">Why Guided SOAR</div>
  <p class="lede">The Bible is a book about God. Guided SOAR is a simple way to read it so that, passage by passage, you see Him more clearly and let that change you.</p>
  <div class="why">
    <div class="why-row"><div><span class="why-tag">Scripture</span><div class="why-t">Step back before you dive in.</div>
      <p>Knowing who wrote a book, when, and why gives you perspective to read it the way it was meant to be read, not just the way it sounds to us today.</p></div></div>
    <div class="why-row"><div><span class="why-tag">Observation</span><div class="why-t">Slow down.</div>
      <p>Notice words, wrestle with hard ideas, follow connections. It&rsquo;s okay not to have every answer today. Understanding grows a little at a time.</p></div></div>
    <div class="why-row center"><div><span class="why-tag dark">Central Truth</span><div class="why-t">Keep the main thing the main thing.</div>
      <p>We read to know God, not just to find tips for life. That&rsquo;s why every page has His character at the center, because the knowledge of God and the knowledge of self go hand in hand.</p></div></div>
    <div class="why-row"><div><span class="why-tag">Application</span><div class="why-t">Understand first, then apply.</div>
      <p>Ask what it says, then what it means, and only then what it means for you. Application built on the text will hold up.</p></div></div>
    <div class="why-row"><div><span class="why-tag">Reflection</span><div class="why-t">Pray the whole way through.</div>
      <p>Before, during, and after. The same Spirit who inspired these words helps us understand them and live them out.</p></div></div>
  </div>
</div></section>''')
def spread_page(side, title, sub, shelf_html, legend_html, stops):
    # timeline header lives on the left page; the right page keeps the same space so both lines align
    head = ('<div class="ptitle">Bible Timeline</div><div class="psub">One unified story that leads to Jesus.</div>'
            if side == "ot" else '<div class="ptitle">&nbsp;</div><div class="psub">&nbsp;</div>')
    return f'''<section class="page ref-page spread"><div class="inner">
  <div class="tl-head">{head}</div>
  {timeline_half(stops, side)}
  <div class="shelf-block">
    <div class="ptitle" data-mark="{side}">{title}</div>
    <div class="psub">{sub}</div>
    <div class="case">{shelf_html}</div>
    <div class="legend">{legend_html}</div>
  </div>
</div></section>'''
pages.append(spread_page("ot", "Old Testament", "39 books. The story begins and points to a coming King.",
                         shelves(OT, 17), legend(OT), TIMELINE[:SPLIT]))
pages.append(spread_page("nt", "New Testament", "27 books. The King arrives and announces the kingdom of God.",
                         shelves(NT, 14), legend(NT), TIMELINE[SPLIT:]))
pages.append(f'''<section class="page ref-page"><div class="inner">
  <div class="ptitle">Resources</div>
  <div class="psub">Point your phone camera at a code to open it.</div>
  <div class="qr-list">{resources_page()}</div>
</div></section>''')
# Dwell: the leader guide sits on a plain white page like the study cards (Guided SOAR keeps the grey reference page)
pages.append('<section class="page leader-page" data-card="leader"></section>' if DWELL else
             '<section class="page ref-page" data-card="leader"></section>')
if DWELL:   # card on the left page, Reflect on the facing right page (the leader guide is page 3, so pairs start on page 4)
    pages += ['<section class="page" data-card="blank"></section>', '<section class="page" data-card="reflect"></section>'] * STUDIES
else:
    pages += ['<section class="page" data-card="blank"></section>'] * BLANKS
# the OT / NT spread lives at the back: OT on an even (left) page, NT on the facing right page
for marker in ('data-mark="ot"', 'data-mark="nt"'):
    i = next(k for k, pg in enumerate(pages) if marker in pg)
    pages.append(pages.pop(i))
# drop pages that are saved for later versions
if not INCLUDE_WHY:
    pages = [pg for pg in pages if 'Why Guided SOAR' not in pg]
if not INCLUDE_RESOURCES:
    pages = [pg for pg in pages if '<div class="ptitle">Resources</div>' not in pg]

# faint mountain range along the bottom of every grey reference page
pages = [pg.replace('class="page ref-page"', 'class="page ref-page"', 1) for pg in pages]
pages = [re.sub(r'(<section class="page ref-page[^>]*>)', lambda m: m.group(1) + mountains_svg(light=True), pg, count=1)
         if 'ref-page' in pg else pg for pg in pages]
pages = [re.sub(r'(<section class="page inside-cover"[^>]*>)', lambda m: m.group(1) + mountains_svg(light=True), pg, count=1)
         if 'inside-cover' in pg else pg for pg in pages]
# two lined notes pages before the back cover: keeps the OT/NT spread off the cover sheet and the count a multiple of 4
NOTES_PAGES = 2
pages += ['<section class="page notes-page"><div class="inner"><div class="ptitle">Notes</div><div class="rules"></div></div></section>'] * NOTES_PAGES
if RESOURCES_URL:   # inside back cover: the Resources QR code takes the place of the second notes page
    pages[-1] = f'<section class="page inside-cover inside-back">{mountains_svg(light=True)}{resources_qr()}</section>'
pages.append(f'<section class="page back{" back-light" if COVER_STYLE == "light" else ""}"></section>')
assert len(pages) % 4 == 0, f"{len(pages)} pages is not a multiple of 4"

DWELL_CSS = """
  /* Dwell Skills wordmark sits in the cover circle where the Guided SOAR logo goes */
  .cv-verse { display: flex; flex-direction: column; align-items: center; text-align: center; color: #111; transform: translateY(-17pt); }   /* clear the ridge */
  .cv-line { font-family: var(--display), sans-serif; font-weight: 600; font-size: 11.5pt; line-height: 1.1; }
  .ds-box.cv-dwell { height: auto; font-size: 27pt; letter-spacing: 1pt; padding: 5pt 10pt 4pt 11pt; border-radius: 7pt; margin: 4pt 0; }
  .cv-ref { font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 7.5pt; letter-spacing: 1.6pt; text-transform: uppercase; color: #4a5568; margin-top: 6pt; }
  .reflect-card { margin: 0; }
  .leader-page .ref-head { margin-bottom: 6pt; }
"""
# Dwell cover: Colossians 3:16 (ESV) on the sun, with DWELL set in the wordmark's black box
COVER_VERSE = ('<div class="cv-verse"><span class="cv-line">Let the word of Christ</span>'
               '<span class="ds-box cv-dwell">DWELL</span><span class="cv-line">in you richly.</span>'
               '<span class="cv-ref">Colossians 3:16</span></div>')
COVER_JS = (f"c.querySelector('.mini-circle').innerHTML = '{COVER_VERSE}';" if DWELL else
    """c.querySelector('.mini-circle').innerHTML = '<img class="cover-logo" src="' + (p.classList.contains('cover-light') ? 'guided-soar-logo.png' : 'guided-soar-logo-white.png') + '" alt="Guided SOAR">';""")
REFLECT_JS = ("document.querySelectorAll('[data-card=\"reflect\"]').forEach(function (p) { p.appendChild(buildReflectionCard()); });\n"
              if DWELL else "")

t = TINTS.get(COVER_TINT)
tint_css = (f".cover.cover-light {{ background: linear-gradient(180deg, {t['sky'][0]} 0%, {t['sky'][1]} 78%); }} "
            f".cover-light .cover-card .mini-circle {{ background: {t['sun']}; border-color: {t['sun']}; }} "
            f".back.back-light {{ background: {t['back']}; }}") if t else ""
html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{"Dwell Skills Journal" if DWELL else "Guided SOAR Journal"}</title>
{head_links}
<style>{style}{JOURNAL_CSS.replace('{tint_css}', tint_css)}{DWELL_CSS if DWELL else ""}</style>
</head>
<body>
{chr(10).join(pages)}
<script>
{builders}
document.querySelectorAll('[data-card="leader"]').forEach(function (p) {{ var c = buildLeaderCard(); c.classList.add('rev'); setRefHead(c, 'Leader Guide', 'Questions to guide your prep in each section.'); p.appendChild(c); }});
document.querySelectorAll('[data-card="cover"]').forEach(function (p) {{ var c = buildMiniCard(); c.classList.add('cover-card'); {COVER_JS} p.appendChild(c); }});
function setRefHead(card, title, sub) {{
  card.querySelector('.mini-brand').outerHTML = '<div class="ref-head"><div class="ptitle">' + title + '</div><div class="psub">' + sub + '</div></div>';
}}
function resList(groups) {{
  return '<div class="mini-prompts res">' + groups.map(function (g) {{
    return '<div class="res-h">' + g[0] + '</div><ul>' + g[1].map(function (t) {{ return '<li>' + t + '</li>'; }}).join('') + '</ul>';
  }}).join('') + '</div>';
}}
function buildResourceCard() {{
  var el = buildMiniCard();
  el.classList.add('rev');
  setRefHead(el, 'Resources', 'Tools in print and online for each section.');
  el.querySelector('.mtl').insertAdjacentHTML('beforeend', resList([
    ['In print', ['Study Bible book introductions', 'Bible handbook or atlas']],
    ['Online', ['BibleProject overview videos', 'YouVersion Bible App book intros']]]));
  el.querySelector('.mtr').insertAdjacentHTML('beforeend', resList([
    ['In print', ['Cross-references in the margin', 'Bible dictionary or concordance']],
    ['Online', ['Compare translations: Bible Gateway', 'Word studies: Blue Letter Bible']]]));
  el.querySelector('.mbl').insertAdjacentHTML('afterbegin', resList([
    ['With people', ['Talk it through with your leader or a friend']],
    ['Everyday', ['Write the truth on a card or your lock screen', 'Memorize one verse with a Bible app plan']]]));
  el.querySelector('.mbr').insertAdjacentHTML('afterbegin', resList([
    ['With people', ['Bring questions to a leader', 'Pray with a friend']],
    ['On your own', ['Keep a prayer list', 'Pray the passage back to God']]]));
  var spaces = el.querySelectorAll('.mini-circle .mini-write-space');
  spaces[0].outerHTML = '<div class="mini-hint god-hint"><span>Check your answer with<br>a study Bible note or<br>a trusted commentary.</span></div>';
  spaces[1].outerHTML = '<div class="mini-hint"><span>Ask a leader what this<br>could look like this week.</span></div>';
  return el;
}}
document.querySelectorAll('[data-card="resources"]').forEach(function (p) {{ p.appendChild(buildResourceCard()); }});
document.querySelectorAll('[data-card="blank"]').forEach(function (p) {{
  var c = buildMiniCard();
  c.querySelectorAll('.mini-field > span:first-child').forEach(function (l) {{ if (l.textContent.trim() === 'NAME:') l.textContent = 'DATE:'; }});
  p.appendChild(c);
}});
{REFLECT_JS}</script>
</body>
</html>
'''
out = "dwell-journal.html" if DWELL else "journal.html"
(ROOT / out).write_text(html)
print("wrote", out, "with", len(pages), "pages")
