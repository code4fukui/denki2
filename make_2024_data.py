import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SETS = {
    "2024-upper": {
        "label": "令和6年度上期（2024年5月）",
        "source_pdf": "20240526_co_second_q01.pdf",
        "answers": "ロ ハ ニ イ ロ イ イ ロ ハ イ ハ ロ ニ ロ イ ロ ロ イ ロ ニ イ ロ イ ニ ニ イ ロ イ ハ ニ イ ロ ニ イ ハ ハ ロ イ イ ロ ロ ハ イ イ ニ ニ ニ ロ イ ニ",
        "pages": {
            5: (1, [397, 716, 989, 1274, 1521, 1941]),
            6: (6, [236, 712, 1183, 1481, 2089]),
            7: (10, [236, 627, 830, 979, 1303, 1493, 1688, 2090]),
            8: (17, [236, 654, 1053, 1659, 2016]),
            9: (21, [236, 580, 1068, 1395, 1735, 2074]),
            10: (26, [236, 583, 1037, 1378, 1761, 2071]),
            11: (31, [573, 748, 923, 1027, 1131, 1306, 1516, 1620, 1726, 1900, 2040]),
            12: (41, [264, 626, 915, 1240, 1603, 2001]),
            13: (46, [264, 583, 903, 1293, 1719, 2110]),
        },
    },
    "2024-lower": {
        "label": "令和6年度下期（2024年10月）",
        "source_pdf": "20241027_co_second_q01.pdf",
        "answers": "ロ イ ハ ハ ニ ニ ニ ハ ハ ロ ロ ハ イ ロ ハ ハ ニ イ ハ イ ロ ロ ロ ハ ハ イ ハ イ ロ ロ ロ ハ ハ ハ ニ ニ ロ イ イ イ ニ ハ イ ニ ハ ハ ロ イ イ ロ",
        "pages": {
            5: (1, [397, 716, 955, 1244, 1661, 2067]),
            6: (6, [236, 637, 1376, 1672, 2075]),
            7: (10, [236, 657, 875, 1068, 1306, 1496, 1686, 2089]),
            8: (17, [236, 652, 935, 1333, 1617, 2030]),
            9: (22, [236, 654, 997, 1695, 2017]),
            10: (26, [236, 772, 1036, 1393, 1860, 2079]),
            11: (31, [599, 666, 798, 952, 1113, 1220, 1381, 1534, 1649, 1802, 1957]),
            12: (41, [266, 819, 1077, 1446, 1742, 2109]),
            13: (46, [264, 653, 971, 1292, 1665, 2021]),
        },
    },
}

TEMPLATES = {
    1: "回路の接続状態を整理し、直列・並列の合成抵抗の式に当てはめます。",
    2: "オームの法則と電力の関係式（V＝IR、P＝VI）を変形して確認します。",
    3: "電力量は電力または熱量を時間の単位に合わせて計算します。",
    4: "交流回路では抵抗分とリアクタンス分の関係から位相と力率を判断します。",
    5: "三相交流の線間電圧・相電圧、線電流・相電流の関係を使って計算します。",
    6: "回路の断線箇所を確認し、残った負荷にかかる電圧と消費電力を求めます。",
    7: "電線の電圧降下を考慮し、負荷電流と電線抵抗から負荷側の電圧を求めます。",
    8: "電線の太さと本数に応じた許容電流・電流減少係数を基準表と照合します。",
    9: "幹線からの分岐に関する許容電流の規定と距離の条件を確認します。",
    10: "配線用遮断器、電線の太さ、コンセントの定格が適合する組合せを選びます。",
    11: "器具の構造と、金属管・金属線ぴ工事で求められる施工方法を確認します。",
    12: "電線・コードの種類と許容電流または許容温度を基準表と照合します。",
    13: "工事の種類ごとに使用する工具の用途を対応させます。",
    14: "電動機の種類・極数・周波数、または始動方式の特徴から判断します。",
    15: "機器の目的と組合せを確認し、電気設備で使用される機器を選びます。",
    16: "写真の形状・接続部の構造を、材料や器具の名称・用途と照合します。",
    17: "写真の端子・操作部・外形の特徴を、各種器具の構造と比較します。",
    18: "工具の形状から、電気工事での具体的な用途を判断します。",
    19: "低圧屋内配線で使用できる電線の種類と施設条件を確認します。",
    20: "配線方法ごとの施設場所・支持方法・離隔距離の規定を確認します。",
    21: "専用回路や接地など、住宅設備に関する施設条件を定格と照合します。",
    22: "特殊場所の危険性と、そこで認められる施工方法を対応させます。",
    23: "電線管内の電線本数、占積率、接続方法などの施工規定を確認します。",
    24: "測定器を使用する前の電池・零位・測定端子などの準備手順を確認します。",
    25: "絶縁抵抗計の接続方法と測定対象の状態を確認します。",
    26: "接地抵抗計の電池、端子、補助極の配置など正しい測定手順を確認します。",
    27: "指示計器の構造と目盛板の記号から、測定できる電気量を読み取ります。",
    28: "電気工事士法・電気用品安全法などの定義と義務を確認します。",
    29: "特定電気用品や屋内配線材料の指定条件を法令・技術基準と照合します。",
    30: "一般用電気工作物の範囲と、電圧・発電設備・設置場所の定義を確認します。",
}


def explanation(number, answer):
    reason = TEMPLATES.get(number, "配線図の記号、接続関係、電源・負荷の位置を確認し、電気的な成立条件と施工方法に照らして判断します。")
    return f"正答は「{answer}」です。{reason}"


def make_set(name, config):
    page_dir = ROOT / "tmp" / "pdfs" / name.replace("-", "")
    out_dir = ROOT / "output" / name
    images_dir = out_dir / "questions"
    images_dir.mkdir(parents=True, exist_ok=True)
    answers = dict(enumerate(config["answers"].split(), start=1))
    if len(answers) != 50:
        raise ValueError(f"{name}: expected 50 answers, got {len(answers)}")
    records = []
    for page_no, (first, lines) in config["pages"].items():
        src = page_dir / f"page-{page_no:02d}.png"
        x = 230 if page_no >= 11 else 245
        width = 1250 if page_no >= 11 else 1245
        split_x = 495 if first <= 40 else 318
        for offset, (top, bottom) in enumerate(zip(lines, lines[1:])):
            number = first + offset
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
                "explanation": explanation(number, answers[number]),
                "image": f"questions/{whole_name}",
                "question_image": f"questions/{question.name}",
                "answer_image": f"questions/{answer.name}",
                "source_page": page_no,
            })
    records.sort(key=lambda item: item["number"])
    if [item["number"] for item in records] != list(range(1, 51)):
        raise ValueError(f"{name}: question ranges are incomplete")
    (out_dir / "questions.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({"label": config["label"], "source_pdf": config["source_pdf"], "count": 50}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["convert", str(page_dir / "page-11.png"), "-crop", "1250x470+230+100", "+repage", str(out_dir / "diagram-intro.png")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"created {name}: 50 questions")


for name, config in SETS.items():
    make_set(name, config)
