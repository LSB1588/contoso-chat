"""
PPTX Generator - ヒューリスティック調査結果をPowerPointに出力
"""
from __future__ import annotations

import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


# ─────────────────────────────── カラー定義 ───────────────────────────────
COLORS = {
    "astryda":    {"primary": RGBColor(0x1A, 0x23, 0x7E), "accent": RGBColor(0x42, 0x8B, 0xCA)},
    "bell_fresh": {"primary": RGBColor(0x1B, 0x5E, 0x20), "accent": RGBColor(0x4C, 0xAF, 0x50)},
    "default":    {"primary": RGBColor(0x1A, 0x23, 0x7E), "accent": RGBColor(0x42, 0x8B, 0xCA)},
}
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK      = RGBColor(0x1A, 0x1A, 0x2E)
GRAY      = RGBColor(0x78, 0x78, 0x78)
LIGHT_BG  = RGBColor(0xF5, 0xF7, 0xFA)
RED       = RGBColor(0xD3, 0x2F, 0x2F)
ORANGE    = RGBColor(0xF5, 0x7C, 0x00)
GREEN     = RGBColor(0x38, 0x8E, 0x3C)
YELLOW    = RGBColor(0xFF, 0xD6, 0x00)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


# ─────────────────────────────── ヘルパー ────────────────────────────────
def _rgb(r, g, b): return RGBColor(r, g, b)

