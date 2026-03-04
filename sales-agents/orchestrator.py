"""
Agent Teams Orchestrator
========================
複数のエージェントを並列・逐次で実行し、企業ごとに以下の出力を生成する：

1. Research Agent    → JSON リサーチレポート + ヒューリスティック調査
2. PPTX Agent        → ニールセン評価のPowerPointプレゼンテーション
3. Mock Generator    → Before/After HTML モック
4. Approach Agent    → 営業メール・電話スクリプト Markdown

Usage:
    python orchestrator.py                          # companies.json 全社処理
    python orchestrator.py --company astryda        # 特定企業のみ
    python orchestrator.py --report-only            # リサーチ済みJSONからPPTX等を再生成
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ─── パス設定 ──────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "companies.json"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUTS_DIR = BASE_DIR / "outputs"

sys.path.insert(0, str(BASE_DIR))

from agents.research.research_agent   import run_research, save_research
from agents.research.pptx_generator   import generate_heuristic_pptx
from agents.mock_generator.mock_generator_agent import save_mocks
from agents.approach.approach_agent   import generate_approach_package, save_approach


# ─── Agent 定義 ────────────────────────────────────────────────────────

class ResearchAgent:
    """Agent 1: 企業Webサイトのリサーチ＋ヒューリスティック調査"""
    name = "Research Agent"

    def run(self, company: dict) -> dict:
        print(f"\n[{self.name}] 🔍 Start: {company['name']}")
        t0 = time.time()

        # 既存レポートがあれば再利用
        existing = REPORTS_DIR / f"{company['id']}_research.json"
        if existing.exists():
            print(f"[{self.name}] ♻️  Loaded existing report: {existing}")
            with open(existing, encoding="utf-8") as f:
                return json.load(f)

        result = run_research(company)
        save_research(result, str(REPORTS_DIR))
        print(f"[{self.name}] ✅ Done in {time.time()-t0:.1f}s")
        return result.to_dict()


class PPTXAgent:
    """Agent 2: ヒューリスティック調査 → PowerPointスライド生成"""
    name = "PPTX Agent"

    def run(self, company: dict, research: dict) -> str:
        print(f"\n[{self.name}] 📊 Start: {company['name']}")
        t0 = time.time()
        out_dir = str(OUTPUTS_DIR / company["id"])
        path = generate_heuristic_pptx(company, research, out_dir)
        print(f"[{self.name}] ✅ Done in {time.time()-t0:.1f}s → {path}")
        return path


class MockGeneratorAgent:
    """Agent 3: Before/After HTMLモック生成"""
    name = "Mock Generator Agent"

    def run(self, company: dict, research: dict) -> dict:
        print(f"\n[{self.name}] 🖼️  Start: {company['name']}")
        t0 = time.time()
        out_dir = str(OUTPUTS_DIR / company["id"])
        paths = save_mocks(company, research, out_dir)
        print(f"[{self.name}] ✅ Done in {time.time()-t0:.1f}s → {paths}")
        return paths


class ApproachAgent:
    """Agent 4: 営業メール・電話スクリプト生成"""
    name = "Approach Agent"

    def run(self, company: dict, research: dict) -> str:
        print(f"\n[{self.name}] 📧 Start: {company['name']}")
        t0 = time.time()
        package = generate_approach_package(company, research)
        out_dir = str(OUTPUTS_DIR / company["id"])
        path = save_approach(package, out_dir)
        print(f"[{self.name}] ✅ Done in {time.time()-t0:.1f}s → {path}")
        return path


# ─── Orchestrator ──────────────────────────────────────────────────────

class AgentTeamOrchestrator:
    """
    Agent Teams のオーケストレーター。
    - Phase 1 (並列): 複数企業を同時にリサーチ
    - Phase 2 (並列): 各企業のPPTX・Mock・Approachを並列生成
    """

    def __init__(self, max_workers: int = 4):
        self.research_agent      = ResearchAgent()
        self.pptx_agent          = PPTXAgent()
        self.mock_agent          = MockGeneratorAgent()
        self.approach_agent      = ApproachAgent()
        self.max_workers         = max_workers

    def _load_companies(self, company_id: str | None = None) -> list[dict]:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        companies = [c for c in cfg["companies"] if c["status"] == "active"]
        if company_id:
            companies = [c for c in companies if c["id"] == company_id]
        return companies

    def _process_one_company(self, company: dict, report_only: bool = False) -> dict:
        """1社の全エージェント処理を実行"""
        print(f"\n{'='*60}")
        print(f"  Processing: {company['name']}")
        print(f"{'='*60}")

        # Phase 1: Research（同期）
        research = self.research_agent.run(company)

        # Phase 2: PPTX・Mock・Approach を並列実行
        results = {}
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {
                ex.submit(self.pptx_agent.run,     company, research): "pptx",
                ex.submit(self.mock_agent.run,      company, research): "mocks",
                ex.submit(self.approach_agent.run,  company, research): "approach",
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"[ERROR] {key}: {e}")
                    results[key] = str(e)

        return {
            "company_id":   company["id"],
            "company_name": company["name"],
            "research":     research,
            **results
        }

    def run(self, company_id: str | None = None, report_only: bool = False):
        """全エージェントチームを実行"""
        companies = self._load_companies(company_id)
        if not companies:
            print(f"[ERROR] No companies found (id={company_id})")
            return {}

        print(f"\n{'='*60}")
        print(f"  🚀 Agent Teams Orchestrator")
        print(f"  対象企業: {len(companies)}社")
        for c in companies:
            print(f"  - {c['name']}")
        print(f"{'='*60}\n")

        all_results = {}

        # 企業が複数の場合は並列リサーチ（I/O bound）
        if len(companies) > 1:
            print("[Orchestrator] Phase 1: 並列リサーチ開始")
            research_map = {}
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                future_to_co = {ex.submit(self.research_agent.run, c): c for c in companies}
                for future in as_completed(future_to_co):
                    co = future_to_co[future]
                    try:
                        research_map[co["id"]] = future.result()
                    except Exception as e:
                        print(f"[ERROR] Research failed for {co['name']}: {e}")

            print("[Orchestrator] Phase 2: PPTX・Mock・Approach を並列生成")
            for company in companies:
                research = research_map.get(company["id"], {})
                with ThreadPoolExecutor(max_workers=3) as ex:
                    futures = {
                        ex.submit(self.pptx_agent.run,    company, research): "pptx",
                        ex.submit(self.mock_agent.run,    company, research): "mocks",
                        ex.submit(self.approach_agent.run, company, research): "approach",
                    }
                    results = {}
                    for future in as_completed(futures):
                        key = futures[future]
                        try:
                            results[key] = future.result()
                        except Exception as e:
                            print(f"[ERROR] {key} for {company['name']}: {e}")
                            results[key] = str(e)

                all_results[company["id"]] = {
                    "company_name": company["name"],
                    "research":     research,
                    **results
                }
        else:
            result = self._process_one_company(companies[0], report_only)
            all_results[result["company_id"]] = result

        # サマリーを出力
        self._print_summary(all_results)
        return all_results

    def _print_summary(self, results: dict):
        print(f"\n{'='*60}")
        print("  📋 実行サマリー")
        print(f"{'='*60}")
        for cid, r in results.items():
            print(f"\n  ✅ {r.get('company_name', cid)}")
            if "pptx" in r:
                print(f"     📊 PPTX:     {r['pptx']}")
            if "mocks" in r:
                mocks = r["mocks"]
                if isinstance(mocks, dict):
                    print(f"     🖼️  Before:   {mocks.get('before','')}")
                    print(f"     🖼️  After:    {mocks.get('after','')}")
            if "approach" in r:
                print(f"     📧 Approach: {r['approach']}")
        print(f"\n{'='*60}\n")


# ─── CLI Entry Point ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sales Agent Teams - 企業分析・営業資料自動生成"
    )
    parser.add_argument("--company",     type=str, default=None,
                        help="処理する企業ID（省略時は全社処理）")
    parser.add_argument("--report-only", action="store_true",
                        help="既存リサーチJSONからPPTX等を再生成（Webアクセスなし）")
    parser.add_argument("--workers",     type=int, default=4,
                        help="並列ワーカー数（デフォルト: 4）")
    args = parser.parse_args()

    orchestrator = AgentTeamOrchestrator(max_workers=args.workers)
    orchestrator.run(
        company_id  = args.company,
        report_only = args.report_only
    )


if __name__ == "__main__":
    main()
