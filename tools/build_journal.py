"""Builds journal.html (a printable 5.5x8.5in Guided SOAR journal) from index.html.

Reuses index.html's styles and card builders so the journal always matches the site.
Run:  python3 tools/build_journal.py   (then open journal.html and print, or use tools/journal_pdf.py)
"""
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "index.html").read_text()

head_links = "\n".join(l for l in src.split("\n")[:9] if "fonts.g" in l or "preconnect" in l)
style = src[src.index("<style>") + 7 : src.index("</style>")]
js = src[src.index("<script>", src.index("</style>")) + 8 :]
builders = js[js.index("    // ---------- shared caption builder") : js.index("    document.querySelectorAll('#leaderPage")]

BLANKS = 12

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

def mountains_svg():
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
        ("#1d1e21", ridge(5, 388, [(-30, 14, 160), (150, -4, 120), (330, 26, 200)], 1.3, step=(5, 10))),
        # near ridge: darkest, low rolling hills in front
        ("#111214", ridge(9, 478, [(30, 22, 170), (200, 6, 120), (380, 30, 170)], 1.1, step=(5, 10))),
    ]
    paths = []
    for color, pts in layers:
        d = f"M-10 {H} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts) + f" L{W + 10} {H} Z"
        paths.append(f'<path d="{d}" fill="{color}"/>')
    return f'<svg class="cover-mtn" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">{"".join(paths)}</svg>'

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

def shelves(groups, split_at):
    flat = [(name, SHADES[i]) for i, (_, books) in enumerate(groups) for name in books]
    rows = [flat[:split_at], flat[split_at:]]
    out = []
    for r, row in enumerate(rows):
        spines = []
        for k, (name, shade) in enumerate(row):
            h = 86 + ((k * 37 + r * 13 + len(name) * 5) % 5) * 3   # gentle, repeatable height variety
            spines.append(f'<div class="spine {shade}" style="height:{h}%"><span>{name}</span></div>')
        out.append('<div class="shelf">' + "".join(spines) + "</div>")
    return "".join(out)

def legend(groups):
    return "".join(f'<span class="key"><i class="{SHADES[i]}"></i>{name} <b>{len(b)}</b></span>'
                   for i, (name, b) in enumerate(groups))

TIMELINE = [
    ("Creation &amp; the Fall", "The beginning", "Genesis 1&ndash;11"),
    ("Abraham, Isaac &amp; Jacob", "c. 2000&ndash;1800 BC", "Genesis 12&ndash;50 &middot; (Job may be set here)"),
    ("Exodus &amp; the Law", "c. 1446 BC", "Exodus &middot; Leviticus &middot; Numbers &middot; Deuteronomy"),
    ("Into the Promised Land", "c. 1400&ndash;1050 BC", "Joshua &middot; Judges &middot; Ruth"),
    ("United Kingdom: Saul, David, Solomon", "c. 1050&ndash;930 BC",
     "1&ndash;2 Samuel &middot; 1 Kings &middot; 1 Chronicles &middot; Psalms &middot; Proverbs &middot; Ecclesiastes &middot; Song of Songs"),
    ("Divided Kingdom: Israel &amp; Judah", "930&ndash;722 BC",
     "1&ndash;2 Kings &middot; 2 Chronicles &middot; Isaiah &middot; Hosea &middot; Amos &middot; Jonah &middot; Micah"),
    ("Judah Alone, Then Exile", "722&ndash;586 BC", "Jeremiah &middot; Lamentations &middot; Nahum &middot; Habakkuk &middot; Zephaniah"),
    ("Exile in Babylon", "586&ndash;538 BC", "Ezekiel &middot; Daniel &middot; Obadiah"),
    ("Return &amp; Rebuild", "538&ndash;430 BC", "Ezra &middot; Nehemiah &middot; Esther &middot; Haggai &middot; Zechariah &middot; Malachi"),
    ("Jesus", "c. 5 BC &ndash; AD 30", "Matthew &middot; Mark &middot; Luke &middot; John"),
    ("The Church Spreads", "c. AD 30&ndash;90", "Acts &middot; Romans&ndash;Jude"),
    ("Revelation: All Things Made New", "c. AD 95", "Revelation"),
]

def timeline():
    items = []
    for i, (title, date, books) in enumerate(TIMELINE):
        nt = " nt" if i >= 9 else ""
        items.append(f'<li class="ev{nt}"><div class="date">{date}</div><div class="what">{title}</div><div class="books">{books}</div></li>')
    return '<ol class="tl">' + "".join(items) + "</ol>"

