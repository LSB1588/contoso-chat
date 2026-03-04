"""
Research Agent - 企業情報の収集とニールセン方式ヒューリスティック調査
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup


NIELSEN_PRINCIPLES = [
    ("visibility",         "Visibility of system status",          "システム状態の可視性"),
    ("real_world_match",   "Match between system and real world",  "システムと現実の対応"),
    ("user_control",       "User control and freedom",             "ユーザーコントロールと自由"),
    ("consistency",        "Consistency and standards",            "一貫性と標準"),
    ("error_prevention",   "Error prevention",                     "エラー防止"),
    ("recognition",        "Recognition rather than recall",       "記憶より認識"),
    ("flexibility",        "Flexibility and efficiency",           "柔軟性と効率"),
    ("aesthetic",          "Aesthetic and minimalist design",      "審美的でミニマルなデザイン"),
    ("error_recovery",     "Help users recognize, diagnose, recover from errors",
                                                                   "エラーの認識・診断・回復を助ける"),
    ("help_docs",          "Help and documentation",               "ヘルプとドキュメント"),
]


@dataclass
class HeuristicScore:
    key: str
    principle_en: str
    principle_ja: str
    score: int          # 1-5
    issues: list[str]
    suggestions: list[str]


@dataclass
class CompanyResearch:
    company_id: str
    company_name: str
    url: str
    researched_at: str
    # basic info
    page_title: str = ""
    description: str = ""
    last_update_estimate: str = "不明"
    # feature checklist
    has_contact_form: bool = False
    has_english_page: bool = False
    has_recruitment_page: bool = False
    has_mobile_friendly: bool = False
    has_sns_links: bool = False
    has_online_shop: bool = False
    # products / services
    products: list[str] = field(default_factory=list)
    inactive_products: list[str] = field(default_factory=list)
    # heuristic
    heuristic_scores: list[dict] = field(default_factory=list)
    total_score: int = 0
    max_score: int = 50
    top_issues: list[str] = field(default_factory=list)
    top_suggestions: list[str] = field(default_factory=list)
    # raw
    raw_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _fetch(url: str, timeout: int = 15) -> Optional[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[WARN] fetch failed: {url} -> {e}")
        return None


def _parse_basic(soup: BeautifulSoup, base_url: str) -> dict:
    info: dict = {}

    # title
    title_tag = soup.find("title")
    info["page_title"] = title_tag.get_text(strip=True) if title_tag else ""

    # meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        info["description"] = meta["content"][:200]
    else:
        info["description"] = ""

    # all text
    info["raw_text"] = soup.get_text(" ", strip=True)[:5000]

    # links for feature detection
    links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    link_text = [a.get_text(strip=True).lower() for a in soup.find_all("a")]
    all_text_lower = info["raw_text"].lower()
    links_lower = [l.lower() for l in links]

    # contact form
    forms = soup.find_all("form")
    info["has_contact_form"] = len(forms) > 0

    # english page
    info["has_english_page"] = any(
        "en" in l or "/english" in l or "/en/" in l for l in links_lower
    ) or "english" in all_text_lower

    # recruitment
    info["has_recruitment_page"] = any(
        kw in all_text_lower for kw in ["採用", "recruit", "career", "求人", "採用情報"]
    )

    # sns
    sns_domains = ["twitter.com", "facebook.com", "instagram.com", "linkedin.com",
                   "youtube.com", "x.com", "tiktok.com"]
    info["has_sns_links"] = any(
        any(sns in l for sns in sns_domains) for l in links_lower
    )

    # mobile friendly (viewport meta)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    info["has_mobile_friendly"] = viewport is not None

    # last update estimate
    time_tags = soup.find_all(["time", "meta"], attrs=True)
    dates_found = []
    for tag in soup.find_all(["p", "span", "div", "small", "li"]):
        txt = tag.get_text(" ", strip=True)
        m = re.search(r"(20\d{2})[年\-/\.](0?[1-9]|1[0-2])[月\-/\.]", txt)
        if m:
            dates_found.append(m.group(0))
    if dates_found:
        info["last_update_estimate"] = dates_found[-1]
    else:
        info["last_update_estimate"] = "不明"

    return info


def _heuristic_eval(soup: BeautifulSoup, basic: dict) -> list[HeuristicScore]:
    raw = basic.get("raw_text", "").lower()
    scores: list[HeuristicScore] = []

    # 1. Visibility of system status
    has_breadcrumb = bool(soup.find(class_=lambda c: c and "breadcrumb" in c.lower()))
    has_loader = bool(soup.find(attrs={"id": lambda x: x and "load" in x.lower()}))
    s1 = HeuristicScore(
        key="visibility", principle_en=NIELSEN_PRINCIPLES[0][1],
        principle_ja=NIELSEN_PRINCIPLES[0][2],
        score=2 if not has_breadcrumb else 3,
        issues=["現在地を示すブレッドクラムナビゲーションが不明瞭"] if not has_breadcrumb else [],
        suggestions=["パンくずリストを全ページに追加し、階層構造を明示する"]
    )
    scores.append(s1)

    # 2. Match between system and real world
    jargon_count = sum(raw.count(w) for w in ["仕様", "ルクス", "照度", "lm", "spec"])
    s2 = HeuristicScore(
        key="real_world_match", principle_en=NIELSEN_PRINCIPLES[1][1],
        principle_ja=NIELSEN_PRINCIPLES[1][2],
        score=3 if jargon_count < 5 else 2,
        issues=["専門用語・型番の羅列が多く、初見ユーザーには理解困難"] if jargon_count >= 5 else [],
        suggestions=["製品ページに用語解説・ユースケース図を追加する"]
    )
    scores.append(s2)

    # 3. User control and freedom
    nav_links = soup.find_all("a")
    has_back_to_top = any("top" in a.get("href", "").lower() or
                           "上に戻る" in a.get_text() or "トップ" in a.get_text()
                           for a in nav_links)
    s3 = HeuristicScore(
        key="user_control", principle_en=NIELSEN_PRINCIPLES[2][1],
        principle_ja=NIELSEN_PRINCIPLES[2][2],
        score=2 if not has_back_to_top else 3,
        issues=["ページ内の戻るボタン・Undo操作が不在で、ユーザーが迷いやすい"],
        suggestions=["グローバルナビの固定表示（sticky nav）と「トップへ戻る」ボタンを追加"]
    )
    scores.append(s3)

    # 4. Consistency and standards
    buttons = soup.find_all(["button", "input"])
    h_tags = [soup.find_all(f"h{i}") for i in range(1, 5)]
    inconsistent_hierarchy = any(
        len(h_tags[i]) > 0 and len(h_tags[i - 1]) == 0 for i in range(1, 4)
    )
    s4 = HeuristicScore(
        key="consistency", principle_en=NIELSEN_PRINCIPLES[3][1],
        principle_ja=NIELSEN_PRINCIPLES[3][2],
        score=2 if inconsistent_hierarchy else 3,
        issues=["見出し階層が一貫しておらず、スクリーンリーダー対応が不十分"] if inconsistent_hierarchy else [],
        suggestions=["H1→H2→H3 の見出し階層を統一し、CSSデザインも統一する"]
    )
    scores.append(s4)

    # 5. Error prevention
    has_form = basic.get("has_contact_form", False)
    s5 = HeuristicScore(
        key="error_prevention", principle_en=NIELSEN_PRINCIPLES[4][1],
        principle_ja=NIELSEN_PRINCIPLES[4][2],
        score=1 if not has_form else 3,
        issues=["問い合わせフォームがなく、電話・FAXのみで入力エラーが発生しやすい"] if not has_form else [],
        suggestions=["バリデーション付きWebフォームを設置し、誤入力防止・24時間受付を実現する"]
    )
    scores.append(s5)

    # 6. Recognition rather than recall
    nav = soup.find("nav") or soup.find(class_=lambda c: c and "nav" in str(c).lower())
    s6 = HeuristicScore(
        key="recognition", principle_en=NIELSEN_PRINCIPLES[5][1],
        principle_ja=NIELSEN_PRINCIPLES[5][2],
        score=2 if not nav else 3,
        issues=["グローバルナビが不明瞭で、ユーザーがページ間の移動を記憶する必要がある"] if not nav else [],
        suggestions=["常時表示のグローバルナビゲーションと視覚的なアイコンでサイト構造を明示"]
    )
    scores.append(s6)

    # 7. Flexibility and efficiency
    has_search = bool(soup.find("input", attrs={"type": "search"})) or \
                 bool(soup.find("form", attrs={"role": "search"}))
    s7 = HeuristicScore(
        key="flexibility", principle_en=NIELSEN_PRINCIPLES[6][1],
        principle_ja=NIELSEN_PRINCIPLES[6][2],
        score=1 if not has_search else 3,
        issues=["サイト内検索機能が不在で、製品を探す手間が大きい"] if not has_search else [],
        suggestions=["サイト内検索・製品フィルター機能を追加し、リピートユーザーの効率を向上させる"]
    )
    scores.append(s7)

    # 8. Aesthetic and minimalist design
    img_count = len(soup.find_all("img"))
    text_density = len(raw) / max(img_count, 1)
    aesthetic_score = 3 if 50 < text_density < 500 else 2
    s8 = HeuristicScore(
        key="aesthetic", principle_en=NIELSEN_PRINCIPLES[7][1],
        principle_ja=NIELSEN_PRINCIPLES[7][2],
        score=aesthetic_score,
        issues=["情報密度が高すぎる、または画像が少なくビジュアル訴求力が低い"] if aesthetic_score < 3 else [],
        suggestions=["製品写真・インフォグラフィックを活用し、テキスト量を30%削減する"]
    )
    scores.append(s8)

    # 9. Error recovery
    error_pages = any("404" in l or "error" in l for l in
                      [a.get("href", "") for a in soup.find_all("a")])
    s9 = HeuristicScore(
        key="error_recovery", principle_en=NIELSEN_PRINCIPLES[8][1],
        principle_ja=NIELSEN_PRINCIPLES[8][2],
        score=2,
        issues=["カスタム404ページやエラーメッセージが確認できない"],
        suggestions=["カスタム404ページを作成し、サイトマップへの誘導とよくあるページへのリンクを配置"]
    )
    scores.append(s9)

    # 10. Help and documentation
    has_faq = "faq" in raw or "よくある質問" in raw or "q&a" in raw
    s10 = HeuristicScore(
        key="help_docs", principle_en=NIELSEN_PRINCIPLES[9][1],
        principle_ja=NIELSEN_PRINCIPLES[9][2],
        score=3 if has_faq else 2,
        issues=["FAQ・使い方ガイドが不在で、潜在顧客の疑問が解消されにくい"] if not has_faq else [],
        suggestions=["FAQページと製品仕様・納期・発注方法の明記を追加する"]
    )
    scores.append(s10)

    return scores


def run_research(company: dict) -> CompanyResearch:
    """企業1社のリサーチを実行してCompanyResearchを返す"""
    company_id = company["id"]
    url = company["url"]
    print(f"[Research] Fetching: {url}")

    html = _fetch(url)
    result = CompanyResearch(
        company_id=company_id,
        company_name=company["name"],
        url=url,
        researched_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    if not html:
        print(f"[Research] Could not fetch {url}")
        return result

    soup = BeautifulSoup(html, "html.parser")
    basic = _parse_basic(soup, url)

    result.page_title = basic.get("page_title", "")
    result.description = basic.get("description", "")
    result.last_update_estimate = basic.get("last_update_estimate", "不明")
    result.has_contact_form = basic.get("has_contact_form", False)
    result.has_english_page = basic.get("has_english_page", False)
    result.has_recruitment_page = basic.get("has_recruitment_page", False)
    result.has_mobile_friendly = basic.get("has_mobile_friendly", False)
    result.has_sns_links = basic.get("has_sns_links", False)
    result.raw_text = basic.get("raw_text", "")

    scores = _heuristic_eval(soup, basic)
    result.heuristic_scores = [asdict(s) for s in scores]
    result.total_score = sum(s.score for s in scores)

    # top issues / suggestions
    for s in sorted(scores, key=lambda x: x.score):
        result.top_issues.extend(s.issues)
        result.top_suggestions.extend(s.suggestions)
    result.top_issues = result.top_issues[:5]
    result.top_suggestions = result.top_suggestions[:5]

    return result


def save_research(result: CompanyResearch, output_dir: str) -> str:
    """リサーチ結果をJSONファイルに保存"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/{result.company_id}_research.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"[Research] Saved: {path}")
    return path
