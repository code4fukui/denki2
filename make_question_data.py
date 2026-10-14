import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
pages_dir = ROOT / "tmp" / "pdfs" / "pages"
out_dir = ROOT / "output"
images_dir = out_dir / "questions"
images_dir.mkdir(parents=True, exist_ok=True)

# Answers from the official answer PDF.
answers = {
    1: "イ", 2: "ロ", 3: "ハ", 4: "ニ", 5: "ロ",
    6: "ロ", 7: "ニ", 8: "ロ", 9: "イ", 10: "ハ",
    11: "イ", 12: "ロ", 13: "ニ", 14: "ハ", 15: "イ",
    16: "ニ", 17: "イ", 18: "イ", 19: "イ", 20: "イ",
    21: "イ", 22: "ニ", 23: "ロ", 24: "ハ", 25: "ロ",
    26: "イ", 27: "ニ", 28: "ロ", 29: "ハ", 30: "イ",
    31: "ニ", 32: "ハ", 33: "ニ", 34: "イ", 35: "ロ",
    36: "ハ", 37: "ニ", 38: "ロ", 39: "イ", 40: "ニ",
    41: "ニ", 42: "ハ", 43: "ロ", 44: "イ", 45: "ロ",
    46: "ニ", 47: "ハ", 48: "ロ", 49: "イ", 50: "ニ",
}

# Rendered at 150 dpi: table bounds are in pixels. Each tuple is
# (page number, first question number, horizontal table lines).
tables = [
    (5, 1, [409, 730, 966, 1215, 1588, 2072]),
    (6, 6, [246, 742, 1317, 1598, 2069]),
    (7, 10, [246, 668, 933, 1200, 1482, 1718, 1985]),
    (8, 16, [246, 681, 1051, 1393, 1703, 2091]),
    (9, 21, [246, 535, 949, 1273, 1493, 1864]),
    (10, 26, [246, 697, 918, 1163, 1463, 1789]),
    (11, 31, [776, 907, 994, 1124, 1284, 1414, 1544, 1670, 1800, 1930, 2058]),
    (12, 41, [278, 610, 942, 1384, 1753, 2084]),
    (13, 46, [275, 631, 1057, 1305, 1660, 2014]),
]

records = []
for page_no, first_question, lines in tables:
    src = pages_dir / f"page-{page_no:02d}.png"
    if not src.exists():
        raise FileNotFoundError(src)
    # General tables begin at x=245; wiring tables begin at x=230.
    x = 230 if page_no >= 11 else 245
    width = 1250 if page_no >= 11 else 1245
    for offset, (top, bottom) in enumerate(zip(lines, lines[1:])):
        qno = first_question + offset
        filename = f"q{qno:03d}.png"
        dst = images_dir / filename
        height = bottom - top - 4
        subprocess.run([
            "convert", str(src), "-crop", f"{width}x{height}+{x}+{top + 2}",
            "+repage", str(dst)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        records.append({
            "number": qno,
            "answer": answers[qno],
            "image": f"questions/{filename}",
            "source_page": page_no,
        })

records.sort(key=lambda item: item["number"])
assert [item["number"] for item in records] == list(range(1, 51))
assert len(answers) == 50

(out_dir / "questions.json").write_text(
    json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"created {len(records)} question images and {out_dir / 'questions.json'}")
