"""Lay the 5.5x8.5 journal out two-up on landscape letter for "cut and stack" printing.

Print double-sided (flip on SHORT edge), cut every sheet down the middle at 5.5",
put the left-half stack on top of the right-half stack, and coil bind on the left.
The pages then read in order and the OT/NT spread still faces.

usage: python3 tools/impose_letter.py "Guided SOAR Journal.pdf" "Guided SOAR Journal - Letter.pdf"
"""
import sys
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

src, dst = sys.argv[1], sys.argv[2]
pages = PdfReader(src).pages
W, H = 396, 612                       # half-letter in points
leaves = (len(pages) + 1) // 2        # each leaf = front + back
sheets = (leaves + 1) // 2            # left halves hold leaves 1..S, right halves S+1..

def page(n):                          # n is 0-based; None past the end
    return pages[n] if n is not None and n < len(pages) else None

def side(left, right):
    out = PageObject.create_blank_page(width=2 * W, height=H)
    for p, x in ((left, 0), (right, W)):
        if p is not None:
            out.merge_transformed_page(p, Transformation().translate(x, 0))
    return out

w = PdfWriter()
for i in range(sheets):
    a, b = i, sheets + i                              # leaf indexes on this sheet
    b_ok = b < leaves
    w.add_page(side(page(2 * a), page(2 * b) if b_ok else None))          # front
    w.add_page(side(page(2 * b + 1) if b_ok else None, page(2 * a + 1)))  # back (short-edge flip)
w.write(dst)
print(f"{len(pages)} pages -> {sheets} letter sheets ({2 * sheets} sides)")
