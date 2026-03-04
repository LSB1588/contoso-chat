#!/usr/bin/env python3
"""
Sales Agent CLI - 永続的な利用のためのコマンドラインツール
==============================================================

使用方法:
  python sales_agent_cli.py run                      # 全社を処理
  python sales_agent_cli.py run --company astryda    # 1社だけ処理
  python sales_agent_cli.py add --url https://... --name "会社名" --industry "業種"
  python sales_agent_cli.py list                     # 登録企業一覧
  python sales_agent_cli.py report astryda           # レポートパスを表示
  python sales_agent_cli.py watch                    # 定期実行モード（毎日）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR    = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "companies.json"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUTS_DIR = BASE_DIR / "outputs"

sys.path.insert(0, str(BASE_DIR))


# ─────────────────────────── ヘルパー ────────────────────────────────────

def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_config(cfg: dict):
    cfg["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _slugify(name: str) -> str:
    """日本語企業名からIDを生成"""
    # 英数字+アンダースコアのみ
    name_en = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    name_en = re.sub(r"[\s\-]+", "_", name_en)
    name_en = name_en.lower().strip("_")
    # 全角→ローマ字の簡易変換
    kana_map = {
        "株式会社": "", "有限会社": "", "合同会社": "",
        "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
        "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    }
    for k, v in kana_map.items():
        name = name.replace(k, v)
    # 残った文字を除去して小文字化
    slug = re.sub(r"[^\x20-\x7E]", "", name)
    slug = re.sub(r"\s+", "_", slug.strip())
    slug = slug.lower() or f"company_{int(time.time())}"
    return slug[:30]


# ─────────────────────────── コマンド実装 ─────────────────────────────────

def cmd_list(args):
    """登録企業一覧の表示"""
    cfg = _load_config()
    companies = cfg.get("companies", [])
    if not companies:
        print("（登録企業なし）")
        return

    print(f"\n{'─'*70}")
    print(f"  登録企業一覧（{len(companies)}社）")
    print(f"{'─'*70}")
    for c in companies:
        status_icon = "✅" if c.get("status") == "active" else "⏸️"
        # リサーチレポートの存在確認
        report_exists = (REPORTS_DIR / f"{c['id']}_research.json").exists()
        pptx_exists   = (OUTPUTS_DIR / c["id"] / f"{c['id']}_heuristic_report.pptx").exists()
        report_mark = "📊" if pptx_exists else ("📄" if report_exists else "  ")
        print(f"  {status_icon} [{c['id']:20s}] {c['name']} {report_mark}")
        print(f"     URL: {c['url']}")
        print(f"     業種: {c['industry']}  追加日: {c.get('added_at','不明')}")
        print()


def cmd_add(args):
    """新しい企業を追加"""
    cfg = _load_config()

    # IDを生成（または指定）
    company_id = args.id if hasattr(args, "id") and args.id else _slugify(args.name)

    # 重複チェック
    existing_ids = {c["id"] for c in cfg["companies"]}
    if company_id in existing_ids:
        print(f"[ERROR] 企業ID '{company_id}' は既に登録されています。")
        cmd_list(args)
        return

    new_company = {
        "id":           company_id,
        "name":         args.name,
        "name_en":      getattr(args, "name_en", ""),
        "url":          args.url,
        "industry":     getattr(args, "industry", ""),
        "industry_en":  "",
        "business_model": getattr(args, "biz_model", "B2B"),
        "contact_email": getattr(args, "email", ""),
        "founded":      "",
        "added_at":     datetime.now().strftime("%Y-%m-%d"),
        "status":       "active",
        "tags":         [],
        "notes":        ""
    }

    cfg["companies"].append(new_company)
    _save_config(cfg)
    print(f"✅ 追加完了: {args.name} (ID: {company_id})")
    print(f"   次のコマンドで処理を開始: python sales_agent_cli.py run --company {company_id}")


def cmd_remove(args):
    """企業を削除（または非アクティブ化）"""
    cfg = _load_config()
    company_id = args.company_id
    found = False

    for c in cfg["companies"]:
        if c["id"] == company_id:
            if args.soft:
                c["status"] = "inactive"
                print(f"⏸️  非アクティブ化: {c['name']}")
            else:
                cfg["companies"].remove(c)
                print(f"🗑️  削除: {c['name']}")
            found = True
            break

    if not found:
        print(f"[ERROR] 企業ID '{company_id}' が見つかりません")
        return

    _save_config(cfg)


def cmd_run(args):
    """エージェントチームを実行"""
    from orchestrator import AgentTeamOrchestrator

    orchestrator = AgentTeamOrchestrator(max_workers=getattr(args, "workers", 4))
    company_id   = getattr(args, "company", None)
    report_only  = getattr(args, "report_only", False)

    orchestrator.run(company_id=company_id, report_only=report_only)


def cmd_report(args):
    """指定企業の生成済みレポートパスを表示"""
    company_id = args.company_id
    output_dir = OUTPUTS_DIR / company_id

    print(f"\n  📁 出力ファイル: {company_id}")
    print(f"  {'─'*50}")

    files = {
        "リサーチJSON":   REPORTS_DIR / f"{company_id}_research.json",
        "PPTX":           output_dir / f"{company_id}_heuristic_report.pptx",
        "Before モック":  output_dir / f"{company_id}_before.html",
        "After モック":   output_dir / f"{company_id}_after.html",
        "アプローチメール": output_dir / f"{company_id}_approach.md",
    }

    for label, path in files.items():
        exists = "✅" if path.exists() else "❌"
        size   = f"({path.stat().st_size // 1024}KB)" if path.exists() else ""
        print(f"  {exists} {label:20s}: {path} {size}")

    print()


def cmd_watch(args):
    """定期実行モード（--interval 分でポーリング）"""
    interval_sec = getattr(args, "interval", 1440) * 60  # デフォルト24時間
    print(f"🔁 定期実行モード: {interval_sec // 60}分ごとに全社を処理")
    print("   Ctrl+C で停止")

    while True:
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} — 処理開始")
        try:
            cmd_run(args)
        except Exception as e:
            print(f"[ERROR] {e}")
        print(f"⏳ 次回実行まで {interval_sec // 60} 分待機...")
        time.sleep(interval_sec)


# ─────────────────────────── メインCLI ───────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-agent",
        description="Sales Agent Teams CLI — 企業リサーチ・営業資料自動生成"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="登録企業一覧を表示")

    # add
    p_add = sub.add_parser("add", help="新しい企業を登録")
    p_add.add_argument("--url",      required=True, help="企業WebサイトURL")
    p_add.add_argument("--name",     required=True, help="企業名（日本語可）")
    p_add.add_argument("--industry", default="",    help="業種")
    p_add.add_argument("--email",    default="",    help="連絡先メールアドレス")
    p_add.add_argument("--id",       default=None,  help="カスタムID（省略時は自動生成）")
    p_add.add_argument("--biz-model", default="B2B", help="ビジネスモデル（B2B/B2C）")

    # remove
    p_rm = sub.add_parser("remove", help="企業を削除")
    p_rm.add_argument("company_id", help="削除する企業ID")
    p_rm.add_argument("--soft", action="store_true", help="論理削除（非アクティブ化）")

    # run
    p_run = sub.add_parser("run", help="エージェントチームを実行")
    p_run.add_argument("--company",     default=None, help="特定企業IDのみ処理（省略時は全社）")
    p_run.add_argument("--report-only", action="store_true", help="既存JSONからPPTX等を再生成")
    p_run.add_argument("--workers",     type=int, default=4, help="並列ワーカー数")

    # report
    p_rep = sub.add_parser("report", help="生成済みレポートのパスを確認")
    p_rep.add_argument("company_id", help="企業ID")

    # watch
    p_watch = sub.add_parser("watch", help="定期実行モード")
    p_watch.add_argument("--interval", type=int, default=1440,
                         help="実行間隔（分）デフォルト: 1440=24時間")
    p_watch.add_argument("--company", default=None, help="特定企業IDのみ定期処理")

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()

    cmd_map = {
        "list":   cmd_list,
        "add":    cmd_add,
        "remove": cmd_remove,
        "run":    cmd_run,
        "report": cmd_report,
        "watch":  cmd_watch,
    }

    handler = cmd_map.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
