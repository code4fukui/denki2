import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SETS = {
    "2025-upper": {
        "label": "令和7年度上期（2025年5月）",
        "source_pdf": "20250525_co_second_q01.pdf",
        "answers": "ロ ハ イ ハ ロ ハ ロ ロ ロ ニ  ハ ロ ハ ロ ハ イ ハ イ ニ ニ  ハ ロ イ ハ ハ ロ イ ハ ロ イ  ロ ニ ロ ニ イ ロ ロ ロ イ ハ  ロ ロ ニ ハ イ ロ ハ ロ ロ ハ",
        "pages": {
            5: (1, [399, 718, 954, 1219, 1592, 2061]),
            6: (6, [236, 988, 1408, 1682, 2089]),
            7: (10, [236, 656, 921, 1186, 1497, 1688, 1954]),
            8: (16, [236, 538, 965, 1364, 1778, 2015]),
            9: (21, [236, 678, 1005, 1248, 1563, 2051]),
            10: (26, [236, 787, 1231, 1630, 1813, 2088]),
            11: (31, [696, 910, 1016, 1194, 1335, 1513, 1584, 1762, 1868, 1939, 2049]),
            12: (41, [268, 716, 1237, 1535, 1795, 2127]),
            13: (46, [259, 522, 883, 1277, 1573, 1934]),
        },
    },
    "2025-lower": {
        "label": "令和7年度下期（2025年10月）",
        "source_pdf": "20251026_co_second_q01.pdf",
        "answers": "ロ イ ハ イ ハ ニ ハ ハ ロ ハ  イ ロ ニ イ ニ ロ ロ ニ ハ ロ  イ イ イ イ ハ イ ニ ニ イ ハ  ハ ロ ニ イ ロ ハ ロ ニ イ ニ  ハ ロ ハ イ ロ イ ニ イ ロ ハ",
        "pages": {
            5: (1, [399, 718, 950, 1168, 1573, 2048]),
            6: (6, [236, 787, 1258, 1539, 2095]),
            7: (10, [236, 663, 946, 1141, 1334, 1528, 1737, 2095]),
            8: (17, [236, 671, 998, 1312, 1701, 2064]),
            9: (22, [236, 610, 1121, 1699, 2089]),
            10: (26, [236, 603, 870, 1651, 1877, 2108]),
            11: (31, [647, 818, 925, 1032, 1205, 1378, 1559, 1641, 1752, 1875, 2016]),
            12: (41, [268, 679, 977, 1312, 1719, 2130]),
            13: (46, [266, 768, 1128, 1489, 1845, 2096]),
        },
    },
}

def make_set(set_name, config):
    page_dir = ROOT / "tmp" / "pdfs" / set_name.replace("-", "")
    out_dir = ROOT / "output" / set_name
    images_dir = out_dir / "questions"
    images_dir.mkdir(parents=True, exist_ok=True)
    answers = dict(enumerate(config["answers"].split(), start=1))
    if len(answers) != 50:
        raise ValueError(f"{set_name}: expected 50 answers, got {len(answers)}")
    records = []
    for page_no, (first_question, lines) in config["pages"].items():
        src = page_dir / f"page-{page_no:02d}.png"
        x = 230 if page_no >= 11 else 245
        width = 1250 if page_no >= 11 else 1245
        split_x = 495 if first_question <= 40 else 318
        for offset, (top, bottom) in enumerate(zip(lines, lines[1:])):
            number = first_question + offset
            height = bottom - top - 4
            whole_name = f"q{number:03d}.png"
            whole = images_dir / whole_name
            question = images_dir / f"q{number:03d}-question.png"
            answer = images_dir / f"q{number:03d}-answer.png"
            subprocess.run(["convert", str(src), "-crop", f"{width}x{height}+{x}+{top + 2}", "+repage", str(whole)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["convert", str(whole), "-crop", f"{split_x}x{height}+0+0", "+repage", str(question)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["convert", str(whole), "-crop", f"{width - split_x}x{height}+{split_x}+0", "+repage", str(answer)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            records.append({
                "number": number,
                "answer": answers[number],
                "image": f"questions/{whole_name}",
                "question_image": f"questions/{question.name}",
                "answer_image": f"questions/{answer.name}",
                "source_page": page_no,
            })
    records.sort(key=lambda item: item["number"])
    if [item["number"] for item in records] != list(range(1, 51)):
        raise ValueError(f"{set_name}: question ranges are incomplete")
    (out_dir / "questions.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({"label": config["label"], "source_pdf": config["source_pdf"], "count": 50}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"created {set_name}: 50 questions")

for name, config in SETS.items():
    make_set(name, config)
