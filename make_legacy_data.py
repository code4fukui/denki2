import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PDF_DIR = ROOT / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
OUTPUT_DIR = ROOT / "output"

# PDFs added to pdf/ but not yet registered in output/exams.json.
SETS = [
    ("2009", "平成21年度（2009年6月）", "20090607_co_second_q01.pdf", "20090607_co_second_a01.pdf"),
    ("2010", "平成22年度（2010年6月）", "20100606_co_second_q01.pdf", "20100606_co_second_a01.pdf"),
    ("2011-upper", "平成23年度上期（2011年6月）", "20110605_co_second_q01.pdf", "20110605_co_second_a01.pdf"),
    ("2011-lower", "平成23年度下期（2011年10月）", "20111001_co_second_q01.pdf", "20111001_co_second_a01.pdf"),
    ("2012-upper", "平成24年度上期（2012年6月）", "20120603_co_second_q01.pdf", "20120603_co_second_a01.pdf"),
    ("2012-lower", "平成24年度下期（2012年10月）", "20121006_co_second_q01.pdf", "20121006_co_second_a01.pdf"),
    ("2013-upper", "平成25年度上期（2013年6月）", "20130602_co_second_q01.pdf", "20130602_co_second_a01.pdf"),
    ("2013-lower", "平成25年度下期（2013年10月）", "20131005_co_second_q01.pdf", "20131005_co_second_a01.pdf"),
    ("2014-upper", "平成26年度上期（2014年6月）", "20140601_co_second_q01.pdf", "20140601_co_second_a01.pdf"),
    ("2014-lower", "平成26年度下期（2014年10月）", "20141004_co_second_q01.pdf", "20141004_co_second_a01.pdf"),
    ("2015-upper", "平成27年度上期（2015年6月）", "20150607_co_second_q01.pdf", "20150607_co_second_a01.pdf"),
    ("2015-lower", "平成27年度下期（2015年10月）", "20151003_co_second_q01.pdf", "20151003_co_second_a01.pdf"),
    ("2016-upper", "平成28年度上期（2016年6月）", "20160605_co_second_q01.pdf", "20160605_co_second_a01.pdf"),
    ("2016-lower", "平成28年度下期（2016年10月）", "20161001_co_second_q01.pdf", "20161001_co_second_a01.pdf"),
    ("2017-upper", "平成29年度上期（2017年6月）", "20170604_co_second_q01.pdf", "20170604_co_second_a01.pdf"),
    ("2017-lower", "平成29年度下期（2017年9月）", "20170930_co_second_q01.pdf", "20170930_co_second_a01.pdf"),
    ("2018-upper", "平成30年度上期（2018年6月）", "20180603_co_second_q01.pdf", "20180603_co_second_a01.pdf"),
    ("2018-lower", "平成30年度下期（2018年10月）", "20181007_co_second_q01.pdf", "20181007_co_second_a01.pdf"),
    ("2019-upper", "2019年度上期（2019年6月）", "20190602_co_second_q01.pdf", "20190602_co_second_a01.pdf"),
    ("2019-lower", "2019年度下期（2019年10月）", "20191006_co_second_q01.pdf", "20191006_co_second_a01.pdf"),
    ("2020-lower-am", "令和2年度下期・午前（2020年10月）", "20201004_co_second_q01.pdf", "20201004_co_second_a01.pdf"),
    ("2020-lower-pm", "令和2年度下期・午後（2020年10月）", "20201004_co_second_q02.pdf", "20201004_co_second_a02.pdf"),
    ("2021-upper-am", "令和3年度上期・午前（2021年5月）", "20210530_co_second_q01.pdf", "20210530_co_second_a01.pdf"),
    ("2021-upper-pm", "令和3年度上期・午後（2021年5月）", "20210530_co_second_q02.pdf", "20210530_co_second_a02.pdf"),
    ("2021-lower-am", "令和3年度下期・午前（2021年10月）", "220211024_co_second_q01.pdf", "220211024_co_second_a01.pdf"),
    ("2021-lower-pm", "令和3年度下期・午後（2021年10月）", "220211024_co_second_q02.pdf", "220211024_co_second_a02.pdf"),
    ("2022-upper-am", "令和4年度上期・午前（2022年5月）", "20220529_co_second_q01.pdf", "20220529_co_second_a01.pdf"),
    ("2022-upper-pm", "令和4年度上期・午後（2022年5月）", "20220529_co_second_q02.pdf", "20220529_co_second_a02.pdf"),
    ("2022-lower-am", "令和4年度下期・午前（2022年10月）", "20221030_co_second_q01.pdf", "20221030_co_second_a01.pdf"),
    ("2022-lower-pm", "令和4年度下期・午後（2022年10月）", "20221030_co_second_q02.pdf", "20221030_co_second_a02.pdf"),
]