def _add_textbox(slide, left, top, width, height, text, size=14, bold=False,
                 color=DARK, align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox

def _fill_shape(shape, color: RGBColor):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color

def _add_rect(slide, left, top, width, height, fill_color: RGBColor, line=False):
    shape = slide.shapes.add_shape(1, left, top, width, height)  # MSO_SHAPE_TYPE.RECTANGLE=1
    _fill_shape(shape, fill_color)
    if not line:
        shape.line.fill.background()
    return shape

def _score_color(score: int) -> RGBColor:
    if score >= 4: return GREEN
    if score >= 3: return ORANGE
    return RED

def _grade_to_badge(grade: str) -> tuple[str, RGBColor]:
    if "良好" in grade: return (grade, GREEN)
    if "要改善" in grade or "C" in grade: return (grade, ORANGE)
    return (grade, RED)


# ────────────────────────────── スライド生成 ──────────────────────────────

def _slide_title(prs: Presentation, company: dict, research: dict):
    """スライド1: タイトル"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    company_id = company["id"]
    primary = COLORS.get(company_id, COLORS["default"])["primary"]
    accent  = COLORS.get(company_id, COLORS["default"])["accent"]

    # 背景グラデーション風（2色の矩形重ね）
    bg = _add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, primary)
    accent_rect = _add_rect(slide, Inches(7), 0, Inches(6.33), SLIDE_H, accent)
    accent_rect.fill.fore_color.rgb = accent

    # ロゴ的なアクセントライン
    _add_rect(slide, Inches(1), Inches(2.5), Inches(0.1), Inches(2.5), YELLOW)

    # タイトルテキスト
    _add_textbox(slide, Inches(1.3), Inches(1.5), Inches(8), Inches(0.8),
                 "ウェブサイト ヒューリスティック調査レポート",
                 size=18, bold=False, color=RGBColor(0xFF,0xFF,0xCC))

    _add_textbox(slide, Inches(1.3), Inches(2.3), Inches(9), Inches(1.2),
                 company["name"],
                 size=36, bold=True, color=WHITE)

    _add_textbox(slide, Inches(1.3), Inches(3.8), Inches(8), Inches(0.6),
                 f"調査日: {research.get('researched_at','2026-03-04')}　｜　ニールセン10原則準拠",
                 size=14, color=RGBColor(0xCC,0xDD,0xFF))

    score = research.get("total_score", 0)
    max_s = research.get("max_score", 50)
    pct   = int(score / max_s * 100)
    grade = research.get("grade", "要改善")
    grade_text, grade_color = _grade_to_badge(grade)

    _add_textbox(slide, Inches(1.3), Inches(4.6), Inches(3), Inches(0.8),
                 f"総合スコア: {score}/{max_s}点 ({pct}%)",
                 size=20, bold=True, color=YELLOW)

    _add_textbox(slide, Inches(1.3), Inches(5.4), Inches(3), Inches(0.5),
                 f"評価: {grade_text}",
                 size=16, bold=True, color=grade_color)

    _add_textbox(slide, Inches(9.5), Inches(6.8), Inches(3.5), Inches(0.4),
                 "Powered by Agent Teams | Sales Intelligence",
                 size=9, color=RGBColor(0xBB,0xCC,0xDD), align=PP_ALIGN.RIGHT)


def _slide_overview(prs, company, research):
    """スライド2: サイト概要チェックリスト"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    company_id = company["id"]
    primary = COLORS.get(company_id, COLORS["default"])["primary"]

    # ヘッダーバー
    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), primary)
    _add_textbox(slide, Inches(0.4), Inches(0.2), Inches(10), Inches(0.7),
                 "サイト概要 & チェックリスト", size=24, bold=True, color=WHITE)

    # 会社情報ブロック
    _add_rect(slide, Inches(0.3), Inches(1.3), Inches(5.8), Inches(2.8), LIGHT_BG)
    _add_textbox(slide, Inches(0.5), Inches(1.4), Inches(5.5), Inches(0.5),
                 "企業基本情報", size=14, bold=True, color=primary)
    info_lines = [
        f"企業名: {company['name']}",
        f"業種:   {company['industry']}",
        f"URL:    {company['url']}",
        f"最終更新: {research.get('last_update_estimate','不明')}",
        f"総合スコア: {research.get('total_score',0)}/{research.get('max_score',50)}点",
    ]
    _add_textbox(slide, Inches(0.5), Inches(1.9), Inches(5.5), Inches(2.0),
                 "\n".join(info_lines), size=12, color=DARK)

    # 機能チェックリスト
    _add_rect(slide, Inches(6.5), Inches(1.3), Inches(6.3), Inches(2.8), LIGHT_BG)
    _add_textbox(slide, Inches(6.7), Inches(1.4), Inches(5.8), Inches(0.5),
                 "機能チェックリスト", size=14, bold=True, color=primary)

    features = [
        ("お問い合わせフォーム", research.get("has_contact_form", False)),
        ("スマートフォン対応",   research.get("has_mobile_friendly", None)),
        ("英語ページ",          research.get("has_english_page", False)),
        ("採用ページ（自社）",  research.get("has_recruitment_page", False)),
        ("SNSリンク",           research.get("has_sns_links", False)),
    ]
    for i, (name, val) in enumerate(features):
        y = Inches(1.95 + i * 0.45)
        if val is True:
            mark, col = "✅", GREEN
        elif val is False:
            mark, col = "❌", RED
        else:
            mark, col = "⚠️", ORANGE
        _add_textbox(slide, Inches(6.7), y, Inches(0.5), Inches(0.4), mark, size=13, color=col)
        _add_textbox(slide, Inches(7.2), y, Inches(5.0), Inches(0.4), name, size=12, color=DARK)

    # TOP課題
    _add_rect(slide, Inches(0.3), Inches(4.3), Inches(12.5), Inches(2.9), _rgb(0xFF,0xF3,0xE0))
    _add_textbox(slide, Inches(0.5), Inches(4.4), Inches(5), Inches(0.5),
                 "🔥 主要課題 TOP5", size=14, bold=True, color=RED)
    issues = research.get("top_issues", [])
    for i, issue in enumerate(issues[:5]):
        y = Inches(4.9 + i * 0.43)
        _add_textbox(slide, Inches(0.6), y, Inches(0.4), Inches(0.4),
                     f"{i+1}.", size=11, bold=True, color=RED)
        _add_textbox(slide, Inches(1.0), y, Inches(11.5), Inches(0.4),
                     issue, size=11, color=DARK)


