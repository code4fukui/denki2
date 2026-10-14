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

explanations = {
    1: "左側の5 Ω二つは並列で2.5 Ω。右側は導線で短絡されるため、合成抵抗は2.5 Ω（イ）。",
    2: "抵抗は断面積の2乗ではなく、断面積に反比例する。したがって誤りはロ。",
    3: "発熱量は300 W×2 h×3,600 s/h÷1,000＝2,160 kJ。正答はハ。",
    4: "コンデンサで力率を改善すると無効電流が補償され、電源側の電流は減少する。正答はニ。",
    5: "平衡時の相電圧は200/√3≒116 V。中性点が移動するとa-o間は100 Vとなるためロ。",
    6: "負荷電流は1,600/100＝16 A。往復線路の抵抗は5×0.012×2＝0.12 Ωで、電圧降下は約1.92 V＝2 V（ロ）。",
    7: "スイッチを閉じると負荷電流と電線の電圧降下の関係が変わり、Vは99 Vから102 Vへ3 V上がる（ニ）。",
    8: "3.5 mm²電線の基準許容電流に電流減少係数0.63を掛けると約31 A。正答はハ。",
    9: "需要率100％なので、電動機10 Aと電熱器15 A・20 Aを合計し、10＋15＋20＝45 A（イ）。",
    10: "20 Aの配線用遮断器には2.0 mm電線を用い、20 A定格のコンセント1個とする組合せが適切（ハ）。",
    11: "TSカップリングは、硬質ポリ塩化ビニル電線管どうしを接続する部材（イ）。",
    12: "許容電流から使える電力は600 Wまで。100 Vで最も大きい適切な器具は600 Wの電気がま（ロ）。",
    13: "薄鋼電線管の切断にプリカナイフは使わない。したがって誤りはニ。",
    14: "誘導電動機の回転速度は周波数に比例するため、60 Hzから50 Hzでは低下する。誤りはハ。",
    15: "低圧進相コンデンサを並列接続する主目的は、誘導性負荷の無効電力を補償して力率を改善すること（イ）。",
    16: "写真の材料は金属製可とう電線管で、金属可とう電線管工事に使用する（ハ）。",
    17: "写真の部材はジョイントボックスで、VVFケーブルなどの接続箇所に使用する（イ）。",
    18: "写真はトーチランプ。硬質ポリ塩化ビニル電線管を加熱して曲げる作業に用いる（イ）。",
    19: "終端接続部の絶縁処理として、自己融着性テープを1回・2層だけ巻く方法は必要な処理を満たさないため不適切（イ）。",
    20: "ケーブル工事の支持点間距離は、通常は2 m以下、接触防護場所で垂直なら6 m以下。正答はイ。",
    21: "CD管は主にコンクリート埋込み用で、木造の床下・壁内・天井裏の隠ぺい配管には使用できない（イ）。",
    22: "漏電遮断器を設けても、この条件では機械器具の金属外箱の接地を省略できない。誤りはニ。",
    23: "薄鋼電線管どうしの接続には適切なカップリングを用いる。提示されたコンビネーションカップリングの使用が不適切（ロ）。",
    24: "電力計は瞬時の電力を測る計器で、消費電力量の測定には用いない。誤りはハ。",
    25: "使用電圧200 Vの回路は絶縁抵抗0.2 MΩ以上が必要で、0.18 MΩは基準未満（ロ）。",
    26: "接地抵抗の測定前には、接地極の地電圧が許容値以下であることを確認する（イ）。",
    27: "単相3線式の漏れ電流は、3本の電線をまとめてクランプし、電流の不平衡を測定する（ニ）。",
    28: "配電盤を造営材に取り付ける作業は、電気工事士でなければ従事できない（ロ）。",
    29: "ライティングダクトと差込み接続器はいずれも特定電気用品に該当する組合せ（ニ）。",
    30: "電気設備の技術基準を定める省令は電気工事士法ではなく、電気事業法に基づく。誤りはイ。",
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
        # Split each table row into the question column and the answer column.
        # The general questions and questions 31-40 use a wider question column;
        # the photo-choice pages 41-50 use a narrower one.
        split_x = 495 if qno <= 40 else 318
        question_image = images_dir / f"q{qno:03d}-question.png"
        answer_image = images_dir / f"q{qno:03d}-answer.png"
        subprocess.run([
            "convert", str(dst), "-crop", f"{split_x}x{height}+0+0",
            "+repage", str(question_image)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "convert", str(dst), "-crop", f"{width - split_x}x{height}+{split_x}+0",
            "+repage", str(answer_image)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        records.append({
            "number": qno,
            "answer": answers[qno],
            "explanation": explanations.get(qno, ""),
            "image": f"questions/{filename}",
            "question_image": f"questions/{question_image.name}",
            "answer_image": f"questions/{answer_image.name}",
            "source_page": page_no,
        })

records.sort(key=lambda item: item["number"])
assert [item["number"] for item in records] == list(range(1, 51))
assert len(answers) == 50

(out_dir / "questions.json").write_text(
    json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"created {len(records)} question images and {out_dir / 'questions.json'}")