JOURNAL_CSS = r"""
  @page { size: 5.5in 8.5in; margin: 0; }
  html, body { margin: 0; padding: 0; background: #fff; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .page { width: 396pt; height: 612pt; position: relative; overflow: hidden; page-break-after: always; break-after: page; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
  .page:last-child { page-break-after: auto; break-after: auto; }
  .page .mini-card { margin: 0; }
  @media screen { body { background: #9aa0a6; } .page { margin: 16px auto; box-shadow: 0 4px 18px rgba(0,0,0,.25); background: #fff; } }

  /* cover */
  .cover { background: #2e2f33; }
  /* cover reuses the blank card so the circle sits exactly where it does on every template */
  .cover-card .mini-brand, .cover-card .mini-box { visibility: hidden; }
  .cover-card .mini-circle { background: #ececee; border-color: #ececee; box-shadow: 0 0 40pt 14pt rgba(236,236,238,0.18); }
  .cover-card .mini-label { color: #fff; }
  .cover-card .mini-circle { gap: 9pt; padding: 0; }
  .cover-logo { height: 40pt; width: auto; display: block; }
  .cover-word { font-family: var(--display), sans-serif; font-weight: 600; font-size: 11pt; letter-spacing: 5pt; padding-left: 5pt; color: #fff; line-height: 1; }
  .cover-circle { width: 176pt; height: 176pt; border-radius: 50%; background: #47494f; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 30pt; }
  .cover-circle .lbl { font-family: var(--display), sans-serif; font-weight: 700; font-size: 15pt; color: #fff; letter-spacing: 0.3pt; }
  .back { background: #2e2f33; }
  .cover { background: radial-gradient(circle at 50% 54%, #6a6c72 0%, #4a4c52 22%, #2f3034 48%, #1f2023 80%); }
  .cover-mtn { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; }
  .cover .mini-card { position: relative; z-index: 1; }

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
  .ref-page .win, .ref-page .case { background: #fff; }
  ol.tl { background: transparent; }

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
  .spine { flex: 1 1 0; border: 0.9pt solid #111; border-bottom: none; border-radius: 2pt 2pt 0 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  .spine span { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 6.3pt; font-weight: 500; white-space: nowrap; letter-spacing: 0.1pt; }
  .g1 { background: #111; color: #fff; } .g2 { background: #4a4d55; color: #fff; } .g3 { background: #9a9ea6; color: #111; }
  .g4 { background: #cfd2d7; color: #111; } .g5 { background: #fff; color: #111; }
  .legend { display: flex; flex-wrap: wrap; gap: 3pt 9pt; font-size: 7.5pt; margin: -1pt 2pt 7pt; }
  .key { display: inline-flex; align-items: center; gap: 3pt; white-space: nowrap; }
  .key i { width: 8pt; height: 8pt; border: 0.9pt solid #111; border-radius: 1.5pt; display: inline-block; }
  .key b { color: #4a5568; font-weight: 500; }

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
pages.append(f'<section class="page cover" data-card="cover">{mountains_svg()}</section>')
pages.append('''<section class="page inside-cover" data-card="inside">
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
pages.append(f'''<section class="page ref-page"><div class="inner">
  <div class="ptitle">66 Books, One Story</div>
  <div class="psub">The Bible is a library. Here&rsquo;s where every book lives.</div>
  <div class="case"><div class="case-h">Old Testament <small>39 books</small></div>{shelves(OT, 17)}</div>
  <div class="legend">{legend(OT)}</div>
  <div class="case"><div class="case-h">New Testament <small>27 books</small></div>{shelves(NT, 14)}</div>
  <div class="legend">{legend(NT)}</div>
</div></section>''')
pages.append(f'''<section class="page ref-page"><div class="inner">
  <div class="ptitle">The Big Story</div>
  <div class="psub">Where each book fits in the story of God and His people.</div>
  {timeline()}
  <div class="tl-note">Dates are approximate; scholars differ on some. &#9675; Old Testament &nbsp; &#9679; New Testament</div>
</div></section>''')
pages.append(f'''<section class="page ref-page"><div class="inner">
  <div class="ptitle">Resources</div>
  <div class="psub">Point your phone camera at a code to open it.</div>
  <div class="qr-list">{resources_page()}</div>
</div></section>''')
pages.append('<section class="page ref-page" data-card="leader"></section>')
pages += ['<section class="page" data-card="blank"></section>'] * BLANKS
# reference pages that live at the back of the journal, with the timeline last
for marker in ("66 Books, One Story", "The Big Story"):
    i = next(k for k, pg in enumerate(pages) if marker in pg)
    pages.append(pages.pop(i))
pages.append('<section class="page back"></section>')

html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Guided SOAR Journal</title>
{head_links}
<style>{style}{JOURNAL_CSS}</style>
</head>
<body>
{chr(10).join(pages)}
<script>
{builders}
document.querySelectorAll('[data-card="leader"]').forEach(function (p) {{ var c = buildLeaderCard(); c.classList.add('rev'); setRefHead(c, 'Leader Guide', 'Questions to guide your prep in each section.'); p.appendChild(c); }});
document.querySelectorAll('[data-card="cover"]').forEach(function (p) {{ var c = buildMiniCard(); c.classList.add('cover-card'); c.querySelector('.mini-circle').innerHTML = '<img class="cover-logo" src="guided-soar-logo.png" alt="Guided SOAR">'; p.appendChild(c); }});
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
</script>
</body>
</html>
'''
(ROOT / "journal.html").write_text(html)
print("wrote journal.html with", len(pages), "pages")