def _slide_heuristic_scores(prs, company, research):
    """スライド3: ニールセン10原則スコア一覧"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    company_id = company["id"]
    primary = COLORS.get(company_id, COLORS["default"])["primary"]

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), primary)
    _add_textbox(slide, Inches(0.4), Inches(0.2), Inches(12), Inches(0.7),
                 "ニールセン10原則 スコアカード", size=24, bold=True, color=WHITE)

    scores = research.get("heuristic_scores", [])
    max_bar_w = Inches(3.5)

    for i, s in enumerate(scores[:10]):
        col_idx = i % 2
        row_idx = i // 2
        x_base = Inches(0.3) + col_idx * Inches(6.5)
        y_base = Inches(1.3) + row_idx * Inches(1.15)

        score_val = s.get("score", 1)
        color = _score_color(score_val)

        # 枠
        _add_rect(slide, x_base, y_base, Inches(6.2), Inches(1.0), LIGHT_BG)

        # 番号＋名前
        _add_textbox(slide, x_base + Inches(0.1), y_base + Inches(0.05),
                     Inches(0.4), Inches(0.4),
                     f"{i+1}.", size=11, bold=True, color=primary)
        _add_textbox(slide, x_base + Inches(0.5), y_base + Inches(0.05),
                     Inches(3.3), Inches(0.4),
                     s.get("principle_ja", ""), size=11, bold=True, color=DARK)

        # スコア数字
        _add_textbox(slide, x_base + Inches(5.0), y_base + Inches(0.05),
                     Inches(1.0), Inches(0.4),
                     f"{score_val}/5", size=13, bold=True, color=color,
                     align=PP_ALIGN.RIGHT)

        # バー
        bar_w = int(max_bar_w * score_val / 5)
        _add_rect(slide, x_base + Inches(0.5), y_base + Inches(0.55),
                  max_bar_w, Inches(0.2), _rgb(0xE0,0xE0,0xE0))
        if bar_w > 0:
            _add_rect(slide, x_base + Inches(0.5), y_base + Inches(0.55),
                      bar_w, Inches(0.2), color)

        # 最初の課題を小さく表示
        issues = s.get("issues", [])
        if issues:
            short_issue = issues[0][:45] + ("…" if len(issues[0]) > 45 else "")
            _add_textbox(slide, x_base + Inches(0.5), y_base + Inches(0.78),
                         Inches(5.5), Inches(0.25),
                         f"→ {short_issue}", size=9, color=GRAY, italic=True)


def _slide_heuristic_detail(prs, company, research, start_idx=0, end_idx=5):
    """スライド4/5: ヒューリスティック詳細（5件ずつ2枚）"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    company_id = company["id"]
    primary = COLORS.get(company_id, COLORS["default"])["primary"]
    accent  = COLORS.get(company_id, COLORS["default"])["accent"]

    label = f"詳細分析 ({start_idx+1}〜{end_idx})"
    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), primary)
    _add_textbox(slide, Inches(0.4), Inches(0.2), Inches(12), Inches(0.7),
                 f"ニールセン原則 詳細分析 — {label}", size=22, bold=True, color=WHITE)

    scores = research.get("heuristic_scores", [])[start_idx:end_idx]
    item_h = Inches(1.15)

    for i, s in enumerate(scores):
        y = Inches(1.25) + i * item_h
        score_val = s.get("score", 1)
        color = _score_color(score_val)

        # 背景
        _add_rect(slide, Inches(0.2), y, Inches(12.9), item_h - Inches(0.08), LIGHT_BG)

        # 番号バッジ
        badge = _add_rect(slide, Inches(0.2), y, Inches(0.45), item_h - Inches(0.08), color)
        _add_textbox(slide, Inches(0.22), y + Inches(0.3), Inches(0.4), Inches(0.4),
                     str(start_idx + i + 1), size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

        # 原則名
        _add_textbox(slide, Inches(0.75), y + Inches(0.05), Inches(5), Inches(0.45),
                     s.get("principle_ja",""), size=12, bold=True, color=primary)
        _add_textbox(slide, Inches(0.75), y + Inches(0.05), Inches(5), Inches(0.45),
                     "", size=10, color=GRAY)  # English subtitle placeholder

        # スコア
        _add_textbox(slide, Inches(11.5), y + Inches(0.05), Inches(1.2), Inches(0.45),
                     f"★ {score_val}/5", size=14, bold=True, color=color, align=PP_ALIGN.RIGHT)

        # 課題
        issues = s.get("issues", [])
        issue_text = "・" + "　・".join(issues[:2]) if issues else "—"
        _add_textbox(slide, Inches(0.75), y + Inches(0.52), Inches(6.0), Inches(0.5),
                     f"課題: {issue_text}", size=9, color=RED)

        # 改善提案
        sugs = s.get("suggestions", [])
        sug_text = sugs[0][:60] + "…" if sugs and len(sugs[0]) > 60 else (sugs[0] if sugs else "—")
        _add_textbox(slide, Inches(7.0), y + Inches(0.52), Inches(6.0), Inches(0.5),
                     f"改善案: {sug_text}", size=9, color=GREEN)


def _slide_priority_improvements(prs, company, research):
    """スライド6: 優先改善提案"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    company_id = company["id"]
    primary = COLORS.get(company_id, COLORS["default"])["primary"]

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), primary)
    _add_textbox(slide, Inches(0.4), Inches(0.2), Inches(12), Inches(0.7),
                 "優先改善提案 & ロードマップ", size=24, bold=True, color=WHITE)

    suggestions = research.get("top_suggestions", [])
    effort_map  = {"低": GREEN, "中": ORANGE, "高": RED, "低〜中": _rgb(0x66,0xBB,0x6A)}

    # 改善提案リスト
    _add_textbox(slide, Inches(0.4), Inches(1.2), Inches(7.5), Inches(0.4),
                 "改善提案（優先度順）", size=14, bold=True, color=primary)

    for i, sug in enumerate(suggestions[:5]):
        y = Inches(1.65) + i * Inches(0.85)
        priority_colors = [RED, RED, ORANGE, ORANGE, _rgb(0x42,0xA5,0xF5)]
        pcol = priority_colors[i] if i < len(priority_colors) else GRAY
        _add_rect(slide, Inches(0.4), y, Inches(0.5), Inches(0.55), pcol)
        _add_textbox(slide, Inches(0.43), y + Inches(0.05), Inches(0.45), Inches(0.45),
                     f"P{i+1}", size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _add_textbox(slide, Inches(1.0), y + Inches(0.05), Inches(6.5), Inches(0.55),
                     sug, size=11, color=DARK)

    # 期待効果ボックス
    _add_rect(slide, Inches(8.2), Inches(1.2), Inches(4.9), Inches(5.9), _rgb(0xE8,0xF5,0xE9))
    _add_textbox(slide, Inches(8.4), Inches(1.3), Inches(4.5), Inches(0.5),
                 "💡 改善による期待効果", size=13, bold=True, color=GREEN)

    effects = [
        ("問い合わせ数", "2〜3倍増加"),
        ("直帰率",       "20〜30%改善"),
        ("モバイル流入", "新規獲得"),
        ("採用コスト",   "低減"),
        ("SEO順位",      "向上"),
    ]
    for i, (label, val) in enumerate(effects):
        y = Inches(1.9) + i * Inches(0.9)
        _add_rect(slide, Inches(8.4), y, Inches(4.5), Inches(0.75), WHITE)
        _add_textbox(slide, Inches(8.5), y + Inches(0.05), Inches(2.5), Inches(0.35),
                     label, size=11, color=GRAY)
        _add_textbox(slide, Inches(10.0), y + Inches(0.05), Inches(2.7), Inches(0.35),
                     val, size=13, bold=True, color=GREEN, align=PP_ALIGN.RIGHT)

    # フッター
    _add_textbox(slide, Inches(0.4), Inches(6.9), Inches(12.5), Inches(0.35),
                 "※ 本レポートはAgent Teamsによる自動生成です。営業提案資料としてご活用ください。",
                 size=9, color=GRAY, italic=True)


def _slide_before_after(prs, company, research):
    """スライド7: Before/After サマリー"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    company_id = company["id"]
    primary = COLORS.get(company_id, COLORS["default"])["primary"]
    accent  = COLORS.get(company_id, COLORS["default"])["accent"]

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), primary)
    _add_textbox(slide, Inches(0.4), Inches(0.2), Inches(12), Inches(0.7),
                 "Before / After — 改善イメージ", size=24, bold=True, color=WHITE)

    # Before列
    _add_rect(slide, Inches(0.3), Inches(1.2), Inches(6.0), Inches(5.9), _rgb(0xFF,0xEB,0xEE))
    _add_textbox(slide, Inches(0.5), Inches(1.3), Inches(5.5), Inches(0.6),
                 "😟 BEFORE（現状）", size=18, bold=True, color=RED)

    before_points = []
    if not research.get("has_contact_form"):
        before_points.append("問い合わせはTEL・FAXのみ")
    if not research.get("has_mobile_friendly"):
        before_points.append("スマートフォン非対応")
    if not research.get("has_english_page"):
        before_points.append("英語ページなし")
    if not research.get("has_recruitment_page"):
        before_points.append("採用ページ不在")
    if not research.get("has_sns_links"):
        before_points.append("SNSリンクなし")
    before_points += research.get("top_issues", [])[:3]

    for i, pt in enumerate(before_points[:6]):
        y = Inches(2.1) + i * Inches(0.75)
        _add_rect(slide, Inches(0.5), y, Inches(5.5), Inches(0.6), _rgb(0xFF,0xCC,0xCB))
        _add_textbox(slide, Inches(0.55), y + Inches(0.08), Inches(0.4), Inches(0.4),
                     "✕", size=14, bold=True, color=RED)
        _add_textbox(slide, Inches(1.0), y + Inches(0.08), Inches(4.8), Inches(0.4),
                     pt[:40], size=11, color=DARK)

    # After列
    _add_rect(slide, Inches(7.0), Inches(1.2), Inches(6.0), Inches(5.9), _rgb(0xE8,0xF5,0xE9))
    _add_textbox(slide, Inches(7.2), Inches(1.3), Inches(5.5), Inches(0.6),
                 "😊 AFTER（改善後）", size=18, bold=True, color=GREEN)

    after_points = [
        "24時間Webフォームで問い合わせ受付",
        "スマートフォン完全対応デザイン",
        "英語ページで海外からの問い合わせ対応",
        "採用ページで人材獲得コスト削減",
        "SNS連携でブランド認知向上",
        "FAQページでセルフサービス化",
    ]

    for i, pt in enumerate(after_points[:6]):
        y = Inches(2.1) + i * Inches(0.75)
        _add_rect(slide, Inches(7.2), y, Inches(5.5), Inches(0.6), _rgb(0xC8,0xE6,0xC9))
        _add_textbox(slide, Inches(7.25), y + Inches(0.08), Inches(0.4), Inches(0.4),
                     "✓", size=14, bold=True, color=GREEN)
        _add_textbox(slide, Inches(7.7), y + Inches(0.08), Inches(4.8), Inches(0.4),
                     pt[:40], size=11, color=DARK)

    # 矢印
    _add_rect(slide, Inches(6.3), Inches(3.6), Inches(0.7), Inches(0.7), accent)
    _add_textbox(slide, Inches(6.3), Inches(3.65), Inches(0.7), Inches(0.55),
                 "→", size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


def generate_heuristic_pptx(company: dict, research: dict, output_dir: str) -> str:
    """PPTXを生成して保存"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    _slide_title(prs, company, research)
    _slide_overview(prs, company, research)
    _slide_heuristic_scores(prs, company, research)
    _slide_heuristic_detail(prs, company, research, start_idx=0, end_idx=5)
    _slide_heuristic_detail(prs, company, research, start_idx=5, end_idx=10)
    _slide_priority_improvements(prs, company, research)
    _slide_before_after(prs, company, research)

    company_id = company["id"]
    out_path = f"{output_dir}/{company_id}_heuristic_report.pptx"
    prs.save(out_path)
    print(f"[PPTX] Saved: {out_path}")
    return out_path