def render_pages(source, page_dir):
    page_dir.mkdir(parents=True, exist_ok=True)
    if not (page_dir / "page-15.png").exists():
        subprocess.run(["pdftoppm", "-png", "-r", "150", str(source), str(page_dir / "page")], check=True)
        for page in page_dir.glob("page-*.png"):
            page.rename(page_dir / f"page-{int(page.stem.split('-')[-1]):02d}.png")


def horizontal_lines(image):
    # The question tables have long horizontal rules. Downsampling their
    # table width to one pixel makes those rules easy to detect robustly.
    def read_scan(crop):
        cmd = ["magick", str(image), "-crop", crop, "-colorspace", "gray", "-resize", "1x2200!", "txt:-"]
        return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout

    def detect(result, threshold):
        hits = []
        for line in result.splitlines()[1:]:
            match = re.search(r"^0,(\d+): \((\d+)", line)
            if match and int(match.group(2)) < threshold:
                hits.append(int(match.group(1)))
        groups = []
        for value in hits:
            if not groups or value > groups[-1][-1] + 1:
                groups.append([value])
            else:
                groups[-1].append(value)
        return [100 + round((group[0] + group[-1]) / 2) for group in groups][1:]

    # Newer PDFs have a wider left margin; older PDFs place the table further left.
    # Try the modern scan first, then a narrow left-column scan for scanned editions.
    wide_result = read_scan("1280x2200+220+100")
    wide_lines = detect(wide_result, 100)
    narrow_result = read_scan("180x2200+100+100")
    narrow_lines = detect(narrow_result, 100)
    if len(narrow_lines) > len(wide_lines):
        result, lines = narrow_result, narrow_lines
        # Photo-heavy pages can hide the first row's top rule in the
        # background. Recover the header-bottom rule from a softer scan.
        weak = detect(result, 200)
        before_first = [value for value in weak if 80 < value < lines[0] - 20]
        if before_first:
            candidate = before_first[0] if lines[0] - before_first[-1] > 300 else before_first[-1]
            lines = [candidate] + lines
    elif len(wide_lines) > 1:
        lines = wide_lines
    else:
        lines = detect(narrow_result, 200)
    return lines


def extract_answers(answer_pdf):
    text = subprocess.run(["pdftotext", "-layout", str(answer_pdf), "-"], check=True, capture_output=True, text=True).stdout
    pairs = re.findall(r"(?<!\d)(\d{1,2})\s+([イロハニ])", text)
    answers = {int(number): answer for number, answer in pairs if int(number) <= 50}
    if set(answers) != set(range(1, 51)):
        raise ValueError(f"{answer_pdf.name}: could not extract 50 answers")
    return answers


def explanation(number, answer):
    if number <= 30:
        return f"正答は「{answer}」です。問題文の条件を電気工事の基本公式・法令・施工基準に照らして確認します。"
    return f"正答は「{answer}」です。配線図の記号、接続関係、電源と負荷の位置を確認し、施工条件に照らして判断します。"


