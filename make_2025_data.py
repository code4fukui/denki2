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
            10: (26, [236, 538, 787, 1231, 1630, 2088]),
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
            10: (26, [236, 597, 861, 1308, 1634, 2087]),
            11: (31, [647, 818, 925, 1032, 1205, 1378, 1559, 1641, 1752, 1875, 2016]),
            12: (41, [268, 679, 977, 1312, 1719, 2130]),
            13: (46, [266, 768, 1128, 1489, 1845, 2096]),
        },
    },
}

EXPLANATION_TEMPLATES = {
    1: "回路の接続状態を整理し、直列・並列の合成抵抗の式に当てはめると、正答の選択肢になります。",
    2: "オームの法則と電力の関係式（V＝IR、P＝VI）を変形して確認すると、正答の選択肢になります。",
    3: "電力量は、電力または熱量を時間の単位に合わせて計算し、選択肢と比較します。",
    4: "交流回路では、抵抗分とリアクタンス分の関係から電圧・電流の位相と力率を判断します。",
    5: "三相交流の線間電圧・相電圧、線電流・相電流の関係を使って計算します。",
    6: "回路の断線箇所を確認し、残った負荷にかかる電圧と消費電力を求めます。",
    7: "電線の電圧降下を考慮し、負荷電流と電線抵抗から負荷側の電圧を求めます。",
    8: "電線の太さに対応する基準許容電流に、管内の電線本数による電流減少係数を適用します。",
    9: "幹線からの分岐に関する許容電流の規定と、分岐点までの距離の条件を照合します。",
    10: "配線用遮断器、電線の太さ、コンセントの定格が互いに適合する組合せを選びます。",
    11: "器具の構造と、金属管・金属線ぴ工事で求められる接地や固定方法を確認します。",
    12: "電線・コードの種類と許容電流（または許容温度）を基準表と照合します。",
    13: "工事の種類ごとに使用する工具の用途を対応させると、正しい組合せが分かります。",
    14: "電動機の種類・極数・周波数、または始動方式の特徴から該当する選択肢を判断します。",
    15: "機器の目的と組み合わせを確認し、電気設備で実際に使用される機器を選びます。",
    16: "写真の形状・接続部の構造を、電線管や器具の名称・用途と照合します。",
    17: "写真の端子・操作部・外形の特徴を、各種遮断器や開閉器の構造と比較します。",
    18: "工具の刃先・口金・形状から、電気工事での具体的な用途を判断します。",
    19: "低圧屋内配線で使用できる電線の種類と施設条件を、電気工事の規定に照らして判断します。",
    20: "配線方法ごとの施設場所・支持方法・離隔距離の規定を確認します。",
    21: "専用回路や接地など、住宅設備に関する施設条件を問題文の定格と照合します。",
    22: "特殊場所の危険性と、そこで認められる配線・器具の施工方法を対応させます。",
    23: "電線管内の電線本数、管の占積率、接続方法などの施工規定を確認します。",
    24: "測定器を使用する前の電池・零位・測定端子などの準備手順を確認します。",
    25: "絶縁抵抗計の接続方法と測定対象の状態を確認し、正しい測定方法を選びます。",
    26: "接地抵抗計の電池、端子、補助極の配置など、正しい測定手順に照らして判断します。",
    27: "指示計器の構造と目盛板の記号から、測定できる電気量と使用条件を読み取ります。",
    28: "電気工事士法・電気用品安全法など、問題に示された法令の定義と義務を確認します。",
    29: "特定電気用品や屋内配線で使用する材料の指定条件を、法令・技術基準と照合します。",
    30: "一般用電気工作物の範囲と、電圧・発電設備・設置場所に関する定義を確認します。",
}

def explanation_for(number, answer):
    if number <= 30:
        reason = EXPLANATION_TEMPLATES[number]
    else:
        reason = "配線図の記号、接続関係、電源・負荷の位置を確認し、電気的な成立条件と施工方法に照らして判断します。"
    return f"正答は「{answer}」です。{reason}"

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
                "explanation": explanation_for(number, answers[number]),
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
    subprocess.run(["convert", str(page_dir / "page-11.png"), "-crop", "1250x470+230+100", "+repage", str(out_dir / "diagram-intro.png")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"created {set_name}: 50 questions")

for name, config in SETS.items():
    make_set(name, config)
