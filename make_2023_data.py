import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SETS = {
    "2023-upper-am": {
        "label": "令和5年度上期・午前（2023年5月）", "source_pdf": "20230528_co_second_q01.pdf",
        "answers": "ハ イ イ ロ ハ ニ ロ ハ ニ ハ ロ イ ロ ハ イ ロ ニ イ ニ ニ ニ ハ ニ ハ ロ イ ニ ニ ハ イ ハ ニ ニ ハ ニ イ ニ イ ロ イ ロ ロ イ ハ ハ ニ ニ イ イ ハ",
        "pages": {5:(1,[397,717,953,1139,1513,1941]),6:(6,[236,657,1390,1672,2089]),7:(10,[236,657,922,1187,1595,1785,2090]),8:(16,[236,687,1085,1497,1749,2016]),9:(21,[236,760,996,1174,1394,1722,2074]),10:(27,[236,729,1010,1335,2071]),11:(31,[638,761,883,1046,1168,1290,1408,1531,1653,1856,2041]),12:(41,[262,668,1073,1332,1738,2001]),13:(46,[263,613,1075,1431,1714,2110])}},
    "2023-upper-pm": {
        "label": "令和5年度上期・午後（2023年5月）", "source_pdf": "20230528_co_second_q02.pdf",
        "answers": "ロ ニ ハ ロ ロ ニ ハ ロ ニ ニ ハ イ ニ ロ イ イ ハ ロ ハ イ ニ ニ ニ イ ニ ロ イ イ ロ ロ ニ ニ イ ロ イ ニ ニ ロ ニ イ ハ ハ ロ ハ ハ ハ ニ ロ ニ ロ",
        "pages": {5:(1,[397,743,980,1227,1514,2065]),6:(6,[236,687,1187,1511,2089]),7:(10,[236,657,962,1269,1559,1795,2090]),8:(16,[236,554,937,1249,1545,2016]),9:(21,[236,502,893,1307,1646,2074]),10:(26,[236,627,951,1440,1810,2071]),11:(31,[648,761,873,1061,1249,1357,1471,1621,1734,1846,2040]),12:(41,[264,594,926,1258,1627,2001]),13:(46,[263,791,1182,1502,1750,2110])}},
    "2023-lower-am": {
        "label": "令和5年度下期・午前（2023年10月）", "source_pdf": "20231029_co_second_q01.pdf",
        "answers": "ロ イ ロ ハ ハ ロ ロ ロ ニ ニ イ ハ ニ イ ハ ハ ニ イ ハ ロ ニ イ ロ ハ ハ イ ハ イ イ ハ ロ イ ハ ロ イ ニ ハ イ ハ ニ ニ ロ イ イ ハ イ ニ イ ニ ロ",
        "pages": {5:(1,[397,719,955,1139,1513,2067]),6:(6,[236,686,1247,1553,2075]),7:(10,[236,657,909,1112,1322,1528,1734,2089]),8:(17,[236,687,1028,1395,2028]),9:(21,[236,641,1010,1304,1632,2017]),10:(26,[236,627,1099,1378,1613,2079]),11:(31,[632,704,819,930,1046,1161,1349,1540,1728,1839,1957]),12:(41,[260,715,959,1447,1763,2109]),13:(46,[258,577,897,1253,1572,2021])}},
    "2023-lower-pm": {
        "label": "令和5年度下期・午後（2023年10月）", "source_pdf": "20231029_co_second_q02.pdf",
        "answers": "ロ イ イ ロ ハ ニ ハ ロ ニ ロ イ ロ イ ニ ニ イ ロ ハ ハ ロ ロ ハ イ ニ ニ イ ロ ニ ロ ハ イ ハ イ ニ ロ ニ ニ ハ ニ ロ ロ ハ イ ニ ハ ロ ロ ロ ニ イ",
        "pages": {5:(1,[397,719,955,1232,1606,2067]),6:(6,[236,672,1276,1557,2080]),7:(10,[236,657,962,1269,1534,1759,2089]),8:(16,[236,543,837,1129,1540,2028]),9:(21,[236,605,1007,1332,1697,2017]),10:(26,[236,554,890,1169,1527,2079]),11:(31,[594,716,879,961,1164,1282,1445,1567,1689,1811,1957]),12:(41,[266,709,1004,1336,1815,2109]),13:(46,[258,577,1075,1358,1643,2021])}},
}

def explain(number, answer):
    if number <= 30:
        return f"正答は「{answer}」です。問題文の条件を電気工事の基本公式・法令・施工基準に照らして確認すると、この選択肢が正答になります。"
    return f"正答は「{answer}」です。配線図の記号、接続関係、電源と負荷の位置を確認し、電気的な成立条件に照らして判断します。"

def make_set(name, config):
    page_dir = ROOT / "tmp" / "pdfs" / name
    out_dir = ROOT / "output" / name
    image_dir = out_dir / "questions"
    image_dir.mkdir(parents=True, exist_ok=True)
    answers = dict(enumerate(config["answers"].split(), 1))
    if len(answers) != 50:
        raise ValueError(f"{name}: expected 50 answers, got {len(answers)}")
    records = []
    for page_no, (first, lines) in config["pages"].items():
        src = page_dir / f"page-{page_no:02d}.png"
        x, width = (230, 1250) if page_no >= 11 else (245, 1245)
        split_x = 495 if first <= 40 else 318
        for offset, (top, bottom) in enumerate(zip(lines, lines[1:])):
            number = first + offset
            height = bottom - top - 4
            whole_name = f"q{number:03d}.png"
            whole = image_dir / whole_name
            question = image_dir / f"q{number:03d}-question.png"
            answer = image_dir / f"q{number:03d}-answer.png"
            subprocess.run(["convert", str(src), "-crop", f"{width}x{height}+{x}+{top + 2}", "+repage", str(whole)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["convert", str(whole), "-crop", f"{split_x}x{height}+0+0", "+repage", str(question)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["convert", str(whole), "-crop", f"{width - split_x}x{height}+{split_x}+0", "+repage", str(answer)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            records.append({"number": number, "answer": answers[number], "explanation": explain(number, answers[number]), "image": f"questions/{whole_name}", "question_image": f"questions/{question.name}", "answer_image": f"questions/{answer.name}", "source_page": page_no})
    records.sort(key=lambda item: item["number"])
    if [item["number"] for item in records] != list(range(1, 51)):
        raise ValueError(f"{name}: question ranges are incomplete")
    (out_dir / "questions.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({"label": config["label"], "source_pdf": config["source_pdf"], "count": 50}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(page_dir / "page-15.png", out_dir / "diagram.png")
    subprocess.run(["convert", str(page_dir / "page-11.png"), "-crop", "1250x470+230+100", "+repage", str(out_dir / "diagram-intro.png")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"created {name}: 50 questions")

for name, config in SETS.items():
    make_set(name, config)