def make_set(set_id, label, question_name, answer_name):
    source = PDF_DIR / question_name
    page_dir = TMP_DIR / set_id
    out_dir = OUTPUT_DIR / set_id
    image_dir = out_dir / "questions"
    image_dir.mkdir(parents=True, exist_ok=True)
    render_pages(source, page_dir)
    answers = extract_answers(PDF_DIR / answer_name)
    records = []
    number = 1
    page_specs = []
    for page_no in range(5, 15):
        lines = horizontal_lines(page_dir / f"page-{page_no:02d}.png")
        # Some older PDFs use page 14 for the last questions, while newer
        # PDFs leave it blank before the wiring diagram on page 15.
        if len(lines) < 2:
            continue
        page_specs.append([page_no, lines])

    # Older editions use a slightly different pagination. Normalize only the
    # missing/extra outer row rules; the detected inner rules remain intact.
    if set_id == "2009":
        expected = [6, 5, 5, 5, 5, 4, 10, 5, 5]
    elif set_id.startswith(("2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019")):
        expected = [6, 4, 5, 6, 5, 4, 10, 6, 4]
    else:
        expected = [5, 4, 6, 5, 6, 4, 10, 5, 5]
    for index, (page_no, lines) in enumerate(page_specs):
        target = expected[index] if index < len(expected) else len(lines) - 1
        while len(lines) - 1 < target:
            gaps = [lines[i + 1] - lines[i] for i in range(len(lines) - 1)]
            split = max(range(len(gaps)), key=gaps.__getitem__)
            lines.insert(split + 1, lines[split] + round(gaps[split] / 2))
        while len(lines) - 1 > target:
            gaps = [lines[i + 1] - lines[i] for i in range(1, len(lines) - 1)]
            remove = 1 + min(range(len(gaps)), key=gaps.__getitem__)
            lines.pop(remove)
    for page_no, lines in page_specs:
        for top, bottom in zip(lines, lines[1:]):
            if number > 50:
                break
            height = bottom - top - 4
            old_layout = set_id[:4].isdigit() and int(set_id[:4]) < 2020
            width = 1400 if old_layout else (1250 if page_no >= 11 else 1245)
            x = 100 if old_layout else (230 if page_no >= 11 else 245)
            whole_name = f"q{number:03d}.png"
            whole = image_dir / whole_name
            question = image_dir / f"q{number:03d}-question.png"
            answer = image_dir / f"q{number:03d}-answer.png"
            subprocess.run(["convert", str(page_dir / f"page-{page_no:02d}.png"), "-crop", f"{width}x{height}+{x}+{top + 2}", "+repage", str(whole)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            split_x = (430 if old_layout else 495) if number <= 40 else (330 if old_layout else 318)
            subprocess.run(["convert", str(whole), "-crop", f"{split_x}x{height}+0+0", "+repage", str(question)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["convert", str(whole), "-crop", f"{width - split_x}x{height}+{split_x}+0", "+repage", str(answer)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            records.append({"number": number, "answer": answers[number], "explanation": explanation(number, answers[number]), "image": f"questions/{whole_name}", "question_image": f"questions/{question.name}", "answer_image": f"questions/{answer.name}", "source_page": page_no})
            number += 1
    if number != 51:
        raise ValueError(f"{set_id}: expected 50 questions, stopped at {number - 1}")
    (out_dir / "questions.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({"label": label, "source_pdf": question_name, "count": 50}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(page_dir / "page-15.png", out_dir / "diagram.png")
    print(f"created {set_id}: 50 questions")


for item in SETS:
    make_set(*item)

catalog_path = OUTPUT_DIR / "exams.json"
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
existing = {item["id"] for item in catalog}
for set_id, label, *_ in SETS:
    if set_id not in existing:
        catalog.append({"id": set_id, "label": label, "data": f"output/{set_id}/questions.json"})
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"catalog: {len(catalog)} exams")
