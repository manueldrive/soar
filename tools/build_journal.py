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
    ("400 Quiet Years", "c. 430&ndash;5 BC", "Between the Testaments"),
    ("Jesus", "c. 5 BC &ndash; AD 30", "Matthew &middot; Mark &middot; Luke &middot; John"),
    ("The Church Spreads", "c. AD 30&ndash;95", "Acts &middot; the Letters &middot; Revelation"),
]

def timeline():
    items = []
    for i, (title, date, books) in enumerate(TIMELINE):
        nt = " nt" if i >= 10 else ""
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
  .cover-card .mini-circle { background: #47494f; border-color: #47494f; }
  .cover-card .mini-label { color: #fff; }
  .cover-card .mini-circle { gap: 9pt; padding: 0; }
  .cover-logo { height: 40pt; width: auto; display: block; }
  .cover-word { font-family: var(--display), sans-serif; font-weight: 600; font-size: 11pt; letter-spacing: 5pt; padding-left: 5pt; color: #fff; line-height: 1; }
  .cover-circle { width: 176pt; height: 176pt; border-radius: 50%; background: #47494f; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 30pt; }
  .cover-circle .lbl { font-family: var(--display), sans-serif; font-weight: 700; font-size: 15pt; color: #fff; letter-spacing: 0.3pt; }
  .back { background: #2e2f33; }

  /* content pages */
  .inner { width: 356pt; height: 572pt; display: flex; flex-direction: column; font-family: 'DM Sans', Arial, sans-serif; color: #111; }
  .ptitle { font-family: var(--display), sans-serif; font-weight: 700; font-size: 20pt; line-height: 1; margin: 2pt 0 2pt; }
  .psub { font-size: 9pt; color: #4a5568; margin: 0 0 10pt; }

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
pages.append('<section class="page cover" data-card="cover"></section>')
pages.append(f'''<section class="page"><div class="inner">
  <div class="ptitle">66 Books, One Story</div>
  <div class="psub">The Bible is a library. Here&rsquo;s where every book lives.</div>
  <div class="case"><div class="case-h">Old Testament <small>39 books</small></div>{shelves(OT, 17)}</div>
  <div class="legend">{legend(OT)}</div>
  <div class="case"><div class="case-h">New Testament <small>27 books</small></div>{shelves(NT, 14)}</div>
  <div class="legend">{legend(NT)}</div>
</div></section>''')
pages.append(f'''<section class="page"><div class="inner">
  <div class="ptitle">The Big Story</div>
  <div class="psub">Where each book fits in the story of God and His people.</div>
  {timeline()}
  <div class="tl-note">Dates are approximate; scholars differ on some. &#9675; Old Testament &nbsp; &#9679; New Testament</div>
</div></section>''')
pages.append('<section class="page" data-card="leader"></section>')
pages += ['<section class="page" data-card="blank"></section>'] * BLANKS
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
document.querySelectorAll('[data-card="leader"]').forEach(function (p) {{ p.appendChild(buildLeaderCard()); }});
document.querySelectorAll('[data-card="cover"]').forEach(function (p) {{ var c = buildMiniCard(); c.classList.add('cover-card'); c.querySelector('.mini-circle').innerHTML = '<img class="cover-logo" src="guided-soar-logo-white.png" alt="Guided SOAR">'; p.appendChild(c); }});
document.querySelectorAll('[data-card="blank"]').forEach(function (p) {{ p.appendChild(buildMiniCard()); }});
</script>
</body>
</html>
'''
(ROOT / "journal.html").write_text(html)
print("wrote journal.html with", len(pages), "pages")
