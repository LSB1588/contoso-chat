"""
Mock Generator Agent - コーポレートサイトのBefore/Afterモック生成
既存のHTMLモックを参照し、リサーチ結果に基づいてアップデート
"""
from __future__ import annotations

import os
import json
from pathlib import Path


BEFORE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>{company_name} - 現状サイト診断 (Before)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'MS Gothic', monospace; background: #f5f5f0; color: #333; font-size:13px; }}
    .header {{ background:#003366; color:white; padding:8px 16px; font-size:12px; }}
    .header h1 {{ font-size:18px; font-weight:bold; display:inline; }}
    nav {{ background:#004a99; padding:4px 0; }}
    nav a {{ color:white; text-decoration:none; padding:6px 14px; display:inline-block; font-size:12px; border-right:1px solid #336; }}
    nav a:hover {{ background:#003366; }}
    .hero {{ background:#e8e8e8; padding:20px; border-bottom:2px solid #ccc; }}
    .hero img {{ width:100%; max-width:600px; display:block; margin:0 auto; background:#ccc; height:200px; }}
    .issue-badge {{ background:red; color:white; padding:2px 8px; border-radius:3px; font-size:11px; margin-left:6px; }}
    .warn {{ color:red; font-size:11px; margin-top:4px; }}
    .content {{ max-width:960px; margin:0 auto; padding:16px; }}
    .section {{ background:white; padding:14px; margin:10px 0; border:1px solid #ccc; }}
    .section h2 {{ font-size:15px; color:#003366; border-bottom:1px solid #ccc; padding-bottom:4px; margin-bottom:8px; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    td, th {{ border:1px solid #ccc; padding:4px 8px; }}
    th {{ background:#003366; color:white; }}
    .fax-only {{ background:#fff3cd; border:1px solid #ffc107; padding:6px; font-size:11px; }}
    .outdated {{ color:#888; font-size:11px; }}
    footer {{ background:#222; color:#aaa; text-align:center; padding:10px; font-size:11px; }}
    .heuristic-panel {{ background:#fff8f8; border:1px solid #f88; padding:10px; margin-top:10px; }}
    .heuristic-panel h3 {{ color:#c00; font-size:13px; }}
    .score-bar {{ display:flex; align-items:center; margin:3px 0; font-size:11px; }}
    .score-bar .label {{ width:200px; color:#555; }}
    .score-bar .bar {{ height:10px; background:#e55; border-radius:2px; }}
    .score-total {{ font-size:16px; color:#c00; font-weight:bold; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{company_name}</h1>
    <span class="issue-badge">課題あり</span>
    <span class="outdated"> 推定最終更新: {last_update} ／ スマートフォン対応: {mobile}</span>
  </div>
  <nav>
    <a href="#">トップ</a>
    <a href="#">製品情報</a>
    <a href="#">会社概要</a>
    <a href="#">お問い合わせ</a>
  </nav>
  <div class="hero">
    <div style="background:#bbb;height:180px;display:flex;align-items:center;justify-content:center;color:#666;">
      画像読み込みエラー / 低解像度画像
    </div>
  </div>

  <div class="content">

    <div class="section">
      <h2>■ お問い合わせ方法</h2>
      <div class="fax-only">
        ⚠️ お問い合わせはお電話またはFAXのみとなっております。<br>
        TEL: 0X-XXXX-XXXX（平日 9:00〜17:00）<br>
        FAX: 0X-XXXX-XXXX<br>
        <span class="warn">✕ Webフォームは設置されていません</span>
      </div>
    </div>

    <div class="section">
      <h2>■ 製品・サービス一覧</h2>
      <table>
        <tr><th>製品名</th><th>更新状況</th><th>詳細</th></tr>
        {product_rows}
      </table>
      <p class="warn">※ 一部製品の情報が古い可能性があります</p>
    </div>

    <div class="section">
      <h2>■ ウェブサイト診断スコア（ニールセン10原則）</h2>
      <div class="heuristic-panel">
        <h3>総合スコア: <span class="score-total">{total_score}/50点</span>（評価: {score_label}）</h3>
        <br>
        {score_bars}
        <br>
        <strong style="color:#c00">主な課題:</strong><br>
        {issues_html}
      </div>
    </div>

    <div class="section">
      <h2>■ 不足している機能</h2>
      <ul style="font-size:12px; padding-left:16px;">
        {missing_features}
      </ul>
    </div>

  </div>

  <footer>
    Copyright © {company_name} All Rights Reserved.
    <span class="warn"> ※ このページはBefore診断モックアップです</span>
  </footer>
</body>
</html>"""


AFTER_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{company_name} - 改善提案 (After)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family:'Noto Sans JP',sans-serif; color:#1a1a2e; background:#f8fafc; }}
    /* HEADER */
    header {{ background:linear-gradient(135deg,{color1},{color2}); color:white; padding:0 40px; position:sticky; top:0; z-index:100; box-shadow:0 2px 12px rgba(0,0,0,.15); }}
    .header-inner {{ max-width:1200px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; height:64px; }}
    .logo {{ font-size:22px; font-weight:700; letter-spacing:1px; }}
    nav a {{ color:rgba(255,255,255,.9); text-decoration:none; margin-left:28px; font-size:14px; font-weight:500; transition:.2s; }}
    nav a:hover {{ color:white; border-bottom:2px solid white; }}
    /* HERO */
    .hero {{ background:linear-gradient(135deg,{color1}dd,{color2}cc); color:white; padding:80px 40px; text-align:center; }}
    .hero h1 {{ font-size:36px; font-weight:700; margin-bottom:16px; }}
    .hero p {{ font-size:16px; opacity:.9; max-width:560px; margin:0 auto 32px; }}
    .btn-primary {{ background:white; color:{color1}; padding:14px 36px; border-radius:30px; font-weight:700; font-size:15px; text-decoration:none; display:inline-block; box-shadow:0 4px 16px rgba(0,0,0,.2); transition:.2s; }}
    .btn-primary:hover {{ transform:translateY(-2px); box-shadow:0 6px 20px rgba(0,0,0,.25); }}
    /* FEATURES */
    .section {{ max-width:1200px; margin:60px auto; padding:0 24px; }}
    .section-title {{ text-align:center; font-size:26px; font-weight:700; margin-bottom:8px; }}
    .section-sub {{ text-align:center; color:#666; margin-bottom:40px; font-size:14px; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:24px; }}
    .card {{ background:white; border-radius:12px; padding:28px; box-shadow:0 2px 12px rgba(0,0,0,.08); transition:.2s; }}
    .card:hover {{ transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,.12); }}
    .card-icon {{ font-size:36px; margin-bottom:14px; }}
    .card h3 {{ font-size:16px; font-weight:700; margin-bottom:8px; color:{color1}; }}
    .card p {{ font-size:13px; color:#555; line-height:1.7; }}
    /* PRODUCTS */
    .products-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:20px; }}
    .product-card {{ background:white; border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.08); }}
    .product-img {{ height:160px; background:linear-gradient(135deg,{color1}22,{color2}22); display:flex; align-items:center; justify-content:center; font-size:40px; }}
    .product-body {{ padding:16px; }}
    .product-body h4 {{ font-size:15px; font-weight:700; margin-bottom:6px; }}
    .product-body p {{ font-size:12px; color:#666; line-height:1.6; }}
    .badge-new {{ background:{color1}; color:white; font-size:10px; padding:2px 8px; border-radius:10px; margin-left:6px; }}
    /* CONTACT FORM */
    .contact-section {{ background:linear-gradient(135deg,{color1}11,{color2}11); border-radius:16px; padding:48px; margin:60px auto; max-width:800px; }}
    .contact-section h2 {{ font-size:24px; font-weight:700; margin-bottom:8px; color:{color1}; }}
    form {{ display:grid; gap:14px; margin-top:24px; }}
    .form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    input, textarea, select {{ width:100%; padding:12px 14px; border:1px solid #ddd; border-radius:8px; font-size:14px; font-family:inherit; outline:none; transition:.2s; }}
    input:focus, textarea:focus, select:focus {{ border-color:{color1}; box-shadow:0 0 0 3px {color1}22; }}
    textarea {{ height:120px; resize:vertical; }}
    .submit-btn {{ background:linear-gradient(135deg,{color1},{color2}); color:white; border:none; padding:14px; border-radius:8px; font-size:16px; font-weight:700; cursor:pointer; transition:.2s; }}
    .submit-btn:hover {{ opacity:.9; transform:translateY(-1px); }}
    .form-note {{ font-size:12px; color:#888; text-align:center; margin-top:8px; }}
    /* RECRUITMENT */
    .recruit-section {{ background:{color1}; color:white; padding:48px 40px; text-align:center; border-radius:16px; margin:60px auto; max-width:1200px; }}
    .recruit-section h2 {{ font-size:26px; font-weight:700; margin-bottom:12px; }}
    .recruit-section p {{ opacity:.9; margin-bottom:24px; }}
    .btn-white {{ background:white; color:{color1}; padding:12px 32px; border-radius:24px; font-weight:700; text-decoration:none; display:inline-block; }}
    /* FOOTER */
    footer {{ background:#1a1a2e; color:#aaa; text-align:center; padding:28px; font-size:12px; }}
    footer a {{ color:#aaa; text-decoration:none; margin:0 12px; }}
    .improvement-tag {{ background:#10b981; color:white; font-size:10px; padding:2px 8px; border-radius:10px; margin-left:6px; }}
    /* MOBILE */
    @media(max-width:768px) {{
      .hero h1 {{ font-size:24px; }}
      .form-row {{ grid-template-columns:1fr; }}
      nav a {{ margin-left:12px; font-size:12px; }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-inner">
      <div class="logo">{company_name}</div>
      <nav>
        <a href="#">トップ</a>
        <a href="#">製品・サービス</a>
        <a href="#">会社情報</a>
        <a href="#">採用情報 <span class="improvement-tag">NEW</span></a>
        <a href="#contact" class="btn-primary" style="padding:8px 20px;font-size:13px;">お問い合わせ</a>
      </nav>
    </div>
  </header>

  <section class="hero">
    <h1>{company_name}</h1>
    <p>{hero_description}</p>
    <a href="#contact" class="btn-primary">無料相談・お問い合わせ</a>
  </section>

  <section class="section">
    <div class="section-title">改善ポイント</div>
    <div class="section-sub">リニューアルにより追加・改善される機能</div>
    <div class="cards">
      {improvement_cards}
    </div>
  </section>

  <section class="section">
    <div class="section-title">製品・サービス</div>
    <div class="section-sub">最新情報で更新された製品ラインナップ</div>
    <div class="products-grid">
      {product_cards}
    </div>
  </section>

  <div id="contact" class="contact-section">
    <h2>お問い合わせ <span class="improvement-tag">NEW 24時間受付</span></h2>
    <p style="color:#555;font-size:14px;">ご質問・お見積もり・資料請求など、お気軽にご連絡ください。</p>
    <form>
      <div class="form-row">
        <input type="text" placeholder="会社名 *" required>
        <input type="text" placeholder="お名前 *" required>
      </div>
      <div class="form-row">
        <input type="email" placeholder="メールアドレス *" required>
        <input type="tel" placeholder="電話番号">
      </div>
      <select>
        <option value="">お問い合わせ種別を選択してください</option>
        <option>製品・サービスに関するお問い合わせ</option>
        <option>お見積もり依頼</option>
        <option>資料請求</option>
        <option>その他</option>
      </select>
      <textarea placeholder="お問い合わせ内容をご記入ください"></textarea>
      <button type="submit" class="submit-btn">送信する</button>
      <p class="form-note">※ 通常1〜2営業日以内にご返信いたします。</p>
    </form>
  </div>

  <div class="recruit-section">
    <h2>採用情報 <span class="improvement-tag">NEW</span></h2>
    <p>私たちと一緒に{industry}の未来を創りませんか？<br>積極的に新しいメンバーを募集しています。</p>
    <a href="#" class="btn-white">採用情報を見る</a>
  </div>

  <footer>
    <p>Copyright © {company_name} All Rights Reserved.</p>
    <p style="margin-top:8px;">
      <a href="#">会社概要</a>
      <a href="#">プライバシーポリシー</a>
      <a href="#">サイトマップ</a>
      <a href="#">English</a>
    </p>
    <p style="margin-top:8px; color:#4ade80; font-size:11px;">✓ このページはAfterリニューアル提案モックアップです</p>
  </footer>
</body>
</html>"""


COMPANY_COLORS = {
    "astryda":    ("#1a237e", "#0d47a1"),
    "bell_fresh": ("#1b5e20", "#2e7d32"),
}

COMPANY_HERO_DESC = {
    "astryda": "精密光学技術とLED投影技術で、製造業・医療・半導体分野のお客様の課題を解決します。",
    "bell_fresh": "新鮮なカット野菜を安定供給。食品加工のプロとして40年のノウハウで食卓を支えます。",
}


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


def generate_before_mock(company: dict, research: dict) -> str:
    company_id = company["id"]
    color1, color2 = COMPANY_COLORS.get(company_id, ("#1a237e", "#0d47a1"))
    scores = research.get("heuristic_scores", [])
    total = research.get("total_score", 0)

    # Product rows
    products = research.get("products", []) or ["主力製品A", "主力製品B", "主力製品C"]
    product_rows = "\n".join(
        f'<tr><td>{p}</td><td style="color:orange">要確認</td><td>詳細ページなし</td></tr>'
        for p in products[:5]
    )
    if not product_rows:
        product_rows = '<tr><td>製品情報</td><td style="color:orange">要確認</td><td>更新停止の可能性</td></tr>'

    # Score bars
    score_bars = ""
    for s in scores[:6]:
        w = s["score"] * 20
        score_bars += f'<div class="score-bar"><span class="label">{s["principle_ja"]}</span><div class="bar" style="width:{w}px"></div><span style="margin-left:6px">{s["score"]}/5</span></div>\n'

    # Issues
    issues = research.get("top_issues", [])
    issues_html = "".join(f'<span style="color:#c00">・{i}</span><br>' for i in issues[:4])
    if not issues_html:
        issues_html = "<span style='color:#c00'>・詳細調査中</span>"

    # Missing features
    missing = []
    if not research.get("has_contact_form"):
        missing.append("<li style='color:red'>✕ お問い合わせフォームなし</li>")
    if not research.get("has_mobile_friendly"):
        missing.append("<li style='color:red'>✕ スマートフォン対応なし</li>")
    if not research.get("has_english_page"):
        missing.append("<li style='color:red'>✕ 英語ページなし</li>")
    if not research.get("has_recruitment_page"):
        missing.append("<li style='color:orange'>△ 採用ページなし</li>")
    if not research.get("has_sns_links"):
        missing.append("<li style='color:orange'>△ SNSリンクなし</li>")
    missing_features = "\n".join(missing) or "<li>特に問題なし</li>"

    return BEFORE_TEMPLATE.format(
        company_name=company["name"],
        last_update=research.get("last_update_estimate", "不明"),
        mobile="非対応" if not research.get("has_mobile_friendly") else "対応済み",
        product_rows=product_rows,
        total_score=total,
        score_label=_score_label(total),
        score_bars=score_bars,
        issues_html=issues_html,
        missing_features=missing_features,
    )


def generate_after_mock(company: dict, research: dict) -> str:
    company_id = company["id"]
    color1, color2 = COMPANY_COLORS.get(company_id, ("#1a237e", "#0d47a1"))
    hero_desc = COMPANY_HERO_DESC.get(company_id, company["name"])

    suggestions = research.get("top_suggestions", [
        "お問い合わせフォームを設置し、24時間受付を実現",
        "スマートフォン対応デザインで、モバイルからのアクセスに対応",
        "英語ページを追加し、海外からの問い合わせを獲得",
        "採用ページで人材確保コストを削減",
    ])

    icons = ["📩", "📱", "🌐", "💼", "🔍", "⚡"]
    improvement_cards = ""
    for i, s in enumerate(suggestions[:4]):
        improvement_cards += f"""
        <div class="card">
          <div class="card-icon">{icons[i % len(icons)]}</div>
          <h3>改善ポイント {i+1}</h3>
          <p>{s}</p>
        </div>"""

    products = research.get("products", []) or ["主力製品A", "主力製品B", "主力製品C"]
    emojis = ["🔬", "💡", "🏭", "🌿", "🥦", "🍅"]
    product_cards = ""
    for i, p in enumerate(products[:3]):
        product_cards += f"""
        <div class="product-card">
          <div class="product-img">{emojis[i % len(emojis)]}</div>
          <div class="product-body">
            <h4>{p} <span class="badge-new">更新済</span></h4>
            <p>最新の仕様・価格・納期情報を掲載。オンラインでのお問い合わせも可能です。</p>
          </div>
        </div>"""

    return AFTER_TEMPLATE.format(
        company_name=company["name"],
        industry=company["industry"],
        hero_description=hero_desc,
        color1=color1,
        color2=color2,
        improvement_cards=improvement_cards,
        product_cards=product_cards,
    )


def save_mocks(company: dict, research: dict, output_dir: str) -> dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    company_id = company["id"]

    before_html = generate_before_mock(company, research)
    after_html = generate_after_mock(company, research)

    before_path = f"{output_dir}/{company_id}_before.html"
    after_path = f"{output_dir}/{company_id}_after.html"

    with open(before_path, "w", encoding="utf-8") as f:
        f.write(before_html)
    with open(after_path, "w", encoding="utf-8") as f:
        f.write(after_html)

    print(f"[MockGen] Saved: {before_path}")
    print(f"[MockGen] Saved: {after_path}")
    return {"before": before_path, "after": after_path}
