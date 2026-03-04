"""
Approach Agent - 企業ごとのカスタム営業メール・電話スクリプト生成
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _bool_to_ja(value: bool) -> str:
    return "あり" if value else "なし"


def _score_label(score: int, max_score: int = 50) -> str:
    pct = score / max_score * 100
    if pct >= 80:
        return "良好"
    elif pct >= 60:
        return "要改善"
    elif pct >= 40:
        return "問題あり"
    else:
        return "要緊急対応"


def generate_email_a(company: dict, research: dict) -> str:
    name = company["name"]
    industry = company["industry"]
    url = company["url"]
    issues = research.get("top_issues", [])
    has_form = research.get("has_contact_form", False)
    has_mobile = research.get("has_mobile_friendly", False)
    has_en = research.get("has_english_page", False)

    pain_points = []
    if not has_form:
        pain_points.append("お問い合わせフォームがなく、電話・FAXのみのご対応")
    if not has_mobile:
        pain_points.append("スマートフォン向け表示最適化が未対応")
    if not has_en:
        pain_points.append("英語ページが不在で、海外からのアクセスに対応できない状況")
    if issues:
        pain_points.append(issues[0])

    pain_text = "\n".join(f"・{p}" for p in pain_points[:3])

    subjects = [
        f"【{name}様へ】ウェブサイトの課題を無料で診断いたします",
        f"【Web診断レポート無料進呈】{industry}分野でのデジタル競争力強化のご提案",
        f"御社サイト、新規取引先獲得のボトルネックになっていませんか？"
    ]

    body = f"""
{name}
ご担当者様

突然のご連絡、大変失礼いたします。
ウェブ制作・デジタルマーケティングを専門とする〇〇株式会社の〇〇と申します。

貴社の事業内容と{industry}分野での実績に大変注目しており、
この度ウェブサイトに関するご提案をさせていただきたく、ご連絡いたしました。

貴社のウェブサイト（{url}）を拝見したところ、
貴社の高い技術力・信頼性がオンライン上では十分に伝わりにくい状況にあると感じました。

具体的には以下の点が気になりました：
{pain_text}

このような課題は、オンラインでの新規取引先獲得機会の損失に直結いたします。

つきましては、完全無料・ご義務なしで以下をご提供させていただきます：
✅ ウェブサイト診断レポート（PDF）
✅ 同業他社との比較分析
✅ 改善後のイメージモックアップ（Before/After）

ご多忙中、大変恐縮ではございますが、
ご関心をお持ちいただけましたら、本メールへの返信にてご連絡をお待ちしております。

どうぞよろしくお願い申し上げます。

〇〇株式会社 ウェブ戦略部門
担当: 〇〇 〇〇
TEL: 03-XXXX-XXXX
MAIL: sales@xxxx.co.jp
""".strip()

    return {
        "type": "Email A",
        "label": "初回接触メール",
        "subject_options": subjects,
        "body": body
    }


def generate_email_b(company: dict, research: dict) -> str:
    name = company["name"]
    score = research.get("total_score", 0)
    label = _score_label(score)

    body = f"""
{name}
ご担当者様

先週ウェブサイト診断に関するご案内をお送りした〇〇株式会社の〇〇でございます。
ご多忙中のところ大変恐縮ですが、再度ご連絡させていただきました。

先日ご案内したウェブサイト診断につきまして、
弊社独自の評価指標（ニールセン10原則準拠）でスコアリングを行いましたところ、
貴社サイトは 50点満点中 {score}点（評価：{label}）という結果でした。

この点数は、同業他社の平均値と比較すると改善余地が大きく、
適切なリニューアルにより新規問い合わせ数を2〜3倍に改善できる可能性がございます。

改善後のイメージとして、具体的なBefore/Afterモックアップをご用意することも可能です。
まず無料の診断レポートをご覧いただき、
ご興味があればモックアップをご送付させていただければと存じます。

ご返信またはお電話（03-XXXX-XXXX）にてお気軽にご連絡ください。

〇〇株式会社 ウェブ戦略部門
担当: 〇〇 〇〇
TEL: 03-XXXX-XXXX
MAIL: sales@xxxx.co.jp
""".strip()

    return {
        "type": "Email B",
        "label": "フォローアップメール（1週間後）",
        "subject_options": [
            f"【再ご連絡】御社サイトのスコアは{score}/50点でした",
            "【無料モックアップご提供可能】ウェブサイト改善イメージのご案内",
        ],
        "body": body
    }


def generate_email_c(company: dict, research: dict) -> str:
    name = company["name"]
    suggestions = research.get("top_suggestions", [])
    suggestions_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(suggestions[:4]))

    body = f"""
{name}
ご担当者様

〇〇株式会社の〇〇でございます。
以前ご連絡させていただいた件につきまして、
今回はウェブサイトのBefore/Afterモックアップをご用意いたしましたので、ぜひご覧ください。

【添付モックアップの改善ポイント】
{suggestions_text}

現状のサイトの課題と、リニューアル後のイメージを視覚的にお伝えできるよう作成しました。
いずれも具体的な改善施策に基づいており、制作費・期間の目安もご提示可能です。

【ご参考】制作標準費用（目安）
・コーポレートサイトリニューアル: 50〜150万円
・制作期間: 2〜4ヶ月

費用・内容については完全に御社のご予算・ご要望に合わせて対応いたします。
まずは30分程度のオンライン説明会（Zoom等）をご提案させていただけますと幸いです。

ご都合の良い日時をお知らせいただければ、こちらで調整いたします。

どうぞよろしくお願い申し上げます。

〇〇株式会社 ウェブ戦略部門
担当: 〇〇 〇〇
TEL: 03-XXXX-XXXX
MAIL: sales@xxxx.co.jp
""".strip()

    return {
        "type": "Email C",
        "label": "提案メール（モックアップ送付時）",
        "subject_options": [
            f"【{name}様】Before/Afterモックアップをお送りします",
            "【改善提案資料】ウェブサイトリニューアルのご提案",
        ],
        "body": body
    }


def generate_phone_script(company: dict, research: dict) -> dict:
    name = company["name"]
    issues = research.get("top_issues", [])
    key_issue = issues[0] if issues else "ウェブサイトの最新化"

    return {
        "type": "phone_script",
        "label": "電話アプローチスクリプト（約90秒）",
        "reception_pattern": f"""
【受付・書記対応パターン】
「お電話ありがとうございます。ウェブ制作の〇〇株式会社と申します。
御社のウェブサイトに関するご提案でご連絡させていただきましたが、
ウェブサイトご担当の方はいらっしゃいますでしょうか。」

（担当者につないでもらえた場合は下記パターンへ）
""".strip(),
        "decision_maker_pattern": f"""
【担当者接続パターン（約90秒）】
「突然のお電話、大変失礼いたします。
〇〇株式会社の〇〇と申します。

{name}様のウェブサイトを拝見し、
{key_issue}という点でご提案できることがあると思いまして、
ご連絡させていただきました。

現在、同業他社様で同様の課題を改善し、
オンラインでの問い合わせが2〜3倍に増えた事例が出ております。

まずは無料のウェブサイト診断レポートをメールでお送りさせていただくことは可能でしょうか。
ご覧いただいた上で、もし改善案についてご興味があればお時間をいただければと思います。

ご担当者様のメールアドレスをお伺いできますでしょうか。」
""".strip(),
        "objection_pattern": """
【断られた場合の対応】
Q: 「今は必要ない」
A: 「かしこまりました。無料の診断レポートだけでもご覧いただけますでしょうか。
   参考情報として、業界動向の分析資料もご一緒にお送りいたします。」

Q: 「予算がない」
A: 「承知いたしました。小規模な改善から始めるプランもご用意しており、
   月額費用ゼロから始められる選択肢もございます。まず情報だけでも。」

Q: 「担当者が不在」
A: 「それでは、ご担当者様のお名前とメールアドレスをお伺いできますでしょうか。
   詳細を資料としてお送りいたします。」
""".strip()
    }


def generate_approach_package(company: dict, research: dict) -> dict:
    return {
        "company_id": company["id"],
        "company_name": company["name"],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "emails": [
            generate_email_a(company, research),
            generate_email_b(company, research),
            generate_email_c(company, research),
        ],
        "phone_script": generate_phone_script(company, research),
        "checklist": [
            "Email A 送信（初回接触）",
            "3日後: メール開封確認、未開封なら件名変更の上再送",
            "1週間後: Email B 送信（フォローアップ）",
            "Email B 後3日: 電話アプローチ実施",
            "電話後: Email C 送信（モックアップ添付）",
            "2週間後: オンライン説明会の開催",
        ]
    }


def save_approach(result: dict, output_dir: str) -> str:
    import os
    os.makedirs(output_dir, exist_ok=True)
    company_id = result["company_id"]

    # Markdownで出力
    md_path = f"{output_dir}/{company_id}_approach.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {result['company_name']} 営業アプローチパッケージ\n")
        f.write(f"**生成日時:** {result['generated_at']}\n\n---\n\n")

        for email in result["emails"]:
            f.write(f"## {email['type']}: {email['label']}\n\n")
            f.write("### 件名案\n")
            for s in email["subject_options"]:
                f.write(f"> {s}\n\n")
            f.write("### 本文\n```\n")
            f.write(email["body"])
            f.write("\n```\n\n---\n\n")

        phone = result["phone_script"]
        f.write(f"## 電話スクリプト\n\n")
        f.write(f"### 受付対応\n```\n{phone['reception_pattern']}\n```\n\n")
        f.write(f"### 担当者接続時\n```\n{phone['decision_maker_pattern']}\n```\n\n")
        f.write(f"### 断られた場合\n```\n{phone['objection_pattern']}\n```\n\n")

        f.write("## チェックリスト\n")
        for item in result["checklist"]:
            f.write(f"- [ ] {item}\n")

    print(f"[Approach] Saved: {md_path}")
    return md_path
